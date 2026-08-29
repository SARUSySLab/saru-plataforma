"""Desempate de perfil por coluna discriminante.

O container `.ld` carrega 3 vocabularios concorrentes (`motec_ld`, `acc`,
`gt7_ld`), e a heuristica de cobertura minima (25%, `COBERTURA_MINIMA` em
`pipeline/ingestao.py`) fica sem candidato em gravacoes reais do acervo:
nenhum perfil alcanca o piso, entao os canais ficam sem `canal_canonico_id`
e a analise perde temperatura de pneu.

Este teste cobre o degrau novo de `_resolver_perfil`: quando a cobertura nao
decide, tenta por coluna discriminante ANTES de desistir. A discriminante e
DERIVADA do `mapeamento_canal` de verdade (coluna que so um perfil do formato
mapeia), nunca hardcoded: e o mesmo raciocinio do `_SIM_HINTS` do
`channel_mapper.py` do saru-app, so que sem lista fixa presa no codigo.

Roda contra o Postgres real da PoC (porta 5442), igual `test_reingestao.py`:
o teste cria formato/perfis/mapeamentos PROPRIOS dentro de uma transacao que
e revertida no teardown, entao nao suja o catalogo real nem depende da
contagem exata de canais dos perfis reais (que muda se o aliases.yaml
mudar).
"""

from __future__ import annotations

import uuid

import pytest

from saru_poc.pipeline.ingestao import _resolver_perfil
from saru_poc.readers.base import CanalBruto, Cabecalho


@pytest.fixture
def conn():
    try:
        from saru_poc.db import connect

        with connect() as c:
            yield c
            c.rollback()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")


def _canal_canonico_qualquer(conn) -> str:
    """Pega um id de canal_canonico existente pra usar como FK nos mapeamentos.

    O teste nao precisa que o canonico faca sentido semantico (nao materializa
    amostra, so testa a resolucao de perfil), so precisa satisfazer a FK.
    """
    linha = conn.execute("select id from canal_canonico limit 1").fetchone()
    assert linha is not None, "seed do catalogo nao rodou (canal_canonico vazio)"
    return linha[0]


def _mapa_versao_qualquer(conn) -> str:
    linha = conn.execute("select versao from mapa_canal limit 1").fetchone()
    assert linha is not None, "seed do catalogo nao rodou (mapa_canal vazio)"
    return linha[0]


def _semear_formato_com_dois_perfis(
    conn, canonico: str, mapa_versao: str
) -> tuple[str, str, str]:
    """Formato sintetico com 2 perfis concorrentes, cada um com:

    - 2 colunas COMPARTILHADAS pelos dois perfis (empurra cobertura pra baixo
      do piso quando o arquivo so declara elas, porque nenhum perfil se
      distingue).
    - 1 coluna EXCLUSIVA (a discriminante que o teste espera que decida).

    Devolve (formato_id, perfil_a, perfil_b).
    """
    sufixo = uuid.uuid4().hex[:8]
    formato_id = f"teste_fmt_{sufixo}"
    perfil_a = f"teste_perfil_a_{sufixo}"
    perfil_b = f"teste_perfil_b_{sufixo}"

    conn.execute(
        """insert into formato_telemetria
             (id, rotulo, fabricante, extensao_tipica, binario, leitor)
           values (%s,%s,%s,%s,%s,%s)""",
        (formato_id, "Formato de teste", "teste", ".tst", False, "nativo"),
    )
    for perfil in (perfil_a, perfil_b):
        conn.execute(
            """insert into perfil_origem (id, formato_id, rotulo, simulado)
               values (%s,%s,%s,%s)""",
            (perfil, formato_id, perfil, False),
        )

    compartilhadas = ["COL_COMUM_1", "COL_COMUM_2"]
    exclusivas = {perfil_a: "COL_SO_A", perfil_b: "COL_SO_B"}
    for perfil in (perfil_a, perfil_b):
        colunas = [*compartilhadas, exclusivas[perfil]]
        for coluna in colunas:
            conn.execute(
                """insert into mapeamento_canal
                     (perfil_id, canal_canonico_id, mapa_versao, coluna_bruta,
                      unidade_entrada, fator_escala)
                   values (%s,%s,%s,%s,%s,%s)""",
                (perfil, canonico, mapa_versao, coluna, "-", 1.0),
            )
    return formato_id, perfil_a, perfil_b


def _cabecalho(colunas: list[str]) -> Cabecalho:
    return Cabecalho(
        formato_id="ignorado",
        leitor_versao="teste",
        canais=tuple(
            CanalBruto(nome_bruto=c, frequencia_hz=100.0, n_amostras=10)
            for c in colunas
        ),
    )


def test_discriminante_decide_quando_cobertura_nao_alcanca(conn):
    """Arquivo so declara as compartilhadas + a exclusiva de B: cobertura de
    cada perfil fica em 2 de 3 (67%, passa o piso de 25%), mas margem entre os
    dois e zero (ambos casam as 2 compartilhadas, so B tambem casa a
    exclusiva). Cobertura sozinha empataria; a discriminante deve decidir por
    B porque so B mapeia COL_SO_B.
    """
    canonico = _canal_canonico_qualquer(conn)
    mapa_versao = _mapa_versao_qualquer(conn)
    formato_id, perfil_a, perfil_b = _semear_formato_com_dois_perfis(
        conn, canonico, mapa_versao
    )
    cabecalho = _cabecalho(["COL_COMUM_1", "COL_COMUM_2", "COL_SO_B"])

    perfil, motivo = _resolver_perfil(conn, formato_id, cabecalho, mapa_versao)

    assert perfil == perfil_b
    assert "COL_SO_B" in motivo
    assert "discriminante" in motivo


def test_discriminante_ausente_mantem_nao_mapeado(conn):
    """Arquivo so declara as colunas compartilhadas: nenhuma exclusiva
    presente, nenhum perfil se distingue. Tem que continuar None, com o
    motivo explicando que a discriminante tambem nao resolveu (nao pode virar
    silencio: o comportamento atual, do B2, era exatamente devolver um
    default sem dizer por que).
    """
    canonico = _canal_canonico_qualquer(conn)
    mapa_versao = _mapa_versao_qualquer(conn)
    formato_id, _perfil_a, _perfil_b = _semear_formato_com_dois_perfis(
        conn, canonico, mapa_versao
    )
    cabecalho = _cabecalho(["COL_COMUM_1", "COL_COMUM_2"])

    perfil, motivo = _resolver_perfil(conn, formato_id, cabecalho, mapa_versao)

    assert perfil is None
    assert "discriminante" in motivo


def test_resolucao_idempotente_entre_duas_chamadas(conn):
    """Resolver o mesmo cabecalho duas vezes seguidas devolve o mesmo perfil e
    o mesmo motivo: a heuristica so le o catalogo, nao muda estado, entao
    reingerir a mesma gravacao nao pode oscilar o resultado.
    """
    canonico = _canal_canonico_qualquer(conn)
    mapa_versao = _mapa_versao_qualquer(conn)
    formato_id, _perfil_a, perfil_b = _semear_formato_com_dois_perfis(
        conn, canonico, mapa_versao
    )
    cabecalho = _cabecalho(["COL_COMUM_1", "COL_COMUM_2", "COL_SO_B"])

    primeira = _resolver_perfil(conn, formato_id, cabecalho, mapa_versao)
    segunda = _resolver_perfil(conn, formato_id, cabecalho, mapa_versao)

    assert primeira == segunda
    assert primeira[0] == perfil_b
