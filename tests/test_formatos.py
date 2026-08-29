"""Deteccao de formato, contra arquivo real do acervo.

Teste que roda contra fixture sintetica nao prova nada aqui: a regra do
projeto e que formato so existe com assinatura medida. Quando o acervo nao
esta montado, o teste pula em vez de passar em falso.
"""

from __future__ import annotations

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers import FORMATOS, detectar, registrar

pytestmark = pytest.mark.skipif(
    not CONFIG.acervo_root.exists(), reason="acervo nao montado nesta maquina"
)


def _um(padrao: str):
    for f in sorted(CONFIG.acervo_root.rglob(padrao)):
        if ".git" not in f.parts:
            return f
    pytest.skip(f"sem {padrao} no acervo")


@pytest.mark.parametrize(
    ("padrao", "esperado"),
    [
        ("*.xrk", "aim_xrk"),
        ("*.gpk", "aim_gpk"),
        ("*.rrk", "aim_rrk"),
        ("*.ld", "motec_ld"),
        ("*.ldx", "motec_ldx"),
        ("*.vbo", "vbox_vbo"),
        ("*.mf4", "asam_mf4"),
        ("*.pid", "pi_pid"),
        ("*.bmsbin", "bosch_bmsbin"),
        ("*.dlf", "protune_dlf"),
    ],
)
def test_detecta_formato_real(padrao: str, esperado: str) -> None:
    d = detectar(_um(padrao))
    assert d.resolvido, d.motivo
    assert d.formato is not None
    assert d.formato.id == esperado


def test_lic_nao_e_confundido_com_ldx() -> None:
    """`<?xml version="1.0"?>` casa com qualquer XML.

    Sem o marcador `<LDXFile`, os 4 arquivos de licenca .lic do acervo eram
    classificados como sidecar de voltas do MoTeC. Regressao real, corrigida
    em 29/08.
    """
    lic = _um("*.lic")
    d = detectar(lic)
    assert not d.resolvido or (d.formato is not None and d.formato.id != "motec_ldx")


def test_bak_do_bundle_aim_nao_conta_como_divergencia() -> None:
    """O `.bak` do bundle AiM e o mesmo container do `.drk`, por isso e alias."""
    bak = _um("*.bak")
    d = detectar(bak)
    if d.formato is None:
        pytest.skip("o .bak deste acervo nao e do bundle AiM")
    aceitas = (d.formato.extensao_tipica, *d.formato.aliases_ext)
    assert ".bak" in aceitas


def test_desconhecido_nao_vira_default() -> None:
    """Nao reconhecer devolve nada, nunca o formato mais provavel.

    E o fix estrutural do B2: o buraco la era devolver o default do cliente
    quando o arquivo nao declarava venue.
    """
    from pathlib import Path

    alvo = Path("/etc/hostname")
    if not alvo.exists():
        pytest.skip("sem arquivo neutro pra testar")
    d = detectar(alvo)
    assert not d.resolvido
    assert d.motivo


def test_registrar_recusa_formato_fora_do_catalogo() -> None:
    class Falso:
        formato_id = "inventado_pelo_dev"
        versao = "0"

        def inspecionar(self, caminho):
            raise NotImplementedError

        def ler(self, caminho):
            raise NotImplementedError

    with pytest.raises(ValueError, match="nao consta no catalogo"):
        registrar(Falso())


def test_todo_formato_tem_amostra_medida() -> None:
    """Regra D5 da ADR-0044: leitor sem amostra e evidencia fabricada."""
    sem_amostra = [f.id for f in FORMATOS if f.amostras_medidas < 1]
    assert not sem_amostra, f"formato sem amostra medida: {sem_amostra}"


def test_catalogo_nao_declara_leitor_que_nao_existe() -> None:
    """Regressao de 29/08: o catalogo afirmava leitor nativo pra 3 formatos AiM.

    `formatos.py` escrevia `leitor="nativo"` e `leitor_ref="readers.aim_drk"` a
    mao, e o seed propagava isso pro banco. Os modulos nunca existiram. Era
    suporte fabricado dentro do repo que existe pra matar suporte fabricado.

    O campo saiu do catalogo e passou a ser derivado do registro. Este teste
    garante que ninguem o traga de volta.
    """
    from dataclasses import fields

    from saru_poc.readers import FORMATOS
    from saru_poc.readers.formatos import Formato

    escritos = {f.name for f in fields(Formato)}
    assert "leitor" not in escritos
    assert "leitor_ref" not in escritos
    assert FORMATOS


def test_banco_so_afirma_leitor_que_esta_no_registro() -> None:
    """O que o banco diz sobre suporte tem que bater com o codigo."""
    import pytest

    from saru_poc.readers import LEITORES

    try:
        from saru_poc.db import connect

        with connect(autocommit=True) as c:
            no_banco = {
                r[0]
                for r in c.execute(
                    "select id from formato_telemetria where leitor <> 'ausente'"
                )
            }
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")
    assert no_banco == set(LEITORES), (
        "o banco afirma leitor pra formato sem modulo registrado, ou o "
        "contrario. Rode `saru-poc seed` depois de registrar leitor novo."
    )
