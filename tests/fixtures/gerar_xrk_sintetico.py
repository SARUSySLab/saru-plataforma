"""Gera as fixtures sinteticas `xrk_completo.xrk` e `xrk_parcial.xrk`, usadas
por `tests/test_reader_xrk.py`.

Roda uma vez so, manualmente (`python tests/fixtures/gerar_xrk_sintetico.py`),
pra regravar as fixtures versionadas. Nao roda como parte da suite de teste.

Contra a estrutura medida em `src/saru_poc/readers/xrk.py`: container `CNF`
com `CHS` (definicao de canal) e `GRP` (definicao de grupo) aninhados,
chunks de metadado soltos (`RCR`, `VEH`, `CMP`, `MANL`, `MODL`, `TRK `,
`TMD`, `TMT`), e um stream de amostra misturando registro escalar (`S`),
registro de grupo (`G`), registro de rajada (`M`) e chunks nomeados soltos
(`GPS`, `LAP`, `CAL`).

`xrk_parcial.xrk` e o mesmo cabecalho, mas o stream de amostra tem um kind
de registro nao mapeado (`X`) no meio: o leitor tem que parar ali e declarar
leitura parcial, sem adivinhar o tamanho do payload.
"""

from __future__ import annotations

import struct
from pathlib import Path


def _chunk(tag4: bytes, versao: int, corpo: bytes) -> bytes:
    assert len(tag4) == 4
    abertura = b"<h" + tag4 + struct.pack("<I", len(corpo)) + bytes([versao]) + b">"
    fecho = b"<" + tag4 + struct.pack("<H", 0) + b">"
    return abertura + corpo + fecho


def _texto(tag4: bytes, texto: str, versao: int = 1) -> bytes:
    return _chunk(tag4, versao, texto.encode("latin-1") + b"\x00")


def _chs(cid: int, curto: str, longo: str, periodo_us: int, bps: int) -> bytes:
    buf = bytearray(112)
    struct.pack_into("<I", buf, 0, cid)
    curto_b = curto.encode("latin-1")
    buf[0x18 : 0x18 + len(curto_b)] = curto_b
    longo_b = longo.encode("latin-1")
    buf[0x20 : 0x20 + len(longo_b)] = longo_b
    struct.pack_into("<I", buf, 0x40, periodo_us)
    struct.pack_into("<I", buf, 0x48, bps)
    return bytes(buf)


def _grp(gid: int, membros: list[int]) -> bytes:
    corpo = struct.pack("<HH", gid, len(membros))
    for m in membros:
        corpo += struct.pack("<H", m)
    return corpo


def _cnf(canais_corpo: bytes) -> bytes:
    return _chunk(b"CNF\x00", 1, canais_corpo)


def _reg_s(ts_ms: int, cid: int, payload: bytes) -> bytes:
    return b"(S" + struct.pack("<IH", ts_ms, cid) + payload + b")"


def _reg_g(ts_ms: int, gid: int, payload: bytes) -> bytes:
    return b"(G" + struct.pack("<IH", ts_ms, gid) + payload + b")"


def _reg_m(ts_ms: int, cid: int, amostras: list[int]) -> bytes:
    payload = struct.pack("<H", len(amostras)) + b"".join(
        struct.pack("<h", v) for v in amostras
    )
    return b"(M" + struct.pack("<IH", ts_ms, cid) + payload + b")"


def _cabecalho_completo() -> bytes:
    corpo_cnf = (
        _chunk(b"CHS\x00", 1, _chs(0, "MClk", "Master Clk", 100_000, 4))
        + _chunk(b"CDE\x00", 1, b"\x00\x00")
        + _chunk(b"CHS\x00", 1, _chs(1, "RPM", "Engine RPM", 20_000, 2))
        + _chunk(b"CDE\x00", 1, b"\x00\x00")
        + _chunk(b"CHS\x00", 1, _chs(10, "TPS", "Throttle Pos", 100_000, 2))
        + _chunk(b"CDE\x00", 1, b"\x00\x00")
        + _chunk(b"CHS\x00", 1, _chs(11, "ECT", "Engine Coolant T", 100_000, 2))
        + _chunk(b"CDE\x00", 1, b"\x00\x00")
        + _chunk(b"CHS\x00", 1, _chs(20, "Vib", "Vibration Raw", 50_000, 2))
        + _chunk(b"CDE\x00", 1, b"\x00\x00")
        + _chunk(b"GRP\x00", 1, _grp(50, [10, 11]))
    )
    return (
        _cnf(corpo_cnf)
        + _texto(b"RCR\x00", "Piloto Fixture")
        + _texto(b"VEH\x00", "Kart Fixture")
        + _texto(b"CMP\x00", "Copa Fixture")
        + _texto(b"MANL", "ACME")
        + _texto(b"MODL", "ECU9000")
        + _texto(b"TRK ", "Autodromo Fixture")
        + _texto(b"TMD\x00", "01/02/2024")
        + _texto(b"TMT\x00", "10:00:00")
    )


def construir_completo() -> bytes:
    stream = (
        _reg_s(0, 0, struct.pack("<f", 0.0))
        + _reg_s(10, 1, struct.pack("<h", 8500))
        + _reg_g(20, 50, struct.pack("<hh", 42, 90))
        + _reg_m(30, 20, [1, 2, 3])
        + _chunk(b"GPS\x00", 1, b"\x00" * 56)
        + _chunk(b"LAP\x00", 1, b"\x00" * 20)
        + _reg_s(1000, 0, struct.pack("<f", 1.0))
        + _reg_s(1010, 1, struct.pack("<h", 8600))
        + _chunk(b"CAL\x00", 1, b"\x00" * 144)
    )
    return _cabecalho_completo() + stream


def construir_parcial() -> bytes:
    stream = (
        _reg_s(0, 0, struct.pack("<f", 0.0))
        + _reg_s(10, 1, struct.pack("<h", 8500))
        + _chunk(b"GPS\x00", 1, b"\x00" * 56)
        # kind 'X' nao mapeado: o leitor tem que parar exatamente aqui.
        + b"(X"
        + struct.pack("<IH", 40, 99)
        + b"\x01\x02\x03\x04)"
        # o que vem depois nunca deveria ser lido.
        + _reg_s(50, 0, struct.pack("<f", 2.0))
    )
    return _cabecalho_completo() + stream


if __name__ == "__main__":
    destino = Path(__file__).parent
    (destino / "xrk_completo.xrk").write_bytes(construir_completo())
    (destino / "xrk_parcial.xrk").write_bytes(construir_parcial())
    print("gerado: xrk_completo.xrk, xrk_parcial.xrk")
