"""Cadastro, login, logout e quem sou eu.

As unicas rotas publicas do sistema. Todo o resto exige `Dono`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ..auth import (
    Dono,
    autenticar,
    buscar_usuario,
    criar_token,
    criar_usuario,
    gravar_cookie,
    limpar_cookie,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

SENHA_MINIMA = 10


def _validar(email: str, senha: str) -> None:
    if "@" not in email or len(email) < 5:
        raise HTTPException(status_code=422, detail="e-mail inválido")
    # 10, nao 8: o achado S3 do saru-app foi cadastro aberto com senha de 8 sem
    # outra exigencia, num ambiente exposto. Comprimento e a unica regra que
    # aumenta trabalho do atacante sem empurrar o usuario pra Senha123!.
    if len(senha) < SENHA_MINIMA:
        raise HTTPException(
            status_code=422, detail=f"senha precisa de pelo menos {SENHA_MINIMA} caracteres"
        )


@router.post("/registro", status_code=201)
def registro(corpo: dict, resposta: Response) -> dict:
    email = str(corpo.get("email") or "")
    senha = str(corpo.get("senha") or "")
    _validar(email, senha)
    usuario = criar_usuario(email, senha, corpo.get("nome"))
    # ja entra logado: obrigar login logo apos o cadastro nao protege nada e
    # so adiciona um passo
    gravar_cookie(resposta, criar_token(usuario["id"]))
    return usuario


@router.post("/login")
def login(corpo: dict, resposta: Response) -> dict:
    usuario = autenticar(str(corpo.get("email") or ""), str(corpo.get("senha") or ""))
    gravar_cookie(resposta, criar_token(usuario["id"]))
    return usuario


@router.post("/logout", status_code=204)
def logout(resposta: Response) -> None:
    """Apaga o cookie. Nao ha lista de revogacao: o token e curto (12h) e a
    troca do `SARU_JWT_SECRET` derruba todas as sessoes de uma vez."""
    limpar_cookie(resposta)


@router.get("/eu")
def eu(dono: Dono) -> dict:
    """Quem esta logado. E como o front decide entre mostrar o app e mandar
    pro login, sem guardar usuario em `localStorage`."""
    return buscar_usuario(dono)
