"""Escrita e leitura da amostra. Parquet em disco, DuckDB pra consultar.

Amostra nunca entra no Postgres: o banco guarda o ponteiro (`serie_amostral`)
e o Parquet guarda os numeros. Trocar disco por S3/MinIO depois muda o prefixo
da URI e mais nada.

O objeto e imutavel, e o caminho e enderecado pelo conteudo: o nome do arquivo
carrega os primeiros 12 hex do sha256. Reprocessar nunca sobrescreve. Se o
reprocessamento produzir bytes identicos, o caminho e o mesmo e a operacao e
idempotente de graca; se produzir bytes diferentes, nasce outro objeto e quem
decide qual vale e a constraint do banco, nao o filesystem.
"""

from __future__ import annotations

import shutil

import hashlib
import os
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .config import CONFIG
from .readers.base import Lote

CAMADA_BRUTA = "bruta"
CAMADA_CANONICA = "canonica"
_CHUNK = 1 << 20


@dataclass(frozen=True)
class PonteiroSerie:
    """O que vira uma linha de `serie_amostral`."""

    uri: str
    camada: str
    frequencia_hz: float
    mapa_versao: str | None
    linhas: int
    bytes_: int
    sha256: str
    t_inicio_s: float
    t_fim_s: float
    formato_armazenamento: str = "parquet"
    # Rotulo do `Lote.serie` de origem ("" = serie principal da taxa) e as
    # colunas de canal do Parquet (sem `t_s`). As colunas existem pra ligar
    # `canal_gravado.serie_id` por NOME: com duas series na MESMA taxa (caso
    # GPS do .xrk), ligar so por taxa penduraria canal na serie errada.
    serie: str = ""
    colunas: tuple[str, ...] = ()


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as fh:
        for bloco in iter(lambda: fh.read(_CHUNK), b""):
            h.update(bloco)
    return h.hexdigest()


def _diretorio(
    raiz: Path,
    gravacao_id: str,
    camada: str,
    hz: float,
    mapa: str | None,
    serie: str = "",
) -> Path:
    # Particionado por gravacao e taxa nativa, como o plano fecha. A taxa entra
    # no caminho com 3 casas pra 12.5 Hz e 0.5 Hz nao colidirem em "12" e "0".
    # `serie` nao-vazia (fluxo paralelo na mesma taxa, ex. GPS do .xrk) vira
    # particao propria pra nao misturar objetos de fluxos diferentes no mesmo
    # diretorio.
    partes = [
        raiz,
        f"gravacao={gravacao_id}",
        f"camada={camada}",
        f"taxa={hz:.3f}",
    ]
    if serie:
        partes.append(f"serie={serie}")
    if mapa is not None:
        partes.append(f"mapa={mapa}")
    return Path(*partes)


def escrever_serie(
    gravacao_id: str,
    lotes: Iterable[Lote],
    *,
    camada: str = CAMADA_BRUTA,
    mapa_versao: str | None = None,
    raiz: Path | None = None,
) -> list[PonteiroSerie]:
    """Consome o streaming do leitor e escreve um Parquet por taxa nativa.

    Os lotes podem chegar intercalados entre taxas: um escritor e mantido
    aberto por taxa vista, e nada e acumulado em memoria alem do lote corrente.
    """
    raiz = raiz if raiz is not None else CONFIG.parquet_root
    if camada == CAMADA_CANONICA and mapa_versao is None:
        raise ValueError(
            "serie canonica exige mapa_versao: sem a versao do mapa o numero "
            "nao e reproduzivel depois"
        )
    if camada == CAMADA_BRUTA and mapa_versao is not None:
        raise ValueError("serie bruta nao tem mapa: os nomes ainda sao do fabricante")

    # Chave de escritor: (taxa, rotulo de serie). O rotulo separa fluxos
    # paralelos que dividem a mesma taxa (GPS do .xrk); DENTRO de uma chave o
    # esquema continua imutavel e a falha continua alta.
    Chave = tuple[float, str]
    escritores: dict[Chave, pq.ParquetWriter] = {}
    temporarios: dict[Chave, Path] = {}
    linhas: dict[Chave, int] = {}
    t_min: dict[Chave, float] = {}
    t_max: dict[Chave, float] = {}
    esquemas: dict[Chave, pa.Schema] = {}

    try:
        for lote in lotes:
            chave = (lote.frequencia_hz, lote.serie)
            tabela = lote.tabela
            if chave not in escritores:
                fd, bruto = tempfile.mkstemp(suffix=".parquet")
                os.close(fd)
                temporarios[chave] = Path(bruto)
                esquemas[chave] = tabela.schema
                escritores[chave] = pq.ParquetWriter(
                    temporarios[chave], tabela.schema, compression="zstd"
                )
            elif tabela.schema != esquemas[chave]:
                raise ValueError(
                    f"lote de {chave[0]} Hz mudou de esquema no meio da serie. "
                    "Canal que aparece e some no mesmo arquivo precisa de "
                    "decisao explicita, nao de coluna nula silenciosa."
                )
            escritores[chave].write_batch(tabela)
            linhas[chave] = linhas.get(chave, 0) + tabela.num_rows
            if tabela.num_rows:
                col = tabela.column("t_s")
                a, b = col[0].as_py(), col[-1].as_py()
                t_min[chave] = min(t_min.get(chave, a), a)
                t_max[chave] = max(t_max.get(chave, b), b)
    finally:
        for w in escritores.values():
            w.close()

    ponteiros: list[PonteiroSerie] = []
    for chave, temporario in temporarios.items():
        hz, serie = chave
        if not linhas.get(chave):
            temporario.unlink(missing_ok=True)
            continue
        sha = _sha256(temporario)
        destino_dir = _diretorio(raiz, gravacao_id, camada, hz, mapa_versao, serie)
        destino_dir.mkdir(parents=True, exist_ok=True)
        destino = destino_dir / f"{sha[:12]}.parquet"
        if destino.exists():
            # Mesmo conteudo, mesmo caminho: reprocessamento idempotente.
            temporario.unlink(missing_ok=True)
        else:
            # `shutil.move` e nao `Path.replace`: o rename do POSIX so funciona
            # DENTRO do mesmo dispositivo, e em producao o temporario nasce no
            # overlay do container enquanto o destino mora num volume montado.
            # Dispositivos diferentes, e o rename falha com EXDEV (errno 18,
            # "Invalid cross-device link"). Local nunca aparece porque la e tudo
            # o mesmo disco. `shutil.move` cai pra copiar e apagar quando
            # precisa; e mais lento, e so acontece quando o rename nao serve.
            shutil.move(str(temporario), str(destino))
        ponteiros.append(
            PonteiroSerie(
                uri=destino.as_uri(),
                camada=camada,
                frequencia_hz=hz,
                mapa_versao=mapa_versao,
                linhas=linhas[chave],
                bytes_=destino.stat().st_size,
                sha256=sha,
                t_inicio_s=t_min[chave],
                t_fim_s=t_max[chave],
                serie=serie,
                colunas=tuple(
                    n for n in esquemas[chave].names if n != "t_s"
                ),
            )
        )
    return ponteiros


def caminho_de_uri(uri: str) -> Path:
    """URI de volta pra caminho local, desescapando o percent-encoding.

    `Path.as_uri()` escapa espaco, `#` e acento. Cortar o prefixo `file://` na
    mao devolve um caminho que nao existe, e foi exatamente o que quebrou a
    ingestao dos `.vbo` do acervo, cujos nomes tem espaco e `#`.
    """
    if not uri.startswith("file://"):
        raise ValueError(
            f"URI nao local ({uri.split(':', 1)[0]}): a PoC so le disco hoje"
        )
    from urllib.parse import unquote, urlparse

    return Path(unquote(urlparse(uri).path))


def caminho_de(ponteiro: PonteiroSerie) -> Path:
    """URI da serie de volta pra caminho local."""
    return caminho_de_uri(ponteiro.uri)
