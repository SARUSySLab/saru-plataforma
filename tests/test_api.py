"""Camada HTTP.

Os testes de leitura sao contra o banco real da PoC: a API nao calcula nada, e
mockar o pipeline aqui testaria o mock. O que interessa provar e (a) que as
rotas devolvem o shape do contrato, (b) que erro de cliente e erro nosso saem
com codigos diferentes, e (c) que a guarda de contrato de fato barra resposta
divergente em vez de entregar tela quebrada.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from saru_poc.contrato import carregar, validar


def _adotar_acervo(user_id: str) -> None:
    """Regra de escopo de 29/08: gravacao sem dono nao aparece mais pra
    nenhuma conta. Os testes de leitura usam o acervo semeado, entao a
    fixture ADOTA essas gravacoes pro usuario do teste. Tambem re-adota as
    que ficaram com usuarios de execucoes anteriores (email teste-*@saru.dev),
    senao o modulo so rodaria uma vez por banco.
    """
    from saru_poc.db import connect

    with connect() as conn:
        conn.execute(
            """update gravacao set user_id = %s
                where user_id is null
                   or user_id in (select id from usuario where email like %s)""",
            (user_id, "teste-%@saru.dev"),
        )
        conn.commit()


@pytest.fixture(scope="module")
def cliente():
    """Cliente JA AUTENTICADO.

    Desde a integracao de 29/08 as rotas de leitura exigem sessao: guard de
    autenticacao mais filtro de dono no WHERE. O `TestClient` guarda o cookie
    httpOnly que o registro devolve, entao autenticar aqui uma vez basta pro
    modulo inteiro.

    O usuario e novo a cada execucao (uuid no e-mail) pra o modulo poder rodar
    duas vezes seguidas sem esbarrar no UNIQUE de e-mail. As gravacoes que os
    testes leem sao do ACERVO (`user_id is null`), visiveis a qualquer conta,
    entao usuario novo enxerga o mesmo catalogo.
    """
    from saru_poc.api import app

    try:
        from saru_poc.db import ping

        ping()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")

    c = TestClient(app)
    resposta = c.post(
        "/api/auth/registro",
        json={"email": f"teste-{uuid4()}@saru.dev", "senha": "senha-de-teste-123", "nome": "teste"},
    )
    assert resposta.status_code == 201, resposta.text
    _adotar_acervo(resposta.json()["id"])
    return c


@pytest.fixture(scope="module")
def tipos():
    return carregar()


@pytest.fixture(scope="module")
def gravacao_com_relatorio(cliente):
    """A primeira gravacao que tem volta E trecho: a que rende relatorio cheio."""
    resposta = cliente.get("/api/gravacoes", params={"com_volta": True})
    assert resposta.status_code == 200
    completas = [g for g in resposta.json() if g["voltas"] > 1 and g["trechos"] > 0]
    if not completas:
        pytest.skip("nenhuma gravacao decomposta no catalogo")
    return completas[0]["gravacao_id"]


def test_saude_nao_mente_sobre_o_banco(cliente) -> None:
    corpo = cliente.get("/api/saude").json()
    assert corpo["ok"] is True
    assert "PostgreSQL" in corpo["postgres"]


def test_lista_de_gravacoes_diz_o_que_esta_pronto(cliente) -> None:
    corpo = cliente.get("/api/gravacoes").json()
    assert isinstance(corpo, list)
    assert corpo, "catalogo vazio"
    for chave in ("gravacao_id", "voltas", "trechos", "layout_id"):
        assert chave in corpo[0]


def test_filtro_com_volta_nao_devolve_gravacao_sem_volta(cliente) -> None:
    """Sem volta nao ha N0 nem N1: a lista precisa dizer isso antes de o front
    pedir um relatorio que nao existe."""
    corpo = cliente.get("/api/gravacoes", params={"com_volta": True}).json()
    assert all(g["voltas"] > 0 for g in corpo)


def test_relatorio_bate_com_o_contrato(cliente, tipos, gravacao_com_relatorio) -> None:
    resposta = cliente.get(f"/api/relatorio/{gravacao_com_relatorio}")
    assert resposta.status_code == 200
    assert validar(resposta.json(), "Relatorio", tipos) == []


def test_escopo_muda_as_perdas(cliente, gravacao_com_relatorio) -> None:
    """A razao de `?volta=` e `?referencia=` existirem: sem eles, trocar a volta
    na tela nao mudava as perdas, porque elas vem calculadas do backend."""
    base = cliente.get(f"/api/relatorio/{gravacao_com_relatorio}").json()
    voltas = [v["n"] for v in base["n1"]["voltas"]]
    if len(voltas) < 2:
        pytest.skip("precisa de 2 voltas pra trocar o escopo")
    a = cliente.get(
        f"/api/relatorio/{gravacao_com_relatorio}",
        params={"volta": voltas[0], "referencia": voltas[-1]},
    ).json()
    b = cliente.get(
        f"/api/relatorio/{gravacao_com_relatorio}",
        params={"volta": voltas[-1], "referencia": voltas[0]},
    ).json()
    perdas_a = [i["perda_s"] for i in a["n0"]["perdas_top3"]["itens"]]
    perdas_b = [i["perda_s"] for i in b["n0"]["perdas_top3"]["itens"]]
    assert perdas_a != perdas_b, "trocar volta e referencia nao mudou nada"
    # Inverter o par inverte o sinal: o delta da primeira volta medido contra a
    # ultima e o oposto do delta da ultima medido contra a primeira. Nao e a
    # mesma POSICAO nas duas respostas (na segunda, a volta de referencia tem
    # delta zero por construcao), e sim a volta oposta.
    assert a["n1"]["voltas"][0]["delta_referencia_s"] == pytest.approx(
        -b["n1"]["voltas"][-1]["delta_referencia_s"], abs=0.001
    )


def test_amostras_batem_com_o_contrato_e_com_a_grade(
    cliente, tipos, gravacao_com_relatorio
) -> None:
    from saru_poc.relatorio import GRADE_PONTOS

    resposta = cliente.get(f"/api/gravacoes/{gravacao_com_relatorio}/amostras")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert validar(corpo, "SerieAmostras", tipos) == []
    assert len(corpo["distancia_m"]) == GRADE_PONTOS
    for nome, valores in corpo["canais"].items():
        assert len(valores) == GRADE_PONTOS, f"canal {nome} fora da grade"


def test_duas_voltas_saem_na_mesma_grade(cliente, gravacao_com_relatorio) -> None:
    """`calcularDelta` no front indexa as duas voltas pelos MESMOS indices. Se a
    grade divergir entre voltas, a comparacao mente sem erro nenhum."""
    base = cliente.get(f"/api/relatorio/{gravacao_com_relatorio}").json()
    voltas = [v["n"] for v in base["n1"]["voltas"]][:2]
    if len(voltas) < 2:
        pytest.skip("precisa de 2 voltas")
    series = [
        cliente.get(
            f"/api/gravacoes/{gravacao_com_relatorio}/amostras", params={"volta": n}
        ).json()
        for n in voltas
    ]
    assert series[0]["distancia_m"] == series[1]["distancia_m"]


def test_velocidade_sai_na_unidade_que_o_front_assume(
    cliente, gravacao_com_relatorio
) -> None:
    """km/h, nao m/s. Um carro de pista passa de 100 km/h e nao passa de 100 m/s
    (360 km/h), entao o pico separa as duas escalas sem ambiguidade."""
    corpo = cliente.get(
        f"/api/gravacoes/{gravacao_com_relatorio}/amostras"
    ).json()
    if "velocidade" not in corpo["canais"]:
        pytest.skip("captura sem canal de velocidade")
    pico = max(corpo["canais"]["velocidade"])
    assert 80.0 < pico < 400.0, f"pico de {pico} nao parece km/h"


def test_gravacao_inexistente_e_404(cliente) -> None:
    zero = "00000000-0000-0000-0000-000000000000"
    assert cliente.get(f"/api/relatorio/{zero}").status_code == 404
    assert cliente.get(f"/api/gravacoes/{zero}/amostras").status_code == 404


def test_volta_nao_numerica_e_422(cliente, gravacao_com_relatorio) -> None:
    resposta = cliente.get(
        f"/api/gravacoes/{gravacao_com_relatorio}/amostras", params={"volta": "abc"}
    )
    assert resposta.status_code == 422


def test_volta_que_nao_existe_na_captura_e_404(
    cliente, gravacao_com_relatorio
) -> None:
    resposta = cliente.get(
        f"/api/gravacoes/{gravacao_com_relatorio}/amostras", params={"volta": 9999}
    )
    assert resposta.status_code == 404


def test_resposta_divergente_do_contrato_vira_500(
    cliente, gravacao_com_relatorio, monkeypatch
) -> None:
    """A guarda tem que barrar shape errado ANTES de sair. 500 e o codigo certo:
    quem errou fomos nos, nao o cliente."""
    from saru_poc import api

    monkeypatch.setattr(
        api, "montar", lambda *a, **k: {"gravacao_id": "x", "inventado": True}
    )
    resposta = cliente.get(f"/api/relatorio/{gravacao_com_relatorio}")
    assert resposta.status_code == 500
    assert "contrato" in str(resposta.json()["detail"]["erro"])


def test_upload_sem_arquivo_e_422(cliente) -> None:
    assert cliente.post("/api/gravacoes").status_code == 422


def test_upload_do_mesmo_arquivo_nao_cria_segunda_gravacao(cliente) -> None:
    """Dedupe pelo sha256 do primario, a chave natural da gravacao. Reenviar o
    bundle inteiro de novo tem que devolver a gravacao que ja existe."""
    from saru_poc.config import CONFIG

    if not CONFIG.acervo_root.exists():
        pytest.skip("acervo nao montado")
    candidatos = [
        f
        for f in CONFIG.acervo_root.rglob("*.vbo")
        if f.is_file() and f.stat().st_size < 3_000_000
    ]
    if not candidatos:
        pytest.skip("sem arquivo pequeno no acervo pra testar upload")
    alvo = candidatos[0]
    with alvo.open("rb") as fh:
        resposta = cliente.post(
            "/api/gravacoes", files={"arquivos": (alvo.name, fh, "text/plain")}
        )
    assert resposta.status_code == 202
    corpo = resposta.json()
    # D1-A: a resposta e uma LISTA de gravacoes (cada captura vira a sua);
    # um arquivo so vira uma lista de um item
    assert len(corpo["gravacoes"]) == 1
    assert corpo["gravacoes"][0]["ja_existia"] is True, "o arquivo do acervo ja foi ingerido antes"
    assert corpo["pipeline"] == "ja processada"


def test_contexto_entra_e_volta_no_relatorio(cliente, gravacao_com_relatorio) -> None:
    """Escrita e leitura tem que fechar o loop. Na primeira versao a rota
    gravava e o relatorio seguia dizendo "sem contexto": o `montar` nunca lia a
    tabela."""
    resposta = cliente.post(
        f"/api/gravacoes/{gravacao_com_relatorio}/contexto",
        json={
            "pneu": {"estado": "novo", "voltas_rodadas": 3, "composto": "teste"},
            "temperatura_ar_c": 21.5,
            "notas_piloto": "teste automatizado",
        },
    )
    assert resposta.status_code == 201
    rel = cliente.get(f"/api/relatorio/{gravacao_com_relatorio}").json()
    sessao = rel["contexto"]["sessao"]
    assert sessao["disponivel"] is True
    assert sessao["pneu"]["voltas_rodadas"] == 3
    assert sessao["temperatura_ar_c"] == pytest.approx(21.5)
    assert sessao["origem"] == "gravacao"


def test_contexto_em_gravacao_inexistente_e_404(cliente) -> None:
    zero = "00000000-0000-0000-0000-000000000000"
    assert cliente.post(f"/api/gravacoes/{zero}/contexto", json={}).status_code == 404


# --- excecao 3e do E-UC-01: captura que entrou so como inventario --------


def _gravacao_so_de_inventario(cliente) -> str:
    """Uma gravacao cujo bundle inteiro veio de leitor de inventario.

    Sai do banco, nao de lista fixa de id: o acervo de cada maquina e outro, e
    fixar id faria o teste falhar por motivo errado. Sem candidata, pula.
    """
    from saru_poc.db import connect
    from saru_poc.readers import LEITORES

    so_inventario = [f for f, leitor in LEITORES.items() if not leitor.suporta_amostra]
    if not so_inventario:
        pytest.skip("nenhum formato de inventario registrado")
    with connect() as conn:
        linha = conn.execute(
            """select g.id from gravacao g
                where exists (select 1 from ingestao i where i.gravacao_id = g.id)
                  and not exists (
                        select 1 from arquivo_bruto ab
                         where ab.gravacao_id = g.id
                           and ab.formato_id <> all(%s))
                  -- Todo arquivo do bundle tem que ter sido lido: bundle com
                  -- arquivo ainda na fila NAO e inventario, e desde a correcao
                  -- do achado 2 a rota nao o declara como tal.
                  and not exists (
                        select 1 from arquivo_bruto ab2
                         where ab2.gravacao_id = g.id
                           and not exists (
                                 select 1 from ingestao i2
                                  where i2.arquivo_id = ab2.id
                                    and i2.status <> 'falhou'))
                limit 1""",
            (so_inventario,),
        ).fetchone()
    if linha is None:
        pytest.skip("nenhuma gravacao so de inventario no acervo desta maquina")
    return str(linha[0])


def test_estado_declara_inventario(cliente) -> None:
    """Segundo criterio da issue #2: o piloto pergunta em que pe esta a
    gravacao e a resposta traz o status `parcial` da ingestao e o motivo, em
    vez de culpar a pista."""
    gravacao_id = _gravacao_so_de_inventario(cliente)
    corpo = cliente.get(f"/api/gravacoes/{gravacao_id}/estado").json()
    assert corpo["ingestao"] is not None
    assert corpo["ingestao"]["status"] == "parcial"
    assert "inventário" in corpo["ingestao"]["motivo"]
    assert corpo["etapa"] == "ingestao"
    assert "inventário" in corpo["motivo"]
    assert corpo["sugestao"], "erro sem saida e erro decorativo"


def test_estado_de_gravacao_com_amostra_nao_fala_de_inventario(
    cliente, gravacao_com_relatorio
) -> None:
    """Terceiro criterio: com amostra no bundle, o aviso nao aparece."""
    corpo = cliente.get(f"/api/gravacoes/{gravacao_com_relatorio}/estado").json()
    assert corpo["etapa"] == "pronto"
    motivo = (corpo["ingestao"] or {}).get("motivo") or ""
    assert "inventário" not in motivo


def test_relatorio_declara_se_a_captura_virou_amostra(
    cliente, gravacao_com_relatorio
) -> None:
    """PIL-CT-52 no relatorio: o bloco existe sempre, e numa gravacao que rende
    relatorio cheio ele esta disponivel com a contagem de arquivos."""
    corpo = cliente.get(f"/api/relatorio/{gravacao_com_relatorio}").json()
    bloco = corpo["amostra_da_captura"]
    assert bloco["disponivel"] is True
    assert bloco["arquivos_com_amostra"] >= 1
    assert bloco["arquivos_lidos"] >= bloco["arquivos_com_amostra"]


def test_estado_de_bundle_com_arquivo_na_fila_nao_manda_reenviar(cliente) -> None:
    """Achado 2 da revisao. A recepcao ingere arquivo a arquivo, com commit
    entre eles, entao um bundle CERTO passa por um estado em que so o `.gpk`
    entrou. Declarar inventario ali mandava o piloto reenviar o arquivo que ele
    ja tinha enviado e que estava na fila.

    O teste varre o catalogo atras de uma gravacao nesse estado; onde nao houver
    nenhuma, a garantia fica com os testes puros de `tests/test_relatorio.py`."""
    from saru_poc.db import connect

    with connect() as conn:
        linha = conn.execute(
            """select g.id from gravacao g
                where exists (select 1 from ingestao i where i.gravacao_id = g.id)
                  and exists (
                        select 1 from arquivo_bruto ab
                         where ab.gravacao_id = g.id
                           and not exists (
                                 select 1 from ingestao i2
                                  where i2.arquivo_id = ab.id
                                    and i2.status <> 'falhou'))
                limit 1""",
        ).fetchone()
    if linha is None:
        pytest.skip("nenhuma gravacao com arquivo por ingerir no acervo desta maquina")

    corpo = cliente.get(f"/api/gravacoes/{linha[0]}/estado").json()
    motivo = corpo.get("motivo") or ""
    sugestao = corpo.get("sugestao") or ""
    assert "só como inventário" not in motivo
    assert "envie também o arquivo principal" not in sugestao
