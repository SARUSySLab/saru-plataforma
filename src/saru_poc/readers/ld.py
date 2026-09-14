"""Leitor de inventario do container MoTeC i2 (`.ld`), formato `motec_ld`.

Le so o cabecalho e a lista encadeada de canais, sem tocar amostra: o maior
`.ld` do acervo passa de 400 MB e materializar o arquivo inteiro so pra listar
canal e um teto que a gente encosta cedo. Todo acesso e via `seek`/`read` nos
offsets medidos em 2026-08-29 contra os 42 `.ld` do acervo (ver o prompt de
delegacao que originou este arquivo). Sem `ldparser` e sem dependencia nova:
so `struct` da stdlib.

Formula de escala do canal, aplicada em `ler()` (nao em `inspecionar()`, que
so inventaria cabecalho e nao toca amostra):

    valor = (raw / scale * 10**-dec_places + shift) * mul

Ela transforma o inteiro (ou float32) cru do arquivo no valor que o MoTeC
considera o dado. Entra na camada bruta porque e a escala que o proprio
fabricante gravou no arquivo, nao uma traducao de vocabulario (isso e etapa
3, contra o `mapeamento_canal`).

ARMADILHA (nao resolvida aqui, so reportada): nos 22 arquivos ACC do lote
`telemetria/acc-autoanalise/`, os canais `G_LAT` e `G_LON` NAO sao coordenada
GPS: sao aceleracao lateral e longitudinal, com unidade `m/s2` (valores de
-12,3 a +34,0) e essa unidade vem certa no byte +72 do registro de canal.
O nome mente, a unidade desmente. E a `unidade_declarada` que sobrevive pra
etapa 3 detectar a divergencia depois; este leitor nao reescreve nome nem
unidade de canal nenhum.

OUTRA: os 3 arquivos GT7 em `samples-saru/gt7_*.ld` tem canais `GPS Latitude`
e `GPS Longitude` reais a 60 Hz, mas georreferenciados em Donington Park
(Inglaterra) mesmo o `venue_declarado` do cabecalho dizendo
"Autodromo de Interlagos". O leitor devolve o venue do arquivo do jeito que
esta escrito, sem corrigir: corrigir e decisao de outra etapa, com o mapa de
venue na mao.
"""

from __future__ import annotations

import struct
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pyarrow as pa

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario, Lote

MAGIC_ESPERADO = 64

# Offsets do cabecalho fixo do arquivo (medidos, ver docstring do modulo).
OFF_MAGIC = 0x00
OFF_PTR_CANAIS = 0x08
OFF_PTR_DADOS = 0x0C
OFF_PTR_EVENTO = 0x24
OFF_DEVICE = 0x4A
LEN_DEVICE = 8
OFF_DATA = 0x5E
LEN_DATA = 16
OFF_HORA = 0x7E
LEN_HORA = 16
OFF_PILOTO = 0x9E
LEN_PILOTO = 64
OFF_VEICULO = 0xDE
LEN_VEICULO = 64
OFF_VENUE = 0x15E
LEN_VENUE = 64
OFF_COMENTARIO = 0x624
LEN_COMENTARIO = 64
OFF_EVENTO = 0x6E2
LEN_EVENTO = 64

# Tamanho minimo de arquivo pra caber o cabecalho fixo inteiro (ate o campo
# mais distante que este leitor le, com folga).
TAMANHO_MINIMO_CABECALHO = OFF_EVENTO + LEN_EVENTO

# Registro de canal: 124 bytes, lista duplamente encadeada.
TAMANHO_REGISTRO_CANAL = 124
OFF_CANAL_PREV = 0
OFF_CANAL_NEXT = 4
OFF_CANAL_PTR_DADOS = 8
OFF_CANAL_N_AMOSTRAS = 12
OFF_CANAL_FREQ_HZ = 22
OFF_CANAL_NOME_LONGO = 32
LEN_CANAL_NOME_LONGO = 32
OFF_CANAL_NOME_CURTO = 64
LEN_CANAL_NOME_CURTO = 8
OFF_CANAL_UNIDADE = 72
LEN_CANAL_UNIDADE = 12
OFF_CANAL_DTYPE_A = 18
OFF_CANAL_DTYPE = 20
OFF_CANAL_SHIFT = 24
OFF_CANAL_MUL = 26
OFF_CANAL_SCALE = 28
OFF_CANAL_DEC_PLACES = 30

# Teto de seguranca contra lista encadeada que nunca fecha (arquivo
# corrompido apontando em ciclo). Nenhum arquivo do acervo passa de 221
# canais; 10_000 e folga generosa sem virar loop infinito de verdade.
MAX_CANAIS = 10_000

# Combinacao (dtype_a, dtype) -> tipo numpy do dado cru, medida contra os 42
# arquivos do acervo em 2026-08-29: (7,4) float32, (5,4) int32, (3,2) e
# (0,2) int16 (os dois ultimos com o mesmo tamanho, dtype_a so distingue uma
# variante interna do MoTeC que nao muda a decodificacao). Combinacao fora
# deste mapa levanta ErroDeLeitura em `ler()` em vez de adivinhar o tamanho
# do campo: `inspecionar()` nao usa este mapa, entao arquivo com combinacao
# nova continua sendo inventariado normalmente, so a leitura de amostra fica
# bloqueada nele.
_NUMPY_DTYPE_POR_COMBO: dict[tuple[int, int], str] = {
    (7, 4): "<f4",
    (5, 4): "<i4",
    (3, 2): "<i2",
    (0, 2): "<i2",
}

# Linhas por lote emitido em `ler()`. Na taxa mais alta do acervo (500 Hz,
# lote Porsche Cup) isso e ~200s de amostra por lote, bem dentro do teto de
# streaming sugerido no contrato (50 mil a 200 mil linhas).
LINHAS_POR_LOTE = 100_000


@dataclass(frozen=True)
class _RegistroCanal:
    """Um registro de canal decodificado por inteiro, pra uso de `ler()`.

    `inspecionar()` usa so o subconjunto que vira `CanalBruto`; `ler()` usa
    tambem `ptr_dados`, `dtype_a`/`dtype` (pra escolher o tipo numpy) e os
    quatro campos de escala (formula documentada no topo do modulo).
    """

    nome_bruto: str
    frequencia_hz: float
    n_amostras: int
    unidade_declarada: str | None
    ptr_dados: int
    dtype_a: int
    dtype: int
    shift: int
    mul: int
    scale: int
    dec_places: int


def _decodificar_string(bruto: bytes) -> str:
    """Corta no primeiro nulo e tira espaco nas pontas.

    ASCII com padding de nulo, mas usa latin1 pra nunca levantar
    UnicodeDecodeError num byte alto isolado (o acervo tem arquivo com lixo
    de encoding em campo de comentario).
    """
    fim = bruto.find(b"\x00")
    if fim != -1:
        bruto = bruto[:fim]
    return bruto.decode("latin1").strip()


def _normalizar_capturado_em(data_str: str, hora_str: str) -> tuple[str | None, str]:
    """Combina data (`D/M/AAAA`, dia e mes sem zero a esquerda garantido) e
    hora (`HH:MM:SS`) em ISO 8601. Quando nao da pra parsear, devolve None
    e preserva a string crua pra `bruto`: nunca inventa data.

    Naive de proposito (sem `tzinfo`): o cabecalho do MoTeC nao declara fuso
    horario nenhum, e e o mesmo horario local que o dash gravou. Inventar um
    fuso aqui seria pior que nao ter: e outro caso do B2, so que com hora em
    vez de venue.
    """
    bruto_combinado = f"{data_str} {hora_str}"
    if not data_str or not hora_str:
        return None, bruto_combinado
    try:
        dia_s, mes_s, ano_s = data_str.split("/")
        dt = datetime(  # noqa: DTZ001 (naive de proposito, ver docstring)
            year=int(ano_s),
            month=int(mes_s),
            day=int(dia_s),
            hour=int(hora_str.split(":")[0]),
            minute=int(hora_str.split(":")[1]),
            second=int(hora_str.split(":")[2]),
        )
    except (ValueError, IndexError):
        return None, bruto_combinado
    return dt.isoformat(), bruto_combinado


class LeitorLd(LeitorDeInventario):
    """Inventario de canal do container MoTeC `.ld`."""

    formato_id = "motec_ld"
    versao = "1"
    suporta_amostra = True

    def inspecionar(self, caminho: Path) -> Cabecalho:
        tamanho_arquivo = caminho.stat().st_size
        if tamanho_arquivo < TAMANHO_MINIMO_CABECALHO:
            raise ErroDeLeitura(
                f"{caminho}: arquivo menor que o cabecalho fixo "
                f"({tamanho_arquivo} bytes, esperava >= "
                f"{TAMANHO_MINIMO_CABECALHO}) em offset 0"
            )

        with caminho.open("rb") as fh:
            fh.seek(OFF_MAGIC)
            bruto_magic = fh.read(4)
            if len(bruto_magic) < 4:
                raise ErroDeLeitura(f"{caminho}: EOF lendo magic em offset {OFF_MAGIC}")
            (magic,) = struct.unpack("<I", bruto_magic)
            if magic != MAGIC_ESPERADO:
                raise ErroDeLeitura(
                    f"{caminho}: magic {magic} != {MAGIC_ESPERADO} esperado "
                    f"em offset {OFF_MAGIC}, nao e motec_ld"
                )

            ptr_canais = self._ler_u32(fh, caminho, OFF_PTR_CANAIS)
            ptr_dados = self._ler_u32(fh, caminho, OFF_PTR_DADOS)
            # Ponteiro do bloco de evento existe no cabecalho mas nao e usado
            # por este leitor (inventario nao le evento/volta, so canal).
            _ptr_evento = self._ler_u32(fh, caminho, OFF_PTR_EVENTO)

            device = self._ler_string_offset(fh, caminho, OFF_DEVICE, LEN_DEVICE)
            data_str = self._ler_string_offset(fh, caminho, OFF_DATA, LEN_DATA)
            hora_str = self._ler_string_offset(fh, caminho, OFF_HORA, LEN_HORA)
            piloto = self._ler_string_offset(fh, caminho, OFF_PILOTO, LEN_PILOTO)
            veiculo = self._ler_string_offset(fh, caminho, OFF_VEICULO, LEN_VEICULO)
            venue = self._ler_string_offset(fh, caminho, OFF_VENUE, LEN_VENUE)
            comentario = self._ler_string_offset(
                fh, caminho, OFF_COMENTARIO, LEN_COMENTARIO
            )
            nome_evento = self._ler_string_offset(fh, caminho, OFF_EVENTO, LEN_EVENTO)

            registros = self._ler_registros_canais(
                fh, caminho, ptr_canais, ptr_dados, tamanho_arquivo
            )

        if not registros:
            raise ErroDeLeitura(
                f"{caminho}: lista de canais vazia (ponteiro {ptr_canais})"
            )

        canais = [
            CanalBruto(
                nome_bruto=r.nome_bruto,
                frequencia_hz=r.frequencia_hz,
                n_amostras=r.n_amostras,
                unidade_declarada=r.unidade_declarada,
            )
            for r in registros
        ]

        capturado_em, capturado_em_bruto = _normalizar_capturado_em(data_str, hora_str)

        canal_mais_longo = max(canais, key=lambda c: c.n_amostras)
        duracao_s: float | None = None
        if canal_mais_longo.frequencia_hz > 0:
            duracao_s = canal_mais_longo.n_amostras / canal_mais_longo.frequencia_hz

        bruto: dict[str, str] = {
            "device": device,
            "piloto": piloto,
            "veiculo": veiculo,
            "comentario": comentario,
            "nome_evento": nome_evento,
            "n_canais": str(len(canais)),
            "capturado_em_bruto": capturado_em_bruto,
            "duracao_s_derivado_de": canal_mais_longo.nome_bruto or "(sem nome)",
        }

        return Cabecalho(
            formato_id=self.formato_id,
            leitor_versao=self.versao,
            canais=tuple(canais),
            capturado_em=capturado_em,
            duracao_s=duracao_s,
            venue_declarado=venue or None,
            bruto=bruto,
        )

    @staticmethod
    def _ler_u32(fh, caminho: Path, offset: int) -> int:
        fh.seek(offset)
        bruto = fh.read(4)
        if len(bruto) < 4:
            raise ErroDeLeitura(f"{caminho}: EOF lendo u32 em offset {offset}")
        return struct.unpack("<I", bruto)[0]

    @staticmethod
    def _ler_string_offset(fh, caminho: Path, offset: int, tamanho: int) -> str:
        fh.seek(offset)
        bruto = fh.read(tamanho)
        if len(bruto) < tamanho:
            raise ErroDeLeitura(
                f"{caminho}: EOF lendo string de {tamanho} bytes em offset {offset}"
            )
        return _decodificar_string(bruto)

    def _ler_registros_canais(
        self,
        fh,
        caminho: Path,
        ptr_canais: int,
        ptr_dados: int,
        tamanho_arquivo: int,
    ) -> list[_RegistroCanal]:
        """Percorre a lista duplamente encadeada de registros de canal.

        Terminador medido nos 42 arquivos do acervo: a lista fecha com
        `next == 0` em 41 deles. Em `LMP3_SIM01_Baseline.ld` (lote ChassisSim)
        o `next` do ultimo canal real aponta pra `ptr_dados` em vez de 0, ou
        seja o "fim" da lista de canais e o comeco do bloco de amostra, e o
        que vem depois de `ptr_dados` nao e mais registro de canal (e lixo
        de amostra reinterpretado como struct, produz canal com nome vazio
        e frequencia 0). Por isso o la o de parada e `next in (0, ptr_dados)`,
        nao so `next == 0`: tratar so o zero deixaria vazar 3 canais falsos
        nesse arquivo especifico. Nao e fixture forcada, e comportamento
        medido: ver a nota do prompt de delegacao (sublote ChassisSim, 2
        arquivos, comportamento distinto dos outros 3 sublotes).
        """
        canais: list[_RegistroCanal] = []
        no_atual = ptr_canais
        visitados: set[int] = set()

        while no_atual != 0 and no_atual != ptr_dados:
            if no_atual in visitados:
                raise ErroDeLeitura(
                    f"{caminho}: lista de canais em ciclo, no {no_atual} "
                    "ja visitado (nao fecha)"
                )
            visitados.add(no_atual)

            if no_atual + TAMANHO_REGISTRO_CANAL > tamanho_arquivo:
                raise ErroDeLeitura(
                    f"{caminho}: registro de canal em offset {no_atual} "
                    f"ultrapassa o fim do arquivo ({tamanho_arquivo} bytes)"
                )
            if len(canais) >= MAX_CANAIS:
                raise ErroDeLeitura(
                    f"{caminho}: mais de {MAX_CANAIS} canais na lista a "
                    f"partir do offset {no_atual}, lista nao fecha"
                )

            fh.seek(no_atual)
            registro = fh.read(TAMANHO_REGISTRO_CANAL)
            if len(registro) < TAMANHO_REGISTRO_CANAL:
                raise ErroDeLeitura(
                    f"{caminho}: EOF lendo registro de canal em offset "
                    f"{no_atual} ({len(registro)}/{TAMANHO_REGISTRO_CANAL} "
                    "bytes)"
                )

            proximo_no = struct.unpack_from("<I", registro, OFF_CANAL_NEXT)[0]
            ptr_dados_canal = struct.unpack_from("<I", registro, OFF_CANAL_PTR_DADOS)[0]
            n_amostras = struct.unpack_from("<I", registro, OFF_CANAL_N_AMOSTRAS)[0]
            frequencia_hz = struct.unpack_from("<H", registro, OFF_CANAL_FREQ_HZ)[0]
            dtype_a, dtype = struct.unpack_from("<HH", registro, OFF_CANAL_DTYPE_A)
            shift, mul, scale, dec_places = struct.unpack_from(
                "<hhhh", registro, OFF_CANAL_SHIFT
            )
            nome_longo = _decodificar_string(
                registro[
                    OFF_CANAL_NOME_LONGO : OFF_CANAL_NOME_LONGO + LEN_CANAL_NOME_LONGO
                ]
            )
            nome_curto = _decodificar_string(
                registro[
                    OFF_CANAL_NOME_CURTO : OFF_CANAL_NOME_CURTO + LEN_CANAL_NOME_CURTO
                ]
            )
            unidade = _decodificar_string(
                registro[OFF_CANAL_UNIDADE : OFF_CANAL_UNIDADE + LEN_CANAL_UNIDADE]
            )

            nome_bruto = nome_longo or nome_curto
            if not nome_bruto:
                raise ErroDeLeitura(
                    f"{caminho}: registro de canal em offset {no_atual} sem "
                    "nome longo nem curto"
                )

            canais.append(
                _RegistroCanal(
                    nome_bruto=nome_bruto,
                    frequencia_hz=float(frequencia_hz),
                    n_amostras=n_amostras,
                    unidade_declarada=unidade or None,
                    ptr_dados=ptr_dados_canal,
                    dtype_a=dtype_a,
                    dtype=dtype,
                    shift=shift,
                    mul=mul,
                    scale=scale,
                    dec_places=dec_places,
                )
            )

            no_atual = proximo_no

        return canais

    def ler(self, caminho: Path) -> Iterator[Lote]:
        """Materializa a amostra dos canais, um `Lote` por taxa nativa.

        Formula de escala aplicada aqui, canal a canal, com os quatro campos
        que o proprio arquivo declara (`shift`, `mul`, `scale`,
        `dec_places`):

            valor = (raw / scale * 10**-dec_places + shift) * mul

        Ela transforma o inteiro (ou float32 ja fisico) cru no valor que o
        MoTeC considera o dado. Nao ha traducao de unidade nem de nome: o
        valor sai na unidade que o proprio arquivo declara (`unidade
        declarada`), e o nome de coluna e exatamente o `nome_bruto` que
        `inspecionar()` devolve pro mesmo canal.

        Canais sao agrupados por `frequencia_hz`: cada grupo vira uma serie
        de `Lote`s streamados em blocos de `LINHAS_POR_LOTE` linhas, lidos
        por `seek`/`read` direto no `ptr_dados` de cada canal (nunca
        carregando o arquivo inteiro). `t_s` de cada linha e
        `indice / frequencia_hz`, contrato do modulo `base`.

        Medido nos 42 arquivos do acervo: canais da mesma taxa, no mesmo
        arquivo, sempre tem a mesma contagem de amostra (nenhuma excecao).
        Por seguranca este metodo confere isso e levanta `ErroDeLeitura` se
        algum dia divergir, em vez de cortar ou preencher a diferenca.
        """
        tamanho_arquivo = caminho.stat().st_size
        if tamanho_arquivo < TAMANHO_MINIMO_CABECALHO:
            raise ErroDeLeitura(
                f"{caminho}: arquivo menor que o cabecalho fixo "
                f"({tamanho_arquivo} bytes, esperava >= "
                f"{TAMANHO_MINIMO_CABECALHO}) em offset 0"
            )

        with caminho.open("rb") as fh:
            fh.seek(OFF_MAGIC)
            bruto_magic = fh.read(4)
            if len(bruto_magic) < 4:
                raise ErroDeLeitura(f"{caminho}: EOF lendo magic em offset {OFF_MAGIC}")
            (magic,) = struct.unpack("<I", bruto_magic)
            if magic != MAGIC_ESPERADO:
                raise ErroDeLeitura(
                    f"{caminho}: magic {magic} != {MAGIC_ESPERADO} esperado "
                    f"em offset {OFF_MAGIC}, nao e motec_ld"
                )

            ptr_canais = self._ler_u32(fh, caminho, OFF_PTR_CANAIS)
            ptr_dados = self._ler_u32(fh, caminho, OFF_PTR_DADOS)

            registros = self._ler_registros_canais(
                fh, caminho, ptr_canais, ptr_dados, tamanho_arquivo
            )
            if not registros:
                raise ErroDeLeitura(
                    f"{caminho}: lista de canais vazia (ponteiro {ptr_canais})"
                )

            grupos: dict[float, list[_RegistroCanal]] = {}
            for r in registros:
                grupos.setdefault(r.frequencia_hz, []).append(r)

            for frequencia_hz in sorted(grupos):
                yield from self._ler_grupo_por_taxa(
                    fh, caminho, frequencia_hz, grupos[frequencia_hz]
                )

    def _ler_grupo_por_taxa(
        self,
        fh,
        caminho: Path,
        frequencia_hz: float,
        registros: list[_RegistroCanal],
    ) -> Iterator[Lote]:
        n_total = registros[0].n_amostras
        for r in registros:
            if r.n_amostras != n_total:
                raise ErroDeLeitura(
                    f"{caminho}: canais da taxa {frequencia_hz} Hz com "
                    f"contagem de amostra divergente ({r.nome_bruto}: "
                    f"{r.n_amostras}, {registros[0].nome_bruto}: {n_total})"
                )

        np_dtypes: list[np.dtype] = []
        for r in registros:
            combo = (r.dtype_a, r.dtype)
            dtype_str = _NUMPY_DTYPE_POR_COMBO.get(combo)
            if dtype_str is None:
                raise ErroDeLeitura(
                    f"{caminho}: canal {r.nome_bruto!r} com combinacao de "
                    f"tipo (dtype_a={r.dtype_a}, dtype={r.dtype}) nao "
                    "suportada (mapa cobre so o medido no acervo)"
                )
            if r.scale == 0:
                raise ErroDeLeitura(
                    f"{caminho}: canal {r.nome_bruto!r} com scale=0, "
                    "divisao por zero na formula de escala"
                )
            np_dtypes.append(np.dtype(dtype_str))

        inicio = 0
        while inicio < n_total:
            fim = min(inicio + LINHAS_POR_LOTE, n_total)
            n_linhas = fim - inicio

            colunas: dict[str, np.ndarray] = {
                "t_s": np.arange(inicio, fim, dtype=np.float64) / frequencia_hz
            }
            for r, np_dtype in zip(registros, np_dtypes, strict=True):
                tamanho_item = np_dtype.itemsize
                offset = r.ptr_dados + inicio * tamanho_item
                fh.seek(offset)
                bruto = fh.read(n_linhas * tamanho_item)
                if len(bruto) < n_linhas * tamanho_item:
                    raise ErroDeLeitura(
                        f"{caminho}: EOF lendo amostra do canal "
                        f"{r.nome_bruto!r} em offset {offset} "
                        f"({len(bruto)}/{n_linhas * tamanho_item} bytes)"
                    )
                bruto_np = np.frombuffer(bruto, dtype=np_dtype).astype(np.float64)
                valores = (bruto_np / r.scale * (10.0**-r.dec_places) + r.shift) * r.mul
                colunas[r.nome_bruto] = valores

            tabela = pa.RecordBatch.from_pydict(colunas)
            yield Lote(frequencia_hz=frequencia_hz, tabela=tabela)
            inicio = fim
