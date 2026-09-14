"""Carga do catalogo de pista a partir do tracks.yaml do saru-app.

As seis tabelas de pista nasceram vazias, e sao elas que travam as etapas 4
(resolucao de pista), 5 (corte de volta) e 6 (decomposicao). O `tracks.yaml`
do saru-app tem 24 layouts, 72 setores e 148 curvas ja medidos, entao a carga
e transcricao, nao modelagem.

Fonte: `services/telemetry-api/config/tracks.yaml`, snapshot `aa94872`.
Validado em 29/08 contra as invariantes do schema: setores monotonicos, ultimo
setor igual ao comprimento do layout, `s_start < s_apex < s_end` em toda curva,
nenhuma curva alem do comprimento, nenhuma sobreposicao entre curvas vizinhas.
Zero violacao nos 24 layouts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .config import CONFIG, REPO_ROOT

# `pista.timezone` e NOT NULL e o tracks.yaml nao traz o campo. Estes sao os
# fusos dos paises onde cada autodromo fica, escritos um a um em vez de
# inferidos de coordenada (so 4 dos 24 tem ref_lat/ref_lon). Onde o circuito e
# conhecido o fuso e fato publico estavel; onde nao for, o carregador RECUSA em
# vez de chutar, porque `evento.local_date` depende disso pra agrupar o dia.
TIMEZONE_POR_LAYOUT: dict[str, str] = {
    "senna_kart": "America/Sao_Paulo",
    "granja_viana": "America/Sao_Paulo",
    "interlagos_gp": "America/Sao_Paulo",
    "cascavel": "America/Sao_Paulo",
    "goiania": "America/Sao_Paulo",
    "curitiba": "America/Sao_Paulo",
    "velocita": "America/Sao_Paulo",
    "taruma": "America/Sao_Paulo",
    "brasilia_gp": "America/Sao_Paulo",
    "monza_gp": "Europe/Rome",
    "monza_no_chicane": "Europe/Rome",
    "imola": "Europe/Rome",
    "lago_maggiore": "Europe/Rome",
    "spa_gp": "Europe/Brussels",
    "zolder": "Europe/Brussels",
    "barcelona": "Europe/Madrid",
    "nurburgring": "Europe/Berlin",
    "nurburgring_24h": "Europe/Berlin",
    "nordschleife_tourist": "Europe/Berlin",
    "lemans": "Europe/Paris",
    "red_bull_ring": "Europe/Vienna",
    "zandvoort": "Europe/Amsterdam",
    "suzuka": "Asia/Tokyo",
    "road_atlanta": "America/New_York",
}

# O sufixo depois do travessao no `track_name` as vezes e variante de layout
# ("GP", "No Chicane") e as vezes e a cidade ("Mogi Guacu/SP"). So o segundo
# caso vira `pista.cidade`.
_CIDADE_UF = re.compile(r"^(.+)/([A-Z]{2})$")
_SEPARADOR = re.compile(r"\s*[—–-]\s")


# Apelidos curados a mao, com fonte `curado` pra ficarem distinguiveis dos que
# vieram do tracks.yaml e dos que a etapa 4 aprende do dado.
#
# Existem porque o catalogo registra o nome FORMAL do autodromo e todo arquivo
# de telemetria escreve o nome POPULAR. Medido em 29/08: `interlagos_gp` e
# "Autodromo Jose Carlos Pace", e os arquivos escrevem "Interlagos",
# "Autodromo de Interlagos" e "Interlagos GP Circuit". Nenhuma dessas formas
# tem sobreposicao normalizada com o nome do catalogo, entao 8 gravacoes de
# Interlagos ficavam sem layout nenhum.
#
# So entram identidades sem ambiguidade: o catalogo tem UM layout de Interlagos
# e UM de kart Ayrton Senna. `monza` e `nurburgring` NAO entram, porque cada um
# alcanca dois layouts (GP e no-chicane; GP e 24h) e escolher e decisao de
# conteudo, nao de nomenclatura.
ALIASES_CURADOS: dict[str, str] = {
    "Interlagos": "interlagos_gp",
    "Autodromo de Interlagos": "interlagos_gp",
    "Autódromo de Interlagos": "interlagos_gp",
    "Interlagos GP Circuit": "interlagos_gp",
    "A.Senna Kart": "senna_kart",
    "Ayrton Senna Kart": "senna_kart",
}


@dataclass
class ResumoPistas:
    pistas: int = 0
    layouts: int = 0
    setores: int = 0
    curvas: int = 0
    aliases: int = 0
    sem_timezone: list[str] = field(default_factory=list)


def caminho_aliases_curados() -> Path:
    """De-para de venue versionado em `seeds/`.

    O `tracks.yaml` traz so o alias canonico de cada layout. Os outros nascem de
    duas formas que nao sobrevivem a um banco novo: curados a mao, e APRENDIDOS
    pela etapa 4 durante a ingestao (`gravar_alias=True`), quando um exportador
    escreve o nome da pista de um jeito que ainda nao estava no catalogo.

    Sem exportar isso, um ambiente novo perde a memoria de "Zolder" e
    "Curitiba", e arquivo que resolvia aqui sai como pista nao resolvida la. Foi
    o que aconteceu no primeiro lote migrado pra producao em 29/08.
    """
    return REPO_ROOT / "seeds" / "alias_layout.csv"


def semear_aliases_curados(conn) -> int:
    """Carrega `seeds/alias_layout.csv`. Idempotente.

    Alias ja existente nao e sobrescrito: a chave e (alias, fonte), e o que o
    ambiente aprendeu sozinho vale tanto quanto o que veio do arquivo.
    """
    import csv

    origem = caminho_aliases_curados()
    if not origem.exists():
        return 0
    with origem.open(encoding="utf-8") as fh:
        linhas = list(csv.DictReader(fh))
    n = 0
    for linha in linhas:
        # layout que nao existe neste catalogo e ignorado em silencio: o CSV
        # pode ter vindo de um ambiente com mais pistas, e falhar o seed inteiro
        # por causa de uma linha orfa deixaria o resto de fora
        existe = conn.execute(
            "select 1 from layout where id = %s", (linha["layout_id"],)
        ).fetchone()
        if not existe:
            continue
        n += conn.execute(
            "insert into alias_layout (alias, layout_id, fonte) values (%s,%s,%s)"
            " on conflict do nothing",
            (linha["alias"], linha["layout_id"], linha["fonte"]),
        ).rowcount
    return n


def caminho_tracks() -> Path:
    """A copia versionada em `seeds/` vence o snapshot do saru-app.

    O snapshot mora no disco do Lucas (`SARU_APP_REF`), e producao nao pode
    depender de um caminho que so existe numa maquina: sem isso o container
    sobe com catalogo vazio e a tela nao tem pista nenhuma pra escolher. O
    `seeds/` e a fonte de producao; o snapshot fica como fallback pra quem
    quiser reimportar do saru-app.
    """
    versionado = REPO_ROOT / "seeds" / "tracks.yaml"
    if versionado.exists():
        return versionado
    return CONFIG.app_ref / "services/telemetry-api/config/tracks.yaml"


def _nome_da_pista(track_name: str) -> tuple[str, str | None]:
    """Separa o nome da pista da cidade, quando o sufixo for cidade/UF."""
    partes = _SEPARADOR.split(track_name, maxsplit=1)
    if len(partes) == 1:
        return track_name.strip(), None
    cabeca, cauda = partes[0].strip(), partes[1].strip()
    m = _CIDADE_UF.match(cauda)
    return cabeca, cauda if m else None


def _setor_da_curva(setores: list[tuple[str, float, float]], s_apex: float) -> str:
    """O setor dono da curva e o que contem o apex. Toda curva tem um dono."""
    for sid, ini, fim in setores:
        if ini <= s_apex < fim:
            return sid
    return setores[-1][0]


def semear_pistas(conn, caminho: Path | None = None) -> ResumoPistas:
    """Popula pista, layout, alias_layout, segmento, setor e curva.

    Idempotente. `fase` NAO e populada: o tracks.yaml da tres pontos por curva
    (inicio, apex, fim), o que define dois intervalos, e a fronteira das tres
    fases exige uma decisao que nao esta no dado. Ver o relatorio.
    """
    dados = yaml.safe_load((caminho or caminho_tracks()).read_text(encoding="utf-8"))
    layouts = dados["tracks"] if isinstance(dados, dict) else dados
    r = ResumoPistas()

    faltando = [
        v["track_id"] for v in layouts if v["track_id"] not in TIMEZONE_POR_LAYOUT
    ]
    if faltando:
        raise ValueError(
            "layout sem fuso conhecido, e `pista.timezone` e NOT NULL: "
            f"{faltando}. Acrescente em TIMEZONE_POR_LAYOUT com fonte, nao chute."
        )

    with conn.transaction():
        for v in layouts:
            tid, tnome = v["track_id"], v["track_name"]
            nome_pista, cidade = _nome_da_pista(tnome)
            pista_id = conn.execute(
                """insert into pista (nome, cidade, timezone) values (%s,%s,%s)
                   on conflict (nome) do update set
                     cidade = coalesce(excluded.cidade, pista.cidade)
                   returning id""",
                (nome_pista, cidade, TIMEZONE_POR_LAYOUT[tid]),
            ).fetchone()[0]
            r.pistas += 1

            conn.execute(
                """insert into layout
                     (id, pista_id, nome, comprimento_m, ref_lat, ref_lon)
                   values (%s,%s,%s,%s,%s,%s)
                   on conflict (id) do update set
                     comprimento_m = excluded.comprimento_m,
                     ref_lat = excluded.ref_lat, ref_lon = excluded.ref_lon""",
                (
                    tid,
                    pista_id,
                    tnome,
                    v["length_m"],
                    v.get("ref_lat"),
                    v.get("ref_lon"),
                ),
            )
            r.layouts += 1

            # O proprio track_id e um apelido: e ele que os arquivos e a UI do
            # saru-app usam. A chave e (alias, fonte), entao o mesmo apelido
            # pode significar coisas diferentes vindo de exportadores diferentes.
            conn.execute(
                """insert into alias_layout (alias, layout_id, fonte)
                   values (%s,%s,%s) on conflict (alias, fonte) do nothing""",
                (tid, tid, "tracks.yaml"),
            )
            r.aliases += 1

            setores: list[tuple[str, float, float]] = []
            anterior = 0.0
            for ordem, fim in enumerate(v["sector_distances"], start=1):
                seg = conn.execute(
                    """insert into segmento (layout_id, tipo, ordem, s_inicio_m, s_fim_m)
                       values (%s,'setor',%s,%s,%s)
                       on conflict (layout_id, tipo, ordem) do update set
                         s_inicio_m = excluded.s_inicio_m, s_fim_m = excluded.s_fim_m
                       returning id""",
                    (tid, ordem, anterior, float(fim)),
                ).fetchone()[0]
                conn.execute(
                    """insert into setor (segmento_id, layout_id, rotulo)
                       values (%s,%s,%s) on conflict (segmento_id) do nothing""",
                    (seg, tid, f"S{ordem}"),
                )
                setores.append((seg, anterior, float(fim)))
                anterior = float(fim)
                r.setores += 1

            for ordem, c in enumerate(v.get("corners") or [], start=1):
                seg = conn.execute(
                    """insert into segmento (layout_id, tipo, ordem, s_inicio_m, s_fim_m)
                       values (%s,'curva',%s,%s,%s)
                       on conflict (layout_id, tipo, ordem) do update set
                         s_inicio_m = excluded.s_inicio_m, s_fim_m = excluded.s_fim_m
                       returning id""",
                    (tid, ordem, c["s_start"], c["s_end"]),
                ).fetchone()[0]
                conn.execute(
                    """insert into curva
                         (segmento_id, layout_id, setor_id, corner_id, label, s_apex_m)
                       values (%s,%s,%s,%s,%s,%s)
                       on conflict (segmento_id) do update set
                         label = excluded.label, s_apex_m = excluded.s_apex_m""",
                    (
                        seg,
                        tid,
                        _setor_da_curva(setores, c["s_apex"]),
                        c["corner_id"],
                        c.get("label"),
                        c["s_apex"],
                    ),
                )
                r.curvas += 1

            # O upsert por (layout_id, tipo, ordem) atualiza quem existe e cria
            # quem falta, mas nunca APAGA quem sobrou: quando uma rodada reduz a
            # contagem (Curitiba foi de 7 curvas pra 6 na re-derivacao de
            # 29/08), a ordem excedente ficava no banco com a geometria antiga,
            # orfa do YAML, e continuava rendendo tempo por trecho de uma curva
            # que nao existe mais. A ordem de delecao respeita as FKs: filhos
            # (tempo_trecho, fase, curva/setor) antes do segmento.
            n_setores = len(v["sector_distances"])
            n_curvas = len(v.get("corners") or [])
            for tipo, limite in (("setor", n_setores), ("curva", n_curvas)):
                orfaos = [
                    r_[0]
                    for r_ in conn.execute(
                        "select id from segmento where layout_id = %s and tipo = %s and ordem > %s",
                        (tid, tipo, limite),
                    ).fetchall()
                ]
                for seg_orfao in orfaos:
                    conn.execute(
                        "delete from tempo_trecho where segmento_id = %s", (seg_orfao,)
                    )
                    conn.execute("delete from fase where curva_id = %s", (seg_orfao,))
                    conn.execute("delete from curva where segmento_id = %s", (seg_orfao,))
                    conn.execute("delete from setor where segmento_id = %s", (seg_orfao,))
                    conn.execute("delete from segmento where id = %s", (seg_orfao,))

        ids = {v["track_id"] for v in layouts}
        for alias, layout_id in ALIASES_CURADOS.items():
            if layout_id not in ids:
                continue
            criado = conn.execute(
                """insert into alias_layout (alias, layout_id, fonte)
                   values (%s,%s,'curado') on conflict (alias, fonte) do nothing
                   returning alias""",
                (alias, layout_id),
            ).fetchone()
            if criado:
                r.aliases += 1
    return r
