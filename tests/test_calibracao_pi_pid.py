"""Calibracao de zero por sessao de `Acc Long`/`Acc Lat` do `.pid` (issue #36).

`_maior_trecho_parado` e testado isolado (sem Postgres, sem Parquet). O
restante — `calibrar_offsets_pi_pid` grava em `calibracao_canal_gravado`,
`pipeline.ingestao._escrever_canais` so aceita o canonico calibrado, e
`pipeline.leitura.fator_do_canal` soma o offset por gravacao ao offset do
perfil — precisa do Postgres real (mesmo padrao de `tests/test_acervo.py`).
"""

from __future__ import annotations

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from saru_poc.acervo import caminho_aliases, semear
from saru_poc.pipeline.calibracao import (
    CANONICOS_CALIBRADOS_POR_SESSAO,
    _maior_trecho_parado,
    calibrar_offsets_pi_pid,
)
from saru_poc.pipeline.ingestao import _escrever_canais
from saru_poc.pipeline.leitura import fator_do_canal
from saru_poc.readers.base import Cabecalho, CanalBruto
from saru_poc.storage import CAMADA_BRUTA, PonteiroSerie

# ---------------------------------------------------------------------------
# _maior_trecho_parado: puro, sem Postgres nem Parquet.
# ---------------------------------------------------------------------------


def test_maior_trecho_parado_acha_o_trecho_mais_longo() -> None:
    """Dois trechos com Speed ~ 0: o de 150 amostras vence o de 40."""
    speed = np.concatenate(
        [
            np.zeros(150),  # trecho parado 1 (o maior)
            np.linspace(1, 200, 300),  # andando
            np.zeros(40),  # trecho parado 2, curto demais sozinho
            np.linspace(1, 50, 60),
        ]
    )
    trecho = _maior_trecho_parado(speed)
    assert trecho == (0, 150)


def test_maior_trecho_parado_none_sem_trecho_longo_o_bastante() -> None:
    """Carro nunca fica de fato parado por tempo suficiente: sem calibracao,
    nunca adivinha (criterio de aceitacao da issue #36)."""
    speed = np.concatenate(
        [np.linspace(1, 200, 500), np.zeros(30), np.linspace(1, 100, 100)]
    )
    assert _maior_trecho_parado(speed) is None


def test_maior_trecho_parado_none_quando_carro_nunca_para() -> None:
    speed = np.linspace(5, 250, 1000)
    assert _maior_trecho_parado(speed) is None


# ---------------------------------------------------------------------------
# calibrar_offsets_pi_pid, _escrever_canais e fator_do_canal: contra o
# Postgres real da PoC (mesmo padrao skipif de tests/test_acervo.py).
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    not caminho_aliases().exists(), reason="snapshot do saru-app nao montado"
)


@pytest.fixture(scope="module")
def banco():
    from saru_poc.db import connect

    try:
        with connect() as conn:
            semear(conn)
            conn.commit()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")
    with connect(autocommit=True) as conn:
        yield conn


@pytest.fixture
def conn(banco):
    from saru_poc.db import connect

    with connect() as c:
        yield c
        c.rollback()


def _nova_gravacao(conn) -> str:
    linha = conn.execute("insert into gravacao default values returning id").fetchone()
    return str(linha[0])


def _ponteiro_50hz(tmp_path, *, speed, acc_long, acc_lat) -> PonteiroSerie:
    """Escreve um Parquet com o formato que o `LeitorPiPid.ler()` produz pra
    o grupo de 50 Hz (t_s, Speed, Acc Long, Acc Lat) e devolve o ponteiro
    correspondente, sem passar pelo `.pid` binario nem por `escrever_serie`.
    """
    n = len(speed)
    tabela = pa.table(
        {
            "t_s": np.arange(n, dtype=np.float64) / 50.0,
            "Speed": np.asarray(speed, dtype=np.float64),
            "Acc Long": np.asarray(acc_long, dtype=np.float64),
            "Acc Lat": np.asarray(acc_lat, dtype=np.float64),
        }
    )
    caminho = tmp_path / "50hz.parquet"
    pq.write_table(tabela, caminho)
    return PonteiroSerie(
        uri=caminho.as_uri(),
        camada=CAMADA_BRUTA,
        frequencia_hz=50.0,
        mapa_versao=None,
        linhas=n,
        bytes_=caminho.stat().st_size,
        sha256="0" * 64,
        t_inicio_s=0.0,
        t_fim_s=(n - 1) / 50.0,
        colunas=("Speed", "Acc Long", "Acc Lat"),
    )


def test_com_trecho_parado_calibra_os_dois_canais(conn, tmp_path) -> None:
    n = 400
    speed = np.zeros(n)
    speed[150:] = np.linspace(1.0, 200.0, n - 150)  # anda depois do trecho parado
    acc_long = np.full(n, 500.0)
    acc_lat = np.full(n, 480.0)
    ponteiro = _ponteiro_50hz(tmp_path, speed=speed, acc_long=acc_long, acc_lat=acc_lat)

    gravacao_id = _nova_gravacao(conn)
    resultado = calibrar_offsets_pi_pid(conn, gravacao_id, [ponteiro])

    assert resultado.canonicos_calibrados == CANONICOS_CALIBRADOS_POR_SESSAO
    assert resultado.motivo_faltante is None

    linhas = {
        r[0]: r[1]
        for r in conn.execute(
            """select canal_canonico_id, offset_contagem
                 from calibracao_canal_gravado where gravacao_id = %s""",
            (gravacao_id,),
        ).fetchall()
    }
    assert linhas["lon_acc"] == pytest.approx(500.0)
    assert linhas["lat_acc"] == pytest.approx(480.0)


def test_sem_trecho_parado_nao_calibra_e_declara_o_motivo(conn, tmp_path) -> None:
    n = 400
    speed = np.linspace(20.0, 220.0, n)  # nunca para
    ponteiro = _ponteiro_50hz(
        tmp_path, speed=speed, acc_long=np.full(n, 500.0), acc_lat=np.full(n, 480.0)
    )

    gravacao_id = _nova_gravacao(conn)
    resultado = calibrar_offsets_pi_pid(conn, gravacao_id, [ponteiro])

    assert resultado.canonicos_calibrados == frozenset()
    assert resultado.motivo_faltante is not None
    assert "lon_acc" in resultado.motivo_faltante
    assert "lat_acc" in resultado.motivo_faltante

    n_linhas = conn.execute(
        "select count(*) from calibracao_canal_gravado where gravacao_id = %s",
        (gravacao_id,),
    ).fetchone()[0]
    assert n_linhas == 0


def _cabecalho_pid(nomes: list[str]) -> Cabecalho:
    return Cabecalho(
        formato_id="pi_pid",
        leitor_versao="1",
        canais=tuple(
            CanalBruto(nome_bruto=n, frequencia_hz=50.0, n_amostras=400) for n in nomes
        ),
    )


def test_escrever_canais_deixa_lon_acc_fora_sem_calibracao(conn) -> None:
    """Regressao direta do criterio de aceitacao: sem calibracao, o canonico
    nao entra no inventario da gravacao, mesmo o perfil mapeando a coluna."""
    gravacao_id = _nova_gravacao(conn)
    cabecalho = _cabecalho_pid(["Acc Long", "Acc Lat", "Speed"])
    mapa = {
        "Acc Long": ("lon_acc", "contagem"),
        "Acc Lat": ("lat_acc", "contagem"),
        "Speed": ("speed", "kph"),
    }

    sem_mapa, _divergentes = _escrever_canais(
        conn, gravacao_id, cabecalho, mapa, frozenset()
    )
    assert sem_mapa == 2  # lon_acc e lat_acc, sem calibracao

    canonicos = {
        r[0]: r[1]
        for r in conn.execute(
            "select nome_bruto, canal_canonico_id from canal_gravado where gravacao_id = %s",
            (gravacao_id,),
        ).fetchall()
    }
    assert canonicos["Acc Long"] is None
    assert canonicos["Acc Lat"] is None
    assert canonicos["Speed"] == "speed"


def test_escrever_canais_aceita_lon_acc_quando_calibrado(conn) -> None:
    gravacao_id = _nova_gravacao(conn)
    cabecalho = _cabecalho_pid(["Acc Long", "Acc Lat"])
    mapa = {
        "Acc Long": ("lon_acc", "contagem"),
        "Acc Lat": ("lat_acc", "contagem"),
    }

    sem_mapa, _divergentes = _escrever_canais(
        conn, gravacao_id, cabecalho, mapa, frozenset({"lon_acc", "lat_acc"})
    )
    assert sem_mapa == 0

    canonicos = {
        r[0]: r[1]
        for r in conn.execute(
            "select nome_bruto, canal_canonico_id from canal_gravado where gravacao_id = %s",
            (gravacao_id,),
        ).fetchall()
    }
    assert canonicos["Acc Long"] == "lon_acc"
    assert canonicos["Acc Lat"] == "lat_acc"


def test_fator_do_canal_soma_offset_da_calibracao_ao_offset_do_perfil(
    conn, tmp_path
) -> None:
    """`canonico = fator*bruto + offset_perfil - fator*offset_contagem`. O
    offset do perfil pra lon_acc/lat_acc do pi_pid e 0 (seeds/aliases.yaml):
    o offset final devolvido tem que ser so a parte da calibracao."""
    n = 400
    speed = np.zeros(n)
    speed[150:] = np.linspace(1.0, 200.0, n - 150)
    acc_long = np.full(n, 500.0)
    ponteiro = _ponteiro_50hz(
        tmp_path, speed=speed, acc_long=acc_long, acc_lat=np.full(n, 480.0)
    )

    gravacao_id = _nova_gravacao(conn)
    calibrar_offsets_pi_pid(conn, gravacao_id, [ponteiro])
    # fator_do_canal resolve o perfil pela ultima ingestao com status <>
    # 'falhou': precisa de arquivo_bruto + ingestao pra achar o perfil pi_pid.
    arquivo_id = conn.execute(
        """insert into arquivo_bruto
             (gravacao_id, papel, formato_id, nome_arquivo, sha256, bytes, objeto_uri)
           values (%s, 'primario', 'pi_pid', 'teste.pid', repeat('0', 64), 1,
                   'file:///tmp/teste.pid')
           returning id""",
        (gravacao_id,),
    ).fetchone()[0]
    conn.execute(
        """insert into ingestao
             (arquivo_id, gravacao_id, perfil_id, leitor_versao, status,
              iniciada_em, concluida_em)
           values (%s, %s, 'pi_pid', '1', 'parcial', now(), now())""",
        (arquivo_id, gravacao_id),
    )

    mapa = fator_do_canal(conn, gravacao_id, "lon_acc", "Acc Long")
    assert mapa is not None
    fator, offset = mapa
    assert fator == pytest.approx(-0.25359997)
    assert offset == pytest.approx(-fator * 500.0)

    # canonico no trecho parado tem que sair perto de zero, e nao no offset
    # estatico do perfil (que e 0 sem a calibracao).
    calibrado = fator * 500.0 + offset
    assert calibrado == pytest.approx(0.0, abs=1e-6)
