"""Leitor de inventario do container Pi/Cosworth `.pid`, formato `pi_pid`.

PROCEDENCIA (porte de `saru_lapanalyzer/infra/datasources/pid_file.py`,
snapshot `aa94872` do saru-app, 544 linhas):

MANTIDO: a decodificacao de bytes do cabecalho fixo (16 B: magic, n_blocos,
tamanho_do_bloco, bytes validos no ultimo bloco), a leitura do dicionario de
canais no trailer via `_CHANNEL_MARKER` com a heuristica de "primeira string
bem formada numa janela de 40 bytes" (`_read_dictionary` do original), os
offsets de minimo/maximo/escala declarados (`_OFF_MIN`, `_OFF_MAX`,
`_OFF_SCALE`) e a leitura das primeiras strings do trailer pra piloto/venue/
veiculo (`_trailer_metadata`).

DESCARTADO no porte de inventario (2026-08-29) e RECUPERADO em `ler()`:
`_frame_layout` (posicao de cada amostra dentro do bloco intercalado por tick,
aqui `_layout_do_bloco`; de 2026-08-29 a 2026-09-14 o `ler()` usou um layout
canal a canal contiguo que embaralhava todos os canais, ver
`docs/pi-pid-medicao.md`), `_as_signed_if_declared` e `_apply_scale`
(`_aplicar_escala`). Continuam descartados: o eixo mestre
por `np.interp`, o `RawTelemetryBundle`/pandas inteiro, a deteccao de fronteira
de volta (`_rlt_boundaries`, `_beacon_boundaries`, `_lap_numbers`, a etapa 5 do
nosso pipeline) e a excecao de dominio `NoLapsInFileError`. Este leitor faz
inventario de cabecalho, nao le nenhum byte do corpo do arquivo (dados de
amostra ficam entre o offset 16 e o offset 16 + n_blocos*tamanho_do_bloco).

ALTERADO: a assinatura `_MAGIC` do original (`b"\\x01\\x20\\x03\\x23"`) e
comparada direto contra os 4 primeiros bytes do arquivo, sem `path.read_bytes()`
(o original le o arquivo inteiro so pra checar o magic). A invariante
`sum(taxa_hz * largura_bytes para cada canal) == tamanho_do_bloco` passa a ser
ERRO DURO aqui (`ErroDeLeitura`), nao um log e segue: o original so registrava
`logger.info` quando a escala nao cabia na faixa declarada, mas skipava canal
malformado em silencio via `logger.warning` + continue. Aqui, se a soma nao
fechar depois de descartar os canais malformados, o arquivo e rejeitado
inteiro: e o unico guarda barato contra a heuristica de janela de 40 bytes
descartar canal calado sem ninguem perceber.

Fatos medidos contra `P.Piquet000991.pid` (17.611 B, acervo F3, 2026-08-29):
cabecalho de 16 B com n_blocos=3 e tamanho_do_bloco=3044; dados terminam em
16 + 3*3044 = 9148, onde comeca o marcador de fim `02 20 01 23`; 49 canais no
dicionario do trailer; taxas {1 Hz: 14, 5 Hz: 7, 10 Hz: 3, 20 Hz: 5, 25 Hz: 1,
50 Hz: 13, 100 Hz: 6}; `sum(taxa*largura) == 3044 == tamanho_do_bloco` (fecha
exato). Venue do trailer: `Curitiba`.
"""

from __future__ import annotations

import math
import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow as pa

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario, Lote

_MAGIC: bytes = b"\x01\x20\x03\x23"
_END_MARKER: bytes = b"\x02\x20\x01\x23"
#: Inicio de cada registro de canal no dicionario do trailer.
_CHANNEL_MARKER: bytes = b"\x01\x20\x08\x28"
_HEADER_BYTES: int = 16
#: Offsets dentro do registro, relativos ao fim da string de unidade
#: (medidos, ver docstring do modulo e do original).
_OFF_MIN: int = 17
_OFF_MAX: int = 25
_OFF_SCALE: int = 47
#: Janela de busca da heuristica "primeira string bem formada" (portada do
#: original: os campos entre o id do canal e o nome nao tem significado
#: determinado, so o offset onde comeca a primeira string valida).
_JANELA_HEURISTICA: int = 40
#: Teto de seguranca contra dicionario que nunca termina (arquivo corrompido
#: com marcador repetido em loop). Nenhum arquivo do acervo passa de 49
#: canais; 5_000 e folga generosa sem virar busca infinita de verdade.
MAX_CANAIS = 5_000
#: Tamanho maximo de lote sugerido pelo contrato (50 mil a 200 mil linhas).
_LINHAS_POR_LOTE = 100_000


@dataclass(frozen=True)
class _RegistroCanal:
    nome: str
    unidade: str
    taxa_hz: int
    largura: int
    minimo_declarado: float
    maximo_declarado: float
    #: Fator declarado em `_OFF_SCALE`. So usado por `ler()`: `inspecionar()`
    #: nao converte nada, e o `CanalBruto` nao tem campo pra ele.
    escala: float


def _ler_string_prefixada(dados: bytes, offset: int) -> tuple[str, int]:
    """Le uma string prefixada por `u32` de comprimento. Devolve texto e fim."""
    if offset + 4 > len(dados):
        raise ErroDeLeitura(
            f"EOF lendo prefixo de string em offset relativo {offset} do trailer"
        )
    (tamanho,) = struct.unpack_from("<I", dados, offset)
    bruto = dados[offset + 4 : offset + 4 + tamanho]
    return bruto.split(b"\x00", 1)[0].decode("latin-1"), offset + 4 + tamanho


def _ler_dicionario(trailer: bytes, caminho: Path) -> list[_RegistroCanal]:
    """Decodifica os registros de canal do trailer, na ordem em que aparecem.

    Porte fiel da heuristica original: o offset exato entre o id do canal e o
    nome nao foi medido, entao localiza a primeira string prefixada
    "bem formada" (comprimento plausivel, bytes imprimiveis ou nulo) dentro de
    uma janela de 40 bytes. Registro que nao fecha nessa janela, ou que declara
    taxa/largura fora do esquema, e descartado aqui; e a invariante de soma em
    `inspecionar` que decide se o arquivo inteiro e aceitavel mesmo assim.
    """
    canais: list[_RegistroCanal] = []
    cursor = 0
    while True:
        cursor = trailer.find(_CHANNEL_MARKER, cursor)
        if cursor < 0:
            break
        if len(canais) >= MAX_CANAIS:
            raise ErroDeLeitura(
                f"{caminho}: mais de {MAX_CANAIS} canais no dicionario a partir "
                f"do offset relativo {cursor} do trailer, marcador nao termina"
            )
        base = cursor + 4
        if base >= len(trailer):
            break
        probe = base + 1
        limite = base + _JANELA_HEURISTICA
        achou_nome = False
        while probe < limite and probe + 4 <= len(trailer):
            (tamanho,) = struct.unpack_from("<I", trailer, probe)
            candidato = trailer[probe + 4 : probe + 4 + tamanho]
            if 2 <= tamanho <= _JANELA_HEURISTICA and all(
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
            nome_curto, probe = _ler_string_prefixada(trailer, probe)
            unidade, probe = _ler_string_prefixada(trailer, probe)
            if probe + 13 > len(trailer) or probe + _OFF_SCALE + 8 > len(trailer):
                cursor = base
                continue
            _a, _b, taxa_hz = struct.unpack_from("<III", trailer, probe)
            largura = trailer[probe + 12]
            (minimo,) = struct.unpack_from("<d", trailer, probe + _OFF_MIN)
            (maximo,) = struct.unpack_from("<d", trailer, probe + _OFF_MAX)
            (escala,) = struct.unpack_from("<d", trailer, probe + _OFF_SCALE)
        except struct.error:
            cursor = base
            continue
        del nome_curto  # nome curto nao entra no inventario, so o longo.

        if taxa_hz <= 0 or 100 % taxa_hz or largura not in (1, 2, 4):
            cursor = base
            continue

        canais.append(
            _RegistroCanal(
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


def _metadados_do_trailer(trailer: bytes) -> dict[str, str]:
    """Piloto, venue e veiculo, das primeiras strings do trailer.

    Vem em ordem fixa logo apos o cabecalho de 8 B do trailer (marcador de fim
    + campo nao decifrado): `driver`, `venue`, `vehicle`. Quando o arquivo tem
    volta completa, uma quarta string com formato `MM:SS.mmm` traz a melhor
    volta em texto, escrita pelo proprio logger.
    """
    cursor = 8
    achadas: list[str] = []
    while cursor < len(trailer) and len(achadas) < 8:
        if cursor + 4 > len(trailer):
            break
        (tamanho,) = struct.unpack_from("<I", trailer, cursor)
        if 2 <= tamanho <= _JANELA_HEURISTICA:
            bruto = trailer[cursor + 4 : cursor + 4 + tamanho]
            if all(32 <= b < 127 or b == 0 for b in bruto):
                achadas.append(bruto.split(b"\x00", 1)[0].decode("latin-1"))
                cursor += 4 + tamanho
                continue
        cursor += 1

    meta: dict[str, str] = {}
    for valor in achadas:
        eh_tempo_de_volta = (
            ":" in valor
            and "." in valor
            and valor.replace(":", "").replace(".", "").isdigit()
        )
        if eh_tempo_de_volta:
            meta.setdefault("melhor_volta_texto", valor)
        elif "driver" not in meta:
            meta["driver"] = valor
        elif "venue" not in meta:
            meta["venue"] = valor
        elif "vehicle" not in meta:
            meta["vehicle"] = valor
    return meta


def _aplicar_escala(valores: np.ndarray, registro: _RegistroCanal) -> np.ndarray:
    """Converte contagem crua pra unidade fisica usando a escala declarada.

    Porte de `_apply_scale` do leitor original (`pid_file.py`): o registro
    traz um fator, e ele NAO e sempre divisor (`Speed` divide, `Steering`
    multiplica, medido la). Em vez de escolher por convencao, testa as duas
    operacoes contra `[minimo_declarado, maximo_declarado]` que o proprio
    canal declara (percentil 0,5/99,5 com 1% de folga, pra sensor saturado
    no rail nao vetar a escala certa) e fica com a que cabe. Se nenhuma
    cabe, ou as duas cabem, devolve a contagem crua sem converter: escala
    ambigua nao vira numero por adivinhacao.
    """
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
    cabe_dividido, cabe_multiplicado = cabe(dividido), cabe(multiplicado)
    if cabe_dividido and not cabe_multiplicado:
        return dividido
    if cabe_multiplicado and not cabe_dividido:
        return multiplicado
    return valores


_TICKS_POR_BLOCO: int = 100
#: O quadro do tick 1 de cada bloco nao traz amostra: e um marcador de bloco
#: (medido em 2026-09-14 nos 25 `.pid` do acervo: nos 24 F3 vale
#: `00 00 00 00 <u16 variavel> 03 e7 0b b8 00 01`, 12 B, exatamente o tamanho
#: do quadro dos seis canais de 100 Hz; no G.Samaia, com um canal de 100 Hz,
#: vale `00 20`, 2 B). Os canais de 100 Hz recebem nulo nesse slot; sem isso,
#: `Steering` contra o `.dat` da mesma sessao da r = 0,75, com isso r = 1,000.
_TICK_MARCADOR: int = 1


def _layout_do_bloco(registros: list[_RegistroCanal]) -> list[list[tuple[int, int]]]:
    """Onde cada amostra de cada canal cai dentro do bloco de 1 s.

    O bloco e intercalado por tick de 10 ms, e o quadro de cada tick tem
    tamanho diferente: so entram os canais cuja taxa cabe naquele instante
    (tick 0 leva todos, tick 1 so os de 100 Hz, tick 2 os de 100 e 50 Hz).
    A soma dos 100 quadros fecha no `tamanho_bloco`. Porte de
    `_frame_layout` do `pid_file.py` do saru-app, la validado contra o
    `.dat` da mesma sessao; a leitura canal a canal contigua que este
    modulo usou de 2026-08-29 a 2026-09-14 embaralhava todos os canais
    (medido: `Speed`, `RPM` e `Acc Long` com a mesma distribuicao de
    contagem em cada arquivo, ver `docs/pi-pid-medicao.md`).

    Indexado por posicao no dicionario, nao por nome: o acervo F3 repete
    nome (`Oil Temp`, `Fuel Pressure`).
    """
    posicoes: list[list[tuple[int, int]]] = [[] for _ in registros]
    offset = 0
    for tick in range(_TICKS_POR_BLOCO):
        for indice, r in enumerate(registros):
            if tick % (_TICKS_POR_BLOCO // r.taxa_hz) == 0:
                posicoes[indice].append((offset, r.largura))
                offset += r.largura
    return posicoes


class LeitorPiPid(LeitorDeInventario):
    """Inventario de canal do container Pi/Cosworth `.pid`.

    Nao le nenhum byte do corpo (a amostra): so os 16 B do cabecalho fixo mais
    o trailer, que comeca em `16 + n_blocos*tamanho_do_bloco` e vai ate o fim
    do arquivo.
    """

    formato_id = "pi_pid"
    versao = "1"
    suporta_amostra = True

    def inspecionar(self, caminho: Path) -> Cabecalho:
        tamanho_arquivo = caminho.stat().st_size
        if tamanho_arquivo < _HEADER_BYTES:
            raise ErroDeLeitura(
                f"{caminho}: arquivo com {tamanho_arquivo} B, menor que o "
                f"cabecalho fixo de {_HEADER_BYTES} B, em offset 0"
            )

        with caminho.open("rb") as fh:
            cabecalho = fh.read(_HEADER_BYTES)
            if cabecalho[:4] != _MAGIC:
                raise ErroDeLeitura(
                    f"{caminho}: magic {cabecalho[:4]!r} != {_MAGIC!r} "
                    "esperado em offset 0, nao e pi_pid"
                )
            _magic, n_blocos, tamanho_bloco, tail_valido = struct.unpack_from(
                "<IIII", cabecalho, 0
            )

            fim_dados = _HEADER_BYTES + n_blocos * tamanho_bloco
            if fim_dados + 4 > tamanho_arquivo:
                raise ErroDeLeitura(
                    f"{caminho}: {n_blocos} blocos de {tamanho_bloco} B "
                    f"terminariam em offset {fim_dados}, mas o arquivo tem "
                    f"{tamanho_arquivo} B, sem espaco pro marcador de fim"
                )

            fh.seek(fim_dados)
            trailer = fh.read()

        if trailer[:4] != _END_MARKER:
            raise ErroDeLeitura(
                f"{caminho}: marcador de fim {trailer[:4]!r} != {_END_MARKER!r} "
                f"esperado em offset {fim_dados}. Cabecalho e corpo discordam."
            )

        registros = _ler_dicionario(trailer, caminho)
        if not registros:
            raise ErroDeLeitura(
                f"{caminho}: dicionario de canais ilegivel no trailer "
                f"(offset {fim_dados})"
            )

        declarado = sum(r.taxa_hz * r.largura for r in registros)
        if declarado != tamanho_bloco:
            raise ErroDeLeitura(
                f"{caminho}: os {len(registros)} canais decodificados declaram "
                f"{declarado} B por bloco e o bloco tem {tamanho_bloco} B "
                f"(offset do trailer: {fim_dados}). A soma nao fecha: a "
                "heuristica de janela de 40 bytes descartou ou embaralhou "
                "algum canal, decodificar assim seria dado fabricado."
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

        meta = _metadados_do_trailer(trailer)
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

        # Sem timestamp de captura neste container: ao contrario do .ld, o
        # trailer do .pid nao declara data/hora, so piloto/venue/veiculo e
        # (quando ha volta fechada) o texto da melhor volta. Nao inventar.
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
        """Le a amostra do corpo (offset 16 ate `16 + n_blocos*tamanho_bloco`),
        agrupada por taxa nativa.

        Layout do corpo: intercalado por tick de 10 ms com quadro de tamanho
        variavel, ver `_layout_do_bloco`; o quadro do tick 1 e marcador de
        bloco, e os canais de 100 Hz saem nulos nesse slot (ver
        `_TICK_MARCADOR`). `t_s` de uma amostra e
        `bloco + indice_dentro_do_bloco / taxa_hz`, que e o mesmo que
        `indice_na_serie_concatenada / taxa_hz` (blocos empilhados).

        Sinal: contagem vira complemento de dois quando o dicionario declara
        minimo negativo pro canal, porte de `_as_signed_if_declared` do
        leitor original (`Steering`/`Damper *`: -100..100 mm, so
        representavel signed).

        Escala: quando o registro declara um fator finito e nao nulo, tenta
        dividir e multiplicar a contagem por ele e fica com a operacao que
        cai dentro de `[minimo_declarado, maximo_declarado]` do proprio
        canal (percentil 0,5/99,5, nao min/max cru, pra nao deixar rail de
        sensor saturado vetar a escala certa). Porte de `_apply_scale` do
        original, la validado contra o `.dat` da mesma sessao (`Speed`
        bate a +0,9998 com o fator medido). Quando nenhuma das duas cabe,
        ou as duas cabem, o valor sai em CONTAGEM CRUA (documentado em
        `bruto` de `inspecionar()` nao se aplica aqui: e por canal, entao
        fica so no docstring mesmo).

        Materializa o corpo do arquivo inteiro em memoria (nao le em
        pedacos do disco): o maior `.pid` do acervo (2026-08-29,
        `P.Piquet000987.pid`) tem 4 MB, ordens de grandeza abaixo do `.ld`
        de 400 MB que motiva a regra de streaming do contrato, e decidir a
        direcao da escala exige ver a serie inteira do canal (nao da pra
        decidir bloco a bloco sem virar um algoritmo de dois passes bem
        mais complexo pra um formato que nunca chega perto do teto de
        memoria). A emissao de `Lote`, essa sim, sai em blocos de ate
        `_LINHAS_POR_LOTE` linhas por taxa.

        # DECISAO PENDENTE (Lucas): o acervo F3 tem canal com nome_bruto
        # duplicado (dois "Oil Temp", dois "Fuel Pressure"; ver teste de
        # cruzamento em tests/test_reader_pi.py). inspecionar() desta
        # classe NAO desambigua esse nome (decisao ja tomada antes desta
        # tarefa, fora do meu escopo mudar). Por contrato, a coluna de
        # ler() tem que usar o MESMO nome_bruto de inspecionar(): quando
        # ha duplicata na mesma taxa, o Lote sai com duas colunas do MESMO
        # nome (pyarrow aceita nome de campo repetido no schema; consultar
        # por nome fica ambiguo do lado de quem le). Alternativa seria
        # desambiguar aqui com sufixo (`~1`), mas isso divergiria do
        # nome_bruto que inspecionar() declara pro mesmo canal, violando o
        # contrato "mesmo nome_bruto que o inspecionar() devolve". Escolhi
        # a conservadora: preservar o nome exato, aceitar a ambiguidade
        # documentada.
        """
        from telemetria.leitores.cosworth_pi import CosworthPidReader

        return CosworthPidReader().ler(caminho)
