"""Runner de migrations. SQL puro versionado, aplicado em ordem de nome.

Regras:
  - cada arquivo roda uma vez, dentro de uma transacao;
  - o sha256 do arquivo fica gravado: editar migration ja aplicada e erro,
    nao silencio;
  - reaplicar e no-op.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .config import REPO_ROOT
from .db import connect

MIGRATIONS_DIR = REPO_ROOT / "migrations"


def _pendentes(conn) -> list[Path]:
    arquivos = sorted(MIGRATIONS_DIR.glob("*.sql"))
    conn.execute(Path(MIGRATIONS_DIR / "000_bookkeeping.sql").read_text())
    aplicadas = {
        v: s
        for v, s in conn.execute("select versao, sha256 from _migrations").fetchall()
    }
    pendentes = []
    for f in arquivos:
        sha = hashlib.sha256(f.read_bytes()).hexdigest()
        anterior = aplicadas.get(f.stem)
        if anterior is None:
            pendentes.append(f)
        elif anterior != sha:
            raise SystemExit(
                f"migration ja aplicada foi editada: {f.name}\n"
                f"  gravado {anterior}\n  agora   {sha}\n"
                "Escreva uma migration nova em vez de mexer nesta."
            )
    return pendentes


def run() -> int:
    with connect() as conn:
        pendentes = _pendentes(conn)
        conn.commit()
        for f in pendentes:
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            with conn.transaction():
                conn.execute(f.read_text())
                conn.execute(
                    "insert into _migrations (versao, sha256) values (%s, %s)"
                    " on conflict (versao) do nothing",
                    (f.stem, sha),
                )
            print(f"  aplicada {f.name}")
    if not pendentes:
        print("  nada pendente")
    return len(pendentes)


def aplicadas() -> list[tuple[str, str]]:
    with connect(autocommit=True) as conn:
        return conn.execute(
            "select versao, to_char(aplicada_em, 'YYYY-MM-DD HH24:MI') from _migrations"
            " order by versao"
        ).fetchall()
