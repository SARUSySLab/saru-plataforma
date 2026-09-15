"""Engenharia reversa: calibra parametros do veiculo contra telemetria real.

Serve a PIL-RF-30 e E-RF-09. Arquitetura em ADR-008
(`docs/arquitetura/adr/ADR-008-engenharia-reversa-e-simulacao-de-volta.md`).

Consome `fisica/parametros_gt3_cup.py` (PR #6, mesclado em 2026-09-15). Este modulo e
um esqueleto: as funcoes existem para fixar a interface e ainda nao foram implementadas.

Entrada: series amostrais canonicas de uma volta ja ingerida (G_Lat, G_Long, Speed,
Damper_Pos_FL/FR/RL/RR, Steering). Saida: os mesmos dataclasses de parametro do modulo
de fisica, com `provenance = Provenance.ENGINEERING_ESTIMATE` e a fonte apontando para a
gravacao e a volta usadas na calibracao.

Nao roda ainda. Ver issue #49 para o roteiro.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SerieCalibracao:
    """Uma serie canonica de entrada da calibracao, ja na grade comum de tempo."""

    canal: str
    unidade: str
    tempo_s: list[float]
    valor: list[float]


@dataclass
class ResultadoCalibracao:
    """Parametros ajustados e o residuo que a otimizacao deixou.

    `residuo_por_canal` guarda o erro medio quadratico entre o canal medido e o canal
    que o modelo produziria com os parametros ajustados, um valor por canal de entrada.
    Fica no relatorio da calibracao para Vitor decidir se o ajuste presta.
    """

    parametros: dict[str, float]
    residuo_por_canal: dict[str, float]
    fonte_gravacao_id: str
    fonte_volta_numero: int


def calibrar(series: list[SerieCalibracao], gravacao_id: str, volta_numero: int) -> ResultadoCalibracao:
    """Ajusta os parametros do GT3 Cup contra as series de uma volta real.

    TODO(#49): implementar. Rascunho do roteiro:
    1. Carregar `PorscheCupVehicle` de catalogo como ponto de partida (nunca do zero).
    2. Definir a funcao objetivo: soma dos residuos (seção 13, Tabela 5, G_Sum e
       Curvature) entre o canal medido e o canal simulado pelo QSS com os parametros
       correntes.
    3. `scipy.optimize.least_squares` sobre o subconjunto de parametros que a issue
       aprovar calibrar primeiro (comecar pelo pneu: rigidez de escorregamento lateral).
    4. Nunca sobrescrever `Provenance.OFFICIAL_MANUAL`; o resultado e um veiculo novo,
       marcado `ENGINEERING_ESTIMATE`, nao uma edicao do catalogo.
    """
    raise NotImplementedError("issue #49: calibracao reversa ainda nao implementada")
