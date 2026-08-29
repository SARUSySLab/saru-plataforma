"""Contrato do leitor.

Decisao do Lucas (29/08), tres partes:

1. **Leitor e por container, nao por modelo.** Um `.dlf` de TDL 4.3 e um de
   TDL 7 EVO passam pelo mesmo leitor: mesmo container, conjuntos de canal
   diferentes. A variacao por modelo (nome de canal, unidade, fator, offset)
   mora em `mapeamento_canal`, versionada por `mapa_canal.versao`. Modelo novo
   do mesmo fabricante e linha nova em tabela, nao deploy.
2. **A amostra sai em streaming de `RecordBatch` do Arrow.** O acervo tem `.ld`
   de 400 MB e `.bmsbin` de 920 MB: materializar arquivo inteiro em memoria e
   um teto que a gente encosta cedo.
3. **Formato so entra no catalogo com assinatura medida** de arquivo real. Sem
   amostra, o formato existe como leitor ausente e o sistema declara que nao
   le. Ver `formatos.py`.

Regra que atravessa tudo: o leitor NAO interpreta semantica. Ele devolve o
nome bruto que o fabricante escreveu, a unidade que o arquivo declara (que
pode estar errada) e a taxa nativa de cada canal. Traduzir e trabalho da
etapa 3, contra o mapa. Leitor que adivinha canal e a mesma doenca do B2.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

import pyarrow as pa


@dataclass(frozen=True)
class CanalBruto:
    """Uma linha de `canal_gravado`, do jeito que o arquivo declara."""

    nome_bruto: str
    frequencia_hz: float
    n_amostras: int
    unidade_declarada: str | None = None
    valor_min: float | None = None
    valor_max: float | None = None


@dataclass(frozen=True)
class Cabecalho:
    """O que da pra saber sem ler a amostra inteira.

    Serve pra etapa 1 (recepcao) decidir e registrar antes de pagar o custo de
    varrer o arquivo, e pra `saru-poc sniff` responder rapido.
    """

    formato_id: str
    leitor_versao: str
    canais: tuple[CanalBruto, ...]
    capturado_em: str | None = None
    duracao_s: float | None = None
    # O venue que o arquivo DECLARA, se declarar. Nulo aqui nao autoriza
    # default nenhum: e exatamente o buraco do B2.
    venue_declarado: str | None = None
    # Cabecalho cru, pra `gravacao.metadata`. Isencao de 1FN ja declarada
    # no catalogo.
    bruto: dict[str, str] = field(default_factory=dict)

    @property
    def taxas(self) -> tuple[float, ...]:
        return tuple(sorted({c.frequencia_hz for c in self.canais}))


@dataclass(frozen=True)
class Lote:
    """Um pedaco de amostra, ja agrupado por taxa nativa.

    `tabela` tem uma coluna `t_s` (segundos desde o inicio da captura) mais uma
    coluna por canal daquela taxa, com o NOME BRUTO como nome de coluna. A
    traducao pro vocabulario canonico acontece depois, na etapa 3.

    `serie` separa fluxos que dividem a MESMA taxa mas tem relogio e colunas
    proprios (caso real: canais GPS sintetizados do .xrk a 25 Hz num arquivo
    que ja tem grupo CHS de 25 Hz - 23 dos 113 arquivos com GPS do acervo,
    medido em 29/08). O default vazio preserva o contrato antigo por inteiro,
    inclusive a falha alta de "canal que some no meio da serie": dentro de um
    mesmo `serie`, esquema continua nao podendo mudar.
    """

    frequencia_hz: float
    tabela: pa.RecordBatch
    serie: str = ""

    def __post_init__(self) -> None:
        if "t_s" not in self.tabela.schema.names:
            raise ValueError(
                f"lote de {self.frequencia_hz} Hz sem coluna t_s: "
                "sem eixo de tempo nao da pra cortar volta nem alinhar canal"
            )


class ErroDeLeitura(Exception):
    """Falha de parse. Vira `ingestao.status = 'falhou'` com a mensagem."""


@runtime_checkable
class Leitor(Protocol):
    """Um container, um leitor.

    `versao` entra em `ingestao.leitor_versao` e faz parte da chave natural da
    execucao: trocar o parser e reprocessar produz linha nova, nunca
    sobrescreve a anterior.
    """

    formato_id: str
    versao: str
    # Nesta fase os leitores fazem inventario, nao amostra. Quem declara False
    # levanta NotImplementedError em `ler`, e a ingestao registra a leitura como
    # parcial em vez de tentar escrever Parquet vazio.
    suporta_amostra: bool

    def inspecionar(self, caminho: Path) -> Cabecalho: ...

    def ler(self, caminho: Path) -> Iterator[Lote]: ...


class LeitorDeInventario:
    """Base dos leitores que so catalogam canal, sem materializar amostra.

    Existe pra o `ler` que levanta ficar escrito uma vez so. Quem passar a
    suportar amostra sobrescreve `ler` e troca `suporta_amostra` pra True.
    """

    formato_id: str = ""
    versao: str = "0"
    suporta_amostra: bool = False

    def inspecionar(self, caminho: Path) -> Cabecalho:  # pragma: no cover
        raise NotImplementedError

    def ler(self, caminho: Path) -> Iterator[Lote]:
        raise NotImplementedError(
            f"o leitor de {self.formato_id} faz inventario de canal, nao le "
            "amostra ainda. Use inspecionar()."
        )
