#!/usr/bin/env python3
"""Simulador de live timing: o painel do autodromo sem sair da mesa.

Gera um `resultspage` (padrao MyLaps/Orbits, o mesmo do MBR Time Attack) que
EVOLUI no tempo: carros cruzando a linha, melhor volta caindo, pit stop
ocasional. Serve o XML por HTTP na porta local, igual o Orbits faz na rede do
autodromo, e o `relay_livetiming.py` consome dali como consumiria na pista.

E o banco de testes da visao de campeonato (mapa estilo HH Timing + SSE):
a animacao dos carrinhos, a derivacao de passagens e o leaderboard mexendo
so aparecem com fonte VIVA, e o XML real baixado do evento e um snapshot
congelado.

Uso (dois terminais):
    # 1. o "autodromo": serve current.xml evoluindo a cada 2 s
    python scripts/simular_livetiming.py --porta 8123

    # 2. o relay, apontado pra ele:
    SARU_MAQUINA_TOKEN=saru_mq_... python scripts/relay_livetiming.py \\
        --fonte http://127.0.0.1:8123/current.xml --api http://127.0.0.1:8010

Default e Interlagos porque e um layout com traçado medido no acervo de dev
(o mapa anima); troque com --pista/--comprimento-km pra testar a degradacao.

Stdlib puro, mesmo criterio do relay: roda em qualquer maquina sem instalar
nada.
"""

from __future__ import annotations

import argparse
import random
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from xml.sax.saxutils import escape, quoteattr

PILOTOS = [
    "Marcelo Lemke",
    "Rodrigo Fontes",
    "Pedro Albuquerque",
    "Carla Menezes",
    "Tiago Sarmento",
    "Bruna Ferraz",
    "Eduardo Pacheco",
    "Rafael Quintela",
    "Luiza Andrade",
    "Otavio Ramos",
    "Felipe Baradel",
    "Marina Couto",
    "Gustavo Leal",
    "Henrique Sales",
    "Aline Nogueira",
    "Diego Furtado",
    "Vitor Camargo",
    "Paulo Cezar Brito",
    "Renata Solano",
    "Icaro Bastos",
    "Caio Drummond",
    "Sofia Rezende",
    "Nelson Prado",
    "Tales Moreira",
]
CARROS = [
    "Golf GTI MK7",
    "Civic Type R FL5",
    "BRZ tS",
    "Supra MK5",
    "M2 G87",
    "AMG A45 S",
    "Corolla GR",
    "308 THP",
    "Fusca Turbo",
    "Opala SS",
    "Chevette Aspirado",
    "Uno Way T",
    "Cupra Leon",
    "RS3 8Y",
    "GT86",
    "Lancer Evo X",
    "Impreza STI",
    "Mini JCW",
    "Polo GTS",
    "Onix Turbo",
    "MX-5 ND",
    "Puma GTE",
    "Passat TS",
    "Gol GTS",
]
CLASSES = [
    "FWD CLUBSPORT",
    "FWD PRORACE",
    "RWD CLUBSPORT",
    "RWD PRORACE",
    "AWD PRORACE",
]


class Carro:
    """Um carro simulado. A volta e PLANEJADA em 3 setores (fracoes fixas com
    ruido leve, renormalizadas): o XML preenche `sectionN` conforme o carro
    completa cada parcial, e zera na virada da volta, exatamente o ciclo do
    Orbits real. E o que permite a tela mostrar delta instantaneo por setor
    (pedido de 29/08: parcial verde nao garante acumulado melhor no fim)."""

    FRACOES_SETOR = (0.32, 0.36, 0.32)

    def __init__(self, i: int, comprimento_m: float, rng: random.Random) -> None:
        self.numero = str(rng.choice([i + 1, 100 + i, 200 + i]))
        self.transponder = str(1000 + i)
        self.piloto = PILOTOS[i % len(PILOTOS)]
        self.carro = CARROS[i % len(CARROS)]
        self.classe = CLASSES[i % len(CLASSES)]
        # ritmo base: ~90 km/h a ~140 km/h de media, dependendo do carro
        media_kmh = rng.uniform(88.0, 142.0)
        self.ritmo_s = comprimento_m / (media_kmh / 3.6)
        self.comprimento_m = comprimento_m
        self.voltas: list[tuple[float, float]] = []  # (tempo_da_volta_s, tod_cruzamento_s)
        self.setores_da_volta: list[float] = []  # parciais completadas da volta corrente
        self.melhores_setores: list[float | None] = [None, None, None]
        self.plano: list[float] = []
        self.proximo_evento: float | None = None
        # ultima passagem em QUALQUER sensor (intermediario ou chegada), como
        # no Orbits real: e o que poe o carro no mapa ja na primeira parcial
        self.ultima_passagem: float | None = None
        self.ultima_linha: str = ""
        self.rng = rng

    def _planejar_volta(self) -> list[float]:
        variacao = self.rng.gauss(0.0, self.ritmo_s * 0.012)
        tempo_volta = max(self.ritmo_s * 0.94, self.ritmo_s + variacao)
        # cada setor com ruido proprio, renormalizado pro total da volta: e o
        # que produz "parcial melhor que o lider, acumulado pior"
        pesos = [f * self.rng.uniform(0.94, 1.06) for f in self.FRACOES_SETOR]
        soma = sum(pesos)
        setores = [tempo_volta * w / soma for w in pesos]
        if self.rng.random() < 0.03:
            # parada de box no fim da volta: estoura o ultimo setor
            setores[-1] += self.rng.uniform(60.0, 150.0)
        return setores

    def tick(self, agora_tod: float) -> None:
        """Avanca a simulacao ate `agora_tod` (segundos do dia)."""
        if self.proximo_evento is None:
            # entra na pista escalonado, na primeira chamada
            entrada = agora_tod + self.rng.uniform(0.0, 90.0)
            self.plano = self._planejar_volta()
            self.proximo_evento = entrada + self.plano[0]
            return
        while agora_tod >= self.proximo_evento:
            k = len(self.setores_da_volta)
            tempo_setor = self.plano[k]
            self.setores_da_volta.append(tempo_setor)
            self.ultima_passagem = self.proximo_evento
            self.ultima_linha = (
                "Finish" if len(self.setores_da_volta) == len(self.plano) else f"Intermediate {k + 1}"
            )
            melhor = self.melhores_setores[k]
            if melhor is None or tempo_setor < melhor:
                self.melhores_setores[k] = tempo_setor
            if len(self.setores_da_volta) == len(self.plano):
                # virada de volta: consolida e comeca o plano novo, secoes zeram
                self.voltas.append((sum(self.plano), self.proximo_evento))
                self.plano = self._planejar_volta()
                self.setores_da_volta = []
                self.proximo_evento += self.plano[0]
            else:
                self.proximo_evento += self.plano[k + 1]

    # --- leituras pro XML ---------------------------------------------------

    @property
    def n_voltas(self) -> int:
        return len(self.voltas)

    def melhor(self) -> tuple[float, int] | None:
        if not self.voltas:
            return None
        i = min(range(len(self.voltas)), key=lambda k: self.voltas[k][0])
        return self.voltas[i][0], i + 1

    def ultimas(self) -> list[float]:
        return [v[0] for v in self.voltas[-3:]][::-1]

    def velocidade(self, tempo_volta: float) -> float:
        return self.comprimento_m / tempo_volta * 3.6


def fmt_tempo(s: float) -> str:
    m, resto = divmod(s, 60.0)
    if m >= 60:
        h, m = divmod(int(m), 60)
        return f"{h}:{m:02d}:{resto:06.3f}"
    return f"{int(m)}:{resto:06.3f}"


def fmt_virgula(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def fmt_tod(s: float) -> str:
    h, resto = divmod(int(s), 3600)
    m, seg = divmod(resto, 60)
    mils = round((s % 1) * 1000)
    return f"{h:02d}:{m:02d}:{seg:02d}.{mils:03d}"


def gerar_xml(
    carros: list[Carro],
    agora_tod: float,
    evento: str,
    pista: str,
    comprimento_km: float,
    inicio_tod: float,
) -> bytes:
    com_volta = [c for c in carros if c.n_voltas > 0]
    com_volta.sort(key=lambda c: c.melhor()[0])  # time attack: grid por melhor volta
    sem_volta = [c for c in carros if c.n_voltas == 0]

    melhor_geral = com_volta[0].melhor() if com_volta else None
    linhas: list[str] = []
    por_classe: dict[str, int] = {}
    for posicao_geral, c in enumerate(com_volta + sem_volta, start=1):
        por_classe[c.classe] = por_classe.get(c.classe, 0) + 1
        ultimas = c.ultimas()
        melhor = c.melhor()
        attrs = {
            "position": str(posicao_geral),
            "positioninclass": str(por_classe[c.classe]),
            "no": c.numero,
            "transponder": c.transponder,
            "fullname": f"{c.piloto} | {c.carro}",
            "firstname": f"{c.piloto} |",
            "lastname": c.carro,
            "class": c.classe,
            "laps": str(c.n_voltas),
            "lasttime": fmt_tempo(ultimas[0]) if ultimas else "",
            "secondlasttime": fmt_tempo(ultimas[1]) if len(ultimas) > 1 else "",
            "thirdlasttime": fmt_tempo(ultimas[2]) if len(ultimas) > 2 else "",
            "besttime": fmt_tempo(melhor[0]) if melhor else "",
            "bestinlap": str(melhor[1]) if melhor else "",
            "bestspeed": fmt_virgula(c.velocidade(melhor[0])) if melhor else "",
            "lastspeed": fmt_virgula(c.velocidade(ultimas[0])) if ultimas else "",
            "averagetime": fmt_tempo(sum(u[0] for u in c.voltas) / c.n_voltas)
            if c.n_voltas
            else "",
            "totaltime": fmt_tempo(sum(u[0] for u in c.voltas)) if c.n_voltas else "",
            "lasttimeofday": (
                fmt_tod(c.ultima_passagem) if c.ultima_passagem is not None else ""
            ),
            "lasttimeline": c.ultima_linha,
            **{
                f"section{i}": (
                    fmt_tempo(c.setores_da_volta[i]) if i < len(c.setores_da_volta) else ""
                )
                for i in range(3)
            },
            **{
                f"bestsection{i}": (
                    fmt_tempo(c.melhores_setores[i])
                    if c.melhores_setores[i] is not None
                    else ""
                )
                for i in range(3)
            },
            "gap": "",
            "difference": (
                f"{c.melhor()[0] - melhor_geral[0]:.3f}"
                if melhor and melhor_geral and c is not com_volta[0]
                else ""
            ),
        }
        campos = " ".join(f"{k}={quoteattr(v)}" for k, v in attrs.items())
        linhas.append(f"<result {campos} />")

    labels = {
        "eventname": evento,
        "groupname": "SIMULADOR SARU",
        "runname": "Simulado",
        "runtype": "P",
        "trackname": pista,
        "tracklength": fmt_virgula(comprimento_km),
        "timeofday": fmt_tod(agora_tod)[:8],
        "racetime": fmt_tod(agora_tod - inicio_tod)[:8],
        "flag": "green",
        "laps": str(max((c.n_voltas for c in carros), default=0)),
    }
    if melhor_geral:
        lider = com_volta[0]
        labels["bestlaptime"] = fmt_tempo(melhor_geral[0])
        labels["bestlapby"] = f"{lider.numero} - {lider.piloto} | {lider.carro}"

    partes = ['<?xml version="1.0" encoding="utf-8" ?><resultspage>']
    partes += [f'<label type="{k}">{escape(v)}</label>' for k, v in labels.items()]
    partes.append("<results>")
    partes += linhas
    partes.append("</results></resultspage>")
    return "".join(partes).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Simulador de resultspage (MyLaps/Orbits)"
    )
    parser.add_argument(
        "--porta",
        type=int,
        default=8123,
        help="porta HTTP local (o 'painel do autodromo')",
    )
    parser.add_argument("--carros", type=int, default=24)
    parser.add_argument("--evento", default="TRACK DAY SIMULADO SARU")
    parser.add_argument("--pista", default="Autódromo de Interlagos")
    parser.add_argument("--comprimento-km", type=float, default=4.309)
    parser.add_argument(
        "--intervalo",
        type=float,
        default=2.0,
        help="segundos entre atualizacoes do XML",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="semente pra repetir a mesma corrida"
    )
    args = parser.parse_args()

    rng = random.Random(args.seed)
    comprimento_m = args.comprimento_km * 1000.0
    carros = [Carro(i, comprimento_m, rng) for i in range(args.carros)]

    agora = datetime.now()  # noqa: DTZ005 (relogio local e o relogio da cronometragem simulada)
    inicio_tod = agora.hour * 3600 + agora.minute * 60 + agora.second
    partida = time.monotonic()
    xml_atual: bytes = b""
    trava = threading.Lock()

    def atualizar() -> None:
        nonlocal xml_atual
        while True:
            tod = inicio_tod + (time.monotonic() - partida)
            for c in carros:
                c.tick(tod)
            novo = gerar_xml(
                carros, tod, args.evento, args.pista, args.comprimento_km, inicio_tod
            )
            with trava:
                xml_atual = novo
            time.sleep(args.intervalo)

    threading.Thread(target=atualizar, daemon=True).start()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in ("/current.xml", "/results.xml", "/"):
                self.send_error(404)
                return
            with trava:
                corpo = xml_atual
            self.send_response(200)
            self.send_header("Content-Type", "application/xml; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)

        def log_message(self, *_: object) -> None:
            pass  # o relay bate a cada 2 s, logar cada GET so faz ruido

    servidor = ThreadingHTTPServer(("127.0.0.1", args.porta), Handler)
    print(
        f"simulando {args.carros} carros em {args.pista} ({args.comprimento_km:.3f} km)"
    )
    print(
        f"XML vivo em http://127.0.0.1:{args.porta}/current.xml (atualiza a cada {args.intervalo:.0f}s)"
    )
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
