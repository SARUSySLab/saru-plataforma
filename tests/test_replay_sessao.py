"""Testes do reprodutor de sessao (scripts/replay_sessao.py).

O reprodutor mora em scripts/, fora do pacote instalado; carrega por caminho
igual os outros scripts do repo (sys.path.insert em src/, ja feito pelo
proprio modulo ao ser importado).
"""

from __future__ import annotations

import importlib.util
import io
import sys
import time
from pathlib import Path

import numpy as np
import pytest

RAIZ = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "replay_sessao", RAIZ / "scripts" / "replay_sessao.py"
)
replay_sessao = importlib.util.module_from_spec(_spec)
sys.modules["replay_sessao"] = replay_sessao
_spec.loader.exec_module(replay_sessao)  # type: ignore[union-attr]

Evento = replay_sessao.Evento
montar_eventos_grupo = replay_sessao.montar_eventos_grupo
mesclar_eventos = replay_sessao.mesclar_eventos
reproduzir = replay_sessao.reproduzir
linha_jsonl = replay_sessao.linha_jsonl


def test_montar_eventos_grupo_pula_nan_e_mantem_finitos() -> None:
    t_s = np.array([0.0, 0.1, 0.2])
    canais = {"speed": np.array([10.0, np.nan, 12.0])}
    eventos = montar_eventos_grupo(t_s, canais)
    # instante 0.1 nao amostrou (NaN): some da saida, nao vira zero disfarcado.
    assert [e.t_s for e in eventos] == [0.0, 0.2]
    assert eventos[0].canais == {"speed": 10.0}
    assert eventos[1].canais == {"speed": 12.0}


def test_mesclar_taxas_mistas_ordena_por_instante_e_seq_cresce() -> None:
    """Duas series sinteticas, 10 Hz e 50 Hz, entrelacadas.

    Confere duas coisas do contrato: a ordenacao final por t_s bate com a
    uniao ordenada dos instantes de origem (nenhuma serie foi reamostrada
    pra caber na outra), e o seq atribuido na emissao e estritamente
    crescente, sem pular nem repetir.
    """
    t_10hz = np.arange(0, 0.5, 0.1)  # 0.0, 0.1, 0.2, 0.3, 0.4
    v_10hz = {"rpm": np.array([1000.0, 1100.0, 1200.0, 1300.0, 1400.0])}
    t_50hz = np.arange(0, 0.5, 0.02)  # 0.0, 0.02, 0.04, ..., 0.48 (25 pontos)
    v_50hz = {"speed": np.linspace(50.0, 74.0, t_50hz.shape[0])}

    grupo_10 = montar_eventos_grupo(t_10hz, v_10hz)
    grupo_50 = montar_eventos_grupo(t_50hz, v_50hz)
    mesclados = mesclar_eventos([grupo_10, grupo_50])

    # t=0.0 e comum as duas taxas: tem que virar UM evento so com os dois canais.
    esperado_t = sorted(set(round(float(x), 10) for x in t_10hz) | set(round(float(x), 10) for x in t_50hz))
    assert [round(e.t_s, 10) for e in mesclados] == esperado_t
    assert mesclados[0].canais == {"rpm": 1000.0, "speed": 50.0}

    # ordenacao monotonica (taxas misturadas nunca produzem t_s regressivo)
    tempos = [e.t_s for e in mesclados]
    assert tempos == sorted(tempos)

    linhas = [linha_jsonl(seq, "grav-teste", e) for seq, e in enumerate(mesclados, start=1)]
    seqs = [linha["seq"] for linha in linhas]
    assert seqs == list(range(1, len(linhas) + 1))
    assert all(b - a == 1 for a, b in zip(seqs, seqs[1:]))


def test_mesclar_sem_grupos_devolve_lista_vazia() -> None:
    assert mesclar_eventos([]) == []
    assert mesclar_eventos([[], []]) == []


def test_reproduzir_respeita_velocidade_com_folga_generosa() -> None:
    """5 s de gravacao sintetica (4 Hz) a 50x: ritmo esperado ~0.1 s.

    Folga generosa dos dois lados: baixo o bastante pra pegar bug grosseiro
    (por exemplo ignorar --velocidade e tocar em tempo real, o que estouraria
    o teto), alto o bastante pra nao ser frágil em CI lento.
    """
    t_s = np.arange(0.0, 5.0, 0.25)  # 20 amostras, 4 Hz
    eventos = montar_eventos_grupo(t_s, {"speed": np.linspace(0.0, 100.0, t_s.shape[0])})
    velocidade = 50.0
    esperado_s = t_s[-1] / velocidade

    saida = io.StringIO()
    inicio = time.monotonic()
    atrasadas = reproduzir(eventos, "grav-teste", velocidade, saida)
    decorrido = time.monotonic() - inicio

    assert atrasadas == 0
    assert decorrido < esperado_s * 6 + 1.0
    assert decorrido > esperado_s * 0.2

    linhas = saida.getvalue().strip().splitlines()
    assert len(linhas) == len(eventos)


def test_reproduzir_acusa_atraso_sem_mascarar_silencio(monkeypatch: pytest.MonkeyPatch) -> None:
    """Forca o relogio a saltar pra frente do alvo em todo evento: reproduzir
    tem que contar as amostras atrasadas e nunca fingir que chegaram no tempo.
    """
    eventos = [Evento(t_s=float(i) * 0.01, canais={"x": float(i)}) for i in range(5)]

    relogio = {"t": 0.0}

    def monotonic_falso() -> float:
        relogio["t"] += 1.0  # cada leitura pula 1 s: garante atraso > limiar sempre
        return relogio["t"]

    monkeypatch.setattr(replay_sessao.time, "monotonic", monotonic_falso)
    monkeypatch.setattr(replay_sessao.time, "sleep", lambda _s: None)

    saida = io.StringIO()
    atrasadas = reproduzir(eventos, "grav-teste", 1.0, saida, limiar_atraso_s=0.001)
    assert atrasadas == len(eventos)


def test_descobrir_canais_erra_com_lista_explicita_faltando(monkeypatch: pytest.MonkeyPatch) -> None:
    """Com --canais explicito, canal sem serie utilizavel e erro declarado,
    nunca saida vazia silenciosa (regra dura de nao inventar dado)."""

    def escolher_canal_falso(conn, gravacao_id, canonicos):
        return None  # nenhum canal pedido tem serie utilizavel

    monkeypatch.setattr(
        "saru_poc.pipeline.leitura.escolher_canal", escolher_canal_falso, raising=False
    )
    import saru_poc.pipeline.leitura as leitura_mod

    monkeypatch.setattr(leitura_mod, "escolher_canal", escolher_canal_falso)

    with pytest.raises(ValueError, match="sem serie utilizavel"):
        replay_sessao.descobrir_canais(conn=None, gravacao_id="grav-teste", pedidos=["speed"])


@pytest.fixture(scope="module")
def conexao_banco():
    sys.path.insert(0, str(RAIZ / "src"))
    from saru_poc.db import connect

    try:
        with connect(autocommit=True) as conn:
            conn.execute("select 1")
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres local indisponivel: {e}")
    with connect(autocommit=True) as conn:
        yield conn


def test_montar_eventos_da_gravacao_real_respeita_limite(conexao_banco) -> None:
    """Integracao fina contra o banco local: pega a primeira gravacao do
    acervo com canal canonico e confere que --limite-s corta a janela."""
    linha = conexao_banco.execute(
        """select distinct cg.gravacao_id from canal_gravado cg
            where cg.canal_canonico_id is not null limit 1"""
    ).fetchone()
    if linha is None:
        pytest.skip("acervo local sem canal canonico gravado")
    gravacao_id = str(linha[0])

    eventos = replay_sessao.montar_eventos_da_gravacao(
        conexao_banco, gravacao_id, pedidos=None, limite_s=5.0
    )
    assert eventos
    assert all(e.t_s <= 5.0 for e in eventos)
    assert eventos == sorted(eventos, key=lambda e: e.t_s)
