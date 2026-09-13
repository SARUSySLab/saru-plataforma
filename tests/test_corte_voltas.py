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
# Fixture sintetica com resposta conhecida por construcao. A serie de
# velocidade e funcao da POSICAO na pista, e cada volta pode durar um tempo
# diferente: e o que separa esta fixture da primeira versao dela, que so tinha
# voltas identicas e por isso escondia o defeito de alinhar volta inteira
# contra volta inteira.
#
# O canal de volta de 1 Hz marca a passagem na primeira amostra DEPOIS do
# cruzamento, que e o que um contador de voltas faz e o que produz tempo de
# volta em segundo inteiro nas 17 gravacoes do acervo.

PERIODO_VOLTA_S = 87.3
LARGADA_S = 3.7


def _perfil(posicao: np.ndarray) -> np.ndarray:
    """Velocidade em funcao da posicao na pista, `posicao` em [0, 1).

    Tres harmonicas com fases diferentes: o sinal se repete a cada volta e tem
    um so alinhamento possivel dentro de uma volta, que e o que o refino
    procura. Uma senoide pura teria simetria e nao serviria de fixture.
    """
    f = 2 * math.pi * posicao
    return (
        40.0
        + 30.0 * np.sin(f)
        + 12.0 * np.sin(2 * f + 0.7)
        + 5.0 * np.sin(3 * f + 2.1)
    )


def _sessao(duracoes: list[float], hz: float = 20.0, rabo_s: float = 20.0):
    """Passagens verdadeiras e serie de velocidade de uma sessao sintetica.

    Cada elemento de `duracoes` e o tempo de uma volta. Volta mais lenta
    percorre a MESMA pista em mais tempo, entao o sinal dela sai esticado no
    tempo: e exatamente o que quebra o alinhamento por volta inteira.
    """
    passagens = [LARGADA_S]
    for d in duracoes:
        passagens.append(passagens[-1] + d)
    t = np.arange(0.0, passagens[-1] + rabo_s, 1 / hz)
    s = np.zeros_like(t)
    for k, d in enumerate(duracoes):
        dentro = (t >= passagens[k]) & (t < passagens[k + 1])
        s[dentro] = (t[dentro] - passagens[k]) / d
    depois = t >= passagens[-1]
    s[depois] = ((t[depois] - passagens[-1]) / duracoes[-1]) % 1.0
    antes = t < passagens[0]
    s[antes] = ((t[antes] - passagens[0]) / duracoes[0]) % 1.0
    return passagens, t, _perfil(s)


def _a_1hz(verdadeiras: list[float]) -> list[float]:
    """O que o canal de volta de 1 Hz entrega: a amostra seguinte ao cruzamento."""
    return [float(math.ceil(x)) for x in verdadeiras]


def _erro_maximo(instantes: list[float], duracoes: list[float]) -> float:
    tempos = [b - a for a, b in pairwise(instantes)]
    return max(abs(x - d) for x, d in zip(tempos, duracoes, strict=True))


def test_canal_de_1hz_sozinho_entrega_tempo_de_volta_inteiro() -> None:
    """A linha de base que a issue #6 quer consertar, medida aqui pra os testes
    seguintes terem contra o que comparar."""
    duracoes = [PERIODO_VOLTA_S] * 4
    verdadeiras, _t, _v = _sessao(duracoes)
    grosseiras = _a_1hz(verdadeiras)
    tempos = [b - a for a, b in pairwise(grosseiras)]
    assert all(x == int(x) for x in tempos), "o canal de 1 Hz nao deveria ter decimo"
    assert _erro_maximo(grosseiras, duracoes) > TOLERANCIA_CORTE_S


def test_refino_recupera_o_instante_verdadeiro() -> None:
    """PIL-CT-58, caso periodico. Com serie de velocidade a 20 Hz o tempo de
    volta sai a menos de `TOLERANCIA_CORTE_S` do verdadeiro.

    A ancora nao se move de proposito, entao o que o teste cobra e o TEMPO DE
    VOLTA, que e diferenca entre instantes: o erro absoluto da ancora cancela
    nela, e e o tempo de volta que o piloto le."""
    duracoes = [PERIODO_VOLTA_S] * 4
    verdadeiras, t_rapido, v_rapido = _sessao(duracoes)
    grosseiras = _a_1hz(verdadeiras)

    refino = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)

    assert refino.motivo is None
    assert refino.recusadas == 0
    assert refino.alinhadas == len(duracoes)
    assert len(refino.instantes) == len(grosseiras), "refino nao cria nem some passagem"
    assert _erro_maximo(refino.instantes, duracoes) <= TOLERANCIA_CORTE_S
    # `resolucao_s` e o passo da grade, e o teste cobra isso E NAO CONFUNDE com
    # erro: o erro real e medido acima, contra a duracao verdadeira da fixture.
    assert refino.resolucao_s == pytest.approx(0.05, abs=1e-9)


def test_refino_aguenta_voltas_de_duracao_diferente() -> None:
    """Contraexemplo do revisor. Variacao de 1 a 2 s entre voltas e o normal de
    uma sessao, e a primeira versao do refino PIORAVA o 1 Hz nesse caso: erro
    maximo subia de 0,60 s para 1,35 s, porque alinhar volta inteira contra
    volta inteira alinha o erro de ritmo em vez da posicao na pista."""
    duracoes = [87.3, 88.9, 86.4, 87.9]
    verdadeiras, t_rapido, v_rapido = _sessao(duracoes)
    grosseiras = _a_1hz(verdadeiras)

    refino = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)

    assert refino.recusadas == 0
    assert _erro_maximo(refino.instantes, duracoes) <= TOLERANCIA_CORTE_S


def test_refino_com_parada_no_meio_nao_piora_o_1hz_e_declara() -> None:
    """Contraexemplo do revisor. A volta com parada no meio nao tem sinal em
    comum com a volta ancora, entao o encaixe nao converge. A resposta e ficar
    com o instante grosseiro e DIZER isso, nao deslocar por um encaixe que nao
    encaixa: o refino nunca pode entregar pior do que o 1 Hz ja entregava."""
    duracoes = [87.3, 132.0, 87.6, 87.4]
    verdadeiras, t_rapido, v_rapido = _sessao(duracoes)
    grosseiras = _a_1hz(verdadeiras)
    erro_1hz = _erro_maximo(grosseiras, duracoes)

    refino = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)

    assert refino.recusadas >= 1, "a volta com parada tinha que ser recusada"
    assert refino.motivo is not None and "grosseiro" in refino.motivo
    assert _erro_maximo(refino.instantes, duracoes) <= erro_1hz
    # A passagem recusada fica com o valor original, byte a byte.
    assert any(a == b for a, b in zip(refino.instantes, grosseiras, strict=True))


def test_refino_com_volta_de_saida_mais_lenta_nao_piora_o_1hz() -> None:
    """Contraexemplo do revisor. A volta de saida e mais lenta que o resto, e e
    ela que vira a ancora. A primeira versao subia o erro de 0,60 s para 1,00 s.
    Aqui o teste cobra o que da pra garantir sem medicao no acervo: o refino
    melhora, e em nenhum caso piora."""
    duracoes = [95.0, 87.4, 87.2, 87.5]
    verdadeiras, t_rapido, v_rapido = _sessao(duracoes)
    grosseiras = _a_1hz(verdadeiras)
    erro_1hz = _erro_maximo(grosseiras, duracoes)

    refino = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)

    assert _erro_maximo(refino.instantes, duracoes) < erro_1hz


def test_refino_sem_serie_mais_rapida_nao_muda_nada_e_diz_por_que() -> None:
    """Terceiro criterio da issue: sem serie de taxa maior o corte permanece
    como esta hoje e declara que nao pode refinar."""
    duracoes = [PERIODO_VOLTA_S] * 4
    verdadeiras, t_rapido, v_rapido = _sessao(duracoes, hz=1.0)
    grosseiras = _a_1hz(verdadeiras)

    refino = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)

    assert refino.instantes == grosseiras
    assert refino.resolucao_s is None
    assert refino.alinhadas == 0
    assert refino.motivo is not None and "mais rapida" in refino.motivo


def test_refino_com_uma_passagem_so_nao_tem_ancora() -> None:
    _v, t_rapido, v_rapido = _sessao([PERIODO_VOLTA_S] * 4)
    refino = refinar_passagens([10.0], 1.0, t_rapido, v_rapido)
    assert refino.instantes == [10.0]
    assert refino.resolucao_s is None
    assert refino.motivo is not None


def test_refino_nao_alcanca_serie_que_acaba_logo_depois_das_passagens() -> None:
    """Janela que nao cabe na serie de apoio nao decide nada, e a resposta e
    dizer isso em vez de deslocar por ruido."""
    duracoes = [PERIODO_VOLTA_S] * 4
    verdadeiras, t_rapido, v_rapido = _sessao(duracoes, rabo_s=0.5)
    grosseiras = _a_1hz([verdadeiras[0], verdadeiras[-1]])

    refino = refinar_passagens(grosseiras, 1.0, t_rapido, v_rapido)

    assert refino.instantes == grosseiras
    assert refino.alinhadas == 0
    assert refino.motivo is not None


def test_refino_com_sinal_constante_nao_aceita_qualquer_deslocamento() -> None:
    """Carro parado ou canal travado da residuo zero em todo deslocamento, e
    aceitar o primeiro seria inventar instante."""
    t_rapido = np.arange(0.0, 400.0, 0.05)
    v_rapido = np.full_like(t_rapido, 40.0)
    refino = refinar_passagens([4.0, 91.0, 179.0], 1.0, t_rapido, v_rapido)
    assert refino.instantes == [4.0, 91.0, 179.0]
    assert refino.alinhadas == 0
    assert refino.motivo is not None and "constante" in refino.motivo


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


def test_resolucao_nao_e_o_erro_do_instante() -> None:
    """A grade de 0,05 s nao prova erro de 0,05 s, e o contrato desta funcao nao
    pode deixar PIL-CT-58 passar por construcao.

    Mesma serie de apoio, mesma resolucao, erros reais muito diferentes: no caso
    periodico o refino acerta na mosca, no caso com parada no meio sobra 0,3 s.
    Se `resolucao_s` fosse lido como erro, os dois se declarariam conformes."""
    periodicas = [PERIODO_VOLTA_S] * 4
    com_parada = [87.3, 132.0, 87.6, 87.4]

    refinos = []
    for duracoes in (periodicas, com_parada):
        verdadeiras, t_rapido, v_rapido = _sessao(duracoes)
        refino = refinar_passagens(_a_1hz(verdadeiras), 1.0, t_rapido, v_rapido)
        refinos.append((refino, _erro_maximo(refino.instantes, duracoes)))

    (a, erro_a), (b, erro_b) = refinos
    assert a.resolucao_s == pytest.approx(b.resolucao_s, abs=1e-9)
    assert erro_b > erro_a + 0.2, "os dois casos tinham que ter erro real distinto"
    assert erro_b > (b.resolucao_s or 0.0), "resolucao subestima o erro real aqui"
