"""CLI `reingerir`: reprocessa ingestao presa em `falhou`/`parcial`.

Contexto do bug que motivou o comando: `storage.py` e `pipeline/tracado.py`
usavam `Path.replace`, que cai com `OSError: Invalid cross-device link` quando
origem e destino do move ficam em filesystems diferentes. A causa ja foi
corrigida (virou `shutil.move`), mas a linha de `ingestao` que registrou o
fracasso e append-only e continua `status='falhou'` pra sempre - e a recepcao
dedupe por sha256, entao reenviar o mesmo arquivo nao chama `ingerir` de novo.

Estes testes rodam contra o Postgres real da PoC (porta 5442), igual
`tests/test_pipeline.py` e `tests/test_api.py`: nao ha mock de banco aqui, o
`reingerir` mexe em tabela de verdade e o que importa provar e que a segunda
rodada nao duplica nada. Os candidatos (arquivo com ingestao falhou/parcial)
sao descobertos em runtime, nunca por uuid fixo: o catalogo e um banco
compartilhado entre sessoes paralelas de trabalho neste repo, entao um uuid
hardcoded quebraria assim que outra sessao reprocessasse aquele arquivo antes
deste teste rodar.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def conn():
    try:
        from saru_poc.db import connect

        with connect() as c:
            yield c
            c.rollback()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")


def _latest_por_arquivo(conn) -> list[tuple[str, str, str]]:
    """(arquivo_id, gravacao_id, status) da ingestao MAIS RECENTE de cada arquivo.

    Mesma consulta que `cli.reingerir` usa pra decidir o que reprocessar:
    reaproveitar aqui garante que o teste descobre exatamente os mesmos
    candidatos que o comando veria.
    """
    linhas = conn.execute(
        """select distinct on (i.arquivo_id) i.arquivo_id, i.gravacao_id, i.status
             from ingestao i
            order by i.arquivo_id, i.iniciada_em desc, i.id desc"""
    ).fetchall()
    return [(str(a), str(g), s) for a, g, s in linhas]


def _contagens(conn, gravacao_id: str) -> tuple[int, int]:
    voltas = conn.execute(
        "select count(*) from volta where session_id = %s", (gravacao_id,)
    ).fetchone()[0]
    trechos = conn.execute(
        """select count(*) from tempo_trecho t join volta v on v.id = t.volta_id
            where v.session_id = %s""",
        (gravacao_id,),
    ).fetchone()[0]
    return voltas, trechos


def _candidato_com_volta_previa(conn) -> str | None:
    """Gravacao com ingestao falhou/parcial pendente E que ja tem volta cortada.

    E o caso mais duro pra idempotencia: reingerir tem que apagar a volta
    velha (FK de tempo_trecho/tracado obriga) e recriar do zero sem sobrar
    nem faltar nada na segunda rodada.
    """
    latest = _latest_por_arquivo(conn)
    pendentes = {g for _, g, s in latest if s in ("falhou", "parcial")}
    if not pendentes:
        return None
    com_volta = {
        str(r[0])
        for r in conn.execute(
            """select v.session_id from volta v
                 join tempo_trecho t on t.volta_id = v.id
                group by v.session_id"""
        ).fetchall()
    }
    achou = pendentes & com_volta
    return next(iter(achou), None)


def test_reprocessar_a_mesma_gravacao_duas_vezes_nao_duplica(conn) -> None:
    from saru_poc.cli import reingerir

    gravacao_id = _candidato_com_volta_previa(conn)
    if gravacao_id is None:
        pytest.skip("nenhuma gravacao com volta previa tem ingestao falhou/parcial")

    reingerir(gravacao=gravacao_id, tudo=True)
    primeira = _contagens(conn, gravacao_id)

    reingerir(gravacao=gravacao_id, tudo=True)
    segunda = _contagens(conn, gravacao_id)

    assert primeira == segunda, (
        "rodar reingerir duas vezes seguidas sobre a mesma gravacao mudou a "
        f"contagem de volta/trecho: {primeira} depois {segunda}"
    )


def test_reingerir_e_idempotente_mesmo_quando_continua_falhando(conn) -> None:
    """Cobaia de propósito num arquivo que hoje falha por OUTRA causa (leitor
    incompleto pra .pds concatenado, .xrk sem amostra decodificavel etc, nao
    a causa que esta tarefa corrigiu). O que este teste prova nao e que o
    arquivo passa a ingerir: e que reingerir com um arquivo que TEIMA em
    falhar continua idempotente (nao acumula volta/trecho fantasma a cada
    rodada) e que o resumo (`falharam_de_novo`) bate com o status real gravado
    em `ingestao`, nao um numero solto.
    """
    from saru_poc.cli import reingerir

    latest = _latest_por_arquivo(conn)
    falhas = [(a, g) for a, g, s in latest if s == "falhou"]
    if not falhas:
        pytest.skip("nenhuma ingestao com status falhou no catalogo agora")

    arquivo_id, gravacao_id = falhas[0]

    codigo_um = reingerir(gravacao=gravacao_id, tudo=False)
    contagens_um = _contagens(conn, gravacao_id)
    status_um = conn.execute(
        """select status from ingestao where arquivo_id = %s
            order by iniciada_em desc, id desc limit 1""",
        (arquivo_id,),
    ).fetchone()[0]
    # O codigo de saida e o espelho do status real: 1 so quando alguem ainda
    # falhou, 0 quando tudo que foi reprocessado saiu ok/parcial.
    assert codigo_um == (1 if status_um == "falhou" else 0)

    codigo_dois = reingerir(gravacao=gravacao_id, tudo=False)
    contagens_dois = _contagens(conn, gravacao_id)
    status_dois = conn.execute(
        """select status from ingestao where arquivo_id = %s
            order by iniciada_em desc, id desc limit 1""",
        (arquivo_id,),
    ).fetchone()[0]

    assert contagens_um == contagens_dois, (
        "duas rodadas sobre o mesmo arquivo que segue falhando nao podem "
        f"mudar volta/trecho: {contagens_um} depois {contagens_dois}"
    )
    assert codigo_dois == (1 if status_dois == "falhou" else 0)


def test_reingerir_sem_pendencia_nao_faz_nada(conn) -> None:
    """Gravacao sem nenhuma linha de ingestao: nao ha o que reprocessar."""
    from uuid import uuid4

    from saru_poc.cli import reingerir

    alvo = str(uuid4())
    antes = conn.execute(
        "select count(*) from ingestao where gravacao_id = %s", (alvo,)
    ).fetchone()[0]
    assert antes == 0

    codigo = reingerir(gravacao=alvo, tudo=True)
    assert codigo == 0
