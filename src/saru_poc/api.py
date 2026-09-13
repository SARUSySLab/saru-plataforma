"""Camada HTTP da PoC.

Serve o que o front consome (relatorio e serie de amostras, nos shapes de
`web/src/types/contract.ts`) e recebe upload de bundle. Porta 8010, que e o
alvo que `web/vite.config.ts` ja proxia em `/api`, entao pro browser tudo sai da
mesma origem e nao ha CORS pra configurar.

Desde a integracao com o front (29/08) ela tambem monta o app inteiro: as
rotas por area vivem em `rotas/` e sao incluidas aqui. Este arquivo continua
sendo o unico lugar que decide **o que e publico**, e a lista e curta: saude,
`/api/auth/registro` e `/api/auth/login`. Todo o resto exige `Dono`.

Tres coisas que esta camada NAO faz, de proposito:

1. **Nao calcula nada.** Todo numero vem das etapas do pipeline. Se um numero
   precisar aparecer aqui, ele nasceu no lugar errado.
2. **Nao inventa shape.** As respostas de leitura saem exatamente como
   `relatorio.montar` e `relatorio.amostras` devolvem, e o teste de contrato
   valida contra o `contract.ts`. Um `response_model` do pydantic aqui seria uma
   TERCEIRA declaracao do mesmo contrato (TS, pydantic, e a montagem), e a
   terceira e a que ninguem lembra de atualizar.
3. **Nao processa o bundle dentro do request.** Ver `POST /api/gravacoes`.

A validacao contra o contrato roda a cada resposta de leitura quando
`SARU_VALIDA_CONTRATO=1` (default em dev). E baratissima perto de ler Parquet, e
transforma divergencia de shape em erro 500 explicito no servidor em vez de
tela quebrada no cliente.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import Dono
from .config import CONFIG
from .contrato import carregar, validar
from .db import connect
from .relatorio import (
    ReferenciaDePistaDiferente,
    amostras,
    arquivos_da_captura,
    captura_so_de_inventario,
    montar,
)
from .rotas import auth as rotas_auth
from .rotas import campeonato as rotas_campeonato
from .rotas import clima as rotas_clima
from .rotas import operacao as rotas_operacao
from .rotas import vivo as rotas_vivo
from .rotas import sarue as rotas_sarue

app = FastAPI(
    title="SARU PoC core, track day",
    version="0.1.0",
    description=(
        "Do arquivo do piloto ao insight. Os shapes de leitura sao os de "
        "web/src/types/contract.ts, validados a cada resposta em dev."
    ),
)

VALIDA_CONTRATO = os.getenv("SARU_VALIDA_CONTRATO", "1") == "1"
_TIPOS = None

# Segredo default em producao e o mesmo que nao ter assinatura: qualquer um que
# leia este repo forja um token. Falhar no boot e melhor do que descobrir isso
# pelo log de acesso de outra pessoa.
if CONFIG.em_producao and CONFIG.jwt_secret.startswith("dev-inseguro"):
    raise RuntimeError(
        "SARU_JWT_SECRET nao foi definido e SARU_AMBIENTE=producao. "
        "Gere um: python -c \"import secrets;print(secrets.token_urlsafe(48))\""
    )

app.include_router(rotas_auth.router)
app.include_router(rotas_operacao.router)
app.include_router(rotas_sarue.router)
app.include_router(rotas_clima.router)
app.include_router(rotas_campeonato.router)
app.include_router(rotas_vivo.router)


def _validado(dado: dict, raiz: str) -> dict:
    """Valida a resposta contra o contrato do front antes de mandar."""
    global _TIPOS
    if not VALIDA_CONTRATO:
        return dado
    if _TIPOS is None:
        _TIPOS = carregar()
    erros = validar(dado, raiz, _TIPOS)
    if erros:
        # 500 e o codigo certo: quem errou fomos nos, nao o cliente. E melhor
        # falhar aqui do que entregar um shape que o front vai ler errado.
        raise HTTPException(
            status_code=500,
            detail={
                "erro": f"resposta divergiu do contrato ({raiz})",
                "divergencias": erros[:10],
            },
        )
    return dado


def _minha(conn, gravacao_id: str, dono) -> None:
    """404 se a gravacao nao e sua.

    Existe como funcao porque a regra tem que ser IDENTICA nas rotas de
    leitura. Repetir o WHERE a mao em cada uma e como o filtro some numa delas.

    **Regra de escopo de 29/08 (decisao do Lucas):** gravacao sem dono NAO e
    mais visivel. O `or user_id is null` que dava acesso ao acervo semeado
    saiu de todas as rotas: era o vazamento de acervo entre contas (uma conta
    recem-criada enxergava arquivo de amostra com nome de piloto real).
    """
    achou = conn.execute(
        "select 1 from gravacao where id = %s and user_id = %s",
        (gravacao_id, dono),
    ).fetchone()
    if not achou:
        # 404, nao 403: 403 confirmaria que o id existe
        raise HTTPException(status_code=404, detail="gravação não encontrada")


@app.get("/api/saude")
def saude() -> dict:
    """Ping do banco. Nao mente: se o Postgres nao responde, isto falha."""
    from .db import ping

    return {"ok": True, "postgres": ping().split(",")[0]}


@app.get("/api/gravacoes")
def listar_gravacoes(
    dono: Dono,
    com_volta: Annotated[
        bool, Query(description="so as que ja tem volta cortada (etapa 5)")
    ] = False,
) -> list[dict]:
    """Catalogo de gravacoes, com o que cada uma tem pronto.

    `voltas` e `trechos` sao o que diz se aquela gravacao rende relatorio: sem
    volta nao ha N0 nem N1, sem trecho nao ha N2.

    **Filtro de dono (regra de escopo de 29/08):** SO as suas. O acervo sem
    dono (`user_id is null`) saiu do caminho do usuario: era o material de
    demonstracao da PoC e vazava entre contas (arquivo de amostra com nome de
    piloto real visivel pra conta recem-criada). Quem precisar dele em testes
    adota as gravacoes pro proprio usuario.
    """
    condicoes = ["g.user_id = %s"]
    if com_volta:
        condicoes.append("v.n > 0")
    filtro = "where " + " and ".join(condicoes)
    with connect() as conn:
        linhas = conn.execute(
            f"""select g.id, g.label, g.layout_id, l.nome, g.capturado_em, g.bateria_id,
                       b.session_id, b.evento_id, ev.name as evento_nome,
                       g.duracao_s, v.n as voltas, t.n as trechos, g.finalidade
                  from gravacao g
                  left join layout l on l.id = g.layout_id
                  -- a espinha inteira vem junto: o front precisa saber a que
                  -- evento e sessao a gravacao pertence pra abrir o "Dia de
                  -- pista" no lugar certo. Sem isso as duas telas ficam
                  -- desconexas, e elas sao a mesma coisa vista de dois angulos.
                  left join bateria b on b.id = g.bateria_id
                  left join evento ev on ev.id = b.evento_id
                  left join lateral (
                        select count(*) n from volta where session_id = g.id
                  ) v on true
                  left join lateral (
                        select count(*) n from tempo_trecho tt
                         join volta vv on vv.id = tt.volta_id
                        where vv.session_id = g.id
                  ) t on true
                  {filtro}
                  order by g.capturado_em desc nulls last, g.created_at desc""",
            (dono,),
        ).fetchall()
    return [
        {
            "gravacao_id": str(gid),
            "label": label,
            "layout_id": layout_id,
            "layout_nome": layout_nome,
            "capturado_em": capturado.isoformat() if capturado else None,
            # Deixa o front ligar bateria a gravacao sem uma segunda consulta:
            # o seletor do header troca a bateria e precisa saber qual gravacao
            # abrir no mesmo gesto.
            "bateria_id": str(bateria_id) if bateria_id else None,
            "sessao_id": str(sessao_id) if sessao_id else None,
            "evento_id": str(evento_id) if evento_id else None,
            "evento_nome": evento_nome,
            "duracao_s": float(duracao) if duracao is not None else None,
            "voltas": int(voltas or 0),
            "trechos": int(trechos or 0),
            # D3-B: 'referencia' e arquivo importado so pra comparar; o front
            # nao o oferece como volta analisada nem o poe em agregado
            "finalidade": finalidade,
        }
        for (gid, label, layout_id, layout_nome, capturado, bateria_id, sessao_id,
             evento_id, evento_nome, duracao, voltas, trechos, finalidade) in linhas
    ]


@app.get("/api/relatorio/{gravacao_id}")
def obter_relatorio(
    gravacao_id: str,
    dono: Dono,
    volta: Annotated[int | None, Query(description="volta em escopo")] = None,
    referencia: Annotated[
        str | None,
        Query(description="volta de referencia (numero) ou 'media' das validas"),
    ] = None,
    ref_gravacao: Annotated[
        str | None,
        Query(description="gravacao da referencia, quando for de OUTRA captura"),
    ] = None,
) -> dict:
    """`Relatorio` do contrato, pro par (volta, referencia) em escopo.

    Os dois parametros `volta`/`referencia` existem por decisao do Lucas
    (29/08): as perdas saem calculadas contra ESTE par, e o seletor de escopo
    global do front refaz a busca ao trocar a selecao. Sem eles, trocar a
    volta na tela nao mudava as perdas, e ninguem via porque o front lia
    fixture.

    `ref_gravacao` e a mudanca de contrato de 29/08: quando presente, `referencia`
    passa a ser um numero de volta de OUTRA gravacao (comparar dias e baterias
    diferentes), em vez de um numero de volta desta mesma gravacao. Passa pelo
    MESMO `_minha` que `gravacao_id`, porque o filtro de dono vale pros dois
    lados do par: referencia de outro usuario tem que sumir como 404, nao
    vazar como 403 (a mesma regra que ja vale pra `gravacao_id`).
    """
    with connect() as conn:
        _minha(conn, gravacao_id, dono)
        if ref_gravacao is not None:
            _minha(conn, ref_gravacao, dono)
        try:
            # `referencia` chega como texto porque aceita numero OU a palavra
            # "media" (o seletor de comparacao do front sempre teve as duas).
            ref: int | str | None = referencia
            if isinstance(referencia, str) and referencia.strip():
                if referencia.strip().lower() == "media":
                    ref = "media"
                elif referencia.strip().lstrip("-").isdigit():
                    ref = int(referencia)
                else:
                    raise HTTPException(
                        status_code=422,
                        detail="referencia tem que ser um numero de volta ou 'media'",
                    )
            elif isinstance(referencia, str):
                ref = None
            rel = montar(
                conn,
                gravacao_id,
                volta=volta,
                referencia=ref,
                ref_gravacao_id=ref_gravacao,
            )
        except ReferenciaDePistaDiferente as e:
            # 422, nao 404: os dois lados existem e sao seus, o problema e que
            # a pista e outra e a grade de distancia nao tem correspondencia
            # (a guarda do B2, ver docstring de `ReferenciaDePistaDiferente`).
            raise HTTPException(status_code=422, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
    return _validado(rel, "Relatorio")


@app.get("/api/gravacoes/{gravacao_id}/amostras")
def obter_amostras(
    gravacao_id: str,
    dono: Dono,
    volta: Annotated[
        str, Query(description="numero da volta, ou 'media' pra media das validas")
    ] = "media",
) -> dict:
    """`SerieAmostras` na grade comum de distancia.

    Fica fora do relatorio porque amostra e pesada: o relatorio cabe numa
    resposta e a serie vem sob demanda, uma por volta.
    """
    alvo: int | str = volta
    if volta != "media":
        try:
            alvo = int(volta)
        except ValueError as e:
            raise HTTPException(
                status_code=422, detail="volta tem que ser um numero ou 'media'"
            ) from e
    with connect() as conn:
        _minha(conn, gravacao_id, dono)
        try:
            serie = amostras(conn, gravacao_id, alvo)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
    return _validado(serie, "SerieAmostras")


@app.get("/api/gravacoes/{gravacao_id}/estado")
def estado_da_gravacao(gravacao_id: str, dono: Dono) -> dict:
    """Em que pe esta o processamento, e POR QUE parou onde parou.

    Existe por causa de um defeito de fluxo achado na homologacao de 29/08: a
    tela de envio ficava em "processando" indefinidamente quando o pipeline ja
    havia terminado declarando que NAO conseguia seguir. O servidor sabia o
    motivo (`ingestao.status`, `gravacao.layout_id` nulo, zero volta), e o
    cliente nao tinha como perguntar: `GET /api/gravacoes` so devolve contagem,
    e contagem zero e ambigua entre "ainda processando" e "nao vai dar".

    O caso real era `.xrk` enviado SOZINHO: o venue e o indice de voltas vem nos
    arquivos irmaos do bundle, entao sem eles a pista nao resolve e nao ha por
    onde cortar volta. Isso e resultado legitimo, nao falha, e a diferenca entre
    "espere" e "mande o bundle inteiro" e a unica coisa que o usuario precisa
    saber.
    """
    with connect() as conn:
        _minha(conn, gravacao_id, dono)
        linha = conn.execute(
            """select g.layout_id,
                      (select count(*) from arquivo_bruto a where a.gravacao_id = g.id),
                      (select count(*) from volta v where v.session_id = g.id),
                      (select count(*) from tempo_trecho tt
                         join volta v2 on v2.id = tt.volta_id where v2.session_id = g.id),
                      (select count(*) from ingestao i where i.gravacao_id = g.id
                        and i.status = 'falhou'),
                      (select count(*) from ingestao i2 where i2.gravacao_id = g.id),
                      (select max(i3.erro) from ingestao i3 where i3.gravacao_id = g.id
                        and i3.erro is not null),
                      (select count(*) from ingestao i4 where i4.gravacao_id = g.id
                        and i4.status = 'parcial')
                 from gravacao g where g.id = %s""",
            (gravacao_id,),
        ).fetchone()
        arquivos_cap = arquivos_da_captura(conn, gravacao_id)
    layout, arquivos, voltas, trechos, falhas, ingestoes, erro, parciais = linha

    # Excecao 3e do E-UC-01 (issue #2, PIL-CT-52): a captura foi lida INTEIRA e
    # nenhum arquivo dela virou amostra. E o caso do `.gpk` e do `.rrk`, cujo
    # leitor so faz inventario (PIL-RN-11). Sem esta pergunta, a cascata abaixo
    # culpava a pista, que e verdade menor: a pista nao resolve porque nao ha
    # nada decodificado onde procurar o venue.
    #
    # "Inteira" e exigencia, nao detalhe: a recepcao ingere arquivo a arquivo,
    # com commit entre eles, e sem ela um bundle correto respondia "envie o
    # arquivo principal" no intervalo entre o `.gpk` entrar e o `.xrk` entrar.
    so_inventario = not falhas and captura_so_de_inventario(arquivos_cap)
    formatos_inventario = ", ".join(
        sorted({a.formato_id for a in arquivos_cap if not a.suporta_amostra})
    ) or "deste arquivo"
    if ingestoes == 0:
        ingestao = None
    elif falhas:
        ingestao = {"status": "falhou", "motivo": erro or "a leitura do arquivo falhou"}
    elif parciais:
        ingestao = {
            "status": "parcial",
            "motivo": (
                f"o leitor de {formatos_inventario} lê o cabeçalho e conta os "
                "registros, e não decodifica canal: a gravação entrou só como "
                "inventário"
                if so_inventario
                else "parte dos canais do arquivo ficou sem tradução no vocabulário canônico"
            ),
        }
    else:
        ingestao = {"status": "ok", "motivo": None}

    if ingestoes == 0:
        return {"etapa": "recebido", "concluido": False, "voltas": 0, "trechos": 0,
                "motivo": None, "sugestao": None, "arquivos": arquivos,
                "ingestao": ingestao}
    if falhas and voltas == 0:
        return {"etapa": "ingestao", "concluido": True, "voltas": 0, "trechos": 0,
                "motivo": erro or "a leitura do arquivo falhou",
                "sugestao": "confira se o arquivo não está truncado.", "arquivos": arquivos,
                "ingestao": ingestao}
    if voltas == 0 and so_inventario:
        # Entra ANTES do degrau da pista porque e causa mais especifica: sem
        # canal decodificado nao ha venue pra resolver nem serie pra cortar, e
        # dizer "a pista nao foi resolvida" manda o piloto procurar o problema
        # no lugar errado.
        return {
            "etapa": "ingestao", "concluido": True, "voltas": 0, "trechos": 0,
            "motivo": (
                f"o formato {formatos_inventario} entrou só como inventário: o "
                "leitor lê o cabeçalho e conta os registros, e não decodifica canal"
            ),
            "sugestao": (
                "envie também o arquivo principal do logger, que é o que carrega "
                "as amostras (.xrk no AiM RS2, .ld no MoTeC, .vbo no VBOX). "
                "Sozinhos, o .gpk e o .rrk registram a sessão, e não há canal "
                "nenhum de onde tirar volta ou tempo."
            ),
            "arquivos": arquivos,
            "ingestao": ingestao,
        }
    if voltas == 0:
        # A cascata de causa, do mais especifico pro mais geral. A sugestao e o
        # que diferencia um erro util de um erro decorativo.
        if not layout:
            return {
                "etapa": "resolucao_pista", "concluido": True, "voltas": 0, "trechos": 0,
                "motivo": "a pista não foi resolvida: o arquivo não declara em que autódromo foi gravado",
                "sugestao": (
                    "envie o bundle inteiro do logger, e não só o arquivo principal. "
                    "O nome do autódromo e o índice de voltas costumam vir nos arquivos "
                    "irmãos (.gpk, .rrk, .ldx)." if arquivos <= 1 else
                    "o nome do autódromo declarado no arquivo não bate com nenhuma pista do catálogo."
                ),
                "arquivos": arquivos,
                "ingestao": ingestao,
            }
        return {"etapa": "corte_voltas", "concluido": True, "voltas": 0, "trechos": 0,
                "motivo": "a pista resolveu, mas não foi possível cortar voltas nesta captura",
                "sugestao": ("o arquivo não tem canal de contagem de volta, índice de voltas "
                             "nem GPS utilizável perto da linha de chegada. A gravação fica "
                             "registrada e dá para enviar outro arquivo normalmente."),
                "arquivos": arquivos, "ingestao": ingestao}
    return {"etapa": "pronto", "concluido": True, "voltas": voltas, "trechos": trechos,
            "motivo": None, "sugestao": None, "arquivos": arquivos,
            "ingestao": ingestao}


# --- escrita -------------------------------------------------------------


def _rodar_pipeline(gravacao_id: str, arquivos: list[int]) -> None:
    """Etapas 2 a 6 de uma gravacao recem-recebida.

    Roda fora do request (ver `POST /api/gravacoes`). Cada etapa ja e
    idempotente e ja registra o proprio fracasso no banco, entao aqui nao ha
    tratamento de erro proprio: engolir excecao viraria silencio, e o estado
    real fica em `ingestao`, `volta` e `tempo_trecho`.
    """
    from .pipeline.corte_voltas import cortar
    from .pipeline.decomposicao import decompor_volta
    from .pipeline.ingestao import ingerir
    from .pipeline.resolucao_pista import resolver
    from .pipeline.tracado import derivar_volta

    with connect() as conn:
        for arquivo_id in arquivos:
            ingerir(conn, arquivo_id)
            conn.commit()
        resolver(conn)
        conn.commit()
        cortar(conn, gravacao_id)
        conn.commit()
        voltas = [
            str(r[0])
            for r in conn.execute(
                "select id from volta where session_id = %s order by lap_number",
                (gravacao_id,),
            ).fetchall()
        ]
        for volta_id in voltas:
            decompor_volta(conn, volta_id)
            derivar_volta(conn, volta_id)
            conn.commit()


@app.post("/api/gravacoes", status_code=202)
async def receber_bundle(
    tarefas: BackgroundTasks,
    dono: Dono,
    arquivos: Annotated[list[UploadFile], File(description="bundle da captura")],
    finalidade: Annotated[
        str,
        Form(description="piloto (default) ou referencia: arquivo importado so pra comparar (D3-B)"),
    ] = "piloto",
) -> dict:
    """Recebe o bundle e devolve 202 com o id da gravacao.

    **Por que 202 e nao 201 com o relatorio pronto:** a recepcao (etapa 1) e
    barata, so hash e registro, e cabe no request. O resto nao: o acervo tem
    `.ld` de 400 MB e `.bmsbin` de 920 MB, e ler, normalizar, escrever Parquet,
    cortar volta e decompor levaria o request a estourar qualquer timeout de
    proxy. Entao a recepcao e sincrona (por isso da pra devolver o
    `gravacao_id`) e as etapas 2 a 6 rodam em background.

    O cliente acompanha por `GET /api/gravacoes` (as colunas `voltas` e
    `trechos` saem de zero quando o pipeline avanca) e busca o relatorio quando
    houver volta. Nao ha entidade de "job": o estado real ja mora em `ingestao`,
    que e append-only justamente pra isso.

    (a confirmar com o Lucas: BackgroundTasks morre junto com o processo. Numa
    PoC de uma maquina isso e aceitavel; virar produto pede fila de verdade, que
    e a D8 do desenho do assistente, ja decidida como Redis.)
    """
    from .pipeline.recepcao import agrupar_bundles, receber

    if not arquivos:
        raise HTTPException(status_code=422, detail="nenhum arquivo no bundle")
    if finalidade not in ("piloto", "referencia"):
        raise HTTPException(status_code=422, detail="finalidade tem que ser piloto ou referencia")

    destino = Path(tempfile.mkdtemp(prefix="saru-upload-", dir=CONFIG.data_root))
    caminhos = []
    for enviado in arquivos:
        nome = Path(enviado.filename or "sem-nome").name
        alvo = destino / nome
        with alvo.open("wb") as fh:
            shutil.copyfileobj(enviado.file, fh)
        caminhos.append(alvo)

    # D1 (decisao do Lucas, 29/08, opcao A): o endpoint agrupa como a CLI
    # sempre agrupou. CADA captura vira a sua gravacao; sidecars da mesma
    # captura (mesmo radical de nome) continuam juntos. Antes N arquivos
    # viravam 1 gravacao e o segundo sobrescrevia os canais do primeiro: era
    # o bug das "2 voltas" que o Vitor achou em producao.
    recepcoes = []
    with connect() as conn:
        for bundle in agrupar_bundles(caminhos):
            try:
                recepcao = receber(conn, bundle)
            except ValueError as e:
                # rollback implicito: nada do request vira gravacao pela metade
                raise HTTPException(status_code=422, detail=str(e)) from e
            # o dono e carimbado aqui, no unico momento em que a gravacao
            # nasce por acao de alguem. Gravacao de acervo continua com
            # user_id nulo porque entra pelo CLI, nao por esta rota.
            conn.execute(
                "update gravacao set user_id = %s where id = %s and user_id is null",
                (dono, recepcao.gravacao_id),
            )
            # D3-B: arquivo de REFERENCIA entra marcado na base de comparacao
            # da conta: nunca vira volta analisada nem alimenta agregado. So
            # marca gravacao SUA (upload novo ou dedupe de arquivo seu); o
            # dedupe de gravacao que ja e de trabalho nao rebaixa pra
            # referencia, senao o arquivo sumia da analise.
            if finalidade == "referencia":
                conn.execute(
                    "update gravacao set finalidade = 'referencia'"
                    " where id = %s and user_id = %s and bateria_id is null",
                    (recepcao.gravacao_id, dono),
                )
            recepcoes.append(
                (recepcao, [a.id for a in recepcao.arquivos if a.id is not None])
            )
        conn.commit()

    for recepcao, ids in recepcoes:
        if not recepcao.ja_existia:
            tarefas.add_task(_rodar_pipeline, str(recepcao.gravacao_id), ids)

    novas = sum(1 for r, _ in recepcoes if not r.ja_existia)
    return {
        "gravacoes": [
            {
                "gravacao_id": str(r.gravacao_id),
                "ja_existia": r.ja_existia,
                "arquivos": [
                    {"papel": a.papel, "nome": a.caminho.name, "formato": a.formato_id}
                    for a in r.arquivos
                ],
                "recusados": r.recusados,
            }
            for r, _ in recepcoes
        ],
        "pipeline": "ja processada" if novas == 0 else "rodando em background",
    }


# A rota de contexto morava aqui e mudou pra `rotas/operacao.py`, junto com a
# da bateria: contexto pendura nos dois donos (num_nonnulls = 1) e ter metade
# da regra num arquivo e metade no outro e como a segunda metade envelhece.


@app.post("/api/gravacoes/{gravacao_id}/pista", status_code=202)
def cravar_pista(
    gravacao_id: str,
    corpo: dict,
    tarefas: BackgroundTasks,
    dono: Dono,
) -> dict:
    """O degrau 3 da cascata de resolucao: o usuario CRAVA a pista.

    O plano sempre foi `alias > GPS > perguntar ao usuario`, e o contrato
    reservou `resolucao_pista: "perguntado"` desde o primeiro dia, mas o degrau
    nunca existiu: arquivo sem venue declarado parava em "pista nao resolvida" e
    nao havia por onde seguir. Isso nao e adivinhacao de formato (a regra do
    B2): e o usuario, que estava la, afirmando onde gravou. A resposta dele fica
    marcada como `perguntado` no relatorio, entao a proveniencia nunca se
    disfarça de deteccao automatica.

    Depois de cravar, as etapas 5 e 6 rodam de novo em background: com o
    comprimento do layout passa a existir grade de distancia, e o que estava
    barrado (corte por GPS, decomposicao, tracado) ganha por onde andar.
    """
    layout_id = str(corpo.get("layout_id") or "").strip()
    if not layout_id:
        raise HTTPException(status_code=422, detail="layout_id é obrigatório")
    with connect() as conn:
        _minha(conn, gravacao_id, dono)
        existe = conn.execute("select 1 from layout where id = %s", (layout_id,)).fetchone()
        if not existe:
            raise HTTPException(status_code=422, detail="layout não existe no catálogo de pistas")
        conn.execute(
            """update gravacao set layout_id = %s, layout_origem = 'perguntado',
                      updated_at = now() where id = %s""",
            (layout_id, gravacao_id),
        )
        conn.commit()

    def _reprocessar() -> None:
        from .pipeline.corte_voltas import cortar
        from .pipeline.decomposicao import decompor_volta
        from .pipeline.tracado import derivar_volta

        with connect() as conn2:
            cortar(conn2, gravacao_id, recortar=True)
            conn2.commit()
            voltas = [
                str(r[0])
                for r in conn2.execute(
                    "select id from volta where session_id = %s order by lap_number",
                    (gravacao_id,),
                ).fetchall()
            ]
            for vid in voltas:
                decompor_volta(conn2, vid)
                derivar_volta(conn2, vid)
                conn2.commit()

    tarefas.add_task(_reprocessar)
    return {"gravacao_id": gravacao_id, "layout_id": layout_id, "pipeline": "reprocessando"}


# --- ciclo periodico do Sarue --------------------------------------------
#
# **Decisao: o timer mora no SERVIDOR, nao no front** (fase 9 do plano, que ja
# recomendava isso). Motivo pratico: no front, o timer morre quando a aba
# fecha, roda N vezes com N abas abertas, e some quando o celular do piloto
# bloqueia a tela, que e exatamente quando ele esta na pista.
#
# Implementado como task do asyncio no lifespan, nao Redis. A D8 do desenho do
# assistente ja escolheu Redis, mas aquilo e o produto; esta e a PoC, e aqui
# vale a mesma ressalva que `POST /api/gravacoes` ja declara: morre junto com o
# processo. Numa maquina so isso e aceitavel, e virar produto troca esta funcao
# por um worker, sem mexer em rota nenhuma.

INTERVALO_AVISO_S = 30 * 60


async def _ciclo_de_avisos() -> None:
    """A cada 30 min, um aviso por gravacao com dono que teve contexto novo.

    O filtro por contexto novo e o que evita o Sarue repetir a mesma leitura a
    cada meia hora: sem contexto novo e sem telemetria nova, ele nao tem o que
    dizer de diferente, e aviso repetido treina o piloto a ignorar o box.
    """
    import asyncio

    from .rotas.sarue import gerar_aviso_para

    while True:
        await asyncio.sleep(INTERVALO_AVISO_S)
        try:
            with connect() as conn:
                pendentes = conn.execute(
                    """select g.id, g.user_id
                         from gravacao g
                        where g.user_id is not null
                          and exists (select 1 from contexto c
                                       where c.gravacao_id = g.id
                                         and c.criado_em > now() - interval '30 minutes')
                          and exists (select 1 from volta v where v.session_id = g.id)"""
                ).fetchall()
            for gravacao_id, user_id in pendentes:
                try:
                    await asyncio.to_thread(gerar_aviso_para, str(gravacao_id), user_id)
                except Exception as e:  # noqa: BLE001
                    # uma gravacao que falha nao pode derrubar o ciclo das outras
                    print(f"[sarue] aviso falhou para {gravacao_id}: {e}")
        except Exception as e:  # noqa: BLE001
            print(f"[sarue] ciclo falhou: {e}")


@asynccontextmanager
async def _ciclo_de_vida(_app: FastAPI):
    """Sobe e derruba o ciclo de avisos junto com o app.

    `lifespan` e nao `@app.on_event`: o segundo esta depreciado, e sem o
    cancelamento no fim a task sobrevive ao shutdown e segura o processo.
    """
    import asyncio

    tarefa = None
    if os.getenv("SARU_CICLO_SARUE", "1") == "1" and CONFIG.openrouter_key:
        tarefa = asyncio.create_task(_ciclo_de_avisos())
    elif not CONFIG.openrouter_key:
        print("[sarue] ciclo de avisos desligado: SARU_OPENROUTER_KEY ausente")
    try:
        yield
    finally:
        if tarefa:
            tarefa.cancel()


app.router.lifespan_context = _ciclo_de_vida


# --- front estatico ------------------------------------------------------
#
# **Decisao (Lucas delegou, 29/08): a API serve o front.** Um servico so no
# Railway, um dominio, mesma origem. E o que torna o cookie httpOnly de sessao
# gratuito: sem isso seriam dois dominios, CORS com credenciais e cookie
# cross-site, que os browsers estao fechando.
#
# Montado por ultimo de proposito: e catch-all, e catch-all antes das rotas
# engoliria `/api/...`.

_DIST = REPO_ROOT_WEB = Path(__file__).resolve().parents[2] / "web" / "dist"

if _DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST / "assets"), name="assets")

    @app.get("/{caminho:path}", include_in_schema=False)
    def spa(caminho: str) -> FileResponse:
        """Rota do app pra caminho de navegacao, 404 pra arquivo que nao existe.

        O front e SPA: quem der F5 em `/evento/123` tem que receber o app, e nao
        404. Mas `/logo-que-nao-existe.png` NAO pode receber o app: devolver
        `index.html` com 200 pra um asset ausente faz o `<img>` "carregar" HTML,
        e o erro so aparece como imagem quebrada, sem nenhum sinal de que o
        arquivo nao subiu. Foi assim que um asset faltando passou despercebido
        em 29/08, e um `curl` de verificacao respondeu 200 pra um arquivo que
        nunca existiu.

        A regra: caminho com extensao e ARQUIVO, e arquivo ausente e 404.
        Caminho sem extensao e navegacao, e navegacao recebe o index.
        """
        alvo = _DIST / caminho
        if caminho and alvo.is_file():
            return FileResponse(alvo)
        if caminho and "." in Path(caminho).name:
            raise HTTPException(status_code=404, detail=f"arquivo não encontrado: {caminho}")
        return FileResponse(_DIST / "index.html")
