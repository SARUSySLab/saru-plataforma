"""Gera a fixture sintetica `pi_pds_sintetico.pds`, usada por
`tests/test_reader_pi_pds.py`.

Roda uma vez so, manualmente (`python tests/fixtures/pi_pds_gerar_sintetico.py`),
pra regravar a fixture versionada. Nao roda como parte da suite de teste: o
arquivo `.pds` gerado e o artefato versionado, este script e so a receita.

Contra o layout medido no acervo real (ver `src/saru_poc/readers/pi_pds.py`):
magic de 4 B no offset 4, dicionario de canais (registros de 552 B, nome em
UTF-16LE duplicado no offset 88, unidade no offset 152, indice do canal nos
ultimos 4 B) e, logo em seguida, a tabela de blocos de amostra (registros de
64 B com indice, intervalo em ticks de 1e-7 s, numero de amostras e offset de
bytes que fecha exato com `n_amostras_anterior * 8`).

8 canais (minimo pra passar em `_MIN_REGISTROS_CANDIDATO` e
`_MIN_CANAIS_COM_DADO`), todos com 2.0 s de duracao (mesma convencao da
fixture irma `pi_pid_sintetico.pid`), cobrindo as 7 taxas medidas no acervo
real (1, 5... aqui so 1, 10, 20, 25, 50 e 100 Hz, ja que 5 canais bastam pra
cobrir a maioria) mais um canal repetido em taxa pra exercitar `cab.taxas`
com valor duplicado descartado pelo `set`.
"""

from __future__ import annotations

import struct
from pathlib import Path

_MAGIC = b"\x1a\x12\x40\xf7"
_OFF_MAGIC = 4
_ESTRIDE_DICIONARIO = 552
_OFF_NOME = 0
_OFF_NOME_DUP = 88
_OFF_UNIDADE = 152
_OFF_IDX_DICIONARIO = 544
_TAMANHO_REGISTRO_TABELA = 64

_DURACAO_S = 2.0

# (nome, unidade, taxa_hz). 10 canais, nao 8: sobra pra
# `test_indice_duplicado_no_dicionario_exclui_os_dois_canais` derrubar 2 por
# colisao de indice e ainda passar no minimo `_MIN_CANAIS_COM_DADO` (8) do
# leitor.
_CANAIS = [
    ("Steering", "mm", 100),
    ("Speed", "kph", 50),
    ("Throttle Position", "%", 20),
    ("RPM", "rpm", 100),
    ("Water Temp", "° C", 10),
    ("Gear", "", 1),
    ("Beacon Code", "", 1),
    ("Lambda", "La", 25),
    ("Fuel Pressure", "mB", 5),
    ("Oil Pressure", "B", 5),
]


def _registro_dicionario(nome: str, unidade: str, idx: int) -> bytes:
    buf = bytearray(_ESTRIDE_DICIONARIO)
    nome_b = nome.encode("utf-16le") + b"\x00\x00"
    unidade_b = unidade.encode("utf-16le") + b"\x00\x00"
    buf[_OFF_NOME : _OFF_NOME + len(nome_b)] = nome_b
    buf[_OFF_NOME_DUP : _OFF_NOME_DUP + len(nome_b)] = nome_b
    buf[_OFF_UNIDADE : _OFF_UNIDADE + len(unidade_b)] = unidade_b
    struct.pack_into("<i", buf, _OFF_IDX_DICIONARIO, idx)
    return bytes(buf)


def _registro_tabela(
    idx: int, taxa_hz: int, n_amostras: int, byte_offset: int
) -> bytes:
    buf = bytearray(_TAMANHO_REGISTRO_TABELA)
    intervalo_ticks = round(1e7 / taxa_hz)
    struct.pack_into("<i", buf, 0, idx)
    struct.pack_into("<i", buf, 16, intervalo_ticks)
    struct.pack_into("<i", buf, 20, n_amostras)
    struct.pack_into("<i", buf, 48, byte_offset)
    struct.pack_into("<i", buf, 56, idx + 1)
    struct.pack_into("<i", buf, 60, idx + 1)
    return bytes(buf)


def construir() -> bytes:
    cabecalho = bytearray(64)
    cabecalho[0:4] = b"\x01\x00\x00\x00"
    cabecalho[_OFF_MAGIC : _OFF_MAGIC + 4] = _MAGIC

    corpo_amostra = b"\x00" * 256  # nunca lido por inspecionar(), so preenche.

    dicionario = bytearray()
    for idx, (nome, unidade, _taxa) in enumerate(_CANAIS):
        dicionario += _registro_dicionario(nome, unidade, idx)

    tabela = bytearray()
    byte_offset = 4096
    for idx, (_nome, _unidade, taxa_hz) in enumerate(_CANAIS):
        n_amostras = round(taxa_hz * _DURACAO_S)
        tabela += _registro_tabela(idx, taxa_hz, n_amostras, byte_offset)
        byte_offset += n_amostras * 8

    return bytes(cabecalho) + corpo_amostra + bytes(dicionario) + bytes(tabela)


if __name__ == "__main__":
    destino = Path(__file__).parent / "pi_pds_sintetico.pds"
    destino.write_bytes(construir())
    print(f"escrito {destino} ({destino.stat().st_size} B)")
