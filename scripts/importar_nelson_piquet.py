#!/usr/bin/env python3
"""Importa o acervo do Autodromo Nelson Piquet montando a espinha inteira.

Estrutura criada, na ordem decidida pelo Lucas em 30/08:

    evento (um por DIA de pista)
      piloto (quem dirigiu)
        sessao (um bloco continuo de saidas do mesmo piloto no dia)
          saida pra pista (uma por arquivo)
            telemetria (a gravacao, ingerida pelo pipeline normal)

POR QUE O PILOTO ENTRA AQUI, e nao como atributo solto: um dia de pista no
Nelson Piquet teve ate 8 pilotos diferentes (27/06). Sem o degrau, as sessoes
de todo mundo caem no mesmo balaio e "como foi o dia do Andre" nao tem onde ser
perguntado.

IDENTIDADE, que e a parte delicada. O acervo trouxe 24 grafias para 13 pessoas:

  - encoding do logger quebra acento: o .xrk grava "Andre" em latin-1 e o
    leitor entrega "AndrÃ©". O nome do ARQUIVO preserva o acento, entao a fonte
    boa e o cruzamento dos dois, nunca um so;
  - numero do carro cola no nome do piloto: "Miguel Pantazis 296" anda de
    "Ferrari 296", "Joao Almeida 9" de "911 turbo s 9". O numero e do carro;
  - apelido e grafia: "Edu" e "Eduardo Senra", "Vitor" e "Victor Lira".

As fusoes abaixo NAO foram inferidas: cada uma foi confirmada pelo Lucas em
30/08. Fundir por semelhanca seria arriscar juntar duas pessoas, e o acervo tem
justamente um par que NAO pode ser fundido (William Bento e Henrique Bento).
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
from zoneinfo import ZoneInfo
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from saru_poc.db import connect  # noqa: E402
from saru_poc.pipeline.ingestao import ingerir  # noqa: E402
from saru_poc.pipeline.recepcao import receber  # noqa: E402
from saru_poc.readers.xrk import LeitorXrk  # noqa: E402

# O logger grava HORA LOCAL da pista, sem fuso. Gravar esse valor cru numa
# coluna timestamptz faz o banco assumir UTC, e a tela mostra a saida 3 horas
# mais cedo: "10h32" no rotulo e "07:32" na data, medido em 30/08. Fuso da
# casa e regra dura, entao o horario nasce consciente aqui.
FUSO_DA_PISTA = ZoneInfo("America/Sao_Paulo")

# Confirmado pelo Lucas em 30/08, uma decisao por linha. A chave e a forma
# normalizada; o valor e o nome que fica.
FUSOES = {
    "edu senra": "Eduardo Senra",
    "eduardo senra": "Eduardo Senra",
    "victor lira": "Vitor Lira",       # "Vitor" aparece mais no acervo
    "vitor lira": "Vitor Lira",
    "william": "William Bento",
    "william bento": "William Bento",
    # Henrique Bento NAO entra aqui: e outra pessoa, mesmo sobrenome.
    "kiko": "Kiko Sousa",              # nome completo dado pelo Lucas
    "joao paulo bandeira": "Joao Almeida",   # mesma pessoa, confirmado
    "joao almeida": "Joao Almeida",
}

# Acima disto, duas saidas do mesmo piloto no mesmo dia viram sessoes
# diferentes. 90 min separa manha de tarde sem picotar a manha: o acervo tem
# intervalos de ate 391 min entre saidas do mesmo dia, e saidas seguidas caem
# em 10 a 40 min.
CORTE_DE_SESSAO_MIN = 90

# Acima disto o arquivo nao e uma saida, e o logger que ficou ligado com o
# carro entrando e saindo. Sao 11 arquivos no acervo, o maior com 2h20. Eles
# entram assim mesmo (o corte de volta resolve o que aconteceu dentro), mas com
# o rotulo dizendo o que sao, pra ninguem ler "saida de 140 min" como fato.
SAIDA_LONGA_MIN = 45


def conserta_encoding(s: str) -> str:
    """Desfaz o mojibake do logger: 'AndrÃ© Gomide' vira 'André Gomide'."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def normalizar(s: str) -> str:
    s = conserta_encoding(s).strip().lower()
    s = re.sub(r"\s+\d+$", "", s)  # numero do carro colado no fim
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s)


def limpar_grafia(s: str) -> str:
    """Grafia sem o numero do carro colado no fim, com o acento consertado."""
    return re.sub(r"\s+\d+$", "", conserta_encoding(s).strip())


def tem_acento(s: str) -> bool:
    return any(unicodedata.category(c) == "Mn" for c in unicodedata.normalize("NFD", s))


def eleger_nomes(itens: list[dict]) -> dict[str, str]:
    """Uma grafia por pessoa, decidida pelo acervo inteiro e nao arquivo a arquivo.

    A primeira versao disto escolhia a grafia por arquivo, e o Andre Gomide
    saiu como DUAS pessoas: 11 arquivos gravados "Andre" e 8 "André". A chave
    normalizada junta os dois; o nome que fica e a grafia mais frequente, e no
    empate ganha a que tem acento, que e a correta em portugues.
    """
    vistos: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    decidido: dict[str, str] = {}
    for i in itens:
        bruta = normalizar(i["grafia"])
        chave = normalizar(FUSOES[bruta]) if bruta in FUSOES else bruta
        if bruta in FUSOES:
            decidido[chave] = FUSOES[bruta]
        vistos[chave][limpar_grafia(i["grafia"])] += 1
        if i.get("do_arquivo"):
            vistos[chave][limpar_grafia(i["do_arquivo"])] += 1
    eleitos = {}
    for chave, grafias in vistos.items():
        if chave in decidido:
            eleitos[chave] = decidido[chave]
            continue
        # ACENTO GANHA DA FREQUENCIA. "Andre" aparece 11 vezes e "André" 8, mas
        # a grafia sem acento e erro de digitacao do logger, nao uma escolha de
        # como a pessoa se chama. Frequencia decide o resto (Vitor contra
        # Victor, por exemplo, onde as duas sao grafias legitimas).
        eleitos[chave] = max(grafias.items(), key=lambda kv: (tem_acento(kv[0]), kv[1]))[0]
    return eleitos


def numero_do_carro(piloto_bruto: str, veiculo: str) -> str | None:
    """O numero vaza pro nome do piloto e tambem aparece no carro."""
    for candidato in (piloto_bruto, veiculo):
        m = re.search(r"\s(\d{1,3})$", conserta_encoding(candidato or "").strip())
        if m:
            return m.group(1)
    return None


def levantar(raiz: Path) -> list[dict]:
    leitor = LeitorXrk()
    itens = []
    for f in sorted(raiz.rglob("*.xrk")):
        cab = leitor.inspecionar(f)
        bruto = dict(cab.bruto)
        piloto_bruto = bruto.get("piloto") or f.stem.split("_")[0]
        quando = dt.datetime.strptime(cab.capturado_em, "%m/%d/%Y %H:%M:%S").replace(
            tzinfo=FUSO_DA_PISTA
        )
        itens.append({
            "caminho": f,
            "quando": quando,
            "duracao_s": cab.duracao_s or 0.0,
            "grafia": conserta_encoding(piloto_bruto),
            "do_arquivo": f.stem.split("_")[0],
            "veiculo": conserta_encoding(bruto.get("veiculo") or "?"),
            "numero": numero_do_carro(piloto_bruto, bruto.get("veiculo") or ""),
            "venue": cab.venue_declarado,
        })
    eleitos = eleger_nomes(itens)
    for i in itens:
        chave = normalizar(i["grafia"])
        chave = normalizar(FUSOES.get(chave, chave))
        i["piloto"] = eleitos[chave]
    return sorted(itens, key=lambda i: i["quando"])


def agrupar_em_sessoes(itens: list[dict]) -> list[list[dict]]:
    """Saidas seguidas do mesmo piloto viram uma sessao ate abrir a lacuna."""
    blocos: list[list[dict]] = []
    for item in itens:
        if blocos and (item["quando"] - blocos[-1][-1]["quando"]).total_seconds() / 60 <= CORTE_DE_SESSAO_MIN:
            blocos[-1].append(item)
        else:
            blocos.append([item])
    return blocos


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raiz", type=Path)
    p.add_argument("--email", required=True, help="dono do acervo (usuario ja existente)")
    p.add_argument("--track-id", default="brasilia_gp", help="id da pista no catalogo")
    p.add_argument("--dry-run", action="store_true", help="mostra o plano e nao grava")
    p.add_argument("--limite", type=int, help="importa so os N primeiros arquivos")
    args = p.parse_args()

    itens = levantar(args.raiz)
    if args.limite:
        itens = itens[: args.limite]
    print(f"{len(itens)} arquivos, {len({i['piloto'] for i in itens})} pilotos, "
          f"{len({i['quando'].date() for i in itens})} dias")

    with connect() as conn:
        dono = conn.execute("select id from usuario where email = %s", (args.email,)).fetchone()
        if dono is None and not args.dry_run:
            print(f"erro: nao existe usuario com e-mail {args.email}", file=sys.stderr)
            return 2
        user_id = dono[0] if dono else None

        # de-para de grafias por pessoa, pra guardar em piloto.apelidos
        grafias = collections.defaultdict(set)
        for i in itens:
            grafias[i["piloto"]].add(i["grafia"])

        criados = collections.Counter()
        por_dia = collections.defaultdict(list)
        for i in itens:
            por_dia[i["quando"].date()].append(i)

        for dia, do_dia in sorted(por_dia.items()):
            nome_evento = f"Dia de pista, Nelson Piquet, {dia:%d/%m/%Y}"
            if args.dry_run:
                print(f"\n{nome_evento}")
            else:
                # BUSCA ANTES DE INSERIR. A primeira versao usava `on conflict
                # do nothing`, mas nao existe unique em (user_id, name): o
                # conflito nunca acontecia e cada reexecucao criava o dia de
                # pista de novo, com sessoes e saidas junto. Sem chave unica no
                # banco, a idempotencia tem que ser explicita aqui.
                ev = conn.execute(
                    "select id from evento where user_id = %s and name = %s",
                    (user_id, nome_evento),
                ).fetchone()
                if ev is None:
                    ev = conn.execute(
                        """insert into evento (user_id, track_id, name, tipo, starts_at, local_date)
                           values (%s, %s, %s, 'track_day', %s, %s) returning id""",
                        (user_id, args.track_id, nome_evento, do_dia[0]["quando"], dia),
                    ).fetchone()
                    criados["evento"] += 1
                evento_id = ev[0]

            por_piloto = collections.defaultdict(list)
            for i in do_dia:
                por_piloto[i["piloto"]].append(i)

            for piloto, saidas in sorted(por_piloto.items()):
                if not args.dry_run:
                    pl = conn.execute(
                        """insert into piloto (user_id, name, apelidos)
                           values (%s, %s, %s)
                           on conflict (user_id, name) do update
                             set apelidos = (select array_agg(distinct a) from unnest(
                                   piloto.apelidos || excluded.apelidos) a)
                           returning id""",
                        (user_id, piloto, sorted(grafias[piloto])),
                    ).fetchone()
                    piloto_id = pl[0]

                blocos = agrupar_em_sessoes(saidas)
                if args.dry_run:
                    print(f"  {piloto}: {len(saidas)} saidas em {len(blocos)} sessao(oes)")
                for n, bloco in enumerate(blocos, start=1):
                    rotulo = f"{bloco[0]['quando']:%Hh%M} a {bloco[-1]['quando']:%Hh%M}"
                    if args.dry_run:
                        print(f"    sessao {n} ({rotulo}), {len(bloco)} saidas")
                        for i in bloco:
                            longa = " [logger ligado]" if i["duracao_s"] / 60 > SAIDA_LONGA_MIN else ""
                            print(f"      {i['quando']:%H:%M} {i['duracao_s']/60:5.0f} min  "
                                  f"{i['veiculo']}{longa}")
                        continue

                    # IDEMPOTENTE por (evento, piloto, rotulo): a primeira versao
                    # criava sessao e saida sempre, e reexecutar o importador
                    # deixou 5 saidas vazias no banco, porque a telemetria caiu
                    # na saida da primeira rodada (o arquivo ja existia, dedupe
                    # por sha) e a segunda ficou orfa. Importar de novo agora
                    # reaproveita a espinha em vez de duplicar.
                    ses = conn.execute(
                        """select id from sessao
                            where event_id = %s and piloto_id = %s and label = %s""",
                        (evento_id, piloto_id, rotulo),
                    ).fetchone()
                    if ses is None:
                        ses = conn.execute(
                            """insert into sessao (user_id, event_id, piloto_id, type, label, starts_at)
                               values (%s, %s, %s, 'trackday_battery', %s, %s) returning id""",
                            (user_id, evento_id, piloto_id, rotulo, bloco[0]["quando"]),
                        ).fetchone()
                        criados["sessao"] += 1
                    sessao_id = ses[0]

                    # Rotulo tem que ser UNICO dentro da sessao: ele e a chave
                    # de idempotencia da saida. Dois arquivos do mesmo carro
                    # comecando no mesmo minuto existem de verdade no acervo
                    # (o Andre tem gravacoes as 09:47:22 e 09:47:39), e sem o
                    # desempate os dois caiam na mesma saida.
                    vistos_no_bloco: dict[str, int] = {}
                    for i in bloco:
                        minutos = i["duracao_s"] / 60
                        etiqueta = f"{i['quando']:%Hh%M}, {i['veiculo']}"
                        vistos_no_bloco[etiqueta] = vistos_no_bloco.get(etiqueta, 0) + 1
                        if vistos_no_bloco[etiqueta] > 1:
                            etiqueta = f"{i['quando']:%Hh%M:%S}, {i['veiculo']}"
                        if minutos > SAIDA_LONGA_MIN:
                            etiqueta += f" ({minutos:.0f} min, logger ligado entre idas)"
                        bat = conn.execute(
                            "select id from bateria where session_id = %s and label = %s",
                            (sessao_id, etiqueta),
                        ).fetchone()
                        if bat is None:
                            bat = conn.execute(
                                """insert into bateria (user_id, session_id, evento_id, label, went_out_at)
                                   values (%s, %s, %s, %s, %s) returning id""",
                                (user_id, sessao_id, evento_id, etiqueta, i["quando"]),
                            ).fetchone()
                            criados["saida"] += 1
                        bateria_id = bat[0]

                        rec = receber(conn, [i["caminho"]], label=etiqueta)
                        gravacao_id = rec.gravacao_id
                        arquivo_id = rec.arquivos[0].id if rec.arquivos else None
                        # `gravacao.piloto_id` NAO e preenchido aqui de proposito: o
                        # schema (005) so permite piloto na gravacao quando ela esta
                        # SOLTA, sem saida. Com a saida pendurada, o piloto vem pela
                        # espinha, e agora ele vem da sessao (migration 024).
                        # `user_id` E OBRIGATORIO aqui: `receber()` cria a gravacao
                        # como acervo (dono nulo, que e valido pelo schema), mas
                        # toda leitura da tela filtra por dono. Sem isto a saida
                        # aparece com "0 arquivos" mesmo com a telemetria
                        # pendurada, medido em 30/08.
                        conn.execute(
                            "update gravacao set bateria_id = %s, user_id = %s where id = %s",
                            (bateria_id, user_id, gravacao_id),
                        )
                        # recepcao dedupe por sha256: reimportar a mesma pasta nao
                        # duplica gravacao, so acrescenta historico de ingestao
                        if rec.ja_existia or arquivo_id is None:
                            criados["telemetria_ja_existia"] += 1
                        else:
                            ingerir(conn, arquivo_id)
                            criados["telemetria"] += 1
                        conn.commit()

        if not args.dry_run:
            conn.commit()
            print("\ncriado:", dict(criados))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
