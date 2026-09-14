"""Gera a fixture sintetica `mf4_sintetico.mf4`, usada por
`tests/test_reader_mf4.py`.

Roda uma vez so, manualmente (`python tests/fixtures/gerar_mf4_sintetico.py`),
pra regravar a fixture versionada. Nao roda como parte da suite de teste: o
arquivo `.mf4` gerado e o artefato versionado, este script e so a receita.

MDF4 e norma ASAM aberta: dá pra montar um arquivo minimo valido com
`struct`, sem depender de nenhuma biblioteca de MDF. A arvore de blocos
segue exatamente o layout medido nos 5 arquivos reais do acervo em
2026-08-29 (ver `src/saru_poc/readers/asam_mf4.py`): 1 `##DG`, 1 `##CG`,
dado num `##DL` de 1 filho `##DT` so, sem `##CC` (unidade vem do `##TX` de
`cn_md_unit`).

3 canais, pra exercitar dois `data_type` diferentes e a derivacao de taxa:
- `Time` (mestre, `cn_type == 2`, float64, unidade `s`).
- `RPM` (float64, unidade `1/min`).
- `Speed` (float32, unidade `km/h`), pra provar que o leitor le `data_type`
  4 tanto em 32 quanto em 64 bits.

5 amostras a 10 Hz (`t = 0.0, 0.1, 0.2, 0.3, 0.4`), pra que
`frequencia_hz = (cycle_count - 1) / duracao` de exatos `10.0`.
"""

from __future__ import annotations

import struct
from pathlib import Path

BLOCO_CABECALHO = 24


def _pad8(dado: bytes) -> bytes:
    """Completa `dado` pro proximo multiplo de 8 com NUL, como o formato
    real faz em `##TX`/`##MD` (nao e exigido pelo nosso leitor, mas deixa a
    fixture fiel ao layout medido)."""
    resto = len(dado) % 8
    if resto == 0:
        return dado
    return dado + b"\x00" * (8 - resto)


class _Escritor:
    """Escreve blocos sequencialmente e devolve o offset de cada um."""

    def __init__(self) -> None:
        self.buf = bytearray()

    def offset(self) -> int:
        return len(self.buf)

    def bloco(self, bid: bytes, links: tuple[int, ...], dado: bytes) -> int:
        off = self.offset()
        length = BLOCO_CABECALHO + len(links) * 8 + len(dado)
        self.buf += bid
        self.buf += b"\x00\x00\x00\x00"  # reservado
        self.buf += struct.pack("<Q", length)
        self.buf += struct.pack("<Q", len(links))
        for link in links:
            self.buf += struct.pack("<Q", link)
        self.buf += dado
        return off

    def tx(self, texto: str) -> int:
        dado = _pad8(texto.encode("utf-8") + b"\x00")
        return self.bloco(b"##TX", (), dado)

    def reservar(self, tamanho: int) -> int:
        """Reserva `tamanho` bytes zerados, devolve o offset. Usado pro
        `##HD`, que o padrao MDF4 exige logo apos o IDBLOCK (offset 64) mas
        cujos links (`dg_first`, `md_comment`) so existem depois de escrever
        o resto da arvore: reserva o espaco, escreve os filhos, volta e
        substitui os bytes no fim (`substituir`)."""
        off = self.offset()
        self.buf += b"\x00" * tamanho
        return off

    def substituir(self, offset: int, dado: bytes) -> None:
        self.buf[offset : offset + len(dado)] = dado


def construir() -> bytes:
    w = _Escritor()

    # IDBLOCK: 64 bytes fixos. Magic + versao + programa gerador + zeros.
    idblock = bytearray(64)
    idblock[0:8] = b"MDF     "
    idblock[8:16] = b"4.00    "
    idblock[16:24] = b"fixture "
    w.buf += bytes(idblock)
    assert w.offset() == 64

    # ##HD tem que ficar exatamente em offset 64 (regra fixa do MDF4), mas
    # os links dele (dg_first, md_comment) so existem depois de escrever o
    # resto da arvore: reserva o tamanho exato (cabecalho 24 + 6 links * 8 +
    # 32 de dado = 104 bytes, igual ao medido nos 5 arquivos reais) e
    # preenche no fim com `substituir`.
    hd_off = w.reservar(104)
    assert hd_off == 64

    # --- textos, escritos antes de quem os referencia (offset conhecido) ---
    tx_time_name = w.tx("Time")
    tx_time_unit = w.tx("s")
    tx_rpm_name = w.tx("RPM")
    tx_rpm_unit = w.tx("1/min")
    tx_speed_name = w.tx("Speed")
    tx_speed_unit = w.tx("km/h")

    md_hd_comment = w.bloco(
        b"##MD",
        (),
        _pad8(b"<HDcomment><TX>fixture sintetica</TX></HDcomment>\x00"),
    )

    # --- CN: mestre (Time), RPM, Speed. Escritos do ultimo pro primeiro
    # porque cada um precisa saber o offset do proximo (cn_cn_next). ---
    cn_dado_speed = bytearray(24)
    struct.pack_into("<BBBB", cn_dado_speed, 0, 0, 0, 4, 0)  # fixed, none, float, bit0
    struct.pack_into("<II", cn_dado_speed, 4, 16, 32)  # byte_offset 16, 32 bits
    cn_speed_off = w.bloco(
        b"##CN",
        (0, 0, tx_speed_name, 0, 0, 0, tx_speed_unit, 0),
        bytes(cn_dado_speed),
    )

    cn_dado_rpm = bytearray(24)
    struct.pack_into("<BBBB", cn_dado_rpm, 0, 0, 0, 4, 0)
    struct.pack_into("<II", cn_dado_rpm, 4, 8, 64)  # byte_offset 8, 64 bits
    cn_rpm_off = w.bloco(
        b"##CN",
        (cn_speed_off, 0, tx_rpm_name, 0, 0, 0, tx_rpm_unit, 0),
        bytes(cn_dado_rpm),
    )

    cn_dado_time = bytearray(24)
    # cn_type=2 (master), cn_sync_type=1 (time), data_type=4 (float), bit_offset=0
    struct.pack_into("<BBBB", cn_dado_time, 0, 2, 1, 4, 0)
    struct.pack_into("<II", cn_dado_time, 4, 0, 64)  # byte_offset 0, 64 bits
    cn_time_off = w.bloco(
        b"##CN",
        (cn_rpm_off, 0, tx_time_name, 0, 0, 0, tx_time_unit, 0),
        bytes(cn_dado_time),
    )

    # --- CG: 1 grupo, record_size = 8 (time) + 8 (rpm) + 4 (speed) = 20 ---
    n_amostras = 5
    record_size = 20
    cg_dado = struct.pack(
        "<QQHHIII",
        0,  # cg_record_id
        n_amostras,  # cg_cycle_count
        0,  # cg_flags
        0,  # cg_path_separator
        0,  # reserved
        record_size,  # cg_data_bytes
        0,  # cg_invalid_bytes
    )
    cg_off = w.bloco(
        b"##CG",
        (0, cn_time_off, 0, 0, 0, 0),
        cg_dado,
    )

    # --- DT: os registros de amostra propriamente ditos. ---
    tempos = [0.0, 0.1, 0.2, 0.3, 0.4]
    rpms = [1000.0, 2500.0, 4000.0, 5500.0, 7000.0]
    speeds = [0.0, 40.0, 80.0, 120.0, 160.0]
    registros = bytearray()
    for t, rpm, speed in zip(tempos, rpms, speeds, strict=True):
        registros += struct.pack("<d", t)
        registros += struct.pack("<d", rpm)
        registros += struct.pack("<f", speed)
    assert len(registros) == n_amostras * record_size
    dt_off = w.bloco(b"##DT", (), bytes(registros))

    # --- DL: aponta pro DT, com DL_FLAG_EQUAL_LENGTH e dl_count=1. ---
    dl_dado = struct.pack("<BBBBI", 0x01, 0, 0, 0, 1) + struct.pack(
        "<Q", len(registros)
    )
    dl_off = w.bloco(b"##DL", (0, dt_off), dl_dado)

    # --- DG: 1 grupo de dado. ---
    dg_off = w.bloco(b"##DG", (0, cg_off, dl_off, 0), b"\x00" * 8)

    # --- HD: cabecalho raiz, escrito por cima do espaco reservado em 64. ---
    hd_start_time_ns = 1_722_700_000_000_000_000  # arbitrario, so pra testar ISO 8601
    hd_dado = struct.pack("<QhhBBBB", hd_start_time_ns, 0, 0, 0, 0, 0, 0)
    hd_dado += struct.pack("<dd", 0.0, 0.0)  # hd_start_angle_rad, hd_start_distance_m
    hd_links = (dg_off, 0, 0, 0, 0, md_hd_comment)
    hd_bytes = (
        b"##HD"
        + b"\x00\x00\x00\x00"
        + struct.pack("<Q", 104)
        + struct.pack("<Q", len(hd_links))
        + b"".join(struct.pack("<Q", link) for link in hd_links)
        + hd_dado
    )
    assert len(hd_bytes) == 104
    w.substituir(hd_off, hd_bytes)

    return bytes(w.buf)


if __name__ == "__main__":
    destino = Path(__file__).parent / "mf4_sintetico.mf4"
    destino.write_bytes(construir())
    print(f"escrito {destino} ({destino.stat().st_size} bytes)")
