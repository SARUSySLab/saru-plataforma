"""Live timing externo: parse e ingestao do XML "resultspage" (MyLaps/Orbits).

E a terceira fonte de dado do SARU (achado do Lucas, 29/08): a cronometragem
que o autodromo streama na rede local pra alimentar o painel do evento. Nao e
telemetria de bordo: e o contexto competitivo do grid inteiro (posicao, tempos,
gaps, classes), e alimenta a visao de campeonato.

Decisoes do Lucas (29/08, sessao da visao de campeonato):
  - ingestao por relay local autenticado como usuario maquina (a producao no
    Railway nao enxerga a LAN do autodromo);
  - persistencia snapshot + historico: o XML so carrega as ultimas 3 voltas
    de cada carro, entao o historico volta a volta e DERIVADO aqui, por diff
    entre snapshots, e acumulado em `lt_passagem`;
  - front recebe por SSE.

Fatos do formato, medidos no XML real do 12o MBR Time Attack 2026 (84 carros,
9 classes, Autodromo de Brasilia):
  - tempos usam PONTO decimal ("1:58.349", "7:18:44.553"), velocidades e
    comprimento de pista usam VIRGULA ("163,834", "5,386");
  - `fullname` embute o carro: "Piloto | Carro" (o firstname vem com o "|"
    grudado, entao o split e no fullname, nao na concatenacao);
  - `gap` e pro carro da frente, `difference` e pro lider, e ambos podem ser
    texto ("4 Voltas"), entao ficam como string;
  - `lasttimeofday` e hora do relogio da cronometragem ("18:16:56.108") e pode
    ser de HORAS atras: time attack roda em levas, carro parado nao passa no
    loop. Quem decide se o carro esta em pista e o consumidor, comparando com
    o `timeofday` do snapshot;
  - campos de setor (`section0..9`) existem no schema e vieram vazios no
    evento medido: parse os inclui so quando preenchidos.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass

# O relay e autenticado (usuario maquina), entao a superficie de XML hostil e
# pequena; ainda assim, nada de DTD aqui: o ElementTree do stdlib nao resolve
# entidade externa, e entidade interna indefinida vira erro de parse, que a
# rota devolve como 422.
import xml.etree.ElementTree as ET
from typing import Any

from psycopg.types.json import Jsonb


class XmlInvalido(ValueError):
    """O corpo nao e um resultspage utilizavel."""


# --- conversoes de campo ----------------------------------------------------


def _segundos(txt: str | None) -> float | None:
    """ "1:58.349" -> 118.349; "7:18:44.553" -> horas tambem; vazio -> None."""
    if not txt:
        return None
    txt = txt.strip()
    if not re.fullmatch(r"[0-9:.,]+", txt):
        return None
    partes = txt.replace(",", ".").split(":")
    try:
        total = 0.0
        for p in partes:
            total = total * 60 + float(p)
    except ValueError:
        return None
    return total


def _decimal(txt: str | None) -> float | None:
    """Numero com virgula decimal da cronometragem ("163,834")."""
    if not txt:
        return None
    try:
        return float(txt.strip().replace(",", "."))
    except ValueError:
        return None


def _inteiro(txt: str | None) -> int | None:
    if not txt:
        return None
    try:
        return int(txt.strip())
    except ValueError:
        return None


def _nome_e_carro(fullname: str) -> tuple[str, str | None]:
    """ "Pedro Piquet | Mclaren 765 LT 61MS" -> (piloto, carro)."""
    if "|" in fullname:
        nome, _, carro = fullname.partition("|")
        return nome.strip() or fullname.strip(), carro.strip() or None
    return fullname.strip(), None


# --- parse ------------------------------------------------------------------


def parse_resultspage(xml_bruto: str | bytes) -> dict[str, Any]:
    """Labels + resultados normalizados. Levanta `XmlInvalido` se nao for o formato."""
    try:
        raiz = ET.fromstring(xml_bruto)
    except ET.ParseError as e:
        raise XmlInvalido(f"XML não parseia: {e}") from e
    if raiz.tag != "resultspage":
        raise XmlInvalido(f"raiz é <{raiz.tag}>, esperado <resultspage>")

    labels = {
        el.get("type", ""): (el.text or "").strip() for el in raiz.findall("label")
    }

    resultados: list[dict[str, Any]] = []
    bloco = raiz.find("results")
    for r in bloco.findall("result") if bloco is not None else []:
        a = r.attrib
        nome, carro = _nome_e_carro(a.get("fullname") or "")
        setores = {
            f"s{i + 1}": _segundos(a.get(f"section{i}"))
            for i in range(10)
            if a.get(f"section{i}")
        }
        melhores_setores = {
            f"s{i + 1}": _segundos(a.get(f"bestsection{i}"))
            for i in range(10)
            if a.get(f"bestsection{i}")
        }
        resultados.append(
            {
                "posicao": _inteiro(a.get("position")),
                "posicao_classe": _inteiro(a.get("positioninclass")),
                "numero": (a.get("no") or "").strip(),
                "transponder": (a.get("transponder") or "").strip() or None,
                "nome": nome,
                "carro": carro,
                "classe": (a.get("class") or "").strip() or None,
                "voltas": _inteiro(a.get("laps")),
                "ultima_volta_s": _segundos(a.get("lasttime")),
                "penultima_volta_s": _segundos(a.get("secondlasttime")),
                "antepenultima_volta_s": _segundos(a.get("thirdlasttime")),
                "melhor_volta_s": _segundos(a.get("besttime")),
                "melhor_volta_n": _inteiro(a.get("bestinlap")),
                "melhor_vel_kmh": _decimal(a.get("bestspeed")),
                "segunda_melhor_s": _segundos(a.get("secondbesttime")),
                "media_s": _segundos(a.get("averagetime")),
                "total_s": _segundos(a.get("totaltime")),
                # gap (pro da frente) e diff (pro lider) podem ser "4 Voltas":
                # ficam como texto, quem formata e a tela
                "gap": (a.get("gap") or "").strip() or None,
                "diff": (a.get("difference") or "").strip() or None,
                "ultima_vel_kmh": _decimal(a.get("lastspeed")),
                "ultima_passagem_tod": (a.get("lasttimeofday") or "").strip() or None,
                "ultima_passagem_s": _segundos(a.get("lasttimeofday")),
                "pits": _inteiro(a.get("nopitstops")),
                "setores": setores,
                "melhores_setores": melhores_setores,
            }
        )

    evento = {
        "nome": labels.get("eventname") or "",
        "grupo": labels.get("groupname") or None,
        "run_nome": labels.get("runname") or "",
        "run_tipo": labels.get("runtype") or None,
        "pista_nome": labels.get("trackname") or None,
        # tracklength vem em km com virgula ("5,386")
        "track_length_m": (
            round(_decimal(labels.get("tracklength")) * 1000.0, 1)
            if _decimal(labels.get("tracklength"))
            else None
        ),
    }
    if not evento["nome"]:
        raise XmlInvalido("resultspage sem label eventname")

    return {
        "evento": evento,
        "labels": labels,
        "timeofday": labels.get("timeofday") or None,
        "timeofday_s": _segundos(labels.get("timeofday")),
        "racetime": labels.get("racetime") or None,
        "flag": labels.get("flag") or None,
        "resultados": resultados,
    }


# --- avisos da direcao de prova (track limits e penalidades) ----------------

# O feed de avisos e um `resultspage` como os outros, mas SEM os labels de
# evento: ele tem so `results` com data, hora e texto. Por isso ele nao passa
# pelo `parse_resultspage`, que exige `eventname` e levantaria XmlInvalido.
# Pedido do Vitor Saru em 29/08: "e bom ter, pq tem tracklimits; tem um .xml
# que tem isso". Amostra real em tests/fixtures/livetiming_announcements.xml,
# capturada do 12o MBR Time Attack.

# Numero de carro e STRING, nunca int: o grid real tem #08, #033, #001 e #2,
# e converter pra numero funde carros diferentes num so.
_RE_CARRO = re.compile(r"#(\d+)\s*(?:\((\d+)x\))?", re.IGNORECASE)


@dataclass(frozen=True)
class Aviso:
    """Um aviso da direcao de prova, com o texto CRU sempre preservado.

    A extracao de carro e reincidencia e camada por cima do texto, nunca no
    lugar dele: aviso que nao casa com padrao nenhum entra como texto puro em
    vez de ser descartado ou meio interpretado.
    """

    data: str
    hora: str
    texto: str
    tipo: str
    carros: tuple[tuple[str, int], ...]


def _classificar_aviso(texto: str, tem_carro: bool) -> str:
    """Tipo do aviso a partir do texto.

    Tres tipos vistos no feed real: track limit anunciado com prefixo, perda
    de volta por penalidade, e uma linha que e SO uma lista de carros, sem
    prefixo nenhum (09:16 na amostra). Essa ultima parece continuacao do
    tracklimit anterior pela posicao na sequencia, mas isso e INFERENCIA e nao
    da pra cravar: ela sai como "indefinido" e o texto cru fica la pra quem
    puder confirmar com a organizacao.
    """
    alto = texto.upper()
    if alto.startswith("TRACKLIMIT"):
        return "track_limit"
    if "PERDE" in alto:
        return "perda_de_volta"
    if tem_carro:
        return "indefinido"
    return "texto"


def parse_avisos(xml_bruto: str | bytes) -> list[Aviso]:
    """Avisos do feed `announcements`, na ordem em que vieram."""
    try:
        raiz = ET.fromstring(xml_bruto)
    except ET.ParseError as e:
        raise XmlInvalido(f"XML de avisos não parseia: {e}") from e
    if raiz.tag != "resultspage":
        raise XmlInvalido(f"raiz é <{raiz.tag}>, esperado <resultspage>")

    bloco = raiz.find("results")
    avisos: list[Aviso] = []
    for r in bloco.findall("result") if bloco is not None else []:
        texto = (r.get("text") or "").strip()
        if not texto:
            continue
        # `(3x)` e reincidencia declarada pela organizacao: o carro apareceu
        # tres vezes naquele anuncio. Sem parenteses, conta uma.
        carros = tuple(
            (numero, int(vezes) if vezes else 1)
            for numero, vezes in _RE_CARRO.findall(texto)
        )
        avisos.append(
            Aviso(
                data=(r.get("date") or "").strip(),
                hora=(r.get("time") or "").strip(),
                texto=texto,
                tipo=_classificar_aviso(texto, bool(carros)),
                carros=carros,
            )
        )
    return avisos


def contar_track_limits(avisos: list[Aviso]) -> dict[str, int]:
    """Quantos track limits cada carro acumulou na sessao.

    So conta o que a organizacao anunciou COMO track limit. O aviso
    "indefinido" (lista de carros sem prefixo) fica de fora de proposito:
    somar ele seria transformar inferencia em numero, e esse numero apareceria
    ao lado do delta no painel como se fosse fato.
    """
    total: dict[str, int] = {}
    for aviso in avisos:
        if aviso.tipo != "track_limit":
            continue
        for numero, vezes in aviso.carros:
            total[numero] = total.get(numero, 0) + vezes
    return total


def ingerir_avisos(conn, evento_id, xml_bruto: str | bytes) -> dict[str, Any]:
    """Grava os avisos do feed no banco, idempotente por (data, hora, texto).

    O relay reenvia o feed inteiro a cada poll, entao a mesma linha chega
    dezenas de vezes: reler nao pode duplicar aviso nem inflar a contagem de
    track limit do carro. Quem garante isso e o unique da tabela, nao um
    controle em memoria que morre no restart.
    """
    avisos = parse_avisos(xml_bruto)
    novos = 0
    for aviso in avisos:
        linha = conn.execute(
            """insert into lt_aviso (evento_id, data_txt, hora_txt, texto, tipo, carros)
               values (%s, %s, %s, %s, %s, %s)
               on conflict (evento_id, data_txt, hora_txt, texto) do nothing
               returning id""",
            (
                evento_id,
                aviso.data,
                aviso.hora,
                aviso.texto,
                aviso.tipo,
                Jsonb([{"numero": n, "vezes": v} for n, v in aviso.carros]),
            ),
        ).fetchone()
        if linha is not None:
            novos += 1
    return {"lidos": len(avisos), "novos": novos}


def ler_avisos(conn, evento_id, limite: int = 30) -> dict[str, Any]:
    """Avisos recentes do evento e a contagem de track limit por carro.

    A contagem soma so o que a organizacao anunciou COMO track limit. Aviso do
    tipo indefinido (lista de carros sem prefixo) aparece na lista, para o
    engenheiro ler, mas fica fora do numero: somar inferencia daria um valor
    que o painel exibiria ao lado do delta como se fosse fato.
    """
    linhas = conn.execute(
        """select data_txt, hora_txt, texto, tipo, carros
             from lt_aviso where evento_id = %s
            order by hora_txt desc limit %s""",
        (evento_id, limite),
    ).fetchall()
    avisos = [
        {"data": d, "hora": h, "texto": t, "tipo": tipo, "carros": carros}
        for d, h, t, tipo, carros in linhas
    ]
    total: dict[str, int] = {}
    for a in avisos:
        if a["tipo"] != "track_limit":
            continue
        for c in a["carros"]:
            total[c["numero"]] = total.get(c["numero"], 0) + int(c["vezes"])
    return {"avisos": avisos, "track_limits_por_carro": total}


# --- resolucao de layout ----------------------------------------------------


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", sem_acento.lower()).strip()


_PALAVRAS_VAZIAS = {
    "autodromo",
    "circuito",
    "de",
    "do",
    "da",
    "internacional",
    "kartodromo",
}


def resolver_layout(
    conn, pista_nome: str | None, track_length_m: float | None
) -> str | None:
    """Layout do catalogo que corresponde ao trackname da cronometragem.

    Dois degraus, na ordem do resto do sistema (alias antes de heuristica):
      1. `alias_layout` com fonte 'livetiming' (de-para cravado por alguem);
      2. tokens do trackname contra pista.nome + layout.nome/id, desempatando
         pelo comprimento declarado no XML quando houver mais de um layout da
         mesma pista.

    Sem correspondencia devolve None: mapa sem pista declarada e melhor que
    mapa da pista errada (regra do B2).
    """
    if not pista_nome:
        return None

    linha = conn.execute(
        "select layout_id from alias_layout where fonte = 'livetiming' and alias = %s",
        (pista_nome,),
    ).fetchone()
    if linha:
        return linha[0]

    tokens = {
        t for t in _normalizar(pista_nome).split() if t and t not in _PALAVRAS_VAZIAS
    }
    if not tokens:
        return None

    candidatos = []
    for layout_id, layout_nome, comprimento, nome_pista in conn.execute(
        """select l.id, l.nome, l.comprimento_m, p.nome
             from layout l join pista p on p.id = l.pista_id"""
    ).fetchall():
        alvo = _normalizar(f"{nome_pista} {layout_nome} {layout_id.replace('_', ' ')}")
        if all(t in alvo for t in tokens):
            candidatos.append((layout_id, comprimento))

    if not candidatos:
        return None
    if track_length_m:
        candidatos.sort(key=lambda c: abs((c[1] or 0.0) - track_length_m))
        # comprimento a mais de 15% de distancia nao e o mesmo layout, e outra
        # variante da pista que nao esta no catalogo
        if abs((candidatos[0][1] or 0.0) - track_length_m) > track_length_m * 0.15:
            return None
    elif len(candidatos) > 1:
        return None
    return candidatos[0][0]


# --- ingestao ---------------------------------------------------------------


def ingerir(conn, xml_bruto: bytes, maquina_id) -> dict[str, Any]:
    """Um XML postado pelo relay vira evento + snapshot + passagens derivadas.

    Idempotente por sha256: o relay posta sem medo, snapshot identico e no-op.
    A transacao e de quem chama (a rota commita no fim).
    """
    dados = parse_resultspage(xml_bruto)
    ev = dados["evento"]
    sha = hashlib.sha256(xml_bruto).hexdigest()

    linha = conn.execute(
        """insert into lt_evento (maquina_id, nome, grupo, run_nome, run_tipo,
                                  pista_nome, track_length_m)
           values (%s, %s, %s, %s, %s, %s, %s)
           on conflict (nome, run_nome) do update set
                grupo = coalesce(excluded.grupo, lt_evento.grupo),
                run_tipo = coalesce(excluded.run_tipo, lt_evento.run_tipo),
                pista_nome = coalesce(excluded.pista_nome, lt_evento.pista_nome),
                track_length_m = coalesce(excluded.track_length_m, lt_evento.track_length_m)
           returning id, layout_id""",
        (
            maquina_id,
            ev["nome"],
            ev["grupo"],
            ev["run_nome"],
            ev["run_tipo"],
            ev["pista_nome"],
            ev["track_length_m"],
        ),
    ).fetchone()
    evento_id, layout_id = linha

    if layout_id is None:
        layout_id = resolver_layout(conn, ev["pista_nome"], ev["track_length_m"])
        if layout_id:
            conn.execute(
                "update lt_evento set layout_id = %s where id = %s and layout_id is null",
                (layout_id, evento_id),
            )

    snap = conn.execute(
        """insert into lt_snapshot (evento_id, timeofday, racetime, flag, labels,
                                    resultados, raw_sha256, raw_xml)
           values (%s, %s, %s, %s, %s, %s, %s, %s)
           on conflict (evento_id, raw_sha256) do nothing
           returning id""",
        (
            evento_id,
            dados["timeofday"],
            dados["racetime"],
            dados["flag"],
            Jsonb(dados["labels"]),
            Jsonb(dados["resultados"]),
            sha,
            xml_bruto.decode("utf-8", errors="replace"),
        ),
    ).fetchone()
    if snap is None:
        return {"evento_id": str(evento_id), "novo": False, "passagens_novas": 0}
    snapshot_id = snap[0]

    passagens = 0
    for r in dados["resultados"]:
        if not r["numero"]:
            continue
        comp = conn.execute(
            """insert into lt_competidor (evento_id, numero, transponder, nome, carro, classe)
               values (%s, %s, %s, %s, %s, %s)
               on conflict (evento_id, numero) do update set
                    transponder = coalesce(excluded.transponder, lt_competidor.transponder),
                    nome = excluded.nome,
                    carro = coalesce(excluded.carro, lt_competidor.carro),
                    classe = coalesce(excluded.classe, lt_competidor.classe)
               returning id""",
            (
                evento_id,
                r["numero"],
                r["transponder"],
                r["nome"],
                r["carro"],
                r["classe"],
            ),
        ).fetchone()
        competidor_id = comp[0]

        voltas = r["voltas"]
        if not voltas or voltas < 1:
            continue
        # o XML carrega as 3 ultimas voltas; tudo que ja passou disso so
        # existe se um snapshot anterior capturou. Buraco fica buraco.
        candidatas = [
            (
                voltas,
                r["ultima_volta_s"],
                r["ultima_vel_kmh"],
                r["ultima_passagem_tod"],
            ),
            (voltas - 1, r["penultima_volta_s"], None, None),
            (voltas - 2, r["antepenultima_volta_s"], None, None),
        ]
        for volta_n, tempo_s, vel, tod in candidatas:
            if volta_n < 1 or tempo_s is None:
                continue
            gravou = conn.execute(
                """insert into lt_passagem (competidor_id, volta, tempo_s,
                                            velocidade_kmh, timeofday, snapshot_id)
                   values (%s, %s, %s, %s, %s, %s)
                   on conflict (competidor_id, volta) do nothing
                   returning id""",
                (competidor_id, volta_n, tempo_s, vel, tod, snapshot_id),
            ).fetchone()
            if gravou:
                passagens += 1

    return {"evento_id": str(evento_id), "novo": True, "passagens_novas": passagens}


# --- leitura ----------------------------------------------------------------


def eventos(conn) -> list[dict[str, Any]]:
    linhas = conn.execute(
        """select e.id, e.nome, e.grupo, e.run_nome, e.run_tipo, e.pista_nome,
                  e.track_length_m, e.layout_id,
                  (select max(recebido_em) from lt_snapshot s where s.evento_id = e.id),
                  (select count(*) from lt_snapshot s where s.evento_id = e.id)
             from lt_evento e
            order by 9 desc nulls last"""
    ).fetchall()
    return [
        {
            "id": str(l[0]),
            "nome": l[1],
            "grupo": l[2],
            "run_nome": l[3],
            "run_tipo": l[4],
            "pista_nome": l[5],
            "track_length_m": l[6],
            "layout_id": l[7],
            "ultimo_snapshot_em": l[8].isoformat() if l[8] else None,
            "snapshots": l[9],
        }
        for l in linhas
    ]


def estado(conn, evento_id) -> dict[str, Any] | None:
    """O que a visao de campeonato desenha: evento + ultimo snapshot parseado.

    A posicao dos carrinhos no mapa NAO sai daqui: sai do front, interpolando
    `ultima_passagem_s` de cada carro contra o `timeofday_s` do snapshot sobre
    o tracado de referencia. Este endpoint entrega os ingredientes e declara o
    metodo, nao esconde a estimativa.
    """
    ev = conn.execute(
        """select id, nome, grupo, run_nome, run_tipo, pista_nome, track_length_m, layout_id
             from lt_evento where id = %s""",
        (evento_id,),
    ).fetchone()
    if not ev:
        return None
    snap = conn.execute(
        """select id, timeofday, racetime, flag, labels, resultados, recebido_em
             from lt_snapshot where evento_id = %s
            order by recebido_em desc limit 1""",
        (evento_id,),
    ).fetchone()

    corpo: dict[str, Any] = {
        "evento": {
            "id": str(ev[0]),
            "nome": ev[1],
            "grupo": ev[2],
            "run_nome": ev[3],
            "run_tipo": ev[4],
            "pista_nome": ev[5],
            "track_length_m": ev[6],
            "layout_id": ev[7],
        },
        "snapshot": None,
    }
    if snap:
        corpo["snapshot"] = {
            "id": str(snap[0]),
            "timeofday": snap[1],
            "timeofday_s": _segundos(snap[1]),
            "racetime": snap[2],
            "flag": snap[3],
            "labels": snap[4],
            "resultados": snap[5],
            "recebido_em": snap[6].isoformat(),
        }
    return corpo


def voltas_do_evento(conn, evento_id) -> list[dict[str, Any]]:
    """O historico acumulado (lt_passagem), por competidor, pra evolucao."""
    linhas = conn.execute(
        """select c.numero, c.nome, c.classe, p.volta, p.tempo_s, p.timeofday
             from lt_passagem p join lt_competidor c on c.id = p.competidor_id
            where c.evento_id = %s
            order by c.numero, p.volta""",
        (evento_id,),
    ).fetchall()
    por_carro: dict[str, dict[str, Any]] = {}
    for numero, nome, classe, volta, tempo_s, tod in linhas:
        carro = por_carro.setdefault(
            numero, {"numero": numero, "nome": nome, "classe": classe, "voltas": []}
        )
        carro["voltas"].append({"n": volta, "tempo_s": tempo_s, "timeofday": tod})
    return list(por_carro.values())
