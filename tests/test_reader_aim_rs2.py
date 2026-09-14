"""Testes do leitor AiM RaceStudio 2 (`.drk`/`.bak`, formato_id `aim_drk`).

Caminho feliz e degradacoes contra fixtures sinteticas versionadas em
`tests/fixtures/aim_rs2_*.drk` (geradas por
`tests/fixtures/gerar_aim_rs2_sintetico.py`), mais varredura de sanidade
contra o acervo real quando ele estiver montado nesta maquina. Nao versiona
arquivo real do acervo: tem nome de piloto real.

`.gpk` (`aim_gpk`) e `.rrk` (`aim_rrk`) nao tem leitor neste modulo: a
medicao (`docs/aim-rs2-medicao.md`) nao achou estrutura decodificavel neles
com confianca suficiente. Nao ha teste de caminho feliz pra eles aqui
porque nao ha o que testar.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers.aim_rs2 import LeitorAimDrk
from saru_poc.readers.base import Cabecalho, ErroDeLeitura

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def leitor() -> LeitorAimDrk:
    return LeitorAimDrk()


def _todos_do_acervo() -> list[Path]:
    if not CONFIG.acervo_root.exists():
        return []
    drk = list(CONFIG.acervo_root.rglob("*.drk"))
    bak = list(CONFIG.acervo_root.rglob("*.bak"))
    return sorted(drk + bak)


# ---------------------------------------------------------------------------
# Fixtures sinteticas
# ---------------------------------------------------------------------------


def test_formato_id_e_suporte_a_amostra(leitor: LeitorAimDrk) -> None:
    assert leitor.formato_id == "aim_drk"
    assert leitor.suporta_amostra is False


def test_ler_levanta_not_implemented(leitor: LeitorAimDrk) -> None:
    with pytest.raises(NotImplementedError):
        list(leitor.ler(FIXTURES / "aim_rs2_completo.drk"))


def test_nunca_tem_canal(leitor: LeitorAimDrk) -> None:
    """A tabela de descritores de 288 bytes em 0x800 nao decodifica em
    nenhum arquivo medido (ver docstring de aim_rs2.py). canais e sempre
    tupla vazia, o mesmo padrao do sidecar motec_ldx.
    """
    cab = leitor.inspecionar(FIXTURES / "aim_rs2_completo.drk")
    assert cab.canais == ()
    assert cab.taxas == ()


def test_caminho_feliz_extrai_metadado(leitor: LeitorAimDrk) -> None:
    cab = leitor.inspecionar(FIXTURES / "aim_rs2_completo.drk")

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "aim_drk"
    assert cab.venue_declarado == "Autodromo Fixture"
    assert cab.capturado_em == "2021-01-25T08:39:16"
    assert cab.bruto["piloto"] == "Piloto Sintetico"
    assert cab.bruto["veiculo"] == "F309-016 Fixture"
    assert cab.bruto["capturado_em_bruto"] == "25-01-21 08:39:16"
    assert cab.bruto["capturado_em_seculo"] == "inferido (20xx, ano de 2 digitos)"
    assert cab.duracao_s is None


def test_variante_pobre_e_cabecalho_legitimo_sem_excecao(
    leitor: LeitorAimDrk,
) -> None:
    """Medido em 4 dos 129 arquivos reais (`Test.drk`, `Test #1.drk`,
    `WarmUp.drk`, `81214006.drk`): magic `RD\\x90\\x01`/`RD\\xf4\\x01`, os 4
    campos de metadado existem mas vazios. Nao e falha de leitura.
    """
    cab = leitor.inspecionar(FIXTURES / "aim_rs2_variante_pobre.drk")
    assert cab.canais == ()
    assert cab.venue_declarado is None
    assert cab.capturado_em is None
    assert cab.bruto["piloto"] == ""
    assert cab.bruto["veiculo"] == ""


def test_arquivo_curto_demais_levanta_erro(leitor: LeitorAimDrk) -> None:
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(FIXTURES / "aim_rs2_curto_demais.drk")


def test_lixo_binario_no_campo_vira_none_nao_string_lixo(
    leitor: LeitorAimDrk,
) -> None:
    """Byte fora do intervalo ASCII imprimivel prova que o offset caiu em
    dado binario, nao texto. O campo tem que virar None: decodificar lixo
    como nome/piloto e o erro que o leitor de referencia (drk_file.py)
    cometia com nomes de canal como `'°'` ou `'y'`.
    """
    cab = leitor.inspecionar(FIXTURES / "aim_rs2_lixo_no_campo.drk")
    assert "piloto" in cab.bruto
    assert cab.bruto["piloto"] == ""
    assert cab.venue_declarado == "Autodromo Fixture"


def test_data_fora_do_formato_nao_inventa_iso(leitor: LeitorAimDrk) -> None:
    cab = leitor.inspecionar(FIXTURES / "aim_rs2_data_invalida.drk")
    assert cab.capturado_em is None
    assert cab.bruto["capturado_em_bruto"] == "data-quebrada"
    assert "capturado_em_seculo" not in cab.bruto


def test_bak_e_o_mesmo_leitor_por_extensao(
    tmp_path: Path, leitor: LeitorAimDrk
) -> None:
    """`.bak` e alias de extensao do mesmo formato `aim_drk` (ver
    formatos.py): o leitor nao decide por extensao, so pelo conteudo.
    """
    origem = FIXTURES / "aim_rs2_completo.drk"
    copia_bak = tmp_path / "sessao.bak"
    copia_bak.write_bytes(origem.read_bytes())

    cab = leitor.inspecionar(copia_bak)
    assert cab.bruto["piloto"] == "Piloto Sintetico"


# ---------------------------------------------------------------------------
# Sanidade contra o acervo real (so roda se o acervo estiver montado)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
def test_acervo_nao_quebra_e_taxa_de_metadado_condiz_com_a_medicao() -> None:
    """Nao cobra numero exato (o acervo muda), so a faixa medida em
    2026-08-29: nenhum arquivo real levanta excecao nao tratada, e a maioria
    tem pelo menos o venue ou o piloto preenchido (variante `RDX\\x02`).
    """
    arquivos = _todos_do_acervo()
    leitor = LeitorAimDrk()
    com_metadado = 0
    for caminho in arquivos:
        cab = leitor.inspecionar(caminho)
        assert cab.canais == ()
        if cab.venue_declarado or cab.bruto.get("piloto"):
            com_metadado += 1

    proporcao = com_metadado / len(arquivos)
    # medido: 125/129 = 0.97. Deixa folga pro acervo crescer sem quebrar CI.
    assert proporcao > 0.8


# ---------------------------------------------------------------------------
# Tabela de voltas do indice (29/08)
# ---------------------------------------------------------------------------


def _drk_com_tabela(tmp_path: Path, duracoes_ms: list[int], off_tabela: int = 4096) -> Path:
    """Monta um `.drk` sintetico: cabecalho minimo + tabela de voltas no
    layout medido (registros de 288 bytes: contador em +0, acumulado em
    +272, duracao em +276)."""
    import struct

    corpo = bytearray(off_tabela + 288 * (len(duracoes_ms) + 1))
    acumulado = 0
    for k, dur in enumerate(duracoes_ms):
        base = off_tabela + k * 288
        struct.pack_into("<i", corpo, base, k)
        struct.pack_into("<i", corpo, base + 272, acumulado)
        struct.pack_into("<i", corpo, base + 276, dur)
        acumulado += dur
    caminho = tmp_path / "sintetico.drk"
    caminho.write_bytes(bytes(corpo))
    return caminho


def test_tabela_de_voltas_vira_passagens_sem_a_ultima(
    tmp_path: Path, leitor: LeitorAimDrk
) -> None:
    """3 registros = 3 inicios confirmados por beacon = 2 voltas fechadas.
    O fim do ultimo registro fecha no desligamento do logger, nao num
    beacon (medido contra o .xrk irmao em 45 pares do acervo, prefixo
    exato em todos), entao ele NAO vira passagem."""
    cab = leitor.inspecionar(_drk_com_tabela(tmp_path, [95_000, 96_500, 94_000]))
    assert cab.bruto["lap_beacons_ms"] == "0,95000,191500"
    assert cab.bruto["lap_registros"] == "3"
    assert "desligamento" in cab.bruto["lap_ultimo_descartado"]


def test_registro_unico_nao_declara_beacon(tmp_path: Path, leitor: LeitorAimDrk) -> None:
    """Sessao de volta unica: 1 registro nao fecha volta nenhuma (o unico
    fim conhecido e o desligamento). Nada de lap_beacons_ms."""
    cab = leitor.inspecionar(_drk_com_tabela(tmp_path, [275_000]))
    assert "lap_beacons_ms" not in cab.bruto


def test_registro_de_duracao_implausivel_interrompe_a_tabela(
    tmp_path: Path, leitor: LeitorAimDrk
) -> None:
    """Transponder que falha no meio da sessao agrega o resto num registro
    gigante (caso real do kart 0276): a caminhada para nele e as voltas
    anteriores continuam valendo."""
    import struct

    caminho = _drk_com_tabela(tmp_path, [68_000, 41_000])
    dados = bytearray(caminho.read_bytes())
    base = 4096 + 2 * 288
    struct.pack_into("<i", dados, base, 2)
    struct.pack_into("<i", dados, base + 272, 109_000)
    struct.pack_into("<i", dados, base + 276, 4_000_000)  # 66 min: nao e volta
    caminho.write_bytes(bytes(dados))
    cab = leitor.inspecionar(caminho)
    assert cab.bruto["lap_beacons_ms"] == "0,68000"
    assert cab.bruto["lap_registros"] == "2"
