"""Testes unitários dos decodificadores unificados Cosworth Pi (.pid e .pds)."""

from __future__ import annotations

import io
import struct
import tracemalloc
from pathlib import Path

import numpy as np
import pytest

from telemetria.leitores.cosworth_pi import (
    CosworthPdsReader,
    CosworthPidReader,
    TransformacaoLinear,
    parse_cosworth_metadata,
)
from saru_poc.readers.base import Cabecalho, ErroDeLeitura, Lote

FIXTURE_PID = Path("tests/fixtures/pi_pid_sintetico.pid")
FIXTURE_PDS = Path("tests/fixtures/pi_pds_sintetico.pds")
FIXTURE_PDS_992 = Path("tests/fixtures/pi_pds_sintetico_992.pds")


# ---------------------------------------------------------------------------
# Transformacao Linear y = m * x + c
# ---------------------------------------------------------------------------


def test_transformacao_linear_identidade() -> None:
    t = TransformacaoLinear()
    assert t.m == 1.0
    assert t.c == 0.0
    assert t.aplicar(10.0) == 10.0
    assert np.allclose(t.aplicar(np.array([0.0, 5.0, 10.0])), np.array([0.0, 5.0, 10.0]))


def test_transformacao_linear_conversao_adc() -> None:
    # Exemplo da especificacao: X_raw = 1840, m = 0.125, c = 0.0 -> Y_phys = 230.0 km/h
    t = TransformacaoLinear(m=0.125, c=0.0)
    resultado = t.aplicar(1840.0)
    assert abs(resultado - 230.0) < 1e-5

    # Exemplo com offset (pressao de freio: m=0.199645, c=-41.33)
    t_freio = TransformacaoLinear(m=0.199645, c=-41.33)
    res_freio = t_freio.aplicar(300.0)
    esperado = 0.199645 * 300.0 - 41.33
    assert abs(res_freio - esperado) < 1e-5


# ---------------------------------------------------------------------------
# Metadata parser
# ---------------------------------------------------------------------------


def test_parse_cosworth_metadata_pid() -> None:
    meta = parse_cosworth_metadata(FIXTURE_PID)
    assert meta["formato"] == "pi_pid"
    assert meta["n_blocos"] == 2
    assert meta["tamanho_bloco"] == 340


def test_parse_cosworth_metadata_pds() -> None:
    meta = parse_cosworth_metadata(FIXTURE_PDS)
    assert meta["formato"] == "pi_pds"
    assert meta["offset_magic"] == 4


def test_parse_cosworth_metadata_stream_bytes() -> None:
    conteudo = FIXTURE_PID.read_bytes()
    meta = parse_cosworth_metadata(conteudo)
    assert meta["formato"] == "pi_pid"

    stream = io.BytesIO(conteudo)
    meta2 = parse_cosworth_metadata(stream)
    assert meta2["formato"] == "pi_pid"
    assert stream.tell() == 0  # stream restaurado


def test_parse_cosworth_metadata_invalido() -> None:
    meta = parse_cosworth_metadata(b"12345678NAO_E_COSWORTH")
    assert meta["formato"] == "desconhecido"


# ---------------------------------------------------------------------------
# CosworthPidReader
# ---------------------------------------------------------------------------


def test_cosworth_pid_reader_inspecionar() -> None:
    reader = CosworthPidReader()
    cab = reader.inspecionar(FIXTURE_PID)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "pi_pid"
    assert len(cab.canais) == 3
    assert cab.duracao_s == 2.0
    assert cab.venue_declarado == "Interlagos"
    assert cab.taxas == (20.0, 50.0, 100.0)


def test_cosworth_pid_reader_ler_e_lotes() -> None:
    reader = CosworthPidReader()
    lotes = list(reader.ler(FIXTURE_PID))

    assert len(lotes) == 3  # 20 Hz, 50 Hz, 100 Hz
    taxas = {l.frequencia_hz for l in lotes}
    assert taxas == {20.0, 50.0, 100.0}

    for lote in lotes:
        assert isinstance(lote, Lote)
        assert "t_s" in lote.tabela.schema.names
        assert lote.tabela.num_rows > 0


def test_cosworth_pid_reader_com_calibracao_linear() -> None:
    # Aplica calibracao explicita no canal Speed
    calibracao_speed = TransformacaoLinear(m=0.5, c=1.0)
    reader = CosworthPidReader(calibracoes={"Speed": calibracao_speed})

    lotes = list(reader.ler(FIXTURE_PID))
    lote_50hz = next(l for l in lotes if l.frequencia_hz == 50.0)
    assert "Speed" in lote_50hz.tabela.schema.names
    valores = lote_50hz.tabela["Speed"].to_numpy()
    assert len(valores) == 100


# ---------------------------------------------------------------------------
# CosworthPdsReader
# ---------------------------------------------------------------------------


def test_cosworth_pds_reader_inspecionar_f3() -> None:
    reader = CosworthPdsReader()
    cab = reader.inspecionar(FIXTURE_PDS)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "pi_pds"
    assert len(cab.canais) == 10
    assert cab.duracao_s == 2.0
    assert cab.taxas == (1.0, 5.0, 10.0, 20.0, 25.0, 50.0, 100.0)


def test_cosworth_pds_reader_inspecionar_992() -> None:
    reader = CosworthPdsReader()
    cab = reader.inspecionar(FIXTURE_PDS_992)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "pi_pds"
    assert len(cab.canais) == 10
    assert cab.duracao_s == 2.0


def test_cosworth_pds_reader_ler_streaming() -> None:
    reader = CosworthPdsReader()
    lotes = list(reader.ler(FIXTURE_PDS))

    assert len(lotes) == 7
    taxas = {l.frequencia_hz for l in lotes}
    assert taxas == {1.0, 5.0, 10.0, 20.0, 25.0, 50.0, 100.0}

    for lote in lotes:
        assert "t_s" in lote.tabela.schema.names
        assert lote.tabela.num_rows > 0


def test_cosworth_pds_reader_ler_streaming_992() -> None:
    reader = CosworthPdsReader()
    lotes = list(reader.ler(FIXTURE_PDS_992))

    assert len(lotes) == 7
    for lote in lotes:
        assert "t_s" in lote.tabela.schema.names
        assert lote.tabela.num_rows > 0


def test_cosworth_pds_reader_com_calibracao_linear() -> None:
    calibracao_steering = TransformacaoLinear(m=2.0, c=-5.0)
    reader = CosworthPdsReader(calibracoes={"Steering": calibracao_steering})

    lotes = list(reader.ler(FIXTURE_PDS))
    lote_100hz = next(l for l in lotes if l.frequencia_hz == 100.0)
    assert "Steering" in lote_100hz.tabela.schema.names


def test_cosworth_pds_reader_consumo_memoria_streaming() -> None:
    """Verifica se o streaming em blocos nao estoura a memoria."""
    tracemalloc.start()
    reader = CosworthPdsReader()
    lotes = list(reader.ler(FIXTURE_PDS_992))
    _pico_atual, pico_max = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # O pico de memoria em bytes deve ser muito inferior a 90 MB (< 20 MB para fixture)
    assert pico_max < 20 * 1024 * 1024
    assert len(lotes) == 7
