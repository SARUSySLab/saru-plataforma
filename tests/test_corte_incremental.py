"""Corte de volta ao vivo, comparado contra o corte offline como oraculo.

O criterio de pronto desta peca nao e "roda sem erro": e ACHAR AS MESMAS
VOLTAS que `corte_voltas.py` acha na mesma gravacao. Se o ao vivo discordar do
relatorio que o piloto le depois, o produto passa a ter duas verdades.
"""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SARU_CICLO_SARUE", "0")

from saru_poc.pipeline.corte_incremental import CorteIncremental  # noqa: E402

# Interlagos, 16 voltas por beacon. Escolhida por ser a gravacao com mais
# voltas fechadas do acervo local que tem pista resolvida.
GRAVACAO_BEACON = "671afe56-6128-45fa-a200-ae53837e8ca1"


def test_contador_de_volta_fecha_volta_no_degrau():
    corte = CorteIncremental()
    voltas = []
    # cinco marcos de contador dao QUATRO passagens e portanto TRES voltas: a
    # primeira amostra so estabelece o valor de partida, e o primeiro degrau
    # fecha o out lap, que nao e volta medida.
    for i in range(5):
        v = corte.processar(i * 90.0, {"lap_number": float(i)})
        if v:
            voltas.append(v)
    assert [v.numero for v in voltas] == [1, 2, 3]
    assert all(abs(v.tempo_s - 90.0) < 1e-9 for v in voltas)
    assert corte.estado.fonte == "lap_number"


def test_contador_que_volta_atras_nao_fecha_volta():
    # decodificacao ruim faz o contador cair; carro nao anda de re na linha
    corte = CorteIncremental()
    corte.processar(0.0, {"lap_number": 5.0})
    corte.processar(90.0, {"lap_number": 6.0})    # fecha o out lap
    corte.processar(180.0, {"lap_number": 7.0})   # fecha a volta 1
    assert corte.processar(185.0, {"lap_number": 6.0}) is None
    assert len(corte.estado.voltas) == 1


def test_debounce_impede_volta_de_meio_segundo():
    # GPS tremendo com o carro parado na box entrando e saindo do gate
    corte = CorteIncremental(linha_lat=-23.7014, linha_lon=-46.6969)
    dentro = {"gps_lat": -23.7014, "gps_lon": -46.6969}
    fora = {"gps_lat": -23.7100, "gps_lon": -46.7100}
    fechadas = 0
    for i in range(20):
        v = corte.processar(i * 0.5, dentro if i % 2 == 0 else fora)
        if v:
            fechadas += 1
    assert fechadas == 0, "tremida dentro do gate nao pode virar volta"


def test_sem_canal_nenhum_declara_o_motivo_em_vez_de_dizer_zero_voltas():
    corte = CorteIncremental()
    corte.processar(0.0, {"speed": 40.0})
    assert corte.estado.voltas == []
    assert corte.estado.motivo is not None
    assert "não há como saber" in corte.estado.motivo


def test_volta_atual_comeca_em_um_e_anda_com_as_passagens():
    corte = CorteIncremental()
    assert corte.estado.volta_atual == 1
    corte.processar(0.0, {"lap_number": 0.0})
    corte.processar(90.0, {"lap_number": 1.0})   # cruzou a linha, out lap fechado
    assert corte.estado.volta_atual == 1
    corte.processar(180.0, {"lap_number": 2.0})  # volta 1 fechada
    assert corte.estado.volta_atual == 2


@pytest.fixture
def conexao():
    try:
        from saru_poc.db import connect, ping

        ping()
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"postgres indisponivel: {e}")
    with connect() as conn:
        yield conn


def test_bate_com_o_corte_offline_na_mesma_gravacao(conexao):
    """O oraculo e o que ja esta no banco, cortado pelo pipeline offline.

    A comparacao tem que ser DA MESMA FONTE. A primeira versao deste teste
    comparava o corte incremental por contador contra um oraculo que o offline
    tinha cortado por GPS, e claro que os instantes discordavam: sao dois
    sensores diferentes marcando a mesma linha. Aqui a gravacao usada foi
    cortada por GPS, entao o incremental roda por GPS tambem.
    """
    linha = conexao.execute(
        """select v.session_id, l.ref_lat, l.ref_lon
             from volta v join gravacao g on g.id = v.session_id
             join layout l on l.id = g.layout_id
            where v.origem = 'gps' and l.ref_lat is not null
            group by v.session_id, l.ref_lat, l.ref_lon
            order by count(*) desc limit 1""",
    ).fetchone()
    if linha is None:
        pytest.skip("nenhuma gravacao cortada por GPS neste banco")
    gravacao_id, ref_lat, ref_lon = linha

    oraculo = conexao.execute(
        "select t_inicio_s, t_fim_s from volta where session_id = %s order by lap_number",
        (gravacao_id,),
    ).fetchall()

    # Le pelo MESMO caminho do corte offline: `par_gps` devolve o par de
    # canais na mesma serie e `.valores()` aplica o fator de escala do mapa.
    # Ler a coluna crua do Parquet daria coordenada em outra unidade, e a
    # primeira versao deste teste caiu exatamente nisso: a distancia ate a
    # referencia deu 329 mil quilometros e nenhuma amostra entrou no gate.
    from saru_poc.pipeline.corte_voltas import par_gps
    from saru_poc.pipeline.leitura import ler_colunas as _ler

    par = par_gps(conexao, gravacao_id)
    if par is None:
        pytest.skip("gravacao sem par de GPS mapeado na mesma serie")
    canal_lat, canal_lon = par
    dados = _ler(canal_lat.uri, [canal_lat.nome_bruto, canal_lon.nome_bruto])
    if "t_s" not in dados:
        pytest.skip("serie de GPS sem eixo de tempo materializado")
    lat = canal_lat.valores(dados)
    lon = canal_lon.valores(dados)

    corte = CorteIncremental(linha_lat=float(ref_lat), linha_lon=float(ref_lon))
    for t, la, lo in zip(dados["t_s"], lat, lon, strict=False):
        if la != la or lo != lo:
            continue
        corte.processar(float(t), {"gps_lat": float(la), "gps_lon": float(lo)})

    ao_vivo = corte.estado.voltas
    assert corte.estado.fonte == "gps"
    assert len(ao_vivo) == len(oraculo), (
        f"ao vivo achou {len(ao_vivo)} voltas, offline achou {len(oraculo)}"
    )
    # Tolerancia de uma amostra: o gate e o mesmo e o instante e o mesmo; o que
    # pode diferir e qual amostra dentro do raio foi tomada como a passagem.
    for viva, (inicio, fim) in zip(ao_vivo, oraculo, strict=False):
        assert abs(viva.t_inicio_s - float(inicio)) <= 1.0
        assert abs(viva.t_fim_s - float(fim)) <= 1.0
