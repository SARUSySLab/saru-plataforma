"""Rotas da visao de campeonato (live timing externo).

Duas metades com credenciais DIFERENTES, de proposito:
  - escrita (`POST /ingest`): so usuario maquina, via token de API. E o relay
    na rede local do autodromo postando o XML do Orbits.
  - leitura (estado, SSE, tracado, historico): so humano logado (`Dono`).

A leitura NAO filtra por dono, e isso e decisao e nao esquecimento (registro
pra regra esc.3): live timing e o placar publico do autodromo, dado do evento,
nao acervo de uma conta. Nao ha user_id em lt_* pra vazar entre contas.

O transporte ao vivo e SSE (decisao do Lucas, 29/08): o servidor empurra o
estado quando chega snapshot novo, com heartbeat pra atravessar proxy. O
front cai pra poll se o EventSource morrer.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from .. import livetiming
from ..auth import (
    Dono,
    Maquina,
    criar_maquina,
    exigir_gestor,
    listar_maquinas,
    revogar_maquina,
)
from ..db import connect

router = APIRouter(prefix="/api/campeonato", tags=["campeonato"])

# corpo maior que isso nao e um resultspage de cronometragem, e abuso: o XML
# real de 84 carros tem ~91 KB
_LIMITE_XML = 2 * 1024 * 1024


@router.post("/ingest", status_code=201)
async def ingest(maquina: Maquina, request: Request) -> dict:
    corpo = await request.body()
    if len(corpo) > _LIMITE_XML:
        raise HTTPException(status_code=413, detail="XML maior que o limite de 2 MB")
    if not corpo.strip():
        raise HTTPException(status_code=422, detail="corpo vazio")
    try:
        with connect() as conn:
            resultado = livetiming.ingerir(conn, corpo, maquina)
            conn.commit()
    except livetiming.XmlInvalido as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return resultado


@router.get("/eventos")
def listar_eventos(dono: Dono) -> list[dict]:
    with connect() as conn:
        return livetiming.eventos(conn)


def _estado_ou_404(evento_id: UUID) -> dict[str, Any]:
    with connect() as conn:
        corpo = livetiming.estado(conn, evento_id)
    if corpo is None:
        raise HTTPException(
            status_code=404, detail="evento de cronometragem não encontrado"
        )
    return corpo


@router.get("/{evento_id}/estado")
def estado(evento_id: UUID, dono: Dono) -> dict:
    return _estado_ou_404(evento_id)


@router.post("/{evento_id}/avisos/ingest", status_code=201)
async def ingest_avisos(evento_id: UUID, maquina: Maquina, request: Request) -> dict:
    """Feed `announcements` do MyLaps: track limits e penalidades.

    Rota separada da ingestao principal porque o feed e OUTRO arquivo no relay
    (`announcements.xml`), sem os labels de evento que o resultspage tem. Por
    isso o evento vem no caminho, e nao do proprio XML.
    """
    corpo = await request.body()
    if len(corpo) > _LIMITE_XML:
        raise HTTPException(status_code=413, detail="XML maior que o limite de 2 MB")
    if not corpo.strip():
        raise HTTPException(status_code=422, detail="corpo vazio")
    _estado_ou_404(evento_id)
    try:
        with connect() as conn:
            resultado = livetiming.ingerir_avisos(conn, evento_id, corpo)
            conn.commit()
    except livetiming.XmlInvalido as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return resultado


@router.get("/{evento_id}/avisos")
def avisos(evento_id: UUID, dono: Dono) -> dict:
    """Avisos recentes e track limits por carro, pro painel do box."""
    _estado_ou_404(evento_id)
    with connect() as conn:
        return livetiming.ler_avisos(conn, evento_id)


@router.get("/{evento_id}/voltas")
def voltas(evento_id: UUID, dono: Dono) -> list[dict]:
    _estado_ou_404(evento_id)
    with connect() as conn:
        return livetiming.voltas_do_evento(conn, evento_id)


@router.get("/{evento_id}/tracado")
def tracado(evento_id: UUID, dono: Dono) -> dict:
    """Tracado de referencia do layout do evento, pro mapa dos carrinhos.

    Vem do acervo de telemetria: a linha medida de uma volta real naquela
    pista (tabela `tracado`, tipo 'medido'). Sem layout resolvido ou sem
    volta com GPS no acervo, a resposta DECLARA o que falta em vez de
    desenhar outra pista (regra do B2).
    """
    corpo = _estado_ou_404(evento_id)
    layout_id = corpo["evento"]["layout_id"]
    if not layout_id:
        return {
            "disponivel": False,
            "motivo": (
                f"pista da cronometragem ({corpo['evento']['pista_nome'] or 'sem nome'}) "
                "não resolvida pra um layout do catálogo"
            ),
            "pontos": [],
        }
    with connect() as conn:
        linha = conn.execute(
            """select uri, n_pontos from tracado
                where layout_id = %s and tipo = 'medido'
                order by n_pontos desc, criado_em desc limit 1""",
            (layout_id,),
        ).fetchone()
        comprimento = conn.execute(
            "select comprimento_m from layout where id = %s", (layout_id,)
        ).fetchone()
    if linha is None:
        return {
            "disponivel": False,
            "motivo": "nenhuma volta com GPS deste layout no acervo pra desenhar o traçado",
            "pontos": [],
        }

    import pyarrow.parquet as pq

    from ..storage import caminho_de_uri

    tabela = pq.read_table(caminho_de_uri(linha[0])).to_pydict()
    pontos = list(zip(tabela["x_m"], tabela["y_m"], tabela["s_m"], strict=False))
    # ~800 pontos: com 400 a polilinha aparecia na ANIMACAO (o carrinho anda
    # sobre ela e denuncia segmento longo como tremida, feedback de 29/08);
    # pro desenho estatico 400 bastavam
    passo = max(1, len(pontos) // 800)
    amostrado = pontos[::passo]
    return {
        "disponivel": True,
        "motivo": None,
        "layout_id": layout_id,
        "comprimento_m": float(comprimento[0]) if comprimento else None,
        "pontos": [
            {"x": float(x), "y": float(y), "s_m": float(s)} for x, y, s in amostrado
        ],
    }


@router.get("/{evento_id}/stream")
async def stream(evento_id: UUID, dono: Dono, request: Request) -> StreamingResponse:
    """SSE: um evento `estado` na conexao e a cada snapshot novo.

    O produtor real e o relay postando no /ingest; aqui e um watch barato no
    Postgres (id do ultimo snapshot, 1 consulta/s) que so serializa o estado
    completo quando ele mudou. Heartbeat como comentario SSE a cada ~15 s
    mantem proxy e LB acordados sem acordar o front.
    """
    _estado_ou_404(evento_id)

    def _ultimo_snapshot() -> str | None:
        with connect() as conn:
            linha = conn.execute(
                """select id from lt_snapshot where evento_id = %s
                    order by recebido_em desc limit 1""",
                (evento_id,),
            ).fetchone()
        return str(linha[0]) if linha else None

    async def corpo():
        visto: str | None = ""
        sem_novidade = 0
        while not await request.is_disconnected():
            atual = await asyncio.to_thread(_ultimo_snapshot)
            if atual != visto:
                visto = atual
                estado_atual = await asyncio.to_thread(_estado_ou_404, evento_id)
                yield f"event: estado\ndata: {json.dumps(estado_atual, ensure_ascii=False)}\n\n"
                sem_novidade = 0
            else:
                sem_novidade += 1
                if sem_novidade % 15 == 0:
                    yield ": heartbeat\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(
        corpo(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- gestao de maquinas ---------------------------------------------------
#
# Mora aqui, e nao em rotas/auth.py, porque o campeonato e quem consome a
# credencial: quem chega pra configurar o relay encontra tudo no mesmo lugar.


@router.post("/maquinas", status_code=201)
def nova_maquina(corpo: dict, dono: Dono) -> dict:
    exigir_gestor(dono)
    nome = str(corpo.get("nome") or "").strip()
    if not nome:
        raise HTTPException(
            status_code=422, detail="dê um nome à máquina (ex.: relay-mbr)"
        )
    return criar_maquina(nome, dono)


@router.get("/maquinas")
def maquinas(dono: Dono) -> list[dict]:
    exigir_gestor(dono)
    return listar_maquinas()


@router.delete("/maquinas/{maquina_id}", status_code=204)
def revogar(maquina_id: UUID, dono: Dono) -> None:
    exigir_gestor(dono)
    if not revogar_maquina(maquina_id):
        raise HTTPException(
            status_code=404, detail="máquina não encontrada ou já revogada"
        )
