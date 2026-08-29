"""Leitor de inventario para Pro Tune TDL (a confirmar), formato_id
protune_dlf.

Correcao importante sobre a atribuicao do formato: o `.dlf` do acervo desta
maquina (`telemetria/samples-saru/amg_cup_a45.dlf`, 7 980 544 bytes) e ASCII
de ponta a ponta, o primeiro byte fora do intervalo `\\x20-\\x7e` mais
CR/LF/TAB fica no fim do arquivo (ultima linha truncada, ver abaixo). Nao ha
trecho binario.

Procedencia: a decodificacao do corpo esparso (o miolo deste leitor) e um
PORTE, so leitura, do decoder ja validado no snapshot do saru-app, funcao
`_decode_sparse_body` em
`services/telemetry-api/saru_lapanalyzer/infra/datasources/dlf_file.py`,
linhas ~174-226 do snapshot `aa94872`, com a doc
`docs/architecture/formato-dlf-esparso.md` no mesmo snapshot (77 dos 81
arquivos do acervo original decodificam com GPS caindo em Interlagos,
`Lap Number` monotonico e mediana de `Lap Distance` a -0,91% do comprimento
da pista). Este leitor reimplementa so a parte de INVENTARIO (contagem de
canal e taxa), nao a leitura de amostra.

Estrutura MEDIDA em 2026-08-29 sobre o unico `.dlf` do acervo desta maquina:

- Header textual ate a linha `#DATASTART` (medido em offset 0x89B = 2203 no
  arquivo de amostra). Campos uteis: `#V2`, `#SERIALNUMBER`, `#MAINCOMMENT`/
  `#ENDMAINCOMMENT`, `#LOGID`, `#FILTERCHANNEL`, `#CONFIGCHANNEL` (20 linhas
  do tipo `N/A, 000000000147, 000000000000`), `#UNITSYSTEM`.
- Depois de `#DATASTART`: uma linha com 138 nomes de canal separados por
  `;` (o cabecalho real tem 139 campos, o ultimo vazio por causa do `;`
  final: filtrado aqui), uma linha com 138 unidades, e 85 405 linhas de
  dado (medido: 85 406 linhas de texto apos as duas linhas de cabecalho,
  a ultima truncada no meio de um valor, sem newline final: o arquivo foi
  cortado em gravacao, nao esta corrompido no sentido de "ilegivel").

Codificacao ESPARSA das linhas de dado (o miolo do formato):

- A virgula e o separador DECIMAL (`0,124` = 0.124).
- A letra maiuscula e o separador de campo E o passo de avanco de coluna:
  `A` = +1, `B` = +2, ..., `Z` = +26. Letra dupla vale
  `26 * (len - 1) + (ultima - 'A' + 1)`.
- A primeira linha e keyframe: todos os separadores sao `A`, um valor por
  canal, na ordem do cabecalho. As linhas seguintes sao esparsas: so trazem
  os canais que MUDARAM desde a ultima escrita; o salto pula os que nao
  mudaram. O indice comeca em 0 a cada linha (a primeira leitura da linha
  cai na posicao 0, que e sempre `Datalog Time`).
- Exemplo real: `0,035A-0,971A0,124F-23,703465A...` onde `0,124` esta na
  posicao 2 e o `F` (+6) salta pra posicao 8, que e `GPS Latitude` =
  `-23,703465`.

A TAXA por canal NAO e declarada em lugar nenhum do arquivo: e derivada
contando, ao longo de TODA a varredura, quantas vezes cada posicao de canal
foi efetivamente escrita (nao quantas linhas existem: e escrita real, nao
"linha onde o valor ainda vale por persistencia"), dividido pela duracao
total (`Datalog Time` da ultima linha valida). Isso exige uma passada
completa pelo arquivo, aceitavel por ser texto: o leitor abaixo faz
streaming linha a linha e NUNCA materializa as 85 mil linhas em memoria.

Medido no arquivo de amostra: base global ~20,00 Hz (`Datalog Time` escreve
em toda linha), com canais individuais variando bem abaixo disso conforme a
config do logger (ex. `Gear Position` e `Engine Temperature` bem esparsos).

Nome de canal duplicado no proprio cabecalho: medido no arquivo de amostra,
20 dos 138 canais declarados tem o nome literal "N/A" (slots de config sem
rotulo), mas sao 20 posicoes distintas no esparso, cada uma escrita de
verdade (13 amostras cada, valor proprio). `_desambigua_nomes` sufixa com a
posicao 0-based do cabecalho ("N/A#7") so quem repete; ver a docstring da
funcao pra decisao pendente sobre a notacao do sufixo.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

import pyarrow as pa

from .base import Cabecalho, CanalBruto, ErroDeLeitura, LeitorDeInventario, Lote

_VERSAO = "0.1.0"

# Sugestao do contrato: 50 mil a 200 mil linhas por lote. O unico .dlf do
# acervo (2026-08-29) tem 85 405 linhas de dado, entao sai em 2 blocos.
_LINHAS_POR_LOTE = 50_000

_MARCADOR_DATASTART = "#DATASTART"
_TIME_CHANNEL = "Datalog Time"

# Um valor (decimal com virgula) seguido do separador, que e uma letra
# maiuscula dizendo quantas posicoes avancar desde a ultima escrita. Porte
# do mesmo regex validado no saru-app (`dlf_file.py`, `_SPARSE_TOKEN`).
_TOKEN_ESPARSO = re.compile(r"(-?\d+(?:,\d+)?)([A-Z]*)")


def _avanco(letras: str) -> int:
    """Quantas posicoes o separador avanca desde a ultima escrita.

    `A` = proxima posicao, `B` = pula 1, ... `Z` = pula 25. Salto maior que
    26 usa letra dupla (`ZG`, `ZB`): cada `Z` a esquerda vale 26 e a ultima
    letra soma o resto.
    """
    if not letras:
        return 1
    if len(letras) == 1:
        return ord(letras) - ord("A") + 1
    return 26 * (len(letras) - 1) + (ord(letras[-1]) - ord("A") + 1)


def _desambigua_nomes(nomes: list[str]) -> list[str]:
    """Desambigua nome_bruto repetido dentro do MESMO cabecalho.

    Medido no acervo (2026-08-29, amg_cup_a45.dlf): o header declara 20
    canais com o nome literal "N/A" (slots de configuracao que o logger
    nao rotulou), mas sao 20 POSICOES distintas no esparso, cada uma
    escrita de verdade (13 amostras cada, com valor proprio, nao e a mesma
    leitura repetida). Nome_bruto colidindo vira coluna ambigua: Arrow
    aceita RecordBatch com nome de coluna repetido, mas pandas/DuckDB
    desempatam mal (pandas devolve as duas colunas empilhadas como se
    fossem uma serie 2D em vez de erro), e o catalogo (canal_gravado) nao
    consegue diferenciar as 20 series por nome. Desambigua so quem repete,
    sufixando com a posicao (indice 0-based no cabecalho completo):
    "N/A" na posicao 7 vira "N/A#7". Nome que aparece uma vez so, intacto.

    # DECISAO PENDENTE (Lucas): a alternativa a essa desambiguacao seria
    # (b) descartar os canais repetidos (perde os 13 registros de cada) ou
    # (c) fundir todos os "N/A" numa serie so (inventa uma correlacao
    # entre posicoes fisicamente distintas do arquivo, que e exatamente o
    # tipo de invencao que o contrato probe). Sufixar por posicao foi a
    # conservadora: nao perde amostra, nao mistura canal. O sufixo
    # `#<posicao>` e convencao desta PoC (o fabricante nao declara essa
    # numeracao em lugar nenhum do arquivo), entao fica marcado aqui pro
    # Lucas decidir se prefere outra notacao antes de virar canal_gravado.
    """
    contagem = Counter(nomes)
    return [
        f"{nome}#{i}" if contagem[nome] > 1 else nome for i, nome in enumerate(nomes)
    ]


def _le_cabecalho(fh) -> tuple[dict[str, str], list[str], list[str]]:
    """Le o header textual ate `#DATASTART` mais as duas linhas seguintes.

    Devolve (metadados, nomes_de_canal, unidades). `fh` ja esta posicionado
    no inicio do arquivo; ao final desta funcao esta logo apos a linha de
    unidades, pronto pra `fh` seguir em streaming pelas linhas de dado.
    """
    metadados: dict[str, str] = {}
    achou_datastart = False
    for linha in fh:
        bruta = linha.rstrip("\r\n")
        if bruta == _MARCADOR_DATASTART:
            achou_datastart = True
            break
        if bruta.startswith("#SERIALNUMBER"):
            partes = bruta.split(None, 1)
            if len(partes) > 1:
                metadados["numero_serie"] = partes[1].strip()
        elif bruta.startswith("#V"):
            metadados["versao_formato"] = bruta.lstrip("#")
        elif bruta.startswith("#UNITSYSTEM"):
            metadados["sistema_unidades_marcador"] = "presente"

    if not achou_datastart:
        raise ErroDeLeitura(
            "marcador #DATASTART nao encontrado: nao e um .dlf reconhecido "
            "por este leitor"
        )

    linha_nomes = fh.readline()
    linha_unidades = fh.readline()
    if not linha_nomes or not linha_unidades:
        raise ErroDeLeitura(
            "#DATASTART encontrado mas faltam as linhas de nomes/unidades "
            "de canal logo depois"
        )

    nomes_brutos = linha_nomes.rstrip("\r\n").split(";")
    unidades_brutas = linha_unidades.rstrip("\r\n").split(";")

    # O `;` final do cabecalho produz um campo vazio a mais: filtrado aqui,
    # nao no meio (posicao importa pro pareamento nome<->unidade, mas o
    # vazio esta sempre no fim, depois do ultimo canal real).
    nomes = [n for n in nomes_brutos if n]
    unidades = unidades_brutas[: len(nomes)]
    # Desambigua ANTES de devolver: inspecionar() e ler() chamam esta
    # funcao pro mesmo arquivo e tem que enxergar exatamente os mesmos
    # nomes, senao o nome_bruto do Lote diverge do CanalBruto que
    # inspecionar() catalogou (ver docstring de _desambigua_nomes).
    nomes = _desambigua_nomes(nomes)

    return metadados, nomes, unidades


def _parse_hora_gps(valor_hora: str, valor_data: str) -> str | None:
    """Converte `GPS UTC Time` (hhmmss.ss) + `GPS UTC Date` (ddmmyy) do
    primeiro registro em texto legivel. Nao e ISO por decisao de manter o
    mesmo estilo simples usado no leitor do .xrk (data/hora crua concatenada).
    """
    try:
        hhmmss = valor_hora.split(".")[0].zfill(6)
        hh, mm, ss = hhmmss[0:2], hhmmss[2:4], hhmmss[4:6]
        ddmmyy = valor_data.zfill(6)
        dd, mo, yy = ddmmyy[0:2], ddmmyy[2:4], ddmmyy[4:6]
        ano = f"20{yy}"
        return f"{dd}/{mo}/{ano} {hh}:{mm}:{ss}"
    except (IndexError, ValueError):
        return None


def _inspecionar_arquivo(caminho: Path) -> Cabecalho:
    try:
        fh_ctx = caminho.open(encoding="latin-1", errors="replace")
    except OSError as exc:
        raise ErroDeLeitura(f"{caminho}: nao foi possivel abrir: {exc}") from exc

    with fh_ctx as fh:
        metadados, nomes, unidades = _le_cabecalho(fh)
        n_ch = len(nomes)
        if n_ch == 0:
            raise ErroDeLeitura(f"{caminho}: nenhum canal declarado apos #DATASTART")

        idx_tempo = nomes.index(_TIME_CHANNEL) if _TIME_CHANNEL in nomes else None
        idx_gps_hora = nomes.index("GPS UTC Time") if "GPS UTC Time" in nomes else None
        idx_gps_data = nomes.index("GPS UTC Date") if "GPS UTC Date" in nomes else None

        contagem = [0] * n_ch
        ultimo_tempo: float | None = None
        primeira_hora_gps: str | None = None
        primeira_data_gps: str | None = None
        n_linhas = 0
        n_linhas_vazias_ou_malformadas = 0

        for linha in fh:
            texto = linha.strip()
            if not texto:
                continue
            n_linhas += 1
            idx = 0
            escreveu = False
            valores_da_linha: dict[int, str] | None = None
            if n_linhas == 1 or idx_gps_hora is not None:
                valores_da_linha = {}
            for token in _TOKEN_ESPARSO.finditer(texto):
                valor, separador = token.group(1), token.group(2)
                if idx < n_ch:
                    contagem[idx] += 1
                    escreveu = True
                    if idx == idx_tempo:
                        try:
                            ultimo_tempo = float(valor.replace(",", "."))
                        except ValueError:
                            pass
                    if valores_da_linha is not None:
                        valores_da_linha[idx] = valor
                idx += _avanco(separador)
            if not escreveu:
                n_linhas_vazias_ou_malformadas += 1
                continue
            if (
                primeira_hora_gps is None
                and valores_da_linha is not None
                and idx_gps_hora is not None
                and idx_gps_data is not None
                and idx_gps_hora in valores_da_linha
                and idx_gps_data in valores_da_linha
            ):
                primeira_hora_gps = valores_da_linha[idx_gps_hora]
                primeira_data_gps = valores_da_linha[idx_gps_data]

    if n_linhas == 0:
        raise ErroDeLeitura(f"{caminho}: nenhuma linha de dado apos o cabecalho")

    duracao_s = ultimo_tempo if ultimo_tempo and ultimo_tempo > 0 else None

    canais = []
    for i, nome in enumerate(nomes):
        if contagem[i] == 0:
            # Canal declarado no cabecalho mas nunca escrito: nao vira
            # CanalBruto (taxa positiva e invariante do contrato). Fica
            # registrado em bruto pra nao sumir em silencio.
            continue
        freq = contagem[i] / duracao_s if duracao_s else float(contagem[i]) / n_linhas
        unidade = (
            unidades[i]
            if i < len(unidades) and unidades[i] not in ("", "N/A")
            else None
        )
        canais.append(
            CanalBruto(
                nome_bruto=nome,
                frequencia_hz=freq,
                n_amostras=contagem[i],
                unidade_declarada=unidade,
            )
        )

    canais_sem_escrita = [nomes[i] for i in range(n_ch) if contagem[i] == 0]

    bruto: dict[str, str] = dict(metadados)
    bruto["n_canais_declarados"] = str(n_ch)
    bruto["n_canais_com_amostra"] = str(len(canais))
    bruto["n_linhas_dado"] = str(n_linhas)
    bruto["n_linhas_sem_escrita"] = str(n_linhas_vazias_ou_malformadas)
    if canais_sem_escrita:
        bruto["canais_sem_escrita"] = ";".join(canais_sem_escrita)
    if duracao_s is None:
        bruto["duracao_indisponivel"] = (
            "canal Datalog Time ausente ou zerado, taxa estimada por linha"
        )

    capturado_em = None
    if primeira_hora_gps and primeira_data_gps:
        capturado_em = _parse_hora_gps(primeira_hora_gps, primeira_data_gps)

    return Cabecalho(
        formato_id="protune_dlf",
        leitor_versao=_VERSAO,
        canais=tuple(canais),
        capturado_em=capturado_em,
        duracao_s=duracao_s,
        # O .dlf nao declara pista em lugar nenhum do header nem do corpo:
        # nao inferir de coordenada GPS, e o mesmo buraco do B2.
        venue_declarado=None,
        bruto=bruto,
    )


def _ler_grade(caminho: Path, cab: Cabecalho) -> Iterator[Lote]:
    """Le o corpo esparso em blocos e emite `Lote`(s) na taxa da grade."""
    # DECISAO PENDENTE (Lucas): o arquivo e uma grade unica de ~20 Hz onde
    # cada linha e uma escrita real (nao todo canal muda toda linha), com
    # canal variando de 20,00 Hz (Datalog Time) a 0,13 Hz (Engine
    # Temperature). Tres formas de expor isso como Lote:
    #   (a) [IMPLEMENTADO] um Lote so, na taxa da grade (a de Datalog Time,
    #       medida em `frequencia_hz` do CanalBruto homonimo), com os 138
    #       canais (os que tem pelo menos uma escrita, que e o mesmo
    #       conjunto que inspecionar() ja devolve em cab.canais) e NaN nas
    #       linhas em que aquele canal nao foi escrito. Preserva o
    #       alinhamento temporal linha a linha e nao inventa valor nenhum
    #       (a lacuna fica NaN, nunca repete o ultimo valor conhecido); o
    #       custo e um Parquet mais esparso (a maioria das celulas de
    #       canais lentos vira NaN).
    #   (b) um Lote por canal, cada um so com as linhas em que aquele canal
    #       de fato aparece, na taxa efetiva medida dele. Mais fiel a taxa
    #       nativa de cada canal, mas gera ate 138 series (uma linha de
    #       serie_amostral por canal) pra um arquivo so, e cada serie fica
    #       curta e sem `t_s` compartilhado com o resto do carro.
    #   (c) agrupar os canais por faixa de taxa arredondada (ex. 20, 10, 5,
    #       1 Hz). Mais compacto que (a), mas arredondar a taxa medida e
    #       mentir sobre a taxa real do canal, o que a regra dura do
    #       contrato ("valores em unidade nativa, sem conversao" e "nunca
    #       preencha lacuna sem dizer") desaconselha por analogia.
    # Implementado (a): e a que nao fabrica valor nenhum e mantem os 138
    # canais no mesmo eixo de tempo, que e o requisito mais forte do
    # contrato (t_s obrigatorio e alinhavel). Trade-off registrado acima
    # pro Lucas decidir se (b)/(c) valem a pena depois.

    nomes = [c.nome_bruto for c in cab.canais]
    if not nomes:
        return
    if _TIME_CHANNEL not in nomes:
        raise ErroDeLeitura(
            f"{caminho}: canal {_TIME_CHANNEL} nao tem amostra, sem eixo de "
            "tempo pra montar a grade"
        )
    freq_grade = next(
        c.frequencia_hz for c in cab.canais if c.nome_bruto == _TIME_CHANNEL
    )
    idx_col = {nome: i for i, nome in enumerate(nomes)}

    try:
        fh_ctx = caminho.open(encoding="latin-1", errors="replace")
    except OSError as exc:
        raise ErroDeLeitura(f"{caminho}: nao foi possivel abrir: {exc}") from exc

    with fh_ctx as fh:
        _, nomes_completos, _ = _le_cabecalho(fh)
        if _TIME_CHANNEL not in nomes_completos:
            raise ErroDeLeitura(
                f"{caminho}: {_TIME_CHANNEL} sumiu entre inspecionar() e ler(): "
                "cabecalho mudou no meio da leitura"
            )
        idx_completo_tempo = nomes_completos.index(_TIME_CHANNEL)
        # Mapa posicao-no-esparso (contra TODOS os canais declarados, e o
        # espaco que os saltos de letra navegam) -> posicao na coluna
        # reduzida (so os canais com amostra, que e o schema do Lote).
        posicao_reduzida = {
            nomes_completos.index(nome): idx_col[nome]
            for nome in nomes
            if nome in nomes_completos
        }

        colunas_valores: dict[str, list[float]] = {nome: [] for nome in nomes}
        t_s_lista: list[float] = []

        for numero_linha, linha in enumerate(fh, start=1):
            texto = linha.strip()
            if not texto:
                continue

            idx = 0
            valor_tempo: float | None = None
            valores_da_linha: dict[int, float] = {}
            for token in _TOKEN_ESPARSO.finditer(texto):
                valor_bruto, separador = token.group(1), token.group(2)
                try:
                    valor = float(valor_bruto.replace(",", "."))
                except ValueError:
                    valor = math.nan
                if idx == idx_completo_tempo:
                    valor_tempo = valor
                if idx in posicao_reduzida:
                    valores_da_linha[posicao_reduzida[idx]] = valor
                idx += _avanco(separador)

            if valor_tempo is None:
                # Linha sem Datalog Time: nao da pra situar na grade de
                # tempo. Medido no arquivo real, isso so acontece na ultima
                # linha truncada (arquivo cortado em gravacao); levanta com
                # o numero da linha pra facilitar o diagnostico, em vez de
                # inventar um t_s ou descartar a linha em silencio.
                raise ErroDeLeitura(
                    f"{caminho}: linha de dado {numero_linha} sem "
                    f"{_TIME_CHANNEL}, sem como situar na grade de tempo"
                )

            t_s_lista.append(valor_tempo)
            for nome in nomes:
                pos = idx_col[nome]
                colunas_valores[nome].append(valores_da_linha.get(pos, math.nan))

            if len(t_s_lista) >= _LINHAS_POR_LOTE:
                yield _bloco_dlf_para_lote(
                    colunas_valores, t_s_lista, nomes, freq_grade
                )
                colunas_valores = {nome: [] for nome in nomes}
                t_s_lista = []

    if t_s_lista:
        yield _bloco_dlf_para_lote(colunas_valores, t_s_lista, nomes, freq_grade)


def _bloco_dlf_para_lote(
    colunas_valores: dict[str, list[float]],
    t_s_lista: list[float],
    nomes: list[str],
    freq_grade: float,
) -> Lote:
    arrays = [pa.array(t_s_lista, type=pa.float64())]
    nomes_saida = ["t_s"]
    for nome in nomes:
        arrays.append(pa.array(colunas_valores[nome], type=pa.float64()))
        nomes_saida.append(nome)
    tabela = pa.RecordBatch.from_arrays(arrays, names=nomes_saida)
    return Lote(frequencia_hz=freq_grade, tabela=tabela)


class LeitorDlf(LeitorDeInventario):
    formato_id = "protune_dlf"
    versao = _VERSAO
    suporta_amostra = True

    def inspecionar(self, caminho: Path) -> Cabecalho:
        return _inspecionar_arquivo(caminho)

    def ler(self, caminho: Path) -> Iterator[Lote]:
        """Le o corpo esparso e emite Lote(s) na taxa da grade (~20 Hz).

        Chama `inspecionar()` primeiro pra saber quais canais tem amostra
        (mesmo conjunto e mesmo `nome_bruto` do inventario, condicao do
        contrato pra o canal nao ficar orfao) e qual a taxa da grade (a
        taxa medida de `Datalog Time`, o canal que a doc do modulo confirma
        escrever em toda linha). Ver `_ler_grade` pra decisao de desenho
        completa (# DECISAO PENDENTE (Lucas), tres alternativas).

        `t_s` sai direto do valor de `Datalog Time` decodificado naquela
        linha (ja e segundos desde o inicio da captura, medido: primeira
        linha 0,000). Nao ha acumulo: cada linha traz o valor absoluto que
        o logger gravou, sem soma.

        Toda celula vira float64. Celula nao escrita naquela linha (o
        canal nao mudou desde a ultima escrita, ou nunca foi escrito ali)
        vira NaN: NUNCA repete o ultimo valor conhecido em silencio, essa e
        a regra dura do contrato contra preencher lacuna sem dizer.
        """
        cab = self.inspecionar(caminho)
        yield from _ler_grade(caminho, cab)
