"""Mede o limiar de frenagem por desaceleracao longitudinal contra o acervo.

Reproduz a regua da calibracao de 2026-08-22 do saru-app
(`tools/calibrate_braking_threshold.py`) usando os leitores e o mapa de canais
da PoC (`saru_poc.readers`, `seeds/aliases.yaml`), sem banco: tudo em memoria.

Verdade (ground truth) = canal de freio real do arquivo (pedal ou pressao).
Candidato = deteccao so por `lon_acc` canonico abaixo de um limiar, sustentada
por uma distancia minima. Nada aqui vira codigo de produto.

Uso:
    uv run python medir_limiar_frenagem.py --raiz <dir> --out <json>
"""
from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from saru_poc.acervo import PERFIL_PARA_FORMATO, caminho_aliases, ler_aliases
from saru_poc.pipeline.corte_voltas import (
    CANAIS_CONTADOR,
    CANAIS_PULSO,
    MIN_VOLTA_S,
    passagens_de_beacons_ldx,
    passagens_de_contador,
    passagens_de_pulso,
    voltas_de_passagens,
)
from saru_poc.pipeline.decomposicao import (
    distancia_por_canal,
    distancia_por_velocidade,
)
from saru_poc.readers import detectar, leitor_de

# --- parametros da MEDICAO (espelham a calibracao de 2026-08-22) ----------
BRAKE_LO_PCT = 5.0          # "quieto": freio abaixo disso
BRAKE_HI_PCT = 15.0         # onset real: freio acima disso
QUIET_M = 30.0              # quieto minimo antes do onset
BRAKE_SUSTAIN_M = 8.0       # sustentacao minima do freio no onset
DROP_WINDOW_M = 40.0        # janela pos-onset onde se mede a queda de lon_acc
MATCH_TOL_M = 30.0          # tolerancia de casamento onset real <-> detectado
MIN_COVERAGE = 0.9          # cobertura minima do eixo de distancia da volta
DS_M = 1.0                  # passo do eixo de distancia reamostrado
MIN_VOLTA_M = 500.0         # volta menor que isso nao e volta de pista

THRESHOLDS = [-2.0, -2.5, -3.0, -3.5, -4.0, -5.0, -6.0, -8.0, -10.0, -12.0]
MIN_DURATIONS_M = [10.0, 8.0]
REGUAS = ["estrita", "rampa"]

# Canais canonicos que interessam, por ordem de preferencia semantica.
CANONICOS = ("lon_acc", "brake", "speed", "distance_m", "distance", "lap_number")


# --- carga do mapa de canais ---------------------------------------------
def carregar_perfis() -> dict[str, dict[str, dict]]:
    """Perfis do aliases.yaml, so os que tem formato no catalogo da PoC."""
    todos = ler_aliases(caminho_aliases())
    return {p: c for p, c in todos.items() if p in PERFIL_PARA_FORMATO}


PERFIS = carregar_perfis()
FORMATO_PARA_PERFIS: dict[str, list[str]] = defaultdict(list)
for _p in PERFIS:
    FORMATO_PARA_PERFIS[PERFIL_PARA_FORMATO[_p]].append(_p)


def colunas_do_perfil(perfil: str) -> set[str]:
    cols: set[str] = set()
    for spec in PERFIS[perfil].values():
        col = spec.get("col")
        if isinstance(col, list):
            cols.update(col)
        elif col:
            cols.add(col)
    return cols


# Guardas da heuristica de perfil, iguais as de `pipeline/ingestao.py`.
COBERTURA_MINIMA = 0.25
MARGEM_MINIMA = 3


def escolher_perfil(formato_id: str, nomes: set[str]) -> tuple[str | None, str]:
    cands = FORMATO_PARA_PERFIS.get(formato_id, [])
    if not cands:
        return None, f"nenhum perfil para o formato {formato_id}"
    if len(cands) == 1:
        return cands[0], f"perfil unico de {formato_id}"
    placar = sorted(((len(nomes & colunas_do_perfil(p)), p) for p in cands), reverse=True)
    (n_top, top), (n_seg, _) = placar[0], placar[1]
    cobertura = n_top / max(1, len(nomes))
    if cobertura >= COBERTURA_MINIMA and n_top - n_seg >= MARGEM_MINIMA:
        return top, f"{top} por sobreposicao ({n_top}/{len(nomes)}, margem {n_top - n_seg})"
    excl = {p: colunas_do_perfil(p) - set().union(*(colunas_do_perfil(q) for q in cands if q != p))
            for p in cands}
    achados = [p for p in cands if nomes & excl[p]]
    if len(achados) == 1:
        return achados[0], f"{achados[0]} por coluna discriminante"
    return None, f"perfil ambiguo entre {cands} (melhor {top}: {n_top}/{len(nomes)})"


# --- leitura de um arquivo em series por taxa ----------------------------
@dataclass
class Serie:
    t: np.ndarray
    cols: dict[str, np.ndarray]


def ler_series(leitor, caminho: Path) -> dict[tuple[float, str], Serie]:
    pedacos: dict[tuple[float, str], list] = defaultdict(list)
    for lote in leitor.ler(caminho):
        pedacos[(lote.frequencia_hz, lote.serie)].append(lote.tabela)
    saida: dict[tuple[float, str], Serie] = {}
    for chave, tabelas in pedacos.items():
        cols: dict[str, list] = defaultdict(list)
        for tb in tabelas:
            for nome in tb.schema.names:
                cols[nome].append(np.asarray(tb.column(nome).to_numpy(), dtype=float))
        juntas = {n: np.concatenate(v) for n, v in cols.items()}
        t = juntas.pop("t_s")
        ordem = np.argsort(t, kind="stable")
        saida[chave] = Serie(t=t[ordem], cols={n: v[ordem] for n, v in juntas.items()})
    return saida


@dataclass
class Canal:
    canonico: str
    bruto: str
    hz: float
    t: np.ndarray
    v: np.ndarray            # ja na unidade canonica (fator do mapa aplicado)
    pressao: bool = False    # veio de normalize_by_max (freio em bar)


def resolver_canais(
    perfil: str, series: dict[tuple[float, str], Serie]
) -> dict[str, Canal]:
    """Canal canonico -> melhor serie disponivel, por TAXA decrescente."""
    spec_por_canal = PERFIS[perfil]
    achados: dict[str, Canal] = {}
    for canonico in CANONICOS:
        spec = spec_por_canal.get(canonico)
        if not spec:
            continue
        col = spec.get("col")
        alvos = col if isinstance(col, list) else [col]
        melhor: Canal | None = None
        for (hz, _serie), s in series.items():
            for alvo in alvos:
                if alvo not in s.cols:
                    continue
                if spec.get("normalize_by_max"):
                    fator, pressao = 1.0, True    # fica em bar; normaliza depois
                else:
                    fator, pressao = float(spec.get("scale", 1.0)), False
                c = Canal(canonico, alvo, hz, s.t, s.cols[alvo] * fator, pressao)
                if melhor is None or c.hz > melhor.hz:
                    melhor = c
        if melhor is not None:
            achados[canonico] = melhor
    return achados


def para_pct(c: Canal) -> np.ndarray:
    """Freio em % do fundo de escala do proprio arquivo.

    Pedal sai do mapa como fracao 0-1 (`unit_out: '0-1'`), entao vira % por
    multiplicacao. Pressao em bar nao tem fundo de escala declarado: normaliza
    pelo maximo da gravacao, descontando o zero do sensor (p1), que no acervo
    chega a 4,4 bar em .xrk de F3 e sem o desconto empurraria o repouso pra
    cima do piso de 5% da regua.
    """
    v = np.asarray(c.v, dtype=float)
    fin = v[np.isfinite(v)]
    if fin.size == 0:
        return v
    if not c.pressao:
        return v * 100.0
    base = float(np.percentile(fin, 1))
    topo = float(np.max(fin))
    if topo - base <= 0:
        return np.zeros_like(v)
    return (v - base) / (topo - base) * 100.0


# --- corte de voltas ------------------------------------------------------
def cortar_voltas(
    canais: dict[str, Canal],
    series: dict[tuple[float, str], Serie],
    caminho: Path,
    cab,
    duracao: float,
):
    """Cascata sem banco.

    Degrau 1a: canal de volta CANONICO (pega `VBOX_lapnumber`, que o mapa
    traduz e a lista de nomes brutos da PoC nao conhece).
    Degrau 1b: nome bruto de contador ou pulso, a lista de `corte_voltas`
    (pega `Lap Number` do Pi, que o alias do perfil mapeia pela coluna
    `lap_number`, nome que o arquivo nao usa).
    Degrau 2: beacons do proprio `.xrk`. Degrau 3: beacons do `.ldx` irmao.
    """
    teto = duracao / MIN_VOLTA_S + 2
    lap = canais.get("lap_number")
    if lap is not None and len(lap.t) > 1:
        inst = passagens_de_contador(lap.t, lap.v)
        if inst and len(inst) <= teto:
            voltas = voltas_de_passagens(inst, min_volta_s=MIN_VOLTA_S)
            if voltas:
                return voltas, f"contador canonico {lap.bruto} ({lap.hz:.0f} Hz)"

    candidatos = []
    for (hz, _s), serie in series.items():
        for nome in serie.cols:
            if nome in CANAIS_CONTADOR:
                candidatos.append((hz, 0, nome, serie))
            elif nome in CANAIS_PULSO:
                candidatos.append((hz, 1, nome, serie))
    for hz, tipo, nome, serie in sorted(candidatos, key=lambda c: (-c[0], c[1])):
        v = serie.cols[nome]
        inst = (passagens_de_contador(serie.t, v) if tipo == 0
                else passagens_de_pulso(serie.t, v))
        if not inst or len(inst) > teto:
            continue
        voltas = voltas_de_passagens(inst, min_volta_s=MIN_VOLTA_S)
        if voltas:
            rotulo = "contador" if tipo == 0 else "pulso"
            return voltas, f"{rotulo} bruto {nome} ({hz:.0f} Hz)"
    bruto = (cab.bruto or {}).get("lap_beacons_ms")
    if bruto:
        try:
            inst = [int(v) / 1000.0 for v in bruto.split(",") if v.strip()]
        except ValueError:
            inst = []
        if len(inst) >= 2:
            voltas = voltas_de_passagens(inst, min_volta_s=MIN_VOLTA_S)
            if voltas:
                return voltas, "beacons do proprio .xrk"
    ldx = caminho.with_suffix(".ldx")
    if ldx.exists():
        try:
            cldx = leitor_de("motec_ldx").inspecionar(ldx)
        except Exception:
            cldx = None
        cru = (cldx.bruto or {}).get("beacons_time_us_raw") if cldx else None
        if cru:
            inst = passagens_de_beacons_ldx(cru)
            # relogio do sidecar tem que caber na gravacao, senao nao alinha
            if len(inst) >= 2 and inst[-1] <= duracao * 1.02:
                voltas = voltas_de_passagens(inst, min_volta_s=MIN_VOLTA_S)
                if voltas:
                    return voltas, "beacons do .ldx irmao"
    return [], "sem canal de volta, sem beacon .xrk e sem .ldx utilizavel"


# --- eixo de distancia e reamostragem ------------------------------------
def eixo_distancia(canais: dict[str, Canal], t0: float, t1: float):
    """(t, s) da janela da volta, pela cascata canal de distancia -> velocidade."""
    for nome in ("distance_m", "distance"):
        c = canais.get(nome)
        if c is None:
            continue
        m = (c.t >= t0) & (c.t <= t1)
        if int(np.count_nonzero(m)) >= 8:
            return c.t[m], distancia_por_canal(c.v[m]), f"canal {c.bruto}"
    c = canais.get("speed")
    if c is not None:
        m = (c.t >= t0) & (c.t <= t1)
        if int(np.count_nonzero(m)) >= 8:
            return c.t[m], distancia_por_velocidade(c.t[m], c.v[m]), "integral da velocidade"
    return None, None, "sem canal de distancia e sem velocidade na janela"


def na_grade(c: Canal, valores: np.ndarray, t_ref, s_ref, grade):
    """Leva um canal pro eixo de distancia da volta. Devolve (valores, cobertura)."""
    m = (c.t >= t_ref[0]) & (c.t <= t_ref[-1])
    if int(np.count_nonzero(m)) < 4:
        return None, 0.0
    s_c = np.interp(c.t[m], t_ref, s_ref)
    s_c = np.maximum.accumulate(s_c)
    v_c = valores[m]
    ok = np.isfinite(v_c)
    if int(np.count_nonzero(ok)) < 4:
        return None, 0.0
    s_c, v_c = s_c[ok], v_c[ok]
    dentro = (grade >= s_c[0]) & (grade <= s_c[-1])
    cobertura = float(np.count_nonzero(dentro)) / max(1, len(grade))
    return np.interp(grade, s_c, v_c), cobertura


# --- regua da medicao -----------------------------------------------------
#: Quanto a regua "rampa" recua, no maximo, do cruzamento de 15% ate o ultimo
#: metro com o freio solto. Pedal nao leva 60 m pra sair de solto a 15%.
RAMPA_MAX_M = 60.0


def onsets_reais(brake_pct: np.ndarray, regua: str = "estrita") -> list[float]:
    """Posicoes [m] onde o freio de fato entra.

    `estrita` e a regua literal de 2026-08-22: o cruzamento de 15% so vale se
    os 30 m IMEDIATAMENTE anteriores estiverem abaixo de 5%.

    `rampa` exige o mesmo quieto de 30 m, mas conta a partir do ultimo metro
    com o freio solto antes da subida, nao a partir do cruzamento de 15%.
    Existe porque canal de freio lento transforma a subida em rampa longa: no
    `.vbo` de 10 Hz a 250 km/h cada amostra vale 7 m, e os 30 m antes do
    cruzamento ja estao no meio da propria aplicacao (medido: 12 a 15% de
    fundo de escala). A regua estrita zera os onsets nessas fontes.
    """
    quiet_n = max(1, int(QUIET_M / DS_M))
    sustain_n = max(1, int(BRAKE_SUSTAIN_M / DS_M))
    rampa_n = max(1, int(RAMPA_MAX_M / DS_M))
    abaixo = brake_pct < BRAKE_LO_PCT
    acima = brake_pct >= BRAKE_HI_PCT
    onsets: list[float] = []
    n = len(brake_pct)
    i = quiet_n
    while i < n - sustain_n:
        if acima[i] and bool(np.all(acima[i:i + sustain_n])):
            if regua == "estrita":
                base = i
            else:
                soltos = np.flatnonzero(abaixo[max(0, i - rampa_n):i])
                base = (max(0, i - rampa_n) + int(soltos[-1]) + 1) if soltos.size else -1
            if base >= quiet_n and bool(np.all(abaixo[base - quiet_n:base])):
                onsets.append(float(i * DS_M))
                if regua == "estrita":
                    # avanco literal da calibracao de 2026-08-22
                    i += sustain_n
                else:
                    # uma aplicacao, um onset: pula ate o freio voltar a
                    # ficar solto. Sem isso o mesmo `base` quieto reaprova a
                    # mesma frenagem a cada 8 m e a volta ganha onset demais.
                    solta = np.flatnonzero(abaixo[i:])
                    i = (i + int(solta[0]) + 1) if solta.size else n
                continue
        i += 1
    return onsets


def deteccoes(lon: np.ndarray, thr: float, min_dur_m: float) -> list[float]:
    need = max(1, int(min_dur_m / DS_M))
    sob = lon < thr
    saida: list[float] = []
    i, n = 0, len(sob)
    while i < n:
        if sob[i]:
            j = i
            while j < n and sob[j]:
                j += 1
            if j - i >= need:
                saida.append(float(i * DS_M))
            i = j
        else:
            i += 1
    return saida


def casar(truths, dets, brake_pct):
    usados: set[int] = set()
    deltas: list[float] = []
    tp = 0
    for t in truths:
        melhor_j, melhor_d = -1, MATCH_TOL_M + 1.0
        for j, d in enumerate(dets):
            if j in usados:
                continue
            dist = abs(d - t)
            if dist < melhor_d:
                melhor_j, melhor_d = j, dist
        if melhor_j >= 0 and melhor_d <= MATCH_TOL_M:
            usados.add(melhor_j)
            tp += 1
            deltas.append(melhor_d)
    fn = len(truths) - tp
    win = max(1, int(MATCH_TOL_M / DS_M))
    fp_sem, fp_com = 0, 0
    for j, d in enumerate(dets):
        if j in usados:
            continue
        i0 = int(d / DS_M)
        janela = brake_pct[max(0, i0 - win // 2): i0 + win]
        if janela.size and float(np.max(janela)) < BRAKE_LO_PCT:
            fp_sem += 1
        else:
            fp_com += 1
    return tp, fn, fp_sem, fp_com, deltas


# --- acumuladores ---------------------------------------------------------
@dataclass
class Fonte:
    arquivos: int = 0
    voltas: int = 0
    onsets: int = 0
    quedas: list[float] = field(default_factory=list)
    varredura: dict = field(default_factory=dict)
    descartes: dict = field(default_factory=lambda: defaultdict(int))
    origens_corte: dict = field(default_factory=lambda: defaultdict(int))
    origens_eixo: dict = field(default_factory=lambda: defaultdict(int))
    nomes: list = field(default_factory=list)
    taxas: dict = field(default_factory=lambda: defaultdict(int))

    def celula(self, chave):
        return self.varredura.setdefault(chave, [0, 0, 0, 0, []])


SUFIXOS = {".ld", ".dat", ".pid", ".xrk", ".xrz", ".vbo", ".dlf", ".mf4"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raiz", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--limite", type=int, default=0)
    args = ap.parse_args()

    import hashlib

    candidatos = sorted(p for p in args.raiz.rglob("*")
                        if p.is_file() and p.suffix.lower() in SUFIXOS)
    # O acervo repete arquivo em duas pastas (os 3 .vbo do Giaffone estao em
    # `giaffone-vbox` e em `porsche-cup`). Contar duas vezes inflaria volta e
    # onset da fonte. Dedup por hash do conteudo, nunca por nome.
    vistos: dict[str, str] = {}
    arquivos, duplicados = [], []
    for c in candidatos:
        h = hashlib.md5(c.read_bytes()).hexdigest()
        if h in vistos:
            duplicados.append(f"{c.relative_to(args.raiz)} == {vistos[h]}")
            continue
        vistos[h] = str(c.relative_to(args.raiz))
        arquivos.append(c)
    if args.limite:
        arquivos = arquivos[: args.limite]

    fontes: dict[str, Fonte] = defaultdict(Fonte)
    pulos: dict[str, int] = defaultdict(int)
    suspeitos_sinal: list[str] = []
    sem_freio: dict[str, list[str]] = defaultdict(list)
    sem_lon: dict[str, list[str]] = defaultdict(list)
    t0 = time.time()

    for k, caminho in enumerate(arquivos, 1):
        if k % 20 == 0:
            print(f"[{k}/{len(arquivos)}] {time.time() - t0:.0f}s", flush=True)
        det = detectar(caminho)
        if not det.formato:
            pulos["formato nao reconhecido"] += 1
            continue
        leitor = leitor_de(det.formato.id)
        if leitor is None or not leitor.suporta_amostra:
            pulos[f"{det.formato.id}: leitor sem amostra"] += 1
            continue
        try:
            cab = leitor.inspecionar(caminho)
            series = ler_series(leitor, caminho)
        except Exception as e:
            pulos[f"{det.formato.id}: {type(e).__name__}"] += 1
            continue

        nomes = {c.nome_bruto for c in cab.canais}
        perfil, motivo = escolher_perfil(det.formato.id, nomes)
        if perfil is None:
            pulos[f"{det.formato.id}: {motivo[:40]}"] += 1
            continue

        canais = resolver_canais(perfil, series)
        f = fontes[(perfil, "geometria")]
        if "brake" not in canais:
            sem_freio[perfil].append(caminho.name)
            f.descartes["arquivo sem canal de freio no mapa"] += 1
            continue
        if "lon_acc" not in canais:
            sem_lon[perfil].append(caminho.name)
            f.descartes["arquivo sem lon_acc no mapa"] += 1
            continue

        duracao = float(cab.duracao_s or 0.0)
        voltas, origem = cortar_voltas(canais, series, caminho, cab, duracao)
        if not voltas:
            f.descartes[f"sem corte de volta ({origem[:40]})"] += 1
            continue

        brake_pct_serie = para_pct(canais["brake"])
        lon = canais["lon_acc"]

        # Uma passada de geometria por volta; as duas reguas de onset leem a
        # MESMA volta reamostrada, entao a unica coisa que muda entre elas e o
        # que conta como onset verdadeiro.
        voltas_prontas: list[tuple] = []
        for volta in voltas:
            t_ref, s_ref, origem_eixo = eixo_distancia(canais, volta.t_inicio_s, volta.t_fim_s)
            if t_ref is None or s_ref is None or len(s_ref) < 8 or s_ref[-1] < MIN_VOLTA_M:
                f.descartes["volta sem eixo de distancia utilizavel"] += 1
                continue
            grade = np.arange(0.0, float(s_ref[-1]), DS_M)
            if len(grade) < int((QUIET_M + BRAKE_SUSTAIN_M) / DS_M) + 10:
                f.descartes["volta curta demais pra regua"] += 1
                continue
            b, cob_b = na_grade(canais["brake"], brake_pct_serie, t_ref, s_ref, grade)
            a, cob_a = na_grade(lon, lon.v, t_ref, s_ref, grade)
            if b is None or a is None or min(cob_b, cob_a) < MIN_COVERAGE:
                f.descartes["cobertura baixa do eixo de distancia"] += 1
                continue
            voltas_prontas.append((np.nan_to_num(b, nan=0.0), np.nan_to_num(a, nan=0.0), origem_eixo))
        if not voltas_prontas:
            continue

        win = max(1, int(DROP_WINDOW_M / DS_M))
        for regua in REGUAS:
            fr = fontes[(perfil, regua)]
            acumulado = []
            quedas_arquivo: list[float] = []
            for b, a, origem_eixo in voltas_prontas:
                truths = onsets_reais(b, regua)
                if not truths:
                    fr.descartes["volta sem onset real de freio"] += 1
                    continue
                quedas = [float(np.min(a[int(t / DS_M): int(t / DS_M) + win])) for t in truths]
                quedas_arquivo.extend(quedas)
                acumulado.append((truths, quedas, a, b, origem_eixo))
            if not acumulado:
                continue
            if float(np.median(quedas_arquivo)) > 0:
                suspeitos_sinal.append(f"{caminho.name} ({perfil}, regua {regua})")
                continue
            fr.arquivos += 1
            fr.nomes.append(str(caminho.relative_to(args.raiz)))
            fr.origens_corte[origem] += 1
            fr.taxas[
                f"freio {canais['brake'].bruto} {canais['brake'].hz:.0f} Hz | "
                f"lon_acc {lon.bruto} {lon.hz:.0f} Hz"
            ] += 1
            for truths, quedas, a, b, origem_eixo in acumulado:
                fr.voltas += 1
                fr.onsets += len(truths)
                fr.quedas.extend(quedas)
                fr.origens_eixo[origem_eixo] += 1
                for thr in THRESHOLDS:
                    for dur in MIN_DURATIONS_M:
                        tp, fn, fp_sem, fp_com, deltas = casar(truths, deteccoes(a, thr, dur), b)
                        cel = fr.celula((thr, dur))
                        cel[0] += tp
                        cel[1] += fn
                        cel[2] += fp_sem
                        cel[3] += fp_com
                        cel[4].extend(deltas)

    relatorio = {
        "gerado_em_s": round(time.time() - t0, 1),
        "raiz": str(args.raiz),
        "arquivos_varridos": len(arquivos),
        "duplicados_por_conteudo": duplicados,
        "pulos": dict(pulos),
        "suspeitos_de_sinal": suspeitos_sinal,
        "arquivos_sem_canal_de_freio": {k: v for k, v in sem_freio.items()},
        "arquivos_sem_lon_acc": {k: v for k, v in sem_lon.items()},
        "reguas": REGUAS,
        "parametros": {
            "brake_lo_pct": BRAKE_LO_PCT, "brake_hi_pct": BRAKE_HI_PCT,
            "quiet_m": QUIET_M, "sustain_m": BRAKE_SUSTAIN_M,
            "drop_window_m": DROP_WINDOW_M, "match_tol_m": MATCH_TOL_M,
            "min_coverage": MIN_COVERAGE, "ds_m": DS_M,
            "min_volta_m": MIN_VOLTA_M, "min_volta_s": MIN_VOLTA_S,
            "limiares": THRESHOLDS, "sustentos_m": MIN_DURATIONS_M,
        },
        "fontes": {},
    }
    for (perfil_nome, regua_nome), f in sorted(fontes.items()):
        nome = f"{perfil_nome}|{regua_nome}"
        if not f.voltas:
            relatorio["fontes"][nome] = {
                "arquivos": 0, "voltas": 0, "onsets_reais": 0,
                "descartes": dict(f.descartes),
            }
            continue
        q = np.asarray(f.quedas)
        linhas = []
        for (thr, dur), (tp, fn, fp_sem, fp_com, deltas) in sorted(f.varredura.items()):
            total = tp + fn
            det_total = tp + fp_sem + fp_com
            linhas.append({
                "limiar_ms2": thr, "sustento_m": dur,
                "onsets_reais": total, "deteccoes": det_total,
                "tp": tp, "fn": fn, "fp_sem_pedal": fp_sem, "fp_pedal_ativo": fp_com,
                "sensibilidade": round(tp / total, 3) if total else None,
                "precisao": round(tp / det_total, 3) if det_total else None,
                "precisao_fp_real": round(tp / (tp + fp_sem), 3) if (tp + fp_sem) else None,
                "fp_sem_pedal_por_volta": round(fp_sem / f.voltas, 2),
                "fp_pedal_ativo_por_volta": round(fp_com / f.voltas, 2),
                "erro_mediano_m": round(float(np.median(deltas)), 1) if deltas else None,
            })
        relatorio["fontes"][nome] = {
            "arquivos": f.arquivos, "voltas": f.voltas, "onsets_reais": f.onsets,
            "queda_lon_acc_ms2": {
                "p25": round(float(np.percentile(q, 25)), 2),
                "mediana": round(float(np.percentile(q, 50)), 2),
                "p75": round(float(np.percentile(q, 75)), 2),
            },
            "origens_corte": dict(f.origens_corte),
            "canais_usados": dict(f.taxas),
            "origens_eixo": dict(f.origens_eixo),
            "descartes": dict(f.descartes),
            "arquivos_usados": sorted(f.nomes),
            "varredura": linhas,
        }
    args.out.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    print("escrito:", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
