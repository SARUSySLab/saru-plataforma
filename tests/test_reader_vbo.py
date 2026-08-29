"""Testes do leitor Racelogic VBOX .vbo (formato_id vbox_vbo)."""

from __future__ import annotations

from pathlib import Path

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers.base import ErroDeLeitura, Lote
from saru_poc.readers.vbo import LeitorVbo

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def leitor() -> LeitorVbo:
    return LeitorVbo()


def _todos_do_acervo() -> list[Path]:
    if not CONFIG.acervo_root.exists():
        return []
    return sorted(CONFIG.acervo_root.rglob("*.vbo"))


# ---------------------------------------------------------------------------
# Fixtures sinteticas
# ---------------------------------------------------------------------------


def test_fixture_22_colunas_le_todos_os_canais(leitor: LeitorVbo) -> None:
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    assert cab.formato_id == "vbox_vbo"
    assert len(cab.canais) == 22
    nomes = [c.nome_bruto for c in cab.canais]
    assert nomes[0] == "sats"
    assert "VBOX_rpm" in nomes
    # taxa global 10 Hz (Tsample = 0.100) pra todo canal, sem excecao
    assert cab.taxas == (10.0,)
    for c in cab.canais:
        assert c.frequencia_hz == 10.0
        assert c.n_amostras == 3
        assert c.nome_bruto


def test_fixture_41_colunas_traz_bloco_rad(leitor: LeitorVbo) -> None:
    cab = leitor.inspecionar(FIXTURES / "vbo_41col.vbo")
    assert len(cab.canais) == 41
    nomes = [c.nome_bruto for c in cab.canais]
    assert "rad_B_SC_lap" in nomes
    assert "rad_corner_num1" in nomes


def test_venue_declarado_e_sempre_none(leitor: LeitorVbo) -> None:
    """O .vbo nao declara pista: nunca inventar a partir do nome do arquivo."""
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    assert cab.venue_declarado is None


def test_laptiming_vai_pro_bruto(leitor: LeitorVbo) -> None:
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    assert "laptiming_raw" in cab.bruto
    assert "Start" in cab.bruto["laptiming_raw"]


def test_decodifica_em_utf8_e_registra_encoding(leitor: LeitorVbo) -> None:
    """`¬` do [laptiming] tem que chegar integro (nao mojibake de latin-1)."""
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    assert cab.bruto["encoding_usado"] == "utf-8"
    assert "¬" in cab.bruto["laptiming_raw"]
    assert "Â¬" not in cab.bruto["laptiming_raw"]


def test_unidade_declarada_dos_canais_vbox(leitor: LeitorVbo) -> None:
    """[channel units] pareia por sampleperiod + cauda apos avisynctime.

    Medido nos arquivos reais: nao e posicional 1 pra 1 com [header].
    """
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    por_nome = {c.nome_bruto: c for c in cab.canais}
    assert por_nome["VBOX_rpm"].unidade_declarada == "rpm"
    assert por_nome["VBOX_asteer"].unidade_declarada == "°"
    assert por_nome["VBOX_pbrk"].unidade_declarada == "bar"
    assert cab.bruto["channel_units_alinhamento"].startswith("alinhado")


def test_lat_long_sem_unidade_declarada_no_arquivo(leitor: LeitorVbo) -> None:
    """[channel units] nunca cobre os canais GPS iniciais (medido no acervo).

    unidade_declarada sai None pra lat/long: nao ha unidade nenhuma pra ler
    ali, e "minutos" nao pode ser inventado (regra dura contra leitor que
    adivinha canal).
    """
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    por_nome = {c.nome_bruto: c for c in cab.canais}
    assert por_nome["lat"].unidade_declarada is None
    assert por_nome["long"].unidade_declarada is None


def test_alinhamento_recusa_quando_contagem_nao_bate(
    tmp_path, leitor: LeitorVbo
) -> None:
    ruim = tmp_path / "unidades_incompativeis.vbo"
    ruim.write_text(
        "File created on 01/01/2024 @ 00:00:00\n\n"
        "[header]\n"
        "satellites\ntime\nsampleperiod\navifileindex\navisynctime\nVBOX_rpm\n\n"
        "[channel units]\n"
        "s\n\n"  # so 1 entrada, mas a cauda apos avisynctime tem 1 canal
        # (VBOX_rpm), entao o esperado seria 2 (sampleperiod + VBOX_rpm)
        "[column names]\n"
        "sats time Tsample avifileindex avitime VBOX_rpm\n\n"
        "[data]\n"
        "10 120000.000 0.100 1 1 +1.000000E+03\n",
        encoding="utf-8",
    )
    cab = leitor.inspecionar(ruim)
    assert all(c.unidade_declarada is None for c in cab.canais)
    assert "nao bateu" in cab.bruto["channel_units_alinhamento"]


def test_min_max_por_canal(leitor: LeitorVbo) -> None:
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    por_nome = {c.nome_bruto: c for c in cab.canais}
    sats = por_nome["sats"]
    assert sats.valor_min == 140.0
    assert sats.valor_max == 140.0


def test_duracao_deriva_de_n_amostras_e_taxa(leitor: LeitorVbo) -> None:
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    assert cab.duracao_s == pytest.approx(0.3)


def test_capturado_em_vem_da_primeira_linha(leitor: LeitorVbo) -> None:
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    assert cab.capturado_em == "01/03/2023 @ 14:54:04"


def test_sem_secao_column_names_levanta_erro(tmp_path, leitor: LeitorVbo) -> None:
    ruim = tmp_path / "sem_colunas.vbo"
    ruim.write_text(
        "File created on 01/01/2024 @ 00:00:00\n\n[data]\n1 2 3\n",
        encoding="latin-1",
    )
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(ruim)


def test_sem_secao_data_levanta_erro(tmp_path, leitor: LeitorVbo) -> None:
    ruim = tmp_path / "sem_dados.vbo"
    ruim.write_text(
        "File created on 01/01/2024 @ 00:00:00\n\n[column names]\na b c\n",
        encoding="latin-1",
    )
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(ruim)


def test_secao_data_vazia_levanta_erro(tmp_path, leitor: LeitorVbo) -> None:
    ruim = tmp_path / "dados_vazios.vbo"
    ruim.write_text(
        "File created on 01/01/2024 @ 00:00:00\n\n[column names]\na b c\n\n[data]\n\n",
        encoding="latin-1",
    )
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(ruim)


def test_arquivo_inexistente_levanta_erro(tmp_path, leitor: LeitorVbo) -> None:
    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(tmp_path / "nao_existe.vbo")


# ---------------------------------------------------------------------------
# Acervo real
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
@pytest.mark.parametrize("caminho", _todos_do_acervo(), ids=lambda p: p.name)
def test_le_arquivo_real_do_acervo(caminho: Path, leitor: LeitorVbo) -> None:
    cab = leitor.inspecionar(caminho)
    assert cab.formato_id == "vbox_vbo"
    assert cab.venue_declarado is None
    assert len(cab.canais) > 0
    # contagem de canais bate com [column names]
    linhas = caminho.read_text(encoding="latin-1").splitlines()
    idx_secao = next(
        i for i, ln in enumerate(linhas) if ln.strip().lower() == "[column names]"
    )
    n_colunas_declarado = len(linhas[idx_secao + 1].split())
    assert len(cab.canais) == n_colunas_declarado
    for c in cab.canais:
        assert c.nome_bruto
        assert c.frequencia_hz > 0
        assert c.n_amostras > 0


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
def test_todo_arquivo_real_decodifica_em_utf8(leitor: LeitorVbo) -> None:
    """Medido em 2026-08-29: os 9 arquivos do acervo decodificam em UTF-8."""
    for caminho in _todos_do_acervo():
        cab = leitor.inspecionar(caminho)
        assert cab.bruto["encoding_usado"] == "utf-8"


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
def test_todo_arquivo_real_pareia_unidades_vbox(leitor: LeitorVbo) -> None:
    """A hipotese de alinhamento (sampleperiod + cauda) bate nos 9 arquivos."""
    for caminho in _todos_do_acervo():
        cab = leitor.inspecionar(caminho)
        assert cab.bruto["channel_units_alinhamento"].startswith("alinhado")
        por_nome = {c.nome_bruto: c for c in cab.canais}
        if "lat" in por_nome:
            assert por_nome["lat"].unidade_declarada is None
        if "long" in por_nome:
            assert por_nome["long"].unidade_declarada is None
        if "VBOX_rpm" in por_nome:
            assert por_nome["VBOX_rpm"].unidade_declarada == "rpm"


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
def test_esquema_de_41_colunas_traz_rad(leitor: LeitorVbo) -> None:
    """Confere a segunda largura de esquema medida no acervo (41 colunas)."""
    achou = False
    for caminho in _todos_do_acervo():
        cab = leitor.inspecionar(caminho)
        if len(cab.canais) == 41:
            achou = True
            nomes = [c.nome_bruto for c in cab.canais]
            assert any(n.startswith("rad_") for n in nomes)
    assert achou, "nenhum .vbo de 41 colunas encontrado no acervo"


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
def test_esquema_de_22_colunas_sem_rad(leitor: LeitorVbo) -> None:
    """Confere a primeira largura de esquema medida no acervo (22 colunas)."""
    achou = False
    for caminho in _todos_do_acervo():
        cab = leitor.inspecionar(caminho)
        if len(cab.canais) == 22:
            achou = True
            nomes = [c.nome_bruto for c in cab.canais]
            assert not any(n.startswith("rad_") for n in nomes)
    assert achou, "nenhum .vbo de 22 colunas encontrado no acervo"


# ---------------------------------------------------------------------------
# ler()
# ---------------------------------------------------------------------------


def test_suporta_amostra_e_true(leitor: LeitorVbo) -> None:
    assert leitor.suporta_amostra is True


def test_ler_fixture_22_colunas_um_lote_10hz(leitor: LeitorVbo) -> None:
    lotes = list(leitor.ler(FIXTURES / "vbo_22col.vbo"))
    assert len(lotes) == 1
    lote = lotes[0]
    assert isinstance(lote, Lote)
    assert lote.frequencia_hz == 10.0
    assert lote.tabela.num_rows == 3
    nomes_colunas = set(lote.tabela.schema.names)
    assert "t_s" in nomes_colunas
    # uma coluna por nome de [column names], nome bruto intacto
    cab = leitor.inspecionar(FIXTURES / "vbo_22col.vbo")
    for c in cab.canais:
        assert c.nome_bruto in nomes_colunas


def test_ler_fixture_t_s_deriva_da_coluna_time(leitor: LeitorVbo) -> None:
    """t_s = 0, 0.1, 0.2 pros 3 registros da fixture (time 175943.4/.5/.6)."""
    lote = next(leitor.ler(FIXTURES / "vbo_22col.vbo"))
    t_s = lote.tabela.column("t_s").to_pylist()
    assert t_s == pytest.approx([0.0, 0.1, 0.2], abs=1e-6)


def test_ler_fixture_lat_long_ficam_em_minutos_sem_conversao(
    leitor: LeitorVbo,
) -> None:
    """Camada bruta: lat/long saem exatamente como o arquivo escreve, em
    minutos decimais, sem virar grau nem trocar sinal de longitude."""
    lote = next(leitor.ler(FIXTURES / "vbo_22col.vbo"))
    lat = lote.tabela.column("lat").to_pylist()
    long_ = lote.tabela.column("long").to_pylist()
    assert lat[0] == pytest.approx(-1422.05535600)
    assert long_[0] == pytest.approx(2802.02919000)


def test_ler_fixture_todas_colunas_sao_float64(leitor: LeitorVbo) -> None:
    lote = next(leitor.ler(FIXTURES / "vbo_22col.vbo"))
    for nome in lote.tabela.schema.names:
        assert str(lote.tabela.schema.field(nome).type) == "double"


def test_ler_linha_com_campo_faltando_vira_nan(tmp_path, leitor: LeitorVbo) -> None:
    arq = tmp_path / "linha_curta.vbo"
    arq.write_text(
        "File created on 01/01/2024 @ 00:00:00\n\n"
        "[column names]\n"
        "sats time Tsample VBOX_rpm\n\n"
        "[data]\n"
        "10 120000.000 0.100 8000\n"
        "10 120000.100 0.100\n",
        encoding="utf-8",
    )
    lotes = list(leitor.ler(arq))
    assert len(lotes) == 1
    rpm = lotes[0].tabela.column("VBOX_rpm").to_pylist()
    assert rpm[0] == pytest.approx(8000.0)
    import math

    assert math.isnan(rpm[1])


def test_ler_campo_nao_numerico_vira_nan(tmp_path, leitor: LeitorVbo) -> None:
    arq = tmp_path / "campo_texto.vbo"
    arq.write_text(
        "File created on 01/01/2024 @ 00:00:00\n\n"
        "[column names]\n"
        "sats time Tsample VBOX_rpm\n\n"
        "[data]\n"
        "10 120000.000 0.100 ABC\n",
        encoding="utf-8",
    )
    lote = next(leitor.ler(arq))
    rpm = lote.tabela.column("VBOX_rpm").to_pylist()
    import math

    assert math.isnan(rpm[0])


def test_ler_sem_coluna_time_cai_pro_indice_sobre_taxa(
    tmp_path, leitor: LeitorVbo
) -> None:
    """Sem a coluna `time`, t_s vem de indice / frequencia_hz (nao acumula:
    e multiplicacao a partir do indice, nao soma de Tsample linha a linha)."""
    arq = tmp_path / "sem_time.vbo"
    arq.write_text(
        "File created on 01/01/2024 @ 00:00:00\n\n"
        "[column names]\n"
        "sats Tsample VBOX_rpm\n\n"
        "[data]\n"
        "10 0.100 8000\n"
        "10 0.100 8001\n"
        "10 0.100 8002\n",
        encoding="utf-8",
    )
    lote = next(leitor.ler(arq))
    t_s = lote.tabela.column("t_s").to_pylist()
    assert t_s == pytest.approx([0.0, 0.1, 0.2])


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
def test_ler_arquivo_real_bate_com_n_amostras_do_inspecionar(
    leitor: LeitorVbo,
) -> None:
    """A contagem de linhas lidas por ler() tem que bater com o n_amostras
    que inspecionar() ja declarava (os dois leem o mesmo arquivo)."""
    for caminho in _todos_do_acervo():
        cab = leitor.inspecionar(caminho)
        n_esperado = cab.canais[0].n_amostras
        total_linhas = sum(lote.tabela.num_rows for lote in leitor.ler(caminho))
        assert total_linhas == n_esperado, caminho.name


@pytest.mark.skipif(not _todos_do_acervo(), reason="acervo nao montado nesta maquina")
def test_ler_arquivo_real_t_s_e_monotono_nao_decrescente(leitor: LeitorVbo) -> None:
    import itertools

    for caminho in _todos_do_acervo():
        for lote in leitor.ler(caminho):
            t_s = lote.tabela.column("t_s").to_pylist()
            assert all(b >= a for a, b in itertools.pairwise(t_s)), caminho.name
