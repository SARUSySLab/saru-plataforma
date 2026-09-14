"""Registro de leitores, indexado pelo id de formato.

Registro explicito, por decisao do Lucas (29/08): nada de autodiscovery. Um
formato so passa a ser lido quando alguem registra um leitor pra ele aqui, e
o formato so existe no catalogo com assinatura medida de arquivo real.
"""

from __future__ import annotations

from .base import Cabecalho, CanalBruto, ErroDeLeitura, Leitor, Lote
from .formatos import FORMATOS, FORMATOS_POR_ID, Deteccao, Formato, detectar

# formato_id -> Leitor. `saru-poc doctor` e `saru-poc sniff` leem daqui pra dizer
# o que o sistema reconhece mas nao le, em vez de fingir suporte. O catalogo em
# `formato_telemetria` tambem e semeado a partir deste dict, nunca escrito a mao.
LEITORES: dict[str, Leitor] = {}


def registrar(leitor: Leitor) -> None:
    if leitor.formato_id in LEITORES:
        raise ValueError(f"formato {leitor.formato_id} ja tem leitor registrado")
    if leitor.formato_id not in FORMATOS_POR_ID:
        raise ValueError(
            f"formato {leitor.formato_id} nao consta no catalogo. "
            "Meça a assinatura de um arquivo real antes de registrar leitor."
        )
    LEITORES[leitor.formato_id] = leitor


def leitor_de(formato_id: str) -> Leitor | None:
    return LEITORES.get(formato_id)


__all__ = [
    "FORMATOS",
    "FORMATOS_POR_ID",
    "LEITORES",
    "Cabecalho",
    "CanalBruto",
    "Deteccao",
    "ErroDeLeitura",
    "Formato",
    "Leitor",
    "Lote",
    "detectar",
    "leitor_de",
    "registrar",
]


def _registrar_embutidos() -> None:
    """Registra os leitores que ja existem, na ordem de dependencia nenhuma.

    Import tardio de proposito: `registrar` valida contra o catalogo, entao os
    modulos de leitor importam `formatos`, e importa-los no topo daria ciclo.
    """
    from .aim_gpk import LeitorAimGpk
    from .aim_rrk import LeitorAimRrk
    from .aim_rs2 import LeitorAimDrk
    from .asam_mf4 import LeitorAsamMf4
    from .dlf import LeitorDlf
    from .ld import LeitorLd
    from .ldx import LeitorLdx
    from .pi_listhead_dat import LeitorPiListheadDat
    from .pi_pds import LeitorPiPds
    from .pi_pid import LeitorPiPid
    from .vbo import LeitorVbo
    from .xrk import LeitorXrk

    for leitor in (
        LeitorVbo(),
        LeitorLdx(),
        LeitorLd(),
        LeitorXrk(),
        LeitorDlf(),
        LeitorPiPid(),
        LeitorPiListheadDat(),
        LeitorPiPds(),
        LeitorAimDrk(),
        LeitorAsamMf4(),
        LeitorAimGpk(),
        LeitorAimRrk(),
    ):
        registrar(leitor)


_registrar_embutidos()
