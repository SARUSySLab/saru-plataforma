"""Gera a fixture sintetica `synthetic_motec.ld`, usada por
`tests/test_reader_ld.py`.

Roda uma vez so, manualmente (`python tests/fixtures/gerar_ld_sintetico.py`),
pra regravar a fixture versionada. Nao roda como parte da suite de teste:
o arquivo `.ld` gerado e o artefato versionado, este script e so a receita.

Contra os offsets medidos no acervo real (ver `src/saru_poc/readers/ld.py`),
com 3 canais: um GPS Latitude comum, um G_LAT no estilo ACC (nome mente,
unidade `m/s2` desmente) e um RPM em taxa diferente, pra exercitar
frequencias distintas e o fechamento normal da lista (`next == 0`).
"""

from __future__ import annotations

import struct
from pathlib import Path

MAGIC = 64
TAMANHO_REGISTRO_CANAL = 124


def _s(texto: str, tamanho: int) -> bytes:
    b = texto.encode("latin1")
    if len(b) > tamanho:
        raise ValueError(f"string {texto!r} nao cabe em {tamanho} bytes")
    return b + b"\x00" * (tamanho - len(b))


def _canal(
    prev: int,
    nxt: int,
    ptr_dados: int,
    n_amostras: int,
    freq_hz: int,
    nome_longo: str,
    nome_curto: str,
    unidade: str,
) -> bytes:
    buf = bytearray(TAMANHO_REGISTRO_CANAL)
    struct.pack_into("<IIII", buf, 0, prev, nxt, ptr_dados, n_amostras)
    # +16: dois bytes nao usados por este leitor (offset livre no registro).
    struct.pack_into("<H", buf, 18, 7)  # dtype_a: 7 -> float32 (par (7,4))
    struct.pack_into("<H", buf, 20, 4)  # dtype: 4 bytes
    struct.pack_into("<H", buf, 22, freq_hz)
    struct.pack_into("<hhhh", buf, 24, 0, 1, 1, 0)  # shift, mul, scale, dec
    buf[32:64] = _s(nome_longo, 32)
    buf[64:72] = _s(nome_curto, 8)
    buf[72:84] = _s(unidade, 12)
    return bytes(buf)


def construir() -> bytes:
    tamanho_cabecalho = 0x6E2 + 64
    ptr_canais = tamanho_cabecalho
    n_canais = 3
    ptr_dados = ptr_canais + n_canais * TAMANHO_REGISTRO_CANAL

    buf = bytearray(ptr_dados + 64)  # + folga de "dados" (nao lidos aqui)

    struct.pack_into("<I", buf, 0x00, MAGIC)
    struct.pack_into("<I", buf, 0x08, ptr_canais)
    struct.pack_into("<I", buf, 0x0C, ptr_dados)
    struct.pack_into("<I", buf, 0x24, 0)  # ponteiro de evento, nao usado

    buf[0x4A : 0x4A + 8] = _s("ADL", 8)
    buf[0x5E : 0x5E + 16] = _s("17/08/2024", 16)
    buf[0x7E : 0x7E + 16] = _s("16:46:07", 16)
    buf[0x9E : 0x9E + 64] = _s("Piloto Sintetico", 64)
    buf[0xDE : 0xDE + 64] = _s("Kart Fixture", 64)
    buf[0x15E : 0x15E + 64] = _s("Interlagos GP Circuit", 64)
    buf[0x624 : 0x624 + 64] = _s("gerado pelo gerar_ld_sintetico.py", 64)
    buf[0x6E2 : 0x6E2 + 64] = _s("Fixture de teste", 64)

    no0 = ptr_canais
    no1 = ptr_canais + TAMANHO_REGISTRO_CANAL
    no2 = ptr_canais + 2 * TAMANHO_REGISTRO_CANAL

    canal0 = _canal(0, no1, 1000, 6000, 60, "GPS Latitude", "Lat", "deg")
    canal1 = _canal(
        no0, no2, 2000, 2000, 20, "G_LAT", "GLat", "m/s2"
    )  # a armadilha: nome mente, unidade desmente
    canal2 = _canal(no1, 0, 3000, 12000, 100, "Engine RPM", "RPM", "1/min")

    buf[no0 : no0 + TAMANHO_REGISTRO_CANAL] = canal0
    buf[no1 : no1 + TAMANHO_REGISTRO_CANAL] = canal1
    buf[no2 : no2 + TAMANHO_REGISTRO_CANAL] = canal2

    return bytes(buf)


if __name__ == "__main__":
    destino = Path(__file__).parent / "synthetic_motec.ld"
    destino.write_bytes(construir())
    print(f"escrito {destino} ({destino.stat().st_size} bytes)")
