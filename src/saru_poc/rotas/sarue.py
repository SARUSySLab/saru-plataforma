"""Rotas do Sarue: pergunta livre e aviso periodico (fases 9 e 12).

A regra desta camada e a mesma de `operacao.py`, linha a linha: todo SELECT e
UPDATE que toca dado de usuario carrega `user_id = %s` no WHERE, com o id vindo
de `Dono`, nunca do corpo nem da URL. Recurso de outro dono da 404, nao 403.

O que muda aqui em relacao a `operacao.py` e que o "dado de usuario" e o turno
ou o aviso, nao a gravacao. A gravacao pode ser de acervo (user_id nulo,
visivel a todos, mesma regra de `_dono_do_contexto`), mas o turno e o aviso sao
sempre do dono que perguntou ou que estava logado quando o ciclo rodou.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from psycopg.types.json import Jsonb

from .. import relatorio
from ..auth import Dono
from ..config import CONFIG
from ..db import connect
from ..sarue import SarueIndisponivel, gerar_aviso, montar_base, responder
from .operacao import NAO_ACHADO, _serializar

router = APIRouter(prefix="/api/sarue", tags=["sarue"])


def _dono_da_gravacao(conn, gravacao_id: str, dono: UUID) -> None:
    """Confere se a gravacao e do dono ou de acervo, mesma regra de operacao.py.

    Acervo tem `user_id` nulo e e visivel a todos. Sem esta checagem o Sarue
    responderia sobre gravacao de outra conta so por saber o id.
    """
    achou = conn.execute(
        "select 1 from gravacao where id = %s and user_id = %s",
        (gravacao_id, dono),
    ).fetchone()
    if not achou:
        raise HTTPException(status_code=404, detail=NAO_ACHADO)


def _contextos_da_gravacao(conn, gravacao_id: str) -> list[dict[str, Any]]:
    """Historico de contexto da gravacao, mais novo primeiro.

    `montar_base` so usa `contextos[0]` e `contextos[1]` (atual e anterior),
    mas passar a lista inteira deixa a decisao de quanto usar dentro de
    `sarue.py`, que e onde a base de fatos e definida.
    """
    linhas = conn.execute(
        """select id, bateria_id, gravacao_id, pneu_estado, pneu_voltas_rodadas,
                  pneu_composto, temp_ar_c, temp_pista_c, vento_kmh, horario,
                  notas_piloto, notas_engenheiro, criado_em
             from contexto
            where gravacao_id = %s
            order by criado_em desc""",
        (gravacao_id,),
    ).fetchall()
    colunas = [
        "id", "bateria_id", "gravacao_id", "pneu_estado", "pneu_voltas_rodadas",
        "pneu_composto", "temp_ar_c", "temp_pista_c", "vento_kmh", "horario",
        "notas_piloto", "notas_engenheiro", "criado_em",
    ]
    return [_serializar(l, colunas) for l in linhas]


def _base_da_gravacao(conn, gravacao_id: str) -> dict[str, Any]:
    """Monta a base de fatos que o Sarue le: relatorio da etapa 7 + contexto."""
    try:
        rel = relatorio.montar(conn, gravacao_id)
    except ValueError as e:
        # Gravacao sem volta cortada nao rende relatorio, e sem relatorio nao ha
        # base de fatos: perguntar sobre ela e pedir sobre o que ainda nao
        # existe. 404 com o motivo, nao 500. O 500 dizia "a culpa foi nossa" e
        # escondia do usuario que bastava esperar o pipeline terminar.
        raise HTTPException(
            status_code=404, detail=f"esta gravação ainda não rende relatório: {e}"
        ) from e
    contextos = _contextos_da_gravacao(conn, gravacao_id)
    return montar_base(rel, contextos)


# --- perguntar -------------------------------------------------------------

TURNO_COLS = ["id", "gravacao_id", "pergunta", "resposta", "modelo", "erro", "criado_em"]


@router.post("/perguntar")
def perguntar(corpo: dict, dono: Dono) -> dict:
    gravacao_id = corpo.get("gravacao_id")
    pergunta = corpo.get("pergunta")
    if not gravacao_id or not pergunta:
        raise HTTPException(status_code=422, detail="gravacao_id e pergunta são obrigatórios")

    with connect() as conn:
        _dono_da_gravacao(conn, gravacao_id, dono)
        base = _base_da_gravacao(conn, gravacao_id)

        try:
            resposta, nao_conferidos = responder(pergunta, base)
        except SarueIndisponivel as e:
            # grava o turno mesmo na falha: turno apagado vira "o Sarue nunca
            # respondeu isso" na proxima leitura, o comentario da migration.
            conn.execute(
                """insert into sarue_turno (user_id, gravacao_id, pergunta, resposta,
                                             base, modelo, erro)
                    values (%s,%s,%s,null,%s,null,%s)""",
                (dono, gravacao_id, pergunta, Jsonb(base), str(e)),
            )
            conn.commit()
            raise HTTPException(status_code=503, detail=str(e)) from e

        linha = conn.execute(
            f"""insert into sarue_turno (user_id, gravacao_id, pergunta, resposta,
                                         base, modelo)
                values (%s,%s,%s,%s,%s,%s)
                returning {', '.join(TURNO_COLS)}""",
            (dono, gravacao_id, pergunta, resposta, Jsonb(base), CONFIG.openrouter_modelo),
        ).fetchone()
        conn.commit()

    saida = _serializar(linha, TURNO_COLS)
    return {
        "id": saida["id"],
        "pergunta": saida["pergunta"],
        "resposta": saida["resposta"],
        "numeros_nao_conferidos": nao_conferidos,
        "criado_em": saida["criado_em"],
    }


@router.get("/turnos")
def listar_turnos(gravacao_id: str, dono: Dono) -> list[dict]:
    with connect() as conn:
        linhas = conn.execute(
            f"""select {', '.join(TURNO_COLS)} from sarue_turno
                 where gravacao_id = %s and user_id = %s
                 order by criado_em desc limit 50""",
            (gravacao_id, dono),
        ).fetchall()
    return [_serializar(l, TURNO_COLS) for l in linhas]


# --- avisos ------------------------------------------------------------

AVISO_COLS = ["id", "bateria_id", "gravacao_id", "texto", "modelo", "visto_em", "criado_em"]


def gerar_aviso_para(gravacao_id: str, dono: UUID) -> dict:
    """Gera e grava um aviso. Separado da rota porque o CICLO PERIODICO chama
    isto direto (`api.py`), sem passar por HTTP: o timer mora no servidor, e
    fazer o servidor falar consigo mesmo por rede so acrescentaria uma forma
    nova de falhar."""
    with connect() as conn:
        _dono_da_gravacao(conn, gravacao_id, dono)
        base = _base_da_gravacao(conn, gravacao_id)

        try:
            texto, _nao_conferidos = gerar_aviso(base)
        except SarueIndisponivel as e:
            raise HTTPException(status_code=503, detail=str(e)) from e

        linha = conn.execute(
            f"""insert into sarue_aviso (user_id, gravacao_id, texto, base, modelo)
                values (%s,%s,%s,%s,%s)
                returning {', '.join(AVISO_COLS)}""",
            (dono, gravacao_id, texto, Jsonb(base), CONFIG.openrouter_modelo),
        ).fetchone()
        conn.commit()

    return _serializar(linha, AVISO_COLS)


@router.post("/avisos/gerar")
def gerar_aviso_rota(corpo: dict, dono: Dono) -> dict:
    gravacao_id = corpo.get("gravacao_id")
    if not gravacao_id:
        raise HTTPException(status_code=422, detail="gravacao_id é obrigatório")
    return gerar_aviso_para(gravacao_id, dono)


@router.get("/avisos")
def listar_avisos(gravacao_id: str, dono: Dono, apenas_novos: bool = False) -> list[dict]:
    filtro_novos = "and visto_em is null" if apenas_novos else ""
    with connect() as conn:
        linhas = conn.execute(
            f"""select {', '.join(AVISO_COLS)} from sarue_aviso
                 where gravacao_id = %s and user_id = %s {filtro_novos}
                 order by criado_em desc""",
            (gravacao_id, dono),
        ).fetchall()
    return [_serializar(l, AVISO_COLS) for l in linhas]


@router.post("/avisos/{aviso_id}/visto", status_code=204)
def marcar_aviso_visto(aviso_id: str, dono: Dono) -> None:
    with connect() as conn:
        atualizadas = conn.execute(
            "update sarue_aviso set visto_em = now() where id = %s and user_id = %s",
            (aviso_id, dono),
        ).rowcount
        if not atualizadas:
            raise HTTPException(status_code=404, detail=NAO_ACHADO)
        conn.commit()
