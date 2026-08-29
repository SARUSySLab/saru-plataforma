"""Rota de clima. O front NAO fala com a fonte de meteorologia direto.

Passa pelo backend por tres motivos: o cache de 15 min (agora persistente no
Postgres, incidente de 29/08) vale pra todos os clientes de uma vez, o dia
que a fonte exigir chave essa chave nao vai pro bundle, e a degradacao pra
dado velho (`defasado=True`) so faz sentido centralizada aqui.

O 502 abaixo so acontece quando `previsao()` falhou na fonte E nao tinha
NADA em cache pra servir degradado: ver `clima.py`.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException

from ..auth import Dono
from ..clima import previsao
from ..db import connect

router = APIRouter(prefix="/api/clima", tags=["clima"])


@router.get("/{layout_id}")
def clima_do_layout(layout_id: str, dono: Dono) -> dict:
    """Previsao na coordenada de referencia do layout.

    Sem `ref_lat`/`ref_lon` a resposta e 422 explicito, nao uma previsao de
    coordenada default. Previsao da pista errada e pior que previsao nenhuma:
    e a mesma doenca do B2, so que no clima.
    """
    with connect() as conn:
        linha = conn.execute(
            """select l.ref_lat, l.ref_lon, l.nome, p.timezone
                 from layout l left join pista p on p.id = l.pista_id
                where l.id = %s""",
            (layout_id,),
        ).fetchone()
    if not linha:
        raise HTTPException(status_code=404, detail="layout não encontrado")
    lat, lon, nome, fuso = linha
    if lat is None or lon is None:
        raise HTTPException(
            status_code=422,
            detail=f"{nome} não tem coordenada de referência no catálogo, sem isso a previsão seria de outro lugar",
        )
    try:
        return {"layout_id": layout_id, **previsao(float(lat), float(lon), fuso=fuso)}
    except httpx.HTTPError as e:
        # 502: quem falhou foi a fonte, nao nos e nem o cliente
        raise HTTPException(status_code=502, detail=f"fonte de meteorologia não respondeu: {e}") from e
