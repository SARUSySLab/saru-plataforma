"""Leitura de amostra pelas etapas do pipeline.

Tres coisas que as etapas 5, 6 e 7 fazem igual e nao deviam fazer duas vezes:
abrir o Parquet de uma serie, escolher qual serie usar quando o mesmo canal
aparece em varias taxas, e aplicar o fator do mapa pra sair do valor nativo do
fabricante e chegar na unidade canonica.

O ultimo item nao e detalhe: a camada bruta guarda o que o arquivo escreveu, e
o que o arquivo escreveu nao e grau nem metro por segundo. O VBOX grava
latitude em MINUTO e ainda inverte o sinal da longitude (fator -1/60 no mapa);
quase todo logger grava velocidade em km/h. Ler sem o mapa poe o carro em outro
continente ou multiplica a distancia por 3,6.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from ..storage import caminho_de_uri


@dataclass(frozen=True)
class CanalEscolhido:
    """Um canal canonico resolvido num arquivo concreto."""

    canonico: str
    nome_bruto: str
    uri: str
    frequencia_hz: float
    fator: float
    offset: float

    def valores(self, dados: dict[str, np.ndarray]) -> np.ndarray:
        """Aplica o mapa: valor nativo vira unidade canonica."""
        return dados[self.nome_bruto] * self.fator + self.offset


def ler_colunas(uri: str, colunas: list[str]) -> dict[str, np.ndarray]:
    """Le so as colunas pedidas de um Parquet de serie, mais o eixo de tempo."""
    caminho: Path = caminho_de_uri(uri)
    arquivo = pq.ParquetFile(caminho)
    presentes = set(arquivo.schema_arrow.names)
    pedidas = [c for c in ["t_s", *colunas] if c in presentes]
    tabela = arquivo.read(columns=pedidas)
    return {nome: tabela.column(nome).to_numpy() for nome in pedidas}


def fator_do_canal(
    conn, gravacao_id: str, canonico: str, nome_bruto: str
) -> tuple[float, float] | None:
    """Fator e offset do mapa, pelo perfil da ultima ingestao que deu certo.

    Nulo quando o perfil daquela ingestao nao mapeia aquele canal. Devolver
    (1, 0) como padrao seria supor que o nativo ja esta na unidade canonica, o
    que e falso na maioria dos loggers do acervo.
    """
    linha = conn.execute(
        """select m.fator_escala, m."offset"
             from mapeamento_canal m
            where m.perfil_id = (
                    select i.perfil_id from ingestao i
                     where i.gravacao_id = %s and i.status <> 'falhou'
                       and i.perfil_id is not null
                     order by i.iniciada_em desc limit 1)
              and m.canal_canonico_id = %s
              and m.coluna_bruta = %s
            order by m.mapa_versao desc limit 1""",
        (gravacao_id, canonico, nome_bruto),
    ).fetchone()
    return (float(linha[0]), float(linha[1])) if linha else None


def escolher_canal(
    conn, gravacao_id: str, canonicos: tuple[str, ...]
) -> CanalEscolhido | None:
    """O melhor canal disponivel entre os canonicos pedidos, por TAXA.

    Ordem dos `canonicos` e preferencia semantica (pedir ('distance',
    'distance_m') significa "distancia, de qualquer um dos dois nomes"); dentro
    do que existe, quem manda e a taxa de amostragem, porque ela e o teto da
    precisao de tudo que se calcula depois. Foi a licao da etapa 5, onde o
    canal "certo" morava numa serie de 1 Hz.
    """
    linhas = conn.execute(
        """select cg.canal_canonico_id, cg.nome_bruto, s.uri, s.frequencia_hz
             from canal_gravado cg
             join serie_amostral s on s.id = cg.serie_id
            where cg.gravacao_id = %s and cg.canal_canonico_id = any(%s)
            order by s.frequencia_hz desc""",
        (gravacao_id, list(canonicos)),
    ).fetchall()
    for canonico, nome_bruto, uri, hz in linhas:
        mapa = fator_do_canal(conn, gravacao_id, canonico, nome_bruto)
        if mapa is None:
            continue
        return CanalEscolhido(
            canonico=canonico,
            nome_bruto=nome_bruto,
            uri=uri,
            frequencia_hz=float(hz),
            fator=mapa[0],
            offset=mapa[1],
        )
    return None


def par_gps(conn, gravacao_id: str) -> tuple[CanalEscolhido, CanalEscolhido] | None:
    """Latitude e longitude, exigindo que as duas venham da MESMA serie.

    Taxas diferentes exigiriam reamostrar pra cruzar as duas, e reamostrar
    dentro de uma etapa esconde decisao de interpolacao onde ninguem vai
    procurar depois.
    """
    lat = escolher_canal(conn, gravacao_id, ("gps_lat",))
    lon = escolher_canal(conn, gravacao_id, ("gps_lon",))
    if lat is None or lon is None or lat.uri != lon.uri:
        return None
    return lat, lon


def janela(
    t_s: np.ndarray, t_inicio: float, t_fim: float
) -> tuple[np.ndarray, np.ndarray]:
    """Indices e mascara da fatia de uma volta dentro da serie da captura."""
    mascara = (t_s >= t_inicio) & (t_s <= t_fim)
    return np.flatnonzero(mascara), mascara
