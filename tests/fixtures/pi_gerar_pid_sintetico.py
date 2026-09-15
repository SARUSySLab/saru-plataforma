"""Gera a fixture sintetica `pi_pid_sintetico.pid`, usada por
`tests/test_reader_pi.py`.

Roda uma vez so, manualmente (`python tests/fixtures/pi_gerar_pid_sintetico.py`),
pra regravar a fixture versionada. Nao roda como parte da suite de teste: o
arquivo `.pid` gerado e o artefato versionado, este script e so a receita.

Contra o layout medido no acervo real (ver `src/saru_poc/readers/pi_pid.py`):
cabecalho de 16 B, corpo de `n_blocos*tamanho_bloco` bytes em layout
intercalado por tick (ver `_corpo()`: valores conhecidos por canal, e o quadro
do tick 1 ocupado pelo marcador de bloco medido no acervo), marcador de fim, tres strings
(piloto/venue/veiculo) e um dicionario de 3 canais cuja soma
`taxa_hz * largura` fecha exato no `tamanho_bloco`.

Os 3 canais (`Steering` 100 Hz, `Speed` 50 Hz, `Throttle Position` 20 Hz) tem
nome e taxa espelhados na fixture irma `pi_listhead_sintetico.dat`
(`pi_gerar_listhead_sintetico.py`), pra exercitar o teste de cruzamento
`.dat` x `.pid` sem depender do acervo real.
"""

from __future__ import annotations

import struct
from pathlib import Path

_MAGIC = b"\x01\x20\x03\x23"
_END_MARKER = b"\x02\x20\x01\x23"
_CHANNEL_MARKER = b"\x01\x20\x08\x28"

# (nome, nome_curto, unidade, taxa_hz, largura, minimo, maximo)
_CANAIS = [
    ("Steering", "Str", "mm", 100, 2, -100.0, 100.0),
    ("Speed", "Spd", "kph", 50, 2, 0.0, 260.0),
    ("Throttle Position", "Thr", "%", 20, 2, 0.0, 100.0),
]
N_BLOCOS = 2
#: Escala declarada no registro, como no acervo: `Speed` grava 0,1 kph por
#: contagem e declara 10 (divisor); os outros declaram 1 (sem conversao).
_ESCALA = {"Speed": 10.0}


def _string_prefixada(texto: str) -> bytes:
    bruto = texto.encode("latin-1")
    return struct.pack("<I", len(bruto)) + bruto


def _registro_canal(
    channel_id: int,
    nome: str,
    nome_curto: str,
    unidade: str,
    taxa_hz: int,
    largura: int,
    minimo: float,
    maximo: float,
) -> bytes:
    buf = bytearray()
    buf += _CHANNEL_MARKER
    buf += bytes([channel_id])
    buf += _string_prefixada(nome)
    buf += _string_prefixada(nome_curto)
    buf += _string_prefixada(unidade)
    inicio_campos = len(buf)
    buf += struct.pack("<III", 0, 0, taxa_hz)  # a, b, taxa_hz
    buf += bytes([largura])  # +12: largura
    buf += b"\x00" * 4  # +13..17: campos nao usados por este leitor
    buf += struct.pack("<d", minimo)  # +17: minimo declarado
    buf += struct.pack("<d", maximo)  # +25: maximo declarado
    buf += b"\x00" * 14  # +33..47: campos nao usados por este leitor
    buf += struct.pack("<d", _ESCALA.get(nome, 1.0))  # +47: escala declarada
    assert len(buf) - inicio_campos == 55, "registro de canal fora do layout"
    return bytes(buf)


_TICKS = 100
#: Marcador do tick 1, medido no acervo F3 (12 B, com u16 variavel no meio).
#: Aqui o quadro do tick 1 so tem `Steering` (100 Hz, 2 B), entao o marcador
#: e o prefixo de 2 B: `00 00`.
_MARCADOR_TICK_1 = b"\x00\x00"


def contagem_esperada(nome: str, indice: int) -> int:
    """Contagem gravada pra amostra `indice` (na serie concatenada) do canal.

    Rampa distinta por canal, pra qualquer troca de posicao no quadro trocar
    o valor lido: `Steering` = 400 + i, `Speed` = 10 * (100 + i) (0,1 kph por
    contagem, como no acervo), `Throttle Position` = 5 * i.
    """
    return {
        "Steering": 400 + indice,
        "Speed": 1000 + 10 * indice,
        "Throttle Position": 5 * indice,
    }[nome]


def _corpo(tamanho_bloco: int) -> bytes:
    corpo = bytearray()
    contador = {nome: 0 for nome, *_ in _CANAIS}
    for _bloco in range(N_BLOCOS):
        for tick in range(_TICKS):
            for nome, _curto, _unidade, taxa, largura, _mn, _mx in _CANAIS:
                if tick % (_TICKS // taxa):
                    continue
                if tick == 1:
                    corpo += _MARCADOR_TICK_1[:largura]
                else:
                    corpo += contagem_esperada(nome, contador[nome]).to_bytes(
                        largura, "big"
                    )
                contador[nome] += 1
    assert len(corpo) == N_BLOCOS * tamanho_bloco
    return bytes(corpo)


def construir() -> bytes:
    tamanho_bloco = sum(taxa * largura for _, _, _, taxa, largura, _, _ in _CANAIS)

    cabecalho = _MAGIC + struct.pack("<III", N_BLOCOS, tamanho_bloco, tamanho_bloco)
    corpo = _corpo(tamanho_bloco)

    trailer = bytearray()
    trailer += _END_MARKER
    trailer += b"\x00" * 4  # filler entre o marcador de fim e as strings
    trailer += _string_prefixada("P.Sintetico")  # driver
    trailer += _string_prefixada("Interlagos")  # venue
    trailer += _string_prefixada("KartFixture")  # vehicle
    trailer += _string_prefixada("01:13.461")  # melhor volta em texto
    for idx, (nome, curto, unidade, taxa, largura, minimo, maximo) in enumerate(
        _CANAIS, start=1
    ):
        trailer += _registro_canal(
            idx, nome, curto, unidade, taxa, largura, minimo, maximo
        )

    return cabecalho + corpo + bytes(trailer)


if __name__ == "__main__":
    destino = Path(__file__).parent / "pi_pid_sintetico.pid"
    destino.write_bytes(construir())
    print(f"escrito {destino} ({destino.stat().st_size} B)")
