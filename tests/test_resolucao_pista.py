"""Etapa 4: resolucao de pista.

O modulo decide contra o BANCO (catalogo de layout, alias, gravacao), entao o
teste troca o banco por um dublê em memoria que responde as cinco consultas do
`resolver`. O degrau GPS tem a posicao injetada por monkeypatch, do mesmo jeito
que `tests/test_replay_sessao.py` troca `escolher_canal`: o que esta sob teste e
a DECISAO (alias, raio, ambiguidade, recusa), nao a leitura do Parquet.

A regra que estes testes protegem e a mesma do docstring do modulo: nao resolver
e resultado, com motivo gravado. Ambiguidade tambem e nao resolvido. Um layout
escolhido no palpite reproduz o bug B2, em que um kart de 1,1 km foi analisado
contra os setores de Interlagos.

Criterios cobertos: PIL-CT-09 (alias), PIL-CT-10 (GPS unico a ate 5,0 km),
PIL-CT-11 (sem venue e sem GPS coerente vira nao resolvida) e a parte do
PIL-CT-56 e do PIL-CT-45 que cai no degrau do alias, esta em `xfail` estrito
(issue #10, regra PIL-RN-17).

Distancia entre Interlagos e Donington, usada em dois testes daqui: cerca de
9.570 km, medido com `_distancia_m` sobre as constantes deste modulo. Os
docstrings de `tracado.py:16` e `corte_voltas.py:288` dizem 9.500 km e o
ADR-0048 do `saru-app` diz 9.600 km; sao arredondamentos da mesma medida, e
nenhum deles foi alterado.
"""

from __future__ import annotations

import math

import pytest

from saru_poc.pipeline import resolucao_pista
from saru_poc.pipeline.resolucao_pista import RAIO_GPS_M, _distancia_m, resolver

# Interlagos, a referencia do proprio catalogo. Serve so para dar escala real as
# distancias; qualquer coordenada de pista daria o mesmo resultado.
INTERLAGOS = (-23.70071, -46.69871)
# Donington, a coordenada que as 3 gravacoes GT7 do acervo declaram enquanto
# dizem no venue que sao de Interlagos (excecao 5g do E-UC-01).
DONINGTON = (52.82972, -1.37528)

R_TERRA_M = 6_371_000.0


def ao_norte(origem: tuple[float, float], metros: float) -> tuple[float, float]:
    """Ponto a `metros` ao norte de `origem`, pela mesma esfera do modulo."""
    lat, lon = origem
    return lat + math.degrees(metros / R_TERRA_M), lon


class Cursor(list):
    """O que `psycopg` devolve de um execute, no minimo que o modulo usa."""

    def fetchall(self) -> list:
        return list(self)

    def fetchone(self):
        return self[0] if self else None


class BancoFalso:
    """Catalogo e gravacoes em memoria, respondendo as consultas do `resolver`.

    `layouts` e uma lista de (layout_id, nome do layout, nome da pista, ref_lat,
    ref_lon), com referencia nula quando o layout nao tem coordenada.
    `gravacoes` e uma lista de (gravacao_id, metadata).
    """

    def __init__(self, layouts, gravacoes, aliases=()):
        self.layouts = list(layouts)
        self.gravacoes = list(gravacoes)
        self.aliases = list(aliases)
        self.resolvidas: dict[str, tuple[str, str]] = {}
        self.aliases_gravados: list[tuple[str, str, str]] = []

    def execute(self, sql: str, params=None) -> Cursor:
        q = " ".join(sql.split())
        if q.startswith("select l.id, l.nome, p.nome"):
            return Cursor(
                [(lid, nome, pista) for lid, nome, pista, _, _ in self.layouts]
            )
        if q.startswith("select alias, layout_id from alias_layout"):
            return Cursor(list(self.aliases))
        if q.startswith("select id, ref_lat, ref_lon from layout"):
            return Cursor(
                [
                    (lid, lat, lon)
                    for lid, _, _, lat, lon in self.layouts
                    if lat is not None and lon is not None
                ]
            )
        if q.startswith("select id, metadata from gravacao"):
            return Cursor(list(self.gravacoes))
        if q.startswith("update gravacao set layout_id"):
            layout_id, gid = params
            origem = "alias" if "'alias'" in q else "gps"
            self.resolvidas[gid] = (layout_id, origem)
            return Cursor()
        if q.startswith("insert into alias_layout"):
            alias, layout_id, fonte = params
            if any(a == alias and f == fonte for a, _, f in self.aliases_gravados):
                return Cursor()
            self.aliases_gravados.append((alias, layout_id, fonte))
            return Cursor([(alias,)])
        raise AssertionError(f"consulta nao prevista pelo banco falso: {q}")


@pytest.fixture
def sem_gps(monkeypatch: pytest.MonkeyPatch):
    """Gravacao sem amostra de GPS utilizavel: so o degrau do alias decide."""
    monkeypatch.setattr(resolucao_pista, "_posicao_mediana", lambda conn, gid: None)


def com_gps(monkeypatch: pytest.MonkeyPatch, posicao: tuple[float, float]) -> None:
    monkeypatch.setattr(resolucao_pista, "_posicao_mediana", lambda conn, gid: posicao)


def interlagos(ref: tuple[float, float] | None = INTERLAGOS):
    lat, lon = ref if ref else (None, None)
    return ("interlagos_gp", "Interlagos GP", "Interlagos", lat, lon)


def venue(formato: str, nome: str) -> dict:
    return {f"{formato}.venue_declarado": nome}


# --- degrau 1: alias -----------------------------------------------------


def test_venue_com_alias_unico_resolve_por_alias(sem_gps) -> None:
    """PIL-CT-09. O arquivo escreve `Autodromo de Interlagos`, o catalogo guarda
    `Interlagos GP`, e o alias e o que liga os dois sem inventar sinonimo."""
    banco = BancoFalso(
        layouts=[interlagos()],
        gravacoes=[("g1", venue("aim_xrk", "Autodromo de Interlagos"))],
        aliases=[("Autodromo de Interlagos", "interlagos_gp")],
    )
    resumo = resolver(banco)
    assert banco.resolvidas["g1"] == ("interlagos_gp", "alias")
    assert (resumo.resolvidas, resumo.por_gps, resumo.nao_resolvidas) == (1, 0, 0)


def test_acento_e_pontuacao_nao_impedem_o_casamento(sem_gps) -> None:
    """`Autódromo de Interlagos` e `autodromo-de-interlagos` sao a mesma pista
    escrita por dois exportadores."""
    banco = BancoFalso(
        layouts=[interlagos()],
        gravacoes=[("g1", venue("motec_ld", "Autódromo de Interlagos"))],
        aliases=[("autodromo-de-interlagos", "interlagos_gp")],
    )
    resolver(banco)
    assert banco.resolvidas["g1"][1] == "alias"


def test_venue_ambiguo_entre_layouts_da_mesma_pista_nao_resolve(sem_gps) -> None:
    """`monza` alcanca `monza_gp` e `monza_no_chicane`. Escolher um dos dois no
    palpite e o bug B2 com outra roupa."""
    banco = BancoFalso(
        layouts=[
            ("monza_gp", "Monza GP", "Monza", None, None),
            ("monza_no_chicane", "Monza sem chicane", "Monza", None, None),
        ],
        gravacoes=[("g1", venue("aim_xrk", "Monza"))],
    )
    resumo = resolver(banco)
    assert banco.resolvidas == {}
    assert resumo.nao_resolvidas == 1
    assert any("ambiguo" in m for m in resumo.por_motivo)


def test_venue_de_bancada_nao_vira_pista(sem_gps) -> None:
    """`Engine test` e rotulo de bancada, nao pista. Vira nao resolvida com o
    motivo, nunca a pista mais parecida."""
    banco = BancoFalso(
        layouts=[interlagos()],
        gravacoes=[("g1", venue("protune_dlf", "Engine test"))],
    )
    resumo = resolver(banco)
    assert banco.resolvidas == {}
    assert "venue declarado nao e pista" in resumo.por_motivo


def test_irmaos_do_bundle_que_declaram_venues_diferentes_nao_resolvem(sem_gps) -> None:
    banco = BancoFalso(
        layouts=[interlagos(), ("goiania", "Goiania", "Goiania", None, None)],
        gravacoes=[
            (
                "g1",
                {
                    "aim_xrk.venue_declarado": "Interlagos",
                    "aim_gpk.venue_declarado": "Goiania",
                },
            )
        ],
    )
    resumo = resolver(banco)
    assert banco.resolvidas == {}
    assert "arquivos do bundle declaram venues diferentes" in resumo.por_motivo


def test_alias_novo_e_gravado_com_a_fonte_que_o_escreveu(sem_gps) -> None:
    """O mesmo apelido pode significar coisas diferentes vindo de exportadores
    diferentes, e por isso a chave e (alias, fonte)."""
    banco = BancoFalso(
        layouts=[interlagos()],
        gravacoes=[("g1", venue("aim_xrk", "Interlagos"))],
    )
    resolver(banco)
    assert banco.aliases_gravados == [("Interlagos", "interlagos_gp", "aim_xrk")]


# --- degrau 2: GPS -------------------------------------------------------


def test_raio_do_degrau_gps_e_de_cinco_quilometros() -> None:
    """PIL-RN-06, aprovada por Vitor em 2026-08-20 com base em espalhamento
    medido de 501 m e pista errada mais proxima a 318,8 km. O numero e da
    regra, nao de conveniencia do codigo."""
    assert RAIO_GPS_M == 5_000.0


def test_gps_dentro_do_raio_e_layout_unico_resolve_por_gps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PIL-CT-10. Sem venue declarado, a posicao mediana decide, desde que exista
    exatamente um layout no raio."""
    posicao = ao_norte(INTERLAGOS, 1_000.0)
    com_gps(monkeypatch, posicao)
    banco = BancoFalso(layouts=[interlagos()], gravacoes=[("g1", {})])
    resumo = resolver(banco)
    assert banco.resolvidas["g1"] == ("interlagos_gp", "gps")
    assert (resumo.resolvidas, resumo.por_gps) == (1, 1)


def test_4999_metros_resolve_e_5001_metros_nao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A borda dos 5,0 km e dura dos dois lados, ancorada em numero absoluto.

    As duas distancias sao literais, nao derivadas de RAIO_GPS_M. Uma versao
    anterior deste teste usava `RAIO_GPS_M - 1` e `RAIO_GPS_M + 1`, e por isso
    continuava verde quando o raio era mutado de 5 km para 8 km: o teste andava
    junto com a mutacao, e o que ele prometia no docstring nao era o que ele
    fazia.

    Os 5,0 km sao o valor aprovado por Vitor em 2026-08-20 (PIL-RN-06). Nenhum
    numero novo foi escolhido aqui.
    """
    dentro = ao_norte(INTERLAGOS, 4_999.0)
    fora = ao_norte(INTERLAGOS, 5_001.0)
    # A construcao do ponto e conferida com a funcao do proprio modulo, para a
    # distancia nao depender da aritmetica de quem escreveu o teste.
    assert _distancia_m(*dentro, *INTERLAGOS) == pytest.approx(4_999.0, abs=1.0)
    assert _distancia_m(*fora, *INTERLAGOS) == pytest.approx(5_001.0, abs=1.0)

    com_gps(monkeypatch, dentro)
    banco = BancoFalso(layouts=[interlagos()], gravacoes=[("g1", {})])
    resolver(banco)
    assert banco.resolvidas["g1"][1] == "gps"

    com_gps(monkeypatch, fora)
    banco = BancoFalso(layouts=[interlagos()], gravacoes=[("g2", {})])
    resolver(banco)
    assert banco.resolvidas == {}


def test_dois_layouts_no_raio_nao_decidem(monkeypatch: pytest.MonkeyPatch) -> None:
    """Duas referencias dentro do mesmo raio tornam o degrau ambiguo, e ambiguo
    aqui e nao resolvido, igual ao alias."""
    com_gps(monkeypatch, INTERLAGOS)
    vizinho = ao_norte(INTERLAGOS, 2_000.0)
    banco = BancoFalso(
        layouts=[
            interlagos(),
            ("interlagos_sem_s", "Interlagos sem S", "Interlagos", *vizinho),
        ],
        gravacoes=[("g1", {})],
    )
    resumo = resolver(banco)
    assert banco.resolvidas == {}
    assert any("ambiguo" in m for m in resumo.por_motivo)


def test_sem_venue_e_gps_longe_do_catalogo_fica_nao_resolvida(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PIL-CT-11. Arquivo que NAO declara venue e cujo GPS e coerente consigo
    mesmo mas cai a cerca de 9.570 km de toda referencia do catalogo. Nenhum
    setor sai dai.

    Este teste nao e o caso GT7: os 3 arquivos GT7 do acervo DECLARAM venue
    (ver o teste seguinte). Aqui o venue esta ausente de proposito, que e o
    unico jeito de o degrau GPS chegar a rodar.
    """
    com_gps(monkeypatch, DONINGTON)
    banco = BancoFalso(layouts=[interlagos()], gravacoes=[("g1", {})])
    resumo = resolver(banco)
    assert banco.resolvidas == {}
    assert resumo.nao_resolvidas == 1
    assert any("GPS longe" in m for m in resumo.por_motivo)


@pytest.mark.xfail(
    strict=True,
    reason="PIL-RN-17 nao implementada: perfil simulado ainda pode cair no degrau GPS "
    "e nao ha guarda de coerencia entre venue e GPS no degrau do alias; issue #10",
)
def test_venue_resolve_por_alias_mesmo_com_gps_em_outro_continente(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PIL-CT-56, excecao 5g do E-UC-01, no degrau que de fato decide.

    Caso real: os 3 arquivos GT7 do acervo declaram
    `venue_declarado = "Autodromo de Interlagos"` e trazem GPS georreferenciado
    em Donington Park (`src/saru_poc/readers/ld.py:29`). A distancia entre as
    duas coordenadas e de cerca de 9.570 km, medida com `_distancia_m` sobre as
    constantes deste teste. Os docstrings de `tracado.py:16` e
    `corte_voltas.py:288` arredondam para 9.500 km.

    O comportamento de hoje: o alias resolve, o `resolver` da `continue`, e o
    degrau GPS nunca roda. Para ESTES arquivos a pista escolhida esta certa (a
    distancia por volta da 4.217 m contra 4.309 m de Interlagos, e Donington tem
    4.020 m), entao recusar seria pior. O que falta e a etapa 4 DECLARAR que o
    nome e a posicao discordam, como `tracado.py` e `corte_voltas.py` ja fazem
    mais adiante. Enquanto a guarda nao existe, a divergencia passa em silencio,
    contra E-RNF-01.

    A guarda que falta tem regra desde 2026-09-13: PIL-RN-17, espelho do E-RN-08
    do nucleo, decidida por Vitor. Gravacao de perfil SIMULADO resolve a pista
    pelo que o jogo declara, nao entra no degrau GPS e nao grava alias novo a
    partir de posicao, porque a coordenada exportada por simulador e placeholder
    do exportador. O GT7 e perfil simulado (`acervo.SIMULADOS`, `acervo.py:104`,
    que alimenta a coluna `perfil_origem.simulado` em `acervo.py:243`), e
    `resolucao_pista.py` nao le essa coluna em lugar nenhum. Por isso a
    gravacao deste teste declara o perfil `gt7_ld`: quando a regra entrar, e por
    ele que o modulo vai saber que nao deve olhar GPS.

    O `xfail` e estrito de proposito: no dia em que a guarda entrar, este teste
    passa, o `xfail` vira erro, e quem implementou e obrigado a tirar o marcador
    e fechar a issue #10.
    """
    com_gps(monkeypatch, DONINGTON)
    banco = BancoFalso(
        layouts=[interlagos()],
        # `gt7_ld` e o perfil simulado do container .ld (`acervo.py:86`).
        gravacoes=[("g1", venue("gt7_ld", "Autodromo de Interlagos"))],
        aliases=[("Autodromo de Interlagos", "interlagos_gp")],
    )
    resumo = resolver(banco)
    # Isto ja vale hoje, e tem que continuar valendo: o jogo declarou o
    # circuito, e e o circuito declarado que vence (PIL-RN-17).
    assert banco.resolvidas["g1"] == ("interlagos_gp", "alias")
    # Isto e o que falta: a divergencia entre o nome e a posicao, declarada.
    assert any("gps" in m.lower() for m in resumo.por_motivo), (
        "resolveu por alias com o GPS a 9.570 km do layout, sem dizer nada"
    )


def test_degrau_gps_nao_ensina_alias_ao_catalogo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O nome declarado nao casou com o catalogo. Grava-lo como alias por causa
    de uma posicao contaminaria o degrau 1 com inferencia do degrau 2."""
    com_gps(monkeypatch, INTERLAGOS)
    banco = BancoFalso(
        layouts=[interlagos()],
        gravacoes=[("g1", venue("aim_xrk", "Pista que ninguem cadastrou"))],
    )
    resolver(banco)
    assert banco.resolvidas["g1"][1] == "gps"
    assert banco.aliases_gravados == []


def test_layout_sem_coordenada_de_referencia_nao_entra_no_degrau_gps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    com_gps(monkeypatch, INTERLAGOS)
    banco = BancoFalso(layouts=[interlagos(ref=None)], gravacoes=[("g1", {})])
    resolver(banco)
    assert banco.resolvidas == {}


def test_sem_nome_e_sem_posicao_conta_como_sem_venue(sem_gps) -> None:
    """Nem nome nem posicao nao e falha de resolucao: e captura que nao tem como
    ser resolvida, e o resumo separa as duas coisas."""
    banco = BancoFalso(layouts=[interlagos()], gravacoes=[("g1", {})])
    resumo = resolver(banco)
    assert (resumo.sem_venue, resumo.nao_resolvidas) == (1, 0)
    assert banco.resolvidas == {}
