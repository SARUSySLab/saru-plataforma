"""Simulador quasi-steady-state (QSS) de uma volta.

Serve a PIL-RF-30. Arquitetura em ADR-008
(`docs/arquitetura/adr/ADR-008-engenharia-reversa-e-simulacao-de-volta.md`).

Segmenta o traçado por curvatura (mesma decomposição de `pipeline/decomposicao.py`) e,
por segmento, resolve a velocidade máxima que a elipse de atrito de Kamm permite
(seção 4 do guia `engenharia-de-pista.md`), depois integra o tempo. Mais rápido que o
transiente 14-DOF em Julia; serve para varredura de parâmetro logo após a calibração
reversa (`fisica/calibracao_reversa.py`), não para o resultado final de precisão.

Nao roda ainda. Ver issue #49 para o roteiro.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SegmentoTracado:
    """Um segmento do traçado com curvatura constante, unidade SI."""

    distancia_inicio_m: float
    distancia_fim_m: float
    curvatura_1_por_m: float


@dataclass
class ResultadoQSS:
    """Saída da simulação: tempo de volta e o perfil de velocidade por segmento."""

    tempo_volta_s: float
    velocidade_por_segmento_ms: list[float]


def simular(segmentos: list[SegmentoTracado], parametros: dict[str, float]) -> ResultadoQSS:
    """Resolve a velocidade limite por segmento pela elipse de Kamm e integra o tempo.

    TODO(#49): implementar depois do PR #6 e de `fisica/calibracao_reversa.py` ter ao
    menos um `ResultadoCalibracao` real para testar contra. Rascunho do roteiro:
    1. Para cada segmento, resolver v_max tal que G_Lat(v_max, curvatura) fique na borda
       da elipse (Equação da seção 4, `a_y,lim` vindo de `parametros["a_y_lim"]`).
    2. Suavizar a transição entre segmentos (aceleração/frenagem limitada pela mesma
       elipse) antes de integrar o tempo segmento a segmento.
    3. Validar contra uma volta real já ingerida: o tempo de volta simulado tem que
       ficar dentro de uma banda de erro que Vitor aprovar, medida contra o `Lap Time`
       do próprio arquivo, não contra suposição.
    """
    raise NotImplementedError("issue #49: implementar apos o PR #6 e a calibracao reversa")
