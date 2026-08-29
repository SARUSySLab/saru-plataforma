"""Gera a fixture sintetica `pi_listhead_sintetico.dat`, usada por
`tests/test_reader_pi.py`.

Roda uma vez so, manualmente
(`python tests/fixtures/pi_gerar_listhead_sintetico.py`), pra regravar a
fixture versionada. Nao roda como parte da suite de teste: o arquivo `.dat`
gerado e o artefato versionado, este script e so a receita.

Contra o layout medido no acervo real (ver
`src/saru_poc/readers/pi_listhead_dat.py`): container plano de nos de 32 B
mais payload, cobrindo o arquivo inteiro sem sobra. Os 3 canais (`Steering`
100 Hz, `Speed` 50 Hz, `Throttle Position` 20 Hz, este ultimo truncado em 16 B
pelo container real) tem nome e taxa espelhados na fixture irma
`pi_pid_sintetico.pid` (`pi_gerar_pid_sintetico.py`), pra exercitar o teste
de cruzamento `.dat` x `.pid` sem depender do acervo real.
"""

from __future__ import annotations

import struct
from pathlib import Path

_NODE_HEADER_BYTES = 32
_TICK_S = 1e-4

# (nome, unidade, intervalo_ticks, n_amostras)
_CANAIS = [
    ("Steering", "mm", 100, 200),
    ("Speed", "kph", 200, 100),
    ("Throttle Position", "%", 500, 40),
]
_VENUE = "Interlagos"
_DRIVER = "P.Sintetico"
_VEHICLE = "KartFixture"


def _s(texto: str, tamanho: int) -> bytes:
    bruto = texto.encode("latin-1")
    if len(bruto) > tamanho:
        bruto = bruto[:tamanho]
    return bruto + b"\x00" * (tamanho - len(bruto))


def _nome_canal(texto: str) -> bytes:
    """Campo de nome de `CHANNEL_INFO`: 16 B, mas o container real SEMPRE
    reserva o ultimo byte (nunca preenche os 16 com texto), truncando o
    conteudo util em 15 caracteres. Medido no acervo: `'Min Corner Spee'`,
    `'Throttle Positi'`, `'Running Lap Tim'`, todos com 15 chars uteis mesmo
    quando o nome original e mais longo. Reproduzido aqui pra exercitar o
    teste de cruzamento contra o `.pid`, que nao tem esse limite.
    """
    return _s(texto[:15], 16)


def _no(tipo: str, payload: bytes) -> bytes:
    tamanho = _NODE_HEADER_BYTES + len(payload)
    cabecalho = _s(tipo, 16) + struct.pack("<IIII", 0, 0, tamanho, 0)
    return cabecalho + payload


def construir() -> bytes:
    partes: list[bytes] = []

    # No raiz: o magic do container e os primeiros 8 bytes do arquivo, e o
    # tipo do primeiro no no acervo real e "LISTHEAD" mesmo (nao ha payload
    # usado por este leitor).
    partes.append(_no("LISTHEAD", b""))

    for indice, (nome, unidade, _intervalo, _n) in enumerate(_CANAIS):
        payload = bytearray(88)
        payload[0x00 : 0x00 + 16] = _nome_canal(nome)
        struct.pack_into("<I", payload, 0x18, indice)
        payload[0x3E : 0x3E + 12] = _s(unidade, 12)
        # +0x4A: faixa MEDIDA (nao declarada), nao consumida por este leitor.
        struct.pack_into("<ff", payload, 0x4A, 0.0, 0.0)
        partes.append(_no("CHANNEL_INFO", bytes(payload)))

    for indice, (_nome, _unidade, intervalo, n_amostras) in enumerate(_CANAIS):
        ultimo_tick = intervalo * n_amostras - 1
        subcabecalho = struct.pack("<IIII", intervalo, 0, ultimo_tick, n_amostras)
        # As amostras vem logo depois do sub-cabecalho, como float32 little
        # endian. A versao anterior desta fixture escrevia so o sub-cabecalho:
        # passava no `inspecionar()`, que le apenas os 16 bytes, e quebrava no
        # `ler()`, que precisa do payload. Fixture tem que conter o que declara.
        #
        # Rampa deterministica por canal, pra o teste poder afirmar valor e nao
        # so contagem: canal i, amostra k -> i * 1000 + k.
        amostras = struct.pack(
            f"<{n_amostras}f",
            *[float(indice * 1000 + k) for k in range(n_amostras)],
        )
        partes.append(_no(f"CHID_{indice:04x}", subcabecalho + amostras))

    info = bytearray(340)
    info[8 : 8 + 12] = _s(_VENUE, 12)
    info[20 : 20 + 12] = _s(_DRIVER, 12)
    info[307 : 307 + 16] = _s(_VEHICLE, 16)
    partes.append(_no("FILE_INFO", bytes(info)))

    return b"".join(partes)


if __name__ == "__main__":
    destino = Path(__file__).parent / "pi_listhead_sintetico.dat"
    destino.write_bytes(construir())
    print(f"escrito {destino} ({destino.stat().st_size} B)")
