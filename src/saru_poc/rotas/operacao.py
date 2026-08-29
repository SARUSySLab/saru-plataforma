"""Espinha operacional: evento, sessao, bateria, contexto, setup, trecho.

**A regra desta camada, e ela vale linha a linha:** todo SELECT, UPDATE e
DELETE carrega `user_id = %s` no WHERE, com o id vindo de `Dono`. Nunca do
corpo, nunca da URL. O guard de autenticacao diz QUEM esta chamando; e o WHERE
que diz o que e dele. Foi exatamente essa distincao que faltou no `saru-app` e
virou o achado S1 (endpoints com JwtAuthGuard e nenhum filtro por usuario,
qualquer conta autenticada editava sessao alheia).

Consequencia pratica: recurso de outro dono devolve **404, nao 403**. 403
confirmaria que o id existe, e isso ja e vazamento.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..auth import Dono
from ..db import connect

router = APIRouter(prefix="/api", tags=["operacao"])

NAO_ACHADO = "não encontrado"

PNEU_ESTADOS = ("novo", "usado")


def _vazio_e_nulo(v: Any) -> Any:
    """String vazia vira NULL.

    Um `<input>` em branco manda `""`, nao `null`, e `""` nao e um valor: nao
    passa no CHECK de `pneu_estado`, nao converte pra real, e derrubava a rota
    com 500. Campo em branco significa "nao informado", que no banco e NULL.
    """
    if isinstance(v, str) and not v.strip():
        return None
    return v


def _numero(v: Any, campo: str) -> float | None:
    """Numero ou NULL, com 422 no lugar de 500 quando o texto nao e numero.

    Entrada invalida de cliente e erro DELE (4xx). Deixar o psycopg estourar
    devolvia 500, que diz "a culpa foi nossa" e nao diz qual campo estava
    errado, entao o usuario nao tinha o que corrigir.
    """
    v = _vazio_e_nulo(v)
    if v is None:
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"{campo} precisa ser um número") from e


def _instante(v: Any, campo: str) -> Any:
    """Aceita `14:00`, `2026-08-29T14:00` ou ISO completo. Vazio vira NULL.

    A coluna e `timestamptz`, e a tela pre-preenche o horario com HH:MM, que e o
    que um `<input type="time">` devolve. Mandar "14:00" cru pro Postgres
    derrubava a rota com 500 no CAMINHO FELIZ: bastava o usuario nao apagar o
    valor que a propria tela sugeriu. Hora sozinha e completada com a data de
    HOJE, que e o unico significado possivel pra quem esta na pista agora.
    """
    from datetime import date, datetime

    v = _vazio_e_nulo(v)
    if v is None:
        return None
    texto = str(v).strip()
    try:
        if len(texto) <= 5 and ":" in texto:
            hora = datetime.strptime(texto, "%H:%M").time()
            return datetime.combine(date.today(), hora)
        return datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(
            status_code=422, detail=f"{campo} precisa ser um horário válido (HH:MM ou ISO 8601)"
        ) from e


def _inteiro(v: Any, campo: str) -> int | None:
    n = _numero(v, campo)
    return None if n is None else int(n)


def _um(linha: Any, colunas: list[str]) -> dict:
    return dict(zip(colunas, linha, strict=True)) if linha else {}


def _iso(v: Any) -> Any:
    return v.isoformat() if hasattr(v, "isoformat") else v


def _serializar(linha: tuple, colunas: list[str]) -> dict:
    return {c: _iso(v) if not isinstance(v, UUID) else str(v) for c, v in zip(colunas, linha, strict=True)}


# --- evento --------------------------------------------------------------

EVENTO_COLS = ["id", "track_id", "name", "tipo", "starts_at", "ends_at", "local_date", "created_at"]

TIPOS_DE_EVENTO = ("track_day", "corrida", "teste")


@router.get("/eventos")
def listar_eventos(dono: Dono) -> list[dict]:
    with connect() as conn:
        linhas = conn.execute(
            f"""select e.{', e.'.join(EVENTO_COLS)}, l.nome as layout_nome,
                       (select count(*) from sessao s where s.event_id = e.id) as sessoes
                  from evento e
                  left join layout l on l.id = e.track_id
                 where e.user_id = %s
                 order by e.starts_at desc""",
            (dono,),
        ).fetchall()
    return [_serializar(l, [*EVENTO_COLS, "layout_nome", "sessoes"]) for l in linhas]


@router.post("/eventos", status_code=201)
def criar_evento(corpo: dict, dono: Dono) -> dict:
    for obrigatorio in ("track_id", "name", "starts_at"):
        if not corpo.get(obrigatorio):
            raise HTTPException(status_code=422, detail=f"{obrigatorio} é obrigatório")
    with connect() as conn:
        existe = conn.execute("select 1 from layout where id = %s", (corpo["track_id"],)).fetchone()
        if not existe:
            raise HTTPException(status_code=422, detail="layout não existe no catálogo de pistas")
        tipo = _vazio_e_nulo(corpo.get("tipo"))
        if tipo is not None and tipo not in TIPOS_DE_EVENTO:
            raise HTTPException(
                status_code=422,
                detail=f"tipo de evento tem que ser um de {', '.join(TIPOS_DE_EVENTO)}",
            )
        linha = conn.execute(
            f"""insert into evento (user_id, track_id, name, tipo, starts_at, ends_at, local_date)
                values (%s,%s,%s,%s,%s,%s,%s) returning {', '.join(EVENTO_COLS)}""",
            (dono, corpo["track_id"], corpo["name"], tipo, corpo["starts_at"],
             corpo.get("ends_at"), corpo.get("local_date")),
        ).fetchone()
        # D2-B (29/08): o tipo do evento PRE-MONTA as sessoes a partir de
        # `modelo_sessao` (resposta 1.3 do Vitor: a run sheet importa esse
        # dado). Na mesma transacao: evento sem as sessoes do modelo nao e um
        # estado que exista.
        if tipo is not None:
            conn.execute(
                """insert into sessao (user_id, event_id, type, label)
                   select %s, %s, m.type, m.label
                     from modelo_sessao m
                    where m.tipo_evento = %s
                    order by m.ordem""",
                (dono, linha[0], tipo),
            )
        conn.commit()
    return _serializar(linha, EVENTO_COLS)


@router.patch("/eventos/{evento_id}")
def editar_evento(evento_id: str, corpo: dict, dono: Dono) -> dict:
    # lista branca de coluna: montar SET a partir das chaves do corpo deixaria
    # o cliente escolher qual coluna escrever, user_id inclusive
    editaveis = {"name", "tipo", "starts_at", "ends_at", "local_date", "track_id"}
    campos = {k: v for k, v in corpo.items() if k in editaveis}
    if not campos:
        raise HTTPException(status_code=422, detail="nada para editar")
    sets = ", ".join(f"{k} = %s" for k in campos)
    with connect() as conn:
        linha = conn.execute(
            f"""update evento set {sets}, updated_at = now()
                 where id = %s and user_id = %s returning {', '.join(EVENTO_COLS)}""",
            (*campos.values(), evento_id, dono),
        ).fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        conn.commit()
    return _serializar(linha, EVENTO_COLS)


# --- sessao e bateria ----------------------------------------------------

SESSAO_COLS = ["id", "event_id", "type", "label", "planned_laps", "starts_at", "ends_at"]
BATERIA_COLS = ["id", "session_id", "evento_id", "label", "objective", "laps",
                "fuel_in_l", "fuel_out_l", "started_at", "went_out_at", "created_at"]


@router.get("/eventos/{evento_id}/sessoes")
def listar_sessoes(evento_id: str, dono: Dono) -> list[dict]:
    with connect() as conn:
        linhas = conn.execute(
            f"""select s.{', s.'.join(SESSAO_COLS)},
                       (select count(*) from bateria b where b.session_id = s.id) as baterias,
                       (select count(*) from volta v
                         join gravacao g on g.id = v.session_id
                         join bateria b2 on b2.id = g.bateria_id
                        where b2.session_id = s.id) as voltas
                  from sessao s
                 where s.event_id = %s and s.user_id = %s
                 order by s.starts_at nulls last, s.created_at""",
            (evento_id, dono),
        ).fetchall()
    return [_serializar(l, [*SESSAO_COLS, "baterias", "voltas"]) for l in linhas]


@router.post("/eventos/{evento_id}/sessoes", status_code=201)
def criar_sessao(evento_id: str, corpo: dict, dono: Dono) -> dict:
    tipo = corpo.get("type") or "trackday_battery"
    with connect() as conn:
        # confere o dono do evento ANTES: sem isto o insert dependeria da FK
        # composta pra barrar, e o erro sairia como 500 de constraint
        if not conn.execute(
            "select 1 from evento where id = %s and user_id = %s", (evento_id, dono)
        ).fetchone():
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        try:
            linha = conn.execute(
                f"""insert into sessao (user_id, event_id, type, label, planned_laps,
                                        starts_at, ends_at)
                    values (%s,%s,%s,%s,%s,%s,%s) returning {', '.join(SESSAO_COLS)}""",
                (dono, evento_id, tipo, corpo.get("label"), corpo.get("planned_laps"),
                 corpo.get("starts_at"), corpo.get("ends_at")),
            ).fetchone()
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"sessão inválida: {e}") from e
        conn.commit()
    return _serializar(linha, SESSAO_COLS)


@router.patch("/sessoes/{sessao_id}")
def editar_sessao(sessao_id: str, corpo: dict, dono: Dono) -> dict:
    """Editar o nome (e o resto do administrativo) da sessao (pedido 2.1.1).

    Mesma lista branca de coluna dos outros PATCH: montar SET a partir das
    chaves do corpo deixaria o cliente escolher a coluna, user_id inclusive.
    """
    editaveis = {"label", "type", "planned_laps", "starts_at", "ends_at"}
    campos = {k: v for k, v in corpo.items() if k in editaveis}
    if not campos:
        raise HTTPException(status_code=422, detail="nada para editar")
    sets = ", ".join(f"{k} = %s" for k in campos)
    with connect() as conn:
        linha = conn.execute(
            f"""update sessao set {sets}, updated_at = now()
                 where id = %s and user_id = %s returning {', '.join(SESSAO_COLS)}""",
            (*campos.values(), sessao_id, dono),
        ).fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        conn.commit()
    return _serializar(linha, SESSAO_COLS)


@router.get("/sessoes/{sessao_id}/baterias")
def listar_baterias(sessao_id: str, dono: Dono) -> list[dict]:
    with connect() as conn:
        linhas = conn.execute(
            f"""select b.{', b.'.join(BATERIA_COLS)},
                       (select count(*) from gravacao g where g.bateria_id = b.id) as gravacoes,
                       -- Uma bateria E o conjunto de voltas que a telemetria dela
                       -- mediu. Devolver so a contagem de arquivos faria a tela
                       -- mostrar um registro administrativo em vez do que a
                       -- bateria realmente e. `laps` existe na tabela mas e
                       -- denormalizado e sem trigger de recalculo nesta PoC, entao
                       -- nao serve como fonte: conta na `volta`, que e o fato.
                       (select count(*) from volta v
                         join gravacao g2 on g2.id = v.session_id
                        where g2.bateria_id = b.id) as voltas,
                       (select min(v.lap_time_s) from volta v
                         join gravacao g3 on g3.id = v.session_id
                        where g3.bateria_id = b.id and v.is_valid) as melhor_volta_s
                  from bateria b
                 where b.session_id = %s and b.user_id = %s
                 order by b.went_out_at nulls last, b.created_at""",
            (sessao_id, dono),
        ).fetchall()
    return [
        _serializar(l, [*BATERIA_COLS, "gravacoes", "voltas", "melhor_volta_s"]) for l in linhas
    ]


@router.post("/sessoes/{sessao_id}/baterias", status_code=201)
def criar_bateria(sessao_id: str, corpo: dict, dono: Dono) -> dict:
    with connect() as conn:
        sessao = conn.execute(
            "select event_id from sessao where id = %s and user_id = %s", (sessao_id, dono)
        ).fetchone()
        if not sessao:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        linha = conn.execute(
            f"""insert into bateria (user_id, session_id, evento_id, label, objective,
                                     laps, fuel_in_l, fuel_out_l, started_at, went_out_at)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning {', '.join(BATERIA_COLS)}""",
            (dono, sessao_id, sessao[0], _vazio_e_nulo(corpo.get("label")),
             _vazio_e_nulo(corpo.get("objective")), corpo.get("laps"),
             corpo.get("fuel_in_l"), corpo.get("fuel_out_l"),
             corpo.get("started_at"), corpo.get("went_out_at")),
        ).fetchone()
        conn.commit()
    return _serializar(linha, BATERIA_COLS)


@router.patch("/baterias/{bateria_id}")
def editar_bateria(bateria_id: str, corpo: dict, dono: Dono) -> dict:
    editaveis = {"label", "objective", "laps", "fuel_in_l", "fuel_out_l", "started_at", "went_out_at"}
    campos = {k: v for k, v in corpo.items() if k in editaveis}
    if not campos:
        raise HTTPException(status_code=422, detail="nada para editar")
    sets = ", ".join(f"{k} = %s" for k in campos)
    with connect() as conn:
        linha = conn.execute(
            f"""update bateria set {sets}, updated_at = now()
                 where id = %s and user_id = %s returning {', '.join(BATERIA_COLS)}""",
            (*campos.values(), bateria_id, dono),
        ).fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        conn.commit()
    return _serializar(linha, BATERIA_COLS)


@router.post("/baterias/{bateria_id}/gravacoes/{gravacao_id}", status_code=204)
def vincular_gravacao(bateria_id: str, gravacao_id: str, dono: Dono) -> None:
    """Pendura uma gravacao numa bateria (fase 11, o ciclo).

    `gravacao.bateria_id` e anulavel de proposito (decisao D3: a espinha e
    opcional). Este endpoint e o momento em que o arquivo solto deixa de ser
    solto.
    """
    with connect() as conn:
        if not conn.execute(
            "select 1 from bateria where id = %s and user_id = %s", (bateria_id, dono)
        ).fetchone():
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        linha = conn.execute(
            "select bateria_id from gravacao"
            " where id = %s and user_id = %s",
            (gravacao_id, dono),
        ).fetchone()
        if linha is None:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        bateria_atual = linha[0]
        if bateria_atual is not None and str(bateria_atual) != bateria_id:
            # Pendurar em outra bateria MOVERIA o vinculo (bateria_id e um
            # so), e a bateria antiga perderia a telemetria em silencio. Foi
            # o que aconteceu em producao em 29/08: upload duplicado devolve
            # a MESMA gravacao (dedupe por sha256) e o pendurar automatico
            # ia roubando o arquivo de bateria em bateria, esvaziando as
            # anteriores. Recusar nomeando onde ele esta e o unico
            # comportamento que nao surpreende ninguem.
            onde = conn.execute(
                """select coalesce(s.label, s.type), b.went_out_at
                     from bateria b join sessao s on s.id = b.session_id
                    where b.id = %s""",
                (bateria_atual,),
            ).fetchone()
            if onde and onde[1]:
                rotulo = f"{onde[0]} ({onde[1]:%d/%m %H:%M})"
            elif onde:
                rotulo = str(onde[0])
            else:
                rotulo = "outra bateria"
            raise HTTPException(
                status_code=409,
                detail=(
                    "esta telemetria já está pendurada na bateria de "
                    f"{rotulo}. Cada arquivo pertence a uma bateria só; "
                    "para esta bateria, envie o arquivo dela."
                ),
            )
        atualizadas = conn.execute(
            "update gravacao set bateria_id = %s, piloto_id = null, updated_at = now()"
            " where id = %s and user_id = %s",
            (bateria_id, gravacao_id, dono),
        ).rowcount
        if not atualizadas:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        conn.commit()


@router.delete("/baterias/{bateria_id}/gravacoes/{gravacao_id}", status_code=204)
def desvincular_gravacao(bateria_id: str, gravacao_id: str, dono: Dono) -> None:
    """Solta a gravacao da bateria SEM apagar nada (pedido 2.1.7.2).

    Corrige anexo errado: o arquivo continua no acervo, so deixa de pertencer
    a esta bateria. E o oposto exato do vincular, e nao tem nada de destrutivo:
    quem quer apagar telemetria usa o DELETE da gravacao, que confirma.
    """
    with connect() as conn:
        if not conn.execute(
            "select 1 from bateria where id = %s and user_id = %s", (bateria_id, dono)
        ).fetchone():
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        soltas = conn.execute(
            "update gravacao set bateria_id = null, updated_at = now()"
            " where id = %s and bateria_id = %s and user_id = %s",
            (gravacao_id, bateria_id, dono),
        ).rowcount
        if not soltas:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        conn.commit()


# --- contexto ------------------------------------------------------------

CONTEXTO_COLS = ["id", "bateria_id", "gravacao_id", "pneu_estado", "pneu_voltas_rodadas",
                 "pneu_composto", "temp_ar_c", "temp_pista_c", "vento_kmh", "horario",
                 "notas_piloto", "notas_engenheiro", "criado_em"]


def _dono_do_contexto(conn, tipo: str, alvo: str, dono: UUID) -> None:
    tabela = "bateria" if tipo == "bateria" else "gravacao"
    if tabela == "gravacao":
        achou = conn.execute(
            "select 1 from gravacao where id = %s and user_id = %s",
            (alvo, dono),
        ).fetchone()
    else:
        achou = conn.execute(
            "select 1 from bateria where id = %s and user_id = %s", (alvo, dono)
        ).fetchone()
    if not achou:
        raise HTTPException(status_code=404, detail=NAO_ACHADO)


def _historico_contexto(tipo: str, alvo_id: str, dono: UUID) -> list[dict]:
    """Historico, nao o ultimo (fase 5 do plano).

    Contexto e append-only de proposito: temperatura de pista as 9h e as 14h sao
    dois fatos, nao uma correcao do outro. O front pega `[0]` quando quer o
    atual, e a lista inteira quando quer mostrar o que mudou.
    """
    with connect() as conn:
        _dono_do_contexto(conn, tipo, alvo_id, dono)
        linhas = conn.execute(
            f"""select {', '.join(CONTEXTO_COLS)} from contexto
                 where {tipo}_id = %s order by criado_em desc""",
            (alvo_id,),
        ).fetchall()
    return [_serializar(l, CONTEXTO_COLS) for l in linhas]


def _registrar_contexto(tipo: str, alvo_id: str, corpo: dict, dono: UUID) -> dict:
    pneu = corpo.get("pneu") or {}
    estado = _vazio_e_nulo(pneu.get("estado"))
    if estado is not None and estado not in PNEU_ESTADOS:
        raise HTTPException(
            status_code=422,
            detail=f"estado do pneu tem que ser {' ou '.join(PNEU_ESTADOS)}",
        )
    with connect() as conn:
        _dono_do_contexto(conn, tipo, alvo_id, dono)
        linha = conn.execute(
            f"""insert into contexto ({tipo}_id, pneu_estado, pneu_voltas_rodadas,
                                      pneu_composto, temp_ar_c, temp_pista_c, vento_kmh,
                                      horario, notas_piloto, notas_engenheiro)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                returning {', '.join(CONTEXTO_COLS)}""",
            (alvo_id,
             estado,
             _inteiro(pneu.get("voltas_rodadas"), "voltas rodadas"),
             _vazio_e_nulo(pneu.get("composto")),
             _numero(corpo.get("temperatura_ar_c"), "temperatura do ar"),
             _numero(corpo.get("temperatura_pista_c"), "temperatura da pista"),
             _numero(corpo.get("vento_kmh"), "vento"),
             _instante(corpo.get("horario"), "horário"),
             _vazio_e_nulo(corpo.get("notas_piloto")),
             _vazio_e_nulo(corpo.get("notas_engenheiro"))),
        ).fetchone()
        conn.commit()
    return _serializar(linha, CONTEXTO_COLS)


# --- setup ---------------------------------------------------------------

SETUP_COLS = ["id", "bateria_id", "gravacao_id", "versao", "valores", "notas", "criado_em"]


def _listar_setup(tipo: str, alvo_id: str, dono: UUID) -> list[dict]:
    """Todas as versoes, da mais nova pra mais velha."""
    with connect() as conn:
        _dono_do_contexto(conn, tipo, alvo_id, dono)
        linhas = conn.execute(
            f"""select {', '.join(SETUP_COLS)} from setup
                 where {tipo}_id = %s order by versao desc""",
            (alvo_id,),
        ).fetchall()
    return [_serializar(l, SETUP_COLS) for l in linhas]


def _salvar_setup(tipo: str, alvo_id: str, corpo: dict, dono: UUID) -> dict:
    """Salvar cria VERSAO NOVA, nunca sobrescreve.

    Editar a ficha em cima da anterior apagaria a resposta de "o que mudou entre
    a bateria 2 e a 3", que e metade do valor de guardar setup.
    """
    valores = corpo.get("valores")
    if not isinstance(valores, dict):
        raise HTTPException(status_code=422, detail="valores tem que ser um objeto")
    # campo em branco da ficha nao vira `""` no JSONB: some, porque chave com
    # valor vazio depois aparece na tela como se o engenheiro tivesse anotado
    # alguma coisa
    valores = {k: v for k, v in valores.items() if _vazio_e_nulo(v) is not None}
    with connect() as conn:
        _dono_do_contexto(conn, tipo, alvo_id, dono)
        proxima = conn.execute(
            f"select coalesce(max(versao), 0) + 1 from setup where {tipo}_id = %s", (alvo_id,)
        ).fetchone()[0]
        from psycopg.types.json import Jsonb

        linha = conn.execute(
            f"""insert into setup (user_id, {tipo}_id, versao, valores, notas)
                values (%s,%s,%s,%s,%s) returning {', '.join(SETUP_COLS)}""",
            (dono, alvo_id, proxima, Jsonb(valores), corpo.get("notas")),
        ).fetchone()
        conn.commit()
    return _serializar(linha, SETUP_COLS)


# --- contexto e setup: os 8 caminhos explicitos --------------------------
#
# Escritos um a um em vez de `/{tipo}s/...` com o tipo na URL. O parametro
# geraria "/api/gravacaos/..." (plural errado) e, pior, competiria com
# "/api/gravacoes/{id}/amostras" na resolucao de rota do FastAPI: um caminho
# que casa dois padroes e bug esperando a hora certa.


@router.get("/baterias/{alvo_id}/contexto")
def contexto_da_bateria(alvo_id: str, dono: Dono) -> list[dict]:
    return _historico_contexto("bateria", alvo_id, dono)


@router.post("/baterias/{alvo_id}/contexto", status_code=201)
def registrar_contexto_da_bateria(alvo_id: str, corpo: dict, dono: Dono) -> dict:
    return _registrar_contexto("bateria", alvo_id, corpo, dono)


@router.get("/gravacoes/{alvo_id}/contexto")
def contexto_da_gravacao(alvo_id: str, dono: Dono) -> list[dict]:
    return _historico_contexto("gravacao", alvo_id, dono)


@router.post("/gravacoes/{alvo_id}/contexto", status_code=201)
def registrar_contexto_da_gravacao(alvo_id: str, corpo: dict, dono: Dono) -> dict:
    return _registrar_contexto("gravacao", alvo_id, corpo, dono)


@router.get("/baterias/{alvo_id}/setup")
def setup_da_bateria(alvo_id: str, dono: Dono) -> list[dict]:
    return _listar_setup("bateria", alvo_id, dono)


@router.post("/baterias/{alvo_id}/setup", status_code=201)
def salvar_setup_da_bateria(alvo_id: str, corpo: dict, dono: Dono) -> dict:
    return _salvar_setup("bateria", alvo_id, corpo, dono)


@router.get("/gravacoes/{alvo_id}/setup")
def setup_da_gravacao(alvo_id: str, dono: Dono) -> list[dict]:
    return _listar_setup("gravacao", alvo_id, dono)


@router.post("/gravacoes/{alvo_id}/setup", status_code=201)
def salvar_setup_da_gravacao(alvo_id: str, corpo: dict, dono: Dono) -> dict:
    return _salvar_setup("gravacao", alvo_id, corpo, dono)


def _dono_do_registro_de_contexto(conn, contexto_id: str, dono: UUID) -> None:
    """404 quando o registro nao existe ou o pai (bateria/gravacao) nao e seu."""
    achou = conn.execute(
        """select 1 from contexto c
             left join bateria b on b.id = c.bateria_id
             left join gravacao g on g.id = c.gravacao_id
            where c.id = %s
              and (b.user_id = %s or g.user_id = %s)""",
        (contexto_id, dono, dono),
    ).fetchone()
    if not achou:
        raise HTTPException(status_code=404, detail=NAO_ACHADO)


@router.patch("/contexto/{contexto_id}")
def editar_contexto(contexto_id: str, corpo: dict, dono: Dono) -> dict:
    """Corrige um registro de contexto (pedido de 29/08).

    O historico continua sendo a regra (temperatura das 9h e das 14h sao dois
    fatos), mas dedo errado nao e fato: registro com 32 graus digitado como 320
    tem que poder ser corrigido sem virar um terceiro registro.
    """
    pneu = corpo.get("pneu") or {}
    estado = _vazio_e_nulo(pneu.get("estado"))
    if estado is not None and estado not in PNEU_ESTADOS:
        raise HTTPException(
            status_code=422,
            detail=f"estado do pneu tem que ser {' ou '.join(PNEU_ESTADOS)}",
        )
    with connect() as conn:
        _dono_do_registro_de_contexto(conn, contexto_id, dono)
        linha = conn.execute(
            f"""update contexto set pneu_estado = %s, pneu_voltas_rodadas = %s,
                       pneu_composto = %s, temp_ar_c = %s, temp_pista_c = %s,
                       vento_kmh = %s, horario = %s, notas_piloto = %s,
                       notas_engenheiro = %s
                 where id = %s returning {', '.join(CONTEXTO_COLS)}""",
            (estado,
             _inteiro(pneu.get("voltas_rodadas"), "voltas rodadas"),
             _vazio_e_nulo(pneu.get("composto")),
             _numero(corpo.get("temperatura_ar_c"), "temperatura do ar"),
             _numero(corpo.get("temperatura_pista_c"), "temperatura da pista"),
             _numero(corpo.get("vento_kmh"), "vento"),
             _instante(corpo.get("horario"), "horário"),
             _vazio_e_nulo(corpo.get("notas_piloto")),
             _vazio_e_nulo(corpo.get("notas_engenheiro")),
             contexto_id),
        ).fetchone()
        conn.commit()
    return _serializar(linha, CONTEXTO_COLS)


@router.delete("/contexto/{contexto_id}", status_code=204)
def excluir_contexto(contexto_id: str, dono: Dono) -> None:
    with connect() as conn:
        _dono_do_registro_de_contexto(conn, contexto_id, dono)
        conn.execute("delete from contexto where id = %s", (contexto_id,))
        conn.commit()


@router.patch("/setup/{setup_id}")
def editar_setup(setup_id: str, corpo: dict, dono: Dono) -> dict:
    """Corrige uma versao da ficha EM CIMA dela, sem criar versao nova.

    Salvar continua criando versao por default (o historico e metade do valor
    da ficha); isto aqui existe pro dedo errado, nao pra evolucao de setup.
    """
    valores = corpo.get("valores")
    if valores is not None and not isinstance(valores, dict):
        raise HTTPException(status_code=422, detail="valores tem que ser um objeto")
    with connect() as conn:
        sets, params = ["notas = %s"], [corpo.get("notas")]
        if valores is not None:
            from psycopg.types.json import Jsonb

            valores = {k: v for k, v in valores.items() if _vazio_e_nulo(v) is not None}
            sets.append("valores = %s")
            params.append(Jsonb(valores))
        linha = conn.execute(
            f"""update setup set {', '.join(sets)}
                 where id = %s and user_id = %s returning {', '.join(SETUP_COLS)}""",
            (*params, setup_id, dono),
        ).fetchone()
        if not linha:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        conn.commit()
    return _serializar(linha, SETUP_COLS)


@router.delete("/setup/{setup_id}", status_code=204)
def excluir_setup(setup_id: str, dono: Dono) -> None:
    with connect() as conn:
        apagadas = conn.execute(
            "delete from setup where id = %s and user_id = %s", (setup_id, dono)
        ).rowcount
        if not apagadas:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        conn.commit()


# --- trechos e pistas ----------------------------------------------------


@router.get("/layouts")
def listar_layouts() -> list[dict]:
    """Catalogo de pistas, pro seletor de evento.

    O `alias_layout` NAO entra aqui de proposito: ele e de-para de nome de
    arquivo pra layout (o resolvedor de pista usa), nao lista de escolha do
    usuario. O defeito do saru-app era exatamente esse vazamento, o dropdown
    listava o alias como se fosse pista separada. Aqui a lista sai de `layout`,
    e `layout` nao tem duplicata (conferido: 24 linhas, zero nome repetido).
    """
    with connect() as conn:
        linhas = conn.execute(
            """select l.id, l.nome, l.comprimento_m, p.nome as pista_nome, p.cidade
                 from layout l left join pista p on p.id = l.pista_id
                order by p.nome nulls last, l.nome"""
        ).fetchall()
    return [
        {"id": i, "nome": n, "comprimento_m": float(c) if c is not None else None,
         "pista_nome": pn, "cidade": cid}
        for i, n, c, pn, cid in linhas
    ]


@router.get("/layouts/{layout_id}/trechos")
def listar_trechos(layout_id: str) -> list[dict]:
    """Curvas catalogadas do layout (fase 6).

    Inicio e fim vem de `segmento`, nao de `curva`: curva e subtipo, e os dois
    pontos sao do supertipo. So o apex e da curva.

    Sai tambem dentro do `Relatorio`, mas la vem com PERDA junto, calculada
    contra o par em escopo. Aqui e so o catalogo: serve o seletor antes de
    existir volta pra comparar.
    """
    with connect() as conn:
        linhas = conn.execute(
            """select c.segmento_id, c.corner_id, c.label, s.s_inicio_m, s.s_fim_m, c.s_apex_m
                 from curva c join segmento s on s.id = c.segmento_id
                where c.layout_id = %s order by s.s_inicio_m""",
            (layout_id,),
        ).fetchall()
    return [
        {"id": str(sid), "rotulo": label or corner, "s_inicio_m": float(a),
         "s_fim_m": float(b), "apex_m": float(x) if x is not None else None}
        for sid, corner, label, a, b, x in linhas
    ]


# --- exclusao (29/08) -----------------------------------------------------
#
# Regra que atravessa os quatro DELETE: telemetria NUNCA morre por tabela.
# Excluir evento/sessao/bateria e apagar REGISTRO ADMINISTRATIVO; a gravacao
# pendurada e DESPENDURADA (bateria_id = null) e continua analisavel como
# arquivo solto (decisao D3). So o DELETE explicito da gravacao apaga a
# gravacao, e ai apaga TUDO que deriva dela, na ordem que as FKs sem cascade
# exigem (cascade silencioso em tabela de derivado foi vetado no catalogo em
# 28/08 de proposito: apagar em cadeia tem que ser decisao de codigo, nao
# efeito colateral). Os bytes em disco (upload e Parquet) ficam: sao
# enderecados por conteudo e reingerir o mesmo arquivo os reaproveita; row
# some, byte fica.


def _apagar_baterias(conn, bateria_ids: list) -> None:
    """Apaga baterias ja validadas como do dono, despendurando a telemetria."""
    if not bateria_ids:
        return
    conn.execute(
        "update gravacao set bateria_id = null, updated_at = now()"
        " where bateria_id = any(%s::uuid[])",
        (bateria_ids,),
    )
    for tabela in ("contexto", "setup", "sarue_aviso"):
        conn.execute(
            f"delete from {tabela} where bateria_id = any(%s::uuid[])",  # noqa: S608
            (bateria_ids,),
        )
    conn.execute("delete from bateria where id = any(%s::uuid[])", (bateria_ids,))


@router.delete("/baterias/{bateria_id}", status_code=204)
def excluir_bateria(bateria_id: str, dono: Dono) -> None:
    with connect() as conn:
        if not conn.execute(
            "select 1 from bateria where id = %s and user_id = %s", (bateria_id, dono)
        ).fetchone():
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        _apagar_baterias(conn, [bateria_id])
        conn.commit()


@router.delete("/sessoes/{sessao_id}", status_code=204)
def excluir_sessao(sessao_id: str, dono: Dono) -> None:
    with connect() as conn:
        if not conn.execute(
            "select 1 from sessao where id = %s and user_id = %s", (sessao_id, dono)
        ).fetchone():
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        ids = [
            r[0]
            for r in conn.execute(
                "select id from bateria where session_id = %s", (sessao_id,)
            ).fetchall()
        ]
        _apagar_baterias(conn, ids)
        conn.execute("delete from sessao where id = %s", (sessao_id,))
        conn.commit()


@router.delete("/eventos/{evento_id}", status_code=204)
def excluir_evento(evento_id: str, dono: Dono) -> None:
    with connect() as conn:
        if not conn.execute(
            "select 1 from evento where id = %s and user_id = %s", (evento_id, dono)
        ).fetchone():
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        ids = [
            r[0]
            for r in conn.execute(
                """select b.id from bateria b
                     join sessao s on s.id = b.session_id
                    where s.event_id = %s""",
                (evento_id,),
            ).fetchall()
        ]
        _apagar_baterias(conn, ids)
        conn.execute("delete from sessao where event_id = %s", (evento_id,))
        conn.execute("delete from evento where id = %s", (evento_id,))
        conn.commit()


@router.delete("/gravacoes/{gravacao_id}", status_code=204)
def excluir_gravacao(gravacao_id: str, dono: Dono) -> None:
    """Apaga a gravacao e tudo que deriva dela. E o unico DELETE que toca
    telemetria, e por isso o front SEMPRE confirma antes."""
    with connect() as conn:
        if not conn.execute(
            "select 1 from gravacao where id = %s and user_id = %s",
            (gravacao_id, dono),
        ).fetchone():
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        # derivados de volta, na ordem das FKs sem cascade
        conn.execute(
            """delete from subtracado where tracado_id in
                 (select t.id from tracado t join volta v on v.id = t.volta_id
                   where v.session_id = %s)
                or tracado_ref_id in
                 (select t.id from tracado t join volta v on v.id = t.volta_id
                   where v.session_id = %s)""",
            (gravacao_id, gravacao_id),
        )
        conn.execute(
            """delete from tracado where volta_id in
                 (select id from volta where session_id = %s)""",
            (gravacao_id,),
        )
        conn.execute(
            """delete from tempo_trecho where volta_id in
                 (select id from volta where session_id = %s)""",
            (gravacao_id,),
        )
        conn.execute("delete from volta where session_id = %s", (gravacao_id,))
        # series: canal aponta pra serie, entao ele vai primeiro
        conn.execute("delete from canal_gravado where gravacao_id = %s", (gravacao_id,))
        conn.execute("delete from serie_amostral where gravacao_id = %s", (gravacao_id,))
        for tabela in ("ingestao", "contexto", "setup", "sarue_aviso", "sarue_turno"):
            conn.execute(
                f"delete from {tabela} where gravacao_id = %s",  # noqa: S608
                (gravacao_id,),
            )
        conn.execute("delete from arquivo_bruto where gravacao_id = %s", (gravacao_id,))
        conn.execute("delete from gravacao where id = %s", (gravacao_id,))
        conn.commit()
