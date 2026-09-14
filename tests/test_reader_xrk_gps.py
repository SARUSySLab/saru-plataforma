"""Canais GPS sintetizados do leitor .xrk (chunk `<hGPS`, 56 bytes NAV-SOL).

Bytes construidos aqui mesmo (mesmos builders de
`tests/fixtures/gerar_xrk_sintetico.py`, copiados porque aquele arquivo e
script de geracao, nao modulo importavel). A posicao de referencia entra em
lat/lon/alt, vira ECEF pelo forward do WGS-84 (formula fechada, abaixo) e o
teste exige que o leitor devolva a MESMA posicao de volta: roundtrip
forward-inverse, que so fecha se o layout do payload e o `_ecef2lla`
estiverem certos ao mesmo tempo.

A igualdade com o oraculo libxrk nao e testada aqui (arquivo real tem nome
de piloto, nao versionamos): foi medida fora, 111 dos 113 arquivos do
acervo bit-exatos nos 12 canais em 29/08 (os 2 restantes o oraculo nem
abre; 3 .xrz corrompidos fora da conta).
"""

from __future__ import annotations

import math
import struct
from pathlib import Path

import numpy as np
import pytest

from saru_poc.readers.base import ErroDeLeitura
from saru_poc.readers.xrk import _CANAIS_GPS, LeitorXrk

# ---------------------------------------------------------------------------
# Builders (iguais aos do gerador de fixtures)
# ---------------------------------------------------------------------------


def _chunk(tag4: bytes, versao: int, corpo: bytes) -> bytes:
    abertura = b"<h" + tag4 + struct.pack("<I", len(corpo)) + bytes([versao]) + b">"
    fecho = b"<" + tag4 + struct.pack("<H", 0) + b">"
    return abertura + corpo + fecho


def _chs(cid: int, curto: str, longo: str, periodo_us: int, bps: int) -> bytes:
    buf = bytearray(112)
    struct.pack_into("<I", buf, 0, cid)
    buf[0x18 : 0x18 + len(curto)] = curto.encode("latin-1")
    buf[0x20 : 0x20 + len(longo)] = longo.encode("latin-1")
    struct.pack_into("<I", buf, 0x40, periodo_us)
    struct.pack_into("<I", buf, 0x48, bps)
    return bytes(buf)


def _reg_s(ts_ms: int, cid: int, payload: bytes) -> bytes:
    return b"(S" + struct.pack("<IH", ts_ms, cid) + payload + b")"


def _lla2ecef_cm(lat_deg: float, lon_deg: float, alt_m: float) -> tuple[int, int, int]:
    """Forward WGS-84 (lat/lon/alt -> ECEF em CENTIMETROS, como o payload
    NAV-SOL guarda). E o inverso exato do `_ecef2lla` do leitor."""
    a = 6378137.0
    e = 8.181919084261345e-2
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    n = a / math.sqrt(1 - e * e * math.sin(lat) ** 2)
    x = (n + alt_m) * math.cos(lat) * math.cos(lon)
    y = (n + alt_m) * math.cos(lat) * math.sin(lon)
    z = ((1 - e * e) * n + alt_m) * math.sin(lat)
    return round(x * 100), round(y * 100), round(z * 100)


def _corpo_gps(
    tc_ms: int,
    ecef_cm: tuple[int, int, int],
    vel_cms: tuple[int, int, int] = (0, 0, 0),
    fix: int = 3,
    pacc_cm: int = 120,
    sacc_cms: int = 30,
    pdop_x100: int = 150,
    nsat: int = 11,
) -> bytes:
    buf = bytearray(56)
    struct.pack_into("<i", buf, 0, tc_ms)
    buf[14] = fix
    struct.pack_into("<iii", buf, 16, *ecef_cm)
    struct.pack_into("<I", buf, 28, pacc_cm)
    struct.pack_into("<iii", buf, 32, *vel_cms)
    struct.pack_into("<I", buf, 44, sacc_cms)
    struct.pack_into("<H", buf, 48, pdop_x100)
    buf[51] = nsat
    return bytes(buf)


# Kartodromo do Guara, a posicao ja validada contra o acervo real.
_LAT, _LON, _ALT = -15.82570, -47.97108, 1081.0


def _arquivo(
    tmp_path: Path,
    corpos_gps: list[bytes],
    nome_chs_extra: str | None = None,
) -> Path:
    cnf = _chunk(b"CHS\x00", 1, _chs(1, "RPM", "Engine RPM", 20_000, 2))
    if nome_chs_extra is not None:
        cnf += _chunk(b"CHS\x00", 1, _chs(2, "X", nome_chs_extra, 20_000, 2))
    partes = [_chunk(b"CNF\x00", 1, cnf)]
    partes.append(_reg_s(0, 1, struct.pack("<h", 3000)))
    for corpo in corpos_gps:
        partes.append(_chunk(b"GPS\x00", 1, corpo))
    partes.append(_reg_s(20, 1, struct.pack("<h", 3100)))
    caminho = tmp_path / "gps.xrk"
    caminho.write_bytes(b"".join(partes))
    return caminho


def _corpos_a_4hz(n: int, t0_ms: int = 1000) -> list[bytes]:
    ecef = _lla2ecef_cm(_LAT, _LON, _ALT)
    return [
        _corpo_gps(t0_ms + 250 * i, ecef, vel_cms=(300, 400, 0)) for i in range(n)
    ]


# ---------------------------------------------------------------------------
# Inventario
# ---------------------------------------------------------------------------


def test_inventario_sintetiza_os_12_canais(tmp_path: Path) -> None:
    cab = LeitorXrk().inspecionar(_arquivo(tmp_path, _corpos_a_4hz(5)))
    por_nome = {c.nome_bruto: c for c in cab.canais}
    for nome, unidade in _CANAIS_GPS:
        assert nome in por_nome, nome
        assert por_nome[nome].frequencia_hz == 4.0
        assert por_nome[nome].n_amostras == 5
        assert por_nome[nome].unidade_declarada == unidade
    assert cab.bruto["gps_taxa_hz"] == "4"


def test_inventario_um_chunk_so_declara_motivo(tmp_path: Path) -> None:
    """Com 1 chunk nao tem delta pra medir taxa: nada sintetizado, motivo
    escrito (regra do B2, nunca silencio)."""
    cab = LeitorXrk().inspecionar(_arquivo(tmp_path, _corpos_a_4hz(1)))
    nomes = {c.nome_bruto for c in cab.canais}
    assert not nomes & {n for n, _u in _CANAIS_GPS}
    assert "gps_nao_sintetizado" in cab.bruto


def test_inventario_corpo_de_tamanho_errado_contado(tmp_path: Path) -> None:
    corpos = _corpos_a_4hz(3) + [b"\x00" * 20]
    cab = LeitorXrk().inspecionar(_arquivo(tmp_path, corpos))
    assert cab.bruto["gps_chunks_invalidos"] == "1"
    assert cab.bruto["gps_amostras"] == "4"
    por_nome = {c.nome_bruto: c for c in cab.canais}
    assert por_nome["GPS Latitude"].n_amostras == 3


def test_inventario_nome_chs_vence_o_sintetizado(tmp_path: Path) -> None:
    cab = LeitorXrk().inspecionar(
        _arquivo(tmp_path, _corpos_a_4hz(4), nome_chs_extra="GPS Speed")
    )
    velocidade = [c for c in cab.canais if c.nome_bruto == "GPS Speed"]
    assert len(velocidade) == 1
    assert velocidade[0].frequencia_hz == 50.0  # a do CHS, nao a do GPS
    assert cab.bruto["gps_canais_em_conflito"] == "GPS Speed"
    assert any(c.nome_bruto == "GPS Latitude" for c in cab.canais)


# ---------------------------------------------------------------------------
# ler(): serie propria, roundtrip de posicao
# ---------------------------------------------------------------------------


def test_ler_emite_serie_gps_propria(tmp_path: Path) -> None:
    lotes = list(LeitorXrk().ler(_arquivo(tmp_path, _corpos_a_4hz(5))))
    gps = [lote for lote in lotes if lote.serie == "gps"]
    principais = [lote for lote in lotes if lote.serie != "gps"]
    assert len(gps) == 1
    assert principais, "a serie do canal CHS continua saindo"
    tabela = gps[0].tabela
    assert gps[0].frequencia_hz == 4.0
    assert tabela.num_rows == 5
    assert tabela.schema.names == ["t_s", *[n for n, _u in _CANAIS_GPS]]
    # t_s = timecode do proprio GPS em segundos (mesmo relogio do stream).
    assert tabela.column("t_s").to_pylist() == pytest.approx(
        [1.0, 1.25, 1.5, 1.75, 2.0]
    )


def test_ler_roundtrip_de_posicao_e_velocidade(tmp_path: Path) -> None:
    lotes = list(LeitorXrk().ler(_arquivo(tmp_path, _corpos_a_4hz(5))))
    tabela = next(lote for lote in lotes if lote.serie == "gps").tabela
    lat = tabela.column("GPS Latitude").to_numpy()
    lon = tabela.column("GPS Longitude").to_numpy()
    alt = tabela.column("GPS Altitude").to_numpy()
    # Roundtrip forward-inverse: 1e-7 grau ~ 1 cm, folga pro arredondamento
    # do proprio payload (ECEF inteiro em cm).
    assert np.allclose(lat, _LAT, atol=1e-6)
    assert np.allclose(lon, _LON, atol=1e-6)
    assert np.allclose(alt, _ALT, atol=0.05)
    # |v| = sqrt(3^2 + 4^2) m/s = 5 m/s (o classico 3-4-5).
    assert np.allclose(tabela.column("GPS Speed").to_numpy(), 5.0, atol=1e-9)
    assert np.allclose(tabela.column("GPS_Satellites").to_numpy(), 11.0)
    assert np.allclose(tabela.column("GPS_Fix").to_numpy(), 3.0)
    assert np.allclose(tabela.column("GPS_pDOP").to_numpy(), 1.5)
    assert np.allclose(tabela.column("GPS_Position_Accuracy").to_numpy(), 1.2)
    assert np.allclose(tabela.column("GPS_Velocity_Accuracy").to_numpy(), 0.3)


def test_ler_sem_fix_vira_nan_nao_lixo(tmp_path: Path) -> None:
    """ECEF zerado (sem fix) nao pode virar uma coordenada 'valida' no golfo
    da Guine: nan e a resposta honesta e nunca cruza gate de corte."""
    corpos = [_corpo_gps(1000 + 250 * i, (0, 0, 0), fix=0) for i in range(3)]
    lotes = list(LeitorXrk().ler(_arquivo(tmp_path, corpos)))
    tabela = next(lote for lote in lotes if lote.serie == "gps").tabela
    assert np.isnan(tabela.column("GPS Altitude").to_numpy()).all()
    assert np.all(tabela.column("GPS_Fix").to_numpy() == 0.0)


def test_ler_desembaraca_timecode_corrompido(tmp_path: Path) -> None:
    """Bug de firmware dos 16 bits altos (12 dos 113 arquivos reais): o
    timecode salta ~65536 ms pra tras/pra frente. O eixo t_s tem que sair
    monotonico e com os deltas nominais de 250 ms."""
    ecef = _lla2ecef_cm(_LAT, _LON, _ALT)
    tcs = [1000, 1250, 1250 + 65536 + 250, 1250 + 65536 + 500, 2000]
    # ultimo volta pro relogio certo: nao-monotonico dispara o unwrap
    corpos = [_corpo_gps(tc, ecef) for tc in tcs]
    lotes = list(LeitorXrk().ler(_arquivo(tmp_path, corpos)))
    t_s = next(lote for lote in lotes if lote.serie == "gps").tabela.column(
        "t_s"
    ).to_numpy()
    assert t_s.tolist() == pytest.approx([1.0, 1.25, 1.5, 1.75, 2.0])


def test_ler_conflito_de_nome_nao_emite_a_coluna(tmp_path: Path) -> None:
    lotes = list(
        LeitorXrk().ler(_arquivo(tmp_path, _corpos_a_4hz(4), nome_chs_extra="GPS Speed"))
    )
    tabela = next(lote for lote in lotes if lote.serie == "gps").tabela
    assert "GPS Speed" not in tabela.schema.names
    assert "GPS Latitude" in tabela.schema.names


def test_arquivo_so_com_gps_ainda_le(tmp_path: Path) -> None:
    """Canal CHS presente mas de bytes_amostra indecodificavel (4 bytes, sem
    M): antes o ler() levantava 'nenhum canal decodificavel'; com GPS valido
    no arquivo, a serie GPS e amostra suficiente."""
    cnf = _chunk(b"CHS\x00", 1, _chs(1, "MClk", "Master Clk", 100_000, 4))
    partes = [_chunk(b"CNF\x00", 1, cnf)]
    partes.append(_reg_s(0, 1, struct.pack("<i", 1)))
    for corpo in _corpos_a_4hz(3):
        partes.append(_chunk(b"GPS\x00", 1, corpo))
    caminho = tmp_path / "so_gps.xrk"
    caminho.write_bytes(b"".join(partes))
    lotes = list(LeitorXrk().ler(caminho))
    assert len(lotes) == 1
    assert lotes[0].serie == "gps"


def test_sem_gps_e_sem_canal_decodificavel_segue_levantando(tmp_path: Path) -> None:
    cnf = _chunk(b"CHS\x00", 1, _chs(1, "MClk", "Master Clk", 100_000, 4))
    partes = [_chunk(b"CNF\x00", 1, cnf), _reg_s(0, 1, struct.pack("<i", 1))]
    caminho = tmp_path / "nada.xrk"
    caminho.write_bytes(b"".join(partes))
    with pytest.raises(ErroDeLeitura, match="nenhum canal decodificavel"):
        list(LeitorXrk().ler(caminho))
