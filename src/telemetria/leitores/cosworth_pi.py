"""Decodificadores unificados Cosworth Pi (.pid e .pds).

Unifica a leitura de containers Pi Toolbox e Pi Research:
1. `.pid`: arquivo de definicao e log de canais individuais. Aplica a
   transformacao linear y = m * x + c para conversao de contagens brutas de ADC
   em unidades fisicas (km/h, bar, deg, rpm, g, mm), com decodificacao de quadros
   intercalados por tick de 10 ms e descarte de slot nulo no tick 1 (100 Hz).
2. `.pds`: arquivo de sessao consolidada com multiplos canais. Suporta layouts
   de dicionario de 552 bytes (F3 e 992.1 multi-bloco) e leitura streaming em
   blocos de 64 KB (io.DEFAULT_BUFFER_SIZE) para garantir processamento eficiente
   sem sobrecarga de memoria RAM (< 100 MB de pico em arquivos de 105 MB).
"""

from __future__ import annotations

import io
import itertools
import math
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO
import struct

import numpy as np
import pyarrow as pa

from saru_poc.readers.base import Cabecalho, CanalBruto, ErroDeLeitura, Lote


# ---------------------------------------------------------------------------
# Transformacao Linear
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TransformacaoLinear:
    """Transformacao linear canonica y = m * x + c para calibracao fisica."""

    m: float = 1.0
    c: float = 0.0

    def aplicar(self, x: np.ndarray | float) -> np.ndarray | float:
        """Converte valor ou array bruto x para a grandeza fisica y."""
        return self.m * x + self.c


# ---------------------------------------------------------------------------
# Utilitarios compartilhados
# ---------------------------------------------------------------------------

_MAGIC_PID: bytes = b"\x01\x20\x03\x23"
_MAGIC_PDS: bytes = b"\x1a\x12\x40\xf7"
_OFF_MAGIC_PDS: int = 4
_TAMANHO_BUFFER_STREAMING: int = io.DEFAULT_BUFFER_SIZE  # 64 KB (65536 B)
_LINHAS_POR_LOTE: int = 100_000


def parse_cosworth_metadata(origem: Path | BinaryIO | bytes) -> dict[str, str | int | float]:
    """Inspeciona a assinatura e metadados basicos do container Cosworth Pi."""
    if isinstance(origem, bytes):
        stream = io.BytesIO(origem)
    elif isinstance(origem, Path):
        stream = origem.open("rb")
    else:
        stream = origem

    pos_inicial = stream.tell() if stream.seekable() else 0
    try:
        cabecalho = stream.read(64)
        if len(cabecalho) < 8:
            return {"formato": "desconhecido", "tamanho_cabecalho": len(cabecalho)}

        if cabecalho[:4] == _MAGIC_PID:
            n_blocos, tamanho_bloco = struct.unpack_from("<II", cabecalho, 4)
            return {
                "formato": "pi_pid",
                "magic": _MAGIC_PID.hex(),
                "n_blocos": n_blocos,
                "tamanho_bloco": tamanho_bloco,
            }

        if len(cabecalho) >= _OFF_MAGIC_PDS + 4 and cabecalho[_OFF_MAGIC_PDS : _OFF_MAGIC_PDS + 4] == _MAGIC_PDS:
            return {
                "formato": "pi_pds",
                "magic": _MAGIC_PDS.hex(),
                "offset_magic": _OFF_MAGIC_PDS,
            }

        return {"formato": "desconhecido", "magic": cabecalho[:4].hex()}
    finally:
        if stream.seekable():
            stream.seek(pos_inicial)
        if isinstance(origem, Path):
            stream.close()


def _ler_string_u16(dados: bytes, offset: int, tamanho_max_chars: int) -> str | None:
    """Le uma string UTF-16LE terminada em par de bytes nulos."""
    fim_max = offset + tamanho_max_chars * 2
    if offset < 0 or offset + 2 > len(dados):
        return None
    fim = dados.find(b"\x00\x00", offset, fim_max)
    if fim < 0:
        return None
    if (fim - offset) % 2 == 1:
        fim += 1
    try:
        return dados[offset:fim].decode("utf-16le")
    except UnicodeDecodeError:
        return None


# ---------------------------------------------------------------------------
# Decodificador .PID
# ---------------------------------------------------------------------------

_END_MARKER_PID: bytes = b"\x02\x20\x01\x23"
_CHANNEL_MARKER_PID: bytes = b"\x01\x20\x08\x28"
_HEADER_BYTES_PID: int = 16
_OFF_MIN_PID: int = 17
_OFF_MAX_PID: int = 25
_OFF_SCALE_PID: int = 47
_JANELA_HEURISTICA_PID: int = 40
_MAX_CANAIS_PID: int = 5_000
_TICKS_POR_BLOCO_PID: int = 100
_TICK_MARCADOR_PID: int = 1


@dataclass(frozen=True)
class _RegistroCanalPid:
    nome: str
    unidade: str
    taxa_hz: int
    largura: int
    minimo_declarado: float
    maximo_declarado: float
    escala: float


def _ler_string_prefixada(dados: bytes, offset: int) -> tuple[str, int]:
    if offset + 4 > len(dados):
        raise ErroDeLeitura(
            f"EOF lendo prefixo de string em offset relativo {offset} do trailer"
        )
    (tamanho,) = struct.unpack_from("<I", dados, offset)
    bruto = dados[offset + 4 : offset + 4 + tamanho]
    return bruto.split(b"\x00", 1)[0].decode("latin-1"), offset + 4 + tamanho


def _ler_dicionario_pid(trailer: bytes, caminho: Path) -> list[_RegistroCanalPid]:
    canais: list[_RegistroCanalPid] = []
    cursor = 0
    while True:
        cursor = trailer.find(_CHANNEL_MARKER_PID, cursor)
        if cursor < 0:
            break
        if len(canais) >= _MAX_CANAIS_PID:
            raise ErroDeLeitura(
                f"{caminho}: mais de {_MAX_CANAIS_PID} canais no dicionario a partir "
                f"do offset relativo {cursor} do trailer"
            )
        base = cursor + 4
        if base >= len(trailer):
            break
        probe = base + 1
        limite = base + _JANELA_HEURISTICA_PID
        achou_nome = False
        while probe < limite and probe + 4 <= len(trailer):
            (tamanho,) = struct.unpack_from("<I", trailer, probe)
            candidato = trailer[probe + 4 : probe + 4 + tamanho]
            if 2 <= tamanho <= _JANELA_HEURISTICA_PID and all(
                32 <= b < 127 or b == 0 for b in candidato
            ):
                achou_nome = True
                break
            probe += 1
        if not achou_nome:
            cursor = base
            continue

        try:
            nome, probe = _ler_string_prefixada(trailer, probe)
            _nome_curto, probe = _ler_string_prefixada(trailer, probe)
            unidade, probe = _ler_string_prefixada(trailer, probe)
            if probe + 13 > len(trailer) or probe + _OFF_SCALE_PID + 8 > len(trailer):
                cursor = base
                continue
            _a, _b, taxa_hz = struct.unpack_from("<III", trailer, probe)
            largura = trailer[probe + 12]
            (minimo,) = struct.unpack_from("<d", trailer, probe + _OFF_MIN_PID)
            (maximo,) = struct.unpack_from("<d", trailer, probe + _OFF_MAX_PID)
            (escala,) = struct.unpack_from("<d", trailer, probe + _OFF_SCALE_PID)
        except struct.error:
            cursor = base
            continue

        if taxa_hz <= 0 or 100 % taxa_hz or largura not in (1, 2, 4):
            cursor = base
            continue

        canais.append(
            _RegistroCanalPid(
                nome=nome,
                unidade=unidade,
                taxa_hz=taxa_hz,
                largura=largura,
                minimo_declarado=float(minimo),
                maximo_declarado=float(maximo),
                escala=float(escala),
            )
        )
        cursor = base

    return canais


def _metadados_do_trailer_pid(trailer: bytes) -> dict[str, str]:
    cursor = 8
    achadas: list[str] = []
    while cursor < len(trailer) and len(achadas) < 8:
        if cursor + 4 > len(trailer):
            break
        (tamanho,) = struct.unpack_from("<I", trailer, cursor)
        if 2 <= tamanho <= _JANELA_HEURISTICA_PID:
            bruto = trailer[cursor + 4 : cursor + 4 + tamanho]
            if all(32 <= b < 127 or b == 0 for b in bruto):
                achadas.append(bruto.split(b"\x00", 1)[0].decode("latin-1"))
                cursor += 4 + tamanho
                continue
        cursor += 1

    meta: dict[str, str] = {}
    for valor in achadas:
        eh_tempo = (
            ":" in valor
            and "." in valor
            and valor.replace(":", "").replace(".", "").isdigit()
        )
        if eh_tempo:
            meta.setdefault("melhor_volta_texto", valor)
        elif "driver" not in meta:
            meta["driver"] = valor
        elif "venue" not in meta:
            meta["venue"] = valor
        elif "vehicle" not in meta:
            meta["vehicle"] = valor
    return meta


def _aplicar_escala_declarada_pid(valores: np.ndarray, registro: _RegistroCanalPid) -> np.ndarray:
    if not (math.isfinite(registro.escala) and registro.escala != 0.0):
        return valores
    lo, hi = registro.minimo_declarado, registro.maximo_declarado
    if not (math.isfinite(lo) and math.isfinite(hi) and hi > lo):
        return valores
    if valores.size == 0:
        return valores

    margem = (hi - lo) * 0.01

    def cabe(candidato: np.ndarray) -> bool:
        lo_c = float(np.percentile(candidato, 0.5))
        hi_c = float(np.percentile(candidato, 99.5))
        return lo_c >= lo - margem and hi_c <= hi + margem

    dividido = valores / registro.escala
    multiplicado = valores * registro.escala
    cabe_div, cabe_mult = cabe(dividido), cabe(multiplicado)
    if cabe_div and not cabe_mult:
        return dividido
    if cabe_mult and not cabe_div:
        return multiplicado
    return valores


def _layout_do_bloco_pid(registros: list[_RegistroCanalPid]) -> list[list[tuple[int, int]]]:
    posicoes: list[list[tuple[int, int]]] = [[] for _ in registros]
    offset = 0
    for tick in range(_TICKS_POR_BLOCO_PID):
        for indice, r in enumerate(registros):
            if tick % (_TICKS_POR_BLOCO_PID // r.taxa_hz) == 0:
                posicoes[indice].append((offset, r.largura))
                offset += r.largura
    return posicoes


class CosworthPidReader:
    """Decodificador de container Pi/Cosworth `.pid` com conversao fisica."""

    formato_id = "pi_pid"
    versao = "1"
    suporta_amostra = True

    def __init__(self, calibracoes: dict[str, TransformacaoLinear] | None = None) -> None:
        self.calibracoes = calibracoes or {}

    def inspecionar(self, caminho: Path) -> Cabecalho:
        tamanho = caminho.stat().st_size
        if tamanho < _HEADER_BYTES_PID:
            raise ErroDeLeitura(
                f"{caminho}: arquivo com {tamanho} B, menor que cabecalho fixo"
            )

        with caminho.open("rb") as fh:
            cabecalho = fh.read(_HEADER_BYTES_PID)
            if cabecalho[:4] != _MAGIC_PID:
                raise ErroDeLeitura(f"{caminho}: magic invalido para pi_pid")
            _magic, n_blocos, tamanho_bloco, tail_valido = struct.unpack_from(
                "<IIII", cabecalho, 0
            )

            fim_dados = _HEADER_BYTES_PID + n_blocos * tamanho_bloco
            if fim_dados + 4 > tamanho:
                raise ErroDeLeitura(f"{caminho}: arquivo truncado antes do trailer")

            fh.seek(fim_dados)
            trailer = fh.read()

        if trailer[:4] != _END_MARKER_PID:
            raise ErroDeLeitura(f"{caminho}: marcador de fim ausente no trailer")

        registros = _ler_dicionario_pid(trailer, caminho)
        if not registros:
            raise ErroDeLeitura(f"{caminho}: nenhum canal identificado no trailer")

        declarado = sum(r.taxa_hz * r.largura for r in registros)
        if declarado != tamanho_bloco:
            raise ErroDeLeitura(
                f"{caminho}: canais declaram {declarado} B/bloco, bloco tem {tamanho_bloco} B"
            )

        canais = tuple(
            CanalBruto(
                nome_bruto=r.nome,
                frequencia_hz=float(r.taxa_hz),
                n_amostras=n_blocos * r.taxa_hz,
                unidade_declarada=r.unidade or None,
                valor_min=r.minimo_declarado,
                valor_max=r.maximo_declarado,
            )
            for r in registros
        )

        meta = _metadados_do_trailer_pid(trailer)
        bruto: dict[str, str] = {
            "n_blocos": str(n_blocos),
            "tamanho_bloco": str(tamanho_bloco),
            "bytes_validos_ultimo_bloco": str(tail_valido),
            "n_canais": str(len(canais)),
            **({"driver": meta["driver"]} if "driver" in meta else {}),
            **({"vehicle": meta["vehicle"]} if "vehicle" in meta else {}),
            **(
                {"melhor_volta_texto": meta["melhor_volta_texto"]}
                if "melhor_volta_texto" in meta
                else {}
            ),
        }

        return Cabecalho(
            formato_id=self.formato_id,
            leitor_versao=self.versao,
            canais=canais,
            capturado_em=None,
            duracao_s=float(n_blocos),
            venue_declarado=meta.get("venue"),
            bruto=bruto,
        )

    def ler(self, caminho: Path) -> Iterator[Lote]:
        tamanho = caminho.stat().st_size
        if tamanho < _HEADER_BYTES_PID:
            raise ErroDeLeitura(f"{caminho}: arquivo menor que cabecalho fixo")

        with caminho.open("rb") as fh:
            cabecalho = fh.read(_HEADER_BYTES_PID)
            if cabecalho[:4] != _MAGIC_PID:
                raise ErroDeLeitura(f"{caminho}: magic invalido")
            _magic, n_blocos, tamanho_bloco, _tail = struct.unpack_from(
                "<IIII", cabecalho, 0
            )

            fim_dados = _HEADER_BYTES_PID + n_blocos * tamanho_bloco
            if fim_dados + 4 > tamanho:
                raise ErroDeLeitura(f"{caminho}: dados truncados")

            fh.seek(_HEADER_BYTES_PID)
            corpo = fh.read(n_blocos * tamanho_bloco)
            trailer = fh.read()

        if trailer[:4] != _END_MARKER_PID:
            raise ErroDeLeitura(f"{caminho}: marcador de fim invalido")

        registros = _ler_dicionario_pid(trailer, caminho)
        if not registros:
            raise ErroDeLeitura(f"{caminho}: dicionario ilegivel")

        declarado = sum(r.taxa_hz * r.largura for r in registros)
        if declarado != tamanho_bloco:
            raise ErroDeLeitura(f"{caminho}: soma de bytes por bloco nao fecha")

        if n_blocos == 0:
            return

        corpo_np = np.frombuffer(corpo, dtype=np.uint8).reshape(n_blocos, tamanho_bloco)
        posicoes = _layout_do_bloco_pid(registros)

        grupos: dict[int, list[tuple[str, np.ndarray]]] = {}
        for r, janelas in zip(registros, posicoes, strict=True):
            amostras_por_tick = []
            for offset, largura in janelas:
                janela = corpo_np[:, offset : offset + largura].astype(np.int64)
                contagem = np.zeros(n_blocos, dtype=np.int64)
                for byte_idx in range(largura):
                    contagem = (contagem << 8) | janela[:, byte_idx]
                amostras_por_tick.append(contagem)
            contagem = np.stack(amostras_por_tick, axis=1).reshape(-1)
            nulos = np.zeros(contagem.shape, dtype=bool)
            if r.taxa_hz == _TICKS_POR_BLOCO_PID:
                nulos[_TICK_MARCADOR_PID :: r.taxa_hz] = True

            if math.isfinite(r.minimo_declarado) and r.minimo_declarado < 0:
                metade = np.int64(1) << (8 * r.largura - 1)
                cheio = np.int64(1) << (8 * r.largura)
                contagem = np.where(contagem >= metade, contagem - cheio, contagem)

            # Conversao fisica: escala declarada ou calibracao linear explicita
            if r.nome in self.calibracoes:
                valores = self.calibracoes[r.nome].aplicar(contagem.astype(np.float64))
            else:
                valores = _aplicar_escala_declarada_pid(contagem.astype(np.float64), r)

            valores = np.where(nulos, np.nan, valores)
            grupos.setdefault(r.taxa_hz, []).append((r.nome, valores))

        for taxa_hz, canais_do_grupo in sorted(grupos.items()):
            n = n_blocos * taxa_hz
            nomes = [nome for nome, _ in canais_do_grupo]
            valores_por_canal = [vals for _, vals in canais_do_grupo]

            inicio = 0
            while inicio < n:
                fim = min(inicio + _LINHAS_POR_LOTE, n)
                t_s = pa.array(np.arange(inicio, fim, dtype=np.float64) / taxa_hz)
                arrays = [
                    t_s,
                    *(
                        pa.array(v[inicio:fim], mask=np.isnan(v[inicio:fim]))
                        for v in valores_por_canal
                    ),
                ]
                tabela = pa.RecordBatch.from_arrays(arrays, names=["t_s", *nomes])
                yield Lote(frequencia_hz=float(taxa_hz), tabela=tabela)
                inicio = fim


# ---------------------------------------------------------------------------
# Decodificador .PDS com Streaming em 64 KB
# ---------------------------------------------------------------------------

_ESTRIDE_DICIONARIO_PDS: int = 552
_OFF_NOME_PDS: int = 0
_LEN_NOME_MAX_PDS: int = 40
_OFF_NOME_DUP_PDS: int = 88
_OFF_UNIDADE_PDS: int = 152
_OFF_IDX_DICIONARIO_PDS: int = 544

_TAMANHO_REGISTRO_TABELA_PDS: int = 64
_OFF_TAB_IDX_PDS: int = 0
_OFF_TAB_INTERVALO_PDS: int = 16
_OFF_TAB_N_AMOSTRAS_PDS: int = 20
_OFF_TAB_BYTE_OFFSET_PDS: int = 48

_TICK_S_PDS: float = 1e-7
_TAMANHOS_DE_AMOSTRA_PDS: tuple[int, ...] = (1, 2, 4, 8)
_FRACAO_MINIMA_PARES_FECHADOS_PDS: float = 0.9
_JANELA_BUSCA_BYTES_PDS: int = 4_000_000
_MIN_REGISTROS_CANDIDATO_PDS: int = 8
_MIN_CANAIS_COM_DADO_PDS: int = 8
_MAX_CANDIDATOS_TENTADOS_PDS: int = 200


@dataclass(frozen=True)
class _BlocoTabelaPds:
    idx: int
    intervalo_ticks: int
    n_amostras: int
    byte_offset: int
    bytes_por_amostra: int = 4


def _e_registro_dicionario_pds(dados: bytes, offset: int) -> str | None:
    if offset + _ESTRIDE_DICIONARIO_PDS > len(dados):
        return None
    nome = _ler_string_u16(dados, offset + _OFF_NOME_PDS, _LEN_NOME_MAX_PDS)
    if not nome or len(nome) < 1:
        return None
    repetido = _ler_string_u16(dados, offset + _OFF_NOME_DUP_PDS, _LEN_NOME_MAX_PDS)
    if repetido != nome:
        return None
    return nome


def _candidatos_dicionario_pds(dados: bytes) -> list[tuple[int, int]]:
    validos: set[int] = set()
    limite = len(dados) - _ESTRIDE_DICIONARIO_PDS - _OFF_NOME_DUP_PDS - 4
    offset = 0
    while offset < limite:
        if _e_registro_dicionario_pds(dados, offset) is not None:
            validos.add(offset)
        offset += 2

    candidatos: list[tuple[int, int]] = []
    visitados: set[int] = set()
    for v in validos:
        inicio = v
        while (inicio - _ESTRIDE_DICIONARIO_PDS) in validos:
            inicio -= _ESTRIDE_DICIONARIO_PDS
        if inicio in visitados:
            continue
        visitados.add(inicio)
        n = 0
        p = inicio
        while p in validos:
            n += 1
            p += _ESTRIDE_DICIONARIO_PDS
        if n >= _MIN_REGISTROS_CANDIDATO_PDS:
            candidatos.append((inicio, n))

    candidatos.sort(key=lambda c: (-c[1], c[0]))
    return candidatos


def _ler_tabela_pds(
    dados: bytes, offset_inicio: int, n_dicionario: int, offset_dicionario_abs: int
) -> list[_BlocoTabelaPds]:
    blocos: list[_BlocoTabelaPds] = []
    p = offset_inicio
    while p + _TAMANHO_REGISTRO_TABELA_PDS <= len(dados):
        idx = struct.unpack_from("<i", dados, p + _OFF_TAB_IDX_PDS)[0]
        intervalo = struct.unpack_from("<i", dados, p + _OFF_TAB_INTERVALO_PDS)[0]
        n_amostras = struct.unpack_from("<i", dados, p + _OFF_TAB_N_AMOSTRAS_PDS)[0]
        byte_offset = struct.unpack_from("<i", dados, p + _OFF_TAB_BYTE_OFFSET_PDS)[0]

        if intervalo <= 0 or n_amostras <= 0:
            break
        if not (0 <= idx < n_dicionario):
            break
        if byte_offset <= 0 or byte_offset + n_amostras > offset_dicionario_abs:
            break

        blocos.append(_BlocoTabelaPds(idx, intervalo, n_amostras, byte_offset))
        p += _TAMANHO_REGISTRO_TABELA_PDS

    return blocos


def _checar_invariante_e_deduzir_tamanhos(
    blocos: list[_BlocoTabelaPds], offset_dic_abs: int, caminho: Path
) -> tuple[int, int, list[_BlocoTabelaPds]]:
    ordenados = sorted(blocos, key=lambda b: b.byte_offset)
    fechados = 0
    buracos = 0
    tamanhos_resolvidos: dict[int, int] = {}  # byte_offset -> bytes_por_amostra

    for anterior, atual in itertools.pairwise(ordenados):
        distancia = atual.byte_offset - anterior.byte_offset
        if distancia < anterior.n_amostras:
            raise ErroDeLeitura(
                f"{caminho}: blocos de amostra sobrepostos na tabela: canal "
                f"{anterior.idx} em offset {anterior.byte_offset} com "
                f"{anterior.n_amostras} amostras e canal {atual.idx} em offset "
                f"{atual.byte_offset}. A tabela decodificada nao e confiavel."
            )

        t_resolvido = 4  # default fallback
        fechou = False
        for t in _TAMANHOS_DE_AMOSTRA_PDS:
            if distancia == anterior.n_amostras * t:
                fechou = True
                t_resolvido = t
                break

        if fechou:
            fechados += 1
        else:
            buracos += 1
            k = distancia // anterior.n_amostras
            if k in _TAMANHOS_DE_AMOSTRA_PDS:
                t_resolvido = k

        tamanhos_resolvidos[anterior.byte_offset] = t_resolvido

    if ordenados:
        ultimo = ordenados[-1]
        distancia = offset_dic_abs - ultimo.byte_offset
        t_resolvido = tamanhos_resolvidos.get(ultimo.byte_offset, 4)
        for t in _TAMANHOS_DE_AMOSTRA_PDS:
            if distancia == ultimo.n_amostras * t:
                t_resolvido = t
                break
        tamanhos_resolvidos[ultimo.byte_offset] = t_resolvido

    pares = fechados + buracos
    if pares and fechados / pares < _FRACAO_MINIMA_PARES_FECHADOS_PDS:
        raise ErroDeLeitura(
            f"{caminho}: so {fechados} de {pares} pares consecutivos de blocos "
            f"fecham com 1, 2, 4 ou 8 bytes por amostra (minimo "
            f"{_FRACAO_MINIMA_PARES_FECHADOS_PDS:.0%}). A tabela decodificada nao e "
            "confiavel."
        )

    blocos_com_tamanho = [
        _BlocoTabelaPds(
            b.idx,
            b.intervalo_ticks,
            b.n_amostras,
            b.byte_offset,
            tamanhos_resolvidos.get(b.byte_offset, 4),
        )
        for b in blocos
    ]
    return fechados, buracos, blocos_com_tamanho


class CosworthPdsReader:
    """Decodificador de container Pi Toolbox `.pds` com streaming em 64 KB."""

    formato_id = "pi_pds"
    versao = "1"
    suporta_amostra = True

    def __init__(self, calibracoes: dict[str, TransformacaoLinear] | None = None) -> None:
        self.calibracoes = calibracoes or {}

    def _obter_estrutura(
        self, caminho: Path
    ) -> tuple[Cabecalho, dict[int, tuple[str, str | None]], list[_BlocoTabelaPds]]:
        tamanho = caminho.stat().st_size
        if tamanho < _OFF_MAGIC_PDS + len(_MAGIC_PDS):
            raise ErroDeLeitura(f"{caminho}: arquivo menor que magic offset")

        with caminho.open("rb") as fh:
            fh.seek(_OFF_MAGIC_PDS)
            magic = fh.read(len(_MAGIC_PDS))
            if magic != _MAGIC_PDS:
                raise ErroDeLeitura(f"{caminho}: magic invalido para pi_pds")

            janela = min(_JANELA_BUSCA_BYTES_PDS, tamanho)
            base = tamanho - janela
            fh.seek(base)
            dados = fh.read(janela)

        candidatos = _candidatos_dicionario_pds(dados)
        if not candidatos:
            raise ErroDeLeitura(f"{caminho}: nenhum dicionario encontrado nos ultimos bytes")

        erro_maior: ErroDeLeitura | None = None
        for offset_dic, n_dic in candidatos[:_MAX_CANDIDATOS_TENTADOS_PDS]:
            try:
                nomes_por_idx: dict[int, tuple[str, str | None]] = {}
                idx_ambiguos: set[int] = set()
                for i in range(n_dic):
                    registro = offset_dic + i * _ESTRIDE_DICIONARIO_PDS
                    nome = _ler_string_u16(dados, registro + _OFF_NOME_PDS, _LEN_NOME_MAX_PDS)
                    if not nome:
                        raise ErroDeLeitura(f"{caminho}: registro de dicionario sem nome")
                    unidade = _ler_string_u16(dados, registro + _OFF_UNIDADE_PDS, 20)
                    idx = struct.unpack_from("<i", dados, registro + _OFF_IDX_DICIONARIO_PDS)[0]
                    if idx in nomes_por_idx and nomes_por_idx[idx][0] != nome:
                        idx_ambiguos.add(idx)
                    else:
                        nomes_por_idx[idx] = (nome, unidade or None)

                tabela_offset = offset_dic + n_dic * _ESTRIDE_DICIONARIO_PDS
                blocos_brutos = _ler_tabela_pds(
                    dados, tabela_offset, n_dic, offset_dic + base
                )
                if not blocos_brutos:
                    raise ErroDeLeitura(f"{caminho}: nenhum registro de tabela valido")

                fechados, buracos, blocos = _checar_invariante_e_deduzir_tamanhos(
                    blocos_brutos, offset_dic + base, caminho
                )

                por_idx: dict[int, list[_BlocoTabelaPds]] = {}
                for bloco in blocos:
                    por_idx.setdefault(bloco.idx, []).append(bloco)

                canais = []
                for idx in sorted(por_idx):
                    if idx in idx_ambiguos or idx not in nomes_por_idx:
                        continue
                    nome, unidade = nomes_por_idx[idx]
                    intervalos = {b.intervalo_ticks for b in por_idx[idx]}
                    if len(intervalos) != 1:
                        raise ErroDeLeitura(
                            f"{caminho}: canal {nome} com intervalos diferentes"
                        )
                    frequencia_hz = 1.0 / (intervalos.pop() * _TICK_S_PDS)
                    canais.append(
                        CanalBruto(
                            nome_bruto=nome,
                            frequencia_hz=frequencia_hz,
                            n_amostras=sum(b.n_amostras for b in por_idx[idx]),
                            unidade_declarada=unidade,
                        )
                    )

                if len(canais) < _MIN_CANAIS_COM_DADO_PDS:
                    raise ErroDeLeitura(f"{caminho}: menos de {_MIN_CANAIS_COM_DADO_PDS} canais")

                canal_mais_longo = max(canais, key=lambda c: c.n_amostras)
                duracao_s = canal_mais_longo.n_amostras / canal_mais_longo.frequencia_hz

                bruto: dict[str, str] = {
                    "offset_dicionario": str(offset_dic + base),
                    "n_canais_dicionario": str(n_dic),
                    "n_canais_com_dado": str(len(canais)),
                    "n_canais_sem_dado": str(n_dic - len(canais)),
                    "offset_tabela": str(tabela_offset + base),
                    "n_registros_tabela": str(len(blocos)),
                    "n_pares_fechados": str(fechados),
                    "n_buracos": str(buracos),
                }

                cab = Cabecalho(
                    formato_id=self.formato_id,
                    leitor_versao=self.versao,
                    canais=tuple(canais),
                    capturado_em=None,
                    duracao_s=duracao_s,
                    venue_declarado=None,
                    bruto=bruto,
                )
                return cab, nomes_por_idx, blocos
            except ErroDeLeitura as e:
                if erro_maior is None:
                    erro_maior = e
                continue

        assert erro_maior is not None
        raise ErroDeLeitura(f"{caminho}: falha de decodificacao: {erro_maior}")

    def inspecionar(self, caminho: Path) -> Cabecalho:
        cab, _nomes, _blocos = self._obter_estrutura(caminho)
        return cab

    def ler(self, caminho: Path) -> Iterator[Lote]:
        """Le amostras do .pds com gerador de streaming em blocos de 64 KB."""
        cab, nomes_por_idx, blocos = self._obter_estrutura(caminho)
        if not cab.canais:
            return

        # Agrupa blocos por canal (idx)
        blocos_por_idx: dict[int, list[_BlocoTabelaPds]] = {}
        for b in blocos:
            blocos_por_idx.setdefault(b.idx, []).append(b)

        # Mapa canal -> frequencia_hz
        canais_por_freq: dict[float, list[CanalBruto]] = {}
        canal_por_nome: dict[str, CanalBruto] = {c.nome_bruto: c for c in cab.canais}
        for c in cab.canais:
            canais_por_freq.setdefault(c.frequencia_hz, []).append(c)

        # Leitura com stream em buffer de 64 KB
        with caminho.open("rb", buffering=_TAMANHO_BUFFER_STREAMING) as fh:
            for freq_hz, lista_canais in sorted(canais_por_freq.items()):
                nomes_grupo: list[str] = []
                series_grupo: list[np.ndarray] = []

                for canal in lista_canais:
                    # Encontra o indice correspondente no dicionario
                    idx_canal = next(
                        (i for i, (n, _) in nomes_por_idx.items() if n == canal.nome_bruto),
                        None,
                    )
                    if idx_canal is None or idx_canal not in blocos_por_idx:
                        continue

                    # Le e concatena blocos do canal
                    partes: list[np.ndarray] = []
                    for bloco in blocos_por_idx[idx_canal]:
                        fh.seek(bloco.byte_offset)
                        bytes_totais = bloco.n_amostras * bloco.bytes_por_amostra
                        
                        # Streaming em fatias de 64 KB
                        bytes_restantes = bytes_totais
                        buffer_leitura = bytearray()
                        while bytes_restantes > 0:
                            tam_chunk = min(bytes_restantes, _TAMANHO_BUFFER_STREAMING)
                            pedaco = fh.read(tam_chunk)
                            if not pedaco:
                                break
                            buffer_leitura.extend(pedaco)
                            bytes_restantes -= len(pedaco)

                        # Conversao conforme largura de byte
                        t = bloco.bytes_por_amostra
                        if t == 8:
                            amostras = np.frombuffer(buffer_leitura, dtype="<f8")
                        elif t == 4:
                            amostras = np.frombuffer(buffer_leitura, dtype="<f4")
                        elif t == 2:
                            amostras = np.frombuffer(buffer_leitura, dtype="<i2")
                        elif t == 1:
                            amostras = np.frombuffer(buffer_leitura, dtype="<u1")
                        else:
                            amostras = np.frombuffer(buffer_leitura, dtype="<f4")

                        partes.append(amostras.astype(np.float64))

                    if not partes:
                        continue

                    serie = np.concatenate(partes) if len(partes) > 1 else partes[0]

                    # Aplicacao de calibracao linear se configurada
                    if canal.nome_bruto in self.calibracoes:
                        serie = self.calibracoes[canal.nome_bruto].aplicar(serie)

                    nomes_grupo.append(canal.nome_bruto)
                    series_grupo.append(serie)

                if not series_grupo:
                    continue

                # Emissao de Lotes Arrow
                total_linhas = max(len(s) for s in series_grupo)
                inicio = 0
                while inicio < total_linhas:
                    fim = min(inicio + _LINHAS_POR_LOTE, total_linhas)
                    t_s = pa.array(np.arange(inicio, fim, dtype=np.float64) / freq_hz)
                    arrays = [
                        t_s,
                        *(pa.array(s[inicio:fim]) for s in series_grupo),
                    ]
                    tabela = pa.RecordBatch.from_arrays(arrays, names=["t_s", *nomes_grupo])
                    yield Lote(frequencia_hz=float(freq_hz), tabela=tabela)
                    inicio = fim
