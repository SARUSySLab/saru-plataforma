"""Leitor de inventario do container Pi/Cosworth `LISTHEAD` (`.dat`), formato
`pi_listhead_dat`.

PROCEDENCIA (porte de
`saru_lapanalyzer/infra/datasources/listhead_dat_file.py`, snapshot `aa94872`
do saru-app, 358 linhas):

MANTIDO: o walk linear de nos de 32 B por `node_size` (`_walk` do original), a
leitura de `CHANNEL_INFO` (nome em `+0x00`, id em `+0x18`, unidade em `+0x3E`)
e do sub-cabecalho de 16 B de `CHID_xxxx` (`interval`, `last_tick`,
`n_samples`), a constante `_TICK_S = 1e-4` (provada pelo cruzamento beacon x
`Running Lap Time` no proprio arquivo original) e a leitura de `FILE_INFO`
(venue, driver, vehicle).

DESCARTADO: tudo que materializa amostra ou junta canal num eixo comum. Isso
inclui `_read_samples` lendo o `float32` cru de cada `CHID` (aqui so o
sub-cabecalho de 16 B e lido, nunca o payload de amostra), o eixo mestre por
`np.interp`, o `RawTelemetryBundle`/pandas, o corte de volta por `EVNT_B0`
(`lap_number`, a etapa 5 do nosso pipeline) e a excecao de dominio
`NoLapsInFileError`. Este leitor faz inventario, nao amostra.

ALTERADO (MUDANCA OBRIGATORIA, ver instrucao de delegacao): o original faz
`path.read_bytes()` e carrega o arquivo inteiro em memoria antes de andar
pelos nos. Trocado por `mmap.mmap` em modo so-leitura: o walk indexa o arquivo
mapeado, o SO pagina sob demanda, e nada obriga materializar de uma vez um
arquivo de centenas de MB (o contrato do projeto, `base.py`, e explicito sobre
isso). Tambem alterado: o walk levanta `ErroDeLeitura` quando um no declara
`node_size` invalido, em vez do `logger.warning` + `break` silencioso do
original, porque cobertura parcial do walk teria que virar erro visivel, nao
inventario incompleto sem aviso. E os bytes de faixa em `CHANNEL_INFO+0x4A`
NAO viram `valor_min`/`valor_max` do `CanalBruto` (ver secao abaixo).

Fatos medidos contra `_P.Piquet000991.dat` (34.383 B, mesma sessao do
`pi_pid` acima, acervo F3, 2026-08-29): 154 nos, walk cobre 100% do arquivo
(`covered == tamanho_arquivo`); tipos LISTHEAD:53, CHANNEL_INFO:48, CHID:48,
EVNT_B0:2, FREESTATS:1, FREE:1, FILE_INFO:1; 48 canais, todos com `CHID`
correspondente (indice do sufixo hex do no == `id & 0xFFFF` do
`CHANNEL_INFO`, confirmado 48/48). `Steering`: unidade `mm`, `interval`=100
ticks -> 100,0 Hz, n=300. `WS_FL` e `Speed`: unidade `kph`, `interval`=200
ticks -> 50,0 Hz, n=150. `FILE_INFO`: venue=`Curitiba`, driver=`P.Piquet`,
vehicle=`F309-021`.

FAIXA DECLARADA: NAO. Os bytes em `CHANNEL_INFO+0x4A` (`declared_max,
declared_min` no codigo original) sao a faixa MEDIDA daquele arquivo
especifico, nao uma faixa declarada de fabrica como no `.pid`. Confirmado
neste mesmo arquivo: `Steering` (unidade `mm`) sai `(maximo=1.6618,
minimo=0.3910)`, quando o `.pid` da MESMA sessao declara `Steering` em
`-100..100 mm` de faixa de fabrica. Sao numeros de grandeza (e as vezes sinal)
incompativel, porque so descrevem o que ESTE arquivo mediu, nao o que o
sensor suporta. `valor_min`/`valor_max` ficam `None` aqui: preencher com o
medido seria apresentar evidencia fabricada como se fosse faixa declarada,
que e proibido neste repo (ver instrucao de delegacao).

NOME TRUNCADO: o campo de nome de `CHANNEL_INFO` tem 16 B e o container
trunca em 15 ou 16 caracteres (`'Throttle Positi'`, `'Min Corner Spee'`,
`'Running Lap Tim'`, medidos). Este leitor devolve o nome do jeito que o
arquivo grava, truncado, sem tentar completar contra o `.pid` ou qualquer
outra fonte: isso e informacao verdadeira sobre o que o container consegue
guardar, nao um bug do leitor.
"""

from __future__ import annotations

import mmap
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow as pa

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario, Lote

_MAGIC: bytes = b"LISTHEAD"
_NODE_HEADER_BYTES: int = 32
#: Um tick vale 100 us. Ver docstring do modulo.
_TICK_S: float = 1e-4
#: Offsets do payload de CHANNEL_INFO, relativos a `node.offset + 32`.
_OFF_NOME: int = 0x00
_LEN_NOME: int = 16
_OFF_ID: int = 0x18
_OFF_UNIDADE: int = 0x3E
_LEN_UNIDADE: int = 12
#: Offsets do payload de FILE_INFO, relativos a `node.offset + 32`.
_OFF_VENUE: int = 8
_LEN_VENUE: int = 12
_OFF_DRIVER: int = 20
_LEN_DRIVER: int = 12
_OFF_VEHICLE: int = 307
_LEN_VEHICLE: int = 16
#: Teto de seguranca: nenhum arquivo do acervo passa de 154 nos; 200_000 e
#: folga generosa contra um `node_size` que nunca fecha em erro (arquivo
#: absurdamente grande e malformado ao mesmo tempo).
MAX_NOS = 200_000
#: A amostra `float32` de um no `CHID_xxxx` comeca logo apos o cabecalho do
#: no (32 B) mais o sub-cabecalho de intervalo/n_amostras (16 B).
_CHID_DATA_OFFSET: int = _NODE_HEADER_BYTES + 16
#: Tamanho maximo de lote sugerido pelo contrato (50 mil a 200 mil linhas).
_LINHAS_POR_LOTE = 100_000


@dataclass(frozen=True)
class _No:
    """Um no do container, ja localizado no arquivo mapeado."""

    tipo: str
    offset: int
    tamanho: int


def _ascii(bruto: bytes) -> str:
    """Texto de um campo de tamanho fixo, cortado no primeiro NUL."""
    return bruto.split(b"\x00", 1)[0].decode("latin-1", errors="replace").strip()


def _andar(mm: mmap.mmap, tamanho_arquivo: int, caminho: Path) -> list[_No]:
    """Percorre o container no a no, do inicio ao fim.

    O passo e o proprio `node_size` de cada no: e isso que torna o formato
    auto-descrito. Um `node_size` que nao caiba no arquivo levanta erro em vez
    de andar por bytes arbitrarios, que produziria no de lixo com cara de
    dado.
    """
    nos: list[_No] = []
    pos = 0
    while pos + _NODE_HEADER_BYTES <= tamanho_arquivo:
        if len(nos) >= MAX_NOS:
            raise ErroDeLeitura(
                f"{caminho}: mais de {MAX_NOS} nos a partir do offset {pos}, "
                "walk nao termina"
            )
        tipo = _ascii(mm[pos : pos + 16])
        tamanho, _flags = struct.unpack_from("<II", mm, pos + 24)
        if tamanho < _NODE_HEADER_BYTES or pos + tamanho > tamanho_arquivo:
            raise ErroDeLeitura(
                f"{caminho}: no {tipo!r} em offset {pos} declara tamanho "
                f"{tamanho}, fora do arquivo ({tamanho_arquivo} B). O walk "
                "nao cobre o container inteiro, decodificar o resto seria "
                "adivinhacao."
            )
        nos.append(_No(tipo=tipo, offset=pos, tamanho=tamanho))
        pos += tamanho
    return nos


def _ler_channel_info(mm: mmap.mmap, no: _No) -> tuple[int, str, str]:
    """Le nome, unidade e indice de um no `CHANNEL_INFO`. Nao le faixa: ver
    docstring do modulo, secao FAIXA DECLARADA."""
    base = no.offset + _NODE_HEADER_BYTES
    nome = _ascii(mm[base + _OFF_NOME : base + _OFF_NOME + _LEN_NOME])
    (chan_id,) = struct.unpack_from("<I", mm, base + _OFF_ID)
    unidade = _ascii(mm[base + _OFF_UNIDADE : base + _OFF_UNIDADE + _LEN_UNIDADE])
    return chan_id & 0xFFFF, nome, unidade


def _ler_subcabecalho_chid(mm: mmap.mmap, no: _No) -> tuple[int, int]:
    """Le so os 16 B do sub-cabecalho de um no `CHID_xxxx`: intervalo em
    ticks e numero de amostras. Nunca le o payload de `float32` que vem
    depois: isso e amostra, fora do escopo de inventario."""
    base = no.offset + _NODE_HEADER_BYTES
    intervalo, _zero, _ultimo_tick, n_amostras = struct.unpack_from("<IIII", mm, base)
    return intervalo, n_amostras


def _ler_amostras_chid(mm: mmap.mmap, no: _No, caminho: Path) -> np.ndarray:
    """Le o payload `float32` LE de um no `CHID_xxxx`, ja como `float64`.

    Porte de `_read_samples` do original: le `n_amostras` valores `float32`
    a partir de `node.offset + 48`. Alterado: o original recorta pro numero
    de amostras que CABEM no no (`available = (node.size - 48) // 4`) e so
    registra um `logger.warning` quando o declarado excede o disponivel.
    Aqui isso vira `ErroDeLeitura`: se o no declara mais amostras do que o
    proprio tamanho comporta, o layout esta desalinhado e recortar em
    silencio esconderia amostra perdida atras de um numero que parece
    inteiro.
    """
    base = no.offset + _NODE_HEADER_BYTES
    _intervalo, _zero, _ultimo_tick, n_amostras = struct.unpack_from("<IIII", mm, base)
    disponivel = (no.tamanho - _CHID_DATA_OFFSET) // 4
    if n_amostras > disponivel:
        raise ErroDeLeitura(
            f"{caminho}: no {no.tipo!r} em offset {no.offset} declara "
            f"{n_amostras} amostras mas o payload comporta {disponivel} "
            f"(tamanho do no {no.tamanho} B)"
        )
    offset_dados = no.offset + _CHID_DATA_OFFSET
    dados = np.frombuffer(mm, dtype="<f4", count=n_amostras, offset=offset_dados)
    # copia pra float64: desconecta do mmap (que fecha ao sair do `with` do
    # chamador) e da a mesma largura numerica dos outros leitores do projeto.
    return dados.astype(np.float64, copy=True)


def _ler_file_info(mm: mmap.mmap, no: _No) -> dict[str, str]:
    """Venue, piloto e veiculo do no `FILE_INFO`. Offsets relativos ao
    payload (`node.offset + 32`), medidos no acervo."""
    base = no.offset + _NODE_HEADER_BYTES
    meta = {
        "venue": _ascii(mm[base + _OFF_VENUE : base + _OFF_VENUE + _LEN_VENUE]),
        "driver": _ascii(mm[base + _OFF_DRIVER : base + _OFF_DRIVER + _LEN_DRIVER]),
        "vehicle": _ascii(mm[base + _OFF_VEHICLE : base + _OFF_VEHICLE + _LEN_VEHICLE]),
    }
    return {k: v for k, v in meta.items() if v}


class LeitorPiListheadDat(LeitorDeInventario):
    """Inventario de canal do container Pi/Cosworth `LISTHEAD` (`.dat`).

    Le o arquivo via `mmap`, nunca `read()` inteiro: o corpo de amostra
    (`float32` dentro de cada `CHID_xxxx`) nunca e tocado, so o sub-cabecalho
    de 16 B de cada no de canal.
    """

    formato_id = "pi_listhead_dat"
    versao = "1"
    suporta_amostra = True

    def inspecionar(self, caminho: Path) -> Cabecalho:
        tamanho_arquivo = caminho.stat().st_size
        if tamanho_arquivo < _NODE_HEADER_BYTES:
            raise ErroDeLeitura(
                f"{caminho}: arquivo com {tamanho_arquivo} B, menor que um "
                f"no de {_NODE_HEADER_BYTES} B, em offset 0"
            )

        with (
            caminho.open("rb") as fh,
            mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm,
        ):
            if mm[:8] != _MAGIC:
                raise ErroDeLeitura(
                    f"{caminho}: magic {bytes(mm[:8])!r} != {_MAGIC!r} "
                    "esperado em offset 0, nao e pi_listhead_dat"
                )

            nos = _andar(mm, tamanho_arquivo, caminho)

            infos: dict[int, tuple[str, str]] = {}
            for no in nos:
                if no.tipo != "CHANNEL_INFO":
                    continue
                indice, nome, unidade = _ler_channel_info(mm, no)
                infos[indice] = (nome, unidade)

            if not infos:
                raise ErroDeLeitura(f"{caminho}: nenhum CHANNEL_INFO no container")

            # Um canal pode ocupar mais de um no CHID; soma n_amostras e
            # confere que todos os nos do indice concordam na taxa (o
            # mesmo canal nao pode mudar de intervalo no meio do arquivo,
            # isso indicaria offset errado, nao dado real).
            intervalos: dict[int, int] = {}
            amostras: dict[int, int] = {}
            for no in nos:
                if not no.tipo.startswith("CHID_"):
                    continue
                try:
                    indice = int(no.tipo.split("_", 1)[1], 16)
                except ValueError:
                    raise ErroDeLeitura(
                        f"{caminho}: no {no.tipo!r} em offset {no.offset} "
                        "com indice hexadecimal ilegivel"
                    ) from None
                intervalo, n = _ler_subcabecalho_chid(mm, no)
                if intervalo <= 0:
                    raise ErroDeLeitura(
                        f"{caminho}: no {no.tipo!r} em offset {no.offset} "
                        f"declara intervalo {intervalo} ticks, nao pode "
                        "ser <= 0"
                    )
                if indice in intervalos and intervalos[indice] != intervalo:
                    raise ErroDeLeitura(
                        f"{caminho}: canal de indice {indice} muda de "
                        f"intervalo entre nos ({intervalos[indice]} ticks "
                        f"vs {intervalo} ticks no offset {no.offset})"
                    )
                intervalos[indice] = intervalo
                amostras[indice] = amostras.get(indice, 0) + n

            info_file = next((n for n in nos if n.tipo == "FILE_INFO"), None)
            meta = _ler_file_info(mm, info_file) if info_file else {}

        faltantes = set(infos) - set(intervalos)
        if faltantes:
            raise ErroDeLeitura(
                f"{caminho}: canais sem no CHID correspondente: {sorted(faltantes)}"
            )

        canais = []
        for indice in sorted(infos):
            nome, unidade = infos[indice]
            if not nome:
                raise ErroDeLeitura(
                    f"{caminho}: CHANNEL_INFO de indice {indice} sem nome"
                )
            frequencia_hz = 1.0 / (intervalos[indice] * _TICK_S)
            canais.append(
                CanalBruto(
                    nome_bruto=nome,
                    frequencia_hz=frequencia_hz,
                    n_amostras=amostras[indice],
                    unidade_declarada=unidade or None,
                    # Ver docstring do modulo, secao FAIXA DECLARADA: os bytes
                    # disponiveis sao faixa MEDIDA deste arquivo, nao faixa
                    # declarada de fabrica. Preencher aqui seria evidencia
                    # fabricada.
                    valor_min=None,
                    valor_max=None,
                )
            )

        # Duracao pelo canal mais rapido (menor intervalo em ticks): mesma
        # convencao do .pid, "quanto tempo o arquivo cobre" e do canal com
        # mais amostras por segundo.
        indice_mais_rapido = min(intervalos, key=lambda i: intervalos[i])
        duracao_s: float | None = None
        if amostras[indice_mais_rapido] > 0:
            freq = 1.0 / (intervalos[indice_mais_rapido] * _TICK_S)
            duracao_s = amostras[indice_mais_rapido] / freq

        bruto: dict[str, str] = {
            "n_nos": str(len(nos)),
            "n_canais": str(len(canais)),
            **({"driver": meta["driver"]} if "driver" in meta else {}),
            **({"vehicle": meta["vehicle"]} if "vehicle" in meta else {}),
        }

        return Cabecalho(
            formato_id=self.formato_id,
            leitor_versao=self.versao,
            canais=tuple(canais),
            capturado_em=None,
            duracao_s=duracao_s,
            venue_declarado=meta.get("venue"),
            bruto=bruto,
        )

    def ler(self, caminho: Path) -> Iterator[Lote]:
        """Le a amostra `float32` de cada `CHID_xxxx`, agrupada por taxa.

        Um canal pode ter varios nos `CHID` (mesmo indice, mesmo
        `interval`): concatena na ordem em que aparecem no walk, que e a
        ordem de gravacao no arquivo. `t_s` de uma amostra e
        `indice_na_serie_concatenada / frequencia_hz`. O nome da coluna e o
        `nome_bruto` exato que `inspecionar()` devolve (ja truncado pelo
        proprio container, ja com o sufixo `~1` que o arquivo grava pra
        canal duplicado: ver docstring do modulo, secao NOME TRUNCADO).

        `valor_min`/`valor_max` nao entram aqui: essa decisao e do
        `CanalBruto` de `inspecionar()`, este metodo so materializa
        amostra.

        Le o arquivo inteiro via `mmap` (nunca `read_bytes()`), igual ao
        `inspecionar()`: o SO pagina sob demanda, e o array `float32` de
        cada `CHID` so e copiado pra memoria do processo (como `float64`)
        no momento em que aquele no e visitado, nunca o arquivo inteiro de
        uma vez. A emissao de `Lote` sai em blocos de ate
        `_LINHAS_POR_LOTE` linhas por taxa.
        """
        tamanho_arquivo = caminho.stat().st_size
        if tamanho_arquivo < _NODE_HEADER_BYTES:
            raise ErroDeLeitura(
                f"{caminho}: arquivo com {tamanho_arquivo} B, menor que um "
                f"no de {_NODE_HEADER_BYTES} B, em offset 0"
            )

        with (
            caminho.open("rb") as fh,
            mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm,
        ):
            if mm[:8] != _MAGIC:
                raise ErroDeLeitura(
                    f"{caminho}: magic {bytes(mm[:8])!r} != {_MAGIC!r} "
                    "esperado em offset 0, nao e pi_listhead_dat"
                )

            nos = _andar(mm, tamanho_arquivo, caminho)

            infos: dict[int, tuple[str, str]] = {}
            for no in nos:
                if no.tipo != "CHANNEL_INFO":
                    continue
                indice, nome, _unidade = _ler_channel_info(mm, no)
                infos[indice] = (nome, _unidade)
            if not infos:
                raise ErroDeLeitura(f"{caminho}: nenhum CHANNEL_INFO no container")

            intervalos: dict[int, int] = {}
            pedacos: dict[int, list[np.ndarray]] = {}
            for no in nos:
                if not no.tipo.startswith("CHID_"):
                    continue
                try:
                    indice = int(no.tipo.split("_", 1)[1], 16)
                except ValueError:
                    raise ErroDeLeitura(
                        f"{caminho}: no {no.tipo!r} em offset {no.offset} "
                        "com indice hexadecimal ilegivel"
                    ) from None
                intervalo, _n = _ler_subcabecalho_chid(mm, no)
                if intervalo <= 0:
                    raise ErroDeLeitura(
                        f"{caminho}: no {no.tipo!r} em offset {no.offset} "
                        f"declara intervalo {intervalo} ticks, nao pode "
                        "ser <= 0"
                    )
                if indice in intervalos and intervalos[indice] != intervalo:
                    raise ErroDeLeitura(
                        f"{caminho}: canal de indice {indice} muda de "
                        f"intervalo entre nos ({intervalos[indice]} ticks "
                        f"vs {intervalo} ticks no offset {no.offset})"
                    )
                intervalos[indice] = intervalo
                dados = _ler_amostras_chid(mm, no, caminho)
                pedacos.setdefault(indice, []).append(dados)

            faltantes = set(infos) - set(intervalos)
            if faltantes:
                raise ErroDeLeitura(
                    f"{caminho}: canais sem no CHID correspondente: {sorted(faltantes)}"
                )

            colunas: dict[int, np.ndarray] = {
                indice: np.concatenate(partes) if len(partes) > 1 else partes[0]
                for indice, partes in pedacos.items()
            }

        # Agrupa por intervalo em ticks (chave exata, sem risco de ponto
        # flutuante) e confere que todo canal do grupo tem o MESMO numero de
        # amostras: e essa contagem comum que vira o `t_s` compartilhado do
        # `Lote`. Medido no acervo (2026-08-29, `_P.Piquet000991.dat`): em
        # cada uma das 7 taxas todos os canais do grupo tem a mesma
        # contagem (ex.: 100 Hz -> todos com 300); nao ha caso ragged no
        # acervo hoje, mas se aparecer, e ERRO DURO, nao corte silencioso.
        grupos: dict[int, list[tuple[str, np.ndarray]]] = {}
        for indice in sorted(infos):
            nome, _unidade = infos[indice]
            if not nome:
                raise ErroDeLeitura(
                    f"{caminho}: CHANNEL_INFO de indice {indice} sem nome"
                )
            grupos.setdefault(intervalos[indice], []).append((nome, colunas[indice]))

        for intervalo_ticks, canais in sorted(grupos.items()):
            frequencia_hz = 1.0 / (intervalo_ticks * _TICK_S)
            tamanhos = {vals.size for _, vals in canais}
            if len(tamanhos) > 1:
                raise ErroDeLeitura(
                    f"{caminho}: canais a {frequencia_hz:g} Hz com numero de "
                    f"amostras diferente entre si ({sorted(tamanhos)}); sem "
                    "um t_s comum nao da pra montar o Lote"
                )
            n = tamanhos.pop()
            if n == 0:
                continue
            nomes = [nome for nome, _ in canais]
            valores = [vals for _, vals in canais]

            inicio = 0
            while inicio < n:
                fim = min(inicio + _LINHAS_POR_LOTE, n)
                t_s = pa.array(np.arange(inicio, fim, dtype=np.float64) / frequencia_hz)
                arrays = [t_s, *(pa.array(v[inicio:fim]) for v in valores)]
                tabela = pa.RecordBatch.from_arrays(arrays, names=["t_s", *nomes])
                yield Lote(frequencia_hz=frequencia_hz, tabela=tabela)
                inicio = fim
