"""Testes do leitor Pi Toolbox `.pds` (`pi_pds`).

Caminho feliz contra a fixture sintetica versionada em
`tests/fixtures/pi_pds_sintetico.pds` (gerada por
`pi_pds_gerar_sintetico.py`), mais varredura contra o acervo real quando
montado nesta maquina. Nao versiona arquivo real: tem nome de piloto real,
e o formato mistura pelo menos dois layouts internos distintos (ver
docstring de `pi_pds.py`), so um deles decifrado.
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from saru_poc.readers.base import Cabecalho, ErroDeLeitura
from saru_poc.readers.pi_pds import LeitorPiPds

FIXTURES = Path(__file__).parent / "fixtures"
FIXTURE_PDS = FIXTURES / "pi_pds_sintetico.pds"
FIXTURE_PDS_992 = FIXTURES / "pi_pds_sintetico_992.pds"

_OFF_MAGIC = 4
_ESTRIDE_DICIONARIO = 552
_OFF_IDX_DICIONARIO = 544
_TAMANHO_REGISTRO_TABELA = 64
_N_CANAIS_FIXTURE = 10
_OFF_DICIONARIO_FIXTURE = 4096 + 8 * sum(
    round(t * 2.0) for t in (100, 50, 20, 100, 10, 1, 1, 25, 5, 5)
)


@pytest.fixture
def leitor() -> LeitorPiPds:
    return LeitorPiPds()


# ---------------------------------------------------------------------------
# caminho feliz na fixture sintetica
# ---------------------------------------------------------------------------


def test_formato_id_e_suporte_a_amostra(leitor: LeitorPiPds) -> None:
    assert leitor.formato_id == "pi_pds"
    assert leitor.suporta_amostra is True


def test_ler_emite_lotes_em_streaming(leitor: LeitorPiPds) -> None:
    lotes = list(leitor.ler(FIXTURE_PDS))
    assert len(lotes) == 7
    taxas = {l.frequencia_hz for l in lotes}
    assert taxas == {1.0, 5.0, 10.0, 20.0, 25.0, 50.0, 100.0}
    for lote in lotes:
        assert "t_s" in lote.tabela.schema.names
        assert lote.tabela.num_rows > 0


def test_fixture_caminho_feliz(leitor: LeitorPiPds) -> None:
    cab = leitor.inspecionar(FIXTURE_PDS)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "pi_pds"
    assert len(cab.canais) == _N_CANAIS_FIXTURE
    assert cab.duracao_s == pytest.approx(2.0)
    assert cab.venue_declarado is None
    assert cab.capturado_em is None
    assert cab.bruto["n_canais_dicionario"] == "10"
    assert cab.bruto["n_canais_com_dado"] == "10"
    assert cab.bruto["n_canais_sem_dado"] == "0"

    nomes = {c.nome_bruto for c in cab.canais}
    assert nomes == {
        "Steering",
        "Speed",
        "Throttle Position",
        "RPM",
        "Water Temp",
        "Gear",
        "Beacon Code",
        "Lambda",
        "Fuel Pressure",
        "Oil Pressure",
    }
    assert cab.taxas == (1.0, 5.0, 10.0, 20.0, 25.0, 50.0, 100.0)


def test_unidade_e_frequencia_por_canal(leitor: LeitorPiPds) -> None:
    cab = leitor.inspecionar(FIXTURE_PDS)
    por_nome = {c.nome_bruto: c for c in cab.canais}

    assert por_nome["Steering"].unidade_declarada == "mm"
    assert por_nome["Steering"].frequencia_hz == 100.0
    assert por_nome["Steering"].n_amostras == 200

    assert por_nome["Speed"].unidade_declarada == "kph"
    assert por_nome["Speed"].frequencia_hz == 50.0

    # Canal com unidade vazia no arquivo real vira None, nunca string vazia.
    assert por_nome["Gear"].unidade_declarada is None


def test_valor_min_max_nao_preenchidos(leitor: LeitorPiPds) -> None:
    """Ao contrario do `.pid`, o dicionario do `.pds` nao declara faixa de
    fabrica em nenhum campo decifrado: `valor_min`/`valor_max` ficam None,
    mesma postura do `.dat` LISTHEAD pra faixa nao medida."""
    cab = leitor.inspecionar(FIXTURE_PDS)
    steering = next(c for c in cab.canais if c.nome_bruto == "Steering")
    assert steering.valor_min is None
    assert steering.valor_max is None


# ---------------------------------------------------------------------------
# erros
# ---------------------------------------------------------------------------


def test_magic_invalido_levanta_erro_de_leitura(
    leitor: LeitorPiPds, tmp_path: Path
) -> None:
    ruim = tmp_path / "ruim.pds"
    conteudo = bytearray(FIXTURE_PDS.read_bytes())
    conteudo[_OFF_MAGIC : _OFF_MAGIC + 4] = b"XXXX"
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="magic"):
        leitor.inspecionar(ruim)


def test_arquivo_menor_que_magic_levanta_erro_de_leitura(
    leitor: LeitorPiPds, tmp_path: Path
) -> None:
    curto = tmp_path / "curto.pds"
    curto.write_bytes(FIXTURE_PDS.read_bytes()[:4])

    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(curto)


def test_arquivo_sem_dicionario_levanta_erro_de_leitura(
    leitor: LeitorPiPds, tmp_path: Path
) -> None:
    """Arquivo com magic valido mas sem estrutura de dicionario reconhecivel
    (regressao do B2: nunca devolver inventario vazio calado)."""
    so_cabecalho = tmp_path / "so_cabecalho.pds"
    conteudo = bytearray(64)
    conteudo[_OFF_MAGIC : _OFF_MAGIC + 4] = b"\x1a\x12\x40\xf7"
    so_cabecalho.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="dicionario"):
        leitor.inspecionar(so_cabecalho)


def test_indice_duplicado_no_dicionario_exclui_os_dois_canais(
    leitor: LeitorPiPds, tmp_path: Path
) -> None:
    """Regressao do B2: quando dois registros do dicionario declaram o
    mesmo indice com nomes diferentes (medido no acervo real: canal sem
    dado grava indice 0 em vez de ficar de fora), nenhum dos dois pode
    entrar no inventario por adivinhacao de qual e o certo."""
    conteudo = bytearray(FIXTURE_PDS.read_bytes())
    # Faz o segundo registro (Speed, indice 1) declarar indice 0, colidindo
    # com o primeiro (Steering).
    off_indice_speed = (
        _OFF_DICIONARIO_FIXTURE + 1 * _ESTRIDE_DICIONARIO + _OFF_IDX_DICIONARIO
    )
    struct.pack_into("<i", conteudo, off_indice_speed, 0)
    ambiguo = tmp_path / "indice_ambiguo.pds"
    ambiguo.write_bytes(bytes(conteudo))

    cab = leitor.inspecionar(ambiguo)
    nomes = {c.nome_bruto for c in cab.canais}
    assert "Steering" not in nomes
    assert "Speed" not in nomes
    assert len(cab.canais) == _N_CANAIS_FIXTURE - 2


def test_invariante_de_offset_quebrada_levanta_erro_de_leitura(
    leitor: LeitorPiPds, tmp_path: Path
) -> None:
    """Regressao do B2: se dois blocos consecutivos (em ordem de offset) se
    sobrepoem, decodificamos campo errado, e o arquivo inteiro tem que ser
    rejeitado (mesma postura da soma de bytes por bloco do `pi_pid`)."""
    conteudo = bytearray(FIXTURE_PDS.read_bytes())
    offset_tabela = _OFF_DICIONARIO_FIXTURE + _N_CANAIS_FIXTURE * _ESTRIDE_DICIONARIO
    # Faz o segundo bloco comecar 8 B depois do primeiro (que tem 200
    # amostras): sobreposicao.
    off_byte_offset_2o_registro = offset_tabela + 1 * _TAMANHO_REGISTRO_TABELA + 48
    struct.pack_into("<i", conteudo, off_byte_offset_2o_registro, 4096 + 8)
    quebrado = tmp_path / "invariante_quebrada.pds"
    quebrado.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="sobrepostos"):
        leitor.inspecionar(quebrado)


# ---------------------------------------------------------------------------
# layout do 992.1 (issue #25): varios blocos por canal, amostra de 1, 2 ou 4 B,
# tabela fora de ordem, campo 56 como numero de serie
# ---------------------------------------------------------------------------


def test_layout_992_varios_blocos_por_canal(leitor: LeitorPiPds) -> None:
    cab = leitor.inspecionar(FIXTURE_PDS_992)
    por_nome = {c.nome_bruto: c for c in cab.canais}

    assert len(cab.canais) == _N_CANAIS_FIXTURE
    assert cab.bruto["n_registros_tabela"] == "13"
    assert cab.bruto["n_pares_fechados"] == "11"
    assert cab.bruto["n_buracos"] == "1"
    # Dois blocos de 100 amostras somam as 200 de 2,0 s a 100 Hz.
    assert por_nome["Steering"].n_amostras == 200
    assert por_nome["Steering"].frequencia_hz == 100.0
    # Um bloco de 1 B por amostra (canal discreto) le igual ao de 4 B.
    assert por_nome["Gear"].n_amostras == 2
    assert cab.duracao_s == pytest.approx(2.0)


def test_layout_992_intervalo_diferente_entre_blocos_levanta_erro(
    leitor: LeitorPiPds, tmp_path: Path
) -> None:
    """Dois blocos do mesmo canal com intervalos diferentes: o leitor nao
    escolhe a frequencia por ele."""
    conteudo = bytearray(FIXTURE_PDS_992.read_bytes())
    offset_tabela = int(leitor.inspecionar(FIXTURE_PDS_992).bruto["offset_tabela"])
    # O segundo registro da tabela embaralhada e o primeiro bloco do canal 0
    # (Steering, 100 Hz): troca o intervalo pra 50 Hz.
    registro = offset_tabela + 1 * _TAMANHO_REGISTRO_TABELA
    assert struct.unpack_from("<i", conteudo, registro)[0] == 0
    struct.pack_into("<i", conteudo, registro + 16, 200_000)
    quebrado = tmp_path / "intervalo_diferente.pds"
    quebrado.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="intervalos diferentes"):
        leitor.inspecionar(quebrado)


# ---------------------------------------------------------------------------
# varredura do acervo real, quando montado nesta maquina
# ---------------------------------------------------------------------------

_ACERVO = Path.home() / "Desktop/trabalho/clientes/saru/dados_telemetria"


@pytest.mark.skipif(
    not _ACERVO.exists(), reason="acervo real nao montado nesta maquina"
)
def test_acervo_real_le_pelo_menos_metade_dos_pds(leitor: LeitorPiPds) -> None:
    """Nao e caminho feliz 100%: o formato mistura pelo menos dois layouts
    internos e alguns arquivos concatenam varias capturas (ver docstring de
    `pi_pds.py`). O teto aqui e uma regressao-guarda, nao uma promessa de
    suporte total."""
    arquivos = sorted(_ACERVO.rglob("*.pds"))
    assert arquivos, "acervo montado mas sem nenhum .pds, algo mudou"

    ok = 0
    for caminho in arquivos:
        try:
            cab = leitor.inspecionar(caminho)
        except ErroDeLeitura:
            continue
        assert len(cab.canais) > 0
        ok += 1

    assert ok >= len(arquivos) // 2, (
        f"so {ok}/{len(arquivos)} arquivos .pds do acervo real leram: "
        "regressao no layout de 552 B (ver docstring do modulo)"
    )
