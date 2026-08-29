"""Configuracao do ambiente. Uma fonte so, lida do .env."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")


def _path(var: str, default: str) -> Path:
    raw = os.getenv(var, default)
    p = Path(raw).expanduser()
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


@dataclass(frozen=True)
class Config:
    pg_host: str = os.getenv("SARU_PG_HOST", "127.0.0.1")
    pg_port: int = int(os.getenv("SARU_PG_PORT", "5442"))
    pg_db: str = os.getenv("SARU_PG_DB", "saru_poc")
    pg_user: str = os.getenv("SARU_PG_USER", "saru")
    pg_password: str = os.getenv("SARU_PG_PASSWORD", "saru")

    # Amostra nunca entra no Postgres: vai pra Parquet aqui, particionado por
    # gravacao e taxa nativa. serie_amostral guarda so o ponteiro.
    data_root: Path = field(default_factory=lambda: _path("SARU_DATA_ROOT", "./data"))
    acervo_root: Path = field(
        default_factory=lambda: _path("SARU_ACERVO_ROOT", "../dados_telemetria")
    )
    # Snapshot do saru-app, so leitura. A PoC nao escreve nada la.
    app_ref: Path = field(
        default_factory=lambda: _path("SARU_APP_REF", "../tudo_junto/saru-app")
    )

    @property
    def dsn(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_db}"
        )

    @property
    def parquet_root(self) -> Path:
        return self.data_root / "parquet"


CONFIG = Config()
