"""Leitor de inventario para AiM RaceStudio 3 (.xrk), formato_id aim_xrk.

Decisao do Lucas: Python puro, sem `libxrk` (dependencia de terceiro fica
fora do escopo desta PoC, ver `pyproject.toml`, extra `aim` nao usado aqui).
Nenhuma dependencia nova.

Estrutura MEDIDA em 2026-08-29 contra 66 arquivos reais do acervo (nao veio
de documentacao do fabricante, que nao e publica). Um parser exploratorio de
cerca de 60 linhas leu 56 dos 66 a 100% de cobertura de bytes antes de este
arquivo existir; a implementacao abaixo formaliza esse mesmo parser.

Container de chunks delimitado por ASCII, com abertura e fecho simetricos::

    abertura:  '<h' + tag[4] + u32 tamanho + versao(0x01 ou 0x02) + '>'
    fecho:     '<'  + tag[4] + u16 checksum + '>'

`tag` tem sempre 4 bytes (`'TRK '` com espaco no fim, `'MANL'`/`'MODL'` com a
letra final grudada. o prefixo de 3 bytes e o que identifica a familia).

O chunk `CNF` e um CONTAINER: seu corpo e uma sequencia contigua de
sub-chunks `CHS` (definicao de canal, 112 bytes fixos, um canal por chunk) e
`CDE` (descricao, binaria, nao decodificada aqui: nao faz parte do
contrato). Fora do `CNF` vem uma sequencia de chunks de metadado soltos
(`RCR` piloto, `VEH` veiculo, `CMP` campeonato, `MANL`/`MODL` fabricante e
modelo da ECU, `TRK ` pista, `TMD` data, `TMT` hora, mais `VTY`, `NDV`,
`SRC`, `ENF`, `RACM`, `HWNF`, `VET`, `ODO` que este leitor nao usa e apenas
pula).

Depois dos metadados comeca o stream de amostra, uma mistura de dois tipos
de unidade que se alternam sem marcador de secao:

1. Registro compacto: ``'(' + kind(1) + u32 timestamp_ms + u16 id + payload
   + ')'``. Kinds medidos e cobertos:

   - ``S`` (escalar): ``payload`` tem `bytes_por_amostra` do canal `id`,
     valor lido do `CHS` correspondente.
   - ``G`` (grupo): ``payload`` tem a SOMA de `bytes_por_amostra` de cada
     canal membro (nao um tamanho fixo: medido com membros de 2 bytes,
     payload de grupo com 10 membros saiu 20 bytes, nao 40). `id` e o id do
     GRUPO (namespace proprio, definido pelo chunk `GRP`: ``u16 id_grupo +
     u16 contagem + contagem * u16 id_de_canal``, tambem aninhado dentro do
     `CNF`).
   - ``M`` (rajada): ``'(' + 'M' + u32 timestamp_ms + u16 id + u16 n +
     n * int16 + ')'``, contagem `n` inline no proprio registro (canal
     amostrado em rajada, ex. vibracao/knock em alta taxa).
   - ``c`` (canal expandido, 3 sub-formatos V1/V2/V3, ver
     `_tamanho_registro_c`): cabecalho DIFERENTE do S/G/M (11 ou 7 bytes
     conforme o sub-formato, sem o par ts_ms/cid nas mesmas posicoes).
     Corrigido em 29/08 (portado de libxrk/aim_xrk.pyx): ate entao esse
     kind dava `break` no walker e derrubava a cobertura do arquivo inteiro
     dali pra frente (3 arquivos do acervo paravam nele, um a 0% de
     cobertura). So o V1 mapeia pro MESMO namespace de canal do `S`; V2/V3
     usam um `channel_field` que so vira indice de canal real depois de
     reconciliar o arquivo inteiro contra o `CHS` (o que o proprio libxrk
     so faz no fim do parse) - fora do alcance de um walker streaming de
     passada unica. Reconhecido, tamanho calculado certo, e PULADO sem
     decodificar amostra (ocorrencias contadas em `bruto`); isso e o piso
     aceito pelo escopo, nao o ideal.

   Kind fora desses quatro interrompe a leitura aqui: sem tabela de tamanho
   por kind, adivinhar o payload e o mesmo buraco do B2.

2. Chunk nomeado solto, mesmo formato de abertura/fecho do topo, aparecendo
   INTERCALADO com os registros compactos acima (nao so no cabecalho):
   `LAP` (20 OU 32 bytes/volta - os dois tamanhos convivem no acervo, 87 dos
   116 arquivos usam o de 32; os primeiros 20 bytes tem o MESMO layout nos
   dois, ver `_acumula_lap`), `GPS` (56 bytes: timecode int32 + payload
   u-blox NAV-SOL, posicao e velocidade ECEF em centimetros; DECODIFICADO
   desde 29/08 em 12 canais sintetizados que saem como serie propria, ver o
   bloco GPS antes de `_inspecionar_bytes`; validado no par kart-guara:
   decodifica pra lat -15.82570, lon -47.97108, 1081 m, que e o Guara em
   Brasilia e bate com a pasta do acervo) e `CAL` (144 bytes, calibracao
   analogica).

   # CAL nao decodificado aqui de proposito: sem ele os int16 crus de canal
   # analogico nao viram unidade fisica, e isso e trabalho do `ler()` da
   # etapa 3, nao do inventario.

Arquivos do acervo que paravam numa variante de registro nao mapeada (kind
desconhecido, ou payload que nao fecha em ')' onde esperado) caem pra
leitura PARCIAL declarada, nao falha: os canais definidos em `CHS` ja foram
lidos antes de o stream de amostra comecar, entao o inventario de canal sai
completo mesmo quando a contagem de amostra para no meio. O ponto de parada
e quantos bytes ficaram sem cobertura vao em `bruto`.

## ler(): amostra em streaming, sem calibracao, PASSADA UNICA

`ler()` percorre o MESMO fluxo de registros que `inspecionar()` (chunks +
S/G/M) uma unica vez (ate 29/08 eram duas passadas: a segunda so existia
porque a decodificabilidade de um canal de `bytes_amostra != 2` so fica
definitiva depois de varrer o arquivo inteiro procurando um registro `M`
que o confirme, e o schema por taxa (`colunas_por_periodo`) precisa dessa
resposta ANTES do primeiro `Lote`).

Validado em 29/08 contra os 116 `.xrk`/`.xrz` do acervo (script de
varredura da tarefa, nao versionado): em ZERO arquivos um registro (`S`,
`G` ou `M`) referencia um `cid`/`gid` cuja definicao (`CHS`/`GRP`, dentro ou
fora do `CNF`) ainda nao foi vista; a definicao sempre precede o uso. 22
`CHS` sao redefinidos (mesmo `cid` duas vezes, sempre com os MESMOS valores
de `periodo_us`/`bytes_amostra`, sempre antes de qualquer amostra), o que
nao muda a leitura incremental. E em ZERO arquivos um canal aparece primeiro
via `S`/`G` e so e confirmado decodificavel por um `M` mais tarde no mesmo
arquivo (quando ha `M` pra um `cid`, e sempre a PRIMEIRA aparicao desse
`cid` no stream de amostra).

A passada unica USA essa medicao pra decidir, EM CADA REGISTRO, se acumula
o evento: `bytes_amostra == 2` decide decodificavel na hora (nao depende de
nada mais adiante), `cid` ja visto num `M` anterior tambem decide na hora,
e so esses dois casos entram na estrutura de eventos por taxa. Primeira
versao desta passada unica (29/08, revertida no mesmo dia) acumulava TODO
evento indiscriminadamente e filtrava so no fim: correto, mas mais lento
que a versao antiga de duas passadas em arquivos com canal de
`bytes_amostra != 2` de alto volume e nunca confirmado por `M` (`Distance
Lap`, `Master Clk`: dezenas de milhares de amostras cada, sempre
descartadas) porque o custo de acumular+filtrar essas dezenas de milhares
de eventos por nada superava o custo da segunda passada que a reescrita
eliminava. A versao atual so acumula o que ja sabe que e decodificavel.

Isso e uma aposta em cima da medicao, nao uma garantia do formato: um canal
de `bytes_amostra != 2` confirmado por `M` DEPOIS de ja ter sido descartado
via `S`/`G` (nunca visto no acervo) perderia essas amostras anteriores a
confirmacao. Pra nao devolver dado incompleto nesse caso hipotetico, todo
`cid` que perde um evento por essa razao vai pra `cids_com_evento_perdido`;
se esse `cid` acabar confirmado por `M` (`cid` em `canais_via_m` E em
`cids_com_evento_perdido`), a passada unica reconhece que furou PRA ESSE
ARQUIVO e cai pra `_ler_bytes_duas_passadas` (o algoritmo antigo, correto
por construcao, preservado so pra este caso de escape - nunca exercitado
pelo acervo real, mas mantido porque "nunca medido" nao e "impossivel").

O offset de parada da passada unica e o MESMO que `inspecionar()` produz,
pela mesma logica de quebra (`_percorre_registros`, compartilhada por
`inspecionar()`, `_ler_bytes` e `_ler_bytes_duas_passadas`).

### Que canais sao decodificados

**So os canais cujo `bytes_amostra` (`CHS`+0x48) e exatamente 2 sao lidos
como int16 cru** (`struct '<h'`), que e o formato que o enunciado descreve
e que bate com os canais analogicos/digitais medidos (RPM, TPS, ECT, OILP,
BRAKE_F, LAT_ACC, STEERING, LONG_ACC, GyroX-Z, LogT, VBat: todos 2 bytes).
Um registro `M` (rajada) e sempre `n * int16` PELO FORMATO DO REGISTRO
(docstring acima), entao um canal usado via `M` e decodificado mesmo que o
`CHS` dele declare outro `bytes_amostra` (o `bytes_amostra` do `CHS`
descreve o tamanho da amostra em `S`/`G`, nao o de `M`).

Canais com `bytes_amostra` em {4, 8, 12, 20, 32, 56, 60} (medido no
acervo: `Distance Lap`, `Gear`, odometros, `Lap Time`, `GPS`/`iGPS`,
`Best Time`) NAO sao decodificados aqui. Medido na fixture sintetica
(`MClk`, `bytes_amostra=4`): o valor gravado e um `float32`, nao um
`int32`, entao um canal de 4 bytes pode ser inteiro OU ponto flutuante e
nao ha como saber qual sem o `CAL`/documentacao do fabricante que este
leitor nao decodifica. Adivinhar o tipo seria a mesma doenca do B2.
`# DECISAO PENDENTE (Lucas):` decodificar esses canais exige mapear o tipo
por largura (ou por `CAL`), e isso fica pra quando houver um canal desses
que o negocio realmente precise. Por ora o inventario (`inspecionar()`) ja
lista esses canais com `n_amostras` correto, so nao vem no `Lote`.

### Rajada (`M`): timestamp de cada amostra e inferido

O registro `M` tem UM `ts_ms` pro conjunto de `n` amostras, nao um por
amostra. `# DECISAO PENDENTE (Lucas):` a amostra `i` (0-indexed) do burst
recebe `ts_ms + i * periodo_us_do_canal / 1000`, isto e, as `n` amostras
sao espacadas pelo periodo nativo do canal (INFERIDO: nao ha campo no
formato que declare isso, mas e a leitura natural de "canal amostrado em
rajada na taxa dele", e evita colidir todas as `n` amostras no mesmo
`t_s`, que seria pior: perderia `n-1` valores por sobrescrita silenciosa).

### Alinhamento por taxa (opcao B do enunciado)

Um `Lote` por taxa nativa, com uma coluna por canal decodificavel daquela
taxa. Canais da mesma taxa podem ter `ts_ms` diferentes entre si (nao sao
sincronos fora dos registros `G`): o eixo `t_s` da tabela e a UNIAO dos
timestamps vistos por qualquer canal daquela taxa, e cada celula sem
amostra naquele instante fica `NaN` (arrow `float64`). Nunca interpolado e
nunca repetido do valor anterior: `NaN` e a resposta honesta pra "esse
canal nao amostrou aqui". Duas outras opcoes descartadas: (a) um `Lote`
por CANAL sem alinhamento nenhum (zero risco, mas nao respeita o
agrupamento por taxa que o contrato pede), (c) alinhar com `np.interp`,
que e exatamente o que o saru-app fazia e foi descartado por decisao do
Lucas.
"""

from __future__ import annotations

import struct
from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pyarrow as pa

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario, Lote

# 0.2.0: canais GPS sintetizados (serie propria "gps") + unwrap do timecode.
# 0.3.0: decode TIPADO dos escalares de 2 bytes pelo byte corpo[20] do CHS
# (float16/uint16/int16; ate entao tudo saia int16 e um fp16 de 100.0 virava
# 22080). Versao propria porque muda o VALOR das amostras, e `reingerir
# --desatualizadas` usa a versao pra saber o que reprocessar. A versao entra
# na chave natural da ingestao: reprocessar com este leitor produz linha nova
# de `ingestao`, nunca sobrescreve a anterior.
_VERSAO = "0.3.0"

# Linhas por Lote emitido em ler(): grande o bastante pra nao pulverizar em
# milhares de Parquet pequenos, pequeno o bastante pra nao acumular um
# arquivo de 36 MB inteiro em RecordBatch antes de escrever.
_LINHAS_POR_LOTE = 100_000

# Prefixo de 3 bytes das tags que carregam metadado textual simples, e a
# chave correspondente em `bruto`. `MANL`/`MODL` tem o prefixo de 3 letras
# igual a `MAN`/`MOD`.
_TAGS_TEXTO: dict[bytes, str] = {
    b"RCR": "piloto",
    b"VEH": "veiculo",
    b"CMP": "campeonato",
    b"MAN": "fabricante_ecu",
    b"MOD": "modelo_ecu",
    b"TRK": "pista_declarada",
    b"TMD": "data_captura",
    b"TMT": "hora_captura",
}


class _CanalTmp:
    __slots__ = ("bytes_amostra", "nome_curto", "nome_longo", "periodo_us", "tipo")

    def __init__(
        self,
        nome_curto: str,
        nome_longo: str,
        periodo_us: int,
        bytes_amostra: int,
        tipo: int = -1,
    ) -> None:
        self.nome_curto = nome_curto
        self.nome_longo = nome_longo
        self.periodo_us = periodo_us
        self.bytes_amostra = bytes_amostra
        # corpo[20] do CHS: o BYTE DE TIPO do decoder, conferido contra a
        # tabela `_decoders` do libxrk (chaveada por `unknown[20]`, o mesmo
        # byte) e MEDIDO no acervo em 29/08 sobre os canais de 2 bytes:
        # 2.625 canais tipo 20 (float16: STEERING, SPEED_*, External
        # Voltage), 599 tipo 1 (uint16: OIL_P, FUEL_P, ECT), 118 tipo 4
        # (int16: RPM, EDL8_RPM). Ate 29/08 TUDO era lido como int16, e um
        # canal fp16 saia com o bit pattern cru: acelerador "22080" era
        # 100.0 em fp16 (0x5640). -1 = CHS curto demais pra ter o byte.
        self.tipo = tipo


def _texto(corpo: bytes) -> str:
    """Extrai texto ASCII/latin-1 ate o primeiro byte nulo."""
    return corpo.split(b"\x00", 1)[0].decode("latin-1", errors="replace").strip()


def _cabecalho_chunk(dados: bytes, off: int) -> tuple[bytes, int, int, int] | None:
    """Le abertura+fecho de um chunk em `off`.

    Devolve (tag, inicio_corpo, fim_corpo, proximo_offset), ou None se o que
    esta em `off` nao e um chunk valido (fim de arquivo, dado truncado, ou
    chunk cujo fecho nao bate com a tag/tamanho declarados).
    """
    if off + 12 > len(dados) or dados[off : off + 2] != b"<h":
        return None
    tag = dados[off + 2 : off + 6]
    tamanho = struct.unpack_from("<I", dados, off + 6)[0]
    if dados[off + 11 : off + 12] != b">":
        return None
    inicio_corpo = off + 12
    fim_corpo = inicio_corpo + tamanho
    fim_fecho = fim_corpo + 8
    if fim_fecho > len(dados):
        return None
    fecho = dados[fim_corpo:fim_fecho]
    if fecho[0:1] != b"<" or fecho[1:5] != tag or fecho[7:8] != b">":
        return None
    return tag, inicio_corpo, fim_corpo, fim_fecho


def _parse_chs(corpo: bytes) -> tuple[int, _CanalTmp] | None:
    if len(corpo) < 0x4C:
        return None
    cid = struct.unpack_from("<I", corpo, 0)[0]
    curto = corpo[0x18:0x20].split(b"\x00", 1)[0].decode("latin-1", errors="replace")
    longo = corpo[0x20:0x40].split(b"\x00", 1)[0].decode("latin-1", errors="replace")
    periodo_us = struct.unpack_from("<I", corpo, 0x40)[0]
    bytes_amostra = struct.unpack_from("<I", corpo, 0x48)[0]
    return cid, _CanalTmp(
        curto.strip(), longo.strip(), periodo_us, bytes_amostra, corpo[20]
    )


def _parse_grp(corpo: bytes) -> tuple[int, list[int]] | None:
    if len(corpo) < 4:
        return None
    gid = struct.unpack_from("<H", corpo, 0)[0]
    contagem = struct.unpack_from("<H", corpo, 2)[0]
    fim = 4 + 2 * contagem
    if fim > len(corpo):
        return None
    membros = [struct.unpack_from("<H", corpo, 4 + 2 * i)[0] for i in range(contagem)]
    return gid, membros


def _escaneia_container(
    dados: bytes,
    inicio: int,
    fim: int,
    canais: dict[int, _CanalTmp],
    grupos: dict[int, list[int]],
) -> None:
    """Percorre chunks dentro de [inicio, fim), coletando CHS e GRP.

    Usado para o corpo do chunk CNF, que embrulha as definicoes de canal.
    Chunk que nao bate no meio do container e apenas ignorado ali (o
    container pai ja garantiu, pelo tamanho declarado, onde ele termina).
    """
    off = inicio
    while off < fim:
        span = _cabecalho_chunk(dados, off)
        if span is None:
            break
        tag, corpo_ini, corpo_fim, prox = span
        prefixo = tag[:3]
        corpo = dados[corpo_ini:corpo_fim]
        if prefixo == b"CHS":
            par = _parse_chs(corpo)
            if par is not None:
                canais[par[0]] = par[1]
        elif prefixo == b"GRP":
            par_g = _parse_grp(corpo)
            if par_g is not None:
                grupos[par_g[0]] = par_g[1]
        off = prox


def _tamanho_registro_c(
    dados: bytes, off: int, tamanho_total: int, canais: dict[int, _CanalTmp]
) -> tuple[int, str] | None:
    """Calcula o offset do fecho ')' de um registro kind `c` SEM decodificar
    a amostra. Ate 29/08 esse kind nao era conhecido: qualquer registro fora
    de S/G/M dava `break` no walker e o resto do arquivo (LAP, GPS, o resto
    da amostra) virava `bytes_sem_cobertura` (B2 do walker). `c` tem 3
    sub-formatos, discriminados por `unk1`/`unk4` do cabecalho da mensagem
    (portado de libxrk/aim_xrk.pyx: struct `cmsg_hdr` ~L280 e o `elif typ ==
    ord_op_c` do loop principal ~L424, unico jeito de saber o tamanho certo
    pra pular sem adivinhar).

    Layout comum aos 3 (offsets relativos a `off`, onde `off` e o '('):
    +0 '(' +1 'c' +2 unk1(u8) +3 channel(u16) +5 unk3(u8) +6 unk4(u8). O
    `unk3` e sempre `0x84` no libxrk (`raise ValueError` de lá se nao bate):
    tratamos violar isso como formato desconhecido, mesma regra do kind fora
    da tabela. Dali em diante o tamanho diverge por sub-formato:

    - V1 (unk1=0, unk4=6): cabecalho de 11 bytes (soma mais o timecode i32
      em +7..+11), canal em `channel >> 3` (bits baixos sempre 4, outro
      contrato de sanidade do libxrk), payload do MESMO tamanho que um `S`
      desse canal (`CHS.bytes_amostra`) - literalmente o mesmo fluxo do `S`,
      só que com um cabecalho maior.
    - V2 (unk1=0, unk4=8): 16 bytes fixos (11 de cabecalho + 2 amostras
      fp16 de 2 bytes cada, timecodes derivados do nibble baixo de
      `channel`).
    - V3 (unk1=1, unk4=2): 10 bytes fixos, sem campo timecode proprio (o
      timecode e sintetizado a partir do V2 mais recente do mesmo par de
      `channel`, regra que só faz sentido depois de resolvida a etapa
      seguinte).

    V2 e V3 NAO decodificam amostra aqui (piso aceito pelo escopo desta
    correcao, nao o ideal): mapear `channel` (um `channel_field` cru) pro
    indice de canal real do `CHS` exige reconciliar o CONJUNTO INTEIRO de
    `channel_field` observado no arquivo inteiro contra o `CHS` - o proprio
    libxrk so resolve isso DEPOIS de varrer o arquivo todo (bloco de
    `expansion_channel_map` no fim do parse), nunca durante o loop
    principal. Nosso walker e uma passada unica e streaming: dar essa
    resolucao exigiria uma segunda passada que ele nao tem hoje. V1 nao tem
    esse problema (o indice de canal sai direto do proprio registro, sem
    reconciliacao), mas decodificar SO V1 e nao V2/V3 adicionaria uma
    amostra por canal que a etapa 3 (`ler()`) ainda nao tem como consumir
    (nao ha `cid` desse namespace na tabela de canais que ela monta); por
    isso o inventario so CONTA a ocorrencia (ver `bruto`), pros 3
    sub-formatos, e `ler()` so pula.

    Devolve `(offset_do_fecho, "v1"|"v2"|"v3")`, ou `None` quando o registro
    nao valida (bytes insuficientes, `unk3` errado, ou combinacao
    `unk1`/`unk4` fora das 3 conhecidas) - o chamador trata `None` como o
    kind desconhecido generico, um `break`.
    """
    if off + 7 > tamanho_total:
        return None
    unk1 = dados[off + 2]
    channel_field = struct.unpack_from("<H", dados, off + 3)[0]
    unk3 = dados[off + 5]
    unk4 = dados[off + 6]
    if unk3 != 0x84:
        return None
    if unk1 == 0 and unk4 == 6:
        if (channel_field & 7) != 4:
            return None
        canal = canais.get(channel_field >> 3)
        if canal is None:
            return None
        return off + 11 + canal.bytes_amostra, "v1"
    if unk1 == 0 and unk4 == 8:
        return off + 15, "v2"
    if unk1 == 1 and unk4 == 2:
        return off + 9, "v3"
    return None


def _acumula_lap(
    corpo: bytes,
    lap_nums: list[int],
    lap_starts_ms: list[int],
    lap_ends_ms: list[int],
) -> str:
    """Decodifica UM chunk LAP (corpo de 20 OU 32 bytes) e acumula em
    `lap_nums`/`lap_starts_ms`/`lap_ends_ms`.

    `segment`/`lap`/`duration_ms` ficam nos MESMOS 3 primeiros campos nos
    dois tamanhos (portado de libxrk/aim_xrk.pyx `_get_laps` ~L1311: o chunk
    de 20 que ja liamos so extraia `fim_ms`/`duracao_ms`, cegos pra sector
    time e pra numeracao de volta). MAS o `end_time_ms` cumulativo NAO fica
    no mesmo offset nos dois tamanhos - essa e a parte em que a referencia
    (lida direto da fonte) nao bate com o arquivo real, ver o paragrafo
    "DIVERGENCIA DA REFERENCIA" abaixo.

    Layout de 20 bytes (offsets relativos ao inicio do corpo, validado em
    29/08 contra 4 arquivos reais): +0 pula 1, +1 `segment` (u8), +2 `lap`
    (u16), +4 `duration_ms` (u32), +8 pula 8, +16 `end_time_ms` (u32).

    Layout de 32 bytes (mesmos +0/+1/+2/+4 de segment/lap/duration_ms; os 12
    bytes extras REORGANIZAM o resto do corpo, nao so apendam): +12 melhor
    volta ate agora em ms, sentinela `0x7fffffff` quando ainda nao ha
    nenhuma (u32, nao usado aqui), +16 um valor por volta proximo da propria
    `duration_ms` (nao e o cumulativo, tambem nao usado aqui), +28
    `end_time_ms` cumulativo (u32) - ESTE e o campo que teoricamente caiu
    no offset +16 pro leitor de 20 bytes.

    DIVERGENCIA DA REFERENCIA: o texto da tarefa (e a propria
    `_get_laps` lida ao pe da letra) diz que os primeiros 20 bytes do chunk
    de 32 tem o MESMO layout do chunk de 20, ou seja, `end_time_ms` em +16.
    Validado em 29/08 contra os 39 arquivos do acervo com >=2 chunks LAP de
    32 bytes em sequencia normal (`lap` = anterior+1): a invariante
    `fim_n - fim_{n-1} == duracao_n` (a MESMA que valida o layout de 20)
    bate 39/39 com `fim_ms` em +28 e ZERO/39 com `fim_ms` em +16 (+16 fica
    proximo mas nunca exato de `duration_ms` da MESMA volta, e um campo
    completamente diferente). Causa provavel: a propria `_get_laps` nunca
    roda pra corpo de 32 bytes nesta versao do libxrk (0.13) - o handler
    ANTERIOR no loop principal (`elif tok == _tokdec('LAP')`, ~L690) faz
    `struct.unpack('4xI8xI', data)`, que EXIGE um buffer de EXATAMENTE 20
    bytes; pra um corpo de 32 bytes isso sempre levanta `struct.error`,
    capturado pelo `except` generico do loop (recuperacao "badbytes"), e o
    chunk nunca chega a virar `Message` nem a ser visto por `_get_laps`. O
    texto de `_get_laps` pro layout de 32 bytes e codigo morto nesta versao
    instalada: nunca foi exercitado contra um arquivo real, e diverge do
    formato real. Detalhe tecnico completo no relato da tarefa.

    Regras de sequencia (idem `_get_laps`, SEM a normalizacao de
    `time_offset` da referencia: o `time_offset` dela desloca TODOS os
    timecodes exportados, inclusive os de amostra, pra por o inicio da
    primeira volta em zero; o resto deste leitor nunca aplica esse
    deslocamento em `ts_ms`, entao aplicar so aqui desalinharia
    `lap_beacons_ms` do proprio `t_s` que `ler()` produz, e e contra esse
    `t_s` que `corte_voltas.py` casa os beacons. Ver relato da tarefa.):

    - `segment != 0` e tempo de SETOR, nao fecha volta: ignora (nunca visto
      no acervo, mas o campo existe no formato e o contrato pede a regra).
    - Mesmo `lap` do ultimo aceito: chunk duplicado, ignora (nao conta 2x).
    - `lap` = ultimo + 1: sequencia normal, aceita.
    - `lap` = ultimo + 2: um chunk sumiu no meio (nao chegou a nos, ou o
      pulo do walker perdeu um). A referencia INFERE a volta que faltou:
      fim dela e o INICIO da volta atual (`fim_ms - duration_ms` da atual),
      inicio dela e o fim da anterior (o beacon nunca fica vazado, so o
      numero da volta e formal, nao usado no corte).
    - Qualquer outro salto (incluindo numeracao pra tras, ex. volta 2
      seguida de volta 1, visto num arquivo do acervo): a referencia
      levanta excecao e aborta o arquivo inteiro. Este leitor nunca crasha
      por anomalia de um unico registro (regra dura do projeto): descarta
      SO esse chunk (devolve `False`) e o chamador conta em `bruto`, sem
      perder o resto da leitura.

    Devolve o motivo: `"aceito"` (sequencia normal), `"inferido"` (aceitou a
    atual E inferiu uma volta perdida antes dela), `"setor"` (`segment !=
    0`), `"duplicata"` (mesmo `lap` do ultimo aceito) ou `"salto"` (gap
    grande demais pra inferir com seguranca, chunk descartado). So os 3
    ultimos NAO alteram os acumuladores.
    """
    if len(corpo) == 20:
        segment, lap, duration_ms, fim_ms = struct.unpack_from("<xBHI8xI", corpo, 0)
    elif len(corpo) == 32:
        segment, lap, duration_ms = struct.unpack_from("<xBHI", corpo, 0)
        fim_ms = struct.unpack_from("<I", corpo, 28)[0]
    else:
        return "tamanho_invalido"
    if segment:
        return "setor"
    motivo = "aceito"
    if not lap_nums:
        pass
    elif lap_nums[-1] == lap:
        return "duplicata"
    elif lap_nums[-1] + 1 == lap:
        pass
    elif lap_nums[-1] + 2 == lap:
        lap_nums.append(lap - 1)
        lap_starts_ms.append(lap_ends_ms[-1])
        lap_ends_ms.append(fim_ms - duration_ms)
        motivo = "inferido"
    else:
        return "salto"
    lap_nums.append(lap)
    lap_starts_ms.append(fim_ms - duration_ms)
    lap_ends_ms.append(fim_ms)
    return motivo


_LIMITE_RESYNC = 8192


def _resincroniza_em_chunk(dados: bytes, off: int, tamanho_total: int) -> int | None:
    """Quando nem chunk `<h` nem registro `(` reconhecido comeca em `off`,
    procura o proximo `<h` VALIDO (cabecalho+fecho batendo, ver
    `_cabecalho_chunk`) dentro de `_LIMITE_RESYNC` bytes a frente e retoma
    dali, em vez de desistir do resto do arquivo inteiro.

    Existe pra um caso medido no maior arquivo do acervo (LimeRock, 36 MB):
    uma sequencia de ~17 bytes solta no meio do stream de amostra, repetida
    centenas de vezes ao longo do arquivo, que NAO e chunk nem registro
    S/G/M/c (o primeiro byte nem e `(`) - o proprio libxrk tambem nao
    reconhece essa sequencia (conferido: o dispatch dele so aceita op comecando
    com `(`, isso comeca com outro byte), e so segue em frente porque o loop
    principal DELE tem recuperacao "badbytes": qualquer excecao no parse
    pula 1 byte e tenta de novo, token a token. Isso aqui e a MESMA ideia,
    so que como fallback pontual (nao token a token: so quando o dispatch
    normal falha em bater em `off`) e restrito a fronteira de CHUNK: um
    registro `(` teria que revalidar canal/grupo/tamanho pra nao arriscar
    falso positivo (uma sequencia de bytes aleatoria comecando com `(` e um
    kind conhecido tem chance nao-trivial de "validar" por acaso; um chunk
    exige a tag EXATA repetida no fecho, risco bem menor), e o ganho
    marginal de tentar isso tambem nao valeu a complexidade pro caso medido
    (LimeRock resincroniza inteiro so com chunk).

    Devolve o offset do `<h` valido encontrado, ou `None` se nada validou
    dentro do limite (o chamador declara parcial e para, como sempre).
    """
    fim_busca = min(off + _LIMITE_RESYNC, tamanho_total)
    candidato = dados.find(b"<h", off + 1, fim_busca)
    while candidato != -1:
        if _cabecalho_chunk(dados, candidato) is not None:
            return candidato
        candidato = dados.find(b"<h", candidato + 1, fim_busca)
    return None


def _descomprime_se_xrz(dados: bytes, caminho: Path) -> bytes:
    """`.xrz` e o mesmo stream XRK embrulhado em zlib. Descomprimir aqui deixa
    o resto do leitor cego pra diferenca, que e o que se quer: um formato, dois
    envelopes."""
    if dados[:1] == b"\x78" and dados[1:2] in (b"\x01", b"\x5e", b"\x9c", b"\xda"):
        import zlib

        try:
            return zlib.decompress(dados)
        except zlib.error as exc:
            raise ErroDeLeitura(f"{caminho}: zlib corrompido: {exc}") from exc
    return dados


# ---------------------------------------------------------------------------
# GPS: o chunk `<hGPS` carrega, por ocorrencia, um registro de 56 bytes =
# timecode int32 do logger (ms) + payload u-blox NAV-SOL de 52 bytes (posicao
# e velocidade ECEF em centimetros, precisao, fix, satelites). O layout foi
# conferido campo a campo contra libxrk/aim_xrk.pyx `_decode_gps` (oraculo de
# auditoria, decisao do Lucas: a lib NAO roda em runtime, so serviu de
# referencia de leitura) e validado no acervo em 29/08 (kart do Guara
# decodifica pra lat -15.82570, lon -47.97108, que e o kartodromo do Guara em
# Brasilia). Daqui saem 12 canais sintetizados com os MESMOS nomes que o
# ecossistema AiM usa ("GPS Latitude", "GPS_LateralAcc", ...), porque e esse
# o vocabulario que o perfil `aim_xrk` do aliases.yaml ja mapeia pro canonico
# (`gps_lat`/`gps_lon`/`speed`/...) - e o canonico e o que destrava o corte
# de volta por GPS nos arquivos sem beacon.
# ---------------------------------------------------------------------------

_GPS_CORPO_BYTES = 56

# (nome do canal sintetizado, unidade declarada). Nomes e unidades identicos
# aos do oraculo pra auditoria 1:1; "-" e adimensional (contagem/indice).
_CANAIS_GPS: tuple[tuple[str, str], ...] = (
    ("GPS Speed", "m/s"),
    ("GPS Latitude", "deg"),
    ("GPS Longitude", "deg"),
    ("GPS Altitude", "m"),
    ("GPS_Satellites", "-"),
    ("GPS_Fix", "-"),
    ("GPS_pDOP", "-"),
    ("GPS_Position_Accuracy", "m"),
    ("GPS_Velocity_Accuracy", "m/s"),
    ("GPS_InlineAcc", "g"),
    ("GPS_LateralAcc", "g"),
    ("GPS_Yaw_Rate", "deg/s"),
)


def _desembaraca_timecodes_gps(tc: np.ndarray) -> np.ndarray:
    """Conserta o bug de firmware que corrompe os 16 bits ALTOS do timecode
    GPS (medido em 12 dos 113 arquivos com GPS do acervo, 29/08): a serie
    deixa de ser monotonica com saltos de ~65536 ms. O conserto e phase
    unwrap: cada delta e dobrado pro intervalo [-32768, +32767] usando so os
    16 bits baixos (que o bug nao toca), e a serie e reconstruida por soma
    acumulada a partir do primeiro valor. Mesmo algoritmo do oraculo
    (libxrk/aim_xrk.pyx), que documenta o bug como "certain old MXP firmware
    would periodically butcher the upper 16-bits". Serie ja monotonica passa
    reta, sem custo."""
    if tc.size >= 2 and bool(np.any(tc[1:] < tc[:-1])):
        deltas = ((np.diff(tc) & 0xFFFF) ^ 0x8000) - 0x8000
        tc = tc[0] + np.concatenate(([0], np.cumsum(deltas)))
    return tc


def _timecodes_gps(dados: bytes, offsets: list[int]) -> np.ndarray:
    """So os timecodes (int32 no offset 0 de cada corpo GPS), ja
    desembaracados. E o que `inspecionar()` precisa pra declarar a taxa sem
    pagar o decode completo."""
    base = np.frombuffer(dados, dtype=np.uint8)
    offs = np.asarray(offsets, dtype=np.int64)
    idx = offs[:, None] + np.arange(4, dtype=np.int64)
    tc = base[idx].reshape(-1).copy().view("<i4").astype(np.int64)
    return _desembaraca_timecodes_gps(tc)


def _taxa_gps(tc: np.ndarray) -> float | None:
    """Taxa nominal do GPS pela MEDIANA dos deltas (o formato nao declara a
    taxa em campo nenhum). Mediana e nao media porque buraco de sinal (delta
    gigante) e registro repetido (delta zero) nao podem puxar o numero; os
    deltas fora de (0, 10s) ficam de fora do voto. Acervo medido em 29/08:
    so aparecem 4, 10 e 25 Hz, e a mediana devolve exatamente esses."""
    if tc.size < 2:
        return None
    d = np.diff(tc)
    d = d[(d > 0) & (d < 10_000)]
    if d.size == 0:
        return None
    mediana = float(np.median(d))
    if mediana <= 0:
        return None
    return 1000.0 / mediana


def _ecef2lla(
    x_m: np.ndarray, y_m: np.ndarray, z_m: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ECEF (metros) para latitude/longitude (graus) e altitude (metros),
    metodo fechado de H. Vermeille (2003/2004), elipsoide WGS-84. Portado de
    libxrk/gps.py `ecef2lla_vermeille2003` (MIT, Scott Smith) de proposito
    SEM mudar formula nenhuma: a auditoria compara nosso valor com o do
    oraculo e qualquer diferenca tem que ser bug, nunca metodo. Registro sem
    fix vem com ECEF zerado e sai como nan aqui (0/0 no ultimo passo), o que
    e o comportamento honesto: nao existe posicao naquele instante, e nan
    nunca cruza o gate do corte por GPS."""
    a = 6378137.0
    e = 8.181919084261345e-2
    with np.errstate(divide="ignore", invalid="ignore"):
        p = (x_m * x_m + y_m * y_m) * (1 / (a * a))
        q = ((1 - e * e) / (a * a)) * z_m * z_m
        r = (p + q - e**4) * (1 / 6)
        s = (e**4 / 4) * p * q / (r**3)
        t = np.cbrt(1 + s + np.sqrt(s * (2 + s)))
        u = r * (1 + t + 1 / t)
        v = np.sqrt(u * u + e**4 * q)
        u = u + v
        w = (e**2 / 2) * (u - q) / v
        k = np.sqrt(u + w * w) - w
        d = k * np.sqrt(x_m * x_m + y_m * y_m) / (k + e**2)
        rt = np.sqrt(d * d + z_m * z_m)
        lat = (180 / np.pi) * 2 * np.arctan2(z_m, d + rt)
        lon = (180 / np.pi) * np.arctan2(y_m, x_m)
        alt = (k + e**2 - 1) / k * rt
    return lat, lon, alt


def _decodifica_chunks_gps(
    dados: bytes, offsets: list[int]
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Decodifica TODOS os corpos GPS de uma vez (mesmo truque vetorizado de
    `_decodifica_escalares_em_bloco`: fancy-index sobre a visao uint8 do arquivo,
    um gather de n x 56 bytes, zero struct.unpack no loop).

    Devolve (timecodes_ms ja desembaracados, {nome do canal: float64}) com
    os 12 canais de `_CANAIS_GPS`. Os 8 primeiros sao leitura direta do
    NAV-SOL (posicao via `_ecef2lla`, velocidade = norma do vetor ECEF); os
    4 derivados (aceleracao inline/lateral, yaw rate) usam as MESMAS
    formulas do oraculo, derivada discreta sobre o proprio eixo de tempo do
    GPS, pra auditoria fechar em zero."""
    base = np.frombuffer(dados, dtype=np.uint8)
    offs = np.asarray(offsets, dtype=np.int64)
    bloco = base[offs[:, None] + np.arange(_GPS_CORPO_BYTES, dtype=np.int64)]

    def _i32(o: int) -> np.ndarray:
        return bloco[:, o : o + 4].copy().view("<i4").reshape(-1)

    def _u32(o: int) -> np.ndarray:
        return bloco[:, o : o + 4].copy().view("<u4").reshape(-1)

    def _u16(o: int) -> np.ndarray:
        return bloco[:, o : o + 2].copy().view("<u2").reshape(-1)

    tc = _desembaraca_timecodes_gps(_i32(0).astype(np.int64))

    x_m = _i32(16).astype(np.float64) / 100.0
    y_m = _i32(20).astype(np.float64) / 100.0
    z_m = _i32(24).astype(np.float64) / 100.0
    lat, lon, alt = _ecef2lla(x_m, y_m, z_m)

    vx = _i32(32).astype(np.float64)
    vy = _i32(36).astype(np.float64)
    vz = _i32(40).astype(np.float64)
    velocidade_ms = np.sqrt(vx * vx + vy * vy + vz * vz) / 100.0

    # Rumo (heading) a partir da velocidade ECEF projetada no plano local
    # ENU (leste/norte), mesma transformacao do oraculo
    # (libxrk/gps.py `ecef_velocity_to_enu`).
    lat_rad = lat * (np.pi / 180)
    lon_rad = lon * (np.pi / 180)
    sin_lat, cos_lat = np.sin(lat_rad), np.cos(lat_rad)
    sin_lon, cos_lon = np.sin(lon_rad), np.cos(lon_rad)
    v_leste = -sin_lon * vx + cos_lon * vy
    v_norte = -sin_lat * cos_lon * vx - sin_lat * sin_lon * vy + cos_lat * vz
    rumo_deg = np.arctan2(v_leste, v_norte) * (180 / np.pi)

    dt_s = np.diff(tc) / 1000.0
    dt_s = np.where(dt_s > 0, dt_s, np.inf)

    dv = np.diff(velocidade_ms)
    acc_inline_g = np.concatenate(([0.0], dv / dt_s)) / 9.81

    d_rumo = np.diff(rumo_deg)
    d_rumo = np.where(d_rumo > 180, d_rumo - 360, d_rumo)
    d_rumo = np.where(d_rumo < -180, d_rumo + 360, d_rumo)
    yaw_deg_s = np.concatenate(([0.0], d_rumo / dt_s))

    acc_lateral_g = velocidade_ms * yaw_deg_s * (np.pi / 180) / 9.81

    colunas: dict[str, np.ndarray] = {
        "GPS Speed": velocidade_ms,
        "GPS Latitude": lat,
        "GPS Longitude": lon,
        "GPS Altitude": alt,
        "GPS_Satellites": bloco[:, 51].astype(np.float64),
        "GPS_Fix": bloco[:, 14].astype(np.float64),
        "GPS_pDOP": _u16(48).astype(np.float64) / 100.0,
        "GPS_Position_Accuracy": _u32(28).astype(np.float64) / 100.0,
        "GPS_Velocity_Accuracy": _u32(44).astype(np.float64) / 100.0,
        "GPS_InlineAcc": acc_inline_g,
        "GPS_LateralAcc": acc_lateral_g,
        "GPS_Yaw_Rate": yaw_deg_s,
    }
    return tc, colunas


def _lotes_gps(
    dados: bytes, offsets: list[int], canais: dict[int, _CanalTmp]
) -> Iterator[Lote]:
    """Emite os canais GPS sintetizados como serie propria (`serie="gps"`).

    Serie PROPRIA e nao mais colunas num grupo existente porque o GPS tem
    relogio proprio: os timecodes dele nao coincidem com os de nenhum grupo
    CHS, e em 23 dos 113 arquivos com GPS do acervo (29/08) a TAXA coincide
    com a de um grupo CHS (25 Hz e comum aos dois) - sem o rotulo `serie` os
    dois lotes disputariam o mesmo escritor Parquet e a escrita quebrava no
    esquema. Canal CHS que ja use um dos 12 nomes sintetizados vence e o
    sintetizado daquele nome nao e emitido (zero ocorrencias no acervo, mas
    a regra fica escrita: nome do fabricante e do fabricante)."""
    if len(offsets) < 2:
        return
    nomes_chs = {
        c.nome_longo or c.nome_curto or f"canal_{cid}" for cid, c in canais.items()
    }
    tc, colunas = _decodifica_chunks_gps(dados, offsets)
    taxa = _taxa_gps(tc)
    if taxa is None:
        return
    manter = [
        (nome, colunas[nome]) for nome, _unidade in _CANAIS_GPS if nome not in nomes_chs
    ]
    if not manter:
        return
    t_s = tc.astype(np.float64) / 1000.0
    n = t_s.shape[0]
    for ini in range(0, n, _LINHAS_POR_LOTE):
        fim = min(ini + _LINHAS_POR_LOTE, n)
        arrays = [pa.array(t_s[ini:fim], type=pa.float64())]
        nomes = ["t_s"]
        for nome, valores in manter:
            arrays.append(pa.array(valores[ini:fim], type=pa.float64()))
            nomes.append(nome)
        yield Lote(
            frequencia_hz=taxa,
            tabela=pa.RecordBatch.from_arrays(arrays, names=nomes),
            serie="gps",
        )


def _inspecionar_bytes(dados: bytes, nome_arquivo: str) -> Cabecalho:
    canais: dict[int, _CanalTmp] = {}
    grupos: dict[int, list[int]] = {}
    contagem_amostras: dict[int, int] = {}
    bruto: dict[str, str] = {}
    n_gps = 0
    # Offsets do corpo de cada chunk GPS de 56 bytes (ver bloco GPS acima):
    # decodificados no fim, de uma vez, pra declarar taxa e canais
    # sintetizados no inventario. Corpo de tamanho errado nao entra (contado
    # a parte): payload NAV-SOL e de tamanho fixo, corpo diferente e outro
    # dialeto que ninguem mediu.
    gps_offsets: list[int] = []
    n_gps_invalidos = 0
    n_lap = 0
    # Estado sequencial pra montar os beacons de volta a partir dos chunks
    # LAP (20 OU 32 bytes, mesmo layout nos primeiros 20, ver
    # `_acumula_lap`). Decodificado porque o proprio arquivo carrega os
    # beacons de volta e nos jogavamos fora: um .xrk de kart enviado sozinho
    # tem tudo pra cortar volta e saia "sem canal de volta nem ldx".
    lap_nums: list[int] = []
    lap_starts_ms: list[int] = []
    lap_ends_ms: list[int] = []
    n_lap_saltos_grandes = 0
    n_cal = 0
    ts_max_ms = 0
    viu_registro = False
    # Ocorrencias de kind `c` por sub-formato (ver `_tamanho_registro_c`):
    # nao decodificado, so contado, pra ficar auditavel sem inflar
    # `contagem_amostras` de canal nenhum.
    contagem_c: dict[str, int] = {}
    # Resincronizacoes (ver `_resincroniza_em_chunk`): quantas vezes o walker
    # pulou bytes nao reconhecidos pra retomar num chunk valido, e quantos
    # bytes no total ficaram sem interpretacao por causa disso.
    n_resyncs = 0
    bytes_ruido = 0

    off = 0
    tamanho_total = len(dados)
    while off < tamanho_total:
        if dados[off : off + 2] == b"<h":
            span = _cabecalho_chunk(dados, off)
            if span is None:
                break
            tag, corpo_ini, corpo_fim, prox = span
            prefixo = tag[:3]
            if prefixo == b"CNF":
                _escaneia_container(dados, corpo_ini, corpo_fim, canais, grupos)
            elif prefixo == b"CHS":
                par = _parse_chs(dados[corpo_ini:corpo_fim])
                if par is not None:
                    canais[par[0]] = par[1]
            elif prefixo == b"GRP":
                par_g = _parse_grp(dados[corpo_ini:corpo_fim])
                if par_g is not None:
                    grupos[par_g[0]] = par_g[1]
            elif prefixo in _TAGS_TEXTO:
                texto = _texto(dados[corpo_ini:corpo_fim])
                if texto:
                    bruto[_TAGS_TEXTO[prefixo]] = texto
            elif prefixo == b"LAP":
                n_lap += 1
                motivo_lap = _acumula_lap(
                    dados[corpo_ini:corpo_fim], lap_nums, lap_starts_ms, lap_ends_ms
                )
                if motivo_lap == "salto":
                    n_lap_saltos_grandes += 1
            elif prefixo == b"GPS":
                n_gps += 1
                if corpo_fim - corpo_ini == _GPS_CORPO_BYTES:
                    gps_offsets.append(corpo_ini)
                else:
                    n_gps_invalidos += 1
            elif prefixo == b"CAL":
                # Calibracao analogica: presente no arquivo, nao decodificada
                # aqui (ver docstring do modulo). So contamos a ocorrencia.
                n_cal += 1
            # Qualquer outra tag conhecida ou desconhecida (VTY, NDV, SRC,
            # ENF, RACM, HWNF, VET, ODO, ...) e apenas pulada: o tamanho
            # declarado no chunk ja diz onde ela termina.
            off = prox
            continue

        if dados[off : off + 1] == b"(":
            if off + 8 > tamanho_total:
                break
            kind = dados[off + 1 : off + 2]
            ts_ms = struct.unpack_from("<I", dados, off + 2)[0]
            cid = struct.unpack_from("<H", dados, off + 6)[0]
            if kind == b"S":
                canal = canais.get(cid)
                if canal is None:
                    break
                fim_payload = off + 8 + canal.bytes_amostra
            elif kind == b"G":
                membros = grupos.get(cid)
                if membros is None:
                    break
                bytes_membros = []
                for membro in membros:
                    canal_membro = canais.get(membro)
                    if canal_membro is None:
                        bytes_membros = None
                        break
                    bytes_membros.append(canal_membro.bytes_amostra)
                if bytes_membros is None:
                    break
                fim_payload = off + 8 + sum(bytes_membros)
            elif kind == b"M":
                if off + 10 > tamanho_total:
                    break
                n = struct.unpack_from("<H", dados, off + 8)[0]
                fim_payload = off + 10 + 2 * n
            elif kind == b"c":
                # Canal expandido (V1/V2/V3), ver `_tamanho_registro_c`. Os
                # campos `ts_ms`/`cid` acima NAO valem pra esse kind (o
                # cabecalho de `c` tem outro shape); ignorados aqui de
                # proposito, o offset do fecho ja sai calculado certo.
                resultado_c = _tamanho_registro_c(dados, off, tamanho_total, canais)
                if resultado_c is None:
                    break
                fim_payload, subtipo_c = resultado_c
            else:
                # Kind nao mapeado: sem tabela de tamanho, parar aqui e
                # declarar parcial e o unico jeito honesto (regra dura do
                # projeto, nasceu do B2).
                break

            if (
                fim_payload + 1 > tamanho_total
                or dados[fim_payload : fim_payload + 1] != b")"
            ):
                break

            if kind == b"c":
                # Nao decodificado aqui (ver docstring de
                # `_tamanho_registro_c`): so conta em `bruto`, sem entrar em
                # `contagem_amostras` (nao e amostra de canal nenhum na
                # tabela que `canais` monta) nem em `ts_max_ms` (o timecode
                # de V3 nem existe no registro, e o de V1/V2 nao foi lido).
                contagem_c[subtipo_c] = contagem_c.get(subtipo_c, 0) + 1
                off = fim_payload + 1
                continue

            viu_registro = True
            ts_max_ms = max(ts_max_ms, ts_ms)
            if kind == b"S":
                contagem_amostras[cid] = contagem_amostras.get(cid, 0) + 1
            elif kind == b"G":
                for membro in grupos[cid]:
                    contagem_amostras[membro] = contagem_amostras.get(membro, 0) + 1
            else:  # M
                contagem_amostras[cid] = contagem_amostras.get(cid, 0) + n
            off = fim_payload + 1
            continue

        # Nem chunk nem registro reconhecido: byte que o formato-fabricante
        # nao documenta (visto em rajadas soltas no meio do stream de
        # amostra do LimeRock, 36 MB, sem relacao com kind `c` - so o `c`
        # sozinho NAO destrava esse arquivo, medido em 29/08 depois de
        # portar V1/V2/V3 e o offset_parada continuar o MESMO). Antes de
        # desistir do resto do arquivo inteiro, tenta resincronizar no
        # proximo `<h` valido (ver `_resincroniza_em_chunk`); so entao
        # declara parcial.
        resync = _resincroniza_em_chunk(dados, off, tamanho_total)
        if resync is None:
            break
        bytes_ruido += resync - off
        n_resyncs += 1
        off = resync
        continue

    if not canais:
        raise ErroDeLeitura(
            f"{nome_arquivo}: nenhum chunk CHS encontrado ate o offset {off}, "
            "nao ha canal pra inventariar"
        )

    lista_canais = []
    for cid, c in canais.items():
        if c.periodo_us <= 0:
            # Periodo zero/negativo nao vira frequencia: taxa tem que ser
            # positiva (invariante do contrato). Registrado, nao descartado
            # em silencio.
            bruto[f"canal_{cid}_periodo_invalido"] = str(c.periodo_us)
            continue
        # O nome LONGO e o vocabulario que o mapa de canais usa: o perfil
        # `aim_xrk` do aliases.yaml espera `BRAKE_F`, `LAT_ACC`, `EDL8_RPM`,
        # que sao os nomes de +0x20. O curto (+0x18) e abreviacao de display
        # (`R_BP`, `AccY`, `RPM`). Usar o curto derrubava a intersecao com o
        # mapa pra 1 canal em 30. Medido em 29/08 nos 66 arquivos do acervo.
        nome = c.nome_longo or c.nome_curto or f"canal_{cid}"
        lista_canais.append(
            CanalBruto(
                nome_bruto=nome,
                frequencia_hz=1_000_000.0 / c.periodo_us,
                n_amostras=contagem_amostras.get(cid, 0),
            )
        )

    # Canais GPS sintetizados no inventario, com a MESMA regra de emissao de
    # `_lotes_gps` (>= 2 corpos validos, taxa pela mediana, nome do CHS
    # vence): inventario e amostra tem que contar a mesma historia, senao o
    # catalogo promete canal que a serie nao tem.
    nomes_chs_usados = {c.nome_bruto for c in lista_canais}
    taxa_gps: float | None = None
    if len(gps_offsets) >= 2:
        taxa_gps = _taxa_gps(_timecodes_gps(dados, gps_offsets))
    if taxa_gps is not None:
        conflitos_gps = []
        for nome_gps, unidade_gps in _CANAIS_GPS:
            if nome_gps in nomes_chs_usados:
                conflitos_gps.append(nome_gps)
                continue
            lista_canais.append(
                CanalBruto(
                    nome_bruto=nome_gps,
                    frequencia_hz=taxa_gps,
                    n_amostras=len(gps_offsets),
                    unidade_declarada=unidade_gps,
                )
            )
        bruto["gps_taxa_hz"] = f"{taxa_gps:g}"
        if conflitos_gps:
            bruto["gps_canais_em_conflito"] = ",".join(conflitos_gps)
    elif n_gps:
        # Tem chunk GPS mas nao da pra sintetizar canal: motivo declarado,
        # nunca silencio (regra do B2).
        bruto["gps_nao_sintetizado"] = (
            "menos de 2 corpos validos de 56 bytes"
            if len(gps_offsets) < 2
            else "taxa indeterminavel pelos timecodes"
        )
    if n_gps_invalidos:
        bruto["gps_chunks_invalidos"] = str(n_gps_invalidos)

    parcial = off < tamanho_total
    bruto["leitura_parcial"] = "sim" if parcial else "nao"
    if parcial:
        bruto["offset_parada"] = str(off)
        bruto["bytes_sem_cobertura"] = str(tamanho_total - off)
    bruto["n_canais_chs"] = str(len(canais))
    bruto["n_grupos_grp"] = str(len(grupos))
    bruto["gps_amostras"] = str(n_gps)
    bruto["lap_chunks"] = str(n_lap)
    if lap_ends_ms:
        # As PASSAGENS pela linha, em ms: o inicio da primeira volta mais o
        # fim de cada uma. E o mesmo shape que o sidecar .ldx declara, entao
        # o corte trata os dois pelo mesmo caminho. `_acumula_lap` ja acumula
        # em ordem cronologica (estado sequencial por numero de volta), sem
        # precisar reordenar aqui.
        passagens = [lap_starts_ms[0]] + lap_ends_ms
        bruto["lap_beacons_ms"] = ",".join(str(v) for v in passagens)
    if n_lap_saltos_grandes:
        bruto["lap_saltos_grandes"] = str(n_lap_saltos_grandes)
    bruto["cal_chunks"] = str(n_cal)
    if contagem_c:
        bruto["c_registros_v1"] = str(contagem_c.get("v1", 0))
        bruto["c_registros_v2"] = str(contagem_c.get("v2", 0))
        bruto["c_registros_v3"] = str(contagem_c.get("v3", 0))
    if n_resyncs:
        bruto["resyncs"] = str(n_resyncs)
        bruto["resync_bytes_ruido"] = str(bytes_ruido)

    duracao_s = ts_max_ms / 1000.0 if viu_registro else None
    if n_gps and duracao_s:
        # Taxa media do GPS a partir da contagem de chunks e da duracao
        # observada no stream, nao de um campo declarado (o formato nao
        # declara taxa de GPS em lugar nenhum).
        bruto["gps_taxa_hz_estimada"] = f"{n_gps / duracao_s:.2f}"

    capturado_em = None
    data_txt = bruto.get("data_captura")
    hora_txt = bruto.get("hora_captura")
    if data_txt and hora_txt:
        capturado_em = f"{data_txt} {hora_txt}"
    elif data_txt:
        capturado_em = data_txt

    venue = bruto.get("pista_declarada") or None

    return Cabecalho(
        formato_id="aim_xrk",
        leitor_versao=_VERSAO,
        canais=tuple(lista_canais),
        capturado_em=capturado_em,
        duracao_s=duracao_s,
        venue_declarado=venue,
        bruto=bruto,
    )


def _percorre_registros(
    dados: bytes,
    canais: dict[int, _CanalTmp],
    grupos: dict[int, list[int]],
    ao_registro,
    ao_chunk_gps=None,
) -> int:
    """Percurso de chunks + registros, compartilhado pelas duas passadas de
    `ler()`. Mesma logica de `_inspecionar_bytes` (chunk CNF/CHS/GRP
    atualiza `canais`/`grupos` on-the-fly, registro `S`/`G`/`M` calcula o
    tamanho do payload pelos MESMOS canais ja vistos, `c` reconhece e pula
    sem decodificar, kind fora da tabela tenta resincronizar num chunk
    valido antes de desistir - ver `_resincroniza_em_chunk`), pra garantir
    que as duas passadas parem exatamente no mesmo offset que
    `inspecionar()` pararia. `ao_registro` e chamado com `(kind, ts_ms, cid,
    off_payload, tamanho_payload)` pra cada registro valido; `off_payload` e
    o comeco do payload (logo apos o id de 2 bytes).
    """
    off = 0
    tamanho_total = len(dados)
    while off < tamanho_total:
        if dados[off : off + 2] == b"<h":
            span = _cabecalho_chunk(dados, off)
            if span is None:
                break
            tag, corpo_ini, corpo_fim, prox = span
            prefixo = tag[:3]
            if prefixo == b"CNF":
                _escaneia_container(dados, corpo_ini, corpo_fim, canais, grupos)
            elif prefixo == b"CHS":
                par = _parse_chs(dados[corpo_ini:corpo_fim])
                if par is not None:
                    canais[par[0]] = par[1]
            elif prefixo == b"GRP":
                par_g = _parse_grp(dados[corpo_ini:corpo_fim])
                if par_g is not None:
                    grupos[par_g[0]] = par_g[1]
            elif prefixo == b"GPS" and ao_chunk_gps is not None:
                # Mesmo criterio de validade do inventario: corpo de 56
                # bytes entra, outro tamanho e ignorado aqui (o inventario
                # ja conta e declara os invalidos).
                if corpo_fim - corpo_ini == _GPS_CORPO_BYTES:
                    ao_chunk_gps(corpo_ini)
            off = prox
            continue

        if dados[off : off + 1] == b"(":
            if off + 8 > tamanho_total:
                break
            kind = dados[off + 1 : off + 2]
            ts_ms = struct.unpack_from("<I", dados, off + 2)[0]
            cid = struct.unpack_from("<H", dados, off + 6)[0]
            off_payload = off + 8
            if kind == b"S":
                canal = canais.get(cid)
                if canal is None:
                    break
                tamanho_payload = canal.bytes_amostra
            elif kind == b"G":
                membros = grupos.get(cid)
                if membros is None:
                    break
                bytes_membros = []
                incompleto = False
                for membro in membros:
                    canal_membro = canais.get(membro)
                    if canal_membro is None:
                        incompleto = True
                        break
                    bytes_membros.append(canal_membro.bytes_amostra)
                if incompleto:
                    break
                tamanho_payload = sum(bytes_membros)
            elif kind == b"M":
                if off + 10 > tamanho_total:
                    break
                n = struct.unpack_from("<H", dados, off + 8)[0]
                off_payload = off + 10
                tamanho_payload = 2 * n
            elif kind == b"c":
                # Canal expandido (V1/V2/V3): mesma regra do inventario
                # (`_tamanho_registro_c`), so que aqui nunca chama
                # `ao_registro` (nenhum consumidor de `ler()` tem pra onde
                # mandar essa amostra hoje, ver docstring da funcao). O que
                # importa e nao dar `break`: sem isso o resto do arquivo
                # ficava sem cobertura so por causa deste kind.
                resultado_c = _tamanho_registro_c(dados, off, tamanho_total, canais)
                if resultado_c is None:
                    break
                fim_payload, _subtipo_c = resultado_c
                if fim_payload + 1 > tamanho_total or dados[
                    fim_payload : fim_payload + 1
                ] != b")":
                    break
                off = fim_payload + 1
                continue
            else:
                # Kind nao mapeado: mesma regra dura do inventario, parar e
                # declarar parcial, nunca adivinhar tamanho de payload.
                break

            fim_payload = off_payload + tamanho_payload
            fecho_ok = dados[fim_payload : fim_payload + 1] == b")"
            if fim_payload + 1 > tamanho_total or not fecho_ok:
                break

            ao_registro(kind, ts_ms, cid, off_payload, tamanho_payload)
            off = fim_payload + 1
            continue

        # Nem chunk nem registro reconhecido: mesmo fallback do inventario
        # (`_resincroniza_em_chunk`), pra garantir que esta funcao pare no
        # MESMO offset que `_inspecionar_bytes` pararia (contrato do
        # docstring acima).
        resync = _resincroniza_em_chunk(dados, off, tamanho_total)
        if resync is None:
            break
        off = resync
        continue

    return off


# Byte de tipo (corpo[20] do CHS) que muda a INTERPRETACAO dos 2 bytes da
# amostra. Espelho da tabela `_decoders` do libxrk pros tipos de 2 bytes
# medidos no acervo (29/08): 20 = float16 (2.625 canais), 1 = uint16 (599),
# 4 e 11 = int16 (118). Tipo fora da tabela cai em int16, que era o
# comportamento unico ate 29/08: e aposta declarada, nao garantia (o oraculo
# prefere NAO decodificar tipo desconhecido; preferimos o int16 historico
# porque zero arquivo do acervo exercita o caso e mudar isso seria regressao
# cega pra formato que ninguem mediu).
_TIPO_FP16 = 20
_TIPO_U16 = 1


def _decodifica_escalares_em_bloco(
    dados: bytes, offsets: list[int], tipos: list[int]
) -> np.ndarray:
    """Decodifica em UM bloco vetorizado os escalares de 2 bytes que comecam
    em cada offset de `offsets`, em vez de um `struct.unpack_from` por
    amostra (o gargalo medido em 29/08: 2,8 milhoes de chamadas). `tipos[i]`
    e o byte de tipo do canal da amostra `i` (ver tabela acima): float16,
    uint16 ou int16 sobre os MESMOS 2 bytes.

    Os offsets nao sao contiguos entre si (amostra `S`/`G` intercalada com
    chunk e com outro canal no meio), entao nao da pra ler com um unico
    `np.frombuffer` de passo fixo. O truque: enxerga `dados` como array de
    bytes (`uint8`, zero-copy) e faz UM fancy-index vetorizado pegando os 2
    bytes de cada offset de uma vez so, depois reinterpreta cada fatia
    (mascara por tipo) no dtype certo. O numpy processa o indexado em ordem
    (documentado: indice repetido resolve pro ULTIMO valor, testado
    empiricamente), entao a ordem de `offsets` decide o resultado, exatamente
    como uma atribuicao de dict em sequencia decidiria (nao muda semantica
    de sobrescrita).
    """
    if not offsets:
        return np.empty(0, dtype=np.float64)
    base = np.frombuffer(dados, dtype=np.uint8)
    offs = np.asarray(offsets, dtype=np.int64)
    idx = offs[:, None] + np.array([0, 1], dtype=np.int64)
    crus_u16 = base[idx].reshape(-1).view("<u2")
    tipos_arr = np.asarray(tipos, dtype=np.int64)
    saida = np.empty(crus_u16.shape[0], dtype=np.float64)
    m_fp16 = tipos_arr == _TIPO_FP16
    m_u16 = tipos_arr == _TIPO_U16
    m_i16 = ~(m_fp16 | m_u16)
    if m_fp16.any():
        saida[m_fp16] = crus_u16[m_fp16].copy().view("<f2").astype(np.float64)
    if m_u16.any():
        saida[m_u16] = crus_u16[m_u16].astype(np.float64)
    if m_i16.any():
        saida[m_i16] = crus_u16[m_i16].copy().view("<i2").astype(np.float64)
    return saida


def _dtype_da_rajada(tipo: int) -> str:
    """dtype numpy dos 2 bytes de cada amostra de um registro `M`, pelo mesmo
    byte de tipo do canal (a rajada e n escalarezinhos do MESMO canal, entao
    a interpretacao e a mesma do `S`)."""
    if tipo == _TIPO_FP16:
        return "<f2"
    if tipo == _TIPO_U16:
        return "<u2"
    return "<i2"


def _monta_lote_da_janela(
    ts_janela: list[int],
    cid_janela: list[int],
    val_janela: list[float],
    colunas: list[tuple[int, str]],
    cids_ordenados: np.ndarray,
    ordem_cid: np.ndarray,
    hz: float,
) -> Lote:
    """Monta UM `Lote` a partir dos eventos de UMA janela (fatia de eventos
    entre dois cortes de `_LINHAS_POR_LOTE` timestamps distintos).

    Substitui o buffer antigo `dict[ts_ms][cid] = valor` + a list
    comprehension com `.get(cid, nan)` por amostra (5,4 milhoes de
    `dict.get()` medidos em 29/08): aqui e tudo vetorizado com
    `np.unique`/`searchsorted`/atribuicao fancy-index, uma vez por janela em
    vez de uma vez por CELULA da tabela.
    """
    ts_arr = np.asarray(ts_janela, dtype=np.int64)
    cid_arr = np.asarray(cid_janela, dtype=np.int64)
    val_arr = np.asarray(val_janela, dtype=np.float64)

    # Linha = timestamp distinto, ordenado (equivalente ao `sorted()` do
    # buffer antigo). Coluna = indice do canal em `colunas`, achado com
    # searchsorted vetorizado.
    ts_unicos, linha_idx = np.unique(ts_arr, return_inverse=True)
    coluna_idx = ordem_cid[np.searchsorted(cids_ordenados, cid_arr)]

    matriz = np.full((ts_unicos.shape[0], len(colunas)), np.nan, dtype=np.float64)
    # Indice repetido (mesmo ts_ms + mesmo cid duas vezes NA MESMA janela)
    # resolve pro ULTIMO elemento de val_arr: testado empiricamente que a
    # atribuicao fancy-index do numpy com indice repetido grava o ultimo,
    # a mesma semantica de sobrescrita que uma atribuicao de dict em
    # sequencia teria.
    matriz[linha_idx, coluna_idx] = val_arr

    t_s = ts_unicos.astype(np.float64) / 1000.0
    arrays = [pa.array(t_s, type=pa.float64())]
    nomes = ["t_s"]
    for j, (_cid, nome) in enumerate(colunas):
        arrays.append(pa.array(matriz[:, j], type=pa.float64()))
        nomes.append(nome)
    tabela = pa.RecordBatch.from_arrays(arrays, names=nomes)
    return Lote(frequencia_hz=hz, tabela=tabela)


def _ler_bytes_duas_passadas(dados: bytes, nome_arquivo: str) -> Iterator[Lote]:
    """Algoritmo de DUAS passadas (o que existia antes de 29/08, preservado
    aqui so como saida de emergencia de `_ler_bytes`, chamado quando a
    passada unica detecta que a propria aposta furou pra este arquivo
    especifico - ver comentario em `_ler_bytes`). Nunca exercitado pelo
    acervo real na varredura de 29/08 (116 arquivos, 0 ocorrencias), mas
    "nunca medido" nao e "impossivel" pelo formato, entao o caminho de
    escape fica correto por construcao em vez de removido.

    Passada 1 (`_prepara_schema`, local): descobre TODOS os canais/grupos e
    quais aparecem em pelo menos um `M`, ate o offset onde a leitura pararia
    (schema por taxa so fica estavel depois disso). Passada 2 (o corpo desta
    funcao): repete o percurso, agora decodificando cada amostra pro slot
    certo. As duas usam `_percorre_registros`, entao param no MESMO offset
    que `inspecionar()` pararia.
    """

    def _prepara_schema(
        dados: bytes,
    ) -> tuple[dict[int, _CanalTmp], dict[int, list[int]], set[int]]:
        canais: dict[int, _CanalTmp] = {}
        grupos: dict[int, list[int]] = {}
        canais_via_m: set[int] = set()

        def _ao_registro(
            kind: bytes, ts_ms: int, cid: int, off_payload: int, tam: int
        ) -> None:
            if kind == b"M":
                canais_via_m.add(cid)

        _percorre_registros(dados, canais, grupos, _ao_registro)
        return canais, grupos, canais_via_m

    canais, grupos, canais_via_m = _prepara_schema(dados)
    if not canais:
        raise ErroDeLeitura(
            f"{nome_arquivo}: nenhum chunk CHS encontrado, nao ha canal pra ler"
        )

    def _decodificavel(cid: int, canal: _CanalTmp) -> bool:
        return canal.bytes_amostra == 2 or cid in canais_via_m

    por_periodo: dict[int, list[tuple[int, str]]] = {}
    for cid, canal in canais.items():
        if canal.periodo_us <= 0 or not _decodificavel(cid, canal):
            continue
        nome = canal.nome_longo or canal.nome_curto or f"canal_{cid}"
        por_periodo.setdefault(canal.periodo_us, []).append((cid, nome))

    if not por_periodo:
        raise ErroDeLeitura(
            f"{nome_arquivo}: nenhum canal decodificavel (int16 ou rajada M), "
            "nada pra ler"
        )

    colunas_por_periodo: dict[int, list[tuple[int, str]]] = {}
    for periodo_us, entradas in por_periodo.items():
        entradas.sort(key=lambda par: par[1])
        vistos: dict[str, int] = {}
        colunas: list[tuple[int, str]] = []
        for cid, nome in entradas:
            n = vistos.get(nome, 0)
            vistos[nome] = n + 1
            nome_final = nome if n == 0 else f"{nome}#{cid}"
            colunas.append((cid, nome_final))
        colunas_por_periodo[periodo_us] = colunas

    ev_ts: dict[int, list[int]] = {p: [] for p in colunas_por_periodo}
    ev_cid: dict[int, list[int]] = {p: [] for p in colunas_por_periodo}
    ev_val: dict[int, list[float | None]] = {p: [] for p in colunas_por_periodo}

    pendentes_periodo: list[int] = []
    pendentes_pos: list[int] = []
    pendentes_off: list[int] = []
    pendentes_tipo: list[int] = []

    def _registra_pendente(
        periodo_us: int, ts_ms: int, cid: int, off: int, tipo: int
    ) -> None:
        lista_ts = ev_ts[periodo_us]
        lista_ts.append(ts_ms)
        ev_cid[periodo_us].append(cid)
        ev_val[periodo_us].append(None)
        pendentes_periodo.append(periodo_us)
        pendentes_pos.append(len(lista_ts) - 1)
        pendentes_off.append(off)
        pendentes_tipo.append(tipo)

    def _ao_registro(
        kind: bytes, ts_ms: int, cid: int, off_payload: int, tam: int
    ) -> None:
        if kind == b"S":
            canal = canais.get(cid)
            if canal is None or not _decodificavel(cid, canal):
                return
            if canal.periodo_us not in ev_ts:
                return
            _registra_pendente(canal.periodo_us, ts_ms, cid, off_payload, canal.tipo)
        elif kind == b"G":
            offset_membro = off_payload
            for membro in grupos.get(cid, []):
                canal_membro = canais.get(membro)
                if canal_membro is None:
                    break
                if _decodificavel(membro, canal_membro) and canal_membro.periodo_us in ev_ts:
                    _registra_pendente(
                        canal_membro.periodo_us,
                        ts_ms,
                        membro,
                        offset_membro,
                        canal_membro.tipo,
                    )
                offset_membro += canal_membro.bytes_amostra
        elif kind == b"M":
            canal = canais.get(cid)
            if canal is None or canal.periodo_us <= 0:
                return
            if canal.periodo_us not in ev_ts:
                return
            n = tam // 2
            if n <= 0:
                return
            valores_burst = np.frombuffer(
                dados, dtype=_dtype_da_rajada(canal.tipo), count=n, offset=off_payload
            )
            periodo_ms = canal.periodo_us / 1000.0
            ts_burst = ts_ms + np.round(np.arange(n) * periodo_ms).astype(np.int64)
            ev_ts[canal.periodo_us].extend(ts_burst.tolist())
            ev_cid[canal.periodo_us].extend([cid] * n)
            ev_val[canal.periodo_us].extend(valores_burst.astype(np.float64).tolist())

    canais_2: dict[int, _CanalTmp] = {}
    grupos_2: dict[int, list[int]] = {}
    _percorre_registros(dados, canais_2, grupos_2, _ao_registro)

    valores_pendentes = _decodifica_escalares_em_bloco(
        dados, pendentes_off, pendentes_tipo
    )
    for periodo_us, pos, valor in zip(
        pendentes_periodo, pendentes_pos, valores_pendentes.tolist(), strict=True
    ):
        ev_val[periodo_us][pos] = valor

    houve_amostra = False
    for periodo_us, colunas in colunas_por_periodo.items():
        ts_lista = ev_ts[periodo_us]
        n_eventos = len(ts_lista)
        if n_eventos == 0:
            continue
        cid_lista = ev_cid[periodo_us]
        val_lista = ev_val[periodo_us]

        cids_coluna = np.array([cid for cid, _nome in colunas], dtype=np.int64)
        ordem_cid = np.argsort(cids_coluna)
        cids_ordenados = cids_coluna[ordem_cid]
        hz = 1_000_000.0 / periodo_us

        vistos_ts: set[int] = set()
        inicio_janela = 0
        for i in range(n_eventos):
            vistos_ts.add(ts_lista[i])
            if len(vistos_ts) >= _LINHAS_POR_LOTE or i == n_eventos - 1:
                fim_janela = i + 1
                lote = _monta_lote_da_janela(
                    ts_lista[inicio_janela:fim_janela],
                    cid_lista[inicio_janela:fim_janela],
                    val_lista[inicio_janela:fim_janela],
                    colunas,
                    cids_ordenados,
                    ordem_cid,
                    hz,
                )
                houve_amostra = True
                yield lote
                inicio_janela = fim_janela
                vistos_ts = set()

    if not houve_amostra:
        raise ErroDeLeitura(
            f"{nome_arquivo}: nenhuma amostra decodificavel foi lida do stream"
        )


def _ler_bytes(dados: bytes, nome_arquivo: str) -> Iterator[Lote]:
    # PASSADA UNICA (ver docstring do modulo, secao "ler()"): canais/grupos
    # sao construidos incrementalmente pelo MESMO walker que decide onde
    # decodificar. Um canal de `bytes_amostra == 2` e decodificavel na hora
    # (nao depende de nada mais adiante no arquivo). Um canal de
    # `bytes_amostra != 2` so e decodificavel se algum registro `M` o
    # confirmar EM QUALQUER PONTO do arquivo - e a confirmacao pode vir
    # DEPOIS do primeiro `S`/`G` que usa esse canal.
    #
    # Em vez de acumular cegamente todo evento de todo canal (caro: canais
    # como `Distance Lap`/`Gear`/`Master Clk`, sempre `bytes_amostra != 2` e
    # NUNCA confirmados por `M` no acervo real, tem dezenas de milhares de
    # amostras cada, e acumular+descartar isso no fim custou mais do que a
    # segunda passada que essa reescrita elimina, medido em 29/08 nos
    # arquivos `grande_8.7mb` e `moto_superbike`), o registro so entra na
    # estrutura final quando ja se sabe que e decodificavel NAQUELE
    # instante: 2 bytes decide na hora, `cid` ja visto num `M` anterior
    # decide na hora. Se nenhuma das duas bate, o evento e so um marcador em
    # `cids_com_evento_perdido` (sem guardar offset: nunca precisou, ver
    # abaixo) e o registro em si e descartado.
    #
    # Isso e uma aposta baseada em medicao (validado em 29/08 contra os 116
    # arquivos do acervo: em ZERO casos um canal de `bytes_amostra != 2` foi
    # confirmado por `M` DEPOIS de ja ter aparecido via `S`/`G`), nao uma
    # garantia do formato. Por isso `cids_com_evento_perdido` fica de
    # sentinela: se algum `cid` acabar em `canais_via_m` (decodificavel)
    # E tambem em `cids_com_evento_perdido` (teve amostra descartada antes
    # de ser confirmado), a aposta furou PRA ESSE ARQUIVO, e a funcao cai
    # pra `_ler_bytes_duas_passadas` (o algoritmo antigo, correto por
    # construcao, preservado exatamente pra este caso de escape) em vez de
    # devolver dado incompleto.
    canais: dict[int, _CanalTmp] = {}
    grupos: dict[int, list[int]] = {}
    canais_via_m: set[int] = set()
    cids_com_evento_perdido: set[int] = set()

    # Eventos por taxa nativa (periodo_us), na ORDEM em que aparecem no
    # arquivo, ja filtrados por decodificavel (ver acima): `ev_ts`, `ev_cid`
    # e `ev_val` sao paralelos (evento i da taxa p).
    ev_ts: dict[int, list[int]] = {}
    ev_cid: dict[int, list[int]] = {}
    ev_val: dict[int, list[float | None]] = {}

    # Escalares pendentes de decodificacao (S + membro de G), acumulados
    # globalmente pra decodificar TODOS de uma vez no fim da passada, em vez
    # de um struct.unpack_from por amostra dentro do loop.
    pendentes_periodo: list[int] = []
    pendentes_pos: list[int] = []
    pendentes_off: list[int] = []
    pendentes_tipo: list[int] = []

    def _registra_pendente(
        periodo_us: int, ts_ms: int, cid: int, off: int, tipo: int
    ) -> None:
        lista_ts = ev_ts.setdefault(periodo_us, [])
        lista_ts.append(ts_ms)
        ev_cid.setdefault(periodo_us, []).append(cid)
        ev_val.setdefault(periodo_us, []).append(None)
        pendentes_periodo.append(periodo_us)
        pendentes_pos.append(len(lista_ts) - 1)
        pendentes_off.append(off)
        pendentes_tipo.append(tipo)

    def _ao_registro(
        kind: bytes, ts_ms: int, cid: int, off_payload: int, tam: int
    ) -> None:
        # `canais`/`grupos` aqui sao os MESMOS que o walker usa pra validar
        # o registro (nao ha copia "completa" separada: e passada unica).
        # Todo cid que chega aqui ja foi validado pelo walker antes de
        # chamar `ao_registro`, entao ele necessariamente existe em
        # `canais`/`grupos`.
        if kind == b"S":
            canal = canais[cid]
            if canal.periodo_us <= 0:
                return
            if canal.bytes_amostra == 2 or cid in canais_via_m:
                _registra_pendente(
                    canal.periodo_us, ts_ms, cid, off_payload, canal.tipo
                )
            else:
                cids_com_evento_perdido.add(cid)
        elif kind == b"G":
            offset_membro = off_payload
            for membro in grupos.get(cid, []):
                canal_membro = canais.get(membro)
                if canal_membro is None:
                    break
                if canal_membro.periodo_us > 0:
                    if canal_membro.bytes_amostra == 2 or membro in canais_via_m:
                        _registra_pendente(
                            canal_membro.periodo_us,
                            ts_ms,
                            membro,
                            offset_membro,
                            canal_membro.tipo,
                        )
                    else:
                        cids_com_evento_perdido.add(membro)
                offset_membro += canal_membro.bytes_amostra
        elif kind == b"M":
            # Diferente de S/G, o walker (`_percorre_registros`) NAO valida
            # `cid` contra `canais` pra kind M (nao ha tamanho de payload
            # que dependa do CHS: `n` vem inline no proprio registro). Um
            # `M` pra `cid` sem CHS nunca foi medido no acervo (0 ocorrencias
            # na varredura de 29/08), mas o `.get()` fica defensivo mesmo
            # assim, igual a versao anterior de duas passadas.
            canais_via_m.add(cid)
            canal = canais.get(cid)
            if canal is None or canal.periodo_us <= 0:
                return
            n = tam // 2
            if n <= 0:
                return
            # Rajada e contigua no arquivo (n escalares de 2 bytes seguidos):
            # um unico np.frombuffer decodifica o bloco inteiro, sem loop de
            # struct, no dtype que o byte de tipo do canal manda.
            valores_burst = np.frombuffer(
                dados, dtype=_dtype_da_rajada(canal.tipo), count=n, offset=off_payload
            )
            periodo_ms = canal.periodo_us / 1000.0
            # Timestamp de cada amostra da rajada, vetorizado (ver docstring
            # do modulo, secao "Rajada"): mesma formula `ts_ms + round(i *
            # periodo_ms)` do codigo anterior, so que pro vetor inteiro.
            ts_burst = ts_ms + np.round(np.arange(n) * periodo_ms).astype(np.int64)
            ev_ts.setdefault(canal.periodo_us, []).extend(ts_burst.tolist())
            ev_cid.setdefault(canal.periodo_us, []).extend([cid] * n)
            ev_val.setdefault(canal.periodo_us, []).extend(
                valores_burst.astype(np.float64).tolist()
            )

    # Chunks GPS coletados pelo MESMO walker (offset do corpo de 56 bytes);
    # viram serie propria no fim (ver `_lotes_gps`).
    gps_offsets: list[int] = []

    _percorre_registros(dados, canais, grupos, _ao_registro, gps_offsets.append)
    if not canais:
        raise ErroDeLeitura(
            f"{nome_arquivo}: nenhum chunk CHS encontrado, nao ha canal pra ler"
        )

    # A aposta da passada unica furou: algum canal so confirmado por `M`
    # tinha amostra `S`/`G` descartada ANTES da confirmacao. Nunca visto no
    # acervo real (29/08), mas se acontecer o dado certo importa mais que a
    # velocidade: cai pro algoritmo de duas passadas, que nunca descarta
    # amostra antes de saber se o canal e decodificavel.
    cids_furados = canais_via_m & cids_com_evento_perdido
    if cids_furados:
        import warnings

        warnings.warn(
            f"{nome_arquivo}: canal(is) {sorted(cids_furados)} confirmados "
            "decodificaveis por M so depois de ja terem amostra S/G no "
            "stream; passada unica nao cobre esse caso, caindo pra duas "
            "passadas (mais lento, mas correto) so pra este arquivo.",
            stacklevel=2,
        )
        yield from _ler_bytes_duas_passadas(dados, nome_arquivo)
        # A serie GPS nao depende da aposta que furou (o chunk GPS nao passa
        # por CHS/M): os offsets ja coletados valem, emite igual.
        yield from _lotes_gps(dados, gps_offsets, canais)
        return

    def _decodificavel(cid: int, canal: _CanalTmp) -> bool:
        # Ver docstring do modulo, secao "Que canais sao decodificados":
        # int16 confirmado (2 bytes) OU visto num registro M, que e sempre
        # n*int16 pelo formato do registro, independente do bytes_amostra
        # declarado no CHS pra S/G.
        return canal.bytes_amostra == 2 or cid in canais_via_m

    # Agrupa por periodo_us (chave inteira, evita comparar float) os canais
    # decodificaveis, com nome de coluna estavel = nome_bruto (mesma regra
    # do inventario: longo, senao curto, senao canal_<id>).
    por_periodo: dict[int, list[tuple[int, str]]] = {}
    for cid, canal in canais.items():
        if canal.periodo_us <= 0 or not _decodificavel(cid, canal):
            continue
        nome = canal.nome_longo or canal.nome_curto or f"canal_{cid}"
        por_periodo.setdefault(canal.periodo_us, []).append((cid, nome))

    if not por_periodo and len(gps_offsets) < 2:
        raise ErroDeLeitura(
            f"{nome_arquivo}: nenhum canal decodificavel (int16, rajada M ou "
            "GPS), nada pra ler"
        )

    colunas_por_periodo: dict[int, list[tuple[int, str]]] = {}
    for periodo_us, entradas in por_periodo.items():
        entradas.sort(key=lambda par: par[1])
        vistos: dict[str, int] = {}
        colunas: list[tuple[int, str]] = []
        for cid, nome in entradas:
            n = vistos.get(nome, 0)
            vistos[nome] = n + 1
            # Colisao de nome_bruto dentro da mesma taxa (nunca medida no
            # acervo, mas o schema tem que ficar estavel mesmo assim):
            # desambigua com o id do canal.
            nome_final = nome if n == 0 else f"{nome}#{cid}"
            colunas.append((cid, nome_final))
        colunas_por_periodo[periodo_us] = colunas

    # Decodifica TODOS os escalares pendentes (S + membro de G) de uma vez,
    # e devolve cada valor pro slot certo (periodo_us, pos) em ev_val. A
    # ordem de `pendentes_*` e a ordem de encontro no arquivo, entao o
    # backfill preserva a mesma ordem que o loop original tinha. So chegam
    # aqui pendentes de canal JA decodificavel (ver `_ao_registro` acima: a
    # decisao de acumular ou so marcar em `cids_com_evento_perdido` e feita
    # na hora, nao existe filtro posterior descartando evento acumulado).
    valores_pendentes = _decodifica_escalares_em_bloco(
        dados, pendentes_off, pendentes_tipo
    )
    for periodo_us, pos, valor in zip(
        pendentes_periodo, pendentes_pos, valores_pendentes.tolist(), strict=True
    ):
        ev_val[periodo_us][pos] = valor

    houve_amostra = False
    for periodo_us, colunas in colunas_por_periodo.items():
        ts_lista = ev_ts.get(periodo_us, [])
        cid_lista = ev_cid.get(periodo_us, [])
        val_lista = ev_val.get(periodo_us, [])
        n_eventos = len(ts_lista)
        if n_eventos == 0:
            continue

        cids_coluna = np.array([cid for cid, _nome in colunas], dtype=np.int64)
        ordem_cid = np.argsort(cids_coluna)
        cids_ordenados = cids_coluna[ordem_cid]
        hz = 1_000_000.0 / periodo_us

        # Corte de janela IDENTICO ao buffer antigo: um lote fecha assim que
        # o numero de timestamps DISTINTOS acumulados desde o ultimo corte
        # bate `_LINHAS_POR_LOTE` (o buffer antigo resetava nesse ponto).
        # Medido no acervo real (29/08): o MESMO ts_ms pode reaparecer bem
        # mais adiante no arquivo (nao e estritamente crescente), e nesse
        # caso o buffer antigo conta como linha NOVA na janela seguinte em
        # vez de fundir com a ocorrencia anterior. Reproduzir o corte por
        # janela, em vez de deduplicar ts_ms globalmente pro periodo inteiro,
        # e o que preserva essa mesma contagem de linha.
        vistos_ts: set[int] = set()
        inicio_janela = 0
        for i in range(n_eventos):
            vistos_ts.add(ts_lista[i])
            if len(vistos_ts) >= _LINHAS_POR_LOTE or i == n_eventos - 1:
                fim_janela = i + 1
                lote = _monta_lote_da_janela(
                    ts_lista[inicio_janela:fim_janela],
                    cid_lista[inicio_janela:fim_janela],
                    val_lista[inicio_janela:fim_janela],
                    colunas,
                    cids_ordenados,
                    ordem_cid,
                    hz,
                )
                houve_amostra = True
                yield lote
                inicio_janela = fim_janela
                vistos_ts = set()

    for lote_gps in _lotes_gps(dados, gps_offsets, canais):
        houve_amostra = True
        yield lote_gps

    if not houve_amostra:
        raise ErroDeLeitura(
            f"{nome_arquivo}: nenhuma amostra decodificavel foi lida do stream"
        )


class LeitorXrk(LeitorDeInventario):
    formato_id = "aim_xrk"
    versao = _VERSAO
    suporta_amostra = True

    def inspecionar(self, caminho: Path) -> Cabecalho:
        try:
            dados = caminho.read_bytes()
        except OSError as exc:
            raise ErroDeLeitura(
                f"{caminho}: nao foi possivel ler o arquivo: {exc}"
            ) from exc
        if not dados:
            raise ErroDeLeitura(f"{caminho}: arquivo vazio")
        return _inspecionar_bytes(_descomprime_se_xrz(dados, caminho), str(caminho))

    def ler(self, caminho: Path) -> Iterator[Lote]:
        try:
            dados = caminho.read_bytes()
        except OSError as exc:
            raise ErroDeLeitura(
                f"{caminho}: nao foi possivel ler o arquivo: {exc}"
            ) from exc
        if not dados:
            raise ErroDeLeitura(f"{caminho}: arquivo vazio")
        yield from _ler_bytes(_descomprime_se_xrz(dados, caminho), str(caminho))
