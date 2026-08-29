"""Etapa 4: resolucao de pista.

A cascata do plano e `alias_layout` > GPS > perguntar ao usuario. Este modulo
implementa o primeiro degrau, que e o unico possivel sem amostra: casar o venue
que o arquivo DECLARA contra os layouts do catalogo.

Regra dura, e a razao de este modulo existir: **sem venue resolvido nao existe
setorizacao, e default silencioso e proibido.** Foi exatamente esse o bug B2 do
saru-app: `_resolve_track_id` devolvia o `track_id` que o cliente mandou quando
o arquivo nao declarava venue, sem registrar mismatch nenhum, e um `.xrk` de
kart de 1,1 km foi analisado contra os setores de Interlagos de 4.309 m. Aqui,
nao resolver e resultado, com motivo gravado.

Ambiguidade tambem e nao resolvido. `monza` casa com `monza_gp` e com
`monza_no_chicane`, e escolher um dos dois no palpite reproduz o mesmo defeito
com outra roupa.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Venues que o arquivo declara mas que nao sao pista. Sao rotulos de bancada ou
# lixo de campo nao preenchido, medidos no acervo em 29/08.
NAO_E_PISTA = {"engine test", "test", "unknown", "n/a", ""}


@dataclass
class Resolucao:
    gravacao_id: str
    venue: str | None
    layout_id: str | None
    motivo: str


@dataclass
class ResumoResolucao:
    resolvidas: int = 0
    nao_resolvidas: int = 0
    sem_venue: int = 0
    aliases_novos: int = 0
    por_motivo: dict[str, int] = field(default_factory=dict)


def normalizar(texto: str) -> str:
    """Forma de comparacao: sem acento, sem pontuacao, minusculo, espaco unico.

    `Autodromo de Interlagos`, `Interlagos GP Circuit` e `interlagos_gp` sao a
    mesma pista escrita por tres exportadores diferentes. Normalizar e o que
    permite casar sem inventar sinonimo.
    """
    s = unicodedata.normalize("NFKD", texto)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", " ", s.lower())
    return " ".join(s.split())


def _indice(conn) -> dict[str, set[str]]:
    """Forma normalizada -> conjunto de layout_id que ela alcanca."""
    idx: dict[str, set[str]] = {}

    def add(chave: str, layout_id: str) -> None:
        if chave:
            idx.setdefault(chave, set()).add(layout_id)

    for lid, nome, pista_nome in conn.execute(
        """select l.id, l.nome, p.nome from layout l join pista p on p.id = l.pista_id"""
    ):
        add(normalizar(lid), lid)
        add(normalizar(nome), lid)
        # O nome da pista alcanca todos os layouts dela, e e por isso que
        # `monza` fica ambiguo: e pista com dois layouts.
        add(normalizar(pista_nome), lid)
    for alias, lid in conn.execute("select alias, layout_id from alias_layout"):
        add(normalizar(alias), lid)
    return idx


def _venues_da_gravacao(metadata: dict) -> list[tuple[str, str]]:
    """(formato, venue) de cada arquivo do bundle que declarou algum."""
    return [
        (k.rsplit(".", 1)[0], v)
        for k, v in (metadata or {}).items()
        if k.endswith(".venue_declarado") and v
    ]


def resolver(conn, *, gravar_alias: bool = True) -> ResumoResolucao:
    """Resolve `gravacao.layout_id` pelo venue declarado. Idempotente."""
    idx = _indice(conn)
    r = ResumoResolucao()

    linhas = conn.execute(
        "select id, metadata from gravacao where layout_id is null"
    ).fetchall()

    for gid, metadata in linhas:
        declarados = _venues_da_gravacao(metadata)
        if not declarados:
            r.sem_venue += 1
            continue

        # Num bundle, arquivos irmaos podem declarar venues diferentes. So
        # resolve quando todos concordam: divergencia entre irmaos e sinal de
        # que o bundle esta errado, nao de que um deles esta certo.
        candidatos = {normalizar(v) for _, v in declarados}
        candidatos -= NAO_E_PISTA
        if not candidatos:
            r.nao_resolvidas += 1
            _conta(r, "venue declarado nao e pista")
            continue
        if len(candidatos) > 1:
            r.nao_resolvidas += 1
            _conta(r, "arquivos do bundle declaram venues diferentes")
            continue

        chave = next(iter(candidatos))
        alcanca = idx.get(chave, set())
        if not alcanca:
            r.nao_resolvidas += 1
            _conta(r, "nenhum layout no catalogo com esse nome")
            continue
        if len(alcanca) > 1:
            r.nao_resolvidas += 1
            _conta(r, f"ambiguo entre {len(alcanca)} layouts da mesma pista")
            continue

        layout_id = next(iter(alcanca))
        conn.execute(
            "update gravacao set layout_id = %s, updated_at = now() where id = %s",
            (layout_id, gid),
        )
        r.resolvidas += 1

        if gravar_alias:
            # A forma exata que o arquivo escreveu vira alias, com a fonte
            # sendo o formato que a escreveu. E pra isso que a chave de
            # `alias_layout` e (alias, fonte): o mesmo apelido pode significar
            # coisas diferentes vindo de exportadores diferentes.
            for fonte, venue in declarados:
                if normalizar(venue) in NAO_E_PISTA:
                    continue
                novo = conn.execute(
                    """insert into alias_layout (alias, layout_id, fonte)
                       values (%s,%s,%s) on conflict (alias, fonte) do nothing
                       returning alias""",
                    (venue, layout_id, fonte),
                ).fetchone()
                if novo:
                    r.aliases_novos += 1
    return r


def _conta(r: ResumoResolucao, motivo: str) -> None:
    r.por_motivo[motivo] = r.por_motivo.get(motivo, 0) + 1
