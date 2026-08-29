"""Validador do contrato de saida contra `web/src/types/contract.ts`.

Existe por causa de um buraco declarado no proprio front. `web/src/dados/
fixture.ts` diz, com todas as letras:

    LIMITE CONHECIDO, nao varrido pra baixo do tapete: o cast abaixo NAO valida
    nada em runtime (...) Ate la, o contrato e acordo, nao garantia.

O cast e `as unknown as Relatorio`, e `tsc` passa limpo justamente porque o cast
desliga a checagem. Ou seja: o front compilar nao prova que o dado tem o shape
do contrato. Validacao de verdade no lado do TypeScript pediria zod, que e
dependencia nova e portanto decisao do Lucas. Do lado do Python nao pede nada:
o `contract.ts` e a fonte, e este modulo le a fonte.

O que este modulo faz: extrai as interfaces e os type alias do `contract.ts` e
valida um dict (o relatorio que a etapa 7 emite, ou o JSON do fixture) contra
elas. Campo faltando, campo a mais, tipo trocado e literal fora da uniao viram
erro com o caminho completo ate o campo.

O que ele NAO faz: nao entende generico arbitrario nem tipo condicional. Entende
o que o contrato usa hoje, e falha alto (ErroDeContrato) em construcao que nao
conhece, em vez de aprovar por omissao. Se o contrato ganhar uma forma nova,
este parser tem que crescer junto: aprovar o que nao se entende seria repetir a
doenca que ele existe pra evitar.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import REPO_ROOT

CONTRATO_TS = REPO_ROOT / "web" / "src" / "types" / "contract.ts"

PRIMITIVOS = {"number", "string", "boolean", "null", "true", "false", "unknown", "any"}


class ErroDeContrato(Exception):
    """Construcao de tipo que o parser nao conhece. Nunca e aprovacao."""


@dataclass
class Tipos:
    """O que foi extraido do contract.ts."""

    interfaces: dict[str, dict[str, str]] = field(default_factory=dict)
    alias: dict[str, str] = field(default_factory=dict)

    def conhece(self, nome: str) -> bool:
        return nome in self.interfaces or nome in self.alias


def _sem_comentarios(texto: str) -> str:
    texto = re.sub(r"/\*.*?\*/", "", texto, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", texto)


def _partir(texto: str, separador: str) -> list[str]:
    """Parte no separador de topo, respeitando {}, <>, [] e ()."""
    partes, atual, profundidade = [], [], 0
    for ch in texto:
        if ch in "{<([":
            profundidade += 1
        elif ch in "}>)]":
            profundidade -= 1
        if ch == separador and profundidade == 0:
            pedaco = "".join(atual).strip()
            if pedaco:
                # Uniao escrita em varias linhas comeca com o separador
                # (`= | "a" | "b"`), e a parte vazia da frente nao e um tipo.
                partes.append(pedaco)
            atual = []
            continue
        atual.append(ch)
    if "".join(atual).strip():
        partes.append("".join(atual).strip())
    return partes


def _campos_do_corpo(corpo: str) -> dict[str, str]:
    """Campos de um corpo de objeto `{ a: T; b: U }`."""
    campos: dict[str, str] = {}
    for pedaco in _partir(corpo, ";"):
        if not pedaco or ":" not in pedaco:
            continue
        nome, tipo = pedaco.split(":", 1)
        campos[nome.strip().strip("?")] = tipo.strip()
    return campos


def carregar(caminho: Path | None = None) -> Tipos:
    """Le o contract.ts e extrai interfaces e alias."""
    caminho = caminho or CONTRATO_TS
    texto = _sem_comentarios(caminho.read_text())
    tipos = Tipos()

    for nome, corpo in re.findall(
        r"export\s+interface\s+(\w+)\s*\{(.*?)\n\}", texto, flags=re.DOTALL
    ):
        tipos.interfaces[nome] = _campos_do_corpo(corpo)

    # O alias tem que ser lido ate o `;` de TOPO, nao ate o primeiro `;`.
    # `type Degradado = { disponivel: false; motivo: ...; texto: string }` tem
    # ponto e virgula dentro do objeto, e um regex ganancioso ate o primeiro
    # deles guardava "{ disponivel: false" como se fosse o tipo inteiro. O
    # efeito era pior que um erro: o ramo degradado nunca era validado de
    # verdade, e o fixture (que nao tem nenhum bloco degradado) passava limpo.
    for m in re.finditer(r"export\s+type\s+(\w+)(?:<[^>]*>)?\s*=\s*", texto):
        resto = texto[m.end() :]
        profundidade = 0
        for i, ch in enumerate(resto):
            if ch in "{<([":
                profundidade += 1
            elif ch in "}>)]":
                profundidade -= 1
            elif ch == ";" and profundidade == 0:
                tipos.alias[m.group(1)] = " ".join(resto[:i].split())
                break

    if "Relatorio" not in tipos.interfaces:
        raise ErroDeContrato(f"{caminho} nao declara a interface Relatorio")
    return tipos


# --- validacao -----------------------------------------------------------


def _erro(erros: list[str], caminho: str, mensagem: str) -> None:
    erros.append(f"{caminho}: {mensagem}")


def _validar(valor, tipo: str, caminho: str, tipos: Tipos, erros: list[str]) -> None:
    tipo = tipo.strip()
    while tipo.startswith("(") and tipo.endswith(")"):
        tipo = tipo[1:-1].strip()

    uniao = _partir(tipo, "|")
    if len(uniao) > 1:
        candidatos = []
        for alternativa in uniao:
            sub: list[str] = []
            _validar(valor, alternativa, caminho, tipos, sub)
            if not sub:
                return
            candidatos.append(f"{alternativa.strip()} ({len(sub)} erro(s))")
        _erro(
            erros,
            caminho,
            f"valor {valor!r} nao casa com nenhuma alternativa de {tipo}: "
            + ", ".join(candidatos),
        )
        return

    intersecao = _partir(tipo, "&")
    if len(intersecao) > 1:
        for parte in intersecao:
            _validar(valor, parte, caminho, tipos, erros)
        return

    # Talvez<T> = Disponivel<T> | Degradado
    generico = re.fullmatch(r"(\w+)\s*<\s*(.*)\s*>", tipo, flags=re.DOTALL)
    if generico:
        nome, argumento = generico.group(1), generico.group(2)
        if nome == "Talvez":
            if isinstance(valor, dict) and valor.get("disponivel") is False:
                _validar(valor, "Degradado", caminho, tipos, erros)
            else:
                _validar(valor, f"Disponivel<{argumento}>", caminho, tipos, erros)
            return
        if nome == "Disponivel":
            if not isinstance(valor, dict):
                _erro(erros, caminho, f"esperava objeto, veio {type(valor).__name__}")
                return
            if valor.get("disponivel") is not True:
                _erro(erros, caminho, "disponivel tem que ser true neste ramo")
            resto = {k: v for k, v in valor.items() if k != "disponivel"}
            _validar(resto, argumento, caminho, tipos, erros)
            return
        if nome == "Record":
            chave_valor = _partir(argumento, ",")
            if len(chave_valor) != 2:
                raise ErroDeContrato(
                    f"Record com {len(chave_valor)} argumentos: {tipo}"
                )
            if not isinstance(valor, dict):
                _erro(erros, caminho, f"esperava objeto, veio {type(valor).__name__}")
                return
            for chave, item in valor.items():
                _validar(item, chave_valor[1], f"{caminho}.{chave}", tipos, erros)
            return
        raise ErroDeContrato(f"generico desconhecido: {tipo}")

    if tipo.endswith("[]"):
        if not isinstance(valor, list):
            _erro(erros, caminho, f"esperava lista, veio {type(valor).__name__}")
            return
        for i, item in enumerate(valor):
            _validar(item, tipo[:-2], f"{caminho}[{i}]", tipos, erros)
        return

    if tipo.startswith("{"):
        campos = _campos_do_corpo(tipo.strip()[1:-1])
        _validar_objeto(valor, campos, caminho, tipos, erros)
        return

    if tipo.startswith(('"', "'")):
        literal = tipo.strip("\"'")
        if valor != literal:
            _erro(erros, caminho, f"esperava o literal {literal!r}, veio {valor!r}")
        return

    if tipo in PRIMITIVOS:
        esperado = {
            "number": (int, float),
            "string": (str,),
            "boolean": (bool,),
        }.get(tipo)
        if tipo == "null":
            if valor is not None:
                _erro(erros, caminho, f"esperava null, veio {valor!r}")
        elif tipo == "true":
            if valor is not True:
                _erro(erros, caminho, f"esperava true, veio {valor!r}")
        elif tipo == "false":
            if valor is not False:
                _erro(erros, caminho, f"esperava false, veio {valor!r}")
        elif esperado is not None:
            # bool e subclasse de int em Python, e number aceitando True seria
            # falso positivo silencioso.
            if isinstance(valor, bool) and tipo == "number":
                _erro(erros, caminho, "esperava number, veio boolean")
            elif not isinstance(valor, esperado):
                _erro(
                    erros,
                    caminho,
                    f"esperava {tipo}, veio {type(valor).__name__} ({valor!r})",
                )
        return

    if tipo in tipos.interfaces:
        _validar_objeto(valor, tipos.interfaces[tipo], caminho, tipos, erros)
        return
    if tipo in tipos.alias:
        _validar(valor, tipos.alias[tipo], caminho, tipos, erros)
        return

    raise ErroDeContrato(f"tipo desconhecido no contrato: {tipo!r} (em {caminho})")


def _validar_objeto(
    valor, campos: dict[str, str], caminho: str, tipos: Tipos, erros: list[str]
) -> None:
    if not isinstance(valor, dict):
        _erro(erros, caminho, f"esperava objeto, veio {type(valor).__name__}")
        return
    for nome, tipo in campos.items():
        if nome not in valor:
            _erro(
                erros, f"{caminho}.{nome}", f"campo obrigatorio ausente (tipo {tipo})"
            )
            continue
        _validar(valor[nome], tipo, f"{caminho}.{nome}", tipos, erros)
    sobrando = set(valor) - set(campos) - {"disponivel"}
    for nome in sorted(sobrando):
        # Campo a mais e erro, nao detalhe: o front nao le, entao alguem
        # calculou algo que ninguem consome, ou o nome foi trocado num lado so.
        _erro(erros, f"{caminho}.{nome}", "campo que o contrato nao declara")


def validar(
    dado: dict, raiz: str = "Relatorio", tipos: Tipos | None = None
) -> list[str]:
    """Valida um dict contra um tipo do contrato. Lista vazia e aprovacao."""
    tipos = tipos or carregar()
    erros: list[str] = []
    _validar(dado, raiz, raiz.lower(), tipos, erros)
    return erros


def validar_arquivo(
    caminho: Path, raiz: str = "Relatorio", tipos: Tipos | None = None
) -> list[str]:
    return validar(json.loads(Path(caminho).read_text()), raiz, tipos)
