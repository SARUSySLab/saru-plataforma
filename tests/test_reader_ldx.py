"""Testes do leitor de sidecar MoTeC .ldx (formato_id motec_ldx)."""

from __future__ import annotations

from pathlib import Path

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers.base import ErroDeLeitura
from saru_poc.readers.ldx import LeitorLdx

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def leitor() -> LeitorLdx:
    return LeitorLdx()


def _todos_do_acervo() -> list[Path]:
    if not CONFIG.acervo_root.exists():
        return []
    return sorted(CONFIG.acervo_root.rglob("*.ldx"))


# ---------------------------------------------------------------------------
# Fixtures sinteticas
# ---------------------------------------------------------------------------


def test_nao_tem_canal(leitor: LeitorLdx) -> None:
    """O .ldx e sidecar puro: canais sempre vazio."""
    cab = leitor.inspecionar(FIXTURES / "ldx_completo.ldx")
    assert cab.formato_id == "motec_ldx"
    assert cab.canais == ()


def test_caminho_feliz_extrai_details_e_beacons(leitor: LeitorLdx) -> None:
    cab = leitor.inspecionar(FIXTURES / "ldx_completo.ldx")
    assert cab.bruto["total_laps"] == "6"
    assert cab.bruto["fastest_lap"] == "1"
    assert cab.bruto["fastest_time_raw"] == "1:15.187"
    assert cab.bruto["beacons_n"] == "3"
    assert "details_ausente" not in cab.bruto
    assert "beacons_ausente" not in cab.bruto


def test_duracao_vem_do_ultimo_beacon_em_microssegundos(leitor: LeitorLdx) -> None:
    """Time do Marker esta em microssegundos desde o inicio do log.

    Confirmado por aritmetica no acervo real: a diferenca entre dois
    beacons bate com o Fastest Time declarado. Nesta fixture o ultimo
    marcador e 3.14773e+08 us = 314.773 s.
    """
    cab = leitor.inspecionar(FIXTURES / "ldx_completo.ldx")
    assert cab.duracao_s == pytest.approx(314.773)


def test_sem_bloco_details_nao_quebra(leitor: LeitorLdx) -> None:
    cab = leitor.inspecionar(FIXTURES / "ldx_sem_details.ldx")
    assert cab.bruto["details_ausente"] == "true"
    assert "total_laps" not in cab.bruto
    assert "fastest_time_raw" not in cab.bruto
    # ainda tem beacon, entao duracao sai deles
    assert cab.duracao_s is not None


def test_sem_marcador_declara_ausencia_sem_excecao(leitor: LeitorLdx) -> None:
    cab = leitor.inspecionar(FIXTURES / "ldx_sem_marcador.ldx")
    assert cab.bruto["beacons_ausente"] == "true"
    assert cab.bruto["beacons_n"] == "0"
    # tem Details com Fastest Time zerado: nao inventa duracao positiva
    assert cab.bruto["fastest_time_raw"] == "0:00.000"
    assert cab.bruto.get("fastest_time_zerado") == "true"
    assert cab.duracao_s is None


def test_xml_malformado_levanta_erro(tmp_path, leitor: LeitorLdx) -> None:
    ruim = tmp_path / "quebrado.ldx"
    ruim.write_text("<LDXFile><Layers>", encoding="utf-8")
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(ruim)


def test_raiz_errada_levanta_erro(tmp_path, leitor: LeitorLdx) -> None:
    ruim = tmp_path / "nao_e_ldx.ldx"
    ruim.write_text('<?xml version="1.0"?><OutraCoisa/>', encoding="utf-8")
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(ruim)


def test_arquivo_inexistente_levanta_erro(tmp_path, leitor: LeitorLdx) -> None:
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(tmp_path / "nao_existe.ldx")


# ---------------------------------------------------------------------------
# Acervo real
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
@pytest.mark.parametrize("caminho", _todos_do_acervo(), ids=lambda p: p.name)
def test_le_arquivo_real_do_acervo(caminho: Path, leitor: LeitorLdx) -> None:
    cab = leitor.inspecionar(caminho)
    assert cab.formato_id == "motec_ldx"
    assert cab.canais == ()
    assert cab.venue_declarado is None


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
def test_degradacoes_reais_sao_declaradas_nao_excecao(leitor: LeitorLdx) -> None:
    """Confere que as degradacoes medidas no acervo (2026-08-29) nao quebram.

    Sem Details em pelo menos 1 arquivo, sem beacon em pelo menos 1, e o
    Fastest Time zerado aparece em pelo menos 1.
    """
    sem_details = 0
    sem_beacon = 0
    zerado = 0
    for caminho in _todos_do_acervo():
        cab = leitor.inspecionar(caminho)
        if cab.bruto.get("details_ausente") == "true":
            sem_details += 1
        if cab.bruto.get("beacons_ausente") == "true":
            sem_beacon += 1
        if cab.bruto.get("fastest_time_zerado") == "true":
            zerado += 1
    assert sem_details >= 1
    assert sem_beacon >= 1
    assert zerado >= 1
