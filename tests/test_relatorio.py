"""Etapa 7: relatorio e insight.

O foco e a guarda do B1 (volta ideal nunca passa a melhor volta) e a coerencia
das perdas: micro-setor particiona a volta, entao a soma das perdas por
micro-setor TEM que dar o delta da volta contra a referencia. Se essas duas
contas nao fecharem, todo o resto do funil mente com aparencia de precisao.
"""

from __future__ import annotations

from itertools import pairwise

import pytest

from saru_poc.relatorio import (
    APRESENTACAO,
    GRADE_PONTOS,
    melhor_volta,
    micro_setores,
    perdas_por_trecho,
    tempos_em_faixas,
)


def _volta(n: int, tempo: float, valida: bool = True) -> dict:
    return {
        "n": n,
        "tempo_s": tempo,
        "valida": valida,
        "t_inicio_s": 0.0,
        "t_fim_s": tempo,
    }


# --- guarda do B1 --------------------------------------------------------


def test_ideal_sai_da_soma_dos_melhores_setores() -> None:
    voltas = [_volta(1, 100.0), _volta(2, 98.0)]
    setores = {1: [30.0, 40.0, 30.0], 2: [31.0, 38.0, 29.0]}
    mv = melhor_volta(voltas, setores)
    assert mv["melhor_volta_n"] == 2
    assert mv["volta_ideal_s"] == pytest.approx(30.0 + 38.0 + 29.0)
    assert mv["margem_para_ideal_s"] == pytest.approx(98.0 - 97.0)
    assert mv["ideal_suprimida"] is False


def test_ideal_e_suprimida_quando_passaria_a_melhor_volta() -> None:
    """O B1: no saru-app a ideal saiu 3:49,289 contra melhor volta de 0:40,560,
    e a tela anunciou "potencial de -188,729 s". Aqui isso e impossivel de
    emitir: se a soma violar a invariante, a ideal nao sai."""
    voltas = [_volta(1, 40.560)]
    # setores de Interlagos aplicados a uma volta de kart, o caso literal do B1
    setores = {1: [70.0, 100.0, 59.0]}
    mv = melhor_volta(voltas, setores)
    assert mv["ideal_suprimida"] is True
    assert mv["volta_ideal_s"] is None
    assert mv["margem_para_ideal_s"] is None


def test_ideal_e_suprimida_com_setor_sem_dado() -> None:
    """Somar 2 de 3 setores daria uma ideal absurdamente menor que a melhor
    volta, e ela passaria na invariante justamente por ser pequena demais."""
    voltas = [_volta(1, 100.0), _volta(2, 98.0)]
    setores = {1: [30.0, None, 30.0], 2: [31.0, None, 29.0]}
    mv = melhor_volta(voltas, setores)
    assert mv["ideal_suprimida"] is True
    assert mv["volta_ideal_s"] is None


def test_volta_invalida_nao_entra_na_melhor_nem_na_ideal() -> None:
    voltas = [_volta(1, 100.0), _volta(2, 80.0, valida=False)]
    setores = {1: [30.0, 40.0, 30.0], 2: [20.0, 30.0, 30.0]}
    mv = melhor_volta(voltas, setores)
    assert mv["melhor_volta_n"] == 1
    assert mv["voltas_validas"] == 1
    assert mv["voltas_totais"] == 2
    assert mv["volta_ideal_s"] == pytest.approx(100.0)


def test_sessao_sem_volta_valida_nao_inventa_melhor() -> None:
    mv = melhor_volta([_volta(1, 100.0, valida=False)], {1: [30.0, 40.0, 30.0]})
    assert mv["voltas_validas"] == 0
    assert mv["ideal_suprimida"] is True


# --- micro-setores e perdas ---------------------------------------------


def test_micro_setores_particionam_a_volta_inteira() -> None:
    faixas = micro_setores(4309.0)
    assert faixas[0]["s_inicio_m"] == 0.0
    assert faixas[-1]["s_fim_m"] == pytest.approx(4309.0)
    for a, b in pairwise(faixas):
        assert a["s_fim_m"] == pytest.approx(b["s_inicio_m"]), "faixa com buraco"


def test_soma_das_perdas_por_micro_setor_da_o_delta_da_volta() -> None:
    """Coerencia que a tela promete: se o funil diz que a volta foi 3,4 s
    melhor, a soma das perdas por trecho tem que dar 3,4 s. Medido com dado real
    do acervo: -3,447 s de delta e -3,447 s de soma."""
    import numpy as np

    faixas = micro_setores(3000.0, passo_m=1000.0)
    hz = 20.0
    t_a = np.arange(0.0, 100.0 + 1 / hz, 1 / hz)
    t_b = np.arange(0.0, 110.0 + 1 / hz, 1 / hz)
    s_a = np.linspace(0.0, 3000.0, len(t_a))
    s_b = np.linspace(0.0, 3000.0, len(t_b))

    tempos_a = tempos_em_faixas(t_a, s_a, faixas, t_inicio=0.0, t_fim=float(t_a[-1]))
    tempos_b = tempos_em_faixas(t_b, s_b, faixas, t_inicio=0.0, t_fim=float(t_b[-1]))
    itens = perdas_por_trecho(faixas, tempos_a, tempos_b, modo="micro_setor")
    assert sum(i["perda_s"] for i in itens) == pytest.approx(-10.0, abs=0.05)


def test_perdas_saem_ordenadas_da_maior_perda_pro_maior_ganho() -> None:
    faixas = micro_setores(3000.0, passo_m=1000.0)
    ids = [f["id"] for f in faixas]
    a = {ids[0]: 31.0, ids[1]: 30.0, ids[2]: 34.0}
    b = {ids[0]: 30.0, ids[1]: 30.0, ids[2]: 36.0}
    itens = perdas_por_trecho(faixas, a, b, modo="micro_setor")
    assert [round(i["perda_s"], 3) for i in itens] == [1.0, 0.0, -2.0]


def test_ganho_aparece_como_perda_negativa_e_nao_e_escondido() -> None:
    """Esconder o ganho e o que faz o delta acumulado mentir: ele so subiria."""
    faixas = micro_setores(1000.0, passo_m=1000.0)
    itens = perdas_por_trecho(
        faixas, {faixas[0]["id"]: 28.0}, {faixas[0]["id"]: 30.0}, modo="curva"
    )
    assert itens[0]["perda_s"] == pytest.approx(-2.0)


def test_trecho_sem_tempo_nos_dois_lados_nao_vira_item() -> None:
    """Comparar contra trecho que a referencia nao tem daria perda igual ao
    tempo inteiro do trecho, o que apontaria a maior perda da sessao no lugar
    onde faltou dado."""
    faixas = micro_setores(3000.0, passo_m=1000.0)
    ids = [f["id"] for f in faixas]
    itens = perdas_por_trecho(
        faixas, {ids[0]: 30.0, ids[1]: 30.0}, {ids[0]: 29.0}, modo="curva"
    )
    assert [i["trecho_id"] for i in itens] == [ids[0]]


def test_fase_sai_declarada_como_indisponivel() -> None:
    """A tabela `fase` esta vazia no catalogo, entao tempo por fase nao existe.
    O contrato pede que isso seja DECLARADO, nao omitido."""
    faixas = micro_setores(1000.0, passo_m=1000.0)
    item = perdas_por_trecho(
        faixas, {faixas[0]["id"]: 30.0}, {faixas[0]["id"]: 29.0}, modo="curva"
    )[0]
    assert item["tempo_por_fase"]["disponivel"] is False
    assert item["tempo_por_fase"]["motivo"] == "sem_catalogo_de_curva"


# --- apresentacao --------------------------------------------------------


def test_de_para_cobre_os_canais_que_o_front_le() -> None:
    """O front tem duas listas hardcoded de canal. Se o de-para nao cobrir um
    deles, o bloco desenha zero em vez de declarar ausencia, e erro de unidade
    nao aparece em nenhum validador de shape."""
    nomes = {v[0] for v in APRESENTACAO.values()}
    for esperado in (
        "velocidade",
        "acelerador",
        "freio",
        "direcao",
        "marcha",
        "rpm",
        "acel_lat",
        "acel_lon",
    ):
        assert esperado in nomes, f"o front le canais.{esperado} e o de-para nao emite"


def test_velocidade_sai_em_km_por_hora() -> None:
    """`useAmostras.calcularDelta` divide por 3.6 hardcoded. Emitir m/s faria o
    delta sair 3,6x errado sem quebrar tipo nenhum."""
    nome, fator, unidade = APRESENTACAO["speed"]
    assert (nome, unidade) == ("velocidade", "km/h")
    assert fator == pytest.approx(3.6)


def test_grade_bate_com_a_que_o_front_espera() -> None:
    assert GRADE_PONTOS == 900
