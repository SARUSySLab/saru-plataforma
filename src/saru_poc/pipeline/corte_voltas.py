"""Etapa 5: corte de voltas.

O plano descreve esta etapa como "corte por GPS", pensando no caminho FuelTech,
onde o log de ECU e stream continuo sem beacon nenhum. Medindo o acervo em
29/08 a realidade veio diferente, e a etapa nasceu maior: 56 gravacoes carregam
o numero da volta como CANAL da propria amostra, 31 carregam um pulso de
beacon, 21 trazem os tempos de beacon no sidecar `.ldx`, e apenas 10 tem
latitude e longitude. Cortar so por GPS entregaria volta em 3 gravacoes de 198,
e as 3 tem o GPS em outra pista (ver `_por_gps`).

Cascata, decisao do Lucas (29/08), nesta ordem:

  1. canal de volta dentro da amostra (contador ou pulso);
  2. tempos de beacon declarados no metadata do sidecar `.ldx`;
  3. cruzamento da linha de chegada por GPS;
  4. nao corta, com o motivo gravado.

O canal vem antes do sidecar porque vive no mesmo eixo `t_s` da serie: o corte
cai exatamente onde a amostra esta. O `.ldx` e arquivo irmao com relogio
proprio (o acervo tem caso de 299,98 s declarados no `.ldx` contra 416,96 s no
`.ld` irmao), e alinhar os dois seria suposicao que ninguem provou ainda.

Regra que atravessa tudo, herdada do B2: **nao cortar e resultado, com motivo.**
Nenhum caminho aqui inventa volta a partir de default.

Volta e o intervalo ENTRE duas passagens consecutivas. O trecho antes da
primeira passagem (out-lap) e o depois da ultima (in-lap) nao viram volta: sao
pedacos de volta, e contar pedaco como volta e o que estraga toda media depois.
N passagens produzem N-1 voltas, sempre.

Numeracao: as voltas saem 1..N na ordem do tempo, ordinal do corte, nao o
numero que o arquivo escreveu. O contador do arquivo comeca em 0 ou 1 conforme
o logger e conta o out-lap junto; renumerar aqui mantem "volta 1" significando
a mesma coisa nas quatro origens. E escolha, nao verdade: se o piloto reclamar
que a volta 3 dele e a nossa 2, o lugar de corrigir e este comentario.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import pairwise

import numpy as np

from .leitura import escolher_canal, ler_colunas, par_gps

# Versao do algoritmo de cada caminho. Entra em `volta.metodo_versao`: trocar o
# corte produz fronteira diferente da mesma captura, e as duas so convivem
# enquanto estiver escrito qual produziu qual.
METODO_CONTADOR = "canal_contador-1"
METODO_PULSO = "canal_pulso-1"
METODO_LDX = "ldx_beacon-1"
METODO_GPS = "gate_perpendicular-1"
# Sufixo de metodo quando o instante grosseiro foi realinhado contra uma serie
# de maior taxa. Entra somado ao metodo de base ("canal_contador-1+refino...")
# porque a proveniencia sao as duas coisas: quem achou a passagem e quem a
# posicionou no tempo.
METODO_REFINO = "refino_correlacao-1"

# Erro de instante que o corte de volta pode ter, e acima do qual o corte sai
# com alerta.
#
# Valor ratificado por Vitor em 2026-09-13, medicao no acervo pendente
# (E-RN-02). Registro em `docs/requisitos/06-validacao.md`, item 7. Duas coisas
# ficam a confirmar, e estao escritas aqui pra nao morarem so no documento:
#
#   1. a ratificacao nao veio com tabela de medicao, que e o que E-RN-02 pede;
#   2. o texto ratificado fala em GPS de 1 Hz, e este modulo aplica o mesmo
#      numero ao CANAL DE VOLTA de 1 Hz, que e outro degrau da cascata. E
#      analogia, nao medicao.
#
# Coerencia que vale registrar: 0,05 s e o periodo de uma serie de 20 Hz, que e
# a taxa da maioria das series de velocidade do acervo. A tolerancia ratificada
# e o teto fisico do metodo coincidem. Isso e bom sinal, nao e a medicao.
TOLERANCIA_CORTE_S = 0.05
ALERTA_CORTE_S = 0.20

# Janela de alinhamento: quanto sinal, depois da passagem, entra na comparacao
# entre a volta k e a volta ancora. A MEDIR NO ACERVO.
#
# A primeira versao comparava a VOLTA INTEIRA, e isso so vale quando todas as
# voltas duram o mesmo, que era a hipotese escondida na fixture. Com duracoes de
# 87,3 / 88,9 / 86,4 / 87,9 s o erro maximo subia de 0,60 s (o 1 Hz cru) para
# 1,35 s: a volta mais lenta percorre a mesma pista em mais tempo, o sinal fica
# esticado, e comparar uma volta inteira contra outra de duracao diferente
# alinha o ERRO DE RITMO em vez da posicao na pista. Quanto mais longe da
# passagem, mais estica; por isso a janela e curta e ancorada na passagem.
#
# 2 s medidos no contraexemplo sintetico: com a guarda de residuo abaixo,
# qualquer janela de 1 a 4 s deixa de piorar o 1 Hz em todos os quatro cenarios,
# e 1 a 2 s dao o menor erro. O numero definitivo sai da medicao no acervo.
JANELA_ALINHAMENTO_S = 2.0

# Residuo maximo que ainda conta como alinhamento. A MEDIR NO ACERVO.
#
# Raiz do erro quadratico do melhor encaixe, dividida pelo desvio padrao do
# proprio sinal de referencia, entao e adimensional e nao depende da unidade do
# canal. Acima disso as duas janelas nao descrevem o mesmo pedaco de pista, e a
# passagem fica com o instante grosseiro em vez de ser deslocada por um encaixe
# que nao encaixa.
#
# No contraexemplo sintetico as passagens que convergem ficam em 0,000 a 0,089 e
# a unica que diverge (a volta com parada no meio) da 0,338. 0,15 fica entre as
# duas com folga dos dois lados. O numero definitivo sai da medicao no acervo.
RESIDUO_MAXIMO_ALINHAMENTO = 0.15

# Canais que contam volta por VALOR: a volta vira quando o valor muda. "Laps
# Left" e regressivo e serve igual, e a transicao que marca, nao o sentido.
CANAIS_CONTADOR = ("Lap Number", "lap_number", "LapNumber")

# Canais que marcam volta por PULSO: a volta vira na borda de subida (zero para
# nao-zero).
CANAIS_PULSO = ("Beacon", "LAP_BEACON", "Beacon (Internal)")

# Dois canais que PARECEM pertencer as listas acima e ficaram de fora, os dois
# por medicao no acervo em 29/08, nao por gosto:
#
# "Beacon Code" carrega o CODIGO do transponder, nao um pulso. Medido: 2.559
# valores distintos indo ate 65535 e 1.394 bordas de subida em 404 s. A guarda
# de densidade abaixo rejeitaria o caso ruidoso, mas nao o caso quieto (um
# arquivo com 3 bordas espurias cortaria 2 voltas erradas em silencio), e volta
# errada e pior que volta ausente.
#
# "Lap Time" e o tempo da volta anterior reescrito pelo logger, entao transicao
# ali nao e passagem. "Laps Left" entrou como contador regressivo na primeira
# versao e saiu na medicao: no acervo ele oscila entre 98 e 258 subindo e
# descendo, 630 transicoes em 640 s. Nao e volta que resta, e outra coisa com
# nome parecido.
#
# Nome igual nao garante semantica igual, e por isso a guarda de densidade
# abaixo nao e paranoia: um "Lap Number" do acervo vai de 28 a 2572 com 136
# transicoes em 640 s. O nome e o mesmo do canal que corta 5 voltas certas em
# outro arquivo; o conteudo nao tem nada a ver. Vocabulario por nome bruto e
# divida conhecida desta etapa: o certo e o canal virar canonico e passar pelo
# mapa, como todo o resto.

# Tempo minimo entre duas passagens. Serve de debounce: ruido de GPS na linha e
# pulso que dura mais de uma amostra produzem cruzamento repetido no mesmo
# instante fisico. 10 s fica bem abaixo da volta mais curta que existe no
# dominio (kart de 1,0 km roda 40 s) e bem acima de qualquer repique.
MIN_VOLTA_S = 10.0

# Teto de velocidade MEDIA de volta usado para derivar o tempo minimo plausivel
# quando o comprimento do layout e conhecido. 320 km/h de MEDIA e absurdo para
# qualquer carro de track day (a media de um GT3 em Interlagos fica perto de
# 160), entao ele so corta o que e fisicamente impossivel, nunca volta rapida
# de verdade.
#
# Por que isto existe: o `MIN_VOLTA_S` fixo de 10 s nasceu do kartodromo, onde
# a volta tem 40 s. Aplicado ao Nelson Piquet (5.384 m), ele deixou passar 22
# "voltas" de 11 a 30 s vindas de beacon repetido, e uma delas virou "melhor
# volta" de 11,6 s no painel do piloto. Volta de 11 s em 5,4 km seria 1.670
# km/h. O comprimento da pista ja estava no banco; era so usar.
TETO_VELOCIDADE_MEDIA_KMH = 320.0


def min_volta_por_comprimento(comprimento_m: float | None) -> float:
    """Piso de tempo de volta para a pista, ou o piso generico se nao souber."""
    if not comprimento_m or comprimento_m <= 0:
        return MIN_VOLTA_S
    return max(MIN_VOLTA_S, comprimento_m / (TETO_VELOCIDADE_MEDIA_KMH / 3.6))

# Raio do gate em volta da coordenada de referencia do layout. 30 m e largo o
# bastante pra pegar a passagem a 250 km/h amostrada a 10 Hz (6,9 m entre
# amostras) e estreito o bastante pra nao capturar o box na maioria dos
# tracados.
RAIO_GATE_M = 30.0

R_TERRA_M = 6_371_000.0


@dataclass(frozen=True)
class Volta:
    """Uma volta fechada entre duas passagens."""

    numero: int
    t_inicio_s: float
    t_fim_s: float

    @property
    def tempo_s(self) -> float:
        return self.t_fim_s - self.t_inicio_s


@dataclass
class Corte:
    """O resultado da etapa pra uma gravacao. Sem volta e resultado valido."""

    gravacao_id: str
    voltas: list[Volta] = field(default_factory=list)
    origem: str | None = None
    metodo_versao: str | None = None
    motivo: str | None = None
    # De qual canal e de que taxa saiu o corte. A taxa e o teto da precisao do
    # tempo de volta: `Lap Number` do MoTeC vive numa serie de 1 Hz, e volta
    # cortada ali sai com tempo inteiro em segundos.
    fonte: str | None = None
    frequencia_hz: float | None = None
    # Por onde a cascata passou antes de chegar aqui. E o que responde "por que
    # essa gravacao nao cortou" sem precisar reproduzir a execucao.
    tentativas: list[str] = field(default_factory=list)
    # Refino do instante contra a serie de maior taxa (excecao 5i, issue #6).
    #
    # `resolucao_s` e o passo da varredura, que e o periodo da serie usada como
    # apoio. E RESOLUCAO, nao erro: diz a menor diferenca que o alinhamento
    # consegue distinguir, e nao quanto o instante ainda esta errado. Enquanto o
    # alinhamento for por janela, o erro de instante que PIL-RNF-10 cobra NAO e
    # medido, e chamar a resolucao de erro faria o criterio passar por
    # construcao. Ver a docstring de `refinar_passagens`.
    #
    # `motivo_refino` diz por que NAO refinou, ou o que ficou de fora quando
    # refinou em parte. Nao refinar e resultado, com motivo, como todo o resto
    # desta etapa.
    refinado: bool = False
    resolucao_s: float | None = None
    motivo_refino: str | None = None

    @property
    def cortou(self) -> bool:
        return bool(self.voltas)

    @property
    def dispersao(self) -> float:
        """Razao entre a volta mais longa e a mais curta desta gravacao.

        Nao decide nada: e sonda. Sessao real varia com trafego e bandeira, mas
        volta de 11 s ao lado de uma de 205 s na mesma captura e canal errado
        lido como se fosse volta, nao piloto lento. Quem decide validade e a
        etapa 7, que e onde in-lap, out-lap e outlier de ritmo ja moram; aqui a
        gravacao suspeita so aparece no relatorio pra ser olhada.
        """
        if not self.voltas:
            return 0.0
        tempos = [v.tempo_s for v in self.voltas]
        return max(tempos) / min(tempos) if min(tempos) > 0 else float("inf")


# Acima de quantas vezes a diferenca entre a volta mais curta e a mais longa da
# mesma gravacao deixa de ser ritmo e vira suspeita de corte errado.
DISPERSAO_SUSPEITA = 3.0


@dataclass
class ResumoCorte:
    cortadas: int = 0
    nao_cortadas: int = 0
    ja_cortadas: int = 0
    voltas: int = 0
    por_metodo: dict[str, int] = field(default_factory=dict)
    por_motivo: dict[str, int] = field(default_factory=dict)
    # Taxa da serie que produziu o corte. Fica no resumo porque e o teto da
    # precisao do tempo de volta, e 1 Hz nao serve pro funil prometer decimo.
    por_taxa: dict[str, int] = field(default_factory=dict)
    suspeitas: list[tuple[str, float]] = field(default_factory=list)


# --- motor puro ----------------------------------------------------------
# Nada daqui pra baixo conhece banco nem arquivo: recebe vetor, devolve
# instante. E o que permite testar o corte contra tracado sintetico sem subir
# Postgres.


def passagens_de_contador(t_s: np.ndarray, valores: np.ndarray) -> list[float]:
    """Instantes em que um canal contador de volta muda de valor."""
    if len(t_s) < 2:
        return []
    muda = np.flatnonzero(np.diff(valores) != 0) + 1
    return [float(t_s[i]) for i in muda]


def passagens_de_pulso(t_s: np.ndarray, valores: np.ndarray) -> list[float]:
    """Instantes de borda de subida (zero para nao-zero) de um canal de pulso."""
    if len(t_s) < 2:
        return []
    anterior = valores[:-1]
    atual = valores[1:]
    sobe = np.flatnonzero((anterior == 0) & (atual != 0)) + 1
    return [float(t_s[i]) for i in sobe]


def passagens_de_beacons_ldx(bruto: str) -> list[float]:
    """Converte `beacons_time_us_raw` do `.ldx` em segundos.

    O campo vem como lista separada por virgula em notacao cientifica, em
    microssegundos: "6.1519e+07,1.81398e+08,2.99982e+08".
    """
    instantes = []
    for pedaco in bruto.split(","):
        pedaco = pedaco.strip()
        if not pedaco:
            continue
        try:
            instantes.append(float(pedaco) / 1e6)
        except ValueError:
            return []
    return sorted(instantes)


def _para_metros(
    lat: np.ndarray, lon: np.ndarray, lat0: float, lon0: float
) -> tuple[np.ndarray, np.ndarray]:
    """Projecao equiretangular local, com origem na referencia do layout.

    Erro de projecao a 30 m do centro e da ordem de milimetros, muito abaixo da
    precisao do proprio GPS. Nao vale carregar pyproj pra isso.
    """
    k = math.cos(math.radians(lat0))
    x = np.radians(lon - lon0) * R_TERRA_M * k
    y = np.radians(lat - lat0) * R_TERRA_M
    return x, y


def passagens_por_gps(
    t_s: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    ref_lat: float,
    ref_lon: float,
    *,
    raio_m: float = RAIO_GATE_M,
    min_volta_s: float = MIN_VOLTA_S,
) -> tuple[list[float], str | None]:
    """Cruzamentos da linha de chegada, pelo gate circular mais o sinal.

    Decisao do Lucas (29/08): `layout.ref_lat`/`ref_lon` e um PONTO, e ponto
    nao define linha. O raio acha os candidatos, e a perpendicular ao rumo
    medio de passagem decide o instante e o sentido:

      1. fica com os pontos a menos de `raio_m` da referencia;
      2. agrupa os pontos contiguos: cada grupo e uma aproximacao da linha;
      3. estima o rumo de cada grupo e tira o rumo medio de todos, que e o
         sentido em que a pista cruza aquele ponto;
      4. projeta cada ponto no rumo medio: o sinal diz de que lado da linha o
         carro esta, e a troca de negativo pra positivo e o cruzamento;
      5. interpola o instante entre as duas amostras que trocam de sinal, o
         que da resolucao melhor que o periodo de amostragem.

    O sentido e o que separa esta funcao de um gate circular puro: passagem no
    contra-fluxo (box, retorno, carro parado balancando em cima da linha) nao
    conta como volta.

    Devolve (instantes, motivo). Com motivo preenchido, a lista vem vazia: nao
    resolver e resultado, nunca default.
    """
    if len(t_s) < 2:
        return [], "serie com menos de 2 amostras"

    x, y = _para_metros(lat, lon, ref_lat, ref_lon)
    dist = np.hypot(x, y)
    dentro = dist <= raio_m
    if not dentro.any():
        # E aqui que a incoerencia entre o GPS e a pista resolvida aparece. No
        # acervo, as 3 gravacoes GT7 que declaram "Autodromo de Interlagos" tem
        # o GPS em 52,83 N / 1,38 W (Donington Park), 9.500 km do ref do
        # layout. Sem esta mensagem, elas sairiam como "sessao sem volta".
        #
        # Medido depois, na etapa 6, e vale registrar aqui pra ninguem tirar a
        # conclusao errada: nessas 3 gravacoes a PISTA esta certa e o GPS esta
        # errado, nao o contrario. A distancia percorrida por volta (canal e
        # integral da velocidade, que concordam entre si) da 4.217 m contra
        # 4.309 m de Interlagos, razao 0,979, enquanto Donington tem 4.020 m. O
        # exportador do GT7 emite coordenada de outro lugar. Ou seja: gate
        # calado nao autoriza declarar a pista errada, so declarar que o GPS
        # nao serve pra cortar volta neste arquivo.
        return [], (
            f"GPS nunca passa a menos de {raio_m:.0f} m da referencia do layout "
            f"(mais perto: {dist.min() / 1000:.1f} km)"
        )

    indices = np.flatnonzero(dentro)
    quebras = np.flatnonzero(np.diff(indices) > 1) + 1
    grupos = np.split(indices, quebras)

    # Rumo de cada grupo: deslocamento do primeiro ao ultimo ponto dele. Grupo
    # de um ponto so nao tem rumo e nao vota.
    rumos = []
    for g in grupos:
        if len(g) < 2:
            continue
        dx = x[g[-1]] - x[g[0]]
        dy = y[g[-1]] - y[g[0]]
        norma = math.hypot(dx, dy)
        if norma > 0:
            rumos.append((dx / norma, dy / norma))
    if not rumos:
        return [], "GPS entra no gate mas nao ha deslocamento pra estimar o rumo"

    ux = sum(r[0] for r in rumos)
    uy = sum(r[1] for r in rumos)
    norma = math.hypot(ux, uy)
    if norma == 0:
        # Passagens em sentidos exatamente opostos se anulam. Acontece em
        # tracado de ida e volta (arrancada, subida de montanha), onde "linha de
        # chegada" nao e a mesma coisa que aqui.
        return [], "rumos de passagem se cancelam: tracado nao parece circuito"
    ux, uy = ux / norma, uy / norma

    lado = x * ux + y * uy
    instantes: list[float] = []
    for g in grupos:
        for i, j in pairwise(g):
            if lado[i] < 0 <= lado[j]:
                # Interpolacao linear no cruzamento do zero.
                fracao = (0.0 - lado[i]) / (lado[j] - lado[i])
                instantes.append(float(t_s[i] + fracao * (t_s[j] - t_s[i])))

    if not instantes:
        return [], "GPS entra no gate mas nunca cruza a linha no sentido da pista"
    return _debounce(sorted(instantes), min_volta_s), None


def _debounce(instantes: list[float], min_volta_s: float) -> list[float]:
    """Descarta passagem que cai perto demais da anterior pra ser outra volta."""
    limpos: list[float] = []
    for t in instantes:
        if not limpos or (t - limpos[-1]) >= min_volta_s:
            limpos.append(t)
    return limpos


def voltas_de_passagens(
    instantes: list[float], *, min_volta_s: float = MIN_VOLTA_S
) -> list[Volta]:
    """Passagens viram voltas: N passagens, N-1 voltas."""
    limpos = _debounce(sorted(instantes), min_volta_s)
    return [
        Volta(numero=n, t_inicio_s=a, t_fim_s=b)
        for n, (a, b) in enumerate(pairwise(limpos), start=1)
    ]


def _densidade_plausivel(instantes: list[float], duracao_s: float) -> bool:
    """Canal que muda mais do que caberia em voltas nao e canal de volta.

    Guarda contra usar como corte um canal que so parece contador (tempo de
    volta reescrito a cada amostra, contador de amostra, ruido em float).
    """
    if duracao_s <= 0:
        return False
    teto = duracao_s / MIN_VOLTA_S + 2
    return len(instantes) <= teto


@dataclass(frozen=True)
class Refino:
    """O que o alinhamento conseguiu fazer com as passagens grosseiras.

    `alinhadas` e `recusadas` contam passagens depois da ancora. Passagem
    recusada fica com o instante grosseiro: o refino nunca pode entregar algo
    pior do que o canal de 1 Hz ja entregava.
    """

    instantes: list[float]
    # Passo da varredura, nao erro do instante. Ver o comentario de `Corte`.
    resolucao_s: float | None
    motivo: str | None
    alinhadas: int = 0
    recusadas: int = 0


def refinar_passagens(
    instantes: list[float],
    periodo_grosso_s: float,
    t_rapido: np.ndarray,
    v_rapido: np.ndarray,
) -> Refino:
    """Realinha passagens grosseiras contra uma serie de maior taxa.

    Excecao 5i do E-UC-01, criterio PIL-CT-58, meta PIL-RNF-10.

    O problema: o canal de volta de 1 Hz marca a passagem na primeira amostra
    DEPOIS do cruzamento, entao o instante tem ate 1 s de erro e o tempo de
    volta sai em segundo inteiro. A linha de chegada quase sempre fica numa
    reta, no ponto de maior velocidade, e o sinal rapido nao tem feicao local
    que a marque: procurar um evento perto do instante grosseiro nao teria base.

    O que a serie rapida sabe e outra coisa. A volta e quase periodica, e o
    mesmo ponto da pista produz o mesmo trecho de sinal em toda volta. Alinhar
    a volta k contra a volta ancora pelo proprio sinal mede o quanto o instante
    grosseiro esta deslocado.

    Isso tambem resolve o erro absoluto da ancora sem precisar conhece-lo. O
    tempo de volta e diferenca entre instantes: se o instante refinado da
    passagem k e o momento em que o carro esta no mesmo ponto de pista em que
    estava na ancora, a diferenca e o tempo de volta verdadeiro, qualquer que
    seja o ponto da pista em que a ancora caiu. Por isso a ancora NAO se move.

    A comparacao usa uma janela CURTA ancorada na passagem
    (`JANELA_ALINHAMENTO_S`), nao a volta inteira. Comparar volta inteira contra
    volta inteira supoe que as duas duram o mesmo, e essa hipotese e falsa em
    sessao real: volta mais lenta estica o sinal, o erro de ritmo entra no
    alinhamento e o refino piora o que o 1 Hz ja entregava. A constante tem a
    medicao pendente, e o que ela vale esta escrito na propria constante.

    A janela de busca e `[-periodo_grosso_s, +periodo_grosso_s]`, tirada do
    periodo do proprio canal grosseiro, e o passo da varredura e o periodo da
    serie rapida. Nenhum dos dois e constante escolhida a mao.

    `resolucao_s` devolve esse passo, e e RESOLUCAO, nao erro de instante. A
    primeira versao devolvia o mesmo numero chamando-o de `erro_instante_s`, e
    isso faria PIL-CT-58 e PIL-RNF-10 passarem por construcao: a grade de 0,05 s
    nao prova erro de 0,05 s. Medido no contraexemplo sintetico, com a grade em
    0,050 s o erro real de tempo de volta vai de 0,000 s no caso periodico a
    0,300 s no caso com parada no meio. O erro de instante deste metodo NAO esta
    medido, e por isso nao sai numero nenhum se dizendo erro: o que existe e a
    resolucao e o motivo.

    Passagem cujo melhor encaixe deixa residuo acima de
    `RESIDUO_MAXIMO_ALINHAMENTO` fica com o instante grosseiro e entra em
    `recusadas`: as duas janelas nao descrevem o mesmo pedaco de pista (volta
    com parada no meio, por exemplo), e deslocar por um encaixe que nao encaixa
    seria trocar erro conhecido por erro inventado.

    Nada refinado devolve os instantes como entraram, com motivo. Refinado em
    parte devolve a lista com o que deu, e o motivo conta quantas ficaram para
    tras: nao refinar e resultado, e refinar pela metade tambem.
    """
    if len(instantes) < 2:
        return Refino(
            list(instantes), None, "menos de 2 passagens: nao ha ancora pra alinhar"
        )
    if len(t_rapido) < 2 or len(t_rapido) != len(v_rapido):
        return Refino(
            list(instantes), None, "serie de apoio vazia ou desalinhada do tempo"
        )
    if periodo_grosso_s <= 0:
        return Refino(list(instantes), None, "periodo do canal de volta nao declarado")

    passo = float(np.median(np.diff(t_rapido)))
    if passo <= 0:
        return Refino(
            list(instantes), None, "serie de apoio sem passo de tempo utilizavel"
        )
    if passo >= periodo_grosso_s:
        return Refino(
            list(instantes),
            None,
            f"serie de apoio a {1 / passo:.3g} Hz nao e mais rapida que o canal "
            f"de volta a {1 / periodo_grosso_s:.3g} Hz",
        )

    inicio_rapido, fim_rapido = float(t_rapido[0]), float(t_rapido[-1])
    janela = min(JANELA_ALINHAMENTO_S, instantes[1] - instantes[0])
    if janela < passo * 2:
        return Refino(
            list(instantes), None, "volta curta demais pra caber janela de alinhamento"
        )
    if instantes[0] + janela > fim_rapido or instantes[0] < inicio_rapido:
        return Refino(
            list(instantes), None, "serie de apoio nao cobre a janela da ancora"
        )

    u = np.arange(0.0, janela, passo)
    referencia = np.interp(instantes[0] + u, t_rapido, v_rapido)
    escala = float(referencia.std())
    if escala <= 0:
        # Sinal constante na janela (carro parado, canal travado): todo encaixe
        # da residuo zero e o alinhamento aceitaria qualquer deslocamento.
        return Refino(
            list(instantes),
            None,
            "sinal de apoio constante na janela da ancora: nao ha o que alinhar",
        )

    # Grade de candidatos. `periodo_grosso_s` de cada lado cobre o erro do
    # contador com folga (a ancora tambem esta deslocada, entao a diferenca
    # entre os dois vieses cabe no intervalo aberto de um periodo para cada
    # lado), e o passo da serie rapida e a menor diferenca que ela distingue.
    deslocamentos = np.arange(
        -periodo_grosso_s, periodo_grosso_s + passo / 2, passo, dtype=float
    )

    refinados = [instantes[0]]
    alinhadas = 0
    recusadas = 0
    for t_k in instantes[1:]:
        cabe = (
            t_k - periodo_grosso_s >= inicio_rapido
            and t_k + periodo_grosso_s + janela <= fim_rapido
        )
        if not cabe:
            refinados.append(t_k)
            recusadas += 1
            continue
        alvos = np.interp(
            (t_k + deslocamentos)[:, None] + u[None, :], t_rapido, v_rapido
        )
        erro = ((alvos - referencia[None, :]) ** 2).mean(axis=1)
        melhor = int(np.argmin(erro))
        residuo = math.sqrt(float(erro[melhor])) / escala
        if residuo > RESIDUO_MAXIMO_ALINHAMENTO:
            refinados.append(t_k)
            recusadas += 1
            continue
        refinados.append(float(t_k + deslocamentos[melhor]))
        alinhadas += 1

    if not alinhadas:
        return Refino(
            list(instantes),
            None,
            f"nenhuma das {len(instantes) - 1} passagens encaixou na janela da "
            "ancora: serie de apoio curta demais ou voltas sem sinal em comum",
            0,
            recusadas,
        )
    motivo = None
    if recusadas:
        motivo = (
            f"{recusadas} de {len(instantes) - 1} passagens ficaram com o "
            "instante grosseiro: o encaixe contra a volta ancora nao convergiu "
            "(volta com parada no meio ou ritmo muito diferente)"
        )
    return Refino(refinados, passo, motivo, alinhadas, recusadas)


# --- leitura do que ja esta no catalogo ----------------------------------


def _canais_de_volta(conn, gravacao_id: str) -> list[tuple[str, str, str, float]]:
    """(nome_bruto, uri, metodo, hz) dos canais que podem demarcar volta.

    Ordenado por TAXA decrescente, e so depois por tipo. A primeira versao
    preferia o contador ao pulso, com o argumento de que o contador ja e a
    decisao do proprio logger sobre o que conta como volta. Medindo o acervo o
    argumento caiu: `Lap Number` do MoTeC mora numa serie de 1 Hz em 51
    gravacoes, enquanto `Beacon Code` (50 Hz) e `LAP_BEACON` (100 Hz) descrevem
    a MESMA passagem com duas ordens de grandeza a mais de resolucao. Cortar
    pelo contador dava tempo de volta inteiro em segundos, e o funil promete
    decimo. A taxa e o teto da precisao, entao ela decide.

    Empate de taxa mantem o criterio antigo: contador antes de pulso.
    """
    linhas = conn.execute(
        """select cg.nome_bruto, s.uri, s.frequencia_hz
             from canal_gravado cg
             join serie_amostral s on s.id = cg.serie_id
            where cg.gravacao_id = %s and cg.nome_bruto = any(%s)""",
        (gravacao_id, list(CANAIS_CONTADOR) + list(CANAIS_PULSO)),
    ).fetchall()
    candidatos = [
        (
            nome,
            uri,
            METODO_CONTADOR if nome in CANAIS_CONTADOR else METODO_PULSO,
            float(hz),
        )
        for nome, uri, hz in linhas
    ]
    return sorted(candidatos, key=lambda c: (-c[3], c[2] != METODO_CONTADOR))


def _por_canal(conn, gravacao_id: str, corte: Corte) -> bool:
    """Degrau 1: o numero da volta esta gravado na propria amostra."""
    candidatos = _canais_de_volta(conn, gravacao_id)
    if not candidatos:
        corte.tentativas.append("canal: a gravacao nao tem canal de volta")
        return False
    # o layout ja foi resolvido na etapa 4; quando ele existe, o comprimento
    # diz qual tempo de volta e fisicamente possivel nesta pista
    linha_layout = conn.execute(
        """select l.comprimento_m from gravacao g
             join layout l on l.id = g.layout_id where g.id = %s""",
        (gravacao_id,),
    ).fetchone()
    min_volta = min_volta_por_comprimento(linha_layout[0] if linha_layout else None)

    for nome, uri, metodo, hz in candidatos:
        dados = ler_colunas(uri, [nome])
        if nome not in dados or "t_s" not in dados:
            continue
        t_s, valores = dados["t_s"], dados[nome]
        instantes = (
            passagens_de_contador(t_s, valores)
            if metodo == METODO_CONTADOR
            else passagens_de_pulso(t_s, valores)
        )
        duracao = float(t_s[-1] - t_s[0]) if len(t_s) else 0.0
        if not instantes:
            corte.tentativas.append(f"canal {nome}: sem transicao")
            continue
        if not _densidade_plausivel(instantes, duracao):
            corte.tentativas.append(
                f"canal {nome}: {len(instantes)} transicoes em {duracao:.0f} s, "
                "denso demais pra ser volta"
            )
            continue
        voltas = voltas_de_passagens(instantes, min_volta_s=min_volta)
        if not voltas:
            corte.tentativas.append(
                f"canal {nome}: {len(instantes)} passagem(ns), nenhuma volta fechada"
                f" (minimo de {min_volta:.0f} s para esta pista)"
            )
            continue
        corte.voltas = voltas
        corte.origem = "beacon"
        corte.metodo_versao = metodo
        corte.fonte = f"canal {nome}"
        corte.frequencia_hz = hz
        _refinar_corte(conn, gravacao_id, corte, hz)
        return True
    return False


def _refinar_corte(conn, gravacao_id: str, corte: Corte, hz_canal: float) -> None:
    """Realinha os instantes do degrau 1 contra a serie de velocidade, se der.

    Tres condicoes para o refino entrar, e as tres juntas sao o que fecha o
    criterio 4 da issue #6 (gravacao que ja corta bem nao pode mudar de
    instante) por construcao, e nao por promessa:

      1. o corte veio do degrau 1, o canal de volta dentro da amostra. Beacon de
         sidecar, beacon nativo do `.xrk` e GPS sao outros degraus e nao passam
         por aqui;
      2. o periodo do canal e PIOR que a tolerancia ratificada, ou seja, o canal
         tem taxa abaixo de 20 Hz. `Beacon Code` a 50 Hz e `LAP_BEACON` a 100 Hz
         reprovam aqui e saem intactos;
      3. existe serie de velocidade com taxa estritamente maior que a do canal.

    A contagem de voltas nao muda: os instantes refinados sao os MESMOS que o
    debounce ja aprovou, deslocados de menos de um periodo do canal grosseiro, e
    deslocamento dessa ordem nao junta nem separa passagem que dista pelo menos
    `min_volta_s`. Por isso as voltas sao remontadas direto, sem passar pelo
    debounce de novo: reexecutar a guarda sobre dado que ela ja aprovou so
    criaria a chance de o numero de voltas mudar por efeito colateral.
    """
    if hz_canal <= 0:
        corte.motivo_refino = "canal de volta sem taxa declarada"
        return
    if 1.0 / hz_canal <= TOLERANCIA_CORTE_S:
        corte.motivo_refino = (
            f"canal de volta a {hz_canal:g} Hz ja entrega o instante dentro da "
            f"tolerancia de {TOLERANCIA_CORTE_S:g} s"
        )
        return

    canal = escolher_canal(conn, gravacao_id, ("speed",))
    if canal is None:
        corte.motivo_refino = "sem canal de velocidade mapeado nesta gravacao"
        return
    if canal.frequencia_hz <= hz_canal:
        corte.motivo_refino = (
            f"a serie de velocidade e de {canal.frequencia_hz:g} Hz, nao e mais "
            f"rapida que o canal de volta de {hz_canal:g} Hz"
        )
        return

    dados = ler_colunas(canal.uri, [canal.nome_bruto])
    if "t_s" not in dados or canal.nome_bruto not in dados:
        corte.motivo_refino = "serie de velocidade sem as colunas esperadas"
        return

    instantes = [v.t_inicio_s for v in corte.voltas] + [corte.voltas[-1].t_fim_s]
    refino = refinar_passagens(
        instantes, 1.0 / hz_canal, dados["t_s"], canal.valores(dados)
    )
    if not refino.alinhadas:
        # Nenhuma passagem se moveu: o corte fica exatamente como estava, que e
        # o que o criterio 3 da issue #6 pede.
        corte.motivo_refino = refino.motivo
        return

    corte.voltas = [
        Volta(numero=n, t_inicio_s=a, t_fim_s=b)
        for n, (a, b) in enumerate(pairwise(refino.instantes), start=1)
    ]
    corte.refinado = True
    corte.resolucao_s = refino.resolucao_s
    corte.metodo_versao = f"{corte.metodo_versao}+{METODO_REFINO}"
    corte.fonte = (
        f"{corte.fonte} refinado contra {canal.nome_bruto} "
        f"a {canal.frequencia_hz:g} Hz"
    )
    # Refino parcial nao e silencio: as passagens que ficaram para tras saem
    # declaradas, com o instante grosseiro que ja tinham.
    corte.motivo_refino = refino.motivo
    if refino.resolucao_s is not None and refino.resolucao_s > ALERTA_CORTE_S:
        # O alerta cai sobre a RESOLUCAO, que e o que se mede. Se a propria
        # grade ja e mais grossa que o alerta, o alinhamento nao tem como
        # distinguir uma divergencia desse tamanho, e isso o piloto precisa
        # saber antes de comparar duas voltas parecidas.
        aviso = (
            f"a serie de apoio tem passo de {refino.resolucao_s:.3f} s, acima do "
            f"alerta de {ALERTA_CORTE_S:g} s: o alinhamento nao distingue "
            "divergencia menor que isso"
        )
        corte.motivo_refino = (
            f"{corte.motivo_refino}; {aviso}" if corte.motivo_refino else aviso
        )


def _por_ldx(conn, gravacao_id: str, corte: Corte) -> bool:
    """Degrau 2: os tempos de beacon declarados no sidecar `.ldx`."""
    linha = conn.execute(
        "select metadata->>'motec_ldx.beacons_time_us_raw' from gravacao where id = %s",
        (gravacao_id,),
    ).fetchone()
    bruto = linha[0] if linha else None
    if not bruto:
        corte.tentativas.append("ldx: a gravacao nao tem beacon declarado no sidecar")
        return False
    instantes = passagens_de_beacons_ldx(bruto)
    if len(instantes) < 2:
        corte.tentativas.append(
            f"ldx: {len(instantes)} beacon(s), precisa de 2 pra fechar uma volta"
        )
        return False
    voltas = voltas_de_passagens(instantes)
    if not voltas:
        corte.tentativas.append("ldx: beacons perto demais pra serem voltas")
        return False
    corte.voltas = voltas
    corte.origem = "beacon"
    corte.metodo_versao = METODO_LDX
    corte.fonte = "sidecar .ldx"
    return True


def _por_xrk(conn, gravacao_id: str, corte: Corte) -> bool:
    """Degrau 2b: beacons de volta nativos do proprio arquivo AiM.

    O `.xrk` grava um chunk LAP por volta fechada, com fim e duracao em ms; o
    `.drk` (indice do RS2) grava uma tabela de voltas equivalente, so que com
    relogio relativo ao primeiro beacon e SEM o fim da ultima volta (o ultimo
    registro fecha no desligamento do logger, e o leitor ja descarta essa
    passagem, ver aim_rs2.py). E a mesma informacao que o `.ldx` declara pro
    MoTeC, dentro do arquivo primario: nao depende de sidecar nenhum. Sem este
    degrau, um `.xrk` ou `.drk` enviado sozinho com voltas marcadas pelo
    beacon fisico saia como "sem canal de volta", que e falso. O `.xrk` vem
    primeiro na ordem porque os beacons dele vivem no MESMO relogio das series
    de amostra; num bundle com os dois, ganha quem alinha.
    """
    fontes = (
        ("aim_xrk.lap_beacons_ms", "xrk", "xrk_lap-1", "chunks LAP do proprio .xrk"),
        ("aim_drk.lap_beacons_ms", "drk", "drk_indice-1",
         "tabela de voltas do indice .drk"),
    )
    # mesmo piso do degrau de canal: beacon fisico repetido (carro cruzando a
    # linha devagar, ou o proprio logger marcando duas vezes) gerava "volta" de
    # 11 s no Nelson Piquet, que tem 5.384 m
    linha_layout = conn.execute(
        """select l.comprimento_m from gravacao g
             join layout l on l.id = g.layout_id where g.id = %s""",
        (gravacao_id,),
    ).fetchone()
    min_volta = min_volta_por_comprimento(linha_layout[0] if linha_layout else None)

    for chave, rotulo, metodo, fonte in fontes:
        linha = conn.execute(
            "select metadata->>%s from gravacao where id = %s",
            (chave, gravacao_id),
        ).fetchone()
        bruto = linha[0] if linha else None
        if not bruto:
            corte.tentativas.append(
                f"{rotulo}: a gravacao nao tem beacon de volta declarado"
            )
            continue
        try:
            instantes = [int(v) / 1000.0 for v in bruto.split(",") if v.strip()]
        except ValueError:
            corte.tentativas.append(f"{rotulo}: beacons ilegiveis no metadata")
            continue
        if len(instantes) < 2:
            corte.tentativas.append(
                f"{rotulo}: {len(instantes)} passagem(ns), precisa de 2 pra "
                "fechar uma volta"
            )
            continue
        voltas = voltas_de_passagens(instantes, min_volta_s=min_volta)
        if not voltas:
            corte.tentativas.append(
                f"{rotulo}: beacons perto demais pra serem voltas "
                f"(minimo de {min_volta:.0f} s para esta pista)"
            )
            continue
        corte.voltas = voltas
        corte.origem = "beacon"
        corte.metodo_versao = metodo
        corte.fonte = fonte
        return True
    return False


def _por_gps(conn, gravacao_id: str, corte: Corte) -> bool:
    """Degrau 3: cruzamento da linha de chegada, calculado por nos."""
    linha = conn.execute(
        """select l.id, l.ref_lat, l.ref_lon
             from gravacao g join layout l on l.id = g.layout_id
            where g.id = %s""",
        (gravacao_id,),
    ).fetchone()
    if linha is None:
        corte.tentativas.append("gps: gravacao sem layout resolvido")
        return False
    layout_id, ref_lat, ref_lon = linha
    if ref_lat is None or ref_lon is None:
        # Regra dura do B2: sem referencia nao existe corte. Hoje 19 dos 24
        # layouts do catalogo estao nesse caso, e a resposta certa e dizer isso,
        # nao chutar o meio do tracado.
        corte.tentativas.append(
            f"gps: layout {layout_id} nao tem coordenada de referencia"
        )
        return False

    par = par_gps(conn, gravacao_id)
    if par is None:
        corte.tentativas.append("gps: sem latitude e longitude mapeadas na mesma serie")
        return False
    lat_canal, lon_canal = par
    dados = ler_colunas(lat_canal.uri, [lat_canal.nome_bruto, lon_canal.nome_bruto])
    if "t_s" not in dados or lat_canal.nome_bruto not in dados:
        corte.tentativas.append("gps: serie sem as colunas esperadas")
        return False
    lat = lat_canal.valores(dados)
    lon = lon_canal.valores(dados)
    instantes, motivo = passagens_por_gps(
        dados["t_s"], lat, lon, float(ref_lat), float(ref_lon)
    )
    if motivo:
        corte.tentativas.append(f"gps: {motivo}")
        return False
    voltas = voltas_de_passagens(instantes)
    if not voltas:
        corte.tentativas.append(
            f"gps: {len(instantes)} cruzamento(s), nenhuma volta fechada"
        )
        return False
    corte.voltas = voltas
    corte.origem = "gps"
    corte.metodo_versao = METODO_GPS
    corte.fonte = f"gps ({lat_canal.nome_bruto}/{lon_canal.nome_bruto})"
    corte.frequencia_hz = lat_canal.frequencia_hz
    return True


# --- cascata e persistencia ----------------------------------------------


def cortar(conn, gravacao_id: str, *, recortar: bool = False) -> Corte:
    """Roda a cascata numa gravacao e grava as voltas. Idempotente."""
    corte = Corte(gravacao_id=gravacao_id)

    existentes = conn.execute(
        """select count(*), min(origem), min(metodo_versao)
             from volta where session_id = %s""",
        (gravacao_id,),
    ).fetchone()
    if existentes[0] and not recortar:
        corte.motivo = (
            f"ja cortada: {existentes[0]} volta(s) por {existentes[2]}. "
            "Use recortar=True pra refazer."
        )
        return corte
    if existentes[0] and recortar:
        # Delete sem cascade de proposito: se a etapa 6 ja escreveu tempo por
        # trecho contra estas voltas, a FK barra e a pessoa decide o que fazer,
        # em vez de o derivado sumir junto em silencio.
        conn.execute("delete from volta where session_id = %s", (gravacao_id,))

    for degrau in (_por_canal, _por_ldx, _por_xrk, _por_gps):
        if degrau(conn, gravacao_id, corte):
            break
    else:
        corte.motivo = "; ".join(corte.tentativas) or "sem fonte de corte de volta"
        return corte

    layout_id = conn.execute(
        "select layout_id from gravacao where id = %s", (gravacao_id,)
    ).fetchone()[0]
    for v in corte.voltas:
        conn.execute(
            """insert into volta
                   (session_id, layout_id, lap_number, lap_time_s, origem,
                    metodo_versao, t_inicio_s, t_fim_s)
               values (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                gravacao_id,
                layout_id,
                v.numero,
                v.tempo_s,
                corte.origem,
                corte.metodo_versao,
                v.t_inicio_s,
                v.t_fim_s,
            ),
        )
    conn.execute(
        "update gravacao set lap_count = %s, updated_at = now() where id = %s",
        (len(corte.voltas), gravacao_id),
    )
    return corte


def cortar_todas(conn, *, recortar: bool = False) -> tuple[ResumoCorte, list[Corte]]:
    """Cascata sobre todas as gravacoes. Nao para no primeiro fracasso."""
    resumo = ResumoCorte()
    cortes: list[Corte] = []
    ids = [
        r[0]
        for r in conn.execute("select id from gravacao order by created_at").fetchall()
    ]
    for gid in ids:
        corte = cortar(conn, str(gid), recortar=recortar)
        cortes.append(corte)
        if corte.cortou:
            resumo.cortadas += 1
            resumo.voltas += len(corte.voltas)
            chave = corte.metodo_versao or "?"
            resumo.por_metodo[chave] = resumo.por_metodo.get(chave, 0) + 1
            taxa = f"{corte.frequencia_hz:g} Hz" if corte.frequencia_hz else "sem taxa"
            resumo.por_taxa[taxa] = resumo.por_taxa.get(taxa, 0) + 1
            if corte.dispersao > DISPERSAO_SUSPEITA:
                resumo.suspeitas.append((corte.gravacao_id, corte.dispersao))
        elif corte.motivo and corte.motivo.startswith("ja cortada"):
            resumo.ja_cortadas += 1
        else:
            resumo.nao_cortadas += 1
            chave = _familia_do_motivo(corte)
            resumo.por_motivo[chave] = resumo.por_motivo.get(chave, 0) + 1
    return resumo, cortes


# Da tentativa mais acionavel pra menos. A ordem importa: uma gravacao sem
# canal de volta, sem ldx e sem layout acumula tres tentativas, e reportar a
# ultima ("sem layout resolvido") mandaria resolver pista pra um arquivo que ia
# cortar por canal de qualquer jeito. O que interessa e o degrau onde a
# gravacao chegou mais perto de cortar.
_FAMILIAS = (
    ("nunca passa a menos", "GPS incoerente com o layout resolvido"),
    ("nunca cruza a linha", "GPS passa pelo gate mas nao cruza no sentido da pista"),
    ("denso demais", "canal de volta denso demais pra ser volta"),
    ("sem transicao", "canal de volta presente mas constante"),
    ("nenhuma volta fechada", "uma passagem so: nao fecha volta"),
    ("precisa de 2 pra fechar", "menos de 2 beacons no sidecar"),
    ("nao tem coordenada de referencia", "layout sem coordenada de referencia"),
    ("sem latitude e longitude", "sem GPS mapeado na mesma serie"),
    ("sem layout resolvido", "sem layout resolvido (e sem canal de volta nem ldx)"),
)


def _familia_do_motivo(corte: Corte) -> str:
    """Agrupa o motivo pra o resumo caber na tela.

    O motivo detalhado continua em `corte.motivo`, por gravacao. Aqui o que
    interessa e a forma da divida: 100 gravacoes sem beacon decodificado e uma
    linha de trabalho, nao 100 linhas de relatorio.
    """
    texto = corte.motivo or ""
    for chave, familia in _FAMILIAS:
        if chave in texto:
            return familia
    return texto[:70] or "nenhuma fonte de corte"
