"""Testes dos leitores AiM RS2 `.gpk` (formato_id aim_gpk) e `.rrk`
(formato_id aim_rrk).

Fixtures sinteticas em `tests/fixtures/aim_gpk_*.gpk` e `aim_rrk_*.rrk`
(geradas por `tests/fixtures/gerar_aim_gpk_rrk_sintetico.py`) exercitam o
framing de segmento (assinatura dupla + pseudo-registro de contador fixo
256 + registros de tamanho fixo), o caso de multiplos segmentos (inclusive
um segmento final sem nenhum registro, medido em uso real no acervo) e o
caso de tamanho quebrado (sobra de bytes que nao fecha um registro
inteiro).

Os 68 `.gpk` e 67 `.rrk` reais do acervo sao testados a parte, com
`pytest.skip` quando o acervo nao esta montado: nao versionamos arquivo
real, tem nome de piloto real.

Nenhum dos dois leitores declara canal (`Cabecalho.canais == ()`): a
semantica do payload (se carrega coordenada GPS ou outra coisa) nao foi
confirmada contra a amostra real, ver a docstring de `aim_gpk.py` e
`aim_rrk.py` para o registro completo das tentativas de validacao
geodesica contra o par `.xrk` de mesmo radical.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from saru_poc.config import CONFIG
from saru_poc.readers.aim_gpk import LeitorAimGpk
from saru_poc.readers.aim_rrk import LeitorAimRrk
from saru_poc.readers.base import Cabecalho, ErroDeLeitura

FIXTURES = Path(__file__).parent / "fixtures"

GPK_COMPLETO = FIXTURES / "aim_gpk_completo.gpk"
GPK_MULTI_SEGMENTO = FIXTURES / "aim_gpk_multi_segmento.gpk"
GPK_TAMANHO_QUEBRADO = FIXTURES / "aim_gpk_tamanho_quebrado.gpk"

RRK_COMPLETO = FIXTURES / "aim_rrk_completo.rrk"
RRK_MULTI_SEGMENTO = FIXTURES / "aim_rrk_multi_segmento.rrk"


@pytest.fixture
def leitor_gpk() -> LeitorAimGpk:
    return LeitorAimGpk()


@pytest.fixture
def leitor_rrk() -> LeitorAimRrk:
    return LeitorAimRrk()


def _todos_gpk_do_acervo() -> list[Path]:
    if not CONFIG.acervo_root.exists():
        return []
    return sorted(CONFIG.acervo_root.rglob("*.gpk"))


def _todos_rrk_do_acervo() -> list[Path]:
    if not CONFIG.acervo_root.exists():
        return []
    return sorted(CONFIG.acervo_root.rglob("*.rrk"))


# ---------------------------------------------------------------------------
# Contrato basico
# ---------------------------------------------------------------------------


def test_gpk_formato_id_e_suporte_a_amostra(leitor_gpk: LeitorAimGpk) -> None:
    assert leitor_gpk.formato_id == "aim_gpk"
    assert leitor_gpk.suporta_amostra is False


def test_rrk_formato_id_e_suporte_a_amostra(leitor_rrk: LeitorAimRrk) -> None:
    assert leitor_rrk.formato_id == "aim_rrk"
    assert leitor_rrk.suporta_amostra is False


def test_gpk_ler_levanta_not_implemented(leitor_gpk: LeitorAimGpk) -> None:
    with pytest.raises(NotImplementedError):
        list(leitor_gpk.ler(GPK_COMPLETO))


def test_rrk_ler_levanta_not_implemented(leitor_rrk: LeitorAimRrk) -> None:
    with pytest.raises(NotImplementedError):
        list(leitor_rrk.ler(RRK_COMPLETO))


# ---------------------------------------------------------------------------
# .gpk: fixture completa, um segmento, 5 registros
# ---------------------------------------------------------------------------


def test_gpk_completo_nao_declara_canal(leitor_gpk: LeitorAimGpk) -> None:
    """Semantica do payload nao confirmada: canais=() e resultado
    legitimo, nao falha de leitura."""
    cab = leitor_gpk.inspecionar(GPK_COMPLETO)
    assert isinstance(cab, Cabecalho)
    assert cab.formato_id == "aim_gpk"
    assert cab.canais == ()


def test_gpk_completo_conta_registros_e_segmento(leitor_gpk: LeitorAimGpk) -> None:
    cab = leitor_gpk.inspecionar(GPK_COMPLETO)
    assert cab.bruto["n_segmentos"] == "1"
    assert cab.bruto["n_registros_total"] == "5"
    assert cab.bruto["tamanho_registro_bytes"] == "144"


def test_gpk_completo_contador_min_max_e_passo_dominante(
    leitor_gpk: LeitorAimGpk,
) -> None:
    """Contadores da fixture: 51, 71, 91, 110, 130 (passos 20,20,19,20)."""
    cab = leitor_gpk.inspecionar(GPK_COMPLETO)
    assert cab.bruto["contador_min"] == "51"
    assert cab.bruto["contador_max"] == "130"
    assert cab.bruto["passo_contador_dominante"] == "20"


def test_gpk_completo_nao_afirma_captura_nem_venue(leitor_gpk: LeitorAimGpk) -> None:
    """Sem campo de data/hora/venue confirmado no framing: fica None, nao
    default silencioso."""
    cab = leitor_gpk.inspecionar(GPK_COMPLETO)
    assert cab.capturado_em is None
    assert cab.venue_declarado is None
    assert cab.duracao_s is None


# ---------------------------------------------------------------------------
# .gpk: multiplos segmentos, o ultimo sem nenhum registro
# ---------------------------------------------------------------------------


def test_gpk_multi_segmento_soma_registros_dos_dois_segmentos(
    leitor_gpk: LeitorAimGpk,
) -> None:
    cab = leitor_gpk.inspecionar(GPK_MULTI_SEGMENTO)
    assert cab.bruto["n_segmentos"] == "2"
    assert cab.bruto["n_registros_total"] == "3"
    assert cab.bruto["registros_por_segmento"] == "3,0"


# ---------------------------------------------------------------------------
# .rrk: fixture completa e multi-segmento
# ---------------------------------------------------------------------------


def test_rrk_completo_nao_declara_canal(leitor_rrk: LeitorAimRrk) -> None:
    cab = leitor_rrk.inspecionar(RRK_COMPLETO)
    assert cab.formato_id == "aim_rrk"
    assert cab.canais == ()


def test_rrk_completo_conta_registros(leitor_rrk: LeitorAimRrk) -> None:
    cab = leitor_rrk.inspecionar(RRK_COMPLETO)
    assert cab.bruto["n_segmentos"] == "1"
    assert cab.bruto["n_registros_total"] == "5"
    assert cab.bruto["tamanho_registro_bytes"] == "64"


def test_rrk_completo_passo_dominante_e_o_dobro_do_gpk(
    leitor_rrk: LeitorAimRrk,
) -> None:
    """Contadores da fixture: 51, 91, 131, 170, 210 (passos 40,40,39,40)."""
    cab = leitor_rrk.inspecionar(RRK_COMPLETO)
    assert cab.bruto["passo_contador_dominante"] == "40"


def test_rrk_multi_segmento_ultimo_segmento_sem_registro(
    leitor_rrk: LeitorAimRrk,
) -> None:
    """3 segmentos, o ultimo so com o cabecalho (0 registros): o mesmo
    padrao medido no acervo real. 0 e legitimo, nao e erro."""
    cab = leitor_rrk.inspecionar(RRK_MULTI_SEGMENTO)
    assert cab.bruto["n_segmentos"] == "3"
    assert cab.bruto["registros_por_segmento"] == "2,3,0"
    assert cab.bruto["n_registros_total"] == "5"


# ---------------------------------------------------------------------------
# Malformado
# ---------------------------------------------------------------------------


def test_gpk_tamanho_quebrado_levanta_erro(leitor_gpk: LeitorAimGpk) -> None:
    with pytest.raises(ErroDeLeitura):
        leitor_gpk.inspecionar(GPK_TAMANHO_QUEBRADO)


def test_gpk_sem_assinatura_levanta_erro(
    tmp_path: Path, leitor_gpk: LeitorAimGpk
) -> None:
    ruim = tmp_path / "sem_assinatura.gpk"
    ruim.write_bytes(b"lixo qualquer sem assinatura PROV aqui dentro")
    with pytest.raises(ErroDeLeitura):
        leitor_gpk.inspecionar(ruim)


def test_gpk_arquivo_vazio_levanta_erro(
    tmp_path: Path, leitor_gpk: LeitorAimGpk
) -> None:
    vazio = tmp_path / "vazio.gpk"
    vazio.write_bytes(b"")
    with pytest.raises(ErroDeLeitura):
        leitor_gpk.inspecionar(vazio)


def test_gpk_arquivo_inexistente_levanta_erro(
    tmp_path: Path, leitor_gpk: LeitorAimGpk
) -> None:
    with pytest.raises(ErroDeLeitura):
        leitor_gpk.inspecionar(tmp_path / "nao_existe.gpk")


def test_rrk_sem_assinatura_levanta_erro(
    tmp_path: Path, leitor_rrk: LeitorAimRrk
) -> None:
    ruim = tmp_path / "sem_assinatura.rrk"
    ruim.write_bytes(b"lixo qualquer sem assinatura HEAD aqui dentro")
    with pytest.raises(ErroDeLeitura):
        leitor_rrk.inspecionar(ruim)


def test_rrk_arquivo_vazio_levanta_erro(
    tmp_path: Path, leitor_rrk: LeitorAimRrk
) -> None:
    vazio = tmp_path / "vazio.rrk"
    vazio.write_bytes(b"")
    with pytest.raises(ErroDeLeitura):
        leitor_rrk.inspecionar(vazio)


def test_rrk_pseudo_registro_com_contador_errado_levanta_erro(
    tmp_path: Path, leitor_rrk: LeitorAimRrk
) -> None:
    """O contador do pseudo-registro e sempre 256 nos 67 arquivos do
    acervo: se vier diferente, o framing assumido nao bate, e o leitor
    tem que recusar em vez de seguir com um offset errado."""
    import struct

    ruim = bytearray(b"HEAD\x00\x01" * 2 + b"\x00" * 16)
    ruim += b"NSOL" + struct.pack("<I", 999) + b"\x00" * 8
    caminho = tmp_path / "contador_pseudo_errado.rrk"
    caminho.write_bytes(bytes(ruim))
    with pytest.raises(ErroDeLeitura):
        leitor_rrk.inspecionar(caminho)


# ---------------------------------------------------------------------------
# Acervo real
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _todos_gpk_do_acervo(), reason="acervo nao montado nesta maquina"
)
def test_le_os_68_gpk_reais_do_acervo(leitor_gpk: LeitorAimGpk) -> None:
    arquivos = _todos_gpk_do_acervo()
    # Piso, nao numero cravado: o acervo e uma pasta VIVA (a importacao do
    # Nelson Piquet de 30/08 levou os .xrk de 66 pra 224). O que o teste quer
    # provar e que o leitor da conta de TUDO que existe no acervo, e cravar a
    # contagem so garantia falha toda vez que chega arquivo novo -- ruido, nao
    # regressao.
    assert len(arquivos) >= 68

    falharam: list[str] = []
    for caminho in arquivos:
        try:
            cab = leitor_gpk.inspecionar(caminho)
        except ErroDeLeitura:
            falharam.append(caminho.name)
            continue
        assert cab.formato_id == "aim_gpk"
        assert cab.canais == ()
        assert int(cab.bruto["n_registros_total"]) > 0

    print(f"\n.gpk do acervo: {len(arquivos) - len(falharam)}/{len(arquivos)} abriram")
    assert not falharam, f"falharam: {falharam}"


@pytest.mark.skipif(
    not _todos_rrk_do_acervo(), reason="acervo nao montado nesta maquina"
)
def test_le_os_67_rrk_reais_do_acervo(leitor_rrk: LeitorAimRrk) -> None:
    arquivos = _todos_rrk_do_acervo()
    # Piso, nao numero cravado: o acervo e uma pasta VIVA (a importacao do
    # Nelson Piquet de 30/08 levou os .xrk de 66 pra 224). O que o teste quer
    # provar e que o leitor da conta de TUDO que existe no acervo, e cravar a
    # contagem so garantia falha toda vez que chega arquivo novo -- ruido, nao
    # regressao.
    assert len(arquivos) >= 67

    falharam: list[str] = []
    multi_segmento = 0
    for caminho in arquivos:
        try:
            cab = leitor_rrk.inspecionar(caminho)
        except ErroDeLeitura:
            falharam.append(caminho.name)
            continue
        assert cab.formato_id == "aim_rrk"
        assert cab.canais == ()
        if int(cab.bruto["n_segmentos"]) > 1:
            multi_segmento += 1

    print(
        f"\n.rrk do acervo: {len(arquivos) - len(falharam)}/{len(arquivos)} "
        f"abriram, {multi_segmento} com mais de 1 segmento"
    )
    assert not falharam, f"falharam: {falharam}"
    # Medido em 2026-08-29: 12 dos 67 caminhos tem mais de 1 segmento (sao
    # so 3 sessoes distintas por conteudo, cada uma salva em ate 4 pastas
    # diferentes do acervo). Ver docstring de aim_rrk.py.
    assert multi_segmento == 12
