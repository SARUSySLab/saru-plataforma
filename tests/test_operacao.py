"""Espinha operacional: evento, sessao, bateria, contexto, setup.

O teste que mais importa aqui e o de isolamento entre contas: regressao do
achado S1 do saru-app, onde os endpoints de GT7 tinham guard de JWT (sabiam
QUEM estava chamando) mas nenhum filtro por usuario no WHERE, e qualquer conta
autenticada conseguia editar sessao alheia. `rotas/operacao.py` promete 404 (
nunca 403) pra recurso de outro dono, porque 403 ja confirmaria que o id
existe. Este arquivo prova que a promessa se sustenta em cada rota.

Roda contra o Postgres real da PoC, no mesmo padrao de `tests/test_api.py`.
Cada teste cria seus proprios usuarios (e-mail unico via uuid4) pra poder
rodar duas vezes seguidas sem colidir com `uq_usuario_email`.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

os.environ.setdefault("SARU_CICLO_SARUE", "0")

from fastapi.testclient import TestClient  # noqa: E402

SENHA_VALIDA = "senha-de-teste-123"
TRACK_ID_VALIDO = "senna_kart"


@pytest.fixture
def app():
    from saru_poc.api import app as app_fastapi

    try:
        from saru_poc.db import ping

        ping()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")
    return app_fastapi


def usuario_logado(app) -> TestClient:
    """Um TestClient com sessao propria (cookie proprio), usuario novo."""
    cliente = TestClient(app)
    resposta = cliente.post(
        "/api/auth/registro",
        json={"email": f"op-{uuid4()}@teste.saru", "senha": SENHA_VALIDA, "nome": "Piloto"},
    )
    assert resposta.status_code == 201
    return cliente


def criar_evento(cliente, nome: str = "Track day de teste") -> dict:
    resposta = cliente.post(
        "/api/eventos",
        json={
            "track_id": TRACK_ID_VALIDO,
            "name": nome,
            "starts_at": "2026-09-01T09:00:00+00:00",
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_sessao(cliente, evento_id: str) -> dict:
    resposta = cliente.post(
        f"/api/eventos/{evento_id}/sessoes",
        json={"type": "trackday_battery", "label": "sessao de teste", "planned_laps": 8},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def criar_bateria(cliente, sessao_id: str) -> dict:
    resposta = cliente.post(f"/api/sessoes/{sessao_id}/baterias", json={"laps": 8})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def espinha_do_usuario_a(app):
    """Usuario A com evento, sessao e bateria ja montados, pronto pra servir
    de alvo nos testes de isolamento e nos de fluxo feliz."""
    cliente_a = usuario_logado(app)
    evento = criar_evento(cliente_a)
    sessao = criar_sessao(cliente_a, evento["id"])
    bateria = criar_bateria(cliente_a, sessao["id"])
    return cliente_a, evento, sessao, bateria


# --- isolamento entre contas (regressao do achado S1) --------------------


def test_usuario_b_nao_ve_evento_de_a_na_listagem(app, espinha_do_usuario_a) -> None:
    _cliente_a, evento_a, _sessao, _bateria = espinha_do_usuario_a
    cliente_b = usuario_logado(app)

    listagem_b = cliente_b.get("/api/eventos")
    assert listagem_b.status_code == 200
    ids_b = [e["id"] for e in listagem_b.json()]
    assert evento_a["id"] not in ids_b


def test_usuario_b_recebe_404_ao_editar_evento_de_a(app, espinha_do_usuario_a) -> None:
    """Nunca 403: 403 confirmaria pro atacante que o id de evento existe."""
    _cliente_a, evento_a, _sessao, _bateria = espinha_do_usuario_a
    cliente_b = usuario_logado(app)

    resposta = cliente_b.patch(f"/api/eventos/{evento_a['id']}", json={"name": "sequestrado"})
    assert resposta.status_code == 404
    assert resposta.status_code != 403


def test_usuario_b_recebe_404_ao_editar_bateria_de_a(app, espinha_do_usuario_a) -> None:
    _cliente_a, _evento, _sessao, bateria_a = espinha_do_usuario_a
    cliente_b = usuario_logado(app)

    resposta = cliente_b.patch(f"/api/baterias/{bateria_a['id']}", json={"laps": 999})
    assert resposta.status_code == 404
    assert resposta.status_code != 403


def test_usuario_b_recebe_404_no_contexto_da_bateria_de_a(app, espinha_do_usuario_a) -> None:
    _cliente_a, _evento, _sessao, bateria_a = espinha_do_usuario_a
    cliente_b = usuario_logado(app)

    leitura = cliente_b.get(f"/api/baterias/{bateria_a['id']}/contexto")
    assert leitura.status_code == 404
    assert leitura.status_code != 403

    escrita = cliente_b.post(
        f"/api/baterias/{bateria_a['id']}/contexto",
        json={"temperatura_ar_c": 30.0},
    )
    assert escrita.status_code == 404
    assert escrita.status_code != 403


def test_usuario_b_recebe_404_no_setup_da_bateria_de_a(app, espinha_do_usuario_a) -> None:
    _cliente_a, _evento, _sessao, bateria_a = espinha_do_usuario_a
    cliente_b = usuario_logado(app)

    leitura = cliente_b.get(f"/api/baterias/{bateria_a['id']}/setup")
    assert leitura.status_code == 404
    assert leitura.status_code != 403

    escrita = cliente_b.post(
        f"/api/baterias/{bateria_a['id']}/setup",
        json={"valores": {"pressao_dianteira": 28}},
    )
    assert escrita.status_code == 404
    assert escrita.status_code != 403


# --- fluxo feliz -----------------------------------------------------------


def test_fluxo_feliz_evento_sessao_bateria_criados_e_listados(app) -> None:
    cliente = usuario_logado(app)
    evento = criar_evento(cliente)
    sessao = criar_sessao(cliente, evento["id"])
    bateria = criar_bateria(cliente, sessao["id"])

    eventos = cliente.get("/api/eventos").json()
    assert any(e["id"] == evento["id"] for e in eventos)

    sessoes = cliente.get(f"/api/eventos/{evento['id']}/sessoes").json()
    assert any(s["id"] == sessao["id"] for s in sessoes)

    baterias = cliente.get(f"/api/sessoes/{sessao['id']}/baterias").json()
    assert any(b["id"] == bateria["id"] for b in baterias)


def test_criar_evento_com_track_id_inexistente_e_422(app) -> None:
    """O catalogo de layouts e fechado: track_id que nao existe la nao pode
    virar evento pendurado em pista nenhuma."""
    cliente = usuario_logado(app)
    resposta = cliente.post(
        "/api/eventos",
        json={
            "track_id": "pista-que-nao-existe-no-catalogo",
            "name": "evento invalido",
            "starts_at": "2026-09-01T09:00:00+00:00",
        },
    )
    assert resposta.status_code == 422


# --- setup: versionado, nunca sobrescreve -----------------------------------


def test_salvar_setup_duas_vezes_cria_versao_1_e_depois_2(app, espinha_do_usuario_a) -> None:
    cliente_a, _evento, _sessao, bateria_a = espinha_do_usuario_a

    primeira = cliente_a.post(
        f"/api/baterias/{bateria_a['id']}/setup",
        json={"valores": {"pressao_dianteira": 26}, "notas": "primeira ficha"},
    )
    assert primeira.status_code == 201
    assert primeira.json()["versao"] == 1

    segunda = cliente_a.post(
        f"/api/baterias/{bateria_a['id']}/setup",
        json={"valores": {"pressao_dianteira": 27}, "notas": "segunda ficha"},
    )
    assert segunda.status_code == 201
    assert segunda.json()["versao"] == 2

    historico = cliente_a.get(f"/api/baterias/{bateria_a['id']}/setup").json()
    versoes = [item["versao"] for item in historico]
    assert 1 in versoes and 2 in versoes, "a versao 1 nao pode ter sido sobrescrita"


# --- contexto: append-only, mais novo primeiro ------------------------------


def test_contexto_e_append_only_e_get_devolve_o_mais_novo_primeiro(
    app, espinha_do_usuario_a
) -> None:
    cliente_a, _evento, _sessao, bateria_a = espinha_do_usuario_a

    primeiro = cliente_a.post(
        f"/api/baterias/{bateria_a['id']}/contexto",
        json={"temperatura_ar_c": 20.0, "notas_piloto": "leitura das 9h"},
    )
    assert primeiro.status_code == 201

    segundo = cliente_a.post(
        f"/api/baterias/{bateria_a['id']}/contexto",
        json={"temperatura_ar_c": 28.0, "notas_piloto": "leitura das 14h"},
    )
    assert segundo.status_code == 201

    historico = cliente_a.get(f"/api/baterias/{bateria_a['id']}/contexto").json()
    # dois POSTs tem que virar dois registros, nao uma correcao do mesmo
    assert len(historico) == 2
    # o GET devolve o mais novo primeiro: a leitura das 14h na frente da das 9h
    assert historico[0]["notas_piloto"] == "leitura das 14h"
    assert historico[1]["notas_piloto"] == "leitura das 9h"
