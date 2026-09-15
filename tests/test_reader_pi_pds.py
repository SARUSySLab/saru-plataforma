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

from saru_poc.config import CONFIG
from saru_poc.readers import pi_pds as pi_pds_mod
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


#: Ordem da tabela das duas fixtures sinteticas: o gerador escreve os canais de
#: `_CANAIS` em `tests/fixtures/pi_pds_gerar_sintetico.py` com indice igual a
#: posicao na lista.
_ORDEM_FIXTURE = (
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
)


@pytest.fixture(autouse=True)
def ligacao_da_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    """As fixtures sinteticas nao tem assinatura medida no acervo: cada teste
    ganha a ligacao da ordem do gerador, e os testes da issue #54 a trocam."""
    monkeypatch.setattr(
        pi_pds_mod,
        "LIGACAO_MEDIDA",
        {frozenset(_ORDEM_FIXTURE): _ORDEM_FIXTURE},
    )


@pytest.fixture
def leitor() -> LeitorPiPds:
    return LeitorPiPds()


# ---------------------------------------------------------------------------
# caminho feliz na fixture sintetica
# ---------------------------------------------------------------------------


def test_formato_id_e_suporte_a_amostra(leitor: LeitorPiPds) -> None:
    assert leitor.formato_id == "pi_pds"
    assert leitor.suporta_amostra is False


def test_ler_levanta_not_implemented(leitor: LeitorPiPds) -> None:
    with pytest.raises(NotImplementedError):
        list(leitor.ler(FIXTURE_PDS))


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


def test_campo_de_indice_do_dicionario_nao_decide_o_nome(
    leitor: LeitorPiPds, tmp_path: Path
) -> None:
    """Issue #54: o inteiro no offset 544 do registro de dicionario nao e o
    indice da tabela. Mexer nele nao muda nome, taxa nem contagem de canal."""
    conteudo = bytearray(FIXTURE_PDS.read_bytes())
    off_indice_speed = (
        _OFF_DICIONARIO_FIXTURE + 1 * _ESTRIDE_DICIONARIO + _OFF_IDX_DICIONARIO
    )
    struct.pack_into("<i", conteudo, off_indice_speed, 0)
    mexido = tmp_path / "indice_do_dicionario_mexido.pds"
    mexido.write_bytes(bytes(conteudo))

    antes = {
        c.nome_bruto: c.frequencia_hz for c in leitor.inspecionar(FIXTURE_PDS).canais
    }
    depois = {c.nome_bruto: c.frequencia_hz for c in leitor.inspecionar(mexido).canais}
    assert depois == antes
    assert len(depois) == _N_CANAIS_FIXTURE


def test_nome_vem_da_ligacao_medida_pelo_indice_da_tabela(
    leitor: LeitorPiPds, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issue #54: com a ligacao trocando os dois primeiros indices, o bloco 0
    (100 Hz) passa a se chamar Speed e o bloco 1 (50 Hz), Steering."""
    trocada = ("Speed", "Steering", *_ORDEM_FIXTURE[2:])
    monkeypatch.setattr(
        pi_pds_mod, "LIGACAO_MEDIDA", {frozenset(_ORDEM_FIXTURE): trocada}
    )
    por_nome = {c.nome_bruto: c for c in leitor.inspecionar(FIXTURE_PDS).canais}
    assert por_nome["Speed"].frequencia_hz == 100.0
    assert por_nome["Steering"].frequencia_hz == 50.0


def test_bloco_sem_ligacao_medida_fica_fora_e_e_contado(
    leitor: LeitorPiPds, monkeypatch: pytest.MonkeyPatch
) -> None:
    sem_gear = tuple(None if n == "Gear" else n for n in _ORDEM_FIXTURE)
    monkeypatch.setattr(
        pi_pds_mod, "LIGACAO_MEDIDA", {frozenset(_ORDEM_FIXTURE): sem_gear}
    )
    cab = leitor.inspecionar(FIXTURE_PDS)
    assert "Gear" not in {c.nome_bruto for c in cab.canais}
    assert cab.bruto["n_blocos_sem_ligacao_medida"] == "1"


def test_dicionario_sem_ligacao_medida_levanta_erro(
    leitor: LeitorPiPds, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assinatura sem medicao nao recebe nome adivinhado (issue #54)."""
    monkeypatch.setattr(pi_pds_mod, "LIGACAO_MEDIDA", {})
    with pytest.raises(ErroDeLeitura, match="ligacao"):
        leitor.inspecionar(FIXTURE_PDS)


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


_PDS_F3_REAL = CONFIG.acervo_root / "F3/Geral/P.Piquet000977.pds"


@pytest.mark.skipif(
    not _PDS_F3_REAL.exists(), reason="P.Piquet000977.pds fora do acervo"
)
def test_pds_real_do_f3_bate_taxa_com_o_dat(monkeypatch: pytest.MonkeyPatch) -> None:
    """Issue #54: com a ligacao medida (sem a fixture automatica), nome e taxa
    batem com o `.dat` do Pi Toolbox da mesma sessao: `Speed` e `RPM` a 50 Hz,
    `Steering` e os amortecedores a 100 Hz. Antes, `Speed` saia a 20 Hz."""
    from saru_poc.readers import pi_pds_ligacao

    monkeypatch.setattr(pi_pds_mod, "LIGACAO_MEDIDA", pi_pds_ligacao.LIGACAO_MEDIDA)
    por_nome = {c.nome_bruto: c for c in LeitorPiPds().inspecionar(_PDS_F3_REAL).canais}
    assert por_nome["Speed"].frequencia_hz == 50.0
    assert por_nome["RPM"].frequencia_hz == 50.0
    assert por_nome["Steering"].frequencia_hz == 100.0
    assert por_nome["Damper FL"].frequencia_hz == 100.0
    assert por_nome["Acc Lat"].frequencia_hz == 50.0
