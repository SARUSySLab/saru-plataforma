"""Calibracao de zero POR GRAVACAO (issue #36).

`Acc Long`/`Acc Lat` do `.pid` do F3 fecham com r = 1,000 contra o `.dat` da
mesma sessao (mesmo fator, -0,02586 G por contagem), mas o offset — o zero do
sensor, ajustado pelo Pi Toolbox — muda de sessao pra sessao: 12,85 a 13,18 G
no longitudinal, 12,44 a 12,50 G no lateral (23 pares medidos, ver
`docs/pi-pid-medicao.md` secao 3 e 7). Uma constante unica erraria ate 0,17 G
(1,6 m/s2) no pior caso, quase metade do limiar de frenagem de -3,5 m/s2.

`mapeamento_canal` (`seeds/aliases.yaml`) e por PERFIL: o mesmo fator/offset
vale pra toda gravacao do perfil `pi_pid`. Nao ha como guardar ali um numero
que muda arquivo a arquivo — essa e a lacuna de esquema que a migration 025
(`calibracao_canal_gravado`) preenche.

Este modulo mede o offset direto do arquivo (media da contagem crua num
trecho de carro parado, `Speed` = 0 sustentado por `_MIN_AMOSTRAS_TRECHO`) e
grava uma linha por canal calibrado. Roda na etapa de ingestao, depois que o
leitor ja escreveu a serie bruta em Parquet — mede o Parquet, nao reabre o
`.pid`. Sem trecho parado longo o bastante, NENHUMA linha e escrita: o canal
fica fora do inventario daquela gravacao (`pipeline/ingestao.py` so aceita o
canonico quando ha calibracao), documentado no motivo devolvido aqui.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyarrow.parquet as pq

from ..storage import CAMADA_BRUTA, PonteiroSerie, caminho_de

#: Coluna bruta do `.pid` -> canal canonico que a calibracao alimenta.
CANAL_BRUTO_PARA_CANONICO: dict[str, str] = {
    "Acc Long": "lon_acc",
    "Acc Lat": "lat_acc",
}

#: Canais canonicos que so entram no vocabulario da gravacao QUANDO calibrados
#: (ao contrario dos demais canais do perfil, mapeados igual em toda
#: gravacao). Consumido por `pipeline/ingestao.py::_escrever_canais`.
CANONICOS_CALIBRADOS_POR_SESSAO: frozenset[str] = frozenset(
    CANAL_BRUTO_PARA_CANONICO.values()
)

#: Formatos em que esses canonicos dependem da calibracao por sessao. Nos
#: demais o mapa do perfil ja entrega o canal em unidade fisica e o canonico
#: entra direto. Sem esta restricao, `.xrk`, `.dat` e `.ld` perdiam G lateral
#: e longitudinal em toda gravacao (issue #51).
FORMATOS_CALIBRADOS_POR_SESSAO: frozenset[str] = frozenset({"pi_pid"})

_COLUNA_REFERENCIA = "Speed"
#: Sensor de velocidade grava 0 exato quando parado (0,1 kph por contagem,
#: divisao exata): a folga aqui e so pra reamostragem/instabilidade numerica,
#: nao pra cobrir baixa velocidade de verdade.
_EPSILON_KPH = 0.05
#: 2 s a 50 Hz. Trecho mais curto vira ruido de sensor, nao zero confiavel:
#: o residuo do ajuste linear contra o .dat (secao 3 da medicao) e da ordem
#: de 0,01-0,04 G, e a media de poucas amostras nao afoga isso.
_MIN_AMOSTRAS_TRECHO = 100
_METODO = "zero_estacionario_speed"


@dataclass(frozen=True)
class ResultadoCalibracao:
    canonicos_calibrados: frozenset[str]
    motivo_faltante: str | None


def _maior_trecho_parado(speed: np.ndarray) -> tuple[int, int] | None:
    """Indices [inicio, fim) do maior trecho contiguo com `Speed` ~ 0.

    `None` quando nenhum trecho chega em `_MIN_AMOSTRAS_TRECHO`: nao ha carro
    parado identificavel neste arquivo, e adivinhar o offset esta fora de
    cogitacao (restricao da issue #36).
    """
    parado = np.abs(speed) <= _EPSILON_KPH
    if not parado.any():
        return None

    indices = np.flatnonzero(parado)
    quebras = np.flatnonzero(np.diff(indices) != 1)
    trechos = np.split(indices, quebras + 1)

    melhor: tuple[int, int] | None = None
    melhor_tamanho = 0
    for trecho in trechos:
        if trecho.size > melhor_tamanho:
            melhor_tamanho = trecho.size
            melhor = (int(trecho[0]), int(trecho[-1]) + 1)

    if melhor_tamanho < _MIN_AMOSTRAS_TRECHO:
        return None
    return melhor


def _serie_bruta_50hz(ponteiros: list[PonteiroSerie]) -> PonteiroSerie | None:
    """O ponteiro da serie bruta que carrega `Speed` e ao menos um dos canais
    a calibrar. `Acc Long`/`Acc Lat` e `Speed` sao os tres a 50 Hz no `.pid`
    (ver `docs/pi-pid-medicao.md`), sempre na MESMA serie: o leitor emite um
    Lote por taxa, nunca um por canal.
    """
    for p in ponteiros:
        if p.camada != CAMADA_BRUTA or _COLUNA_REFERENCIA not in p.colunas:
            continue
        if any(c in p.colunas for c in CANAL_BRUTO_PARA_CANONICO):
            return p
    return None


def calibrar_offsets_pi_pid(
    conn, gravacao_id: str, ponteiros: list[PonteiroSerie]
) -> ResultadoCalibracao:
    """Mede o zero de `Acc Long`/`Acc Lat` nesta gravacao e grava o offset.

    Le a serie bruta que `escrever_serie` acabou de escrever (nao reabre o
    `.pid`), acha o maior trecho de carro parado por `Speed` e grava a media
    da contagem crua de cada canal presente nesse trecho. Idempotente: roda
    de novo (reingestao) e substitui a linha anterior.
    """
    ponteiro = _serie_bruta_50hz(ponteiros)
    if ponteiro is None:
        return ResultadoCalibracao(
            frozenset(),
            "lon_acc e lat_acc fora do inventario: arquivo sem serie bruta "
            "com Speed e Acc Long/Acc Lat na mesma taxa",
        )

    tabela = pq.read_table(
        caminho_de(ponteiro),
        columns=["t_s", _COLUNA_REFERENCIA, *CANAL_BRUTO_PARA_CANONICO],
    )
    colunas_presentes = [
        c for c in CANAL_BRUTO_PARA_CANONICO if c in tabela.column_names
    ]
    if not colunas_presentes:
        return ResultadoCalibracao(
            frozenset(),
            "lon_acc e lat_acc fora do inventario: arquivo sem Acc Long/Acc Lat",
        )

    speed = tabela.column(_COLUNA_REFERENCIA).to_numpy(zero_copy_only=False)
    trecho = _maior_trecho_parado(speed)
    if trecho is None:
        nomes = " e ".join(CANAL_BRUTO_PARA_CANONICO[c] for c in colunas_presentes)
        return ResultadoCalibracao(
            frozenset(),
            f"{nomes} fora do inventario: sem trecho de carro parado (Speed "
            f"<= {_EPSILON_KPH} kph) com pelo menos {_MIN_AMOSTRAS_TRECHO} "
            "amostras (2 s a 50 Hz) neste arquivo",
        )

    inicio, fim = trecho
    t_s = tabela.column("t_s").to_numpy(zero_copy_only=False)
    n_amostras = fim - inicio
    calibrados: set[str] = set()
    for coluna in colunas_presentes:
        bruto = tabela.column(coluna).to_numpy(zero_copy_only=False)[inicio:fim]
        bruto = (
            bruto[~np.isnan(bruto)]
            if np.issubdtype(bruto.dtype, np.floating)
            else bruto
        )
        if bruto.size < _MIN_AMOSTRAS_TRECHO:
            continue
        offset_contagem = float(np.mean(bruto))
        canonico = CANAL_BRUTO_PARA_CANONICO[coluna]
        conn.execute(
            """insert into calibracao_canal_gravado
                 (gravacao_id, canal_canonico_id, offset_contagem, metodo,
                  n_amostras, t_inicio_s, t_fim_s)
               values (%s,%s,%s,%s,%s,%s,%s)
               on conflict (gravacao_id, canal_canonico_id) do update set
                 offset_contagem = excluded.offset_contagem,
                 metodo          = excluded.metodo,
                 n_amostras      = excluded.n_amostras,
                 t_inicio_s      = excluded.t_inicio_s,
                 t_fim_s         = excluded.t_fim_s,
                 calculado_em    = now()""",
            (
                gravacao_id,
                canonico,
                offset_contagem,
                _METODO,
                int(n_amostras),
                float(t_s[inicio]),
                float(t_s[fim - 1]),
            ),
        )
        calibrados.add(canonico)

    esperados = {CANAL_BRUTO_PARA_CANONICO[c] for c in colunas_presentes}
    faltantes = esperados - calibrados
    motivo = None
    if faltantes:
        motivo = (
            " e ".join(sorted(faltantes)) + " fora do inventario: trecho de "
            "carro parado achado, mas amostra insuficiente apos remover nulo"
        )
    return ResultadoCalibracao(frozenset(calibrados), motivo)
