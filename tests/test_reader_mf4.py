"""Leitor de inventario do ASAM MDF4 (`asam_mf4`).

Caminho feliz contra a fixture sintetica versionada em
`tests/fixtures/mf4_sintetico.mf4` (gerada por
`tests/fixtures/gerar_mf4_sintetico.py`), mais varredura contra os 5
arquivos reais do acervo quando ele estiver montado nesta maquina. Nao
versiona arquivo real: e o mesmo criterio do `.ld` e do `.vbo`.
"""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers.asam_mf4 import LeitorAsamMf4
from saru_poc.readers.base import Cabecalho, ErroDeLeitura

FIXTURE = Path(__file__).parent / "fixtures" / "mf4_sintetico.mf4"


@pytest.fixture
def leitor() -> LeitorAsamMf4:
    return LeitorAsamMf4()


def test_formato_id_e_suporte_a_amostra(leitor: LeitorAsamMf4) -> None:
    assert leitor.formato_id == "asam_mf4"
    assert leitor.suporta_amostra is False


def test_ler_levanta_not_implemented(leitor: LeitorAsamMf4) -> None:
    with pytest.raises(NotImplementedError):
        list(leitor.ler(FIXTURE))


def test_fixture_sintetica_caminho_feliz(leitor: LeitorAsamMf4) -> None:
    cab = leitor.inspecionar(FIXTURE)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "asam_mf4"
    assert len(cab.canais) == 3
    assert cab.venue_declarado is None
    assert cab.capturado_em == "2024-08-03T15:46:40+00:00"
    assert cab.duracao_s == pytest.approx(0.4)
    assert cab.bruto["versao_mdf"] == "4.00"
    assert cab.bruto["programa_gerador"] == "fixture"
    assert cab.bruto["n_grupos"] == "1"
    assert "fixture sintetica" in cab.bruto["comentario_hd"]

    nomes = {c.nome_bruto for c in cab.canais}
    assert nomes == {"Time", "RPM", "Speed"}
    # os 3 canais do grupo compartilham o mesmo canal mestre, logo a mesma
    # taxa: 5 amostras, t de 0.0 a 0.4, (5-1)/0.4 = 10 Hz.
    assert cab.taxas == (10.0,)

    unidades = {c.nome_bruto: c.unidade_declarada for c in cab.canais}
    assert unidades == {"Time": "s", "RPM": "1/min", "Speed": "km/h"}

    for c in cab.canais:
        assert c.n_amostras == 5


def test_data_type_32_e_64_bits_lidos_igual(leitor: LeitorAsamMf4) -> None:
    """`Speed` e float32 (32 bits) e `RPM` e float64 (64 bits): a mesma
    tabela de decodificacao tem que cobrir os dois, sem confundir tamanho de
    campo com posicao no registro."""
    cab = leitor.inspecionar(FIXTURE)
    speed = next(c for c in cab.canais if c.nome_bruto == "Speed")
    rpm = next(c for c in cab.canais if c.nome_bruto == "RPM")
    assert speed.frequencia_hz == rpm.frequencia_hz == 10.0


def test_magic_invalido_levanta_erro_de_leitura(
    leitor: LeitorAsamMf4, tmp_path: Path
) -> None:
    ruim = tmp_path / "ruim.mf4"
    conteudo = bytearray(FIXTURE.read_bytes())
    conteudo[0:8] = b"XXXXXXXX"
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="magic"):
        leitor.inspecionar(ruim)


def test_arquivo_menor_que_idblock_levanta_erro_de_leitura(
    leitor: LeitorAsamMf4, tmp_path: Path
) -> None:
    curto = tmp_path / "curto.mf4"
    curto.write_bytes(FIXTURE.read_bytes()[:50])

    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(curto)


def test_lista_de_cn_em_ciclo_levanta_erro_de_leitura(
    leitor: LeitorAsamMf4, tmp_path: Path
) -> None:
    """Regressao do B2 (ver `.ld`): lista de canal que nao fecha nunca pode
    virar leitura parcial silenciosa."""
    conteudo = bytearray(FIXTURE.read_bytes())
    # O primeiro ##CN (canal mestre "Time") fica logo apos o ##CG. Acha o
    # offset dele varrendo o link cn_cn_next: aponta o proprio next pra si
    # mesmo pra fechar o ciclo.
    idx = conteudo.find(b"##CN")
    assert idx != -1
    off_link_next = idx + 24  # primeiro link do ##CN e cn_cn_next
    struct.pack_into("<Q", conteudo, off_link_next, idx)
    ciclo = tmp_path / "ciclo.mf4"
    ciclo.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="ciclo"):
        leitor.inspecionar(ciclo)


def test_grupo_sem_canal_mestre_levanta_erro_de_leitura(
    leitor: LeitorAsamMf4, tmp_path: Path
) -> None:
    """Sem canal mestre nao da pra provar frequencia: o contrato exige
    levantar erro em vez de fabricar taxa (a mesma regra do `.ld`)."""
    conteudo = bytearray(FIXTURE.read_bytes())
    # Acha o ##CN cujo cn_type == 2 (o mestre "Time"; os outros dois ja sao
    # 0, "fixed length", entao nao basta pegar o primeiro ##CN da busca).
    idx = -1
    inicio = 0
    while True:
        achado = conteudo.find(b"##CN", inicio)
        if achado == -1:
            break
        # dado fixo comeca depois do cabecalho (24) + 8 links * 8 bytes = 88.
        if conteudo[achado + 88] == 2:  # cn_type
            idx = achado
            break
        inicio = achado + 4
    assert idx != -1, "canal mestre (cn_type == 2) nao encontrado na fixture"
    conteudo[idx + 88] = 0  # troca cn_type de 2 (mestre) pra 0 (fixed length)
    sem_mestre = tmp_path / "sem_mestre.mf4"
    sem_mestre.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="mestre"):
        leitor.inspecionar(sem_mestre)


# --- Invariantes gerais, contra a fixture e contra o acervo real ---


def _checar_invariantes(cab: Cabecalho) -> None:
    assert len(cab.canais) > 0
    for c in cab.canais:
        assert c.frequencia_hz > 0, f"canal {c.nome_bruto} com frequencia <= 0"
        assert c.nome_bruto.strip() != "", "canal com nome vazio"


def test_invariantes_na_fixture_sintetica(leitor: LeitorAsamMf4) -> None:
    _checar_invariantes(leitor.inspecionar(FIXTURE))


# --- Contra o acervo real, quando montado nesta maquina ---


def _todos_mf4_do_acervo() -> list[Path]:
    if not CONFIG.acervo_root.exists():
        return []
    return sorted(CONFIG.acervo_root.rglob("*.mf4"))


@pytest.mark.skipif(not CONFIG.acervo_root.exists(), reason="acervo nao montado")
def test_todos_os_mf4_do_acervo_abrem(leitor: LeitorAsamMf4) -> None:
    arquivos = _todos_mf4_do_acervo()
    if not arquivos:
        pytest.skip("nenhum .mf4 no acervo")

    falhas: list[str] = []
    todas_taxas: set[float] = set()
    contagens_canais: list[int] = []

    for f in arquivos:
        try:
            cab = leitor.inspecionar(f)
        except ErroDeLeitura as exc:
            falhas.append(f"{f.name}: {exc}")
            continue
        _checar_invariantes(cab)
        todas_taxas.update(cab.taxas)
        contagens_canais.append(len(cab.canais))

    assert not falhas, "\n".join(falhas)
    assert contagens_canais, "nenhum .mf4 do acervo foi lido com sucesso"
    print(
        f"\n{len(arquivos)} arquivos, "
        f"canais de {min(contagens_canais)} a {max(contagens_canais)}, "
        f"taxas medidas: {sorted(todas_taxas)}"
    )
