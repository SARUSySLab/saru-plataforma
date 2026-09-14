"""Escrita da amostra em Parquet, pelo caminho de streaming."""

from __future__ import annotations

import pyarrow as pa
import pytest

from saru_poc import storage
from saru_poc.readers.base import Lote


def _lote(hz: float, t0: float, n: int, canais: tuple[str, ...] = ("SPEED",)) -> Lote:
    cols = {"t_s": pa.array([t0 + i / hz for i in range(n)], pa.float64())}
    for c in canais:
        cols[c] = pa.array([float(i) for i in range(n)], pa.float64())
    return Lote(hz, pa.RecordBatch.from_pydict(cols))


@pytest.fixture
def escrever(tmp_path):
    """Escreve sempre numa raiz temporaria, nunca no data/ do repo."""

    def _escrever(gravacao_id, lotes, **kw):
        return storage.escrever_serie(gravacao_id, lotes, raiz=tmp_path, **kw)

    return _escrever


def test_lote_sem_eixo_de_tempo_e_recusado() -> None:
    with pytest.raises(ValueError, match="sem coluna t_s"):
        Lote(10.0, pa.RecordBatch.from_pydict({"SPEED": pa.array([1.0])}))


def test_uma_serie_por_taxa_nativa(escrever) -> None:
    """O plano fecha: uma serie por taxa, sem reamostrar."""
    ponteiros = escrever(
        "grav-1", [_lote(10.0, 0, 100), _lote(50.0, 0, 500), _lote(10.0, 10, 100)]
    )
    por_taxa = {p.frequencia_hz: p for p in ponteiros}
    assert set(por_taxa) == {10.0, 50.0}
    assert por_taxa[10.0].linhas == 200
    assert por_taxa[50.0].linhas == 500
    assert por_taxa[10.0].t_inicio_s == 0.0
    assert por_taxa[10.0].t_fim_s > 10.0


def test_reprocessar_e_idempotente_e_nao_sobrescreve(escrever) -> None:
    a = escrever("grav-2", [_lote(10.0, 0, 50)])[0]
    b = escrever("grav-2", [_lote(10.0, 0, 50)])[0]
    assert a.sha256 == b.sha256
    assert a.uri == b.uri
    assert storage.caminho_de(a).exists()


def test_conteudo_diferente_nasce_como_outro_objeto(escrever) -> None:
    a = escrever("grav-3", [_lote(10.0, 0, 50)])[0]
    b = escrever("grav-3", [_lote(10.0, 0, 51)])[0]
    assert a.sha256 != b.sha256
    assert a.uri != b.uri
    # O antigo continua no disco: objeto e imutavel.
    assert storage.caminho_de(a).exists()
    assert storage.caminho_de(b).exists()


def test_canal_que_some_no_meio_da_serie_falha_alto(escrever) -> None:
    with pytest.raises(ValueError, match="mudou de esquema"):
        escrever(
            "grav-4",
            [_lote(10.0, 0, 10, ("SPEED", "RPM")), _lote(10.0, 1, 10, ("SPEED",))],
        )


def test_serie_rotulada_convive_com_a_principal_na_mesma_taxa(escrever) -> None:
    """Caso GPS do .xrk: fluxo paralelo com relogio e colunas proprios na
    MESMA taxa do grupo principal. O rotulo `serie` separa os escritores (sem
    ele, o segundo lote quebrava por esquema); cada ponteiro declara as
    colunas do seu objeto, que e o que a ingestao usa pra ligar canal a serie
    por NOME e nao so por taxa."""
    lote_gps = Lote(
        10.0,
        pa.RecordBatch.from_pydict(
            {
                "t_s": pa.array([0.0, 0.1], pa.float64()),
                "GPS Latitude": pa.array([-15.8, -15.8], pa.float64()),
            }
        ),
        serie="gps",
    )
    ponteiros = escrever("grav-8", [_lote(10.0, 0, 10, ("SPEED",)), lote_gps])
    assert len(ponteiros) == 2
    por_serie = {p.serie: p for p in ponteiros}
    assert por_serie[""].colunas == ("SPEED",)
    assert por_serie["gps"].colunas == ("GPS Latitude",)
    assert por_serie[""].uri != por_serie["gps"].uri
    # A falha alta continua valendo DENTRO de cada rotulo.
    with pytest.raises(ValueError, match="mudou de esquema"):
        escrever("grav-9", [lote_gps, Lote(10.0, _lote(10.0, 0, 2).tabela, serie="gps")])


def test_serie_canonica_exige_versao_do_mapa(escrever) -> None:
    with pytest.raises(ValueError, match="exige mapa_versao"):
        escrever("grav-5", [_lote(10.0, 0, 10)], camada="canonica")


def test_serie_bruta_recusa_versao_de_mapa(escrever) -> None:
    with pytest.raises(ValueError, match="nao tem mapa"):
        escrever(
            "grav-6", [_lote(10.0, 0, 10)], camada="bruta", mapa_versao="2026.08-1"
        )


def test_duckdb_le_o_que_foi_escrito(escrever) -> None:
    import duckdb

    p = escrever("grav-7", [_lote(20.0, 0, 200)])[0]
    caminho = storage.caminho_de(p)
    n, tmax = duckdb.sql(
        f"select count(*), max(t_s) from read_parquet('{caminho}')"
    ).fetchone()
    assert n == 200
    assert tmax == pytest.approx(p.t_fim_s)
