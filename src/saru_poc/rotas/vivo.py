"""Rotas da ingestao ao vivo (pit wall do SARU PRO).

Duas metades com credenciais diferentes, mesmo padrao do campeonato:
  - escrita (`POST /amostras`): o GATEWAY do carro, por token proprio. Nao e
    sessao de humano: o carro na pista nao loga, e a credencial precisa ser
    revogavel por carro sem derrubar ninguem.
  - leitura (`GET /painel`, `GET /veiculos`): humano logado, e so os veiculos
    do proprio dono.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Header, HTTPException

from .. import vivo
from ..auth import Dono
from ..db import connect

router = APIRouter(prefix="/api/vivo", tags=["vivo"])

# Um lote e cerca de 250 ms de amostras. A 200 Hz, a serie mais rapida do
# acervo, isso da 50 amostras; o teto de 2000 cabe folga de sobra e ainda
# recusa corpo que so pode ser abuso ou bug de gateway em loop.
_LIMITE_AMOSTRAS = 2000


def _gateway(conn, autorizacao: str | None) -> dict[str, Any]:
    if not autorizacao or not autorizacao.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="falta o token do gateway")
    dados = vivo.autenticar_gateway(conn, autorizacao.split(" ", 1)[1].strip())
    if dados is None:
        raise HTTPException(status_code=401, detail="token de gateway inválido ou revogado")
    return dados


@router.post("/amostras", status_code=202)
def receber(
    corpo: Annotated[dict[str, Any], Body()],
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Recebe um lote do gateway. Reenvio responde 202 idempotente, nao erro."""
    amostras = corpo.get("amostras")
    if not isinstance(amostras, list) or not amostras:
        raise HTTPException(status_code=422, detail="campo 'amostras' vazio ou ausente")
    if len(amostras) > _LIMITE_AMOSTRAS:
        raise HTTPException(status_code=413, detail=f"lote acima de {_LIMITE_AMOSTRAS} amostras")
    seq = corpo.get("seq")
    if not isinstance(seq, int):
        raise HTTPException(status_code=422, detail="campo 'seq' precisa ser inteiro")
    for a in amostras:
        if not isinstance(a, dict) or "t_s" not in a:
            raise HTTPException(status_code=422, detail="cada amostra precisa de 't_s'")

    with connect() as conn:
        g = _gateway(conn, authorization)
        # O veiculo vem do TOKEN, nunca do corpo: aceitar veiculo_id do corpo
        # deixaria um gateway escrever no carro do vizinho.
        resultado = vivo.receber_lote(
            conn,
            veiculo_id=g["veiculo_id"],
            gateway_id=g["gateway_id"],
            sessao=corpo.get("sessao_id"),
            seq=seq,
            amostras=amostras,
        )
        conn.commit()
    return {"veiculo": g["apelido"], **resultado}


@router.get("/painel")
def painel(dono: Dono) -> list[dict]:
    """Um item por veiculo do dono, com a idade do ultimo dado ao vivo."""
    with connect() as conn:
        return vivo.painel_do_dono(conn, dono)


@router.post("/veiculos", status_code=201)
def criar_veiculo(corpo: Annotated[dict[str, Any], Body()], dono: Dono) -> dict:
    """Cria o veiculo e o gateway dele. O token em claro so aparece aqui."""
    apelido = (corpo.get("apelido") or "").strip()
    if not apelido:
        raise HTTPException(status_code=422, detail="campo 'apelido' é obrigatório")
    # numero e TEXTO: no grid real existem #08, #033 e #2 ao mesmo tempo, e
    # converter para inteiro funde carros diferentes.
    numero = corpo.get("numero")
    numero = str(numero).strip() if numero is not None else None
    token, token_sha = vivo.gerar_token()
    with connect() as conn:
        linha = conn.execute(
            """insert into veiculo (dono_id, numero, apelido, modelo_txt)
               values (%s, %s, %s, %s)
               on conflict (dono_id, apelido) do nothing returning id""",
            (dono, numero, apelido, (corpo.get("modelo") or "").strip() or None),
        ).fetchone()
        if linha is None:
            raise HTTPException(status_code=409, detail=f"já existe veículo com o apelido '{apelido}'")
        veiculo_id = linha[0]
        conn.execute(
            "insert into gateway (veiculo_id, token_sha256, nome) values (%s, %s, %s)",
            (veiculo_id, token_sha, f"gateway de {apelido}"),
        )
        conn.commit()
    return {
        "veiculo_id": str(veiculo_id),
        "apelido": apelido,
        "numero": numero,
        "token_do_gateway": token,
        "aviso": "guarde o token agora: ele não é mostrado de novo",
    }


@router.get("/veiculos")
def listar_veiculos(dono: Dono) -> list[dict]:
    with connect() as conn:
        linhas = conn.execute(
            """select v.id, v.numero, v.apelido, v.modelo_txt, g.ultimo_pacote_em
                 from veiculo v left join gateway g on g.veiculo_id = v.id
                where v.dono_id = %s order by v.apelido""",
            (dono,),
        ).fetchall()
    return [
        {
            "veiculo_id": str(i),
            "numero": n,
            "apelido": a,
            "modelo": m,
            "ultimo_pacote_em": u.isoformat() if u else None,
        }
        for i, n, a, m, u in linhas
    ]
