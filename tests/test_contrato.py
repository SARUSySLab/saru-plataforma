"""Validador do contrato de saida.

Estes testes existem porque "zero erro" so vale se o validador for capaz de
achar erro. A primeira versao dele aprovava o fixture com 0 erros E tinha um bug
que ignorava o ramo degradado inteiro (o regex de type alias parava no primeiro
`;`, que em `Degradado` esta DENTRO do objeto). O fixture nao tem nenhum bloco
degradado, entao nada denunciava. Cada teste abaixo e uma mutacao que o
validador tem obrigacao de pegar.
"""

from __future__ import annotations

import copy
import json

import pytest

from saru_poc.contrato import CONTRATO_TS, ErroDeContrato, carregar, validar

FIXTURE = CONTRATO_TS.parents[1] / "fixtures" / "relatorio.json"

pytestmark = pytest.mark.skipif(
    not CONTRATO_TS.exists(), reason="contract.ts nao encontrado"
)


@pytest.fixture(scope="module")
def tipos():
    return carregar()


@pytest.fixture
def base():
    if not FIXTURE.exists():
        pytest.skip("fixture do front nao gerado")
    return json.loads(FIXTURE.read_text())


DEGRADADO = {
    "disponivel": False,
    "motivo": "sem_gps",
    "texto": "sem GPS nesta captura",
}


def test_o_contrato_declara_o_que_o_parser_espera(tipos) -> None:
    assert "Relatorio" in tipos.interfaces
    assert "SerieAmostras" in tipos.interfaces
    # O alias tem que vir INTEIRO: o bug original guardava so ate o primeiro `;`.
    assert tipos.alias["Degradado"].endswith("}")
    assert "texto" in tipos.alias["Degradado"]
    assert "sem_gps" in tipos.alias["MotivoDegradacao"]


def test_fixture_do_front_bate_com_o_contrato(base, tipos) -> None:
    assert validar(base, "Relatorio", tipos) == []


def test_amostras_batem_com_o_contrato(tipos) -> None:
    pasta = FIXTURE.parent / "amostras"
    arquivos = sorted(pasta.glob("volta-*.json"))
    if not arquivos:
        pytest.skip("sem amostras geradas")
    for arquivo in arquivos:
        dado = json.loads(arquivo.read_text())
        assert validar(dado, "SerieAmostras", tipos) == [], arquivo.name


def _mutado(base, mutacao):
    d = copy.deepcopy(base)
    mutacao(d)
    return d


@pytest.mark.parametrize(
    ("nome", "mutacao"),
    [
        (
            "campo obrigatorio ausente",
            lambda d: d["n0"]["melhor_volta"].pop("ideal_suprimida"),
        ),
        (
            "number virou string",
            lambda d: d["n0"]["melhor_volta"].__setitem__("melhor_volta_s", "40.5"),
        ),
        (
            "null onde number e obrigatorio",
            lambda d: d["n0"]["melhor_volta"].__setitem__("melhor_volta_s", None),
        ),
        (
            "literal fora da uniao",
            lambda d: d.__setitem__("resolucao_pista", "chutada"),
        ),
        ("campo a mais", lambda d: d.__setitem__("nota_do_piloto", 87)),
        ("lista virou objeto", lambda d: d["n1"].__setitem__("voltas", {})),
        (
            "boolean onde number",
            lambda d: d["n1"]["voltas"][0].__setitem__("v_max_kmh", True),
        ),
        (
            "string dentro de number[]",
            lambda d: d["n1"]["voltas"][0].__setitem__("setores_s", ["12.3"]),
        ),
        (
            "motivo de degradacao fora da uniao",
            lambda d: d.__setitem__("tracado", {**DEGRADADO, "motivo": "sem_vontade"}),
        ),
        (
            "degradado sem motivo",
            lambda d: d.__setitem__(
                "tracado", {"disponivel": False, "texto": "x"}
            ),
        ),
        (
            "degradado sem texto",
            lambda d: d.__setitem__(
                "tracado", {"disponivel": False, "motivo": "sem_gps"}
            ),
        ),
        (
            "degradado carregando payload de disponivel",
            lambda d: d.__setitem__("tracado", {**DEGRADADO, "pontos": []}),
        ),
        (
            "disponivel sem o payload",
            lambda d: d["n2"]["por_curva"].pop("itens"),
        ),
    ],
)
def test_mutacao_e_detectada(base, tipos, nome, mutacao) -> None:
    erros = validar(_mutado(base, mutacao), "Relatorio", tipos)
    assert erros, f"validador nao pegou: {nome}"


def test_degradado_valido_nao_e_erro(base, tipos) -> None:
    """O ramo degradado e caminho legitimo, nao falha: e assim que o contrato
    diz "nao tenho este dado, e este e o motivo"."""
    d = _mutado(base, lambda x: x.__setitem__("tracado", dict(DEGRADADO)))
    assert validar(d, "Relatorio", tipos) == []


def test_tipo_desconhecido_levanta_em_vez_de_aprovar(tipos) -> None:
    """Aprovar por omissao seria a doenca que este modulo existe pra evitar."""
    import saru_poc.contrato as c

    falso = c.Tipos(interfaces={"X": {"a": "TipoQueNaoExiste"}}, alias={})
    with pytest.raises(ErroDeContrato):
        c.validar({"a": 1}, "X", falso)
