"""Live timing: parser do resultspage, ingestao com historico e rotas.

A fixture `livetiming_mbr.xml` e o XML REAL do 12o MBR Time Attack 2026
(Autodromo de Brasilia, 29/08, 84 carros em 9 classes), baixado do live
timing do evento. Nao e sintetico de proposito: os detalhes que quebram
parser (virgula decimal, "Piloto | Carro", gap "4 Voltas", lasttimeofday de
horas atras) vieram todos dele.

Os testes de banco rodam contra o Postgres real da PoC, no padrao de
`tests/test_api.py`, e pulam se ele nao estiver de pe.
"""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest

os.environ.setdefault("SARU_CICLO_SARUE", "0")

from fastapi.testclient import TestClient

from saru_poc.livetiming import (
    XmlInvalido,
    _nome_e_carro,
    _segundos,
    contar_track_limits,
    parse_avisos,
    parse_resultspage,
)

FIXTURE = Path(__file__).parent / "fixtures" / "livetiming_mbr.xml"


# --- parser, sem banco ------------------------------------------------------


def test_segundos_cobre_os_tres_formatos_do_xml_real() -> None:
    assert _segundos("1:54.459") == pytest.approx(114.459)
    assert _segundos("3:04:36.539") == pytest.approx(11076.539)
    assert _segundos("18:16:56.108") == pytest.approx(65816.108)
    assert _segundos("") is None
    assert _segundos(None) is None
    assert _segundos("4 Voltas") is None


def test_nome_e_carro_separa_no_pipe_do_fullname() -> None:
    assert _nome_e_carro("Pedro Piquet | Mclaren 765 LT 61MS") == (
        "Pedro Piquet",
        "Mclaren 765 LT 61MS",
    )
    assert _nome_e_carro("Fulano Sem Carro") == ("Fulano Sem Carro", None)


def test_parse_do_xml_real_do_mbr() -> None:
    dados = parse_resultspage(FIXTURE.read_bytes())

    assert dados["evento"]["nome"] == "12º MBR TIME ATTACK 2026"
    assert dados["evento"]["pista_nome"] == "Autódromo de Brasília"
    # tracklength "5,386" km -> metros
    assert dados["evento"]["track_length_m"] == pytest.approx(5386.0)
    assert dados["timeofday"] == "18:21:48"

    resultados = dados["resultados"]
    assert len(resultados) == 84
    assert len({r["classe"] for r in resultados}) == 9

    lider = next(r for r in resultados if r["posicao"] == 1)
    assert lider["numero"] == "6"
    assert lider["nome"] == "Pedro Piquet"
    assert lider["carro"] == "Mclaren 765 LT 61MS"
    assert lider["melhor_volta_s"] == pytest.approx(114.459)

    segundo = next(r for r in resultados if r["posicao"] == 2)
    # velocidade usa virgula decimal no XML
    assert segundo["ultima_vel_kmh"] == pytest.approx(163.834)
    assert segundo["ultima_passagem_s"] == pytest.approx(65816.108)
    # gap pode ser texto, fica string
    assert isinstance(segundo["gap"], str)


def test_xml_que_nao_e_resultspage_e_recusado() -> None:
    with pytest.raises(XmlInvalido):
        parse_resultspage(b"<outra_coisa/>")
    with pytest.raises(XmlInvalido):
        parse_resultspage(b"nem xml")


# --- banco + rotas ----------------------------------------------------------


@pytest.fixture
def cliente():
    from saru_poc.api import app

    try:
        from saru_poc.db import ping

        ping()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")
    return TestClient(app)


@pytest.fixture
def dono_logado(cliente):
    resposta = cliente.post(
        "/api/auth/registro",
        json={
            "email": f"lt-{uuid4()}@teste.saru",
            "senha": "senha-de-teste-123",
            "nome": "Gestor LT",
        },
    )
    assert resposta.status_code == 201
    return cliente


@pytest.fixture
def token_maquina(dono_logado):
    resposta = dono_logado.post(
        "/api/campeonato/maquinas", json={"nome": f"relay-teste-{uuid4().hex[:6]}"}
    )
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["token"].startswith("saru_mq_")
    return corpo["token"]


def _xml_unico() -> bytes:
    # eventname unico por teste pra nao colidir com uq_lt_evento_nome_run
    # entre execucoes
    bruto = FIXTURE.read_text(encoding="utf-8")
    return bruto.replace(
        "12º MBR TIME ATTACK 2026", f"MBR TESTE {uuid4().hex[:8]}"
    ).encode("utf-8")


def test_ingest_exige_token_de_maquina_e_cookie_nao_vale(dono_logado) -> None:
    # logado como humano (cookie), sem token de maquina: 401. Credencial de
    # pessoa nao escreve cronometragem.
    resposta = dono_logado.post(
        "/api/campeonato/ingest",
        content=FIXTURE.read_bytes(),
        headers={"Content-Type": "application/xml"},
    )
    assert resposta.status_code == 401


def test_ingest_grava_deduplica_e_deriva_passagens(dono_logado, token_maquina) -> None:
    xml = _xml_unico()
    cabecalhos = {
        "Authorization": f"Bearer {token_maquina}",
        "Content-Type": "application/xml",
    }

    primeira = dono_logado.post(
        "/api/campeonato/ingest", content=xml, headers=cabecalhos
    )
    assert primeira.status_code == 201
    corpo = primeira.json()
    assert corpo["novo"] is True
    # 84 carros com ate 3 voltas visiveis cada: o historico ja nasce populado
    assert corpo["passagens_novas"] > 84

    # mesmo XML de novo: dedupe por sha, no-op
    segunda = dono_logado.post(
        "/api/campeonato/ingest", content=xml, headers=cabecalhos
    )
    assert segunda.status_code == 201
    assert segunda.json()["novo"] is False

    evento_id = corpo["evento_id"]
    estado = dono_logado.get(f"/api/campeonato/{evento_id}/estado")
    assert estado.status_code == 200
    dados = estado.json()
    assert dados["snapshot"] is not None
    assert len(dados["snapshot"]["resultados"]) == 84
    assert dados["snapshot"]["timeofday_s"] == pytest.approx(66_108.0)

    voltas = dono_logado.get(f"/api/campeonato/{evento_id}/voltas")
    assert voltas.status_code == 200
    assert len(voltas.json()) > 0

    # tracado responde SEMPRE, disponivel ou declarando o que falta (regra B2)
    tracado = dono_logado.get(f"/api/campeonato/{evento_id}/tracado")
    assert tracado.status_code == 200
    assert "disponivel" in tracado.json()


def test_token_revogado_para_de_autenticar(dono_logado) -> None:
    criada = dono_logado.post(
        "/api/campeonato/maquinas", json={"nome": "relay-revogavel"}
    )
    assert criada.status_code == 201
    maquina = criada.json()

    revogada = dono_logado.delete(f"/api/campeonato/maquinas/{maquina['id']}")
    assert revogada.status_code == 204

    resposta = dono_logado.post(
        "/api/campeonato/ingest",
        content=_xml_unico(),
        headers={
            "Authorization": f"Bearer {maquina['token']}",
            "Content-Type": "application/xml",
        },
    )
    assert resposta.status_code == 401


def test_leitura_exige_login(cliente) -> None:
    assert cliente.get("/api/campeonato/eventos").status_code == 401


# --- avisos da direcao de prova (track limits) -------------------------------


def _xml_avisos() -> bytes:
    caminho = Path(__file__).parent / "fixtures" / "livetiming_announcements.xml"
    return caminho.read_bytes()


def test_parse_avisos_le_o_feed_real_do_mbr():
    avisos = parse_avisos(_xml_avisos())
    assert len(avisos) == 5
    assert avisos[0].hora == "08:57:02"
    assert avisos[0].tipo == "track_limit"
    # o texto CRU e preservado inteiro, a extracao e camada por cima
    assert avisos[0].texto.startswith("TRACKLIMIT: #70")


def test_numero_de_carro_e_string_com_zero_a_esquerda():
    # #08 nao e #8, e #033 nao e #33: converter pra int fundiria carros
    # diferentes num so, e no MBR os dois existem no mesmo grid.
    avisos = parse_avisos(_xml_avisos())
    numeros = {n for a in avisos for n, _ in a.carros}
    assert "08" in numeros
    assert "033" in numeros
    assert "001" in numeros


def test_reincidencia_entre_parenteses_vira_contagem():
    avisos = parse_avisos(_xml_avisos())
    primeiro = dict(avisos[0].carros)
    assert primeiro["75"] == 3
    assert primeiro["2"] == 5
    assert primeiro["70"] == 1


def test_aviso_sem_prefixo_fica_indefinido_e_nao_conta_como_track_limit():
    # a linha das 09:16 e so uma lista de carros. Parece continuacao do
    # tracklimit anterior, mas isso e inferencia: contar seria transformar
    # palpite em numero exibido ao lado do delta.
    avisos = parse_avisos(_xml_avisos())
    sem_prefixo = avisos[1]
    assert sem_prefixo.tipo == "indefinido"
    assert dict(sem_prefixo.carros)["120"] == 9
    assert "120" not in contar_track_limits(avisos)


def test_penalidade_de_perda_de_volta_e_classificada():
    avisos = parse_avisos(_xml_avisos())
    assert avisos[3].tipo == "perda_de_volta"
    assert avisos[4].tipo == "perda_de_volta"
    assert dict(avisos[4].carros) == {"14": 1}


def test_contagem_de_track_limits_soma_so_o_que_foi_anunciado_como_tal():
    total = contar_track_limits(parse_avisos(_xml_avisos()))
    assert total["2"] == 5
    assert total["75"] == 3
    # carro que so aparece na penalidade nao entra na conta de track limit
    assert "14" not in total
