"""Carga do catalogo de acervo, contra o Postgres e o aliases.yaml reais."""

from __future__ import annotations

import pytest

from saru_poc.acervo import PERFIL_PARA_FORMATO, caminho_aliases, ler_aliases, semear
from saru_poc.config import CONFIG
from saru_poc.readers import FORMATOS_POR_ID

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


def test_todo_perfil_semeado_aponta_pra_formato_medido() -> None:
    """Perfil so entra com formato de assinatura medida (decisao de 29/08)."""
    for perfil, formato in PERFIL_PARA_FORMATO.items():
        assert formato in FORMATOS_POR_ID, f"{perfil} aponta pra formato inexistente"
        assert FORMATOS_POR_ID[formato].amostras_medidas > 0


def test_seed_e_idempotente(banco) -> None:
    from saru_poc.db import connect

    antes = banco.execute("select count(*) from mapeamento_canal").fetchone()[0]
    with connect() as conn:
        semear(conn)
        conn.commit()
    assert banco.execute("select count(*) from mapeamento_canal").fetchone()[0] == antes


def test_varios_nomes_brutos_pro_mesmo_canal(banco) -> None:
    """Regressao da chave invertida em 29/08.

    Com a PK antiga, (perfil, canal_canonico, mapa_versao), so cabia UM nome de
    coluna por canal. O aliases.yaml tem 35 linhas que aceitam mais de um.
    """
    n = banco.execute(
        """select count(*) from (
             select 1 from mapeamento_canal
             group by perfil_id, canal_canonico_id, mapa_versao having count(*) > 1
           ) t"""
    ).fetchone()[0]
    assert n > 0, "nenhum canal com mais de um nome bruto: a carga perdeu alias"


def test_freio_ficou_em_pressao_nao_em_fracao(banco) -> None:
    """Decisao de 29/08: normalize_by_max sai, o freio fica na unidade nativa."""
    linhas = banco.execute(
        """select m.perfil_id, m.unidade_entrada, m.fator_escala, g.unidade_canonica
           from mapeamento_canal m
           join canal_canonico cc on cc.id = m.canal_canonico_id
           join grandeza g on g.id = cc.grandeza_id
           where m.canal_canonico_id = 'brake_press'"""
    ).fetchall()
    assert linhas, "brake_press sem mapeamento"
    for _perfil, unidade_entrada, fator, canonica in linhas:
        assert unidade_entrada == "bar"
        assert canonica == "kPa"
        assert fator == pytest.approx(100.0)


def test_nenhum_mapeamento_semeado_dependia_de_normalize_by_max(banco) -> None:
    """O que era normalizado por arquivo nao pode ter virado fator 1 silencioso."""
    perfis = ler_aliases()
    for perfil in PERFIL_PARA_FORMATO:
        spec = perfis.get(perfil, {}).get("brake")
        if not (spec and spec.get("normalize_by_max")):
            continue
        alvos = {
            r[0]
            for r in banco.execute(
                """select canal_canonico_id from mapeamento_canal
                   where perfil_id = %s and canal_canonico_id in
                         ('brake', 'brake_press')""",
                (perfil,),
            )
        }
        assert alvos == {"brake_press"}, f"{perfil} ainda mapeia brake em fracao"


def test_toda_grandeza_tem_unidade_canonica_unica(banco) -> None:
    """Um canal canonico, uma unidade. E a doenca que o aliases.yaml documenta."""
    conflitos = banco.execute(
        """select cc.id, count(distinct g.unidade_canonica)
           from canal_canonico cc join grandeza g on g.id = cc.grandeza_id
           group by cc.id having count(distinct g.unidade_canonica) > 1"""
    ).fetchall()
    assert not conflitos


def test_acervo_root_existe_ou_pula() -> None:
    if not CONFIG.acervo_root.exists():
        pytest.skip("acervo nao montado")
    assert CONFIG.acervo_root.is_dir()
