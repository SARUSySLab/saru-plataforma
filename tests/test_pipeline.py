"""Etapas 1 e 2, contra arquivo real do acervo e o Postgres da PoC."""

from __future__ import annotations

import pytest

from saru_poc.config import CONFIG
from saru_poc.pipeline.ingestao import ingerir
from saru_poc.pipeline.recepcao import agrupar_bundles, receber
from saru_poc.readers import detectar

pytestmark = pytest.mark.skipif(
    not CONFIG.acervo_root.exists(), reason="acervo nao montado"
)


@pytest.fixture
def conn():
    try:
        from saru_poc.db import connect

        with connect() as c:
            yield c
            c.rollback()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")


def _bundle_aim():
    for f in sorted(CONFIG.acervo_root.rglob("*.xrk")):
        irmaos = sorted(
            x for x in f.parent.iterdir() if x.is_file() and x.stem == f.stem
        )
        if len(irmaos) > 1:
            return irmaos
    pytest.skip("sem bundle AiM no acervo")


def test_bundle_vira_uma_gravacao_com_papeis(conn) -> None:
    rec = receber(conn, _bundle_aim(), label="teste")
    papeis = [a.papel for a in rec.arquivos]
    assert papeis.count("primario") == 1, "bundle tem que ter exatamente um primario"
    assert set(papeis) <= {"primario", "indice", "gps", "backup", "workbook"}
    xrk = next(a for a in rec.arquivos if a.formato_id == "aim_xrk")
    assert xrk.papel == "primario", "o .xrk e quem carrega a amostra no bundle AiM"


def test_reenviar_o_mesmo_arquivo_nao_cria_segunda_gravacao(conn) -> None:
    """A chave natural da gravacao e o sha256 do arquivo primario."""
    bundle = _bundle_aim()
    a = receber(conn, bundle)
    conn.commit()
    b = receber(conn, bundle)
    assert b.ja_existia
    assert b.gravacao_id == a.gravacao_id


def test_arquivo_sem_formato_e_recusado_nao_adivinhado(conn) -> None:
    """Recepcao nao chuta formato: e a mesma regra do B2."""
    from pathlib import Path

    neutro = Path("/etc/hostname")
    if not neutro.exists():
        pytest.skip("sem arquivo neutro")
    with pytest.raises(ValueError, match="nenhum arquivo do bundle"):
        receber(conn, [neutro])


def test_recusado_aparece_no_relatorio_sem_derrubar_o_bundle(conn) -> None:
    from pathlib import Path

    bundle = [*_bundle_aim(), Path("/etc/hostname")]
    if not Path("/etc/hostname").exists():
        pytest.skip("sem arquivo neutro")
    rec = receber(conn, bundle)
    assert any("hostname" in r for r in rec.recusados)
    assert rec.arquivos


def test_sem_leitor_vira_linha_de_ingestao_com_motivo(conn) -> None:
    """Formato reconhecido e nao lido tem que virar divida no banco, nao silencio.

    O bundle AiM servia de cobaia aqui ate 29/08, quando `aim_xrk` e `aim_drk`
    ganharam leitor. O teste passa a procurar um formato que de fato nao tem
    leitor registrado, e pula quando todos tiverem: o dia em que isso acontecer,
    a divida acabou e o teste perdeu o objeto.
    """
    from saru_poc.readers import FORMATOS_POR_ID, LEITORES

    orfaos = {f for f in FORMATOS_POR_ID if f not in LEITORES}
    if not orfaos:
        pytest.skip("todo formato do catalogo tem leitor")

    alvo = None
    for f in sorted(CONFIG.acervo_root.rglob("*")):
        if not f.is_file() or ".git" in f.parts:
            continue
        d = detectar(f)
        if d.formato and d.formato.id in orfaos:
            alvo = f
            break
    if alvo is None:
        pytest.skip(f"sem arquivo no acervo dos formatos sem leitor: {orfaos}")

    rec = receber(conn, [alvo])
    arq = next(a for a in rec.arquivos if a.id)
    r = ingerir(conn, arq.id)
    assert r.status == "falhou"
    assert "sem leitor registrado" in (r.erro or "")


def test_ingestao_e_append_only(conn) -> None:
    """Reprocessar escreve outra linha, nunca sobrescreve a anterior."""
    rec = receber(conn, _bundle_aim())
    alvo = next(a for a in rec.arquivos if a.id)

    def linhas() -> int:
        return conn.execute(
            "select count(*) from ingestao where arquivo_id = %s", (alvo.id,)
        ).fetchone()[0]

    # Delta, nao valor absoluto: o banco pode ja ter historico deste arquivo,
    # e ter historico e justamente o comportamento que este teste protege.
    antes = linhas()
    um = ingerir(conn, alvo.id)
    dois = ingerir(conn, alvo.id)
    assert um.ingestao_id != dois.ingestao_id
    assert linhas() == antes + 2


def test_agrupar_bundles_usa_pasta_e_radical() -> None:
    from pathlib import Path

    caminhos = [
        Path("/a/x.xrk"),
        Path("/a/x.drk"),
        Path("/a/y.xrk"),
        Path("/b/x.xrk"),
    ]
    grupos = agrupar_bundles(caminhos)
    assert sorted(len(g) for g in grupos) == [1, 1, 2]
