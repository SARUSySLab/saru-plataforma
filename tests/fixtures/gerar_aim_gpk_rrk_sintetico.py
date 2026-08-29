"""Gera as fixtures sinteticas de `.gpk`/`.rrk`, usadas por
`tests/test_reader_aim_gpk_rrk.py`.

Roda uma vez so, manualmente
(`python tests/fixtures/gerar_aim_gpk_rrk_sintetico.py`), pra regravar as
fixtures versionadas. Nao roda como parte da suite de teste.

Contra a estrutura medida em `src/saru_poc/readers/aim_gpk.py` e
`aim_rrk.py`: assinatura dupla de 32 bytes abrindo cada segmento, um
pseudo-registro de contador fixo 256, e uma sequencia de registros de
tamanho fixo (144 bytes pro `.gpk`, tag `PSOL`; 64 bytes pro `.rrk`, tag
`NSOL`).
"""

from __future__ import annotations

import struct
from pathlib import Path

_ASSINATURA_GPK = b"PROV\x00\x01"
_ASSINATURA_RRK = b"HEAD\x00\x01"


def _segmento(
    assinatura: bytes,
    tamanho_cabecalho_extra: int,
    tag_registro: bytes,
    tamanho_registro: int,
    contadores: list[int],
) -> bytes:
    """Monta um segmento: assinatura dupla + cabecalho zerado + pseudo-
    registro (contador 256) + N registros reais com o contador dado.

    Cada ocorrencia da assinatura ocupa um bloco de 16 bytes (6 bytes de
    assinatura + 10 de padding zero): e o que os leitores esperam ao
    checar `dados[offset+16:offset+22]` pra segunda ocorrencia."""
    bloco_assinatura = assinatura + b"\x00" * (16 - len(assinatura))
    cabecalho = bloco_assinatura + bloco_assinatura + b"\x00" * tamanho_cabecalho_extra
    pseudo = tag_registro + struct.pack("<I", 256) + b"\x00" * 8
    registros = b""
    for ctr in contadores:
        payload = bytes((ctr + i) % 256 for i in range(tamanho_registro - 8))
        registros += tag_registro + struct.pack("<I", ctr) + payload
    return cabecalho + pseudo + registros


def construir_gpk_completo() -> bytes:
    """Um unico segmento, 5 registros, passo de contador 20 (com um 19)."""
    contadores = [51, 71, 91, 110, 130]  # ultimo passo e 19, nao 20
    return _segmento(_ASSINATURA_GPK, 48, b"PSOL", 144, contadores)


def construir_gpk_multi_segmento() -> bytes:
    """Dois segmentos: o primeiro com 3 registros, o segundo (final) so com
    o cabecalho, sem nenhum registro depois (0 registros e legitimo)."""
    seg1 = _segmento(_ASSINATURA_GPK, 48, b"PSOL", 144, [51, 71, 91])
    seg2 = _segmento(_ASSINATURA_GPK, 48, b"PSOL", 144, [])
    return seg1 + seg2


def construir_gpk_tamanho_quebrado() -> bytes:
    """Assinatura ok, mas sobra bytes que nao fecham um registro inteiro."""
    base = _segmento(_ASSINATURA_GPK, 48, b"PSOL", 144, [51, 71])
    return base + b"\x00" * 10  # 10 bytes soltos, nao fecha registro de 144


def construir_rrk_completo() -> bytes:
    contadores = [51, 91, 131, 170, 210]  # 170->210 e passo 40, 131->170 e 39
    return _segmento(_ASSINATURA_RRK, 16, b"NSOL", 64, contadores)


def construir_rrk_multi_segmento() -> bytes:
    """3 segmentos, o ultimo sem registro (mesmo padrao medido no acervo
    real: `Fabio PittaBMW S1000RR18112022 (...).rrk`)."""
    seg1 = _segmento(_ASSINATURA_RRK, 16, b"NSOL", 64, [51, 91])
    seg2 = _segmento(_ASSINATURA_RRK, 16, b"NSOL", 64, [51, 91, 131])
    seg3 = _segmento(_ASSINATURA_RRK, 16, b"NSOL", 64, [])
    return seg1 + seg2 + seg3


if __name__ == "__main__":
    destino = Path(__file__).parent
    (destino / "aim_gpk_completo.gpk").write_bytes(construir_gpk_completo())
    (destino / "aim_gpk_multi_segmento.gpk").write_bytes(construir_gpk_multi_segmento())
    (destino / "aim_gpk_tamanho_quebrado.gpk").write_bytes(
        construir_gpk_tamanho_quebrado()
    )
    (destino / "aim_rrk_completo.rrk").write_bytes(construir_rrk_completo())
    (destino / "aim_rrk_multi_segmento.rrk").write_bytes(construir_rrk_multi_segmento())
    print(
        "gerado: aim_gpk_completo.gpk, aim_gpk_multi_segmento.gpk, "
        "aim_gpk_tamanho_quebrado.gpk, aim_rrk_completo.rrk, "
        "aim_rrk_multi_segmento.rrk"
    )
