"""Testes dos leitores Pi/Cosworth `.pid` (`pi_pid`) e `.dat` LISTHEAD
(`pi_listhead_dat`).

Caminho feliz contra as fixtures sinteticas versionadas em
`tests/fixtures/pi_pid_sintetico.pid` e `tests/fixtures/pi_listhead_sintetico.dat`
(geradas por `pi_gerar_pid_sintetico.py` e `pi_gerar_listhead_sintetico.py`),
mais varredura contra o acervo real quando montado nesta maquina. As duas
fixtures compartilham os mesmos 3 canais (`Steering`, `Speed`,
`Throttle Position`) pra exercitar o teste de cruzamento sem depender do
acervo. Nao versiona arquivo real: tem nome de piloto real.
"""

from __future__ import annotations

import itertools
import re
import struct
import sys
from pathlib import Path

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers.base import Cabecalho, ErroDeLeitura
from saru_poc.readers.pi_listhead_dat import LeitorPiListheadDat
from saru_poc.readers.pi_pid import LeitorPiPid

FIXTURES = Path(__file__).parent / "fixtures"
sys.path.insert(0, str(FIXTURES))
FIXTURE_PID = FIXTURES / "pi_pid_sintetico.pid"
FIXTURE_DAT = FIXTURES / "pi_listhead_sintetico.dat"


@pytest.fixture
def leitor_pid() -> LeitorPiPid:
    return LeitorPiPid()


@pytest.fixture
def leitor_dat() -> LeitorPiListheadDat:
    return LeitorPiListheadDat()


# ---------------------------------------------------------------------------
# pi_pid: caminho feliz na fixture sintetica
# ---------------------------------------------------------------------------


def test_pid_formato_id_e_suporte_a_amostra(leitor_pid: LeitorPiPid) -> None:
    assert leitor_pid.formato_id == "pi_pid"
    # Passou a suportar amostra em 29/08. O teste anterior afirmava False e
    # virou premissa velha assim que o `ler()` foi implementado.
    assert leitor_pid.suporta_amostra is True


def test_pid_ler_devolve_lote_por_taxa_com_eixo_de_tempo(
    leitor_pid: LeitorPiPid,
) -> None:
    lotes = list(leitor_pid.ler(FIXTURE_PID))
    assert lotes, "ler() nao emitiu lote nenhum"
    for lote in lotes:
        assert lote.frequencia_hz > 0
        assert "t_s" in lote.tabela.schema.names
        assert lote.tabela.num_rows > 0
    # Uma serie por taxa nativa, nunca reamostrada pra um eixo comum.
    taxas = [lote.frequencia_hz for lote in lotes]
    assert len(taxas) == len(set(taxas)) or all(
        a <= b for a, b in itertools.pairwise(taxas)
    )


def test_pid_ler_bate_com_o_que_inspecionar_declarou(
    leitor_pid: LeitorPiPid,
) -> None:
    """Os dois leem o mesmo arquivo: divergencia entre eles e bug."""
    cab = leitor_pid.inspecionar(FIXTURE_PID)
    esperado: dict[str, int] = {}
    for c in cab.canais:
        esperado[c.nome_bruto] = c.n_amostras

    lido: dict[str, int] = {}
    for lote in leitor_pid.ler(FIXTURE_PID):
        for nome in lote.tabela.schema.names:
            if nome == "t_s":
                continue
            # Conta slots, nao valores validos: o slot do tick 1 dos canais
            # de 100 Hz e marcador de bloco e sai nulo (ver `_TICK_MARCADOR`).
            lido[nome] = lido.get(nome, 0) + len(lote.tabela.column(nome))

    for nome, n in esperado.items():
        assert nome in lido, f"canal {nome!r} sumiu no ler()"
        assert lido[nome] == n, (
            f"canal {nome!r}: inspecionar disse {n} amostras, ler devolveu {lido[nome]}"
        )


def test_pid_ler_decodifica_o_layout_por_tick(leitor_pid: LeitorPiPid) -> None:
    """Regressao da issue #26: o corpo e intercalado por tick com quadro de
    tamanho variavel. A fixture grava uma rampa distinta por canal; ler
    canal a canal contiguo (o layout errado de 2026-08-29) embaralha tudo.
    `Speed` sai em kph porque o cabecalho declara escala 10 (divisor);
    `Steering` e `Throttle Position` saem em contagem (escala 1 e faixa
    que nao decide a direcao, ou escala ausente)."""
    from pi_gerar_pid_sintetico import contagem_esperada

    colunas: dict[str, list[float]] = {}
    for lote in leitor_pid.ler(FIXTURE_PID):
        for nome in lote.tabela.schema.names:
            if nome != "t_s":
                colunas.setdefault(nome, []).extend(
                    lote.tabela.column(nome).to_pylist()
                )

    speed = colunas["Speed"]
    assert speed[:3] == [100.0, 101.0, 102.0]
    assert speed[-1] == pytest.approx((contagem_esperada("Speed", 99)) / 10)
    throttle = colunas["Throttle Position"]
    assert throttle[:3] == [0.0, 5.0, 10.0]
    steering = colunas["Steering"]
    # Slot do tick 1 de cada bloco (indices 1 e 101) e marcador: nulo.
    assert steering[0] == 400.0 and steering[2] == 402.0
    assert steering[1] is None and steering[101] is None
    assert sum(v is None for v in steering) == 2
    assert steering[199] == 400.0 + 199


def test_pid_contagem_do_canal_igual_ao_laco_por_byte() -> None:
    """A leitura vetorizada de 2026-09-14 (secao Desempenho de
    `docs/pi-pid-medicao.md`) tem que dar a mesma contagem que o laco por
    janela e por byte que ela substituiu, nas tres larguras do acervo.
    A fixture sintetica so tem canal de 2 B; os de 1 e 4 B so apareciam
    no acervo real."""
    import numpy as np

    from saru_poc.readers.pi_pid import (
        _contagem_do_canal,
        _layout_do_bloco,
        _RegistroCanal,
    )

    registros = [
        _RegistroCanal(f"c{largura}_{taxa}", "", taxa, largura, 0.0, 1.0, 0.0)
        for largura, taxa in ((1, 100), (2, 50), (4, 20), (4, 1), (1, 5))
    ]
    tamanho_bloco = sum(r.taxa_hz * r.largura for r in registros)
    n_blocos = 7
    corpo_np = np.random.default_rng(26).integers(
        0, 256, size=(n_blocos, tamanho_bloco), dtype=np.uint8
    )
    for r, janelas in zip(registros, _layout_do_bloco(registros), strict=True):
        esperado = []
        for offset, largura in janelas:
            janela = corpo_np[:, offset : offset + largura].astype(np.int64)
            contagem = np.zeros(n_blocos, dtype=np.int64)
            for byte_idx in range(largura):
                contagem = (contagem << 8) | janela[:, byte_idx]
            esperado.append(contagem)
        esperado_np = np.stack(esperado, axis=1).reshape(-1)
        obtido = _contagem_do_canal(corpo_np, janelas, r.largura)
        assert obtido.dtype == np.int64
        assert np.array_equal(obtido, esperado_np), r.nome


def test_pid_fixture_caminho_feliz(leitor_pid: LeitorPiPid) -> None:
    cab = leitor_pid.inspecionar(FIXTURE_PID)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "pi_pid"
    assert len(cab.canais) == 3
    assert cab.venue_declarado == "Interlagos"
    assert cab.duracao_s == pytest.approx(2.0)
    assert cab.bruto["driver"] == "P.Sintetico"
    assert cab.bruto["vehicle"] == "KartFixture"
    assert cab.bruto["melhor_volta_texto"] == "01:13.461"
    assert cab.bruto["n_canais"] == "3"

    nomes = {c.nome_bruto for c in cab.canais}
    assert nomes == {"Steering", "Speed", "Throttle Position"}
    assert cab.taxas == (20.0, 50.0, 100.0)


def test_pid_valor_min_max_preenchidos(leitor_pid: LeitorPiPid) -> None:
    """O `.pid` declara faixa de fabrica de verdade: `valor_min`/`valor_max`
    tem que vir preenchidos, ao contrario do `.dat` LISTHEAD."""
    cab = leitor_pid.inspecionar(FIXTURE_PID)
    steering = next(c for c in cab.canais if c.nome_bruto == "Steering")
    assert steering.valor_min == -100.0
    assert steering.valor_max == 100.0
    assert steering.frequencia_hz == 100.0
    assert steering.n_amostras == 200


def test_pid_magic_invalido_levanta_erro_de_leitura(
    leitor_pid: LeitorPiPid, tmp_path: Path
) -> None:
    ruim = tmp_path / "ruim.pid"
    conteudo = bytearray(FIXTURE_PID.read_bytes())
    conteudo[0:4] = b"XXXX"
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="magic"):
        leitor_pid.inspecionar(ruim)


def test_pid_arquivo_menor_que_cabecalho_levanta_erro_de_leitura(
    leitor_pid: LeitorPiPid, tmp_path: Path
) -> None:
    curto = tmp_path / "curto.pid"
    curto.write_bytes(FIXTURE_PID.read_bytes()[:10])

    with pytest.raises(ErroDeLeitura):
        leitor_pid.inspecionar(curto)


def test_pid_marcador_de_fim_ausente_levanta_erro_de_leitura(
    leitor_pid: LeitorPiPid, tmp_path: Path
) -> None:
    """Regressao do B2: cabecalho e corpo discordando nunca pode virar
    leitura parcial silenciosa."""
    ruim = tmp_path / "sem_marcador.pid"
    conteudo = bytearray(FIXTURE_PID.read_bytes())
    # o marcador de fim fica logo apos o corpo; embaralha esses 4 bytes.
    _magic, n_blocos, tamanho_bloco, _tail = struct.unpack_from("<IIII", conteudo, 0)
    fim = 16 + n_blocos * tamanho_bloco
    conteudo[fim : fim + 4] = b"YYYY"
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="marcador de fim"):
        leitor_pid.inspecionar(ruim)


def test_pid_invariante_soma_quebrada_levanta_erro_de_leitura(
    leitor_pid: LeitorPiPid, tmp_path: Path
) -> None:
    """A invariante `sum(taxa_hz * largura) == tamanho_do_bloco` e ERRO DURO:
    troca a taxa do primeiro canal (`Steering`, 100 Hz) pra 50 Hz sem tocar
    no `tamanho_bloco` do cabecalho, quebrando a soma de propósito."""
    ruim = tmp_path / "soma_quebrada.pid"
    conteudo = bytearray(FIXTURE_PID.read_bytes())
    marcador = b"\x01\x20\x08\x28"
    primeiro = conteudo.index(marcador)
    # layout do registro: marcador(4) + id(1) + "Steering"(4+8) +
    # nome_curto(4+3) + unidade(4+2) = 30 bytes ate o inicio dos 3 u32.
    offset_taxa = primeiro + 30 + 8  # pula a, b (2 u32) ate o campo taxa_hz
    (taxa_atual,) = struct.unpack_from("<I", conteudo, offset_taxa)
    assert taxa_atual == 100, "offset da taxa nao bate com o layout esperado"
    struct.pack_into("<I", conteudo, offset_taxa, 50)
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="nao fecha"):
        leitor_pid.inspecionar(ruim)


# ---------------------------------------------------------------------------
# pi_listhead_dat: caminho feliz na fixture sintetica
# ---------------------------------------------------------------------------


def test_dat_formato_id_e_suporte_a_amostra(leitor_dat: LeitorPiListheadDat) -> None:
    assert leitor_dat.formato_id == "pi_listhead_dat"
    # Passou a suportar amostra em 29/08. O teste anterior afirmava False e
    # virou premissa velha assim que o `ler()` foi implementado.
    assert leitor_dat.suporta_amostra is True


def test_dat_ler_devolve_lote_por_taxa_com_eixo_de_tempo(
    leitor_dat: LeitorPiListheadDat,
) -> None:
    lotes = list(leitor_dat.ler(FIXTURE_DAT))
    assert lotes, "ler() nao emitiu lote nenhum"
    for lote in lotes:
        assert lote.frequencia_hz > 0
        assert "t_s" in lote.tabela.schema.names
        assert lote.tabela.num_rows > 0
    # Uma serie por taxa nativa, nunca reamostrada pra um eixo comum.
    taxas = [lote.frequencia_hz for lote in lotes]
    assert len(taxas) == len(set(taxas)) or all(
        a <= b for a, b in itertools.pairwise(taxas)
    )


def test_dat_ler_bate_com_o_que_inspecionar_declarou(
    leitor_dat: LeitorPiListheadDat,
) -> None:
    """Os dois leem o mesmo arquivo: divergencia entre eles e bug."""
    cab = leitor_dat.inspecionar(FIXTURE_DAT)
    esperado: dict[str, int] = {}
    for c in cab.canais:
        esperado[c.nome_bruto] = c.n_amostras

    lido: dict[str, int] = {}
    for lote in leitor_dat.ler(FIXTURE_DAT):
        for nome in lote.tabela.schema.names:
            if nome == "t_s":
                continue
            # Conta slots, nao valores validos: o slot do tick 1 dos canais
            # de 100 Hz e marcador de bloco e sai nulo (ver `_TICK_MARCADOR`).
            lido[nome] = lido.get(nome, 0) + len(lote.tabela.column(nome))

    for nome, n in esperado.items():
        assert nome in lido, f"canal {nome!r} sumiu no ler()"
        assert lido[nome] == n, (
            f"canal {nome!r}: inspecionar disse {n} amostras, ler devolveu {lido[nome]}"
        )


def test_dat_fixture_caminho_feliz(leitor_dat: LeitorPiListheadDat) -> None:
    cab = leitor_dat.inspecionar(FIXTURE_DAT)

    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "pi_listhead_dat"
    assert len(cab.canais) == 3
    assert cab.venue_declarado == "Interlagos"
    assert cab.bruto["driver"] == "P.Sintetico"
    assert cab.bruto["vehicle"] == "KartFixture"

    nomes = {c.nome_bruto for c in cab.canais}
    assert nomes == {"Steering", "Speed", "Throttle Positi"}
    assert cab.taxas == (20.0, 50.0, 100.0)


def test_dat_valor_min_max_sempre_nulos(leitor_dat: LeitorPiListheadDat) -> None:
    """A faixa nos bytes de `CHANNEL_INFO` e MEDIDA, nao declarada: nunca
    pode virar `valor_min`/`valor_max`, sob pena de evidencia fabricada."""
    cab = leitor_dat.inspecionar(FIXTURE_DAT)
    for canal in cab.canais:
        assert canal.valor_min is None
        assert canal.valor_max is None


def test_dat_nome_truncado_em_15_chars(leitor_dat: LeitorPiListheadDat) -> None:
    """O container real trunca em 15 chars uteis, nunca completa contra
    outra fonte."""
    cab = leitor_dat.inspecionar(FIXTURE_DAT)
    throttle = next(c for c in cab.canais if c.nome_bruto.startswith("Throttle"))
    assert throttle.nome_bruto == "Throttle Positi"
    assert len(throttle.nome_bruto) == 15


def test_dat_magic_invalido_levanta_erro_de_leitura(
    leitor_dat: LeitorPiListheadDat, tmp_path: Path
) -> None:
    ruim = tmp_path / "ruim.dat"
    conteudo = bytearray(FIXTURE_DAT.read_bytes())
    conteudo[0:8] = b"XXXXXXXX"
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="magic"):
        leitor_dat.inspecionar(ruim)


def test_dat_arquivo_menor_que_no_levanta_erro_de_leitura(
    leitor_dat: LeitorPiListheadDat, tmp_path: Path
) -> None:
    curto = tmp_path / "curto.dat"
    curto.write_bytes(FIXTURE_DAT.read_bytes()[:10])

    with pytest.raises(ErroDeLeitura):
        leitor_dat.inspecionar(curto)


def test_dat_node_size_invalido_levanta_erro_de_leitura(
    leitor_dat: LeitorPiListheadDat, tmp_path: Path
) -> None:
    """Regressao do B2: `node_size` que estoura o arquivo nunca pode virar
    cobertura parcial silenciosa do walk."""
    ruim = tmp_path / "node_size_ruim.dat"
    conteudo = bytearray(FIXTURE_DAT.read_bytes())
    # node_size do primeiro no (raiz "LISTHEAD") fica no offset 24, 4 bytes.
    struct.pack_into("<I", conteudo, 24, len(conteudo) * 2)
    ruim.write_bytes(bytes(conteudo))

    with pytest.raises(ErroDeLeitura, match="fora do arquivo"):
        leitor_dat.inspecionar(ruim)


def test_dat_le_sem_materializar_arquivo_inteiro(
    leitor_dat: LeitorPiListheadDat,
) -> None:
    """Mudanca obrigatoria do porte: o leitor usa `mmap`, nunca
    `Path.read_bytes()`. Nao da pra observar isso via `inspecionar()`
    diretamente; confere so o CODIGO do modulo (nao a docstring, que cita
    `path.read_bytes()` ao descrever o que o original fazia e foi
    descartado)."""
    import ast

    import saru_poc.readers.pi_listhead_dat as modulo

    arvore = ast.parse(Path(modulo.__file__).read_text(encoding="utf-8"))
    chamadas_read_bytes = [
        n
        for n in ast.walk(arvore)
        if isinstance(n, ast.Attribute) and n.attr == "read_bytes"
    ]
    assert not chamadas_read_bytes, "modulo chama .read_bytes() em algum lugar"
    assert "mmap.mmap(" in Path(modulo.__file__).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Invariantes gerais
# ---------------------------------------------------------------------------


def _checar_invariantes_pid(cab: Cabecalho) -> None:
    # A invariante rate*largura == tamanho_do_bloco ja e ERRO DURO dentro do
    # proprio LeitorPiPid.inspecionar: se o arquivo abriu sem levantar
    # ErroDeLeitura, ela ja fechou. Aqui so confere o que da pra ver de fora.
    assert len(cab.canais) > 0
    for c in cab.canais:
        assert c.frequencia_hz > 0, f"canal {c.nome_bruto} com frequencia <= 0"
        assert c.nome_bruto.strip() != "", "canal com nome vazio"


def _checar_invariantes_dat(cab: Cabecalho) -> None:
    assert len(cab.canais) > 0
    for c in cab.canais:
        assert c.frequencia_hz > 0, f"canal {c.nome_bruto} com frequencia <= 0"
        assert c.nome_bruto.strip() != "", "canal com nome vazio"
        assert c.valor_min is None
        assert c.valor_max is None


def test_invariantes_na_fixture_pid(leitor_pid: LeitorPiPid) -> None:
    _checar_invariantes_pid(leitor_pid.inspecionar(FIXTURE_PID))


def test_invariantes_na_fixture_dat(leitor_dat: LeitorPiListheadDat) -> None:
    _checar_invariantes_dat(leitor_dat.inspecionar(FIXTURE_DAT))


# ---------------------------------------------------------------------------
# Cruzamento .dat x .pid, na fixture sintetica (independente do acervo)
# ---------------------------------------------------------------------------


_SUFIXO_DUPLICATA = re.compile(r"~\d+$")


def _taxas_por_nome_truncado(canais, truncar: bool) -> dict[str, list[float]]:
    """Agrupa a taxa de cada canal pelo nome truncado em 15 chars (o limite
    do container `.dat`). O `.pid` NAO desambigua nome repetido (o acervo F3
    tem dois `Oil Temp` e dois `Fuel Pressure`), enquanto o `.dat` os
    diferencia com sufixo `~1` gravado no proprio campo de nome (medido:
    `'Oil Temp~1'`). Este helper tira esse sufixo dos dois lados antes de
    agrupar, pra comparar o mesmo conceito: por isso o valor e uma LISTA de
    taxas, nao um escalar, e a comparacao usa a lista ordenada, nao o ultimo
    valor de um dict que sobrescreveria o outro em silencio.
    """
    agrupado: dict[str, list[float]] = {}
    for canal in canais:
        nome = canal.nome_bruto[:15] if truncar else canal.nome_bruto
        nome = _SUFIXO_DUPLICATA.sub("", nome)
        agrupado.setdefault(nome, []).append(canal.frequencia_hz)
    return {nome: sorted(taxas) for nome, taxas in agrupado.items()}


def test_cruzamento_fixture_pid_x_dat(
    leitor_pid: LeitorPiPid, leitor_dat: LeitorPiListheadDat
) -> None:
    """Os nomes casam depois de truncar os do `.pid` em 15 chars, a taxa e
    identica canal a canal, e o venue e o mesmo. Mesma validacao cruzada
    exigida contra o acervo real, so que sem depender dele."""
    cab_pid = leitor_pid.inspecionar(FIXTURE_PID)
    cab_dat = leitor_dat.inspecionar(FIXTURE_DAT)

    assert cab_pid.venue_declarado == cab_dat.venue_declarado

    taxas_pid = _taxas_por_nome_truncado(cab_pid.canais, truncar=True)
    taxas_dat = _taxas_por_nome_truncado(cab_dat.canais, truncar=False)

    assert set(taxas_pid) == set(taxas_dat)
    for nome, lista_pid in taxas_pid.items():
        assert lista_pid == taxas_dat[nome], (
            f"canal {nome!r}: taxas {lista_pid} Hz no .pid vs "
            f"{taxas_dat[nome]} Hz no .dat"
        )


# ---------------------------------------------------------------------------
# Contra o acervo real, quando montado nesta maquina
# ---------------------------------------------------------------------------


def _todos_pid_do_acervo() -> list[Path]:
    if not CONFIG.acervo_root.exists():
        return []
    return sorted(CONFIG.acervo_root.rglob("*.pid"))


def _todos_dat_listhead_do_acervo() -> list[Path]:
    """So os `.dat` que comecam com `LISTHEAD`: 12 dos 37 `.dat` do acervo
    sao outra familia, desconhecida (ver `readers/formatos.py`)."""
    if not CONFIG.acervo_root.exists():
        return []
    achados = []
    for f in sorted(CONFIG.acervo_root.rglob("*.dat")):
        try:
            with f.open("rb") as fh:
                if fh.read(8) == b"LISTHEAD":
                    achados.append(f)
        except OSError:
            continue
    return achados


@pytest.mark.skipif(not CONFIG.acervo_root.exists(), reason="acervo nao montado")
def test_todos_os_pid_do_acervo_abrem(leitor_pid: LeitorPiPid) -> None:
    arquivos = _todos_pid_do_acervo()
    if not arquivos:
        pytest.skip("nenhum .pid no acervo")

    falhas: list[str] = []
    todas_taxas: set[float] = set()
    todos_venues: set[str] = set()
    contagens_canais: list[int] = []

    for f in arquivos:
        try:
            cab = leitor_pid.inspecionar(f)
        except ErroDeLeitura as e:
            falhas.append(f"{f.name}: {e}")
            continue
        _checar_invariantes_pid(cab)
        todas_taxas.update(cab.taxas)
        if cab.venue_declarado:
            todos_venues.add(cab.venue_declarado)
        contagens_canais.append(len(cab.canais))

    assert not falhas, "arquivos .pid que falharam:\n" + "\n".join(falhas)
    print(f"\n{len(arquivos)} arquivos .pid abriram sem erro")
    print(f"canais: min={min(contagens_canais)} max={max(contagens_canais)}")
    print(f"taxas encontradas (Hz): {sorted(todas_taxas)}")
    print(f"venues distintos: {sorted(todos_venues)}")


@pytest.mark.skipif(not CONFIG.acervo_root.exists(), reason="acervo nao montado")
def test_todos_os_dat_listhead_do_acervo_abrem(
    leitor_dat: LeitorPiListheadDat,
) -> None:
    arquivos = _todos_dat_listhead_do_acervo()
    if not arquivos:
        pytest.skip("nenhum .dat LISTHEAD no acervo")

    falhas: list[str] = []
    todas_taxas: set[float] = set()
    todos_venues: set[str] = set()
    contagens_canais: list[int] = []

    for f in arquivos:
        try:
            cab = leitor_dat.inspecionar(f)
        except ErroDeLeitura as e:
            falhas.append(f"{f.name}: {e}")
            continue
        _checar_invariantes_dat(cab)
        todas_taxas.update(cab.taxas)
        if cab.venue_declarado:
            todos_venues.add(cab.venue_declarado)
        contagens_canais.append(len(cab.canais))

    assert not falhas, "arquivos .dat que falharam:\n" + "\n".join(falhas)
    print(f"\n{len(arquivos)} arquivos .dat LISTHEAD abriram sem erro")
    print(f"canais: min={min(contagens_canais)} max={max(contagens_canais)}")
    print(f"taxas encontradas (Hz): {sorted(todas_taxas)}")
    print(f"venues distintos: {sorted(todos_venues)}")


@pytest.mark.skipif(not CONFIG.acervo_root.exists(), reason="acervo nao montado")
def test_cruzamento_dat_x_pid_mesma_sessao_no_acervo(
    leitor_pid: LeitorPiPid, leitor_dat: LeitorPiListheadDat
) -> None:
    """`_P.Piquet000991.dat` e `P.Piquet000991.pid` sao a mesma sessao em
    dois containers diferentes, decodificados por dois parsers
    independentes: os nomes casam truncando o `.pid` em 15 chars, a taxa e
    identica canal a canal, e o venue e o mesmo. Validacao cruzada sem
    ground truth externo e sem ler um unico float de amostra.
    """
    candidatos_pid = [
        f for f in _todos_pid_do_acervo() if f.name == "P.Piquet000991.pid"
    ]
    candidatos_dat = [
        f for f in _todos_dat_listhead_do_acervo() if f.name == "_P.Piquet000991.dat"
    ]
    if not candidatos_pid or not candidatos_dat:
        pytest.skip("par P.Piquet000991 nao encontrado no acervo")

    cab_pid = leitor_pid.inspecionar(candidatos_pid[0])
    cab_dat = leitor_dat.inspecionar(candidatos_dat[0])

    assert cab_pid.venue_declarado == cab_dat.venue_declarado == "Curitiba"

    taxas_pid = _taxas_por_nome_truncado(cab_pid.canais, truncar=True)
    taxas_dat = _taxas_por_nome_truncado(cab_dat.canais, truncar=False)

    comuns = set(taxas_pid) & set(taxas_dat)
    assert len(comuns) >= 40, (
        f"so {len(comuns)} canais em comum entre .pid e .dat da mesma "
        "sessao, esperava a maioria dos ~48 canais"
    )
    divergentes = [nome for nome in comuns if taxas_pid[nome] != taxas_dat[nome]]
    assert not divergentes, (
        f"canais com taxa divergente entre .pid e .dat da mesma sessao: {divergentes}"
    )
