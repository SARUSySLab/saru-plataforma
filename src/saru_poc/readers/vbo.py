"""Leitor de inventario para Racelogic VBOX .vbo (formato_id vbox_vbo).

Fatos medidos no acervo em 2026-08-29 (9 arquivos, 3 distintos por conteudo:
Ref_40Rookie/Ref_40 com 22 colunas, Ref_992 e os 3 arquivos Giaffone com 41
colunas, cada um duplicado em duas pastas):

- ASCII com CRLF, sempre com secoes entre colchetes: [header],
  [channel units], [comments], [AVI], [laptiming], [column names], [data].
  As duas primeiras trazem, respectivamente, nome longo e unidade de cada
  canal, mas NAO sao paralelas 1 para 1 (ver bloco de unidades abaixo).
- [column names] tem UMA linha, com os codigos curtos separados por espaco.
  [data] tem uma linha por amostra, valores separados por espaco (linhas
  podem ter espaco extra no fim).
- Duas larguras de esquema no acervo: 22 colunas (sem bloco rad_*) e 41
  colunas (com rad_*). O leitor nao hardcoda largura nenhuma, sempre le de
  [column names].
- Taxa GLOBAL de 10 Hz, declarada na coluna Tsample (0.100) e conferivel
  pela coluna time (HHMMSS.sss). Nao ha taxa por canal aqui: todo CanalBruto
  recebe a mesma frequencia_hz.
- [laptiming] traz a linha de chegada (par de coordenadas geodesicas), que e
  insumo direto da etapa 5 do pipeline (corte de volta). Guardada em bruto
  sob a chave "laptiming_raw".
- lat/long estao em MINUTOS DECIMAIS (convencao Racelogic), e a longitude e
  POSITIVA A OESTE: um valor de longitude "+2801.999150" em minutos vira
  2801.999150 / 60 = 46.6999925 graus, que e OESTE, ou seja -46.6999925 em
  WGS84 (leste positivo). Exemplo do proprio arquivo real (giaffone-vbox):
  lat "-1422.223780" -> -1422.223780 / 60 = -23.7037297 (sul, ja negativo,
  sem troca de sinal); long "+2801.999150" -> 2801.999150 / 60 =
  46.6999858, que E oeste -> -46.6999858 em WGS84. Este leitor NAO faz essa
  conversao (e trabalho da etapa 3, contra o mapa de canal). IMPORTANTE:
  medido nos 3 arquivos distintos do acervo, [channel units] NUNCA declara
  unidade pra lat/long (nem pros outros 6 canais GPS iniciais: satellites,
  time, velocity, heading, height, vertical velocity) - ver a secao "Bloco
  de unidades" abaixo. Por isso unidade_declarada sai None pra esses
  canais: nao ha unidade nenhuma no arquivo pra ler, e inventar
  "minutos" seria a mesma doenca do B2.
- venue_declarado: o .vbo nao declara pista. Sempre None aqui, nunca
  inferido do nome do arquivo.

Bloco de unidades ([channel units]), medido nos 3 arquivos distintos do
acervo (2026-08-29): NAO e paralelo posicionalmente a [header]/[column
names]. O bloco tem exatamente `1 + (n_colunas - indice_avisynctime - 1)`
entradas, e a correspondencia real e:
  - a PRIMEIRA entrada e a unidade de "sampleperiod" (sempre "s");
  - as entradas SEGUINTES casam, em ordem, com os canais que vem DEPOIS de
    "avisynctime" no header (os 6 canais GPS iniciais - satellites, time,
    latitude, longitude, velocity, heading, height, vertical velocity - e
    os dois canais de AVI - avifileindex, avisynctime - nunca tem entrada
    de unidade).
Verificado por semantica em Ref_40 (22 col), Ref_992 e Giaffone Q.1 (41
col): a ordem dos canais VBOX_* no header varia entre exports (um lista
VBOX_rpm primeiro, outro lista VBOX_laptime primeiro), mas a lista de
unidades sempre casa em ordem com a lista de canais QUE VEM DEPOIS de
avisynctime naquele mesmo header - ex. VBOX_asteer -> "°" (graus),
VBOX_pbrk -> "bar", VBOX_rpm -> "rpm", rad_* -> "(null)". Essa hipotese
bateu nos 3 arquivos distintos sem excecao. Se "sampleperiod" ou
"avisynctime" nao existirem no header, ou se a contagem resultante nao
bater com o tamanho real do bloco de unidades, o leitor NAO tenta parear:
devolve unidade_declarada=None pra todo canal e registra o motivo em
`bruto["channel_units_alinhamento"]`, em vez de arriscar atribuir unidade
errada a canal (regra dura do projeto contra leitor que adivinha, doenca
do B2).

Nota de decodificacao (corrigida apos revisao, 2026-08-29): os 9 arquivos
do acervo decodificam em UTF-8 SEM ERRO (confirmado por
`bytes.decode("utf-8")` nos 9). Uma exploracao anterior presumiu que os
bytes de "°" e "¬" quebravam UTF-8 e latin-1 seria necessario; isso estava
errado, e latin-1 produz mojibake nesses arquivos (ex. o "¬" real de
[laptiming], byte b"\\xc2\\xac", vira "Â¬" em latin-1 em vez de "¬"). Este
leitor decodifica em UTF-8 estrito; se algum arquivo futuro do acervo
falhar nisso, cai pra latin-1 e registra qual encoding foi usado em
`bruto["encoding_usado"]`, em vez de assumir um dos dois em silencio.

Porte: decodificacao adaptada de
saru-app/services/telemetry-api/saru_lapanalyzer/infra/datasources/vbo_file.py
(commit aa94872 do snapshot tudo_junto/saru-app, 2026-08-26). A camada de
dominio de la (que colapsa canais num eixo master via np.interp e sintetiza
tempo decorrido) foi descartada: aqui o contrato guarda taxa nativa e nome
bruto, sem interpretar semantica. O pareamento de unidades e integralmente
novo: o leitor de origem so tentava zip posicional (que nunca bate nos
arquivos reais medidos) e caia num dict vazio.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from pathlib import Path

import pyarrow as pa

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario, Lote

FREQUENCIA_HZ_PADRAO = 10.0

# Tamanho de lote sugerido pelo contrato (50 mil a 200 mil linhas). O maior
# .vbo do acervo medido (2026-08-29) tem 21 772 linhas de dado, entao na
# pratica cada arquivo sai num Lote so, mas o streaming em blocos fica pronto
# pra um arquivo maior do que qualquer um do acervo atual.
_LINHAS_POR_LOTE = 50_000

# Codigos/nomes de ancora usados pra achar a taxa e o alinhamento do bloco
# de unidades. "Tsample" e o codigo curto em [column names]; "sampleperiod"
# e "avisynctime" sao nomes longos em [header].
_COLUNAS_TSAMPLE = ("Tsample", "sampleperiod")
_NOME_SAMPLEPERIOD = "sampleperiod"
_NOME_AVISYNCTIME = "avisynctime"


def _particiona_secoes(linhas: list[str]) -> dict[str, list[str]]:
    """Agrupa as linhas do .vbo por secao `[nome]`.

    Linhas antes da primeira secao (a linha "File created on ...") sao
    descartadas, igual ao leitor de origem.
    """
    secoes: dict[str, list[str]] = {}
    atual: str | None = None
    for linha in linhas:
        s = linha.strip()
        if s.startswith("[") and s.endswith("]"):
            atual = s[1:-1].strip().lower()
            secoes[atual] = []
        elif atual is not None:
            secoes[atual].append(linha)
    return secoes


def _le_com_encoding_seguro(caminho: Path) -> tuple[str, str]:
    """Le o arquivo em UTF-8 estrito; cai pra latin-1 se falhar.

    Devolve (texto, encoding_usado). latin-1 nunca levanta
    UnicodeDecodeError (mapeia byte a byte), entao e a rede de seguranca:
    se o UTF-8 estrito falhar, algo esta genuinamente fora do padrao
    medido no acervo, e vale registrar qual encoding foi usado em vez de
    assumir em silencio.
    """
    bruto_bytes = caminho.read_bytes()
    try:
        return bruto_bytes.decode("utf-8", errors="strict"), "utf-8"
    except UnicodeDecodeError:
        return bruto_bytes.decode("latin-1"), "latin-1"


def _unidades_por_indice(
    header: list[str], unidades: list[str], colunas: list[str]
) -> tuple[list[str | None], str]:
    """Pareia [channel units] com os canais de [column names].

    Medido nos 3 arquivos distintos do acervo (2026-08-29): o bloco de
    unidades NAO e paralelo a [header] posicao a posicao. A primeira
    entrada e a unidade de "sampleperiod"; as demais casam em ordem com os
    canais que vem depois de "avisynctime" no header (os canais GPS
    iniciais e os dois de AVI nunca tem unidade declarada). Ver docstring
    do modulo pra evidencia completa.

    Devolve (lista de unidade por indice de coluna, motivo). Se a hipotese
    de alinhamento nao bater (ancora ausente ou contagem incompativel),
    devolve tudo None e o motivo, sem arriscar atribuir unidade errada.
    """
    n_colunas = len(colunas)
    nomes = [ln.strip() for ln in header if ln.strip()]
    vals = [ln.strip() for ln in unidades if ln.strip()]

    if not vals:
        return [None] * n_colunas, "secao [channel units] vazia ou ausente"
    if len(nomes) != n_colunas:
        return (
            [None] * n_colunas,
            (
                f"[header] tem {len(nomes)} entradas, [column names] tem "
                f"{n_colunas}: nao da pra usar [header] como referencia de indice"
            ),
        )

    nomes_lower = [n.lower() for n in nomes]
    if _NOME_SAMPLEPERIOD not in nomes_lower or _NOME_AVISYNCTIME not in nomes_lower:
        return (
            [None] * n_colunas,
            (
                "header sem 'sampleperiod' ou 'avisynctime': sem ancora pra "
                "alinhar [channel units]"
            ),
        )

    idx_sampleperiod = nomes_lower.index(_NOME_SAMPLEPERIOD)
    idx_avisynctime = nomes_lower.index(_NOME_AVISYNCTIME)
    cauda = list(range(idx_avisynctime + 1, n_colunas))
    esperado = 1 + len(cauda)
    if len(vals) != esperado:
        return (
            [None] * n_colunas,
            (
                f"[channel units] tem {len(vals)} entradas, esperava {esperado} "
                "(1 pra sampleperiod + 1 por canal apos avisynctime): hipotese "
                "de alinhamento nao bateu, nao pareando"
            ),
        )

    resultado: list[str | None] = [None] * n_colunas
    resultado[idx_sampleperiod] = vals[0]
    for idx_coluna, valor in zip(cauda, vals[1:], strict=True):
        resultado[idx_coluna] = valor
    return resultado, "alinhado por sampleperiod + cauda apos avisynctime"


def _hhmmss_para_segundos(bruto: str) -> float | None:
    """Converte a coluna `time` (formato HHMMSS.sss) em segundos do dia.

    Nao usa `datetime`/`strptime`: o campo nao e um horario ISO, e um numero
    decimal onde as duas casas mais altas da parte inteira sao hora, as duas
    seguintes minuto e o resto (parte inteira restante + decimal) segundo.
    Ex.: 175943.400 -> 17h 59m 43.400s.
    """
    try:
        v = float(bruto)
    except ValueError:
        return None
    hh = int(v // 10000)
    mm = int((v // 100) % 100)
    ss = v - (hh * 10000 + mm * 100)
    return hh * 3600.0 + mm * 60.0 + ss


class LeitorVbo(LeitorDeInventario):
    """Inventario e amostra para Racelogic VBOX .vbo."""

    formato_id = "vbox_vbo"
    versao = "2"
    suporta_amostra = True

    def inspecionar(self, caminho: Path) -> Cabecalho:
        try:
            texto, encoding_usado = _le_com_encoding_seguro(caminho)
        except OSError as exc:
            raise ErroDeLeitura(f"nao consegui abrir {caminho}: {exc}") from exc

        linhas = texto.splitlines()
        secoes = _particiona_secoes(linhas)

        col_linhas = secoes.get("column names", [])
        if not col_linhas or not col_linhas[0].split():
            raise ErroDeLeitura(f".vbo sem secao [column names] ou vazia: {caminho}")
        colunas = col_linhas[0].split()

        dado_linhas = [ln for ln in secoes.get("data", []) if ln.strip()]
        if not dado_linhas:
            raise ErroDeLeitura(f".vbo sem secao [data] ou sem amostras: {caminho}")

        n_colunas = len(colunas)
        linhas_partidas = [ln.split() for ln in dado_linhas]

        # Acumuladores de min/max por indice de coluna, num passe so.
        minimos: list[float | None] = [None] * n_colunas
        maximos: list[float | None] = [None] * n_colunas
        n_amostras = 0
        for partes in linhas_partidas:
            n_amostras += 1
            for i in range(n_colunas):
                if i >= len(partes):
                    continue
                try:
                    v = float(partes[i])
                except ValueError:
                    continue
                if minimos[i] is None or v < minimos[i]:
                    minimos[i] = v
                if maximos[i] is None or v > maximos[i]:
                    maximos[i] = v

        unidades, motivo_alinhamento = _unidades_por_indice(
            secoes.get("header", []), secoes.get("channel units", []), colunas
        )

        # Taxa global: le o periodo declarado na coluna Tsample (indice
        # comum a todas as linhas de [data], nao ha taxa por canal aqui).
        # Cai para 10 Hz so se a coluna nao existir ou o valor for invalido.
        frequencia_hz = FREQUENCIA_HZ_PADRAO
        idx_tsample = next(
            (colunas.index(c) for c in _COLUNAS_TSAMPLE if c in colunas), None
        )
        if idx_tsample is not None and maximos[idx_tsample] is not None:
            periodo = maximos[idx_tsample]
            if periodo and periodo > 0:
                frequencia_hz = round(1.0 / periodo, 6)

        canais = tuple(
            CanalBruto(
                nome_bruto=nome,
                frequencia_hz=frequencia_hz,
                n_amostras=n_amostras,
                unidade_declarada=unidades[i],
                valor_min=minimos[i],
                valor_max=maximos[i],
            )
            for i, nome in enumerate(colunas)
        )

        primeira_linha = linhas[0].strip() if linhas else ""
        bruto: dict[str, str] = {
            "criado_em_raw": primeira_linha,
            "encoding_usado": encoding_usado,
            "channel_units_alinhamento": motivo_alinhamento,
        }
        laptiming = [ln for ln in secoes.get("laptiming", []) if ln.strip()]
        if laptiming:
            bruto["laptiming_raw"] = " | ".join(laptiming)
        comentarios = [ln for ln in secoes.get("comments", []) if ln.strip()]
        if comentarios:
            bruto["comments_raw"] = " | ".join(comentarios)

        # "File created on 12/11/2022 @ 10:24:06" -> guarda so o timestamp,
        # sem reformatar: o arquivo nao diz se e DD/MM ou MM/DD, entao
        # inventar um parse com datetime seria adivinhar. capturado_em fica
        # com o texto cru apos "File created on ".
        prefixo = "file created on "
        capturado_em = None
        if primeira_linha.lower().startswith(prefixo):
            capturado_em = primeira_linha[len(prefixo) :].strip() or None

        # Duracao pela taxa global (Tsample, 10 Hz nos arquivos medidos):
        # n_amostras / frequencia. Nao depende de parsear a coluna time
        # (HHMMSS.sss), que e mais fragil (vira do dia, pode cruzar meia
        # noite).
        duracao_s = round(n_amostras / frequencia_hz, 3) if n_amostras else None

        return Cabecalho(
            formato_id=self.formato_id,
            leitor_versao=self.versao,
            canais=canais,
            capturado_em=capturado_em,
            duracao_s=duracao_s,
            venue_declarado=None,
            bruto=bruto,
        )

    def ler(self, caminho: Path) -> Iterator[Lote]:
        """Le a secao [data] em blocos e emite um `Lote` de 10 Hz por bloco.

        Escolha de `t_s` (documentada porque o contrato pede a justificativa
        explicita): deriva da coluna `time` (HHMMSS.sss), NAO acumula
        `Tsample`. A razao e que somar `Tsample` (0.100) linha a linha
        acumula erro de ponto flutuante ao longo de milhares de amostras (o
        maior .vbo do acervo tem 21 772 linhas); ler `time` decodifica um
        valor absoluto por linha, direto do relogio que o proprio logger
        gravou, sem soma nenhuma. `t_s` sai como
        `segundos_do_dia(time) - segundos_do_dia(time_da_primeira_linha)`,
        com deteccao de virada de meia noite (se o segundo do dia cai em
        relacao a linha anterior, soma 86400 s de offset): nenhum arquivo do
        acervo medido cruza meia noite (durações na casa de minutos), mas a
        deteccao fica pronta caso apareca um que cruce. Se a coluna `time`
        nao existir ou nao parsear numa linha (`# DECISAO PENDENTE (Lucas)`:
        aqui a alternativa conservadora foi cair pra `indice / frequencia_hz`
        so NAQUELA linha, que nao acumula erro por ser multiplicacao a partir
        do indice, nao soma; a alternativa descartada seria acumular
        `Tsample` do arquivo inteiro, que reintroduz o erro que a escolha por
        `time` evita).

        Tipagem: toda coluna de canal (incluindo `time` e `Tsample`, que
        continuam gravadas com o valor bruto do arquivo) vira float64. Campo
        que nao converte pra float (celula ausente na linha, ou texto) vira
        NaN: e a representacao honesta de "nao da pra ler este valor aqui",
        nunca zero nem o valor da linha anterior.

        `lat`/`long` saem em minutos decimais, longitude positiva a oeste,
        exatamente como o arquivo grava (ver docstring do modulo): este
        metodo nao converte, e camada bruta.
        """
        try:
            texto, _ = _le_com_encoding_seguro(caminho)
        except OSError as exc:
            raise ErroDeLeitura(f"nao consegui abrir {caminho}: {exc}") from exc

        linhas = texto.splitlines()
        secoes = _particiona_secoes(linhas)

        col_linhas = secoes.get("column names", [])
        if not col_linhas or not col_linhas[0].split():
            raise ErroDeLeitura(f".vbo sem secao [column names] ou vazia: {caminho}")
        colunas = col_linhas[0].split()

        dado_linhas = [ln for ln in secoes.get("data", []) if ln.strip()]
        if not dado_linhas:
            raise ErroDeLeitura(f".vbo sem secao [data] ou sem amostras: {caminho}")

        idx_time = colunas.index("time") if "time" in colunas else None
        idx_tsample = next(
            (colunas.index(c) for c in _COLUNAS_TSAMPLE if c in colunas), None
        )

        # Taxa global: mesma logica do inspecionar (le o periodo declarado
        # na primeira linha de dado que tiver a coluna Tsample valida).
        frequencia_hz = FREQUENCIA_HZ_PADRAO
        if idx_tsample is not None:
            for ln in dado_linhas:
                partes = ln.split()
                if idx_tsample < len(partes):
                    try:
                        periodo = float(partes[idx_tsample])
                    except ValueError:
                        continue
                    if periodo > 0:
                        frequencia_hz = round(1.0 / periodo, 6)
                        break

        primeiro_segundos: float | None = None
        segundos_anterior: float | None = None
        offset_dias = 0.0

        def _bloco_para_lote(
            colunas_valores: dict[str, list[float]], t_s_lista: list[float]
        ) -> Lote:
            arrays = [pa.array(t_s_lista, type=pa.float64())]
            nomes = ["t_s"]
            for nome in colunas:
                arrays.append(pa.array(colunas_valores[nome], type=pa.float64()))
                nomes.append(nome)
            tabela = pa.RecordBatch.from_arrays(arrays, names=nomes)
            return Lote(frequencia_hz=frequencia_hz, tabela=tabela)

        colunas_valores: dict[str, list[float]] = {nome: [] for nome in colunas}
        t_s_lista: list[float] = []

        for indice, ln in enumerate(dado_linhas):
            partes = ln.split()

            t_s: float | None = None
            if idx_time is not None and idx_time < len(partes):
                segundos = _hhmmss_para_segundos(partes[idx_time])
                if segundos is not None:
                    if primeiro_segundos is None:
                        primeiro_segundos = segundos
                    elif segundos_anterior is not None and segundos < (
                        segundos_anterior - 1e-6
                    ):
                        offset_dias += 86400.0
                    segundos_anterior = segundos
                    t_s = segundos + offset_dias - primeiro_segundos
            if t_s is None:
                # Coluna time ausente ou ilegivel nesta linha: cai pro
                # indice sobre a taxa, que nao acumula (e multiplicacao, nao
                # soma). Ver docstring do metodo.
                t_s = indice / frequencia_hz
            t_s_lista.append(t_s)

            for i, nome in enumerate(colunas):
                if i < len(partes):
                    try:
                        v = float(partes[i])
                    except ValueError:
                        v = math.nan
                else:
                    v = math.nan
                colunas_valores[nome].append(v)

            if len(t_s_lista) >= _LINHAS_POR_LOTE:
                yield _bloco_para_lote(colunas_valores, t_s_lista)
                colunas_valores = {nome: [] for nome in colunas}
                t_s_lista = []

        if t_s_lista:
            yield _bloco_para_lote(colunas_valores, t_s_lista)
