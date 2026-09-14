"""Testes do leitor Pro Tune TDL .dlf (formato_id protune_dlf).

Fixture sintetica em `tests/fixtures/dlf_esparso.dlf` exercita o caminho
feliz do corpo esparso (keyframe + salto por letra simples e o salto `F`
usado no proprio exemplo do enunciado, mais um caso de letra dupla). O
arquivo real do acervo (`amg_cup_a45.dlf`, 1 arquivo so) e testado a parte,
com `pytest.skip` quando o acervo nao esta montado nesta maquina: nao
versionamos arquivo real, tem nome de piloto real.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers.base import Cabecalho, ErroDeLeitura, Lote
from saru_poc.readers.dlf import LeitorDlf, _avanco

FIXTURE = Path(__file__).parent / "fixtures" / "dlf_esparso.dlf"
ARQUIVO_REAL = CONFIG.acervo_root / "telemetria" / "samples-saru" / "amg_cup_a45.dlf"


@pytest.fixture
def leitor() -> LeitorDlf:
    return LeitorDlf()


# ---------------------------------------------------------------------------
# Contrato basico
# ---------------------------------------------------------------------------


def test_formato_id_e_suporte_a_amostra(leitor: LeitorDlf) -> None:
    assert leitor.formato_id == "protune_dlf"
    assert leitor.suporta_amostra is True


# ---------------------------------------------------------------------------
# Salto por letra (_avanco)
# ---------------------------------------------------------------------------


def test_avanco_letra_simples() -> None:
    assert _avanco("A") == 1
    assert _avanco("F") == 6
    assert _avanco("Z") == 26


def test_avanco_sem_separador_e_1() -> None:
    """Fim de linha sem letra: mesma regra do primeiro valor, avanca 1."""
    assert _avanco("") == 1


def test_avanco_letra_dupla() -> None:
    # 26 * (2-1) + (B - A + 1) = 26 + 2 = 28
    assert _avanco("AB") == 28
    # ZZ = 26*(2-1) + 26 = 52
    assert _avanco("ZZ") == 52


# ---------------------------------------------------------------------------
# Fixture sintetica
# ---------------------------------------------------------------------------


def test_fixture_caminho_feliz(leitor: LeitorDlf) -> None:
    cab = leitor.inspecionar(FIXTURE)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "protune_dlf"
    assert len(cab.canais) == 10
    assert cab.venue_declarado is None
    assert cab.bruto["numero_serie"] == "000000000000001"
    assert cab.bruto["n_linhas_dado"] == "4"


def test_fixture_keyframe_escreve_todos_os_canais(leitor: LeitorDlf) -> None:
    """A primeira linha (keyframe, todos os separadores 'A') tem que
    contribuir uma escrita pra cada um dos 10 canais declarados."""
    cab = leitor.inspecionar(FIXTURE)
    por_nome = {c.nome_bruto: c for c in cab.canais}
    for nome in (
        "Datalog Time",
        "Chan A",
        "Chan B",
        "Chan C",
        "Chan D",
        "Chan E",
        "Chan F",
        "Chan G",
        "GPS Latitude",
        "Chan I",
    ):
        assert nome in por_nome, nome
        assert por_nome[nome].n_amostras >= 1


def test_fixture_salto_f_pousa_no_canal_certo(leitor: LeitorDlf) -> None:
    """Reproduz o exemplo do enunciado: `...0,124F-23,703465A...` pula 6
    posicoes e pousa exatamente em `GPS Latitude` (indice 8), que por isso
    e escrito 2x (keyframe + esta linha) em vez de 1x como os canais de
    enchimento entre ele e o inicio da linha."""
    cab = leitor.inspecionar(FIXTURE)
    por_nome = {c.nome_bruto: c for c in cab.canais}
    assert por_nome["GPS Latitude"].n_amostras == 2
    # canais de enchimento (Chan C a Chan G) so aparecem no keyframe.
    for nome in ("Chan C", "Chan D", "Chan E", "Chan F", "Chan G", "Chan I"):
        assert por_nome[nome].n_amostras == 1


def test_fixture_letra_dupla_nao_quebra_a_leitura(leitor: LeitorDlf) -> None:
    """A linha `0,100AB` usa separador de letra dupla (salto de 28) que
    estoura o numero de canais da fixture: tem que ser ignorado em silencio
    (sem IndexError, sem contar amostra em canal que nao existe), nao travar
    a leitura das linhas seguintes."""
    cab = leitor.inspecionar(FIXTURE)
    por_nome = {c.nome_bruto: c for c in cab.canais}
    # linha seguinte (0,150A1,600A) foi lida normalmente: Datalog Time e
    # Chan A ganham mais uma escrita cada.
    assert por_nome["Datalog Time"].n_amostras == 4
    assert por_nome["Chan A"].n_amostras == 3


def test_fixture_duracao_vem_do_ultimo_datalog_time(leitor: LeitorDlf) -> None:
    cab = leitor.inspecionar(FIXTURE)
    assert cab.duracao_s == pytest.approx(0.150)


def test_fixture_unidade_declarada(leitor: LeitorDlf) -> None:
    cab = leitor.inspecionar(FIXTURE)
    por_nome = {c.nome_bruto: c for c in cab.canais}
    assert por_nome["GPS Latitude"].unidade_declarada == "deg"
    assert por_nome["Datalog Time"].unidade_declarada == "sec"


# ---------------------------------------------------------------------------
# Invariantes
# ---------------------------------------------------------------------------


def test_invariantes_taxa_positiva_e_nome_nao_vazio(leitor: LeitorDlf) -> None:
    cab = leitor.inspecionar(FIXTURE)
    for c in cab.canais:
        assert c.frequencia_hz > 0
        assert c.nome_bruto


# ---------------------------------------------------------------------------
# Malformado
# ---------------------------------------------------------------------------


def test_sem_datastart_levanta_erro(tmp_path: Path, leitor: LeitorDlf) -> None:
    ruim = tmp_path / "sem_datastart.dlf"
    ruim.write_text("#V2\r\n#SERIALNUMBER 1\r\n#MAINCOMMENT\r\n", encoding="latin-1")
    with pytest.raises(ErroDeLeitura, match="DATASTART"):
        leitor.inspecionar(ruim)


def test_datastart_sem_linhas_de_canal_levanta_erro(
    tmp_path: Path, leitor: LeitorDlf
) -> None:
    ruim = tmp_path / "datastart_vazio.dlf"
    ruim.write_text("#V2\r\n#DATASTART\r\n", encoding="latin-1")
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(ruim)


def test_sem_linha_de_dado_levanta_erro(tmp_path: Path, leitor: LeitorDlf) -> None:
    ruim = tmp_path / "sem_dado.dlf"
    ruim.write_text(
        "#V2\r\n#DATASTART\r\nDatalog Time;Chan A;\r\nsec;u1;\r\n",
        encoding="latin-1",
    )
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(ruim)


def test_arquivo_inexistente_levanta_erro(tmp_path: Path, leitor: LeitorDlf) -> None:
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(tmp_path / "nao_existe.dlf")


# ---------------------------------------------------------------------------
# Acervo real (o unico .dlf que a maquina tem)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not ARQUIVO_REAL.exists(), reason="acervo nao montado nesta maquina"
)
def test_le_arquivo_real_do_acervo(leitor: LeitorDlf) -> None:
    cab = leitor.inspecionar(ARQUIVO_REAL)
    assert cab.formato_id == "protune_dlf"
    assert cab.venue_declarado is None
    # 138 canais declarados no cabecalho (o 139o campo, vazio pelo `;`
    # final, e filtrado).
    assert len(cab.canais) <= 138
    assert cab.bruto["n_canais_declarados"] == "138"
    assert cab.duracao_s is not None
    assert cab.duracao_s == pytest.approx(4269.4, abs=1.0)

    por_nome = {c.nome_bruto: c for c in cab.canais}
    # Taxas medidas no enunciado (contagem de escrita real / duracao),
    # tolerancia generosa pra nao acoplar no ultimo digito.
    esperado = {
        "Datalog Time": 20.00,
        "Accel Longitudinal Y": 19.80,
        "Gyro Accel Vertical Z": 13.02,
        "Engine RPM": 18.19,
        "GPS Latitude": 8.06,
        "Lap Distance": 8.85,
        "Vehicle Speed": 1.92,
        "Gear Position": 0.22,
        "Engine Temperature": 0.13,
    }
    for nome, hz in esperado.items():
        assert nome in por_nome, nome
        assert por_nome[nome].frequencia_hz == pytest.approx(hz, abs=0.05), nome

    for c in cab.canais:
        assert c.frequencia_hz > 0
        assert c.nome_bruto


# ---------------------------------------------------------------------------
# Desambiguacao de nome_bruto duplicado
# ---------------------------------------------------------------------------


def test_desambigua_nomes_sufixa_so_repetido() -> None:
    from saru_poc.readers.dlf import _desambigua_nomes

    assert _desambigua_nomes(["Chan A", "N/A", "Chan B", "N/A"]) == [
        "Chan A",
        "N/A#1",
        "Chan B",
        "N/A#3",
    ]


def test_desambigua_nomes_sem_repeticao_fica_intacto() -> None:
    from saru_poc.readers.dlf import _desambigua_nomes

    assert _desambigua_nomes(["a", "b", "c"]) == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# ler()
# ---------------------------------------------------------------------------


def test_ler_fixture_devolve_um_lote_na_taxa_da_grade(leitor: LeitorDlf) -> None:
    lotes = list(leitor.ler(FIXTURE))
    assert len(lotes) == 1
    lote = lotes[0]
    assert isinstance(lote, Lote)
    # taxa da grade == frequencia medida de Datalog Time no inspecionar()
    cab = leitor.inspecionar(FIXTURE)
    freq_datalog = next(
        c.frequencia_hz for c in cab.canais if c.nome_bruto == "Datalog Time"
    )
    assert lote.frequencia_hz == pytest.approx(freq_datalog)
    assert lote.tabela.num_rows == 4  # 4 linhas de dado na fixture


def test_ler_fixture_uma_coluna_por_canal_com_amostra(leitor: LeitorDlf) -> None:
    cab = leitor.inspecionar(FIXTURE)
    lote = next(leitor.ler(FIXTURE))
    nomes_colunas = set(lote.tabela.schema.names)
    assert "t_s" in nomes_colunas
    for c in cab.canais:
        assert c.nome_bruto in nomes_colunas


def test_ler_fixture_t_s_vem_direto_do_datalog_time(leitor: LeitorDlf) -> None:
    """t_s = o proprio Datalog Time da linha, sem acumulo: as 4 linhas da
    fixture tem Datalog Time 0.000, 0.035, 0.100, 0.150."""
    lote = next(leitor.ler(FIXTURE))
    t_s = lote.tabela.column("t_s").to_pylist()
    assert t_s == pytest.approx([0.000, 0.035, 0.100, 0.150])
    # e igual a coluna Datalog Time gravada como canal
    assert lote.tabela.column("Datalog Time").to_pylist() == pytest.approx(t_s)


def test_ler_fixture_keyframe_sem_nan_linhas_seguintes_com_nan(
    leitor: LeitorDlf,
) -> None:
    """Linha 0 (keyframe) escreve todos os canais: sem NaN. Canais de
    enchimento (Chan C a G, Chan I) so aparecem na linha 0: NaN nas linhas
    1 a 3, nunca com o valor da linha anterior repetido."""
    lote = next(leitor.ler(FIXTURE))
    for nome in ("Chan C", "Chan D", "Chan E", "Chan F", "Chan G", "Chan I"):
        col = lote.tabela.column(nome).to_pylist()
        assert not math.isnan(col[0]), nome
        for v in col[1:]:
            assert math.isnan(v), nome


def test_ler_fixture_gps_latitude_escrita_2x_resto_nan(leitor: LeitorDlf) -> None:
    """GPS Latitude e escrita na linha 0 (keyframe) e na linha 1 (salto F
    do exemplo do enunciado): as linhas 2 e 3 ficam NaN, nao repetem o
    ultimo valor conhecido (-23.7)."""
    lote = next(leitor.ler(FIXTURE))
    col = lote.tabela.column("GPS Latitude").to_pylist()
    assert col[0] == pytest.approx(-23.700000)
    assert col[1] == pytest.approx(-23.703465)
    assert math.isnan(col[2])
    assert math.isnan(col[3])


def test_ler_fixture_chan_a_nao_escrita_na_linha_da_letra_dupla(
    leitor: LeitorDlf,
) -> None:
    """Linha 2 (`0,100AB`) so escreve Datalog Time (o salto de letra dupla
    estoura o numero de canais da fixture): Chan A fica NaN nessa linha
    especifica, mesmo tendo sido escrita nas linhas 0, 1 e 3."""
    lote = next(leitor.ler(FIXTURE))
    col = lote.tabela.column("Chan A").to_pylist()
    assert not math.isnan(col[0])
    assert not math.isnan(col[1])
    assert math.isnan(col[2])
    assert not math.isnan(col[3])


def test_ler_fixture_todas_colunas_sao_float64(leitor: LeitorDlf) -> None:
    lote = next(leitor.ler(FIXTURE))
    for nome in lote.tabela.schema.names:
        assert str(lote.tabela.schema.field(nome).type) == "double"


def test_ler_arquivo_sem_datalog_time_levanta_erro(
    tmp_path: Path, leitor: LeitorDlf
) -> None:
    ruim = tmp_path / "sem_time.dlf"
    ruim.write_text(
        "#V2\r\n#DATASTART\r\nChan A;Chan B;\r\nu1;u2;\r\n1,000A2,000A\r\n",
        encoding="latin-1",
    )
    with pytest.raises(ErroDeLeitura):
        list(leitor.ler(ruim))


# ---------------------------------------------------------------------------
# ler() - acervo real (o unico .dlf que a maquina tem)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not ARQUIVO_REAL.exists(), reason="acervo nao montado nesta maquina"
)
def test_ler_arquivo_real_um_lote_por_taxa_bate_linhas_totais(
    leitor: LeitorDlf,
) -> None:
    """Decisao (a): 1 taxa so (a grade), entao total de linhas somado nos
    lotes tem que bater com n_linhas_dado que inspecionar() ja contou."""
    cab = leitor.inspecionar(ARQUIVO_REAL)
    lotes = list(leitor.ler(ARQUIVO_REAL))
    taxas = {lote.frequencia_hz for lote in lotes}
    assert len(taxas) == 1, "decisao (a) e uma taxa so (a grade)"
    total_linhas = sum(lote.tabela.num_rows for lote in lotes)
    assert total_linhas == int(cab.bruto["n_linhas_dado"])


@pytest.mark.skipif(
    not ARQUIVO_REAL.exists(), reason="acervo nao montado nesta maquina"
)
def test_ler_arquivo_real_contagem_nao_nan_bate_com_n_amostras(
    leitor: LeitorDlf,
) -> None:
    """Pra uma amostra de canais (rapido + lento), a contagem de celulas
    NAO-NaN no Lote tem que bater com o n_amostras que inspecionar() ja
    contou (escrita real), nao com o total de linhas da grade."""
    cab = leitor.inspecionar(ARQUIVO_REAL)
    por_nome = {c.nome_bruto: c for c in cab.canais}
    lotes = list(leitor.ler(ARQUIVO_REAL))

    contagem_nao_nan: dict[str, int] = dict.fromkeys(por_nome, 0)
    for lote in lotes:
        for nome in ("Datalog Time", "Vehicle Speed", "Gear Position"):
            col = lote.tabela.column(nome).to_pylist()
            contagem_nao_nan[nome] += sum(1 for v in col if not math.isnan(v))

    for nome in ("Datalog Time", "Vehicle Speed", "Gear Position"):
        assert contagem_nao_nan[nome] == por_nome[nome].n_amostras, nome


@pytest.mark.skipif(
    not ARQUIVO_REAL.exists(), reason="acervo nao montado nesta maquina"
)
def test_ler_arquivo_real_desambigua_canais_n_a(leitor: LeitorDlf) -> None:
    """138 canais declarados, 20 deles literalmente "N/A" no cabecalho
    (medido): tem que sair como colunas distintas (sufixadas por posicao),
    nunca colidir em uma coluna so."""
    cab = leitor.inspecionar(ARQUIVO_REAL)
    nomes_na = [c.nome_bruto for c in cab.canais if c.nome_bruto.startswith("N/A")]
    assert len(nomes_na) == 20
    assert len(set(nomes_na)) == 20  # todos unicos, nenhuma colisao

    lote = next(leitor.ler(ARQUIVO_REAL))
    nomes_colunas = set(lote.tabela.schema.names)
    for nome in nomes_na:
        assert nome in nomes_colunas
