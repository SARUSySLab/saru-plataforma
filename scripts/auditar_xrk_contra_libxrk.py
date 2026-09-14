"""Auditoria do leitor Python puro de .xrk/.xrz contra o oraculo `libxrk`.

Contexto: `src/saru_poc/readers/xrk.py` e um parser proprio, Python puro, do
formato AiM RaceStudio 3 (.xrk/.xrz). `libxrk` e a biblioteca nativa (C++
via bindings) que o `saru-app` usa em producao para o mesmo formato.

Decisao do Lucas: `libxrk` entra aqui SO como ferramenta de AUDITORIA, para
comparar o leitor proprio contra uma implementacao de referencia madura.
Ele NAO vira dependencia de runtime do `saru-poc-trackday` por causa deste
script (o extra opcional `aim` no `pyproject.toml` ja existe pra quem
quiser instalar `libxrk` manualmente, mas o leitor de producao continua
Python puro, sem essa dependencia). Este script roda manualmente, fora do
pipeline normal, contra um venv que tenha `libxrk` instalado (o venv do
projeto ja tem, 0.13).

Uso:
    python scripts/auditar_xrk_contra_libxrk.py [--acervo DIR] [--amostra-valores N]
        [--json SAIDA.json] [--limite N]

Sem `libxrk` instalado o script aborta cedo com mensagem clara.
"""

from __future__ import annotations

import argparse
import importlib
import json
import statistics
import sys
import time
import traceback
from pathlib import Path

ACERVO_DEFAULT = Path(
    "/home/lucas-antunes/Desktop/trabalho/clientes/saru/dados_telemetria"
)

# Arquivos escolhidos pra comparacao de VALOR (etapa 4 do enunciado): kart,
# F3, moto, um .xrz, o maior do acervo. Resolvidos por substring de caminho
# pra nao depender de ordem de `find`.
ARQUIVOS_VALOR_HINTS = [
    ("kart", ".xrk"),
    ("f3", ".xrk"),
    ("superbike", ".xrk"),  # moto
    (None, ".xrz"),  # qualquer .xrz, escolhido por tamanho depois
    ("__maior__", None),  # o maior arquivo do acervo, qualquer extensao
]

TOLERANCIA_LAP_MS = 50


def _import_leitor(tentativas: int = 10, espera_s: float = 30.0):
    """Importa `LeitorXrk`. Se outra sessao esta reescrevendo o arquivo,
    espera e tenta de novo antes de desistir (regra do enunciado)."""
    ultimo_erro: Exception | None = None
    for i in range(tentativas):
        try:
            if "saru_poc.readers.xrk" in sys.modules:
                mod = importlib.reload(sys.modules["saru_poc.readers.xrk"])
            else:
                mod = importlib.import_module("saru_poc.readers.xrk")
            return mod.LeitorXrk, mod.ErroDeLeitura
        except Exception as exc:  # noqa: BLE001 - queremos qualquer falha de import
            ultimo_erro = exc
            print(
                f"[import] leitor quebrado (tentativa {i + 1}/{tentativas}): {exc}",
                file=sys.stderr,
            )
            if i < tentativas - 1:
                time.sleep(espera_s)
    raise RuntimeError(
        f"leitor nao importou apos {tentativas} tentativas, ultimo erro: {ultimo_erro}"
    ) from ultimo_erro


def _norm_nome(nome: str) -> str:
    """Normaliza nome de canal pra casar `libxrk` com o nosso: strip, colapsa
    espaco, lowercase. Nao mexe em underscore (canais como `Calculated_Gear`
    ja usam underscore nos dois lados)."""
    return " ".join(nome.strip().lower().split())


def _achar_arquivos(acervo: Path) -> list[Path]:
    arquivos = [
        p
        for p in acervo.rglob("*")
        if p.is_file() and p.suffix.lower() in (".xrk", ".xrz")
    ]
    arquivos.sort()
    return arquivos


def _escolher_arquivos_valor(arquivos: list[Path]) -> list[Path]:
    escolhidos: list[Path] = []
    maior = max(arquivos, key=lambda p: p.stat().st_size)
    for hint, ext in ARQUIVOS_VALOR_HINTS:
        if hint == "__maior__":
            if maior not in escolhidos:
                escolhidos.append(maior)
            continue
        candidatos = [
            p
            for p in arquivos
            if (ext is None or p.suffix.lower() == ext)
            and (hint is None or hint.lower() in str(p).lower())
            and p not in escolhidos
        ]
        if candidatos:
            escolhidos.append(candidatos[0])
    return escolhidos


def _oraculo_laps(log) -> list[tuple[int, int, int]]:
    """(num, start_ms, end_ms) ordenado por num."""
    df = log.laps.to_pandas().sort_values("num")
    return list(
        zip(
            df["num"].tolist(),
            df["start_time"].tolist(),
            df["end_time"].tolist(),
        )
    )


def _nosso_beacons(bruto: dict[str, str]) -> list[int]:
    txt = bruto.get("lap_beacons_ms")
    if not txt:
        return []
    return [int(v) for v in txt.split(",") if v.strip()]


def _comparar_voltas(bruto: dict[str, str], log) -> dict:
    beacons = _nosso_beacons(bruto)
    n_voltas_nosso = max(len(beacons) - 1, 0)
    laps_oraculo = _oraculo_laps(log)
    n_voltas_oraculo = len(laps_oraculo)

    tempos_nosso = [beacons[i + 1] - beacons[i] for i in range(len(beacons) - 1)]
    tempos_oraculo = [end - start for _, start, end in laps_oraculo]

    n_cmp = min(len(tempos_nosso), len(tempos_oraculo))
    diffs = [
        abs(tempos_nosso[i] - tempos_oraculo[i]) for i in range(n_cmp)
    ]
    fora_tolerancia = sum(1 for d in diffs if d > TOLERANCIA_LAP_MS)

    return {
        "n_voltas_nosso": n_voltas_nosso,
        "n_voltas_oraculo": n_voltas_oraculo,
        "contagem_bate": n_voltas_nosso == n_voltas_oraculo,
        "n_tempos_comparados": n_cmp,
        "n_tempos_fora_tolerancia_50ms": fora_tolerancia,
        "maior_divergencia_ms": max(diffs) if diffs else None,
        "diffs_ms": diffs,
    }


def _comparar_metadata(cabecalho, log) -> dict:
    venue_nosso = cabecalho.venue_declarado
    venue_oraculo = log.metadata.get("Venue")
    campos_so_oraculo = sorted(
        k for k in log.metadata if log.metadata.get(k) not in (None, "")
    )
    return {
        "venue_nosso": venue_nosso,
        "venue_oraculo": venue_oraculo,
        "venue_bate": (venue_nosso or "").strip() == (venue_oraculo or "").strip(),
        "campos_metadata_oraculo_com_valor": campos_so_oraculo,
    }


def _comparar_canais(cabecalho, log) -> dict:
    """Casa canais pelo nome normalizado e compara contagem de amostra.

    Canal nosso com n_amostras=0 e undecoded/nao-observado no stream (nao e
    perda, e o proprio leitor ja documenta isso pra canais > 2 bytes/rajada
    nunca vista); esses ficam fora da comparacao de contagem, so entram na
    lista de "so no nosso lado, sem par no oraculo" se tambem nao existirem
    la.
    """
    por_nome_oraculo = {}
    for nome, tabela in log.channels.items():
        por_nome_oraculo[_norm_nome(nome)] = (nome, tabela.num_rows)

    pares = []
    so_nosso_com_amostra = []
    so_nosso_sem_amostra = []
    for canal in cabecalho.canais:
        chave = _norm_nome(canal.nome_bruto)
        if chave in por_nome_oraculo:
            nome_oraculo, n_oraculo = por_nome_oraculo[chave]
            pares.append(
                {
                    "nome": canal.nome_bruto,
                    "nome_oraculo": nome_oraculo,
                    "n_nosso": canal.n_amostras,
                    "n_oraculo": n_oraculo,
                    "diff": n_oraculo - canal.n_amostras,
                }
            )
        elif canal.n_amostras > 0:
            so_nosso_com_amostra.append(canal.nome_bruto)
        else:
            so_nosso_sem_amostra.append(canal.nome_bruto)

    nomes_pareados = {_norm_nome(p["nome"]) for p in pares}
    so_oraculo = [
        nome_orig
        for chave, (nome_orig, _) in por_nome_oraculo.items()
        if chave not in nomes_pareados
    ]

    return {
        "n_canais_nosso": len(cabecalho.canais),
        "n_canais_oraculo": len(log.channels),
        "n_pares_com_amostra_dos_2_lados": sum(
            1 for p in pares if p["n_nosso"] > 0 and p["n_oraculo"] > 0
        ),
        "pares": pares,
        "so_nosso_com_amostra_sem_par": so_nosso_com_amostra,
        "so_nosso_sem_amostra_sem_par": so_nosso_sem_amostra,
        "so_oraculo_sem_par": so_oraculo,
    }


def _auditar_um(caminho: Path, LeitorXrk, ErroDeLeitura) -> dict:
    from libxrk import aim_xrk

    resultado: dict = {"arquivo": str(caminho), "erro": None}

    t0 = time.perf_counter()
    try:
        cabecalho = LeitorXrk().inspecionar(caminho)
    except ErroDeLeitura as exc:
        resultado["erro"] = f"nosso inspecionar() falhou: {exc}"
        return resultado
    t_nosso = time.perf_counter() - t0

    t0 = time.perf_counter()
    try:
        log = aim_xrk(str(caminho))
    except Exception as exc:  # noqa: BLE001
        resultado["erro"] = f"oraculo aim_xrk() falhou: {exc}"
        resultado["t_nosso_s"] = t_nosso
        return resultado
    t_oraculo = time.perf_counter() - t0

    resultado["t_nosso_s"] = t_nosso
    resultado["t_oraculo_s"] = t_oraculo
    resultado["tamanho_bytes"] = caminho.stat().st_size
    resultado["leitura_parcial"] = cabecalho.bruto.get("leitura_parcial") == "sim"
    resultado["bytes_sem_cobertura"] = cabecalho.bruto.get("bytes_sem_cobertura")
    resultado["voltas"] = _comparar_voltas(cabecalho.bruto, log)
    resultado["metadata"] = _comparar_metadata(cabecalho, log)
    resultado["canais"] = _comparar_canais(cabecalho, log)
    return resultado


def _estatisticas_canal(valores) -> dict:
    import numpy as np

    arr = np.asarray(valores, dtype=float)
    arr = arr[~np.isnan(arr)] if arr.size else arr
    if arr.size == 0:
        return {"n": 0}
    return {
        "n": int(arr.size),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "media": float(np.mean(arr)),
        "primeiras_5": [float(v) for v in arr[:5]],
        "ultimas_5": [float(v) for v in arr[-5:]],
    }


def _auditar_valores(caminho: Path, LeitorXrk) -> dict:
    """Etapa 4: decodifica de verdade (ler()) e compara estatistica por canal
    comum contra o oraculo, pra achar divergencia de VALOR (nao so contagem)."""
    from libxrk import aim_xrk

    log = aim_xrk(str(caminho))
    por_nome_oraculo = {_norm_nome(n): (n, t) for n, t in log.channels.items()}

    valores_nosso: dict[str, list[float]] = {}
    for lote in LeitorXrk().ler(caminho):
        tabela = lote.tabela
        for nome_col in tabela.schema.names:
            if nome_col == "t_s":
                continue
            col = tabela.column(nome_col).to_pylist()
            valores_nosso.setdefault(nome_col, []).extend(
                v for v in col if v is not None
            )

    comparacoes = []
    for nome, vals in valores_nosso.items():
        chave = _norm_nome(nome)
        if chave not in por_nome_oraculo or not vals:
            continue
        nome_oraculo, tabela_oraculo = por_nome_oraculo[chave]
        vals_oraculo = tabela_oraculo.column(nome_oraculo).to_pylist()
        est_nosso = _estatisticas_canal(vals)
        est_oraculo = _estatisticas_canal(vals_oraculo)
        divergencia_min_max = None
        if est_nosso.get("n") and est_oraculo.get("n"):
            divergencia_min_max = {
                "diff_min": est_nosso["min"] - est_oraculo["min"],
                "diff_max": est_nosso["max"] - est_oraculo["max"],
                "diff_media": est_nosso["media"] - est_oraculo["media"],
            }
        comparacoes.append(
            {
                "canal": nome,
                "canal_oraculo": nome_oraculo,
                "nosso": est_nosso,
                "oraculo": est_oraculo,
                "divergencia": divergencia_min_max,
            }
        )
    return {"arquivo": str(caminho), "canais_comparados": comparacoes}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--acervo", type=Path, default=ACERVO_DEFAULT)
    ap.add_argument("--limite", type=int, default=None, help="limita N arquivos (debug)")
    ap.add_argument("--json", type=Path, default=None, help="grava resultado bruto em JSON")
    args = ap.parse_args()

    try:
        import libxrk  # noqa: F401
    except ImportError:
        print(
            "ERRO: libxrk nao esta instalado neste interpretador. "
            "Este script e so de auditoria, ative o venv que tem libxrk 0.13.",
            file=sys.stderr,
        )
        return 2

    LeitorXrk, ErroDeLeitura = _import_leitor()

    arquivos = _achar_arquivos(args.acervo)
    if args.limite:
        arquivos = arquivos[: args.limite]
    print(f"{len(arquivos)} arquivos .xrk/.xrz encontrados em {args.acervo}")

    resultados = []
    t_total_nosso = 0.0
    t_total_oraculo = 0.0
    for i, caminho in enumerate(arquivos, 1):
        print(f"[{i}/{len(arquivos)}] {caminho.name}", file=sys.stderr)
        try:
            r = _auditar_um(caminho, LeitorXrk, ErroDeLeitura)
        except Exception as exc:  # noqa: BLE001
            r = {
                "arquivo": str(caminho),
                "erro": f"excecao nao tratada: {exc}",
                "traceback": traceback.format_exc(),
            }
        resultados.append(r)
        t_total_nosso += r.get("t_nosso_s", 0.0) or 0.0
        t_total_oraculo += r.get("t_oraculo_s", 0.0) or 0.0

    arquivos_ok = [r for r in resultados if not r.get("erro")]
    arquivos_valor = _escolher_arquivos_valor(arquivos)
    print(
        f"\nComparando VALOR (etapa 4) em {len(arquivos_valor)} arquivos: "
        + ", ".join(p.name for p in arquivos_valor),
        file=sys.stderr,
    )
    resultados_valor = []
    for caminho in arquivos_valor:
        try:
            resultados_valor.append(_auditar_valores(caminho, LeitorXrk))
        except Exception as exc:  # noqa: BLE001
            resultados_valor.append(
                {"arquivo": str(caminho), "erro": str(exc), "traceback": traceback.format_exc()}
            )

    saida = {
        "n_arquivos": len(arquivos),
        "n_ok": len(arquivos_ok),
        "n_erro": len(resultados) - len(arquivos_ok),
        "t_total_nosso_s": t_total_nosso,
        "t_total_oraculo_s": t_total_oraculo,
        "resultados": resultados,
        "resultados_valor": resultados_valor,
    }

    if args.json:
        args.json.write_text(json.dumps(saida, indent=2, ensure_ascii=False))
        print(f"JSON bruto gravado em {args.json}")

    # Resumo curto no stdout (o relatorio detalhado e produzido a parte a
    # partir do JSON).
    print(json.dumps({k: v for k, v in saida.items() if k not in ("resultados", "resultados_valor")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
