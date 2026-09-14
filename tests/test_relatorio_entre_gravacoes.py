"""Referencia cruzada entre gravacoes (`?ref_gravacao=`).

Ate 28/08 as perdas do N0 e do N2 so podiam ser calculadas contra um par de
voltas da MESMA gravacao (ver `perdas_por_trecho` em relatorio.py). Mudanca de
contrato aprovada pelo Lucas: `referencia` passa a poder apontar pra uma volta
de OUTRA gravacao, pra comparar dias e baterias diferentes.

Cobertura:
  - referencia na mesma gravacao (passando `ref_gravacao` explicito, igual ao
    proprio `gravacao_id`) tem que sair IDENTICA a nao passar o parametro.
  - referencia em outra gravacao da MESMA pista funciona e muda as perdas.
  - referencia em pista diferente e a guarda do B2: 422, nunca calculada.
  - referencia de gravacao de outro usuario e 404 (o filtro de dono do
    `_minha` vale pros dois lados do par, nao so pra `gravacao_id`).
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


def _adotar_acervo(user_id: str) -> None:
    """Regra de escopo de 29/08: gravacao sem dono nao aparece mais pra
    nenhuma conta. Os testes de leitura usam o acervo semeado, entao a
    fixture ADOTA essas gravacoes pro usuario do teste. Tambem re-adota as
    que ficaram com usuarios de execucoes anteriores (email teste-*@saru.dev),
    senao o modulo so rodaria uma vez por banco.
    """
    from saru_poc.db import connect

    with connect() as conn:
        conn.execute(
            """update gravacao set user_id = %s
                where user_id is null
                   or user_id in (select id from usuario where email like %s)""",
            (user_id, "teste-%@saru.dev"),
        )
        conn.commit()


@pytest.fixture(scope="module")
def cliente():
    """Cliente autenticado. Mesmo padrao de `tests/test_api.py`: usuario novo a
    cada execucao, as gravacoes lidas sao do acervo (`user_id is null`)."""
    from saru_poc.api import app

    try:
        from saru_poc.db import ping

        ping()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")

    c = TestClient(app)
    resposta = c.post(
        "/api/auth/registro",
        json={
            "email": f"teste-ref-{uuid4()}@saru.dev",
            "senha": "senha-de-teste-123",
            "nome": "teste",
        },
    )
    assert resposta.status_code == 201, resposta.text
    _adotar_acervo(resposta.json()["id"])
    return c


def _catalogo_por_pista(cliente) -> dict[str, list[dict]]:
    """Gravacoes do acervo com volta E trecho, agrupadas por `layout_nome`."""
    corpo = cliente.get("/api/gravacoes", params={"com_volta": True}).json()
    completas = [g for g in corpo if g["voltas"] > 1 and g["trechos"] > 0]
    por_pista: dict[str, list[dict]] = {}
    for g in completas:
        por_pista.setdefault(g["layout_nome"] or "", []).append(g)
    return por_pista


@pytest.fixture(scope="module")
def par_mesma_pista(cliente):
    """Duas gravacoes DIFERENTES da MESMA pista, as duas com relatorio cheio."""
    por_pista = _catalogo_por_pista(cliente)
    for nome, gravacoes in por_pista.items():
        if nome and len(gravacoes) >= 2:
            return gravacoes[0]["gravacao_id"], gravacoes[1]["gravacao_id"]
    pytest.skip("acervo nao tem duas gravacoes completas da mesma pista")


@pytest.fixture(scope="module")
def par_pista_diferente(cliente):
    """Duas gravacoes de pistas DIFERENTES, as duas com relatorio cheio."""
    por_pista = _catalogo_por_pista(cliente)
    pistas = [(nome, gravacoes) for nome, gravacoes in por_pista.items() if nome]
    if len(pistas) < 2:
        pytest.skip("acervo nao tem gravacoes completas de duas pistas diferentes")
    return pistas[0][1][0]["gravacao_id"], pistas[1][1][0]["gravacao_id"]


@pytest.fixture(scope="module")
def gravacao_de_outro_usuario(par_mesma_pista):
    """Uma linha de `gravacao` de verdade, dona de um usuario que NAO e o
    `cliente` do modulo. So precisa existir no banco: a checagem de dono
    acontece antes de `montar` tocar em qualquer telemetria dela.
    """
    from saru_poc.db import connect

    gravacao_id, _ = par_mesma_pista
    with connect() as conn:
        layout = conn.execute(
            "select layout_id from gravacao where id = %s", (gravacao_id,)
        ).fetchone()[0]
        outro_id = conn.execute(
            "insert into usuario (email, password_hash, name, role) "
            "values (%s, %s, %s, %s) returning id",
            (f"outro-{uuid4()}@saru.dev", "x", "outro", "owner"),
        ).fetchone()[0]
        alheia_id = conn.execute(
            "insert into gravacao (user_id, layout_id) values (%s, %s) returning id",
            (outro_id, layout),
        ).fetchone()[0]
        conn.commit()
        yield str(alheia_id)
        # limpeza: nao deixa lixo de teste no banco compartilhado da PoC
        conn.execute("delete from gravacao where id = %s", (alheia_id,))
        conn.execute("delete from usuario where id = %s", (outro_id,))
        conn.commit()


def test_ref_gravacao_igual_a_propria_e_identico_a_nao_passar_o_parametro(
    cliente, par_mesma_pista
) -> None:
    """Requisito 1: `ref_gravacao_id=None` (default) tem que continuar
    identico byte a byte a passar a PROPRIA gravacao como referencia."""
    gravacao_id, _ = par_mesma_pista
    base = cliente.get(f"/api/relatorio/{gravacao_id}")
    assert base.status_code == 200
    voltas = [v["n"] for v in base.json()["n1"]["voltas"]]
    if len(voltas) < 2:
        pytest.skip("precisa de 2 voltas pra fixar o par volta/referencia")
    params = {"volta": voltas[0], "referencia": voltas[-1]}

    sem_ref = cliente.get(f"/api/relatorio/{gravacao_id}", params=params).json()
    com_ref_propria = cliente.get(
        f"/api/relatorio/{gravacao_id}",
        params={**params, "ref_gravacao": gravacao_id},
    ).json()

    assert sem_ref == com_ref_propria


def test_referencia_em_outra_gravacao_da_mesma_pista_muda_as_perdas(
    cliente, tipos_de_contrato, par_mesma_pista
) -> None:
    """O nucleo da mudanca: referencia pode vir de outra captura, mesma pista,
    e o par cruzado tem que render um `Relatorio` valido com perdas diferentes
    das que saem comparando a gravacao contra ela mesma."""
    from saru_poc.contrato import validar

    analisada, referencia = par_mesma_pista

    base = cliente.get(f"/api/relatorio/{analisada}")
    assert base.status_code == 200
    voltas_analisada = [v["n"] for v in base.json()["n1"]["voltas"]]
    if not voltas_analisada:
        pytest.skip("gravacao analisada sem volta")
    n_analisada = voltas_analisada[-1]

    ref_relatorio = cliente.get(f"/api/relatorio/{referencia}")
    assert ref_relatorio.status_code == 200
    voltas_referencia = [v["n"] for v in ref_relatorio.json()["n1"]["voltas"]]
    if not voltas_referencia:
        pytest.skip("gravacao de referencia sem volta")
    n_referencia = voltas_referencia[0]

    cruzado = cliente.get(
        f"/api/relatorio/{analisada}",
        params={
            "volta": n_analisada,
            "referencia": n_referencia,
            "ref_gravacao": referencia,
        },
    )
    assert cruzado.status_code == 200
    corpo = cruzado.json()
    assert validar(corpo, "Relatorio", tipos_de_contrato) == []
    # a gravacao continua sendo a analisada: ref_gravacao muda so de ONDE vem
    # a referencia, nao qual gravacao esta em foco na tela
    assert corpo["gravacao_id"] == analisada

    mesma_gravacao = cliente.get(
        f"/api/relatorio/{analisada}",
        params={"volta": n_analisada, "referencia": n_analisada},
    ).json()

    perdas_cruzada = [i["perda_s"] for i in corpo["n0"]["perdas_top3"]["itens"]]
    perdas_mesma = [
        i["perda_s"] for i in mesma_gravacao["n0"]["perdas_top3"]["itens"]
    ]
    assert perdas_cruzada != perdas_mesma, (
        "trocar a fonte da referencia pra outra gravacao nao mudou as perdas"
    )


def test_referencia_em_pista_diferente_e_422(cliente, par_pista_diferente) -> None:
    """A guarda do B2: layouts diferentes nunca podem ser comparados, porque a
    grade de distancia de uma pista nao vale pra outra."""
    analisada, referencia = par_pista_diferente
    resposta = cliente.get(
        f"/api/relatorio/{analisada}", params={"ref_gravacao": referencia}
    )
    assert resposta.status_code == 422
    detalhe = str(resposta.json()["detail"])
    assert "pista" in detalhe.lower()


def test_referencia_de_gravacao_de_outro_usuario_e_404(
    cliente, par_mesma_pista, gravacao_de_outro_usuario
) -> None:
    """O filtro de dono do `_minha` vale pro `ref_gravacao` tambem: gravacao
    que nao e sua nem do acervo tem que sumir como 404, nunca 403 (403
    confirmaria que o id existe)."""
    analisada, _ = par_mesma_pista
    resposta = cliente.get(
        f"/api/relatorio/{analisada}",
        params={"ref_gravacao": gravacao_de_outro_usuario},
    )
    assert resposta.status_code == 404


@pytest.fixture(scope="module")
def tipos_de_contrato():
    from saru_poc.contrato import carregar

    return carregar()
