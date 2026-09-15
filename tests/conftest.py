"""Checagem da suite inteira: teste pulado por falta de PostgreSQL nao e teste verde.

Com `SARU_EXIGIR_BANCO=1` (padrao do `make test`), qualquer teste pulado com
motivo "postgres" reprova a sessao. Sem isso, `pytest` com o banco fora do ar
sai verde e esconde falha real: foi o que aconteceu no PR #35 em 2026-09-14,
quando `test_freio_ficou_em_pressao_nao_em_fracao` so falhava com o banco de pe.
"""

from __future__ import annotations

import os

import pytest

_SKIPS_DE_BANCO: list[str] = []


def _exigir_banco() -> bool:
    return os.environ.get("SARU_EXIGIR_BANCO") == "1"


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if not report.skipped or not isinstance(report.longrepr, tuple):
        return
    if "postgres" in str(report.longrepr[2]).lower():
        _SKIPS_DE_BANCO.append(report.nodeid)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if _exigir_banco() and _SKIPS_DE_BANCO and exitstatus == pytest.ExitCode.OK:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


def pytest_terminal_summary(terminalreporter, exitstatus, config) -> None:
    if _exigir_banco() and _SKIPS_DE_BANCO:
        terminalreporter.section("banco exigido")
        terminalreporter.write_line(
            f"{len(_SKIPS_DE_BANCO)} teste(s) pulado(s) por falta de PostgreSQL "
            "com SARU_EXIGIR_BANCO=1: rode `make up` e repita."
        )
