"""Conexao com o Postgres do catalogo."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg

from .config import CONFIG


@contextmanager
def connect(autocommit: bool = False) -> Iterator[psycopg.Connection]:
    with psycopg.connect(CONFIG.dsn, autocommit=autocommit) as conn:
        yield conn


def ping() -> str:
    """Versao do servidor, ou levanta. Usado pelo doctor."""
    with connect(autocommit=True) as conn:
        return conn.execute("select version()").fetchone()[0]
