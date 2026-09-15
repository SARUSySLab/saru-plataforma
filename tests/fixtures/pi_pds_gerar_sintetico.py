"""Gera as fixtures sinteticas `pi_pds_sintetico.pds` (layout dos arquivos
F3: um bloco por canal, float64, tabela em ordem de indice) e
`pi_pds_sintetico_992.pds` (layout medido no `REF 992.pds` do 992.1 em
2026-09-14: varios blocos por canal, amostra de 1, 2 ou 4 bytes, tabela fora
de ordem, campo 56 como numero de serie, um buraco entre blocos), usadas por
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
    idx: int,
    taxa_hz: int,
    n_amostras: int,
    byte_offset: int,
    serie: int | None = None,
) -> bytes:
    buf = bytearray(_TAMANHO_REGISTRO_TABELA)
    intervalo_ticks = round(1e7 / taxa_hz)
    struct.pack_into("<i", buf, 0, idx)
    struct.pack_into("<i", buf, 16, intervalo_ticks)
    struct.pack_into("<i", buf, 20, n_amostras)
    struct.pack_into("<i", buf, 48, byte_offset)
    struct.pack_into("<i", buf, 56, idx + 1 if serie is None else serie)
    struct.pack_into("<i", buf, 60, idx + 1)
    return bytes(buf)


_CABECALHO = 64
#: Os blocos de amostra comecam aqui, logo depois do cabecalho fixo.
_INICIO_AMOSTRA = 4096


def _montar(dicionario: bytes, tabela: bytes, fim_amostra: int) -> bytes:
    """Cabecalho, corpo de amostra zerado ate `fim_amostra` (nunca lido por
    `inspecionar()`, mas os offsets da tabela tem que caber antes do
    dicionario), dicionario e tabela."""
    cabecalho = bytearray(_CABECALHO)
    cabecalho[0:4] = b"\x01\x00\x00\x00"
    cabecalho[_OFF_MAGIC : _OFF_MAGIC + 4] = _MAGIC
    corpo_amostra = b"\x00" * (fim_amostra - _CABECALHO)
    return bytes(cabecalho) + corpo_amostra + dicionario + tabela


def construir() -> bytes:
    """Layout F3: um bloco float64 por canal, tabela em ordem de indice."""
    dicionario = bytearray()
    for idx, (nome, unidade, _taxa) in enumerate(_CANAIS):
        dicionario += _registro_dicionario(nome, unidade, idx)

    tabela = bytearray()
    byte_offset = _INICIO_AMOSTRA
    for idx, (_nome, _unidade, taxa_hz) in enumerate(_CANAIS):
        n_amostras = round(taxa_hz * _DURACAO_S)
        tabela += _registro_tabela(idx, taxa_hz, n_amostras, byte_offset)
        byte_offset += n_amostras * 8

    return _montar(bytes(dicionario), bytes(tabela), byte_offset)


#: Bytes por amostra de cada canal no layout 992.1 (medido: 4 na maioria,
#: 1 e 2 nos discretos). Indice = posicao em `_CANAIS`.
_BYTES_992 = [4, 4, 4, 4, 2, 1, 1, 4, 2, 4]
#: Canais gravados em dois blocos (segunda saida de pista).
_DOIS_BLOCOS_992 = {0, 1, 3}
#: Buraco de bytes deixado antes do bloco do canal 7 (padding medido no
#: acervo entre segmentos: 2 buracos em 4310 pares no REF 992).
_BURACO_992 = 16


def construir_992() -> bytes:
    """Layout 992.1: varios blocos por canal, amostra de 1, 2 ou 4 bytes,
    tabela embaralhada, campo 56 e numero de serie do registro."""
    dicionario = bytearray()
    for idx, (nome, unidade, _taxa) in enumerate(_CANAIS):
        dicionario += _registro_dicionario(nome, unidade, idx)

    blocos: list[tuple[int, int, int, int]] = []  # idx, taxa, n, offset
    byte_offset = _INICIO_AMOSTRA
    for segmento in (0, 1):
        for idx, (_nome, _unidade, taxa_hz) in enumerate(_CANAIS):
            if segmento == 1 and idx not in _DOIS_BLOCOS_992:
                continue
            if idx == 7:
                byte_offset += _BURACO_992
            n_amostras = (
                round(taxa_hz * _DURACAO_S) // 2
                if idx in _DOIS_BLOCOS_992
                else round(taxa_hz * _DURACAO_S)
            )
            blocos.append((idx, taxa_hz, n_amostras, byte_offset))
            byte_offset += n_amostras * _BYTES_992[idx]

    # Tabela fora de ordem de offset e de indice, como no arquivo real.
    ordem = [blocos[i] for i in (3, 0, 12, 7, 1, 10, 5, 2, 11, 8, 4, 9, 6)]
    tabela = bytearray()
    for serie, (idx, taxa_hz, n_amostras, off) in enumerate(ordem):
        tabela += _registro_tabela(idx, taxa_hz, n_amostras, off, serie=serie + 2122)

    return _montar(bytes(dicionario), bytes(tabela), byte_offset)


if __name__ == "__main__":
    for nome, fabrica in (
        ("pi_pds_sintetico.pds", construir),
        ("pi_pds_sintetico_992.pds", construir_992),
    ):
        destino = Path(__file__).parent / nome
        destino.write_bytes(fabrica())
        print(f"escrito {destino} ({destino.stat().st_size} B)")
