"""Gera as fixtures sinteticas `aim_rs2_*.drk`, usadas por
`tests/test_reader_aim_rs2.py`.

Roda uma vez so, manualmente (`python tests/fixtures/gerar_aim_rs2_sintetico.py`),
pra regravar as fixtures versionadas. Nao roda como parte da suite de teste.

Layout medido contra os 129 arquivos `.drk`/`.bak` reais do acervo em
2026-08-29 (ver `src/saru_poc/readers/aim_rs2.py` e
`docs/aim-rs2-medicao.md`):

- offset 0x4c, 24 bytes: data/hora `DD-MM-AA HH:MM:SS`.
- offset 0x440, 40 bytes: veiculo.
- offset 0x468, 40 bytes: venue/pista.
- offset 0x490, 40 bytes: piloto.

Nenhum arquivo real e versionado aqui (o acervo tem nome de piloto real):
estas fixtures sao construidas do zero, com dado fictício.
"""

from __future__ import annotations

from pathlib import Path

OFF_DATA_HORA = 0x4C
OFF_VEICULO = 0x440
OFF_VENUE = 0x468
OFF_PILOTO = 0x490
LEN_CAMPO = 40
TAMANHO_MINIMO = OFF_PILOTO + LEN_CAMPO


def _s(texto: str, tamanho: int) -> bytes:
    b = texto.encode("ascii")
    if len(b) > tamanho:
        raise ValueError(f"string {texto!r} nao cabe em {tamanho} bytes")
    return b + b"\x00" * (tamanho - len(b))


def construir_completo() -> bytes:
    """Variante `RDX\\x02`, com os 4 campos de metadado preenchidos."""
    buf = bytearray(TAMANHO_MINIMO + 64)
    buf[0:8] = b"RDX\x02" + b"\x00" * 4
    buf[OFF_DATA_HORA : OFF_DATA_HORA + 24] = _s("25-01-21 08:39:16", 24)
    buf[OFF_VEICULO : OFF_VEICULO + LEN_CAMPO] = _s("F309-016 Fixture", LEN_CAMPO)
    buf[OFF_VENUE : OFF_VENUE + LEN_CAMPO] = _s("Autodromo Fixture", LEN_CAMPO)
    buf[OFF_PILOTO : OFF_PILOTO + LEN_CAMPO] = _s("Piloto Sintetico", LEN_CAMPO)
    return bytes(buf)


def construir_variante_pobre() -> bytes:
    """Variante `RD\\x90\\x01`: os 4 campos existem mas vazios (medido em
    4 dos 129 arquivos reais: `Test.drk`, `Test #1.drk`, `WarmUp.drk`,
    `81214006.drk`). Cabecalho pobre e resultado legitimo, nao erro.
    """
    buf = bytearray(TAMANHO_MINIMO + 64)
    buf[0:4] = b"RD\x90\x01"
    return bytes(buf)


def construir_curto_demais() -> bytes:
    """Menor que a regiao de metadado: deve levantar ErroDeLeitura."""
    return b"RDX\x02" + b"\x00" * 100


def construir_lixo_no_campo() -> bytes:
    """Byte fora do intervalo ASCII imprimivel no campo de piloto: o campo
    tem que virar None, nao string com lixo binario decodificado.
    """
    buf = bytearray(TAMANHO_MINIMO + 64)
    buf[0:8] = b"RDX\x02" + b"\x00" * 4
    buf[OFF_DATA_HORA : OFF_DATA_HORA + 24] = _s("25-01-21 08:39:16", 24)
    buf[OFF_VEICULO : OFF_VEICULO + LEN_CAMPO] = _s("F309-016 Fixture", LEN_CAMPO)
    buf[OFF_VENUE : OFF_VENUE + LEN_CAMPO] = _s("Autodromo Fixture", LEN_CAMPO)
    # campo de piloto com byte alto (nao ASCII imprimivel) logo no inicio.
    buf[OFF_PILOTO : OFF_PILOTO + LEN_CAMPO] = b"\xff\xfe" + b"\x00" * (LEN_CAMPO - 2)
    return bytes(buf)


def construir_data_invalida() -> bytes:
    """Data fora do formato `DD-MM-AA HH:MM:SS`: capturado_em vira None,
    mas capturado_em_bruto preserva a string crua.
    """
    buf = bytearray(TAMANHO_MINIMO + 64)
    buf[0:8] = b"RDX\x02" + b"\x00" * 4
    buf[OFF_DATA_HORA : OFF_DATA_HORA + 24] = _s("data-quebrada", 24)
    buf[OFF_VEICULO : OFF_VEICULO + LEN_CAMPO] = _s("F309-016 Fixture", LEN_CAMPO)
    buf[OFF_VENUE : OFF_VENUE + LEN_CAMPO] = _s("Autodromo Fixture", LEN_CAMPO)
    buf[OFF_PILOTO : OFF_PILOTO + LEN_CAMPO] = _s("Piloto Sintetico", LEN_CAMPO)
    return bytes(buf)


if __name__ == "__main__":
    destino_dir = Path(__file__).parent
    fixtures = {
        "aim_rs2_completo.drk": construir_completo(),
        "aim_rs2_variante_pobre.drk": construir_variante_pobre(),
        "aim_rs2_curto_demais.drk": construir_curto_demais(),
        "aim_rs2_lixo_no_campo.drk": construir_lixo_no_campo(),
        "aim_rs2_data_invalida.drk": construir_data_invalida(),
    }
    for nome, conteudo in fixtures.items():
        destino = destino_dir / nome
        destino.write_bytes(conteudo)
        print(f"escrito {destino} ({destino.stat().st_size} bytes)")
