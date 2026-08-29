"""Etapa 2: ingestao.

Cada tentativa de ler um `arquivo_bruto` vira uma linha em `ingestao`,
append-only, carregando a versao do leitor e a versao do mapa usadas. Estado
atual e o ultimo sucesso; reprocessar roda de novo e escreve outra linha, nunca
sobrescreve a anterior.

Arquivo sem leitor registrado tambem vira linha, com `status='falhou'` e o
motivo. Isso e de proposito: o silencio e que e o defeito. Um formato que o
sistema reconhece mas nao le tem que aparecer no banco como divida, nao sumir.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from ..acervo import PERFIL_PARA_FORMATO
from ..readers import FORMATOS_POR_ID, LEITORES, leitor_de
from ..storage import caminho_de_uri, escrever_serie

# Invertido do mapa de carga do catalogo: um formato pode ter mais de um perfil
# no futuro (o mesmo container exportado por dois softwares), e ai a escolha
# passa a ser por heuristica. Hoje e 1 pra 1 e a inversao e exata.
FORMATO_PARA_PERFIL = {f: p for p, f in PERFIL_PARA_FORMATO.items()}

SEM_LEITOR = "sem leitor registrado"


@dataclass
class Resultado:
    ingestao_id: str
    status: str
    perfil_id: str | None
    canais_lidos: int = 0
    canais_sem_mapa: int = 0
    amostras_escritas: int = 0
    erro: str | None = None
    series: int = 0
    unidades_divergentes: int = 0


def _registrar(
    conn,
    arquivo_id: str,
    gravacao_id: str,
    perfil_id: str | None,
    leitor_versao: str,
    mapa_versao: str | None,
    status: str,
    iniciada_em: datetime,
    *,
    erro: str | None = None,
    canais: int = 0,
    sem_mapa: int = 0,
    amostras: int = 0,
    perfil_motivo: str | None = None,
) -> str:
    linha = conn.execute(
        """insert into ingestao
             (arquivo_id, gravacao_id, perfil_id, leitor_versao, mapa_versao,
              status, erro, canais_lidos, canais_sem_mapa, amostras_escritas,
              iniciada_em, perfil_motivo, concluida_em)
           values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
           returning id""",
        (
            arquivo_id,
            gravacao_id,
            perfil_id,
            leitor_versao,
            mapa_versao,
            status,
            erro,
            canais,
            sem_mapa,
            amostras,
            iniciada_em,
            perfil_motivo,
        ),
    ).fetchone()
    return str(linha[0])


# Guarda da heuristica de perfil, calibrada em 29/08 contra o acervo inteiro.
#
# Sem guarda, a escolha por maior sobreposicao vira ruido: 58 arquivos `.xrk`
# "venciam" pro perfil `protune` com 2 canais casados de 30 e empate tecnico no
# segundo colocado. Os numeros medidos separam sinal de ruido com folga:
#   acc sobre .ld      39 de 55 canais (71%), margem 38 sobre o segundo
#   gt7_ld sobre .ld   23 de 37 canais (62%), margem 12
#   ruido              2 de 30 canais (7%),  margem 0
COBERTURA_MINIMA = 0.25
MARGEM_MINIMA = 3


def _gravar_metadados(conn, gravacao_id, cabecalho, formato_id) -> None:
    """Sobe pra `gravacao` o que o cabecalho do arquivo declara.

    `venue_declarado` NAO vira `layout_id` aqui. Ele fica em `metadata` como
    declaracao do arquivo, e a resolucao e a etapa 4, com a cascata
    alias > GPS > perguntar. Confundir os dois foi exatamente o B2: o
    `_resolve_track_id` do saru-app devolvia o default do cliente quando o
    arquivo nao declarava venue, sem registrar mismatch nenhum.

    Num bundle, varios arquivos escrevem na mesma gravacao. Cada um guarda o
    que declarou sob a chave do seu formato, entao a divergencia entre irmaos
    fica visivel em vez de o ultimo a escrever vencer em silencio.
    """
    import json

    novo = {
        f"{formato_id}.venue_declarado": cabecalho.venue_declarado,
        f"{formato_id}.capturado_em": cabecalho.capturado_em,
        f"{formato_id}.duracao_s": cabecalho.duracao_s,
        f"{formato_id}.n_canais": len(cabecalho.canais),
        **{f"{formato_id}.{k}": v for k, v in (cabecalho.bruto or {}).items()},
    }
    novo = {k: v for k, v in novo.items() if v is not None}
    conn.execute(
        "update gravacao set metadata = metadata || %s::jsonb, updated_at = now()"
        " where id = %s",
        (json.dumps(novo, ensure_ascii=False, default=str), gravacao_id),
    )
    # duracao_s e capturado_em tambem viram coluna, quando o arquivo declara e a
    # gravacao ainda nao tem: sao consultados direto, nao dentro do jsonb.
    if cabecalho.duracao_s:
        conn.execute(
            "update gravacao set duracao_s = coalesce(duracao_s, %s) where id = %s",
            (cabecalho.duracao_s, gravacao_id),
        )


def _resolver_perfil(conn, formato_id, cabecalho, mapa_versao):
    """Escolhe o perfil de origem pelo vocabulario do arquivo.

    Devolve `(perfil_id, motivo)`. Nao resolver e resultado legitimo e devolve
    `(None, motivo)`: e a regra do B2, onde devolver o default do cliente sem
    conseguir resolver foi o que produziu o bug.
    """
    candidatos = [
        r[0]
        for r in conn.execute(
            "select id from perfil_origem where formato_id = %s order by id",
            (formato_id,),
        )
    ]
    if not candidatos:
        return None, f"nenhum perfil cadastrado para o formato {formato_id}"
    if len(candidatos) == 1:
        return candidatos[0], f"perfil unico do formato {formato_id}"

    lidos = {c.nome_bruto for c in cabecalho.canais}
    if not lidos:
        return None, (
            f"{len(candidatos)} perfis para {formato_id} e o arquivo nao declara "
            "canal: nao da pra resolver por vocabulario"
        )

    placar = []
    for p in candidatos:
        cols = {
            r[0]
            for r in conn.execute(
                """select coluna_bruta from mapeamento_canal
                   where perfil_id = %s and mapa_versao = %s""",
                (p, mapa_versao),
            )
        }
        placar.append((len(lidos & cols), p))
    placar.sort(reverse=True)
    (n_top, top), (n_seg, _) = placar[0], placar[1]
    cobertura = n_top / len(lidos)
    margem = n_top - n_seg

    if cobertura < COBERTURA_MINIMA or margem < MARGEM_MINIMA:
        return None, (
            f"nao resolvido entre {len(candidatos)} perfis: melhor foi {top} com "
            f"{n_top} de {len(lidos)} canais ({cobertura:.0%}, minimo "
            f"{COBERTURA_MINIMA:.0%}), margem {margem} (minimo {MARGEM_MINIMA})"
        )
    return top, (
        f"{top} por sobreposicao de vocabulario: {n_top} de {len(lidos)} canais "
        f"({cobertura:.0%}), margem {margem} sobre o segundo"
    )


def _mapa_do_perfil(conn, perfil_id: str | None, mapa_versao: str) -> dict[str, tuple]:
    """Coluna bruta -> (canal canonico, unidade que o mapa espera).

    A chave e a coluna bruta porque e ela que resolve: N nomes de fabricante
    caem no mesmo canal do dominio (decisao do Lucas de 29/08, migration 007).
    """
    if perfil_id is None:
        return {}
    return {
        r[0]: (r[1], r[2])
        for r in conn.execute(
            """select coluna_bruta, canal_canonico_id, unidade_entrada
               from mapeamento_canal where perfil_id = %s and mapa_versao = %s""",
            (perfil_id, mapa_versao),
        )
    }


def _escrever_canais(
    conn, gravacao_id, cabecalho, mapa: dict[str, tuple]
) -> tuple[int, int]:
    """Cataloga os canais do arquivo. Devolve (sem mapa, unidade divergente).

    `serie_id` fica nulo: o canal foi catalogado, a amostra nao foi
    materializada ainda (migration 008).

    Num bundle, os arquivos dividem a mesma gravacao, entao o `on conflict`
    atualiza em vez de duplicar. E tambem o que permite reprocessar com leitor
    melhor e ver o inventario melhorar no lugar.
    """
    sem_mapa = divergentes = 0
    for c in cabecalho.canais:
        canonico, unidade_esperada = mapa.get(c.nome_bruto, (None, None))
        if canonico is None:
            sem_mapa += 1
        # Unidade declarada pelo arquivo contra a que o mapa espera. Divergir
        # nao bloqueia: fica marcado pra quem for confiar no numero saber.
        divergente = bool(
            canonico is not None
            and c.unidade_declarada
            and unidade_esperada
            and c.unidade_declarada.strip().lower() != unidade_esperada.strip().lower()
        )
        divergentes += divergente
        conn.execute(
            """insert into canal_gravado
                 (gravacao_id, nome_bruto, unidade_declarada, frequencia_hz,
                  n_amostras, valor_min, valor_max, canal_canonico_id, serie_id,
                  unidade_divergente)
               values (%s,%s,%s,%s,%s,%s,%s,%s, null, %s)
               on conflict (gravacao_id, nome_bruto) do update set
                 unidade_declarada = excluded.unidade_declarada,
                 frequencia_hz     = excluded.frequencia_hz,
                 n_amostras        = excluded.n_amostras,
                 valor_min         = excluded.valor_min,
                 valor_max         = excluded.valor_max,
                 canal_canonico_id = excluded.canal_canonico_id,
                 unidade_divergente = excluded.unidade_divergente""",
            (
                gravacao_id,
                c.nome_bruto,
                c.unidade_declarada,
                c.frequencia_hz,
                c.n_amostras,
                c.valor_min,
                c.valor_max,
                canonico,
                divergente,
            ),
        )
    return sem_mapa, divergentes


def ingerir(conn, arquivo_id: str, *, mapa_versao: str = "2026.08-1") -> Resultado:
    """Tenta ler um arquivo bruto e registra a tentativa, deu certo ou nao."""
    iniciada_em = datetime.now(UTC)
    linha = conn.execute(
        """select gravacao_id, formato_id, objeto_uri, nome_arquivo
           from arquivo_bruto where id = %s""",
        (arquivo_id,),
    ).fetchone()
    if linha is None:
        raise ValueError(f"arquivo_bruto {arquivo_id} nao existe")
    gravacao_id, formato_id, objeto_uri, _nome = linha
    # Perfil so pode ser resolvido depois de ler o cabecalho: e o vocabulario
    # do arquivo que decide, nao o container.
    perfil_id: str | None = None
    perfil_motivo = "nao chegou a inspecionar"

    leitor = leitor_de(formato_id)
    if leitor is None:
        fmt = FORMATOS_POR_ID.get(formato_id)
        rotulo = fmt.rotulo if fmt else formato_id
        erro = (
            f"{SEM_LEITOR} para {formato_id} ({rotulo}). "
            f"{len(LEITORES)} leitor(es) registrado(s) no total."
        )
        ing = _registrar(
            conn,
            arquivo_id,
            str(gravacao_id),
            perfil_id,
            "nenhum",
            None,
            "falhou",
            iniciada_em,
            erro=erro,
        )
        return Resultado(ing, "falhou", perfil_id, erro=erro)

    caminho = caminho_de_uri(objeto_uri)
    ponteiros = []
    try:
        cabecalho = leitor.inspecionar(caminho)
        # Nesta fase os leitores fazem inventario. Quem ja suportar amostra
        # escreve Parquet no mesmo passo, sem mudar mais nada aqui.
        if leitor.suporta_amostra:
            ponteiros = escrever_serie(str(gravacao_id), leitor.ler(caminho))
    except Exception as e:  # noqa: BLE001
        erro = f"{type(e).__name__}: {e}"
        ing = _registrar(
            conn,
            arquivo_id,
            str(gravacao_id),
            perfil_id,
            leitor.versao,
            None,
            "falhou",
            iniciada_em,
            erro=erro,
            perfil_motivo=perfil_motivo,
        )
        return Resultado(ing, "falhou", perfil_id, erro=erro)

    _gravar_metadados(conn, gravacao_id, cabecalho, formato_id)
    perfil_id, perfil_motivo = _resolver_perfil(
        conn, formato_id, cabecalho, mapa_versao
    )
    mapa = _mapa_do_perfil(conn, perfil_id, mapa_versao)
    sem_mapa, divergentes = _escrever_canais(conn, gravacao_id, cabecalho, mapa)
    amostras = sum(p.linhas for p in ponteiros)

    for p in ponteiros:
        linha_serie = conn.execute(
            """insert into serie_amostral
                 (gravacao_id, camada, frequencia_hz, mapa_versao, uri,
                  formato_armazenamento, linhas, bytes, sha256, t_inicio_s, t_fim_s,
                  escrito_em)
               values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
               on conflict (sha256) do nothing
               returning id""",
            (
                gravacao_id,
                p.camada,
                p.frequencia_hz,
                p.mapa_versao,
                p.uri,
                p.formato_armazenamento,
                p.linhas,
                p.bytes_,
                p.sha256,
                p.t_inicio_s,
                p.t_fim_s,
            ),
        ).fetchone()
        if linha_serie is None:
            # Objeto ja existia: o Parquet e enderecado por conteudo, entao
            # reprocessar com o mesmo resultado cai aqui e a serie e a mesma.
            linha_serie = conn.execute(
                "select id from serie_amostral where sha256 = %s", (p.sha256,)
            ).fetchone()
        if linha_serie is None:
            continue
        # Liga o canal ao objeto onde os valores dele moram. Ate a serie
        # existir, `serie_id` fica nulo e o canal esta so catalogado
        # (migration 008). A ligacao e por taxa nativa porque e assim que o
        # Parquet foi particionado: um objeto por taxa.
        conn.execute(
            """update canal_gravado set serie_id = %s
               where gravacao_id = %s and frequencia_hz = %s and serie_id is null""",
            (linha_serie[0], gravacao_id, p.frequencia_hz),
        )

    # `ok` exige as duas coisas: amostra materializada e vocabulario inteiro
    # traduzido. Inventario sem amostra e sucesso parcial, e dizer isso e o
    # ponto: um formato catalogado mas nao lido continua sendo divida.
    status = "ok" if (leitor.suporta_amostra and not sem_mapa) else "parcial"
    ing = _registrar(
        conn,
        arquivo_id,
        str(gravacao_id),
        perfil_id,
        leitor.versao,
        mapa_versao,
        status,
        iniciada_em,
        canais=len(cabecalho.canais),
        sem_mapa=sem_mapa,
        amostras=amostras,
        perfil_motivo=perfil_motivo,
    )
    return Resultado(
        ing,
        status,
        perfil_id,
        canais_lidos=len(cabecalho.canais),
        canais_sem_mapa=sem_mapa,
        amostras_escritas=amostras,
        series=len(ponteiros),
        unidades_divergentes=divergentes,
    )
