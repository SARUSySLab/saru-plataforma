"""Camada de autenticacao: cookie httpOnly com JWT.

Os testes rodam contra o Postgres real da PoC, no mesmo padrao de
`tests/test_api.py`. Cada teste usa e-mail unico (uuid4) para poder rodar duas
vezes seguidas sem colidir com `uq_usuario_email`.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

os.environ.setdefault("SARU_CICLO_SARUE", "0")

from fastapi.testclient import TestClient  # noqa: E402

SENHA_VALIDA = "senha-de-teste-123"


@pytest.fixture
def cliente():
    """Um TestClient novo por teste, pra cada teste comecar sem cookie."""
    from saru_poc.api import app

    try:
        from saru_poc.db import ping

        ping()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")
    return TestClient(app)


def email_unico() -> str:
    return f"auth-{uuid4()}@teste.saru"


def registrar(cliente, email: str | None = None, senha: str = SENHA_VALIDA):
    return cliente.post(
        "/api/auth/registro",
        json={"email": email or email_unico(), "senha": senha, "nome": "Piloto Teste"},
    )


def test_registro_cria_usuario_e_ja_devolve_cookie_de_sessao(cliente) -> None:
    """Cadastro nao deveria exigir login separado: o cookie ja tem que vir na
    resposta do registro."""
    resposta = registrar(cliente)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email"]
    assert "saru_sessao" in resposta.cookies

    # a sessao do registro ja e valida numa rota protegida, sem login separado
    eu = cliente.get("/api/auth/eu")
    assert eu.status_code == 200
    assert eu.json()["id"] == corpo["id"]


def test_rota_protegida_sem_cookie_devolve_401(cliente) -> None:
    """`Dono` tem que barrar quem nao autenticou, antes de qualquer WHERE de
    dono entrar em jogo."""
    resposta = cliente.get("/api/auth/eu")
    assert resposta.status_code == 401


def test_login_com_senha_certa_funciona(cliente) -> None:
    email = email_unico()
    registrar(cliente, email=email)
    cliente.post("/api/auth/logout")

    resposta = cliente.post("/api/auth/login", json={"email": email, "senha": SENHA_VALIDA})
    assert resposta.status_code == 200
    assert resposta.json()["email"] == email
    assert "saru_sessao" in resposta.cookies


def test_senha_errada_e_email_inexistente_dao_o_mesmo_401(cliente) -> None:
    """Regressao proposital: mensagens diferentes pra senha errada e pra
    e-mail inexistente transformam o login num enumerador de contas. O status
    E o texto do erro tem que ser identicos nos dois casos.
    """
    email = email_unico()
    registrar(cliente, email=email)
    cliente.post("/api/auth/logout")

    senha_errada = cliente.post(
        "/api/auth/login", json={"email": email, "senha": "senha-totalmente-errada"}
    )
    email_inexistente = cliente.post(
        "/api/auth/login",
        json={"email": email_unico(), "senha": SENHA_VALIDA},
    )

    assert senha_errada.status_code == 401
    assert email_inexistente.status_code == 401
    assert senha_errada.json()["detail"] == email_inexistente.json()["detail"]


def test_senha_curta_devolve_422(cliente) -> None:
    """Menos de 10 caracteres e a unica exigencia de senha desta PoC (achado
    S3 do saru-app foi cadastro aberto com senha de 8 sem outra regra)."""
    resposta = registrar(cliente, senha="curta123")
    assert resposta.status_code == 422


def test_email_duplicado_devolve_409(cliente) -> None:
    email = email_unico()
    primeiro = registrar(cliente, email=email)
    assert primeiro.status_code == 201

    segundo = registrar(cliente, email=email)
    assert segundo.status_code == 409


def test_logout_limpa_cookie_e_rota_protegida_volta_a_dar_401(cliente) -> None:
    registrar(cliente)
    assert cliente.get("/api/auth/eu").status_code == 200

    saida = cliente.post("/api/auth/logout")
    assert saida.status_code == 204

    depois = cliente.get("/api/auth/eu")
    assert depois.status_code == 401


def test_token_invalido_devolve_401(cliente) -> None:
    """Cookie com lixo no lugar do JWT nao pode nem chegar perto de decodificar
    um `sub`."""
    cliente.cookies.set("saru_sessao", "isto-nao-e-um-jwt")
    resposta = cliente.get("/api/auth/eu")
    assert resposta.status_code == 401


def test_token_adulterado_devolve_401(cliente) -> None:
    """Pega um token valido e mexe num caractere do meio: a assinatura tem que
    parar de bater e o jwt tem que rejeitar, nao aceitar o payload adulterado."""
    resposta = registrar(cliente)
    token_valido = resposta.cookies["saru_sessao"]
    partes = token_valido.split(".")
    assert len(partes) == 3, "token nao parece um JWT de 3 partes"
    meio = partes[1]
    caractere_trocado = "a" if meio[-1] != "a" else "b"
    partes[1] = meio[:-1] + caractere_trocado
    token_adulterado = ".".join(partes)

    cliente.cookies.set("saru_sessao", token_adulterado)
    outra_resposta = cliente.get("/api/auth/eu")
    assert outra_resposta.status_code == 401
