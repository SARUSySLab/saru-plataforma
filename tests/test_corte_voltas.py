"""Etapa 5: corte de voltas.

O motor e puro (vetor entra, instante sai), entao a maior parte destes testes
roda contra tracado sintetico, sem banco e sem acervo. O tracado e um circulo
com a linha de chegada num ponto conhecido: da pra saber a resposta certa por
construcao, o que um arquivo real nunca da.
"""

from __future__ import annotations

import math
from itertools import pairwise

import numpy as np
import pytest

from saru_poc.pipeline.corte_voltas import (
    ALERTA_CORTE_S,
    MIN_VOLTA_S,
    R_TERRA_M,
    TOLERANCIA_CORTE_S,
    Corte,
    Volta,
    _densidade_plausivel,
    _refinar_corte,
    passagens_de_beacons_ldx,
    passagens_de_contador,
    passagens_de_pulso,
    passagens_por_gps,
    refinar_passagens,
    voltas_de_passagens,
)

LAT0, LON0 = -23.70071, -46.69871  # referencia de Interlagos, so pra dar escala


def _para_graus(x_m: np.ndarray, y_m: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Inverso da projecao do modulo: metros locais de volta pra lat/lon."""
    lat = LAT0 + np.degrees(y_m / R_TERRA_M)
    lon = LON0 + np.degrees(x_m / (R_TERRA_M * math.cos(math.radians(LAT0))))
    return lat, lon


def circuito(
    voltas: float,
    tempo_de_volta_s: float = 60.0,
    hz: float = 10.0,
    raio_m: float = 500.0,
    largada_s: float = 2.0,
):
    """Carro dando `voltas` num circulo, com a linha de chegada na origem.

    A origem local (0, 0) e a coordenada de referencia do layout, e o carro
    passa por ela com rumo +x. Volta inteira = uma passagem.

    `largada_s` atrasa a fase pra captura comecar ANTES da linha, que e o caso
    real: o logger liga no box. Comecar exatamente em cima da linha (lado = 0)
    e ambiguo por construcao e nao produz cruzamento, do jeito que deve ser.
    """
    n = int(voltas * tempo_de_volta_s * hz)
    t = np.arange(n + 1) / hz
    fase = 2 * math.pi * (t - largada_s) / tempo_de_volta_s
    x = raio_m * np.sin(fase)
    y = raio_m - raio_m * np.cos(fase)
    return t, *_para_graus(x, y)


# --- passagens a partir de canal ----------------------------------------


def test_contador_marca_passagem_a_cada_troca_de_valor() -> None:
    t = np.arange(10, dtype=float)
    valores = np.array([0, 0, 0, 1, 1, 1, 2, 2, 3, 3], dtype=float)
    assert passagens_de_contador(t, valores) == [3.0, 6.0, 8.0]


def test_contador_constante_nao_produz_passagem() -> None:
    """Canal presente e parado e o caso do LAP_BEACON do acervo: 0 do inicio ao
    fim. Tem que descer a cascata, nao inventar volta."""
    t = np.arange(10, dtype=float)
    assert passagens_de_contador(t, np.zeros(10)) == []


def test_pulso_marca_so_a_borda_de_subida() -> None:
    """Pulso que dura varias amostras e uma passagem so, nao tres."""
    t = np.arange(10, dtype=float)
    valores = np.array([0, 0, 1, 1, 1, 0, 0, 1, 0, 0], dtype=float)
    assert passagens_de_pulso(t, valores) == [2.0, 7.0]


def test_beacons_do_ldx_saem_de_microssegundo_pra_segundo() -> None:
    bruto = "6.1519e+07,1.81398e+08,2.99982e+08"
    assert passagens_de_beacons_ldx(bruto) == pytest.approx([61.519, 181.398, 299.982])


def test_beacon_ilegivel_nao_vira_zero() -> None:
    """Campo corrompido devolve lista vazia, que a cascata trata como ausencia.
    Devolver [0.0] seria inventar uma passagem no inicio da captura."""
    assert passagens_de_beacons_ldx("6.15e+07,lixo") == []


# --- passagens viram voltas ---------------------------------------------


def test_n_passagens_produzem_n_menos_uma_volta() -> None:
    """Out-lap e in-lap nao sao volta: sao pedaco de volta."""
    voltas = voltas_de_passagens([10.0, 80.0, 150.0, 220.0])
    assert [v.numero for v in voltas] == [1, 2, 3]
    assert [v.tempo_s for v in voltas] == pytest.approx([70.0, 70.0, 70.0])
    assert voltas[0].t_inicio_s == 10.0, "a volta 1 comeca na primeira passagem"
    assert voltas[-1].t_fim_s == 220.0, "nada depois da ultima passagem vira volta"


def test_uma_passagem_so_nao_fecha_volta() -> None:
    assert voltas_de_passagens([42.0]) == []


def test_passagens_grudadas_viram_uma_so() -> None:
    """Debounce: repique na linha nao pode virar volta de meio segundo."""
    voltas = voltas_de_passagens([10.0, 10.4, 80.0])
    assert len(voltas) == 1
    assert voltas[0].tempo_s == pytest.approx(70.0)


def test_volta_do_dominio_passa_pelo_debounce() -> None:
    """A volta mais curta do dominio (kart de 1,0 km) roda em ~40 s, bem acima
    do debounce: a guarda nao pode comer volta legitima."""
    assert MIN_VOLTA_S < 40.0


def test_densidade_rejeita_canal_que_muda_demais() -> None:
    """Caso real do acervo: 136 transicoes em 640 s num canal chamado
    'Lap Number' que vai de 28 a 2572."""
    assert not _densidade_plausivel([float(i) for i in range(136)], 640.0)
    assert _densidade_plausivel([0.0, 74.0, 148.0], 640.0)


# --- corte por GPS -------------------------------------------------------


def test_gps_comecando_em_cima_da_linha_nao_inventa_passagem() -> None:
    """Amostra em cima da linha nao tem lado, entao nao e cruzamento. Contar
    ali daria uma volta a mais, e a primeira sairia com o tempo do out-lap."""
    t, lat, lon = circuito(voltas=2.5, tempo_de_volta_s=60.0, largada_s=0.0)
    instantes, motivo = passagens_por_gps(t, lat, lon, LAT0, LON0)
    assert motivo is None
    assert instantes == pytest.approx([60.0, 120.0], abs=0.15)


def test_gps_corta_o_numero_certo_de_voltas() -> None:
    t, lat, lon = circuito(voltas=3.4, tempo_de_volta_s=60.0, largada_s=2.0)
    instantes, motivo = passagens_por_gps(t, lat, lon, LAT0, LON0)
    assert motivo is None
    # Sai do box 2 s antes da linha e cruza a cada volta inteira depois disso.
    assert instantes == pytest.approx([2.0, 62.0, 122.0, 182.0], abs=0.15)
    voltas = voltas_de_passagens(instantes)
    assert len(voltas) == 3
    for v in voltas:
        assert v.tempo_s == pytest.approx(60.0, abs=0.2)


def test_gps_interpola_entre_amostras() -> None:
    """A 10 Hz a amostra cai a cada 0,1 s; o cruzamento nao. Sem interpolacao o
    tempo de volta erra ate um periodo inteiro, que num kart e 0,25% da volta."""
    t, lat, lon = circuito(voltas=2.2, tempo_de_volta_s=61.37, hz=10.0)
    instantes, motivo = passagens_por_gps(t, lat, lon, LAT0, LON0)
    assert motivo is None
    voltas = voltas_de_passagens(instantes)
    assert voltas[0].tempo_s == pytest.approx(61.37, abs=0.05)
    assert voltas[0].tempo_s != pytest.approx(round(voltas[0].tempo_s, 1), abs=1e-9)


def test_gps_longe_do_layout_nao_corta_e_diz_o_motivo() -> None:
    """As 3 gravacoes GT7 do acervo declaram 'Autodromo de Interlagos' e tem o
    GPS em Donington Park. Isso e o B2 de novo, e tem que aparecer nomeado."""
    t, lat, lon = circuito(voltas=3.0)
    instantes, motivo = passagens_por_gps(t, lat + 76.5, lon + 45.3, LAT0, LON0)
    assert instantes == []
    assert motivo is not None
    assert "nunca passa a menos" in motivo
    assert "km" in motivo, "o motivo tem que dizer o tamanho do erro, nao so que houve"


def test_passagem_no_contra_fluxo_nao_conta_como_volta() -> None:
    """Retorno de box cruzando a linha ao contrario nao e volta. E o que separa
    o gate com sinal do gate circular puro."""
    t, lat, lon = circuito(voltas=2.0, tempo_de_volta_s=60.0)
    # Trecho reto atravessando a origem no sentido -x, depois do fim da sessao.
    t_extra = t[-1] + 1 + np.arange(41) / 10.0
    x_extra = np.linspace(60.0, -60.0, 41)
    y_extra = np.zeros(41)
    lat_e, lon_e = _para_graus(x_extra, y_extra)

    limpo, _ = passagens_por_gps(t, lat, lon, LAT0, LON0)
    com_retorno, _ = passagens_por_gps(
        np.concatenate([t, t_extra]),
        np.concatenate([lat, lat_e]),
        np.concatenate([lon, lon_e]),
        LAT0,
        LON0,
    )
    assert len(com_retorno) == len(limpo), "o retorno pela contramao virou volta"


def test_gps_parado_em_cima_da_linha_nao_vira_volta() -> None:
    """Carro parado no grid balanca dentro do gate sem nunca cruzar."""
    t = np.arange(0, 120, 0.1)
    x = np.full(t.shape, 2.0) + 0.05 * np.sin(t)
    y = np.zeros(t.shape)
    lat, lon = _para_graus(x, y)
    instantes, motivo = passagens_por_gps(t, lat, lon, LAT0, LON0)
    assert instantes == []
    assert motivo is not None


def test_serie_curta_demais_nao_corta() -> None:
    instantes, motivo = passagens_por_gps(
        np.array([0.0]), np.array([LAT0]), np.array([LON0]), LAT0, LON0
    )
    assert instantes == []
    assert motivo is not None


# --- invariantes no banco ------------------------------------------------
# A migration 011 poe a janela e a proveniencia dentro de `volta`. Estes dois
# testes provam que o banco recusa o que o motor nao pode produzir: janela
# invertida e janela que nao bate com o tempo da volta.


@pytest.fixture
def conn():
    try:
        from saru_poc.db import connect

        with connect() as c:
            yield c
            c.rollback()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")


def _uma_gravacao(conn):
    linha = conn.execute(
        "select id, layout_id from gravacao order by created_at limit 1"
    ).fetchone()
    if linha is None:
        pytest.skip("catalogo sem gravacao")
    return linha


def test_banco_recusa_volta_com_janela_invertida(conn) -> None:
    import psycopg

    gid, layout_id = _uma_gravacao(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            """insert into volta (session_id, layout_id, lap_number, lap_time_s,
                                  origem, metodo_versao, t_inicio_s, t_fim_s)
               values (%s,%s,%s,%s,'gps','teste',%s,%s)""",
            (gid, layout_id, 9001, 10.0, 100.0, 90.0),
        )


def test_banco_recusa_janela_que_nao_bate_com_o_tempo(conn) -> None:
    """A janela e o tempo tem que contar a mesma historia: se `lap_time_s` puder
    divergir da fronteira, a etapa 6 recorta um pedaco e mostra outro numero."""
    import psycopg

    gid, layout_id = _uma_gravacao(conn)
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute(
            """insert into volta (session_id, layout_id, lap_number, lap_time_s,
                                  origem, metodo_versao, t_inicio_s, t_fim_s)
               values (%s,%s,%s,%s,'beacon','teste',%s,%s)""",
            (gid, layout_id, 9002, 42.0, 100.0, 190.0),
        )


def test_voltas_gravadas_respeitam_a_janela(conn) -> None:
    """Varre o que a etapa 5 ja escreveu: nenhuma volta pode ter tempo que
    discorde da propria fronteira, nem origem fora do vocabulario."""
    ruins = conn.execute(
        """select count(*) from volta
            where t_fim_s <= t_inicio_s
               or abs((t_fim_s - t_inicio_s) - lap_time_s) > 0.05
               or origem not in ('beacon','gps')"""
    ).fetchone()[0]
    assert ruins == 0


# --- refino do instante contra a serie rapida (excecao 5i, PIL-CT-58) ----
#
# Fixture sintetica com resposta conhecida por construcao. A volta de verdade
# dura P segundos, a serie de velocidade e de 20 Hz e o canal de volta e de
# 1 Hz: o contador vira na primeira amostra de 1 Hz DEPOIS do cruzamento, que e
# o que um contador de voltas faz e o que produz tempo de volta em segundo
# inteiro nas 17 gravacoes do acervo.

PERIODO_VOLTA_S = 87.3  # nao inteiro de proposito: o erro do 1 Hz fica visivel
LARGADA_S = 3.7


def _serie_de_velocidade(hz: float, voltas: float = 6.0):
    """Velocidade periodica na volta, com forma assimetrica.

    Tres harmonicas com fases diferentes: o sinal se repete a cada volta e tem
    um so alinhamento possivel dentro de uma volta, que e o que o refino
    procura. Uma senoide pura teria simetria e nao serviria de fixture.
    """
    n = int(voltas * PERIODO_VOLTA_S * hz)
    t = np.arange(n + 1) / hz
    fase = 2 * math.pi * (t - LARGADA_S) / PERIODO_VOLTA_S
    v = (
        40.0
        + 30.0 * np.sin(fase)
        + 12.0 * np.sin(2 * fase + 0.7)
        + 5.0 * np.sin(3 * fase + 2.1)
    )
    return t, v


def _passagens_verdadeiras(quantas: int = 5) -> list[float]:
    return [LARGADA_S + k * PERIODO_VOLTA_S for k in range(quantas)]


def _passagens_a_1hz(verdadeiras: list[float]) -> list[float]:
    """O que o canal de volta de 1 Hz entrega: a amostra seguinte ao cruzamento."""
    return [float(math.ceil(t)) for t in verdadeiras]


def test_canal_de_1hz_sozinho_entrega_tempo_de_volta_inteiro() -> None:
    """A linha de base que a issue #6 quer consertar, medida aqui pra o teste
    seguinte ter contra o que comparar."""
    grosseiras = _passagens_a_1hz(_passagens_verdadeiras())
    tempos = [b - a for a, b in pairwise(grosseiras)]
    assert all(t == int(t) for t in tempos), "o canal de 1 Hz nao deveria ter decimo"
    assert max(abs(t - PERIODO_VOLTA_S) for t in tempos) > TOLERANCIA_CORTE_S


def test_refino_recupera_o_instante_verdadeiro() -> None:
    """PIL-CT-58. Com serie de velocidade a 20 Hz, o tempo de volta sai a menos
    de `TOLERANCIA_CORTE_S` do verdadeiro, contra ate 1 s de erro sem o refino.

    A ancora nao se move de proposito, entao o que o teste cobra e o TEMPO DE
    VOLTA, que e diferenca entre instantes: o erro absoluto da ancora cancela
    nela, e e o tempo de volta que o piloto le."""
    t_rapido, v_rapido = _serie_de_velocidade(hz=20.0)
    grosseiras = _passagens_a_1hz(_passagens_verdadeiras())

    refinadas, erro, motivo = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)

    assert motivo is None
    # O erro declarado e o passo MEDIDO da serie de apoio, nao um arredondamento
    # dela: `arange(n)/20` acumula alguns femtossegundos, e guardar o numero que
    # saiu da medicao vale mais do que esconder isso atras de um round().
    assert erro == pytest.approx(TOLERANCIA_CORTE_S, abs=1e-9)
    assert len(refinadas) == len(grosseiras), "refino nao pode criar nem sumir passagem"
    tempos = [b - a for a, b in pairwise(refinadas)]
    for volta_s in tempos:
        assert volta_s == pytest.approx(PERIODO_VOLTA_S, abs=TOLERANCIA_CORTE_S)


def test_refino_sem_serie_mais_rapida_nao_muda_nada_e_diz_por_que() -> None:
    """Terceiro criterio da issue: sem serie de taxa maior o corte permanece
    como esta hoje e declara que nao pode refinar."""
    t_rapido, v_rapido = _serie_de_velocidade(hz=1.0)
    grosseiras = _passagens_a_1hz(_passagens_verdadeiras())

    refinadas, erro, motivo = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)

    assert refinadas == grosseiras
    assert erro is None
    assert motivo is not None and "mais rapida" in motivo


def test_refino_com_uma_passagem_so_nao_tem_ancora() -> None:
    t_rapido, v_rapido = _serie_de_velocidade(hz=20.0)
    refinadas, erro, motivo = refinar_passagens([10.0], 1.0, t_rapido, v_rapido)
    assert refinadas == [10.0]
    assert erro is None
    assert motivo is not None


def test_refino_nao_alcanca_serie_que_acaba_logo_depois_das_passagens() -> None:
    """Janela de comparacao menor que a propria busca nao decide nada, e a
    resposta e dizer isso em vez de deslocar por ruido."""
    t_rapido, v_rapido = _serie_de_velocidade(hz=20.0, voltas=4.02)
    grosseiras = _passagens_a_1hz(_passagens_verdadeiras(quantas=5))
    grosseiras = [grosseiras[0], grosseiras[-1]]
    refinadas, erro, motivo = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)
    assert refinadas == grosseiras
    assert erro is None
    assert motivo is not None


class BancoQueExplode:
    """Dublê que denuncia consulta indevida: se o refino chegar ao banco quando
    a porta deveria estar fechada, o teste quebra em vez de passar por sorte."""

    def execute(self, *_a, **_k):
        raise AssertionError("o refino nao deveria consultar o banco aqui")


def _corte_com_voltas() -> Corte:
    corte = Corte(gravacao_id="g")
    corte.voltas = [
        Volta(numero=1, t_inicio_s=0.0, t_fim_s=90.0),
        Volta(numero=2, t_inicio_s=90.0, t_fim_s=180.0),
    ]
    corte.metodo_versao = "canal_pulso-1"
    corte.fonte = "canal LAP_BEACON"
    return corte


def test_porta_do_refino_fecha_para_canal_de_taxa_alta() -> None:
    """Quarto criterio da issue, o duro: gravacao que ja corta bem nao muda de
    instante. Um canal a 100 Hz ja entrega o instante dentro da tolerancia, e o
    refino nem chega a procurar serie de apoio."""
    corte = _corte_com_voltas()
    antes = list(corte.voltas)

    _refinar_corte(BancoQueExplode(), "g", corte, 100.0)

    assert corte.voltas == antes
    assert corte.refinado is False
    assert corte.metodo_versao == "canal_pulso-1"
    assert corte.motivo_refino is not None and "tolerancia" in corte.motivo_refino


def test_porta_do_refino_usa_a_tolerancia_ratificada_como_limiar() -> None:
    """O limiar e `TOLERANCIA_CORTE_S`, nao um numero escrito de novo aqui. Um
    canal exatamente a 1/TOLERANCIA Hz esta no limite e nao refina."""
    no_limite = 1.0 / TOLERANCIA_CORTE_S
    corte = _corte_com_voltas()
    _refinar_corte(BancoQueExplode(), "g", corte, no_limite)
    assert corte.refinado is False
    assert ALERTA_CORTE_S > TOLERANCIA_CORTE_S, "alerta tem que ser pior que tolerancia"
