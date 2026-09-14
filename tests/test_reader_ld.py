"""Leitor de inventario do MoTeC `.ld` (`motec_ld`).

Caminho feliz contra a fixture sintetica versionada em
`tests/fixtures/synthetic_motec.ld` (gerada por
`tests/fixtures/gerar_ld_sintetico.py`), mais varredura contra os 42
arquivos reais do acervo quando ele estiver montado nesta maquina. Nao
versiona arquivo real: tem nome de piloto real.
"""

from __future__ import annotations

import struct
import tempfile
from pathlib import Path

import numpy as np
import pytest

from saru_poc.config import CONFIG
from saru_poc.readers import ld as ld_mod
from saru_poc.readers.base import Cabecalho, ErroDeLeitura, Lote
from saru_poc.readers.ld import TAMANHO_REGISTRO_CANAL, LeitorLd
from saru_poc.storage import escrever_serie

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_motec.ld"


@pytest.fixture
def leitor() -> LeitorLd:
    return LeitorLd()


def test_formato_id_e_suporte_a_amostra(leitor: LeitorLd) -> None:
    assert leitor.formato_id == "motec_ld"
    assert leitor.suporta_amostra is True


def test_fixture_sintetica_caminho_feliz(leitor: LeitorLd) -> None:
    cab = leitor.inspecionar(FIXTURE)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "motec_ld"
    assert len(cab.canais) == 3
    assert cab.venue_declarado == "Interlagos GP Circuit"
    assert cab.capturado_em == "2024-08-17T16:46:07"
    assert cab.bruto["device"] == "ADL"
    assert cab.bruto["piloto"] == "Piloto Sintetico"
    assert cab.bruto["veiculo"] == "Kart Fixture"
    assert cab.bruto["nome_evento"] == "Fixture de teste"
    assert cab.bruto["n_canais"] == "3"

    nomes = {c.nome_bruto for c in cab.canais}
    assert nomes == {"GPS Latitude", "G_LAT", "Engine RPM"}
    assert cab.taxas == (20.0, 60.0, 100.0)

    # canal de maior contagem e o Engine RPM, 12000 amostras a 100 Hz.
    assert cab.duracao_s == pytest.approx(120.0)
    assert cab.bruto["duracao_s_derivado_de"] == "Engine RPM"


def test_fixture_armadilha_g_lat_unidade_m_s2(leitor: LeitorLd) -> None:
    """A armadilha central: G_LAT parece coordenada, mas a unidade
    declarada no arquivo e `m/s2` (aceleracao lateral, nao GPS). O leitor
    tem que reportar a unidade fielmente, sem tentar corrigir o nome.
    """
    cab = leitor.inspecionar(FIXTURE)
    g_lat = next(c for c in cab.canais if c.nome_bruto == "G_LAT")
    assert g_lat.unidade_declarada == "m/s2"
    assert g_lat.frequencia_hz == 20.0


def test_magic_invalido_levanta_erro_de_leitura(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    ruim = tmp_path / "ruim.ld"
    conteudo = bytearray(FIXTURE.read_bytes())
    conteudo[0:4] = (999).to_bytes(4, "little")
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="magic"):
        leitor.inspecionar(ruim)


def test_arquivo_menor_que_cabecalho_levanta_erro_de_leitura(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    curto = tmp_path / "curto.ld"
    curto.write_bytes(FIXTURE.read_bytes()[:100])

    with pytest.raises(ErroDeLeitura):
        leitor.inspecionar(curto)


def test_lista_de_canais_em_ciclo_levanta_erro_de_leitura(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    """Regressao do B2: lista que nao fecha (aponta em ciclo pra si mesma)
    nunca pode virar leitura parcial silenciosa, tem que levantar erro com
    o offset onde parou.
    """
    import struct

    conteudo = bytearray(FIXTURE.read_bytes())
    ptr_canais = struct.unpack_from("<I", conteudo, 0x08)[0]
    # Aponta o "next" do primeiro canal de volta pra si mesmo.
    struct.pack_into("<I", conteudo, ptr_canais + 4, ptr_canais)
    ciclo = tmp_path / "ciclo.ld"
    ciclo.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="ciclo"):
        leitor.inspecionar(ciclo)


# --- `ler()`: fixture propria com amostra real, construida em memoria ---
#
# A fixture versionada `synthetic_motec.ld` (gerada por
# `gerar_ld_sintetico.py`, arquivo que este prompt de delegacao nao autoriza
# editar) tem ponteiros de dado fantasiosos (1000/2000/3000) que nao apontam
# pra bytes de amostra de verdade: ela so testa `inspecionar()`. Pra `ler()`
# a fixture monta o proprio `.ld` em memoria, com layout de cabecalho e de
# registro de canal identicos ao de producao (offsets importados do modulo,
# nunca redigitados), so que com `ptr_dados` real e amostra de verdade atras
# dele.


def _string(texto: str, tamanho: int) -> bytes:
    b = texto.encode("latin1")
    return b + b"\x00" * (tamanho - len(b))


def _registro_canal(
    *,
    prev: int,
    prox: int,
    ptr_dados: int,
    n_amostras: int,
    freq_hz: int,
    dtype_a: int,
    dtype: int,
    shift: int,
    mul: int,
    scale: int,
    dec_places: int,
    nome: str,
    unidade: str,
) -> bytes:
    r = bytearray(TAMANHO_REGISTRO_CANAL)
    struct.pack_into("<IIII", r, 0, prev, prox, ptr_dados, n_amostras)
    struct.pack_into("<HH", r, ld_mod.OFF_CANAL_DTYPE_A, dtype_a, dtype)
    struct.pack_into("<H", r, ld_mod.OFF_CANAL_FREQ_HZ, freq_hz)
    struct.pack_into("<hhhh", r, ld_mod.OFF_CANAL_SHIFT, shift, mul, scale, dec_places)
    r[
        ld_mod.OFF_CANAL_NOME_LONGO : ld_mod.OFF_CANAL_NOME_LONGO
        + ld_mod.LEN_CANAL_NOME_LONGO
    ] = _string(nome, ld_mod.LEN_CANAL_NOME_LONGO)
    r[
        ld_mod.OFF_CANAL_NOME_CURTO : ld_mod.OFF_CANAL_NOME_CURTO
        + ld_mod.LEN_CANAL_NOME_CURTO
    ] = _string(nome[: ld_mod.LEN_CANAL_NOME_CURTO], ld_mod.LEN_CANAL_NOME_CURTO)
    r[
        ld_mod.OFF_CANAL_UNIDADE : ld_mod.OFF_CANAL_UNIDADE + ld_mod.LEN_CANAL_UNIDADE
    ] = _string(unidade, ld_mod.LEN_CANAL_UNIDADE)
    return bytes(r)


def _construir_ld_com_amostra(tmp_path: Path) -> Path:
    """3 canais: 2 a 50 Hz (float32 e int16 com escala nao trivial) e 1 a
    20 Hz (float32), pra exercitar agrupamento por taxa e a formula de
    escala ao mesmo tempo. Ver docstring da secao acima.
    """
    tamanho_cabecalho = ld_mod.OFF_EVENTO + ld_mod.LEN_EVENTO
    ptr_canais = tamanho_cabecalho
    n_canais = 3
    ptr_dados_lista = ptr_canais + n_canais * TAMANHO_REGISTRO_CANAL

    dados_float_50hz = np.array([1.0, 2.5, -3.25, 4.0], dtype="<f4")
    # valor = (raw / scale * 10**-dec + shift) * mul, com scale=10, dec=1,
    # shift=1, mul=2: raw=100 -> 4.0, 200 -> 6.0, -50 -> 1.0, 0 -> 2.0.
    raw_int_50hz = np.array([100, 200, -50, 0], dtype="<i2")
    dados_float_20hz = np.array([10.0, 20.0], dtype="<f4")

    ptr_float_50 = ptr_dados_lista
    ptr_int_50 = ptr_float_50 + dados_float_50hz.nbytes
    ptr_float_20 = ptr_int_50 + raw_int_50hz.nbytes
    tamanho_total = ptr_float_20 + dados_float_20hz.nbytes

    buf = bytearray(tamanho_total)

    struct.pack_into("<I", buf, ld_mod.OFF_MAGIC, ld_mod.MAGIC_ESPERADO)
    struct.pack_into("<I", buf, ld_mod.OFF_PTR_CANAIS, ptr_canais)
    struct.pack_into("<I", buf, ld_mod.OFF_PTR_DADOS, ptr_dados_lista)
    struct.pack_into("<I", buf, ld_mod.OFF_PTR_EVENTO, 0)

    buf[ld_mod.OFF_DEVICE : ld_mod.OFF_DEVICE + ld_mod.LEN_DEVICE] = _string(
        "ADL", ld_mod.LEN_DEVICE
    )
    buf[ld_mod.OFF_DATA : ld_mod.OFF_DATA + ld_mod.LEN_DATA] = _string(
        "01/01/2024", ld_mod.LEN_DATA
    )
    buf[ld_mod.OFF_HORA : ld_mod.OFF_HORA + ld_mod.LEN_HORA] = _string(
        "10:00:00", ld_mod.LEN_HORA
    )
    buf[ld_mod.OFF_PILOTO : ld_mod.OFF_PILOTO + ld_mod.LEN_PILOTO] = _string(
        "Piloto Teste", ld_mod.LEN_PILOTO
    )
    buf[ld_mod.OFF_VEICULO : ld_mod.OFF_VEICULO + ld_mod.LEN_VEICULO] = _string(
        "Carro Teste", ld_mod.LEN_VEICULO
    )
    buf[ld_mod.OFF_VENUE : ld_mod.OFF_VENUE + ld_mod.LEN_VENUE] = _string(
        "Pista Teste", ld_mod.LEN_VENUE
    )
    buf[ld_mod.OFF_COMENTARIO : ld_mod.OFF_COMENTARIO + ld_mod.LEN_COMENTARIO] = (
        _string("comentario", ld_mod.LEN_COMENTARIO)
    )
    buf[ld_mod.OFF_EVENTO : ld_mod.OFF_EVENTO + ld_mod.LEN_EVENTO] = _string(
        "evento", ld_mod.LEN_EVENTO
    )

    no0 = ptr_canais
    no1 = ptr_canais + TAMANHO_REGISTRO_CANAL
    no2 = ptr_canais + 2 * TAMANHO_REGISTRO_CANAL

    canal0 = _registro_canal(
        prev=0,
        prox=no1,
        ptr_dados=ptr_float_50,
        n_amostras=4,
        freq_hz=50,
        dtype_a=7,
        dtype=4,
        shift=0,
        mul=1,
        scale=1,
        dec_places=0,
        nome="Canal Float",
        unidade="m/s2",
    )
    canal1 = _registro_canal(
        prev=no0,
        prox=no2,
        ptr_dados=ptr_int_50,
        n_amostras=4,
        freq_hz=50,
        dtype_a=0,
        dtype=2,
        shift=1,
        mul=2,
        scale=10,
        dec_places=1,
        nome="Canal Int",
        unidade="m",
    )
    canal2 = _registro_canal(
        prev=no1,
        prox=0,
        ptr_dados=ptr_float_20,
        n_amostras=2,
        freq_hz=20,
        dtype_a=7,
        dtype=4,
        shift=0,
        mul=1,
        scale=1,
        dec_places=0,
        nome="Canal Lento",
        unidade="deg",
    )

    buf[no0 : no0 + TAMANHO_REGISTRO_CANAL] = canal0
    buf[no1 : no1 + TAMANHO_REGISTRO_CANAL] = canal1
    buf[no2 : no2 + TAMANHO_REGISTRO_CANAL] = canal2

    buf[ptr_float_50 : ptr_float_50 + dados_float_50hz.nbytes] = (
        dados_float_50hz.tobytes()
    )
    buf[ptr_int_50 : ptr_int_50 + raw_int_50hz.nbytes] = raw_int_50hz.tobytes()
    buf[ptr_float_20 : ptr_float_20 + dados_float_20hz.nbytes] = (
        dados_float_20hz.tobytes()
    )

    caminho = tmp_path / "com_amostra.ld"
    caminho.write_bytes(bytes(buf))
    return caminho


def test_ler_agrupa_por_taxa_e_aplica_formula_de_escala(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    caminho = _construir_ld_com_amostra(tmp_path)
    lotes = list(leitor.ler(caminho))

    assert len(lotes) == 2
    for lote in lotes:
        assert isinstance(lote, Lote)

    por_taxa = {lote.frequencia_hz: lote for lote in lotes}
    assert set(por_taxa) == {50.0, 20.0}

    lote_50 = por_taxa[50.0]
    assert lote_50.tabela.num_rows == 4
    assert set(lote_50.tabela.schema.names) == {"t_s", "Canal Float", "Canal Int"}
    assert lote_50.tabela.column("t_s").to_pylist() == pytest.approx(
        [0.0, 0.02, 0.04, 0.06]
    )
    assert lote_50.tabela.column("Canal Float").to_pylist() == pytest.approx(
        [1.0, 2.5, -3.25, 4.0], abs=1e-5
    )
    # raw=100 -> (100/10*10**-1+1)*2 = 4.0; 200 -> 6.0; -50 -> 1.0; 0 -> 2.0
    assert lote_50.tabela.column("Canal Int").to_pylist() == pytest.approx(
        [4.0, 6.0, 1.0, 2.0]
    )

    lote_20 = por_taxa[20.0]
    assert lote_20.tabela.num_rows == 2
    assert set(lote_20.tabela.schema.names) == {"t_s", "Canal Lento"}
    assert lote_20.tabela.column("t_s").to_pylist() == pytest.approx([0.0, 0.05])
    assert lote_20.tabela.column("Canal Lento").to_pylist() == pytest.approx(
        [10.0, 20.0]
    )


def test_ler_nomes_de_coluna_batem_com_inspecionar(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    """A regra central do contrato: o nome de coluna emitido por `ler()` tem
    que ser exatamente o `nome_bruto` que `inspecionar()` devolve, senao o
    canal fica orfao na etapa seguinte."""
    caminho = _construir_ld_com_amostra(tmp_path)
    cab = leitor.inspecionar(caminho)
    nomes_inspecionar = {c.nome_bruto for c in cab.canais}

    nomes_ler: set[str] = set()
    for lote in leitor.ler(caminho):
        nomes_ler.update(n for n in lote.tabela.schema.names if n != "t_s")

    assert nomes_ler == nomes_inspecionar


def test_ler_contagem_de_linhas_bate_com_n_amostras_do_inspecionar(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    caminho = _construir_ld_com_amostra(tmp_path)
    cab = leitor.inspecionar(caminho)
    esperado_por_taxa = {c.frequencia_hz: c.n_amostras for c in cab.canais}

    linhas_por_taxa: dict[float, int] = {}
    for lote in leitor.ler(caminho):
        linhas_por_taxa[lote.frequencia_hz] = (
            linhas_por_taxa.get(lote.frequencia_hz, 0) + lote.tabela.num_rows
        )

    assert linhas_por_taxa == esperado_por_taxa


def test_ler_streaming_em_lotes_pequenos(
    leitor: LeitorLd, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ler()` tem que streamar: com o teto de linhas por lote artificialmente
    baixo, uma taxa com 4 amostras sai em mais de um `Lote`, sem duplicar
    nem perder linha."""
    monkeypatch.setattr(ld_mod, "LINHAS_POR_LOTE", 2)
    caminho = _construir_ld_com_amostra(tmp_path)

    lotes_50hz = [lote for lote in leitor.ler(caminho) if lote.frequencia_hz == 50.0]
    assert len(lotes_50hz) == 2
    assert [lote.tabela.num_rows for lote in lotes_50hz] == [2, 2]

    t_s_concatenado = [
        v for lote in lotes_50hz for v in lote.tabela.column("t_s").to_pylist()
    ]
    assert t_s_concatenado == pytest.approx([0.0, 0.02, 0.04, 0.06])

    valores_concatenados = [
        v for lote in lotes_50hz for v in lote.tabela.column("Canal Int").to_pylist()
    ]
    assert valores_concatenados == pytest.approx([4.0, 6.0, 1.0, 2.0])


def test_ler_via_escrever_serie_produz_parquet_por_taxa(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    """Fim a fim contra `storage.escrever_serie`, o mesmo caminho que a
    ingestao real usa."""
    caminho = _construir_ld_com_amostra(tmp_path)
    ponteiros = escrever_serie(
        "gravacao-teste", leitor.ler(caminho), raiz=Path(tempfile.mkdtemp())
    )
    linhas_por_taxa = {p.frequencia_hz: p.linhas for p in ponteiros}
    assert linhas_por_taxa == {50.0: 4, 20.0: 2}


def test_ler_taxa_com_contagens_divergentes_levanta_erro_de_leitura(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    """Dois canais na MESMA taxa com n_amostras diferente e dado corrompido
    ou premissa quebrada: `ler()` tem que recusar em vez de cortar um dos
    dois silenciosamente."""
    caminho = _construir_ld_com_amostra(tmp_path)
    conteudo = bytearray(caminho.read_bytes())
    ptr_canais = struct.unpack_from("<I", conteudo, ld_mod.OFF_PTR_CANAIS)[0]
    # canal1 ("Canal Int", segundo da lista) e o mesmo 50 Hz do canal0: muda
    # a contagem dele pra divergir do canal0.
    off_canal1 = ptr_canais + TAMANHO_REGISTRO_CANAL
    struct.pack_into("<I", conteudo, off_canal1 + ld_mod.OFF_CANAL_N_AMOSTRAS, 3)
    ruim = tmp_path / "divergente.ld"
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="divergente"):
        list(leitor.ler(ruim))


def test_ler_combinacao_de_dtype_nao_suportada_levanta_erro_de_leitura(
    leitor: LeitorLd, tmp_path: Path
) -> None:
    caminho = _construir_ld_com_amostra(tmp_path)
    conteudo = bytearray(caminho.read_bytes())
    ptr_canais = struct.unpack_from("<I", conteudo, ld_mod.OFF_PTR_CANAIS)[0]
    struct.pack_into("<HH", conteudo, ptr_canais + ld_mod.OFF_CANAL_DTYPE_A, 99, 4)
    ruim = tmp_path / "dtype_ruim.ld"
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="suportada"):
        list(leitor.ler(ruim))


# --- Invariantes gerais, contra a fixture e contra o acervo real ---


def _checar_invariantes(cab: Cabecalho) -> None:
    assert len(cab.canais) > 0
    for c in cab.canais:
        assert c.frequencia_hz > 0, f"canal {c.nome_bruto} com frequencia <= 0"
        assert c.nome_bruto.strip() != "", "canal com nome vazio"


def test_invariantes_na_fixture_sintetica(leitor: LeitorLd) -> None:
    _checar_invariantes(leitor.inspecionar(FIXTURE))


# --- Contra o acervo real, quando montado nesta maquina ---


def _todos_ld_do_acervo() -> list[Path]:
    if not CONFIG.acervo_root.exists():
        return []
    return sorted(CONFIG.acervo_root.rglob("*.ld"))


@pytest.mark.skipif(not CONFIG.acervo_root.exists(), reason="acervo nao montado")
def test_todos_os_ld_do_acervo_abrem(leitor: LeitorLd) -> None:
    arquivos = _todos_ld_do_acervo()
    if not arquivos:
        pytest.skip("nenhum .ld no acervo")

    falhas: list[str] = []
    todas_taxas: set[float] = set()
    todos_venues: set[str] = set()
    contagens_canais: list[int] = []

    for f in arquivos:
        try:
            cab = leitor.inspecionar(f)
        except ErroDeLeitura as e:
            falhas.append(f"{f.name}: {e}")
            continue
        _checar_invariantes(cab)
        todas_taxas.update(cab.taxas)
        if cab.venue_declarado:
            todos_venues.add(cab.venue_declarado)
        contagens_canais.append(len(cab.canais))

    assert not falhas, "arquivos que falharam:\n" + "\n".join(falhas)
    print(f"\n{len(arquivos)} arquivos .ld abriram sem erro")
    print(f"canais: min={min(contagens_canais)} max={max(contagens_canais)}")
    print(f"taxas encontradas (Hz): {sorted(todas_taxas)}")
    print(f"venues distintos: {sorted(todos_venues)}")


@pytest.mark.skipif(not CONFIG.acervo_root.exists(), reason="acervo nao montado")
def test_acc_tem_g_lat_com_unidade_m_s2_no_acervo_real(leitor: LeitorLd) -> None:
    """A armadilha, contra dado real: pelo menos um `.ld` do lote ACC tem
    G_LAT declarado em `m/s2`, nao em grau/coordenada.
    """
    candidatos = [f for f in _todos_ld_do_acervo() if "acc-autoanalise" in f.parts]
    if not candidatos:
        pytest.skip("lote acc-autoanalise nao encontrado no acervo")

    achou = False
    for f in candidatos:
        cab = leitor.inspecionar(f)
        for c in cab.canais:
            if c.nome_bruto == "G_LAT":
                assert c.unidade_declarada == "m/s2", (
                    f"{f.name}: G_LAT com unidade {c.unidade_declarada!r}, "
                    "esperava m/s2 (a armadilha do nome que mente)"
                )
                achou = True
        if achou:
            break

    assert achou, "nenhum G_LAT encontrado no lote ACC do acervo"


@pytest.mark.skipif(not CONFIG.acervo_root.exists(), reason="acervo nao montado")
def test_ler_contra_todo_o_acervo_bate_com_inspecionar(leitor: LeitorLd) -> None:
    """Contra os 42 `.ld` reais: linhas escritas por taxa (via
    `escrever_serie`, o mesmo caminho da ingestao) tem que bater exatamente
    com `n_amostras` que `inspecionar()` mediu pro mesmo canal."""
    arquivos = _todos_ld_do_acervo()
    if not arquivos:
        pytest.skip("nenhum .ld no acervo")

    total_linhas = 0
    total_bytes = 0
    taxas_vistas: set[float] = set()
    falhas: list[str] = []

    for f in arquivos:
        cab = leitor.inspecionar(f)
        esperado_por_taxa: dict[float, int] = {}
        for c in cab.canais:
            esperado_por_taxa[c.frequencia_hz] = c.n_amostras

        ponteiros = escrever_serie(
            "acervo-ld", leitor.ler(f), raiz=Path(tempfile.mkdtemp())
        )
        obtido_por_taxa = {p.frequencia_hz: p.linhas for p in ponteiros}

        for hz, n_esperado in esperado_por_taxa.items():
            n_obtido = obtido_por_taxa.get(hz, 0)
            if n_obtido != n_esperado:
                falhas.append(
                    f"{f.name}: taxa {hz} Hz esperava {n_esperado} linhas, "
                    f"obteve {n_obtido}"
                )

        for p in ponteiros:
            total_linhas += p.linhas
            total_bytes += p.bytes_
            taxas_vistas.add(p.frequencia_hz)

    assert not falhas, "divergencias inspecionar() x ler():\n" + "\n".join(falhas)
    print(f"\n{len(arquivos)} arquivos .ld lidos com sucesso via ler()")
    print(f"total de linhas: {total_linhas}")
    print(f"total de bytes em parquet: {total_bytes}")
    print(f"taxas encontradas (Hz): {sorted(taxas_vistas)}")
