"""Etapa 4: resolucao de pista.

A cascata do plano e `alias_layout` > GPS > perguntar ao usuario. Este modulo
implementa os DOIS primeiros degraus: casar o venue que o arquivo DECLARA
contra os layouts do catalogo (alias), e, quando o nome nao resolve, casar a
POSICAO mediana da amostra GPS contra a coordenada de referencia dos layouts
(`layout.ref_lat`/`ref_lon`). O degrau GPS so ficou possivel em 29/08, quando
o leitor .xrk passou a decodificar o chunk NAV-SOL em canais `gps_lat`/
`gps_lon`; ate entao este modulo era so o alias ("o unico possivel sem
amostra", dizia este docstring).

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

import math
import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np

from .leitura import ler_colunas, par_gps

# Venues que o arquivo declara mas que nao sao pista. Sao rotulos de bancada ou
# lixo de campo nao preenchido, medidos no acervo em 29/08.
NAO_E_PISTA = {"engine test", "test", "unknown", "n/a", ""}

# Raio de aceitacao do degrau GPS, da MEDIANA da amostra ate a referencia do
# layout (a linha de chegada). A mediana de uma sessao cai dentro do circuito,
# entao a distancia real fica na casa do raio do proprio tracado (menos de
# 1 km ate em Interlagos, 4,3 km de volta); 5 km da folga pra pit e reta longa
# sem chegar perto da distancia entre AUTODROMOS diferentes, que e de dezenas
# de quilometros. Duas pistas do catalogo a menos de 2x esse raio uma da outra
# tornariam o degrau ambiguo, e ambiguo aqui e nao-resolvido, como no alias.
RAIO_GPS_M = 5_000.0


@dataclass
class Resolucao:
    gravacao_id: str
    venue: str | None
    layout_id: str | None
    motivo: str


@dataclass
class ResumoResolucao:
    resolvidas: int = 0
    # Quantas das resolvidas vieram do degrau GPS (as demais, do alias).
    por_gps: int = 0
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


def _distancia_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine sobre a esfera media (R=6371 km). Erro do modelo esferico e
    da ordem de 0,5%, irrelevante contra um raio de aceitacao de 5 km."""
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    a = (
        math.sin((rlat2 - rlat1) / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin((rlon2 - rlon1) / 2) ** 2
    )
    return 2 * 6_371_000.0 * math.asin(math.sqrt(a))


def _posicao_mediana(conn, gid) -> tuple[float, float] | None:
    """Mediana de lat/lon da amostra GPS da gravacao, so dos pontos com
    coordenada finita e plausivel (nan = registro sem fix, o leitor ja
    declara assim; |lat| > 90 nao existe). Mediana e nao media: um punhado de
    fixes ruins no comeco da sessao nao pode arrastar a posicao."""
    par = par_gps(conn, str(gid))
    if par is None:
        return None
    lat_c, lon_c = par
    dados = ler_colunas(lat_c.uri, [lat_c.nome_bruto, lon_c.nome_bruto])
    if lat_c.nome_bruto not in dados or lon_c.nome_bruto not in dados:
        return None
    lat = lat_c.valores(dados)
    lon = lon_c.valores(dados)
    validos = (
        np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) <= 90) & (np.abs(lon) <= 180)
        # (0,0) e o "sem fix" de receptor que zera ECEF parcialmente; um ponto
        # real de pista no golfo da Guine nao existe no catalogo.
        & ~((lat == 0) & (lon == 0))
    )
    if int(validos.sum()) < 10:
        return None
    return float(np.median(lat[validos])), float(np.median(lon[validos]))


def _degrau_gps(
    conn, gid, refs: list[tuple[str, float, float]]
) -> tuple[str | None, str]:
    """(layout_id, motivo) do degrau GPS. layout_id nulo = nao resolveu, e o
    motivo diz por que, no vocabulario do resumo."""
    if not refs:
        return None, "nenhum layout com coordenada de referencia"
    pos = _posicao_mediana(conn, gid)
    if pos is None:
        return None, "sem amostra GPS utilizavel"
    lat, lon = pos
    perto = [
        (lid, _distancia_m(lat, lon, rlat, rlon))
        for lid, rlat, rlon in refs
        if _distancia_m(lat, lon, rlat, rlon) <= RAIO_GPS_M
    ]
    if not perto:
        return None, "GPS longe de toda referencia do catalogo"
    if len(perto) > 1:
        return None, f"GPS ambiguo entre {len(perto)} layouts proximos"
    return perto[0][0], "gps"


def resolver(conn, *, gravar_alias: bool = True) -> ResumoResolucao:
    """Resolve `gravacao.layout_id`: venue declarado (alias) e, quando o nome
    nao resolve, posicao GPS mediana contra `layout.ref_lat`/`ref_lon`.
    Idempotente."""
    idx = _indice(conn)
    refs = [
        (lid, float(la), float(lo))
        for lid, la, lo in conn.execute(
            "select id, ref_lat, ref_lon from layout "
            "where ref_lat is not null and ref_lon is not null"
        )
    ]
    r = ResumoResolucao()

    linhas = conn.execute(
        "select id, metadata from gravacao where layout_id is null"
    ).fetchall()

    for gid, metadata in linhas:
        declarados = _venues_da_gravacao(metadata)

        # Degrau 1: alias. `motivo_alias` fica preenchido quando o nome nao
        # resolveu; o degrau GPS decide se a gravacao ainda conta como falha.
        layout_id: str | None = None
        motivo_alias: str | None = None
        sem_venue = not declarados
        if declarados:
            # Num bundle, arquivos irmaos podem declarar venues diferentes. So
            # resolve quando todos concordam: divergencia entre irmaos e sinal
            # de que o bundle esta errado, nao de que um deles esta certo.
            candidatos = {normalizar(v) for _, v in declarados}
            candidatos -= NAO_E_PISTA
            if not candidatos:
                motivo_alias = "venue declarado nao e pista"
            elif len(candidatos) > 1:
                motivo_alias = "arquivos do bundle declaram venues diferentes"
            else:
                chave = next(iter(candidatos))
                alcanca = idx.get(chave, set())
                if not alcanca:
                    motivo_alias = "nenhum layout no catalogo com esse nome"
                elif len(alcanca) > 1:
                    motivo_alias = (
                        f"ambiguo entre {len(alcanca)} layouts da mesma pista"
                    )
                else:
                    layout_id = next(iter(alcanca))

        if layout_id is not None:
            conn.execute(
                "update gravacao set layout_id = %s, layout_origem = 'alias', "
                "updated_at = now() where id = %s",
                (layout_id, gid),
            )
            r.resolvidas += 1
            if gravar_alias:
                # A forma exata que o arquivo escreveu vira alias, com a fonte
                # sendo o formato que a escreveu. E pra isso que a chave de
                # `alias_layout` e (alias, fonte): o mesmo apelido pode
                # significar coisas diferentes vindo de exportadores
                # diferentes.
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
            continue

        # Degrau 2: GPS. Vale tambem pra quem nem declarou venue: e
        # exatamente o caso do bundle de arquivo solto (.xrz sozinho).
        # NAO grava alias: o nome declarado (se houver) nao casou com o
        # catalogo, e ensinar esse nome ao catalogo por causa de uma posicao
        # seria contaminar o degrau 1 com inferencia do degrau 2.
        gps_layout, gps_motivo = _degrau_gps(conn, gid, refs)
        if gps_layout is not None:
            conn.execute(
                "update gravacao set layout_id = %s, layout_origem = 'gps', "
                "updated_at = now() where id = %s",
                (gps_layout, gid),
            )
            r.resolvidas += 1
            r.por_gps += 1
            continue

        if sem_venue and gps_motivo in (
            "sem amostra GPS utilizavel",
            "nenhum layout com coordenada de referencia",
        ):
            # Sem nome E sem posicao: a contagem antiga de "sem venue".
            r.sem_venue += 1
            continue
        r.nao_resolvidas += 1
        _conta(r, motivo_alias or f"sem venue declarado e {gps_motivo}")
        if motivo_alias and gps_motivo != "gps":
            # O degrau GPS tambem tentou e falhou: registra a razao, senao o
            # operador ve so a falha do alias e conclui que o GPS nem rodou.
            _conta(r, f"(gps tambem nao: {gps_motivo})")
    return r


def _conta(r: ResumoResolucao, motivo: str) -> None:
    r.por_motivo[motivo] = r.por_motivo.get(motivo, 0) + 1
