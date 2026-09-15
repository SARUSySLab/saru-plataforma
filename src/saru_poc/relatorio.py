"""Etapa 7: relatorio e insight.

Emite o shape de `web/src/types/contract.ts`, o contrato de saida que o front
ja consome (hoje via fixture). O front nao inventa campo, entao o que nao
existe aqui tem que sair DECLARADO como indisponivel, com motivo, nunca ausente
nem zerado: degradacao silenciosa e a doenca do B2.

Tres perguntas, na ordem do plano:

  N0. Onde perdi?      as 3 maiores perdas por trecho
  N1. Estou melhorando? tempo por volta ao longo da sessao
  N1. Quanto gastei?    litros por volta (sem canal de combustivel no acervo)

Duas coisas que este modulo NAO faz, de proposito:

- Nao guarda volta ideal no banco. E calculo entre voltas, nao propriedade
  de uma volta, e o proprio catalogo marca isso. Sai so no relatorio.
- Nao emite numero sintetico. A nota do piloto de 0 a 100 saiu do contrato
  (decisao 12) por estar quebrada por construcao, e as quatro componentes que a
  alimentavam voltam EM UNIDADE, com a referencia ao lado (`AtributosPilotagem`).

A guarda do B1 vive aqui: volta ideal nunca pode passar a melhor volta. Se a
soma dos melhores setores violar isso (setor faltando, escala misturada), a
ideal e SUPRIMIDA com `ideal_suprimida: true`, em vez de sair um "potencial de
-188,7 s" como o saru-app mostrava.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Comprimento do micro-setor do N2. Micro-setor NAO e entidade do banco: e
# recorte de analise por distancia, calculado aqui, e por isso nao polui o
# catalogo de layout com segmento que nenhum engenheiro cadastrou. 200 m da 21
# recortes em Interlagos, fino o suficiente pra localizar perda e grosso o
# suficiente pra nao virar ruido.
MICRO_SETOR_M = 200.0

# Acima deste multiplo da mediana a volta sai marcada como nao-valida. Cobre
# trafego, bandeira e entrada de box no meio da volta. In-lap e out-lap NAO
# dependem disto: eles nunca viram volta (etapa 5), porque volta e o intervalo
# ENTRE duas passagens.
# (a confirmar com o Lucas: o numero e chute conservador, nao medicao.)
TETO_VOLTA_VALIDA = 1.25

# Acima deste percentual do curso do acelerador conta como "pleno".
ACELERADOR_PLENO = 0.95


# De-para do vocabulario canonico (o do banco, em ingles, em unidade SI) pro
# vocabulario que o FRONT ja consome. Decisao do Lucas (29/08): o backend
# traduz na fronteira e o front nao muda.
#
# Nao e preciosismo de nome: a unidade e o risco real. `web/src/dados/
# useAmostras.ts` divide a velocidade por 3.6 hardcoded ("velocidade vem em
# km/h no contrato"), e o canonico `speed` esta em m/s. Emitir o canonico cru
# faria o delta entre voltas sair 3,6 vezes errado, sem erro de tipo nenhum,
# sem campo faltando, sem nada que o validador de contrato pegasse. Erro de
# unidade e invisivel pro shape e visivel pro piloto.
#
# (canonico) -> (id no front, fator, unidade que o front assume)
APRESENTACAO: dict[str, tuple[str, float, str]] = {
    "speed": ("velocidade", 3.6, "km/h"),
    "throttle": ("acelerador", 100.0, "%"),
    "throttle_tps1": ("acelerador", 100.0, "%"),
    "brake": ("freio", 100.0, "%"),
    # Freio de PRESSAO (kPa no canonico, ver acervo.py: os 9 loggers reais
    # alimentam brake_press). O fator estatico daqui nao resolve: pressao nao
    # vira % por multiplicacao, vira por normalizacao baseline->pico DA
    # GRAVACAO, e isso `amostras()` faz num passo declarado (procurar
    # "brake_press" la). Baseline e nao zero porque tem sensor que repousa
    # deslocado (Freio_Press do caminhao repousa em -1,045 bar, medido em
    # 29/08 no acervo); normalizar so pelo pico deixava o traco em -96%.
    "brake_press": ("freio", 1.0, "%"),
    # Direcao: no acervo AiM o canal e deslocamento de cremalheira (ver
    # aliases.yaml). Sem relacao cremalheira->grau, a apresentacao e % do
    # esterço maximo DA GRAVACAO, normalizada em amostras() (procurar
    # "regua_direcao"), mesma regua declarada do freio por pressao.
    "steering": ("direcao", 1.0, "%"),
    "gear": ("marcha", 1.0, ""),
    "rpm": ("rpm", 1.0, "rpm"),
    "lat_acc": ("acel_lat", 1.0 / 9.80665, "g"),
    "lon_acc": ("acel_lon", 1.0 / 9.80665, "g"),

    # Bloco 16 (temperatura de pneu). O acervo levanta o mesmo canto por ATE
    # TRES sensores diferentes: no meio da banda (mid, sensor infra do MoTeC/
    # AiM, e o mais comum: 34 das 36 gravacoes com dado), na carcaca interna
    # (inner, so no simulador GT7) ou na borda externa (outer, nenhuma
    # gravacao do acervo tem hoje, mas o canonico existe no catalogo). Os tres
    # sao "a temperatura deste canto" pro front: mesmo `id`, mesma unidade, e
    # ISSO e o de-para de apresentacao, entao os tres canonicos convergem pro
    # mesmo `nome_front` por canto.
    #
    # A ORDEM de insercao no dict e a precedencia (mid > inner > outer),
    # exatamente a mesma convencao ja usada acima pra throttle/throttle_tps1.
    # Os dois pontos onde isso e lido (`_canais_de_apresentacao`, usado pela
    # etapa de amostras, e o loop de N3 abaixo) so materializam o primeiro
    # canonico da lista que tiver canal de fato: se so existir mid, mid vence
    # por ser o unico candidato, nao por regra especial. A precedencia so
    # entraria em jogo se uma mesma gravacao tivesse dois sensores no mesmo
    # canto ao mesmo tempo, o que nao acontece em nenhuma das 36 gravacoes
    # hoje (cada uma usa um perfil de leitor so, e cada perfil so mapeia UM
    # ponto de medicao por canto). Mid vem primeiro porque e o ponto que mais
    # perfis do acervo (MoTeC .ld e AiM) usam pra IR (temperatura infra do
    # pneu rodando) e e o mais comparavel entre gravacoes.
    "tyre_temp_mid_fl": ("temp_pneu_fl", 1.0, "°C"),
    "tyre_temp_inner_fl": ("temp_pneu_fl", 1.0, "°C"),
    "tyre_temp_outer_fl": ("temp_pneu_fl", 1.0, "°C"),
    "tyre_temp_mid_fr": ("temp_pneu_fr", 1.0, "°C"),
    "tyre_temp_inner_fr": ("temp_pneu_fr", 1.0, "°C"),
    "tyre_temp_outer_fr": ("temp_pneu_fr", 1.0, "°C"),
    "tyre_temp_mid_rl": ("temp_pneu_rl", 1.0, "°C"),
    "tyre_temp_inner_rl": ("temp_pneu_rl", 1.0, "°C"),
    "tyre_temp_outer_rl": ("temp_pneu_rl", 1.0, "°C"),
    "tyre_temp_mid_rr": ("temp_pneu_rr", 1.0, "°C"),
    "tyre_temp_inner_rr": ("temp_pneu_rr", 1.0, "°C"),
    "tyre_temp_outer_rr": ("temp_pneu_rr", 1.0, "°C"),
}

# Pontos da grade comum de distancia. Decisao do Lucas (29/08): o backend
# reamostra, porque `calcularDelta` no front indexa as duas voltas pelos MESMOS
# indices, e volta nativa tem contagem de amostra diferente a cada volta. 900 e
# o que os 15 fixtures do front ja usam (4,88 m de passo em Interlagos), e o
# front foi desenhado contra essa resolucao.
GRADE_PONTOS = 900


class ReferenciaDePistaDiferente(Exception):
    """A guarda do B2 pro par cruzado entre gravacoes.

    Curva e micro-setor saem do catalogo do LAYOUT, nao da gravacao: os ids de
    `curva_por_volta`/`micro_por_volta` so tem correspondencia entre duas
    gravacoes se as duas forem do mesmo layout. Comparar contra outro layout e
    o bug B2 do saru-app de novo, com roupa nova: `_resolve_track_id` aplicou
    setor de Interlagos (4.309 m) num arquivo de kart de 1,1 km sem avisar
    ninguem. Aqui a resposta nao e calcular torto, e recusar com 422.
    """


def _degradado(motivo: str, texto: str) -> dict:
    return {"disponivel": False, "motivo": motivo, "texto": texto}


def _disponivel(**campos) -> dict:
    return {"disponivel": True, **campos}


# --- captura: a gravacao chegou a virar amostra? -------------------------
# Excecao 3e do E-UC-01, issue #2, criterio PIL-CT-52, regra PIL-RN-11.
#
# `aim_gpk` e `aim_rrk` tem leitor de INVENTARIO: leem cabecalho e contagem de
# registros e nao decodificam canal. A ingestao ja sabia disso e gravava
# `status = 'parcial'` (pipeline/ingestao.py:476), e o piloto nao via em lugar
# nenhum: o relatorio saia sem os blocos e sem dizer por que. Bloco vazio sem
# motivo e a mesma doenca do B2, so que vinda da leitura em vez da pista.


@dataclass(frozen=True)
class ArquivoDaCaptura:
    """Um arquivo do bundle, do ponto de vista da leitura.

    `ingerido` e falso enquanto nenhum leitor rodou sobre o arquivo. E a
    diferenca entre "foi lido e nao tinha amostra" e "ainda nao foi lido", e
    confundir as duas e o defeito que este tipo existe pra impedir: a recepcao
    ingere arquivo a arquivo, com commit entre eles, entao um bundle correto
    passa por um estado em que o `.gpk` ja entrou e o `.xrk` ainda nao.
    """

    formato_id: str
    suporta_amostra: bool
    amostras_escritas: int
    ingerido: bool


def arquivos_da_captura(conn, gravacao_id: str) -> list[ArquivoDaCaptura]:
    """Um item por arquivo do bundle desta gravacao.

    `ingestao` e append-only (uma linha por execucao de leitor sobre o arquivo,
    ver migration 005), entao o estado atual de um arquivo e o MAIOR
    `amostras_escritas` entre as linhas dele, nao a ultima: reprocessar com um
    leitor pior nao pode apagar amostra que ja existe no Parquet.

    `suporta_amostra` sai do registro de leitores, nao da contagem de amostra.
    Sao perguntas diferentes: um `.vbo` vazio escreve zero amostra e nao e
    inventario, e tratar os dois como a mesma coisa acusaria o formato errado.
    """
    from .readers import leitor_de

    linhas = conn.execute(
        """select ab.formato_id,
                  coalesce(max(i.amostras_escritas), 0),
                  count(i.id) > 0
             from arquivo_bruto ab
             left join ingestao i
               on i.arquivo_id = ab.id and i.status <> 'falhou'
            where ab.gravacao_id = %s
            group by ab.id, ab.formato_id
            order by ab.formato_id""",
        (gravacao_id,),
    ).fetchall()
    saida = []
    for formato_id, amostras, ingerido in linhas:
        leitor = leitor_de(formato_id)
        saida.append(
            ArquivoDaCaptura(
                formato_id=formato_id,
                suporta_amostra=bool(leitor and leitor.suporta_amostra),
                amostras_escritas=int(amostras),
                ingerido=bool(ingerido),
            )
        )
    return saida


def captura_so_de_inventario(arquivos: list[ArquivoDaCaptura]) -> bool:
    """A captura inteira foi lida e nenhum arquivo dela virou amostra.

    Exige que TODO arquivo do bundle ja tenha linha de ingestao, e essa exigencia
    e o ponto. A recepcao ingere arquivo a arquivo, com commit entre eles, entao
    um bundle correto de `.gpk` mais `.xrk` passa por um estado em que so o
    `.gpk` entrou. Sem a exigencia, esse estado intermediario respondia ao piloto
    "envie o arquivo principal do logger", que e justamente o arquivo que ele ja
    tinha enviado e que estava na fila.

    Bundle vazio nao e inventario: nao ha evidencia de nada.
    """
    if not arquivos:
        return False
    if not all(a.ingerido for a in arquivos):
        return False
    return not any(a.amostras_escritas > 0 for a in arquivos)


def amostra_da_captura(arquivos: list[ArquivoDaCaptura]) -> dict:
    """Bloco `amostra_da_captura` do contrato, a partir de `arquivos_da_captura`.

    Disponivel quando pelo menos um arquivo materializou serie. Degradado com
    motivo `somente_inventario` quando nenhum materializou.

    O texto do ramo degradado e montado a partir do que foi medido, nunca
    afirmando mais do que se sabe. Sao tres situacoes diferentes com a mesma
    consequencia, e o texto separa as tres: leitura ainda em curso, formato de
    leitor de inventario, e formato que suporta amostra e mesmo assim nao
    escreveu nenhuma.
    """
    com_amostra = [a for a in arquivos if a.amostras_escritas > 0]
    if com_amostra:
        return _disponivel(
            arquivos_lidos=len(arquivos), arquivos_com_amostra=len(com_amostra)
        )

    lidos = [a for a in arquivos if a.ingerido]
    if arquivos and len(lidos) < len(arquivos):
        # Leitura em curso. Dizer "entrou só como inventário" aqui seria afirmar
        # sobre arquivo que ninguém abriu ainda.
        return _degradado(
            "somente_inventario",
            f"a leitura desta captura ainda não terminou: {len(lidos)} de "
            f"{len(arquivos)} arquivos lidos, nenhum com amostra até agora",
        )

    inventario = sorted({a.formato_id for a in arquivos if not a.suporta_amostra})
    sem_escrever = sorted({a.formato_id for a in arquivos if a.suporta_amostra})
    partes = []
    if inventario:
        partes.append(
            f"{', '.join(inventario)}: o leitor lê o cabeçalho e conta os "
            "registros, e não decodifica canal"
        )
    if sem_escrever:
        partes.append(
            f"{', '.join(sem_escrever)}: o leitor suporta amostra e não escreveu nenhuma"
        )
    # A frase de abertura muda com o que foi medido. "Entrou só como inventário"
    # só é verdade quando TODO arquivo veio de leitor de inventário; com um
    # formato que lê amostra no meio, o que se sabe é menos que isso.
    texto = (
        "esta captura entrou só como inventário: nenhum arquivo dela entregou amostra"
        if inventario and not sem_escrever
        else "nenhum arquivo desta captura entregou amostra"
    )
    if partes:
        texto = f"{texto} ({'; '.join(partes)})"
    return _degradado("somente_inventario", texto)


# --- N0: melhor volta e volta ideal --------------------------------------


def melhor_volta(voltas: list[dict], setores_por_volta: dict[int, list[float]]) -> dict:
    """Bloco 1. A guarda do B1 vive aqui.

    A ideal e a soma do melhor tempo de cada setor entre as voltas validas. Ela
    e suprimida em dois casos: quando algum setor nao tem tempo em nenhuma volta
    (somar 2 de 3 setores daria uma ideal absurdamente menor), e quando a soma
    passa a melhor volta real, que e matematicamente impossivel e portanto prova
    de que alguma escala esta misturada.
    """
    validas = [v for v in voltas if v["valida"]]
    if not validas:
        return {
            "melhor_volta_s": 0.0,
            "melhor_volta_n": 0,
            "volta_ideal_s": None,
            "margem_para_ideal_s": None,
            "voltas_validas": 0,
            "voltas_totais": len(voltas),
            "ideal_suprimida": True,
        }

    melhor = min(validas, key=lambda v: v["tempo_s"])
    ideal = None
    suprimida = True

    listas = [setores_por_volta.get(v["n"], []) for v in validas]
    n_setores = max((len(x) for x in listas), default=0)
    if n_setores:
        melhores: list[float | None] = []
        for i in range(n_setores):
            candidatos = [
                x[i] for x in listas if len(x) > i and x[i] is not None and x[i] > 0
            ]
            melhores.append(min(candidatos) if candidatos else None)
        if all(m is not None for m in melhores):
            soma = float(sum(melhores))  # type: ignore[arg-type]
            if soma <= melhor["tempo_s"]:
                ideal = soma
                suprimida = False
            # soma > melhor volta cai fora: e o B1. Fica suprimida.

    return {
        "melhor_volta_s": melhor["tempo_s"],
        "melhor_volta_n": melhor["n"],
        "volta_ideal_s": ideal,
        "margem_para_ideal_s": (melhor["tempo_s"] - ideal)
        if ideal is not None
        else None,
        "voltas_validas": len(validas),
        "voltas_totais": len(voltas),
        "ideal_suprimida": suprimida,
    }


# --- perdas por trecho ---------------------------------------------------


def _medida(valor, referencia, unidade: str, aplicavel: bool = True) -> dict:
    return {
        "valor": valor,
        "referencia": referencia,
        "unidade": unidade,
        "aplicavel": aplicavel,
    }


def perdas_por_trecho(
    trechos: list[dict],
    tempos_analisada: dict[str, float],
    tempos_referencia: dict[str, float],
    *,
    modo: str,
    repeticao: dict[str, float] | None = None,
    pilotagem: dict[str, dict] | None = None,
) -> list[dict]:
    """Fonte unica dos blocos 3 (top 3, N0) e 9 (lista completa, N2).

    Perda e o tempo do trecho na volta analisada menos o tempo do MESMO trecho
    na referencia. Positivo e perda, negativo e ganho, e os dois aparecem: o
    contrato tem bloco pra onde ganhar tempo tambem, e esconder o ganho e o que
    faz o delta acumulado mentir.
    """
    itens = []
    for t in trechos:
        tid = t["id"]
        a = tempos_analisada.get(tid)
        b = tempos_referencia.get(tid)
        if a is None or b is None:
            continue
        item = {
            "trecho_id": tid,
            "rotulo": t["rotulo"],
            "modo": modo,
            "s_inicio_m": t["s_inicio_m"],
            "s_fim_m": t["s_fim_m"],
            "perda_s": a - b,
            # Fase nao existe no catalogo (medido: zero linhas em `fase`), entao
            # tempo por fase sai declarado como indisponivel em vez de inventado.
            "tempo_por_fase": _degradado(
                "sem_catalogo_de_curva",
                "as fases desta curva (entrada, meio, saida) nao estao catalogadas",
            ),
            # Ressalva depende de contexto capturado (pneu, temperatura). Sem
            # contexto, nao ha condicao conhecida que relativize o insight.
            "ressalva": None,
            "pilotagem": (
                _disponivel(
                    tempo_no_trecho=_medida(a, b, "s"),
                    repeticao_entre_voltas_s=(repeticao or {}).get(tid),
                    pico_frenagem=(pilotagem or {})
                    .get(tid, {})
                    .get("pico_frenagem", _medida(None, None, "%", False)),
                    pico_envelope_grip=(pilotagem or {})
                    .get(tid, {})
                    .get("pico_envelope_grip", _medida(None, None, "m/s2", False)),
                )
                if pilotagem is not None
                else _degradado(
                    "sem_contexto_sessao",
                    "sem canal de freio nem de aceleracao pra medir pilotagem",
                )
            ),
        }
        itens.append(item)
    return sorted(itens, key=lambda x: -x["perda_s"])


# --- micro-setores -------------------------------------------------------


def micro_setores(comprimento_m: float, passo_m: float = MICRO_SETOR_M) -> list[dict]:
    """Recorte uniforme da volta em faixas de distancia.

    Micro-setor nao e entidade do banco: e recorte de analise. So exige
    distancia, enquanto curva exige catalogo de layout, e por isso os dois
    recortes vem juntos no N2 (o contrato documenta): quem decide qual esta
    disponivel e o dado, e o usuario alterna sem round-trip.
    """
    faixas = []
    n = max(1, round(comprimento_m / passo_m))
    largura = comprimento_m / n
    for i in range(n):
        a, b = i * largura, (i + 1) * largura
        faixas.append(
            {
                "id": f"micro-{i + 1:02d}",
                "rotulo": f"{a / 1000:.1f} a {b / 1000:.1f} km",
                "s_inicio_m": a,
                "s_fim_m": b,
            }
        )
    return faixas


def tempos_em_faixas(
    t_s, s_m, faixas: list[dict], *, t_inicio: float, t_fim: float
) -> dict[str, float]:
    """Tempo gasto em cada faixa de distancia, por interpolacao."""
    import numpy as np

    if len(t_s) < 2:
        return {}
    tempos: dict[str, float] = {}
    total = float(s_m[-1])
    for faixa in faixas:
        a = float(np.interp(faixa["s_inicio_m"], s_m, t_s))
        b = float(np.interp(faixa["s_fim_m"], s_m, t_s))
        if faixa["s_inicio_m"] <= 0.0:
            a = t_inicio
        if faixa["s_fim_m"] >= total:
            b = t_fim
        if b > a:
            tempos[faixa["id"]] = b - a
    return tempos


# --- montagem a partir do catalogo ---------------------------------------


def _eixos_por_volta(conn, gravacao_id: str, voltas: list[dict]) -> dict[int, tuple]:
    """(t, s) de cada volta, pela mesma cascata da etapa 6.

    Reusa `_eixo_da_volta` de proposito: se o eixo do relatorio divergisse do
    eixo que gerou `tempo_trecho`, o N2 por curva e o N2 por micro-setor
    contariam a volta de dois jeitos diferentes na mesma tela.
    """
    from .pipeline.decomposicao import _eixo_da_volta, fechar_no_layout

    comprimento = conn.execute(
        """select l.comprimento_m from gravacao g join layout l on l.id = g.layout_id
            where g.id = %s""",
        (gravacao_id,),
    ).fetchone()
    if comprimento is None:
        return {}
    eixos: dict[int, tuple] = {}
    for v in voltas:
        t, s, _origem = _eixo_da_volta(conn, gravacao_id, v["t_inicio_s"], v["t_fim_s"])
        if t is None or s is None:
            continue
        fechado, _fator, motivo = fechar_no_layout(s, float(comprimento[0]))
        if fechado is None or motivo is not None:
            continue
        eixos[v["n"]] = (t, fechado)
    return eixos


def classificar_volta(
    numero: int,
    total_voltas: int,
    lap_time: float,
    mediana: float,
    teto: float,
) -> tuple[str, bool, str | None]:
    """Classifica a volta segundo as regras ratificadas em 2026-09-13 (Decisao 2 e PIL-RN-12).

    Retorna tupla (classificacao, valida, motivo):
      - NORMAL: ritmo competitivo (lap_time <= teto).
      - OUT_LAP: primeira volta cortada quando lap_time > teto.
      - IN_LAP: ultima volta cortada quando lap_time > teto.
      - AQUECIMENTO: volta logo apos out-lap (numero == 2) quando lap_time > teto.
      - TRAFEGO: volta intermediaria quando lap_time > teto.
    """
    if lap_time <= teto:
        return "NORMAL", True, None

    razao = lap_time / mediana if mediana > 0 else 1.0
    if numero == 1:
        return "OUT_LAP", False, f"out-lap: saida dos boxes ({razao:.2f}x a mediana)"
    if numero == total_voltas and total_voltas > 1:
        return "IN_LAP", False, f"in-lap: retorno aos boxes ({razao:.2f}x a mediana)"
    if numero == 2 and total_voltas > 2:
        return "AQUECIMENTO", False, f"aquecimento de pneus ({razao:.2f}x a mediana)"
    return "TRAFEGO", False, f"trafego ou bandeira ({razao:.2f}x a mediana)"


def _voltas_e_setores(conn, gravacao_id: str) -> tuple[list[dict], dict[int, list]]:
    """VoltaResumo de cada volta mais os tempos de setor por volta."""
    import numpy as np

    from .pipeline.leitura import escolher_canal, ler_colunas

    linhas = conn.execute(
        """select id, lap_number, lap_time_s, t_inicio_s, t_fim_s
             from volta where session_id = %s order by lap_number""",
        (gravacao_id,),
    ).fetchall()
    if not linhas:
        return [], {}

    tempos = [float(x[2]) for x in linhas]
    mediana = float(np.median(tempos))
    teto = mediana * TETO_VOLTA_VALIDA

    canal_v = escolher_canal(conn, gravacao_id, ("speed",))
    canal_t = escolher_canal(conn, gravacao_id, ("throttle", "throttle_tps1"))
    dados_v = ler_colunas(canal_v.uri, [canal_v.nome_bruto]) if canal_v else None
    dados_t = ler_colunas(canal_t.uri, [canal_t.nome_bruto]) if canal_t else None

    voltas: list[dict] = []
    setores_por_volta: dict[int, list] = {}
    total_linhas = len(linhas)
    for vid, numero, lap_time, t_ini, t_fim in linhas:
        setores = [
            float(x[0])
            for x in conn.execute(
                """select tt.tempo_s from tempo_trecho tt
                     join segmento sg on sg.id = tt.segmento_id
                    where tt.volta_id = %s and sg.tipo = 'setor'
                    order by sg.ordem""",
                (vid,),
            ).fetchall()
        ]
        setores_por_volta[numero] = setores

        v_max = None
        if dados_v is not None and canal_v is not None:
            t = dados_v["t_s"]
            m = (t >= float(t_ini)) & (t <= float(t_fim))
            if m.any():
                # o contrato pede km/h; o canonico e m/s
                v_max = float(canal_v.valores(dados_v)[m].max()) * 3.6

        pleno = None
        if dados_t is not None and canal_t is not None:
            t = dados_t["t_s"]
            m = (t >= float(t_ini)) & (t <= float(t_fim))
            if m.any():
                valores = canal_t.valores(dados_t)[m]
                # curso do acelerador aparece em 0-1 e em 0-100 no acervo
                escala = 100.0 if float(valores.max()) > 1.5 else 1.0
                pleno = float((valores / escala >= ACELERADOR_PLENO).mean() * 100.0)

        _classe, valida, motivo = classificar_volta(
            int(numero),
            total_linhas,
            float(lap_time),
            mediana,
            teto,
        )

        voltas.append(
            {
                "n": int(numero),
                "tempo_s": float(lap_time),
                "setores_s": setores or [],
                "v_max_kmh": v_max,
                "delta_referencia_s": 0.0,  # preenchido depois, contra a referencia
                "valida": valida,
                "motivo_invalida": motivo,
                # Sem canal de combustivel no vocabulario canonico (medido: o
                # catalogo de 62 canais nao tem nenhum de nivel nem de vazao).
                "litros": None,
                "acelerador_pleno_pct": pleno,
                # `gravacao.bateria_id` e anulavel por decisao D3: arquivo solto
                # ingere sem evento nenhum, e o acervo inteiro e arquivo solto.
                "bateria": None,
                "voltas_pneu": None,
                "t_inicio_s": float(t_ini),
                "t_fim_s": float(t_fim),
                "volta_id": str(vid),
            }
        )
    return voltas, setores_por_volta


def _pilotagem_por_trecho(
    conn,
    gravacao_id: str,
    trechos: list[dict],
    t_s,
    s_m,
    *,
    t_inicio: float,
    t_fim: float,
) -> dict[str, dict] | None:
    """Pico de frenagem e pico de envelope de grip dentro de cada trecho.

    Sao duas das quatro componentes que alimentavam a nota do piloto (removida,
    decisao 12). Voltam EM UNIDADE, com a referencia ao lado, nunca como placar
    de 0 a 100: o placar foi testado no prototipo e estava quebrado por
    construcao (o uso do grip batia em 100 em toda curva, porque dentro de curva
    o envelope esta sempre carregado).

    Nulo quando nao ha canal de freio nem de aceleracao: o bloco degrada em vez
    de mostrar zero, porque zero de frenagem e uma afirmacao, e "nao medi" e
    outra.
    """
    import numpy as np

    from .pipeline.leitura import escolher_canal, ler_colunas

    freio = escolher_canal(conn, gravacao_id, ("brake", "brake_press"))
    g_lat = escolher_canal(conn, gravacao_id, ("lat_acc",))
    g_lon = escolher_canal(conn, gravacao_id, ("lon_acc",))
    if freio is None and g_lat is None:
        return None

    d_freio = ler_colunas(freio.uri, [freio.nome_bruto]) if freio else None
    d_lat = ler_colunas(g_lat.uri, [g_lat.nome_bruto]) if g_lat else None
    d_lon = ler_colunas(g_lon.uri, [g_lon.nome_bruto]) if g_lon else None

    saida: dict[str, dict] = {}
    for trecho in trechos:
        a = float(np.interp(trecho["s_inicio_m"], s_m, t_s))
        b = float(np.interp(trecho["s_fim_m"], s_m, t_s))
        a, b = max(a, t_inicio), min(b, t_fim)

        # NaN no canal cru (amostra que o decode nao fechou) contamina o
        # max() e o NaN vaza pro JSON, que o Postgres rejeita no jsonb do
        # Sarue (500 medido em producao em 29/08). Pico so existe se houver
        # amostra FINITA na janela; sem isso, e "nao medi", nao NaN.
        pico_freio = None
        if d_freio is not None and freio is not None:
            t = d_freio["t_s"]
            m = (t >= a) & (t <= b)
            if m.any():
                v = freio.valores(d_freio)[m]
                fin = np.isfinite(v)
                if fin.any():
                    pico_freio = float(v[fin].max())

        pico_grip = None
        if d_lat is not None and g_lat is not None:
            t = d_lat["t_s"]
            m = (t >= a) & (t <= b)
            if m.any():
                lat = g_lat.valores(d_lat)[m]
                if (
                    d_lon is not None
                    and g_lon is not None
                    and len(d_lon["t_s"]) == len(t)
                ):
                    lon = g_lon.valores(d_lon)[m]
                    # Envelope: o modulo do vetor de aceleracao, nao a soma dos
                    # eixos. Somar lateral com longitudinal daria numero maior
                    # que o pneu entrega, e o circulo de tracao e justamente o
                    # limite que os dois compartilham.
                    env = np.hypot(lat, lon)
                else:
                    env = np.abs(lat)
                fin = np.isfinite(env)
                pico_grip = float(env[fin].max()) if fin.any() else None

        saida[trecho["id"]] = {
            "pico_frenagem": _medida(
                pico_freio,
                None,
                "%" if freio and freio.canonico == "brake" else "bar",
                pico_freio is not None,
            ),
            # Unidade: m/s2. `valores()` ja devolve o canal na unidade canonica da
            # casa (aliases.yaml converte g -> m/s2 com fator 9.80665), entao
            # rotular de "g" aqui mostrava 8 g na tela, um numero que nenhum
            # pneu entrega -- era o m/s2 com o rotulo errado.
            "pico_envelope_grip": _medida(pico_grip, None, "m/s2", pico_grip is not None),
        }
    return saida


def _tempos_por_trecho_por_volta(
    conn, voltas: list[dict], faixas: list[dict], eixos: dict[int, tuple]
) -> tuple[dict[int, dict[str, float]], dict[int, dict[str, float]]]:
    """Tempo por curva (do catalogo, via `tempo_trecho`) e por micro-setor (por
    interpolacao no eixo de distancia), pra cada volta recebida.

    Usado tanto pra gravacao analisada quanto pra gravacao de referencia
    (quando ela vem de outra captura): as duas usam o MESMO layout (a guarda
    do B2 acima garante isso antes de qualquer uma destas contas rodar), entao
    os ids de curva e de micro-setor batem sem remapeamento nenhum.
    """
    curva_por_volta: dict[int, dict[str, float]] = {}
    for v in voltas:
        curva_por_volta[v["n"]] = {
            str(sid): float(tempo)
            for sid, tempo in conn.execute(
                """select tt.segmento_id, tt.tempo_s from tempo_trecho tt
                     join segmento sg on sg.id = tt.segmento_id
                    where tt.volta_id = %s and sg.tipo = 'curva'""",
                (v["volta_id"],),
            ).fetchall()
        }
    micro_por_volta: dict[int, dict[str, float]] = {}
    for v in voltas:
        if v["n"] in eixos:
            t, s = eixos[v["n"]]
            micro_por_volta[v["n"]] = tempos_em_faixas(
                t, s, faixas, t_inicio=v["t_inicio_s"], t_fim=v["t_fim_s"]
            )
    return curva_por_volta, micro_por_volta


def montar(
    conn,
    gravacao_id: str,
    *,
    volta: int | None = None,
    referencia: int | str | None = None,
    ref_gravacao_id: str | None = None,
) -> dict:
    """Monta o `Relatorio` do contrato pra uma gravacao.

    `volta` e `referencia` sao o par em escopo. O default espelha o que o front
    faz hoje na casca: analisada = ultima volta valida, referencia = melhor
    volta. Ficam como parametro porque o escopo e do usuario, nao do backend.

    `ref_gravacao_id` e opcional e muda DE ONDE a volta de referencia vem.
    Nulo (default): `referencia` e um numero de volta desta MESMA gravacao,
    comportamento identico ao que existia antes deste parametro, byte a byte.
    Preenchido: `referencia` e um numero de volta da gravacao apontada por
    `ref_gravacao_id`, o que permite comparar dias e baterias diferentes desde
    que seja a MESMA pista. A guarda do B2 (ver `ReferenciaDePistaDiferente`
    acima) recusa o par se os layouts nao baterem ou se um dos dois nao tiver
    layout resolvido: sem layout comum nao existe grade de distancia comum, e
    calcular mesmo assim e o proprio bug B2.

    LIMITE CONHECIDO, e decisao pro Lucas quando a API foi desenhada: os blocos
    de perda (N0 top 3 e N2 completo) saem calculados contra ESTE par. O front
    tem um seletor de escopo global (decisao de produto 1) que hoje nao alcanca
    esses blocos, porque eles vem prontos do backend. Com fixture ninguem viu:
    trocar a volta em escopo na tela nao muda as perdas. Ou a API passa a
    aceitar `?volta=&referencia=` e o front refaz a busca, ou o relatorio passa
    a emitir perda por volta. Sao contratos diferentes, e a escolha e dele.
    """
    import numpy as np

    from .pipeline.leitura import escolher_canal  # noqa: F401  (documenta a fonte)

    cab = conn.execute(
        """select g.id, g.layout_id, l.nome, l.comprimento_m, p.name, g.layout_origem
             from gravacao g
             left join layout l on l.id = g.layout_id
             left join piloto p on p.id = g.piloto_id
            where g.id = %s""",
        (gravacao_id,),
    ).fetchone()
    if cab is None:
        raise ValueError(f"gravacao {gravacao_id} nao existe")
    _gid, layout_id, layout_nome, comprimento, piloto, layout_origem = cab

    # --- guarda do B2 pro par cruzado: entra ANTES de qualquer conta pesada,
    # porque um layout incompativel torna toda a analise abaixo invalida por
    # construcao (ver ReferenciaDePistaDiferente, no topo do modulo).
    cruzada = bool(ref_gravacao_id) and ref_gravacao_id != gravacao_id
    ref_gid = ref_gravacao_id if cruzada else gravacao_id
    if cruzada:
        cab_ref = conn.execute(
            "select layout_id from gravacao where id = %s", (ref_gid,)
        ).fetchone()
        if cab_ref is None:
            raise ValueError(f"gravacao de referencia {ref_gid} nao existe")
        layout_ref_id = cab_ref[0]
        if layout_id is None or layout_ref_id is None:
            raise ReferenciaDePistaDiferente(
                "layout nao resolvido em um dos lados: sem comprimento nao "
                "existe grade de distancia comum pra comparar (regra dura do B2)"
            )
        if layout_ref_id != layout_id:
            raise ReferenciaDePistaDiferente(
                f"nao da pra comparar voltas de pistas diferentes: a gravacao "
                f"analisada e do layout '{layout_id}' e a de referencia e do "
                f"layout '{layout_ref_id}'. A grade de distancia de uma pista "
                "nao vale pra outra (a mesma familia do B2: setorizacao de uma "
                "pista aplicada a outra)."
            )

    voltas, setores_por_volta = _voltas_e_setores(conn, gravacao_id)
    if not voltas:
        raise ValueError(
            f"gravacao {gravacao_id} nao tem volta cortada: rode a etapa 5 antes"
        )

    mv = melhor_volta(voltas, setores_por_volta)
    validas = [v for v in voltas if v["valida"]]
    n_analisada = volta or (validas[-1]["n"] if validas else voltas[-1]["n"])
    # A palavra "media" chega do seletor de comparacao do front, e nao e numero
    # de volta: ela pede a media das validas como referencia.
    pediu_media = isinstance(referencia, str) and referencia.strip().lower() == "media"

    # Fonte da volta de referencia: a propria gravacao (default) ou a gravacao
    # cruzada, ja validada pela guarda acima. `voltas_ref_src` unifica os dois
    # casos, entao o resto da funcao le referencia sem saber de qual lado ela
    # veio.
    if cruzada:
        voltas_ref_src, setores_ref_src = _voltas_e_setores(conn, ref_gid)
        if not voltas_ref_src:
            raise ValueError(
                f"gravacao de referencia {ref_gid} nao tem volta cortada: "
                "rode a etapa 5 antes"
            )
        mv_ref = melhor_volta(voltas_ref_src, setores_ref_src)
        n_ref = mv_ref["melhor_volta_n"] if pediu_media else (referencia or mv_ref["melhor_volta_n"])
    else:
        voltas_ref_src = voltas
        # "media" nao e numero de volta: e o pedido de comparar contra a MEDIA
        # das validas, modo que ja existia aqui embaixo (`ref_media`) mas so
        # era alcancado por acidente, quando a referencia calhava de ser a
        # propria volta analisada. O front sempre teve essa opcao no seletor
        # (`Referencia = number | "media"`), e mandava a palavra para uma rota
        # que so aceitava inteiro: dava 422 e a tela ficava sem relatorio.
        n_ref = n_analisada if pediu_media else (referencia or mv["melhor_volta_n"])

    # Quando a volta em escopo E a melhor volta da sessao (dentro da MESMA
    # gravacao), comparar com ela mesma da perda zero em todo trecho, e o
    # bloco principal do N0 ("onde perdi tempo?") sai com +0,000 s em tudo.
    # Visto na tela, com dado real: a melhor volta e o default da referencia E
    # a ultima valida era a melhor.
    #
    # Nesse caso a referencia passa a ser a MEDIA das voltas validas, que e
    # exatamente o que o front ja faz no traco (`refDoTraco = ehRef ? "media" :
    # refAtiva`). Contra a media, "onde perdi" volta a significar algo: onde
    # esta volta ficou pior que o proprio ritmo tipico do piloto.
    #
    # So se aplica dentro da MESMA gravacao: numero de volta batendo entre
    # DUAS gravacoes diferentes e coincidencia, nao autocomparacao, e a volta
    # da outra gravacao e uma referencia legitima mesmo com o mesmo numero.
    ref_media = pediu_media or ((not cruzada) and n_ref == n_analisada and len(validas) > 1)

    tempo_ref = (
        float(np.mean([v["tempo_s"] for v in validas]))
        if ref_media
        else next((v["tempo_s"] for v in voltas_ref_src if v["n"] == n_ref), None)
    )
    for v in voltas:
        v["delta_referencia_s"] = (
            v["tempo_s"] - tempo_ref if tempo_ref is not None else 0.0
        )

    # --- trechos do layout (curvas) e recorte por micro-setor
    curvas = []
    if layout_id is not None:
        curvas = [
            {
                "id": str(sid),
                "rotulo": rotulo or corner_id,
                "s_inicio_m": float(a),
                "s_fim_m": float(b),
                "apex_m": float(apex) if apex is not None else float(a + b) / 2,
            }
            for sid, rotulo, corner_id, a, b, apex in conn.execute(
                """select c.segmento_id, c.label, c.corner_id, sg.s_inicio_m,
                          sg.s_fim_m, c.s_apex_m
                     from curva c join segmento sg on sg.id = c.segmento_id
                    where c.layout_id = %s order by sg.s_inicio_m""",
                (layout_id,),
            ).fetchall()
        ]

    eixos = _eixos_por_volta(conn, gravacao_id, voltas) if layout_id else {}
    faixas = micro_setores(float(comprimento)) if comprimento else []

    # tempo por curva (vindo de tempo_trecho, etapa 6) e por micro-setor, por
    # volta. Fatorado em `_tempos_por_trecho_por_volta` porque a gravacao de
    # referencia cruzada precisa exatamente da mesma conta, so que rodando
    # contra as PROPRIAS voltas dela.
    curva_por_volta, micro_por_volta = _tempos_por_trecho_por_volta(
        conn, voltas, faixas, eixos
    )

    if cruzada:
        eixos_ref = _eixos_por_volta(conn, ref_gid, voltas_ref_src) if layout_id else {}
        curva_por_volta_ref, micro_por_volta_ref = _tempos_por_trecho_por_volta(
            conn, voltas_ref_src, faixas, eixos_ref
        )
    else:
        curva_por_volta_ref, micro_por_volta_ref = curva_por_volta, micro_por_volta

    def _repeticao(tempos_por_volta: dict[int, dict[str, float]], ids) -> dict:
        """Desvio do tempo de cada trecho entre as voltas validas.

        Diz se a perda e erro pontual ou padrao, que e a pergunta do contrato.
        """
        saida = {}
        for tid in ids:
            serie = [
                tempos_por_volta[v["n"]][tid]
                for v in validas
                if v["n"] in tempos_por_volta and tid in tempos_por_volta[v["n"]]
            ]
            saida[tid] = float(np.std(serie)) if len(serie) > 1 else None
        return saida

    def _media_por_trecho(tempos_por_volta: dict[int, dict[str, float]]) -> dict:
        """Tempo medio de cada trecho entre as voltas validas."""
        soma: dict[str, list[float]] = {}
        for v in validas:
            for tid, tempo in tempos_por_volta.get(v["n"], {}).items():
                soma.setdefault(tid, []).append(tempo)
        return {tid: float(np.mean(xs)) for tid, xs in soma.items() if xs}

    analisada_curvas = curva_por_volta.get(n_analisada, {})
    analisada_micro = micro_por_volta.get(n_analisada, {})
    if ref_media:
        ref_curvas = _media_por_trecho(curva_por_volta)
        ref_micro = _media_por_trecho(micro_por_volta)
    else:
        ref_curvas = curva_por_volta_ref.get(n_ref, {})
        ref_micro = micro_por_volta_ref.get(n_ref, {})

    pilotagem = None
    if n_analisada in eixos:
        t, s = eixos[n_analisada]
        alvo = next(v for v in voltas if v["n"] == n_analisada)
        pilotagem = _pilotagem_por_trecho(
            conn,
            gravacao_id,
            curvas + faixas,
            t,
            s,
            t_inicio=alvo["t_inicio_s"],
            t_fim=alvo["t_fim_s"],
        )

    perdas_curva = perdas_por_trecho(
        curvas,
        analisada_curvas,
        ref_curvas,
        modo="curva",
        repeticao=_repeticao(curva_por_volta, [c["id"] for c in curvas]),
        pilotagem=pilotagem,
    )
    perdas_micro = perdas_por_trecho(
        faixas,
        analisada_micro,
        ref_micro,
        modo="micro_setor",
        repeticao=_repeticao(micro_por_volta, [f["id"] for f in faixas]),
        pilotagem=pilotagem,
    )

    todas = perdas_curva or perdas_micro
    n0_perdas = (
        _disponivel(itens=todas[:3])
        if todas
        else _degradado(
            "sem_setor",
            "sem tempo por trecho nesta volta: a decomposicao (etapa 6) nao rodou "
            "ou o eixo de distancia nao fechou no comprimento do layout",
        )
    )

    # --- tracado medido, quando a etapa 6 conseguiu derivar
    tracado = _degradado(
        "sem_gps", "sem GPS utilizavel nesta captura: o mapa da pista nao desenha"
    )
    linha_tracado = conn.execute(
        """select t.uri from tracado t join volta v on v.id = t.volta_id
            where v.session_id = %s and t.tipo = 'medido'
            order by v.lap_number limit 1""",
        (gravacao_id,),
    ).fetchone()
    if linha_tracado is not None:
        import pyarrow.parquet as pq

        from .storage import caminho_de_uri

        tabela = pq.read_table(caminho_de_uri(linha_tracado[0])).to_pydict()
        tracado = _disponivel(
            pontos=[
                {"x": x, "y": y, "s_m": s}
                for x, y, s in zip(
                    tabela["x_m"], tabela["y_m"], tabela["s_m"], strict=False
                )
            ]
        )

    # --- N3: canais disponiveis na captura
    #
    # `Canal.id` tem que ser a MESMA chave que aparece em `SerieAmostras.canais`,
    # senao o N3 lista um canal que o front nao consegue buscar. Canal com
    # de-para de apresentacao leva o id do front; o resto leva o nome bruto
    # normalizado, e continua achavel em vez de sumir da lista.
    canais = [
        {
            "id": c["id"],
            "rotulo": c["rotulo"],
            "unidade": c["unidade"],
            "uri": c["uri"],
            "frequencia_hz": c["frequencia_hz"],
            "n_amostras": c["n_amostras"],
        }
        for c in _canais_da_captura(conn, gravacao_id)
    ]

    # --- contexto de sessao (tabela `contexto`, dono polimorfico)
    #
    # Le o ultimo contexto capturado. A tabela e append-only por natureza (o
    # engenheiro pode registrar de novo quando a condicao muda, decisao 6), e o
    # que vale na tela e o mais recente.
    sessao = _degradado(
        "sem_contexto_sessao",
        "nenhum contexto de sessao capturado pra esta gravacao",
    )
    linha_ctx = conn.execute(
        """select pneu_estado, pneu_voltas_rodadas, pneu_composto, temp_ar_c,
                  temp_pista_c, vento_kmh, horario, notas_piloto,
                  notas_engenheiro, bateria_id
             from contexto
            where gravacao_id = %s or bateria_id = (
                    select bateria_id from gravacao where id = %s)
            order by criado_em desc limit 1""",
        (gravacao_id, gravacao_id),
    ).fetchone()
    if linha_ctx is not None:
        (
            pneu_estado,
            pneu_voltas,
            pneu_composto,
            ar,
            pista,
            vento,
            horario,
            nota_p,
            nota_e,
            bateria_id,
        ) = linha_ctx
        pneu = (
            _disponivel(
                estado=pneu_estado,
                voltas_rodadas=int(pneu_voltas) if pneu_voltas is not None else None,
                composto=pneu_composto,
            )
            if pneu_estado is not None
            else _degradado(
                "sem_contexto_pneu",
                "o contexto foi capturado mas o estado do pneu ficou em branco",
            )
        )
        sessao = _disponivel(
            pneu=pneu,
            temperatura_ar_c=float(ar) if ar is not None else None,
            temperatura_pista_c=float(pista) if pista is not None else None,
            vento_kmh=float(vento) if vento is not None else None,
            horario=horario.isoformat() if horario is not None else None,
            notas_piloto=nota_p,
            notas_engenheiro=nota_e,
            origem="bateria" if bateria_id is not None else "gravacao",
        )

    sem_combustivel = _degradado(
        "sem_canal_combustivel",
        "nenhum canal de nivel ou vazao de combustivel nesta captura",
    )

    for v in voltas:
        for interno in ("t_inicio_s", "t_fim_s", "volta_id"):
            v.pop(interno, None)

    return {
        "gravacao_id": str(gravacao_id),
        "piloto": piloto,
        "layout": (
            {
                "id": layout_id,
                "nome": layout_nome,
                "comprimento_m": float(comprimento),
            }
            if layout_id is not None
            else None
        ),
        # `layout_origem` nulo com layout preenchido e gravacao anterior a
        # migration 016: o unico degrau que existia era o alias, entao e ele.
        "resolucao_pista": (layout_origem or "alias") if layout_id is not None else "nao_resolvida",
        "amostra_da_captura": amostra_da_captura(
            arquivos_da_captura(conn, gravacao_id)
        ),
        "n0": {"melhor_volta": mv, "perdas_top3": n0_perdas},
        "n1": {
            "voltas": voltas,
            "consumo": {
                "media_etapa": sem_combustivel,
                "media_bateria": sem_combustivel,
            },
        },
        "trechos": (
            _disponivel(
                itens=[
                    {
                        "id": c["id"],
                        "rotulo": c["rotulo"],
                        "s_inicio_m": c["s_inicio_m"],
                        "s_fim_m": c["s_fim_m"],
                        "apex_m": c["apex_m"],
                    }
                    for c in curvas
                ]
            )
            if curvas
            else _degradado(
                "sem_catalogo_de_curva",
                "as curvas deste layout nao estao catalogadas",
            )
        ),
        "tracado": tracado,
        "n2": {
            "por_curva": (
                _disponivel(itens=perdas_curva)
                if perdas_curva
                else _degradado(
                    "sem_catalogo_de_curva",
                    "sem tempo por curva: curva exige catalogo de layout",
                )
            ),
            "por_micro_setor": (
                _disponivel(itens=perdas_micro)
                if perdas_micro
                else _degradado(
                    "sem_setor",
                    "sem eixo de distancia fechado pra recortar micro-setores",
                )
            ),
        },
        "n3": {"canais": canais},
        "contexto": {"setup": None, "sessao": sessao},
    }


# --- serie de amostras na grade comum ------------------------------------


def _canais_da_captura(conn, gravacao_id: str) -> list[dict]:
    """Todo canal da gravacao com serie guardada, com o `id` que o front usa.

    E a regra do N3 e de `amostras()` ao mesmo tempo, porque `Canal.id` tem que
    ser a MESMA chave de `SerieAmostras.canais`: canal com de-para de
    apresentacao leva o id do front; o resto leva o nome bruto normalizado.
    """
    apresentacao_por_canonico = {c: v[0] for c, v in APRESENTACAO.items()}
    usados: set[str] = set()
    canais = []
    for cid, nome_bruto, unidade, hz, n, uri, canonico in conn.execute(
        """select cg.id, cg.nome_bruto, cg.unidade_declarada, cg.frequencia_hz,
                  cg.n_amostras, s.uri, cg.canal_canonico_id
             from canal_gravado cg join serie_amostral s on s.id = cg.serie_id
            where cg.gravacao_id = %s order by s.frequencia_hz desc, cg.nome_bruto""",
        (gravacao_id,),
    ).fetchall():
        nome_front = apresentacao_por_canonico.get(canonico or "")
        if nome_front and nome_front not in usados:
            ident = nome_front
            unidade_saida = APRESENTACAO[canonico][2]
        else:
            ident = re.sub(r"[^a-z0-9]+", "_", nome_bruto.lower()).strip("_") or str(
                cid
            )
            unidade_saida = unidade or ""
        if ident in usados:
            ident = f"{ident}_{str(cid)[:8]}"
        usados.add(ident)
        canais.append(
            {
                "id": ident,
                "rotulo": nome_bruto,
                "unidade": unidade_saida,
                "uri": uri,
                "frequencia_hz": float(hz),
                "n_amostras": int(n),
                "nome_bruto": nome_bruto,
                "canonico": canonico,
            }
        )
    return canais


def _qualidade(valores) -> str:
    """Rotulo de qualidade de um canal dentro da volta (issue #59).

    `no_data`: nenhuma amostra finita na janela. `flat`: amostra existe mas nao
    varia (sensor gravado sem sinal). `ok`: o resto. O rotulo nunca remove o
    canal: quem desenha decide mostrar o aviso em vez do traco. `out_of_range`
    fica de fora ate existir faixa de plausibilidade ratificada por Vitor.
    """
    import numpy as np

    v = np.asarray(valores, dtype=float)
    finitos = v[np.isfinite(v)]
    if finitos.size == 0:
        return "no_data"
    if float(np.ptp(finitos)) == 0.0:
        return "flat"
    return "ok"


def _canais_de_apresentacao(conn, gravacao_id: str) -> dict[str, tuple]:
    """id do front -> (CanalEscolhido, fator de apresentacao, unidade).

    Quando dois canais brutos mapeiam pro mesmo canonico (o acervo tem `.ld`
    com Ground Speed e GPS Speed juntos), fica com o de maior taxa: e o mesmo
    critério da etapa 5, e `escolher_canal` ja ordena por taxa.
    """
    from .pipeline.leitura import escolher_canal

    saida: dict[str, tuple] = {}
    for canonico, (nome_front, fator, unidade) in APRESENTACAO.items():
        if nome_front in saida:
            continue
        canal = escolher_canal(conn, gravacao_id, (canonico,))
        if canal is not None:
            saida[nome_front] = (canal, fator, unidade)
    return saida


def _centros_de_marcha(rpm_cru: "np.ndarray", v_ms_cru: "np.ndarray"):
    """Centros da razao rpm/velocidade, um por marcha, a partir das series
    CRUAS. Tem que ser o dado nativo: a grade de 900 pontos e interpolada, e a
    interpolacao preenche o vao entre as marchas e apaga os clusters (medido
    em 29/08: no dado cru do Bortoleto c_1130 ha 6 picos nitidos; na grade,
    um continuo so). Devolve lista de centros ou None quando os clusters nao
    sao nitidos o bastante pra afirmar marcha."""
    import numpy as np

    confiavel = (
        (v_ms_cru > 8.0) & (rpm_cru > 1500.0)
        & np.isfinite(rpm_cru) & np.isfinite(v_ms_cru)
    )
    if int(confiavel.sum()) < 200:
        return None
    razao = rpm_cru[confiavel] / v_ms_cru[confiavel]
    # Histograma em LOG da razao: cada marcha e um pico (a razao da caixa
    # multiplica, entao o espacamento entre marchas e constante em log).
    # Deteccao por pico local, e nao por salto entre valores ordenados: com
    # dezenas de milhares de amostras as transicoes preenchem o espectro e
    # nunca ha salto, mas os picos continuam nitidos (medido no Bortoleto
    # c_1130: 6 picos, um por marcha do F3).
    logs = np.log(razao)
    p1, p99 = np.percentile(logs, [0.5, 99.5])
    if p99 - p1 < 0.05:
        return None
    hist, bordas = np.histogram(logs, bins=110, range=(p1, p99))
    suave = np.convolve(hist, np.ones(3) / 3, mode="same")
    # 0.8% das amostras e merge de 5%: calibrado em 29/08 contra tres
    # sessoes F3 (6 marchas nas tres, centros consistentes ~99/112/132/
    # 154/177/188); com piso menor, blips de downshift viravam pico.
    piso = max(3.0, 0.008 * logs.size)
    picos: list[float] = []
    for i in range(1, len(suave) - 1):
        if suave[i] > suave[i - 1] and suave[i] >= suave[i + 1] and suave[i] > piso:
            picos.append(float((bordas[i] + bordas[i + 1]) / 2))
    # merge de picos vizinhos (< 4% de razao): ruido de binagem, nao marcha
    unidos: list[float] = []
    for c in picos:
        if unidos and c - unidos[-1] < 0.05:
            unidos[-1] = (unidos[-1] + c) / 2
        else:
            unidos.append(c)
    centros = [float(np.exp(c)) for c in unidos]
    if not (2 <= len(centros) <= 8):
        return None
    return centros


def _atribuir_marcha(rpm: "np.ndarray", vel_kmh: "np.ndarray", centros: list[float]):
    """Marcha por proximidade ao centro, na grade de apresentacao. 0 fora da
    janela confiavel (carro lento, rpm de embreagem) = "sem marcha"."""
    import numpy as np

    v_ms = vel_kmh / 3.6
    confiavel = (v_ms > 8.0) & (rpm > 1500.0) & np.isfinite(rpm) & np.isfinite(v_ms)
    marcha = np.zeros(rpm.shape[0])
    if not confiavel.any():
        return marcha
    centros_arr = np.array(centros)
    razao = rpm[confiavel] / np.maximum(v_ms[confiavel], 0.1)
    idx = np.abs(
        np.log(np.maximum(razao, 1e-6))[:, None] - np.log(centros_arr)[None, :]
    ).argmin(axis=1)
    # razao MAIOR = marcha mais curta = numero MENOR
    marcha[confiavel] = len(centros) - idx
    return marcha


def amostras(conn, gravacao_id: str, volta: int | str) -> dict:
    """`SerieAmostras` de uma volta (ou a media das validas) na grade comum.

    Fica fora do `Relatorio` de proposito, como o contrato documenta: o
    relatorio e leve e cabe numa resposta, a amostra e pesada e vem sob demanda.

    A grade e uniforme em DISTANCIA, de zero ao comprimento do layout. E ela que
    permite sobrepor duas voltas e integrar o delta entre elas sem reamostrar no
    cliente.
    """
    import numpy as np

    from .pipeline.leitura import ler_colunas

    comprimento = conn.execute(
        """select l.comprimento_m from gravacao g join layout l on l.id = g.layout_id
            where g.id = %s""",
        (gravacao_id,),
    ).fetchone()
    if comprimento is None:
        raise ValueError(
            f"gravacao {gravacao_id} sem layout resolvido: sem comprimento nao "
            "existe grade de distancia (regra dura do B2)"
        )
    grade = np.linspace(0.0, float(comprimento[0]), GRADE_PONTOS)

    voltas, _ = _voltas_e_setores(conn, gravacao_id)
    eixos = _eixos_por_volta(conn, gravacao_id, voltas)
    alvo = (
        [v for v in voltas if v["valida"]]
        if volta == "media"
        else [v for v in voltas if v["n"] == volta]
    )
    if not alvo:
        raise ValueError(f"volta {volta} nao existe ou nao tem eixo de distancia")

    canais_fonte = _canais_de_apresentacao(conn, gravacao_id)
    leituras = {
        nome: (canal, fator, ler_colunas(canal.uri, [canal.nome_bruto]))
        for nome, (canal, fator, _unidade) in canais_fonte.items()
    }
    # Vinculo podre de era anterior: ate 29/08 o canal era ligado a serie so
    # pela TAXA, entao canal catalogado mas nunca materializado (bytes_amostra
    # indecodificavel) podia apontar pra um Parquet que nao tem a coluna dele.
    # O vinculo novo (por nome) nao cria mais isso, mas o legado existe no
    # banco; ler aqui estourava KeyError e derrubava a resposta inteira.
    # Pular o canal e a degradacao certa: os demais canais da volta continuam
    # saindo, e o canal fantasma simplesmente nao existe pra apresentacao.
    leituras = {
        nome: (canal, fator, dados)
        for nome, (canal, fator, dados) in leituras.items()
        if canal.nome_bruto in dados
    }

    # Todo canal do N3 que nao saiu por APRESENTACAO vai no valor gravado, sem
    # fator nem promessa de unidade (issue #59: canal com dado tem que chegar a
    # tela). Um Parquet por taxa guarda varios canais: le cada um uma vez so.
    from .pipeline.leitura import CanalEscolhido

    crus = [
        c for c in _canais_da_captura(conn, gravacao_id) if c["id"] not in canais_fonte
    ]
    por_uri: dict[str, list[dict]] = {}
    for c in crus:
        por_uri.setdefault(c["uri"], []).append(c)
    for uri, lista in por_uri.items():
        dados_uri = ler_colunas(uri, [c["nome_bruto"] for c in lista])
        for c in lista:
            if c["nome_bruto"] not in dados_uri:
                continue
            canal_cru = CanalEscolhido(
                canonico=c["canonico"] or "",
                nome_bruto=c["nome_bruto"],
                uri=uri,
                frequencia_hz=c["frequencia_hz"],
                fator=1.0,
                offset=0.0,
            )
            leituras[c["id"]] = (canal_cru, 1.0, dados_uri)
    ids_da_captura = [c["id"] for c in _canais_da_captura(conn, gravacao_id)]

    # Freio de PRESSAO -> % por normalizacao declarada. O canonico
    # `brake_press` guarda kPa (acervo.py descartou o normalize_by_max do
    # aliases de proposito: "quem precisa de 0 a 1 normaliza na analise,
    # declarando contra o que normalizou" - este e o passo que declara). A
    # regua vai da LINHA DE BASE (percentil 5 da gravacao inteira, porque tem
    # sensor que repousa deslocado do zero, ver comentario em APRESENTACAO) ao
    # PICO da gravacao inteira, e nao da volta: normalizar por volta faria a
    # volta de freada leve mostrar 100% onde o pe mal encostou. O par
    # (base, pico) fica pre-computado aqui e aplicado no loop de reamostragem
    # abaixo, sobre o valor ja em unidade fisica.
    # Direcao (ver APRESENTACAO): % do esterço maximo da gravacao, simetrica.
    regua_direcao: float | None = None
    if "direcao" in leituras:
        canal_d, _f, dados_d = leituras["direcao"]
        serie_d = canal_d.valores(dados_d)
        fin_d = np.abs(serie_d[np.isfinite(serie_d)])
        if fin_d.size >= 10 and float(np.max(fin_d)) > 0:
            regua_direcao = float(np.max(fin_d))

    regua_freio: tuple[float, float] | None = None
    if "freio" in leituras and leituras["freio"][0].canonico == "brake_press":
        canal_f, _fator_f, dados_f = leituras["freio"]
        serie_f = canal_f.valores(dados_f)
        finitos = serie_f[np.isfinite(serie_f)]
        if finitos.size >= 10:
            base = float(np.percentile(finitos, 5))
            pico = float(np.max(finitos))
            if pico > base:
                regua_freio = (base, pico)

    acumulado: dict[str, list] = {nome: [] for nome in leituras}
    vistos: dict[str, list] = {nome: [] for nome in leituras}
    for v in alvo:
        if v["n"] not in eixos:
            continue
        t_volta, s_volta = eixos[v["n"]]
        for nome, (canal, fator, dados) in leituras.items():
            t = dados["t_s"]
            todos = canal.valores(dados)
            # NaN e como o Parquet bruto marca "este canal nao amostrou neste
            # instante": o eixo t_s da serie e a UNIAO dos timestamps da taxa,
            # e canal esparso dentro do grupo tem celula vazia (contrato do
            # leitor). np.interp nao ignora NaN, ele CONTAMINA a saida inteira,
            # e um NaN que sobrevive ate o JSON quebra o parse no front
            # (medido em producao em 29/08, nos .xrk solo do F3 que so
            # ganharam volta com o degrau GPS). Interpolar SO nos pontos
            # medidos e a leitura honesta: os buracos viram interpolacao
            # declarada, igual ao alinhamento de taxa logo abaixo.
            na_volta = (t >= v["t_inicio_s"]) & (t <= v["t_fim_s"])
            vistos[nome].append(todos[na_volta])
            m = na_volta & np.isfinite(todos)
            if not m.any():
                continue
            if nome == "freio" and regua_freio is not None:
                base, pico = regua_freio
                valores = np.clip((todos[m] - base) / (pico - base), 0.0, 1.0) * 100.0
            elif nome == "direcao" and regua_direcao is not None:
                valores = np.clip(todos[m] / regua_direcao, -1.0, 1.0) * 100.0
            else:
                valores = todos[m] * fator
            # O canal pode ter taxa diferente do eixo: alinha no tempo primeiro,
            # depois interpola na grade de distancia. Duas interpolacoes, as
            # duas declaradas, em vez de assumir que as taxas coincidem.
            no_eixo = np.interp(t_volta, t[m], valores)
            acumulado[nome].append(np.interp(grade, s_volta, no_eixo))

    canais = {
        nome: [round(float(x), 4) for x in np.mean(series, axis=0)]
        for nome, series in acumulado.items()
        if series
    }
    if "marcha" not in canais and "rpm" in leituras and "velocidade" in leituras:
        # MARCHA DERIVADA: o acervo F3 tem GEAR_CALC zerado NA FONTE (o
        # logger nunca calculou; identico no libxrk), mas a razao
        # rpm/velocidade das series CRUAS clusteriza em picos nitidos, um
        # por marcha (6 picos no Bortoleto c_1130, um por marcha do F3).
        # Os CENTROS saem do dado nativo (a grade interpolada apaga os
        # clusters, ver `_centros_de_marcha`); a ATRIBUICAO acontece na
        # grade. Fora da janela confiavel o valor e 0 ("sem marcha"). E
        # derivacao declarada, nao leitura: este comentario e a regua.
        canal_r, _fr, dados_r = leituras["rpm"]
        canal_v, _fv, dados_v = leituras["velocidade"]
        rpm_cru = canal_r.valores(dados_r)
        v_cru_ms = canal_v.valores(dados_v)  # canonico speed ja e m/s
        # alinha a velocidade no tempo do rpm (taxas diferentes)
        v_no_rpm = np.interp(dados_r["t_s"], dados_v["t_s"], v_cru_ms)
        centros = _centros_de_marcha(np.asarray(rpm_cru), np.asarray(v_no_rpm))
        if centros is not None and "rpm" in canais and "velocidade" in canais:
            derivada = _atribuir_marcha(
                np.asarray(canais["rpm"], dtype=float),
                np.asarray(canais["velocidade"], dtype=float),
                centros,
            )
            canais["marcha"] = [float(v) for v in derivada]
    if "marcha" in canais:
        # Marcha e sinal de degrau: a dupla interpolacao acima (tempo e
        # distancia) produz 2.37 entre uma troca e outra, e marcha 2.37 nao
        # existe. Arredondar DEPOIS de reamostrar preserva o instante da
        # troca na resolucao da grade e devolve o dominio discreto do sinal.
        canais["marcha"] = [float(round(x)) for x in canais["marcha"]]
    if not canais:
        raise ValueError(
            f"volta {volta} sem canal com eixo de distancia fechado: rode a etapa 6"
        )
    qualidade = {
        nome: _qualidade(np.concatenate(partes)) if partes else "no_data"
        for nome, partes in vistos.items()
    }
    for ident in ids_da_captura:
        qualidade.setdefault(ident, "no_data")
    for nome in canais:
        qualidade.setdefault(nome, "ok")
    return {
        "volta": volta,
        "distancia_m": [round(float(x), 3) for x in grade],
        "canais": canais,
        "qualidade": qualidade,
    }
