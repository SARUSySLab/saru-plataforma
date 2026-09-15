"""A checagem de `tests/conftest.py` roda numa suite de brinquedo, em processo
separado, para nao depender do banco nem contaminar a sessao atual."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_CONFTEST = Path(__file__).with_name("conftest.py").read_text()
_SUITE = """
import pytest

@pytest.fixture
def banco():
    pytest.skip("postgres indisponivel: conexao recusada")

def test_usa_banco(banco):
    pass

def test_sem_banco():
    pass
"""


def _rodar(tmp_path: Path, exigir: bool) -> subprocess.CompletedProcess[str]:
    (tmp_path / "conftest.py").write_text(_CONFTEST)
    (tmp_path / "test_brinquedo.py").write_text(_SUITE)
    env = {k: v for k, v in os.environ.items() if k != "SARU_EXIGIR_BANCO"}
    if exigir:
        env["SARU_EXIGIR_BANCO"] = "1"
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--rootdir",
            str(tmp_path),
            str(tmp_path),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_skip_de_banco_reprova_quando_exigido(tmp_path: Path) -> None:
    r = _rodar(tmp_path, exigir=True)
    assert r.returncode == pytest.ExitCode.TESTS_FAILED, r.stdout
    assert "pulado(s) por falta de PostgreSQL" in r.stdout


def test_skip_de_banco_passa_quando_nao_exigido(tmp_path: Path) -> None:
    r = _rodar(tmp_path, exigir=False)
    assert r.returncode == pytest.ExitCode.OK, r.stdout
