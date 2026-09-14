"""Etapa 6, segunda parte: tracado medido.

As duas guardas do modulo (tamanho do contorno e lugar do contorno) sao o alvo
principal: uma sem a outra deixa passar GPS de outra pista com perimetro
parecido, que e o caso medido nas gravacoes GT7 do acervo.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from saru_poc.pipeline.tracado import (
    DISTANCIA_MAX_DO_REF_M,
    MIN_PONTOS,
    distancia_ao_ponto_m,
    montar,
    projetar,
)

LAT0, LON0 = -23.70071, -46.69871  # linha de chegada de Interlagos
R_TERRA_M = 6_371_000.0


def circulo(comprimento_m: float, n: int = 400, lat0: float = LAT0, lon0: float = LON0):
    """Circulo de perimetro `comprimento_m` passando por (lat0, lon0).

    O ponto (lat0, lon0) fica no circulo, nao no centro: e a linha de chegada.
    """
    raio = comprimento_m / (2 * math.pi)
    fase = np.linspace(0.0, 2 * math.pi, n)
    x = raio * np.sin(fase)
    y = raio - raio * np.cos(fase)
    k = math.cos(math.radians(lat0))
    lat = lat0 + np.degrees(y / R_TERRA_M)
    lon = lon0 + np.degrees(x / (R_TERRA_M * k))
    return lat, lon


def test_tracado_com_tamanho_e_lugar_certos_e_montado() -> None:
    lat, lon = circulo(4309.0)
    pontos, fator, motivo = montar(lat, lon, comprimento_m=4309.0, ref=(LAT0, LON0))
    assert motivo is None
    assert pontos is not None
    assert fator == pytest.approx(1.0, abs=0.02)
    assert set(pontos) == {"x_m", "y_m", "s_m"}
    assert pontos["s_m"][-1] == pytest.approx(4309.0, rel=0.01)
    assert pontos["s_m"][0] == 0.0


def test_origem_da_projecao_e_a_linha_de_chegada() -> None:
    """Ancorar na referencia deixa duas voltas da mesma pista comparaveis ponto
    a ponto, em vez de cada uma nascer na origem que o log escolheu."""
    lat, lon = circulo(4309.0)
    pontos, _, _ = montar(lat, lon, comprimento_m=4309.0, ref=(LAT0, LON0))
    assert pontos is not None
    assert abs(pontos["x_m"][0]) < 1.0
    assert abs(pontos["y_m"][0]) < 1.0


def test_perimetro_errado_e_recusado() -> None:
    """Contorno de kart (1,1 km) contra layout de 4,3 km nao e a mesma pista."""
    lat, lon = circulo(1100.0)
    pontos, fator, motivo = montar(lat, lon, comprimento_m=4309.0, ref=(LAT0, LON0))
    assert pontos is None
    assert fator > 1.1
    assert motivo is not None and "perimetro" in motivo


def test_contorno_certo_no_lugar_errado_e_recusado() -> None:
    """Caso medido: as 3 gravacoes GT7 declaram Interlagos, a distancia
    percorrida confirma Interlagos, e as coordenadas estao em Donington Park.
    O perimetro fecha na faixa, entao so a guarda de LUGAR pega."""
    lat, lon = circulo(4020.0, lat0=52.8310, lon0=-1.3764)  # Donington
    pontos, fator, motivo = montar(lat, lon, comprimento_m=4309.0, ref=(LAT0, LON0))
    assert 0.9 <= fator <= 1.1, "o perimetro tinha que fechar, senao o teste nao prova"
    assert pontos is None
    assert motivo is not None and "lugar errado" in motivo
    assert "km" in motivo


def test_sem_referencia_no_layout_o_tracado_ainda_sai() -> None:
    """19 dos 24 layouts nao tem ref_lat/ref_lon. Sem ancora nao da pra checar
    lugar, e a origem passa a ser o primeiro ponto: o mapa continua valendo,
    porque a forma e relativa."""
    lat, lon = circulo(4011.0, lat0=51.0, lon0=5.0)  # Zolder, sem ref no catalogo
    pontos, _, motivo = montar(lat, lon, comprimento_m=4011.0, ref=None)
    assert motivo is None
    assert pontos is not None


def test_poucos_pontos_nao_viram_tracado() -> None:
    lat, lon = circulo(4309.0, n=MIN_PONTOS - 1)
    pontos, _, motivo = montar(lat, lon, comprimento_m=4309.0, ref=(LAT0, LON0))
    assert pontos is None
    assert motivo is not None


def test_gps_parado_nao_vira_tracado() -> None:
    lat = np.full(100, LAT0)
    lon = np.full(100, LON0)
    pontos, _, motivo = montar(lat, lon, comprimento_m=4309.0, ref=(LAT0, LON0))
    assert pontos is None
    assert motivo is not None


def test_guarda_de_lugar_tolera_a_extensao_da_pista() -> None:
    """A folga da guarda de lugar tem que ser maior que o raio de uma pista e
    muito menor que a distancia entre duas pistas diferentes."""
    lat, lon = circulo(20832.0)  # Nordschleife, a maior do catalogo
    perto = distancia_ao_ponto_m(lat, lon, LAT0, LON0)
    assert perto < DISTANCIA_MAX_DO_REF_M


def test_projecao_bate_com_a_regua_do_grau() -> None:
    x, y = projetar(np.array([LAT0 + 0.001]), np.array([LON0]), LAT0, LON0)
    assert float(y[0]) == pytest.approx(111.2, rel=0.01)
    assert abs(float(x[0])) < 1e-6
