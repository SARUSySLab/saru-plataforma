"""Autenticacao. Cookie httpOnly com JWT, argon2 pra senha.

**Decisao do Lucas, 29/08: cookie httpOnly, nao `Authorization: Bearer`.** O
plano de integracao dizia Bearer; a escolha mudou porque a API passa a servir o
front (mesma origem, ver `api.py`), e nessa topologia o cookie sai de graca:
o browser manda sozinho, nao ha CORS pra liberar, e o token nunca fica legivel
pra JavaScript, o que tira o `localStorage` da superficie de XSS.

O preco do cookie e CSRF, e ele e pago em tres camadas:

1. `SameSite=Lax`, que ja barra POST cross-site (o caso perigoso).
2. Toda mutacao exige `Content-Type: application/json` ou multipart, que um
   `<form>` cross-site nao consegue emitir sem preflight.
3. Nenhuma mutacao acontece por GET.

Voltar pro Bearer, se um dia o front sair pra outro dominio, mexe so em
`_token_da_requisicao` e em `login`.

**A regra que este modulo existe pra impor:** guard de autenticacao NAO e filtro
de dono. O `saru-app` tinha `@UseGuards(JwtAuthGuard)` em todo endpoint de GT7 e
nenhum filtro por usuario, e virou vazamento de escrita entre contas (achado S1,
12/08). Por isso `usuario_atual` devolve o id, e todo SELECT/UPDATE que toca dado
de usuario tem que carregar esse id no WHERE. O guard diz QUEM e; o WHERE diz o
QUE e dele.
"""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Cookie, Depends, HTTPException, Response

from .config import CONFIG
from .db import connect

COOKIE = "saru_sessao"
_ALGORITMO = "HS256"
_hasher = PasswordHasher()


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def conferir_senha(hash_gravado: str, senha: str) -> bool:
    try:
        _hasher.verify(hash_gravado, senha)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        # hash corrompido ou de outro algoritmo: e falha de autenticacao, nao
        # 500. Deixar estourar entregaria 500 pra senha errada e viraria um
        # oraculo sobre quais contas tem hash legado.
        return False


def criar_token(user_id: str) -> str:
    agora = dt.datetime.now(dt.UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": agora,
            "exp": agora + dt.timedelta(hours=CONFIG.jwt_horas),
        },
        CONFIG.jwt_secret,
        algorithm=_ALGORITMO,
    )


def gravar_cookie(resposta: Response, token: str) -> None:
    resposta.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=CONFIG.cookie_seguro,
        max_age=CONFIG.jwt_horas * 3600,
        path="/",
    )


def limpar_cookie(resposta: Response) -> None:
    resposta.delete_cookie(COOKIE, path="/")


def _token_da_requisicao(saru_sessao: Annotated[str | None, Cookie()] = None) -> str | None:
    return saru_sessao


def usuario_atual(
    token: Annotated[str | None, Depends(_token_da_requisicao)],
) -> UUID:
    """O dono da requisicao, ou 401. Use como dependencia em TODA rota privada."""
    if not token:
        raise HTTPException(status_code=401, detail="não autenticado")
    try:
        dados = jwt.decode(token, CONFIG.jwt_secret, algorithms=[_ALGORITMO])
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(status_code=401, detail="sessão expirada") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="sessão inválida") from e
    return UUID(str(dados["sub"]))


Dono = Annotated[UUID, Depends(usuario_atual)]


# --- consultas de usuario ------------------------------------------------


def criar_usuario(email: str, senha: str, nome: str | None, papel: str = "owner") -> dict[str, Any]:
    email = email.strip().lower()
    with connect() as conn:
        ja = conn.execute("select 1 from usuario where email = %s", (email,)).fetchone()
        if ja:
            raise HTTPException(status_code=409, detail="e-mail já cadastrado")
        linha = conn.execute(
            "insert into usuario (email, password_hash, name, role)"
            " values (%s,%s,%s,%s) returning id, email, name, role",
            (email, hash_senha(senha), nome, papel),
        ).fetchone()
        conn.commit()
    return {"id": str(linha[0]), "email": linha[1], "nome": linha[2], "papel": linha[3]}


def autenticar(email: str, senha: str) -> dict[str, Any]:
    """Credencial certa devolve o usuario; qualquer falha devolve o MESMO 401.

    E-mail inexistente e senha errada dao a mesma resposta de proposito:
    mensagens diferentes transformam o login num enumerador de contas.
    """
    with connect() as conn:
        linha = conn.execute(
            "select id, email, name, role, password_hash from usuario where email = %s",
            (email.strip().lower(),),
        ).fetchone()
    if not linha or not conferir_senha(linha[4], senha):
        raise HTTPException(status_code=401, detail="e-mail ou senha inválidos")
    return {"id": str(linha[0]), "email": linha[1], "nome": linha[2], "papel": linha[3]}


def buscar_usuario(user_id: UUID) -> dict[str, Any]:
    with connect() as conn:
        linha = conn.execute(
            "select id, email, name, role from usuario where id = %s", (user_id,)
        ).fetchone()
    if not linha:
        # token valido de usuario apagado: sessao morta, nao 500
        raise HTTPException(status_code=401, detail="sessão inválida")
    return {"id": str(linha[0]), "email": linha[1], "nome": linha[2], "papel": linha[3]}
