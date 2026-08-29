"""Etapa 6: decomposicao em tempo por trecho.

O motor e puro: recebe eixo de tempo, eixo de distancia e a lista de segmentos
do layout, devolve tempo por segmento. Os testes usam um perfil de velocidade
sintetico, onde a resposta certa e conhecida por construcao.
"""

from __future__ import annotations

import numpy as np
import pytest

from saru_poc.pipeline.decomposicao import (
    FATOR_MAX,
    FATOR_MIN,
    distancia_por_canal,
    distancia_por_gps,
    distancia_por_velocidade,
    fechar_no_layout,
    tempos_por_segmento,
)

# Tres setores de um layout de 3.000 m, particionando a volta inteira, como o
# catalogo faz (medido: 3 setores por layout, de 0 ao comprimento).
SETORES = [
    ("s1", "setor", 0.0, 1000.0),
    ("s2", "setor", 1000.0, 2000.0),
    ("s3", "setor", 2000.0, 3000.0),
]


def volta_constante(
    v_ms: float = 30.0, comprimento_m: float = 3000.0, hz: float = 20.0
):
    """Volta a velocidade constante: o tempo de cada setor e conhecido na conta."""
    duracao = comprimento_m / v_ms
    t = np.arange(0.0, duracao + 1 / hz, 1 / hz)
    return t, np.full(t.shape, v_ms)


# --- eixos de distancia --------------------------------------------------


def test_velocidade_integrada_da_a_distancia() -> None:
    t, v = volta_constante(v_ms=30.0, comprimento_m=3000.0)
    s = distancia_por_velocidade(t, v)
    assert s[0] == 0.0
    assert s[-1] == pytest.approx(3000.0, rel=1e-3)


def test_velocidade_negativa_nao_encurta_a_volta() -> None:
    """Ruido de sensor sem sinal nao pode fazer o carro andar pra tras."""
    t = np.arange(0.0, 10.0, 0.1)
    v = np.full(t.shape, 20.0)
    v[10:20] = -20.0
    s = distancia_por_velocidade(t, v)
    limpa = distancia_por_velocidade(t, np.clip(v, 0, None))
    assert s[-1] == pytest.approx(limpa[-1])
    assert np.all(np.diff(s) >= 0), "o eixo de distancia nao pode retroceder"


def test_canal_de_distancia_sobrevive_ao_reset_na_linha() -> None:
    """`Lap Distance` zera na passagem. O eixo tem que continuar subindo, e nao
    despencar pro negativo no instante do reset."""
    bruta = np.array([2800.0, 2900.0, 3000.0, 0.0, 100.0, 200.0])
    s = distancia_por_canal(bruta)
    assert np.all(np.diff(s) >= 0)
    assert s[-1] == pytest.approx(400.0), "soma so os incrementos validos"


def test_gps_acumula_deslocamento_em_metros() -> None:
    """Um grau de latitude vale ~111 km: serve de regua grosseira da projecao."""
    lat = np.array([0.0, 0.001, 0.002])
    lon = np.zeros(3)
    s = distancia_por_gps(lat, lon)
    assert s[-1] == pytest.approx(222.4, rel=0.01)


# --- fechamento no layout ------------------------------------------------


def test_fechar_no_layout_escala_e_devolve_o_fator() -> None:
    s = np.linspace(0.0, 2940.0, 100)
    fechado, fator, motivo = fechar_no_layout(s, 3000.0)
    assert motivo is None
    assert fator == pytest.approx(3000.0 / 2940.0)
    assert fechado[-1] == pytest.approx(3000.0)


def test_fechar_recusa_divergencia_que_nao_e_calibracao() -> None:
    """Caso do B1: setores de Interlagos (4.309 m) numa volta de kart de 1,1 km.
    Fator 3,9, e a volta tem que ficar sem decomposicao."""
    s = np.linspace(0.0, 1100.0, 100)
    fechado, fator, motivo = fechar_no_layout(s, 4309.0)
    assert fechado is None
    assert fator > FATOR_MAX
    assert motivo is not None and "fora de" in motivo


def test_fechar_recusa_eixo_parado() -> None:
    fechado, _, motivo = fechar_no_layout(np.zeros(50), 3000.0)
    assert fechado is None
    assert motivo is not None


def test_faixa_de_fator_e_estreita_de_proposito() -> None:
    """A faixa e guarda de dominio, nao conveniencia: 10% de folga cobre
    calibracao de velocidade, e nao cobre pista trocada."""
    assert FATOR_MIN == 0.9
    assert FATOR_MAX == 1.1


# --- tempo por trecho ----------------------------------------------------


def test_tempo_de_setor_sai_proporcional_a_velocidade_constante() -> None:
    t, v = volta_constante(v_ms=30.0, comprimento_m=3000.0)
    s = distancia_por_velocidade(t, v)
    tempos = tempos_por_segmento(
        t, s, SETORES, t_inicio=float(t[0]), t_fim=float(t[-1])
    )
    assert set(tempos) == {"s1", "s2", "s3"}
    for chave in ("s1", "s2", "s3"):
        assert tempos[chave] == pytest.approx(1000.0 / 30.0, rel=0.01)


def test_soma_dos_setores_fecha_o_tempo_da_volta() -> None:
    """O trigger da 006 barra soma de setor maior que o tempo do arquivo. As
    bordas externas ancoradas em t_inicio/t_fim sao o que garante o fechamento,
    em vez de sobrar ponta na interpolacao."""
    t, v = volta_constante(v_ms=25.0, comprimento_m=3000.0)
    s = distancia_por_velocidade(t, v)
    t_ini, t_fim = float(t[0]), float(t[-1])
    tempos = tempos_por_segmento(t, s, SETORES, t_inicio=t_ini, t_fim=t_fim)
    assert sum(tempos.values()) == pytest.approx(t_fim - t_ini, abs=0.05)


def test_curva_nao_entra_na_soma_dos_setores() -> None:
    """Curva e subdivisao de setor: somar os dois niveis contaria o mesmo pedaco
    de pista duas vezes."""
    t, v = volta_constante(v_ms=30.0, comprimento_m=3000.0)
    s = distancia_por_velocidade(t, v)
    segmentos = [*SETORES, ("c1", "curva", 1200.0, 1400.0)]
    tempos = tempos_por_segmento(
        t, s, segmentos, t_inicio=float(t[0]), t_fim=float(t[-1])
    )
    soma_setores = sum(v for k, v in tempos.items() if k.startswith("s"))
    assert soma_setores == pytest.approx(float(t[-1] - t[0]), abs=0.05)
    assert tempos["c1"] == pytest.approx(200.0 / 30.0, rel=0.02)


def test_setor_lento_leva_mais_tempo_que_setor_rapido() -> None:
    """A conta tem que responder a forma do perfil, nao so ao comprimento.

    Perfil montado pra fechar 3.000 m exatos: 40 s a 15 m/s (600 m) e 60 s a
    40 m/s (2.400 m). O setor 1 pega o trecho lento inteiro, o setor 3 pega
    somente trecho rapido.
    """
    hz = 20.0
    t = np.arange(0.0, 100.0 + 1 / hz, 1 / hz)
    v = np.where(t < 40.0, 15.0, 40.0)
    s = distancia_por_velocidade(t, v)
    fechado, fator, motivo = fechar_no_layout(s, 3000.0)
    assert motivo is None, f"perfil deveria fechar na faixa, fator {fator:.3f}"
    tempos = tempos_por_segmento(
        t, fechado, SETORES, t_inicio=float(t[0]), t_fim=float(t[-1])
    )
    assert tempos["s1"] > tempos["s3"]
    # 600 m a 15 m/s (40 s) mais 400 m a 40 m/s (10 s).
    assert tempos["s1"] == pytest.approx(50.0, rel=0.02)
    assert tempos["s3"] == pytest.approx(25.0, rel=0.02)


def test_serie_curta_nao_produz_trecho() -> None:
    assert (
        tempos_por_segmento(
            np.array([0.0]), np.array([0.0]), SETORES, t_inicio=0.0, t_fim=1.0
        )
        == {}
    )
