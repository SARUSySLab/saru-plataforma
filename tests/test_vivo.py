"""Ingestao ao vivo: gateway do carro alimentando o pit wall.

Roda contra o Postgres real da PoC, no mesmo padrao dos outros testes de rota.
O que estes casos protegem, em ordem de importancia:

  1. token de um carro nao escreve no carro de outro (o veiculo vem do TOKEN,
     nunca do corpo);
  2. reenvio de lote e idempotente, porque 4G de autodromo cai e o gateway
     repete o POST quando nao ve resposta;
  3. sequencia fora de ordem nao some: ela e contada e declarada;
  4. a leitura devolve IDADE do dado em vez de fingir que carro calado esta
     parado.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

os.environ.setdefault("SARU_CICLO_SARUE", "0")

from fastapi.testclient import TestClient  # noqa: E402

SENHA_VALIDA = "senha-de-teste-123"


@pytest.fixture
def app():
    from saru_poc.api import app as app_fastapi

    try:
        from saru_poc.db import ping

        ping()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")
    from saru_poc.vivo import BUFFER

    BUFFER.limpar()
    return app_fastapi


def dono_logado(app) -> TestClient:
    cliente = TestClient(app)
    r = cliente.post(
        "/api/auth/registro",
        json={"email": f"vivo-{uuid4()}@teste.saru", "senha": SENHA_VALIDA, "nome": "Engenheiro"},
    )
    assert r.status_code == 201
    return cliente


def criar_carro(cliente, apelido: str, numero: str | None = None) -> dict:
    r = cliente.post("/api/vivo/veiculos", json={"apelido": apelido, "numero": numero, "modelo": "M2"})
    assert r.status_code == 201, r.text
    return r.json()


def lote(seq: int, t0: float = 0.0, n: int = 5) -> dict:
    return {
        "seq": seq,
        "sessao_id": "bateria-3",
        "amostras": [
            {"t_s": t0 + i * 0.02, "canais": {"speed": 40.0 + i, "rpm": 5000 + i}} for i in range(n)
        ],
    }


def test_sem_token_recusa(app):
    r = TestClient(app).post("/api/vivo/amostras", json=lote(1))
    assert r.status_code == 401


def test_token_invalido_recusa(app):
    r = TestClient(app).post(
        "/api/vivo/amostras", json=lote(1), headers={"Authorization": "Bearer nao-existe"}
    )
    assert r.status_code == 401


def test_lote_aceito_e_reenvio_e_idempotente(app):
    cliente = dono_logado(app)
    carro = criar_carro(cliente, f"m2-{uuid4().hex[:6]}", "17")
    cab = {"Authorization": f"Bearer {carro['token_do_gateway']}"}

    primeiro = TestClient(app).post("/api/vivo/amostras", json=lote(1), headers=cab)
    assert primeiro.status_code == 202
    assert primeiro.json()["novo"] is True

    # mesmo lote de novo: o gateway repete quando a resposta se perde na rede
    repetido = TestClient(app).post("/api/vivo/amostras", json=lote(1), headers=cab)
    assert repetido.status_code == 202
    assert repetido.json()["novo"] is False
    assert "repetido" in repetido.json()["motivo"]


def test_sequencia_fora_de_ordem_e_contada_e_nao_descartada(app):
    cliente = dono_logado(app)
    carro = criar_carro(cliente, f"golf-{uuid4().hex[:6]}", "42")
    cab = {"Authorization": f"Bearer {carro['token_do_gateway']}"}
    c = TestClient(app)
    c.post("/api/vivo/amostras", json=lote(10, t0=2.0), headers=cab)
    # o pacote 9 chega depois do 10: rede ruim atrasa, mas a amostra e boa
    resposta = c.post("/api/vivo/amostras", json=lote(9, t0=1.0), headers=cab)
    assert resposta.status_code == 202
    assert resposta.json()["fora_de_ordem"] == 1
    # e as amostras dos dois lotes continuam no buffer
    assert resposta.json()["amostras_no_buffer"] == 10


def test_painel_declara_idade_do_dado(app):
    cliente = dono_logado(app)
    carro = criar_carro(cliente, f"civic-{uuid4().hex[:6]}", "08")
    cab = {"Authorization": f"Bearer {carro['token_do_gateway']}"}
    TestClient(app).post("/api/vivo/amostras", json=lote(1), headers=cab)

    painel = cliente.get("/api/vivo/painel")
    assert painel.status_code == 200
    item = next(v for v in painel.json() if v["veiculo_id"] == carro["veiculo_id"])
    assert item["ao_vivo"] is True
    assert item["idade_s"] is not None
    assert "speed" in item["canais"]
    # numero com zero a esquerda sobrevive: #08 nao pode virar 8
    assert item["numero"] == "08"


def test_carro_sem_pacote_aparece_no_painel_sem_fingir_que_esta_parado(app):
    cliente = dono_logado(app)
    carro = criar_carro(cliente, f"porsche-{uuid4().hex[:6]}", "91")
    item = next(
        v for v in cliente.get("/api/vivo/painel").json() if v["veiculo_id"] == carro["veiculo_id"]
    )
    assert item["ao_vivo"] is False
    assert item["amostras"] == 0
    assert item["ultimo_pacote_em"] is None


def test_dois_carros_do_mesmo_dono_nao_misturam_dado(app):
    cliente = dono_logado(app)
    a = criar_carro(cliente, f"a-{uuid4().hex[:6]}", "1")
    b = criar_carro(cliente, f"b-{uuid4().hex[:6]}", "2")
    c = TestClient(app)
    c.post("/api/vivo/amostras", json=lote(1, n=5), headers={"Authorization": f"Bearer {a['token_do_gateway']}"})
    c.post("/api/vivo/amostras", json=lote(1, n=3), headers={"Authorization": f"Bearer {b['token_do_gateway']}"})

    painel = {v["veiculo_id"]: v for v in cliente.get("/api/vivo/painel").json()}
    assert painel[a["veiculo_id"]]["amostras"] == 5
    assert painel[b["veiculo_id"]]["amostras"] == 3


def test_lote_vazio_ou_sem_seq_e_recusado_com_motivo(app):
    cliente = dono_logado(app)
    carro = criar_carro(cliente, f"vazio-{uuid4().hex[:6]}")
    cab = {"Authorization": f"Bearer {carro['token_do_gateway']}"}
    c = TestClient(app)
    assert c.post("/api/vivo/amostras", json={"seq": 1, "amostras": []}, headers=cab).status_code == 422
    assert c.post("/api/vivo/amostras", json={"amostras": [{"t_s": 0.1}]}, headers=cab).status_code == 422
