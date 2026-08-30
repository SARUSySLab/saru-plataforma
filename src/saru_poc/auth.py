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


# --- usuario maquina ------------------------------------------------------
#
# Decisao do Lucas (29/08, visao de campeonato): o relay de live timing NAO e
# uma pessoa. Entra como usuario proprio com role 'maquina' e autenticacao
# diferenciada: token de API de longa duracao no header Authorization, nunca o
# cookie de sessao. O motivo e operacional, nao estetico: JWT de 12h expira no
# meio de um evento de dia inteiro, e credencial de maquina precisa ser
# revogavel uma a uma (tabela maquina_token) sem derrubar sessao de humano.
# So o sha256 do token fica no banco: o token em claro aparece uma vez.

import hashlib as _hashlib
import secrets as _secrets

from fastapi import Header

_PREFIXO_TOKEN_MAQUINA = "saru_mq_"


def _sha256(texto: str) -> str:
    return _hashlib.sha256(texto.encode()).hexdigest()


def criar_maquina(nome: str, criado_por: UUID) -> dict[str, Any]:
    """Cria o usuario maquina e emite o token. O token so existe nesta resposta.

    O e-mail e sintetico (dominio reservado .invalid, RFC 2606): usuario
    maquina nao recebe e-mail e nao loga por senha. O password_hash recebe o
    hash de um segredo aleatorio DESCARTADO, entao o caminho de login por
    senha fica matematicamente fechado sem precisar de caso especial no
    `autenticar`.
    """
    email = f"maquina-{_secrets.token_hex(4)}@saru.invalid"
    token = _PREFIXO_TOKEN_MAQUINA + _secrets.token_hex(24)
    with connect() as conn:
        linha = conn.execute(
            "insert into usuario (email, password_hash, name, role)"
            " values (%s,%s,%s,'maquina') returning id",
            (email, hash_senha(_secrets.token_hex(32)), nome),
        ).fetchone()
        maquina_id = linha[0]
        conn.execute(
            "insert into maquina_token (user_id, token_sha256, nome, criado_por)"
            " values (%s,%s,%s,%s)",
            (maquina_id, _sha256(token), nome, criado_por),
        )
        conn.commit()
    return {"id": str(maquina_id), "nome": nome, "email": email, "token": token}


def listar_maquinas() -> list[dict[str, Any]]:
    with connect() as conn:
        linhas = conn.execute(
            """select u.id, mt.nome, u.email, mt.criado_em, mt.revogado_em, mt.ultimo_uso_em
                 from maquina_token mt join usuario u on u.id = mt.user_id
                order by mt.criado_em desc"""
        ).fetchall()
    return [
        {
            "id": str(l[0]),
            "nome": l[1],
            "email": l[2],
            "criado_em": l[3].isoformat(),
            "revogado_em": l[4].isoformat() if l[4] else None,
            "ultimo_uso_em": l[5].isoformat() if l[5] else None,
        }
        for l in linhas
    ]


def revogar_maquina(maquina_id: UUID) -> bool:
    with connect() as conn:
        linha = conn.execute(
            "update maquina_token set revogado_em = now()"
            " where user_id = %s and revogado_em is null returning id",
            (maquina_id,),
        ).fetchone()
        conn.commit()
    return linha is not None


def maquina_atual(
    authorization: Annotated[str | None, Header()] = None,
) -> UUID:
    """A maquina da requisicao, ou 401. Dependencia das rotas de ingestao.

    Caminho separado do `usuario_atual` de proposito: cookie nao vale aqui e
    token de maquina nao vale nas rotas humanas. Credencial de maquina que
    abre tela de pessoa (ou o contrario) e cruzamento de contexto.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="token de máquina ausente")
    token = authorization.removeprefix("Bearer ").strip()
    if not token.startswith(_PREFIXO_TOKEN_MAQUINA):
        raise HTTPException(status_code=401, detail="token de máquina inválido")
    with connect() as conn:
        linha = conn.execute(
            """select mt.user_id from maquina_token mt
                 join usuario u on u.id = mt.user_id
                where mt.token_sha256 = %s and mt.revogado_em is null
                  and u.role = 'maquina'""",
            (_sha256(token),),
        ).fetchone()
        if not linha:
            raise HTTPException(status_code=401, detail="token de máquina inválido")
        conn.execute(
            "update maquina_token set ultimo_uso_em = now() where token_sha256 = %s",
            (_sha256(token),),
        )
        conn.commit()
    return UUID(str(linha[0]))


Maquina = Annotated[UUID, Depends(maquina_atual)]


def exigir_gestor(dono: UUID) -> None:
    """Owner/admin. Emitir credencial de maquina nao e acao de membro comum."""
    papel = buscar_usuario(dono)["papel"]
    if papel not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="apenas owner/admin gerencia máquinas")
