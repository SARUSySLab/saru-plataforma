"""Corte de volta com o dado chegando, para o pit wall ao vivo.

O corte de `corte_voltas.py` roda com o arquivo inteiro em maos: le a serie
toda, acha as passagens, devolve as voltas. No box isso nao serve, porque a
volta precisa fechar no instante em que o carro cruza a linha, e nao no fim da
sessao.

DESENHO: uma maquina de estado que come amostra por amostra e emite a volta no
momento em que ela fecha. Estado minimo de proposito, porque vai existir uma
instancia por carro e o painel roda com n carros ao mesmo tempo.

O QUE NAO MUDA em relacao ao offline, e nao muda porque mudar seria trocar o
resultado: a mesma regra de debounce (`MIN_VOLTA_S`), o mesmo raio de gate do
GPS (`RAIO_GATE_M`) e a mesma conversao de graus para metros. Estas funcoes sao
importadas de `corte_voltas`, nunca copiadas: duas copias da mesma regra
divergem no primeiro ajuste, e ai o ao vivo passa a discordar do relatorio que
o piloto le depois.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .corte_voltas import MIN_VOLTA_S, RAIO_GATE_M, Volta, _para_metros


@dataclass
class EstadoCorte:
    """O que o corte sabe agora. Serve de diagnostico direto na tela.

    `motivo` existe porque gravacao sem fonte de corte NAO e "gravacao sem
    voltas": e gravacao que nao da pra cortar, e a diferenca precisa aparecer
    para o engenheiro em vez de virar um zero silencioso.
    """

    fonte: str | None = None
    motivo: str | None = None
    voltas: list[Volta] = field(default_factory=list)
    passagens: list[float] = field(default_factory=list)
    t_ultimo_s: float | None = None

    @property
    def volta_atual(self) -> int:
        # A volta em curso e a proxima depois da ultima fechada. Antes da
        # primeira passagem o carro esta no out lap, que nao e volta 1.
        return len(self.voltas) + 1

    @property
    def t_inicio_volta_atual(self) -> float | None:
        return self.passagens[-1] if self.passagens else None


class CorteIncremental:
    """Alimenta com `processar(amostra)` e escuta as voltas saindo.

    Duas fontes, na mesma ordem de preferencia do corte offline:
      1. contador de volta (`lap_number`), que e o beacon do proprio logger e
         responde por 530 das 559 voltas do acervo local;
      2. GPS cruzando o gate da linha de chegada, que responde pelas outras 29.

    A fonte e decidida pelo dado que chega, nao por configuracao: o primeiro
    canal que servir ganha, e a escolha fica declarada em `estado.fonte`.
    """

    def __init__(
        self,
        *,
        linha_lat: float | None = None,
        linha_lon: float | None = None,
        min_volta_s: float = MIN_VOLTA_S,
        raio_gate_m: float = RAIO_GATE_M,
    ) -> None:
        self._linha = (linha_lat, linha_lon) if linha_lat is not None and linha_lon is not None else None
        self._min_volta_s = min_volta_s
        self._raio_gate_m = raio_gate_m
        self.estado = EstadoCorte()
        self._lap_anterior: float | None = None
        self._dentro_do_gate = False
        # Melhor aproximacao da passagem DENTRO do gate corrente: instante e
        # distancia. Ver `_por_gps` para o porque de nao usar a entrada.
        self._melhor_t: float | None = None
        self._melhor_d2: float = float("inf")

    def processar(self, t_s: float, canais: dict[str, Any]) -> Volta | None:
        """Come uma amostra. Devolve a volta se ela fechou agora, senao None."""
        self.estado.t_ultimo_s = t_s

        lap = canais.get("lap_number")
        if lap is not None:
            return self._por_contador(t_s, float(lap))

        lat, lon = canais.get("gps_lat"), canais.get("gps_lon")
        if lat is not None and lon is not None and self._linha is not None:
            return self._por_gps(t_s, float(lat), float(lon))

        if self.estado.fonte is None:
            self.estado.motivo = (
                "sem contador de volta e sem GPS com linha de referência: "
                "não há como saber onde a volta fecha"
            )
        return None

    def _por_contador(self, t_s: float, lap: float) -> Volta | None:
        anterior, self._lap_anterior = self._lap_anterior, lap
        if anterior is None:
            self.estado.fonte = "lap_number"
            self.estado.motivo = None
            return None
        # So o degrau PARA CIMA conta. Contador que volta atras e ruido de
        # decodificacao, nao carro andando de re na linha.
        if lap > anterior:
            return self._registrar_passagem(t_s)
        return None

    def _por_gps(self, t_s: float, lat: float, lon: float) -> Volta | None:
        """Passagem no ponto de MENOR distancia da referencia, nao na entrada.

        Marcar a entrada no gate custou 1,6 s de erro sistematico contra o
        corte offline, medido na gravacao de Interlagos do acervo: o raio tem
        30 m e o carro entra nele antes de cruzar a linha, entao a 20 m/s a
        volta comeca cedo demais. O offline resolve com a perpendicular ao rumo
        medio, o que exige a serie inteira e nao existe ao vivo.

        Aqui a passagem e o ponto mais proximo da referencia dentro do gate,
        que e a mesma coisa com resolucao de uma amostra. O preco e emitir a
        volta na SAIDA do gate, cerca de um segundo depois: no box isso e
        invisivel, e vale muito mais que um erro fixo no tempo de volta.
        """
        assert self._linha is not None
        dx, dy = _para_metros(lat, lon, self._linha[0], self._linha[1])
        d2 = float(dx * dx + dy * dy)
        dentro = d2 <= (self._raio_gate_m * self._raio_gate_m)

        if dentro:
            self.estado.fonte = "gps"
            self.estado.motivo = None
            if d2 < self._melhor_d2:
                self._melhor_d2, self._melhor_t = d2, t_s
            self._dentro_do_gate = True
            return None

        if self._dentro_do_gate:
            # acabou de sair: agora sabemos qual amostra foi a mais proxima
            self._dentro_do_gate = False
            t_passagem, self._melhor_t = self._melhor_t, None
            self._melhor_d2 = float("inf")
            if t_passagem is not None:
                return self._registrar_passagem(t_passagem)
        return None

    def _registrar_passagem(self, t_s: float) -> Volta | None:
        anteriores = self.estado.passagens
        # Mesmo debounce do offline, so que aplicado de chegada: sem ele, GPS
        # tremendo com o carro parado na box vira dez voltas de meio segundo.
        if anteriores and (t_s - anteriores[-1]) < self._min_volta_s:
            return None
        anteriores.append(t_s)
        if len(anteriores) < 2:
            return None
        volta = Volta(
            numero=len(self.estado.voltas) + 1,
            t_inicio_s=anteriores[-2],
            t_fim_s=anteriores[-1],
        )
        self.estado.voltas.append(volta)
        return volta
