"""CLI da PoC. Por enquanto: migrate e doctor."""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from .config import CONFIG, REPO_ROOT

OK, FALHA, AVISO = "  ok  ", " falha", " aviso"

# Extensoes que o acervo carrega, agrupadas pelo perfil que vai le-las.
# Fonte: Manual de Campo da Telemetria (28/08) + os 21 perfis do aliases.yaml.
FAMILIAS = {
    ".dlf": "Pro Tune TDL (rotulado 'aim' no saru-app, ver ADR-0044)",
    ".xrk": "AiM RaceStudio 3",
    ".drk": "AiM RS2 (indice)",
    ".gpk": "AiM RS2 (GPS)",
    ".rrk": "AiM RS2 (run)",
    ".ld": "MoTeC i2",
    ".ldx": "MoTeC (sidecar de voltas)",
    ".vbo": "VBOX",
    ".dat": "Pi / Cosworth",
    ".pid": "Pi / Cosworth",
    ".csv": "CSV generico (FuelTech, ProTune, TrackAddict, WinDarab, WinTAX)",
    ".mf4": "ASAM MDF4",
    ".bmsbin": "Bosch WinDarab (binario)",
}


def _linha(estado: str, texto: str) -> None:
    print(f"[{estado}] {texto}")


def doctor() -> int:
    falhas = 0
    print("\n== ambiente ==")

    env = REPO_ROOT / ".env"
    if env.exists():
        _linha(OK, f".env presente ({env})")
    else:
        _linha(FALHA, ".env ausente. Rode: cp .env.example .env")
        falhas += 1

    try:
        from .db import ping

        versao = ping().split(",")[0]
        _linha(OK, f"postgres em {CONFIG.pg_host}:{CONFIG.pg_port} -> {versao}")
    except Exception as e:  # noqa: BLE001
        _linha(FALHA, f"postgres inacessivel em {CONFIG.pg_host}:{CONFIG.pg_port}: {e}")
        falhas += 1
    else:
        from .migrate import aplicadas

        aps = aplicadas()
        _linha(OK, f"migrations aplicadas: {len(aps)}")
        for versao, quando in aps:
            print(f"         {versao}  {quando}")

    try:
        CONFIG.parquet_root.mkdir(parents=True, exist_ok=True)
        sonda = CONFIG.parquet_root / ".sonda"
        sonda.write_text("x")
        sonda.unlink()
        _linha(OK, f"parquet root gravavel ({CONFIG.parquet_root})")
    except Exception as e:  # noqa: BLE001
        _linha(FALHA, f"parquet root nao gravavel: {e}")
        falhas += 1

    for lib in ("pyarrow", "duckdb", "numpy", "pandas"):
        try:
            mod = __import__(lib)
            _linha(OK, f"{lib} {getattr(mod, '__version__', '?')}")
        except ImportError:
            _linha(FALHA, f"{lib} ausente")
            falhas += 1
    try:
        import libxrk  # noqa: F401

        _linha(OK, "libxrk presente (leitor nativo AiM .xrk)")
    except ImportError:
        _linha(AVISO, "libxrk ausente. Opcional: uv sync --extra aim")

    print("\n== referencias ==")
    if CONFIG.app_ref.exists():
        _linha(OK, f"snapshot saru-app (so leitura): {CONFIG.app_ref}")
    else:
        _linha(AVISO, f"snapshot saru-app nao encontrado: {CONFIG.app_ref}")

    print("\n== acervo ==")
    if not CONFIG.acervo_root.exists():
        _linha(FALHA, f"acervo nao encontrado: {CONFIG.acervo_root}")
        return falhas + 1

    contagem: Counter[str] = Counter()
    bytes_por_ext: Counter[str] = Counter()
    for f in CONFIG.acervo_root.rglob("*"):
        if not f.is_file() or ".git" in f.parts:
            continue
        ext = f.suffix.lower()
        if ext in FAMILIAS:
            contagem[ext] += 1
            bytes_por_ext[ext] += f.stat().st_size
    _linha(OK, f"acervo em {CONFIG.acervo_root}")
    largura = max((len(FAMILIAS[e]) for e in contagem), default=0)
    for ext, n in contagem.most_common():
        mb = bytes_por_ext[ext] / 1e6
        print(
            f"         {ext:<6} {n:>5} arquivos  {mb:>9.1f} MB  {FAMILIAS[ext]:<{largura}}"
        )
    if not contagem:
        _linha(AVISO, "nenhum arquivo de telemetria reconhecido no acervo")

    print()
    if falhas:
        _linha(FALHA, f"{falhas} problema(s). Ambiente NAO esta pronto.")
    else:
        _linha(OK, "ambiente pronto.")
    return falhas


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="saru-poc", description="PoC core SARU - track day"
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("migrate", help="aplica as migrations pendentes")
    sub.add_parser("doctor", help="confere o ambiente e inventaria o acervo")
    args = p.parse_args(argv)

    if args.cmd == "migrate":
        from .migrate import run

        print("\n== migrations ==")
        run()
        return 0
    if args.cmd == "doctor":
        return 1 if doctor() else 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
