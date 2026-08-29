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

   Kind fora desses tres interrompe a leitura aqui: sem tabela de tamanho
   por kind, adivinhar o payload e o mesmo buraco do B2.

2. Chunk nomeado solto, mesmo formato de abertura/fecho do topo, aparecendo
   INTERCALADO com os registros compactos acima (nao so no cabecalho):
   `LAP` (32 bytes/volta, campos nao decodificados aqui: o contrato desta
   etapa nao pede volta, so canal), `GPS` (56 bytes, 14 x int32; ECEF em
   centimetros nos indices 4, 5 e 6 CONTANDO DE ZERO (validado em 29/08 no
   par kart-guara: decodifica pra lat -15.82570, lon -47.97108, 1081 m, que
   e o Guara em Brasilia e bate com a pasta do acervo), velocidade ECEF nos
   indices 8, 9 e 10. NAO
   convertido aqui por decisao do enunciado) e `CAL` (144 bytes, calibracao
   analogica).

   # CAL nao decodificado aqui de proposito: sem ele os int16 crus de canal
   # analogico nao viram unidade fisica, e isso e trabalho do `ler()` da
   # etapa 3, nao do inventario.

10 dos 66 arquivos do acervo param numa variante de registro nao mapeada
(kind desconhecido, ou payload que nao fecha em ')' onde esperado). Isso e
leitura PARCIAL declarada, nao falha: os canais definidos em `CHS` ja foram
lidos antes de o stream de amostra comecar, entao o inventario de canal sai
completo mesmo quando a contagem de amostra para no meio. O ponto de parada
e quantos bytes ficaram sem cobertura vao em `bruto`.

## ler(): amostra em streaming, sem calibracao

`ler()` percorre o MESMO fluxo de registros que `inspecionar()` (chunks +
S/G/M), duas vezes:

1. Passada de cabecalho: coleta `CHS`/`GRP` completos e, so pra decidir
   decodificabilidade, marca quais canais aparecem em pelo menos um
   registro `M` (rajada). Essa passada para no MESMO offset que
   `inspecionar()` pararia (mesma logica de quebra), entao o schema por
   taxa fica decidido ANTES do primeiro `Lote`, mesmo em leitura parcial.
2. Passada de decodificacao: repete o mesmo percurso, desta vez lendo o
   valor de cada amostra e acumulando por taxa nativa (`periodo_us` do
   `CHS`), com o `ts_ms` do registro como eixo (`t_s = ts_ms / 1000`).

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

import pyarrow as pa

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario, Lote

_VERSAO = "0.1.0"

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
    __slots__ = ("bytes_amostra", "nome_curto", "nome_longo", "periodo_us")

    def __init__(
        self, nome_curto: str, nome_longo: str, periodo_us: int, bytes_amostra: int
    ) -> None:
        self.nome_curto = nome_curto
        self.nome_longo = nome_longo
        self.periodo_us = periodo_us
        self.bytes_amostra = bytes_amostra


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
    return cid, _CanalTmp(curto.strip(), longo.strip(), periodo_us, bytes_amostra)


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


def _inspecionar_bytes(dados: bytes, nome_arquivo: str) -> Cabecalho:
    canais: dict[int, _CanalTmp] = {}
    grupos: dict[int, list[int]] = {}
    contagem_amostras: dict[int, int] = {}
    bruto: dict[str, str] = {}
    n_gps = 0
    n_lap = 0
    n_cal = 0
    ts_max_ms = 0
    viu_registro = False

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
            elif prefixo == b"GPS":
                n_gps += 1
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

        # Nem chunk nem registro reconhecido: para aqui.
        break

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

    parcial = off < tamanho_total
    bruto["leitura_parcial"] = "sim" if parcial else "nao"
    if parcial:
        bruto["offset_parada"] = str(off)
        bruto["bytes_sem_cobertura"] = str(tamanho_total - off)
    bruto["n_canais_chs"] = str(len(canais))
    bruto["n_grupos_grp"] = str(len(grupos))
    bruto["gps_amostras"] = str(n_gps)
    bruto["lap_chunks"] = str(n_lap)
    bruto["cal_chunks"] = str(n_cal)

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
) -> int:
    """Percurso de chunks + registros, compartilhado pelas duas passadas de
    `ler()`. Mesma logica de `_inspecionar_bytes` (chunk CNF/CHS/GRP
    atualiza `canais`/`grupos` on-the-fly, registro `S`/`G`/`M` calcula o
    tamanho do payload pelos MESMOS canais ja vistos, kind fora da tabela
    interrompe), pra garantir que as duas passadas parem exatamente no
    mesmo offset que `inspecionar()` pararia. `ao_registro` e chamado com
    `(kind, ts_ms, cid, off_payload, tamanho_payload)` pra cada registro
    valido; `off_payload` e o comeco do payload (logo apos o id de 2
    bytes).
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

        break

    return off


def _prepara_schema(
    dados: bytes,
) -> tuple[dict[int, _CanalTmp], dict[int, list[int]], set[int], int]:
    """Passada 1: descobre TODOS os canais/grupos e quais canais aparecem
    em pelo menos um registro `M`, ate o offset onde a leitura pararia.
    Precisa rodar por completo antes do primeiro `Lote` pra o schema por
    taxa ficar estavel (regra dura do contrato), mesmo quando o arquivo e
    de leitura parcial.
    """
    canais: dict[int, _CanalTmp] = {}
    grupos: dict[int, list[int]] = {}
    canais_via_m: set[int] = set()

    def _ao_registro(
        kind: bytes, ts_ms: int, cid: int, off_payload: int, tam: int
    ) -> None:
        if kind == b"M":
            canais_via_m.add(cid)

    off_parada = _percorre_registros(dados, canais, grupos, _ao_registro)
    return canais, grupos, canais_via_m, off_parada


def _ler_bytes(dados: bytes, nome_arquivo: str) -> Iterator[Lote]:
    canais, grupos, canais_via_m, _off_parada = _prepara_schema(dados)
    if not canais:
        raise ErroDeLeitura(
            f"{nome_arquivo}: nenhum chunk CHS encontrado, nao ha canal pra ler"
        )

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
            # Colisao de nome_bruto dentro da mesma taxa (nunca medida no
            # acervo, mas o schema tem que ficar estavel mesmo assim):
            # desambigua com o id do canal.
            nome_final = nome if n == 0 else f"{nome}#{cid}"
            colunas.append((cid, nome_final))
        colunas_por_periodo[periodo_us] = colunas

    # Buffers por taxa: {ts_ms: {cid: valor}}. Flush quando o numero de
    # timestamps distintos bufferizados bate o limite de linhas por lote.
    buffers: dict[int, dict[int, dict[int, float]]] = {
        p: {} for p in colunas_por_periodo
    }

    def _flush(periodo_us: int) -> Lote | None:
        buffer = buffers[periodo_us]
        if not buffer:
            return None
        colunas = colunas_por_periodo[periodo_us]
        ts_ordenados = sorted(buffer.keys())
        t_s = [ts / 1000.0 for ts in ts_ordenados]
        arrays = [pa.array(t_s, type=pa.float64())]
        nomes = ["t_s"]
        for cid, nome in colunas:
            valores = [buffer[ts].get(cid, float("nan")) for ts in ts_ordenados]
            arrays.append(pa.array(valores, type=pa.float64()))
            nomes.append(nome)
        tabela = pa.RecordBatch.from_arrays(arrays, names=nomes)
        hz = 1_000_000.0 / periodo_us
        buffers[periodo_us] = {}
        return Lote(frequencia_hz=hz, tabela=tabela)

    def _acumula(periodo_us: int, ts_ms: int, cid: int, valor: float) -> Lote | None:
        buffer = buffers.get(periodo_us)
        if buffer is None:
            return None
        buffer.setdefault(ts_ms, {})[cid] = valor
        if len(buffer) >= _LINHAS_POR_LOTE:
            return _flush(periodo_us)
        return None

    lotes_pendentes: list[Lote] = []

    def _ao_registro(
        kind: bytes, ts_ms: int, cid: int, off_payload: int, tam: int
    ) -> None:
        # `canais`/`grupos` aqui sao os da PASSADA 1 (completos): o walker
        # da passada 2 (`canais_2`/`grupos_2`, abaixo) so os usa pra decidir
        # onde parar de forma identica a passada 1; pra decodificar valor,
        # todo cid que chega aqui ja foi validado pelo walker (senao nao
        # teria chamado `ao_registro`), entao ele necessariamente existe
        # tambem no dicionario completo da passada 1 (superconjunto).
        if kind == b"S":
            canal = canais.get(cid)
            if canal is None or not _decodificavel(cid, canal):
                return
            valor = struct.unpack_from("<h", dados, off_payload)[0]
            lote = _acumula(canal.periodo_us, ts_ms, cid, float(valor))
            if lote is not None:
                lotes_pendentes.append(lote)
        elif kind == b"G":
            offset_membro = off_payload
            for membro in grupos.get(cid, []):
                canal_membro = canais.get(membro)
                if canal_membro is None:
                    break
                if _decodificavel(membro, canal_membro):
                    valor = struct.unpack_from("<h", dados, offset_membro)[0]
                    lote = _acumula(
                        canal_membro.periodo_us, ts_ms, membro, float(valor)
                    )
                    if lote is not None:
                        lotes_pendentes.append(lote)
                offset_membro += canal_membro.bytes_amostra
        elif kind == b"M":
            canal = canais.get(cid)
            if canal is None or canal.periodo_us <= 0:
                return
            n = tam // 2
            periodo_ms = canal.periodo_us / 1000.0
            for i in range(n):
                valor = struct.unpack_from("<h", dados, off_payload + 2 * i)[0]
                ts_amostra = ts_ms + round(i * periodo_ms)
                lote = _acumula(canal.periodo_us, ts_amostra, cid, float(valor))
                if lote is not None:
                    lotes_pendentes.append(lote)

    # Dicionarios NOVOS e vazios, nao copia do resultado da passada 1: o
    # objetivo e reconstruir canais/grupos incrementalmente do zero, do
    # jeito exato que `inspecionar()` faz, pra o ponto de parada desta
    # passada bater com o de `_prepara_schema` byte a byte. Se usassemos os
    # dicionarios ja completos da passada 1, um registro que referencia um
    # canal cujo CHS so aparece MAIS TARDE no arquivo pareceria valido aqui
    # e invalido la, e as duas passadas divergiriam.
    canais_2: dict[int, _CanalTmp] = {}
    grupos_2: dict[int, list[int]] = {}
    _percorre_registros(dados, canais_2, grupos_2, _ao_registro)

    houve_amostra = bool(lotes_pendentes)
    for lote in lotes_pendentes:
        yield lote
    lotes_pendentes.clear()

    for periodo_us in colunas_por_periodo:
        lote = _flush(periodo_us)
        if lote is not None:
            houve_amostra = True
            yield lote

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
        return _inspecionar_bytes(dados, str(caminho))

    def ler(self, caminho: Path) -> Iterator[Lote]:
        try:
            dados = caminho.read_bytes()
        except OSError as exc:
            raise ErroDeLeitura(
                f"{caminho}: nao foi possivel ler o arquivo: {exc}"
            ) from exc
        if not dados:
            raise ErroDeLeitura(f"{caminho}: arquivo vazio")
        yield from _ler_bytes(dados, str(caminho))
