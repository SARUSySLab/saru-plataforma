"""Deriva a posicao real das curvas de Curitiba a partir do dado medido.

CONTEXTO (2026-08-29): o comprimento de Curitiba estava errado no catalogo
(3220 m) e foi corrigido pra 3695 m (ver comentario em seeds/tracks.yaml). Mas
os 3 `sector_distances` e as 7 curvas do bloco `curitiba` foram levantados
contra os 3220 m errados, entao a posicao de cada curva esta deslocada em
relacao a pista real. A fonte upstream (saru-app/services/telemetry-api/
config/tracks.yaml) tem o MESMO erro, entao nao ha de onde copiar: a geometria
tem que ser DERIVADA do proprio dado medido.

POR QUE ACELERACAO LATERAL, NAO GPS
------------------------------------
As 67 voltas de Curitiba no banco vem de arquivos F309 (.xrk, AiM), que nao
gravam latitude/longitude: `canal_gravado` para essas gravacoes nao tem
`gps_lat`/`gps_lon` mapeado (confirmado por consulta direta antes de escrever
este script). O que existe e "Acc Lat" -> canal canonico `lat_acc`, em m/s^2
(fator 9.80665, ou seja o arquivo grava em g). O enunciado da tarefa preve essa
alternativa explicitamente: "aceleracao lateral se houver o canal". Sem GPS,
curvatura geometrica do tracado nao pode ser calculada; aceleracao lateral e o
canal fisico equivalente (curva = forca lateral sustentada) e e exatamente o
canal disponivel.

METODO
------
1. Escolhe as N melhores voltas de Curitiba: is_valid, dist_fator != null (ou
   seja, ja passaram pela etapa 6 e fecharam a distancia no comprimento do
   layout dentro da faixa 0.9-1.1), ordenadas por |dist_fator - 1| (fecho mais
   limpo primeiro).
2. Para cada volta, reconstroi o eixo de distancia com a MESMA cascata e o
   MESMO fechamento que o pipeline usa na etapa 6
   (`saru_poc.pipeline.decomposicao._eixo_da_volta` + `fechar_no_layout`),
   pra nao inventar um segundo metodo de medir distancia que diverge do que
   o banco ja usa pra decompor tempo por trecho.
3. Le `lat_acc` e `speed` na janela de tempo da volta, interpola cada canal no
   eixo de tempo do canal de distancia (cada canal tem sua propria taxa de
   amostragem) e reamostra em uma grade uniforme de distancia (passo
   `GRADE_PASSO_M`) de 0 a `length_m`.
4. Calcula a MEDIANA ponto a ponto de `lat_acc` e `speed` entre as voltas
   escolhidas. Mediana, nao media: robusta a uma volta ruim isolada (troca de
   linha, trafego) sem exigir excluir a volta inteira.
5. Detecta curva por CURVATURA SUSTENTADA em |lat_acc_mediana|, com histerese:
   um patamar FORTE define que ali existe curva (evita contar ruido como
   curva), um patamar FRACO define ate onde a zona da curva se estende pra
   tras e pra frente a partir do nucleo forte (senao a curva sai artificialmente
   estreita, so o pico). O apex e o ponto de |lat_acc| maximo dentro do nucleo.
6. Valida cada curva contra velocidade: o apex tem que cair perto (tolerancia
   `TOL_APEX_VELOCIDADE_M`) de um minimo local de `speed` mediana. Curva sem
   minimo de velocidade por perto e sinalizada, nao descartada (pode ser curva
   rapida, tipo Esesse, onde o carro nao chega a frear muito).
7. Curvas adjacentes de sinal OPOSTO e apex proximo (< `GAP_ESESSE_M`) sao o
   candidato natural a "Esesse" (complexo esquerda-direita): reporta as duas
   e propoe fusao em uma so entrada de catalogo, do jeito que o levantamento
   antigo tratava (um s_start/apex/end so cobrindo o complexo).
8. Setores: divide a volta em 3 tercos escolhendo, para cada fronteira alvo
   (length_m/3 e 2*length_m/3), o meio do maior GAP entre curvas mais proximo
   do alvo -- nunca um ponto dentro do span [s_start, s_end] de uma curva,
   pra nao esbarrar na trigger `tg_curva_dentro_do_setor` (que exige o apex
   dentro do setor dono).

Este script SO LE o banco e a serie Parquet; nao escreve nada. A saida e
YAML pronto pra colar em `seeds/tracks.yaml`, impressa em stdout, mais um
relatorio de sanidade (contagem, validacao contra velocidade, larguras).

Uso:
    .venv/bin/python scripts/derivar_curvas.py
    .venv/bin/python scripts/derivar_curvas.py --n-voltas 10 --grade 2.0
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from saru_poc.db import connect  # noqa: E402
from saru_poc.pipeline.decomposicao import (  # noqa: E402
    FATOR_MAX,
    FATOR_MIN,
    _eixo_da_volta,
    fechar_no_layout,
)
from saru_poc.pipeline.leitura import escolher_canal, ler_colunas  # noqa: E402

# Nasceu fixo em Curitiba (ver o contexto acima). Virou parametro em 30/08 pra
# derivar tambem o Nelson Piquet, que entrou no catalogo com 3 setores e ZERO
# curva: sem curva catalogada, o bloco "onde ganhar tempo" so tem o modo de
# micro-setor e o modo por curva sai degradado, dizendo o porque.
LAYOUT_ID = "curitiba"
LENGTH_M = 3695.0

GRADE_PASSO_M = 2.0

# Patamares de |lat_acc| em m/s^2. 1 g = 9.80665 m/s^2; um carro de pista em
# curva de raio medio sustenta 0.7-1.3 g, entao o patamar forte fica bem
# abaixo disso de proposito (curva lenta tambem e curva).
LIMIAR_FORTE = 4.0  # ~0.41 g -- confirma que ali E curva
LIMIAR_FRACO = 1.3  # ~0.13 g -- ate onde a zona da curva se estende

# Nucleos fortes separados por menos que isso na mesma direcao de curvatura
# sao o mesmo pico partido por ruido, nao duas curvas.
GAP_MERGE_MESMA_DIRECAO_M = 12.0

# Vao entre nucleos vizinhos abaixo do qual nao ha espaco fisico pra serem
# duas curvas independentes (sem reta real entre elas), entao viram UM
# registro de curva so. Calibrado pelos proprios gaps medidos em Curitiba:
# os 3 nucleos da zona 470-862 tem vao de 6-8 m entre si (claramente colados),
# enquanto o proximo vao livre (nucleo 2 -> nucleo 3) e de 474 m. 15 m fica
# folgado o bastante pra pegar o cluster colado sem juntar corners que tem
# reta de verdade entre eles (o menor vao "livre" medido foi 20 m).
GAP_ESESSE_M = 15.0

# Curva minima levada a serio (largura do nucleo forte). Abaixo disso e
# transiente de troca de direcao, nao curva com identidade propria.
LARGURA_MIN_NUCLEO_M = 15.0

TOL_APEX_VELOCIDADE_M = 90.0

N_VOLTAS_PADRAO = 8

# Fracao minima da grade de distancia que `lat_acc` precisa cobrir pra volta
# entrar na mediana. Volta abaixo disso e descartada inteira.
COBERTURA_MIN_DA_VOLTA = 0.8


@dataclass
class VoltaEscolhida:
    volta_id: str
    session_id: str
    lap_number: int
    lap_time_s: float
    dist_fator_banco: float


def escolher_voltas(conn, n: int) -> list[VoltaEscolhida]:
    """As N melhores voltas de Curitiba pra derivar geometria.

    "Melhor" = valida, ja decomposta (dist_fator gravado pela etapa 6) e com o
    fechamento mais limpo (|fator - 1| pequeno). dist_fator gravado e o da
    ultima corrida do pipeline oficial; este script recalcula o proprio no
    passo 2 (mesma formula) so pra ter o eixo em maos, os dois tem que bater.
    """
    linhas = conn.execute(
        """select id, session_id, lap_number, lap_time_s, dist_fator
             from volta
            where layout_id = %s and is_valid and dist_fator is not null
            order by abs(dist_fator - 1.0) asc
            limit %s""",
        (LAYOUT_ID, n),
    ).fetchall()
    return [
        VoltaEscolhida(str(vid), str(sid), int(ln), float(lt), float(df))
        for vid, sid, ln, lt, df in linhas
    ]


def serie_no_eixo_de_distancia(
    conn, session_id: str, t_inicio: float, t_fim: float
) -> tuple[np.ndarray, np.ndarray, float, str] | None:
    """(s_m fechado no layout, t_s do canal de distancia, fator, origem).

    Reusa a cascata oficial da etapa 6 (_eixo_da_volta) e o mesmo fechamento
    (fechar_no_layout) pra que a distancia aqui seja a MESMA que o pipeline
    usaria se rodasse decompor nesta volta -- nao um segundo metodo.
    """
    t, s, origem_ou_motivo = _eixo_da_volta(conn, session_id, t_inicio, t_fim)
    if t is None:
        return None
    s_fechado, fator, motivo = fechar_no_layout(s, LENGTH_M)
    if s_fechado is None:
        return None
    return s_fechado, t, fator, origem_ou_motivo


def canal_interpolado_no_tempo(
    conn, session_id: str, canonicos: tuple[str, ...], t_alvo: np.ndarray
) -> np.ndarray | None:
    """Le um canal e interpola seus valores nos instantes `t_alvo`.

    `t_alvo` vem do canal de distancia, que tem sua propria taxa; lat_acc e
    speed quase sempre vem de series com taxa diferente (50 Hz vs a do
    logger), entao precisam ser levados pro mesmo eixo de tempo antes de virar
    funcao de distancia.
    """
    canal = escolher_canal(conn, session_id, canonicos)
    if canal is None:
        return None
    dados = ler_colunas(canal.uri, [canal.nome_bruto])
    if "t_s" not in dados or canal.nome_bruto not in dados:
        return None
    t_canal = np.asarray(dados["t_s"], dtype=float)
    v_canal = np.asarray(canal.valores(dados), dtype=float)

    # O Parquet tem uma linha por instante de amostragem do arquivo INTEIRO, e
    # cada canal so preenche as linhas da propria taxa: um canal de 10 Hz num
    # arquivo que tem canal de 50 Hz vem com 80% de NaN. `np.interp` propaga
    # esses NaN pro alvo, o que aqui esvaziava o perfil da volta. Ficar so com
    # as amostras reais antes de interpolar e o que reconstroi a serie
    # continua -- que e exatamente o que interpolar quer dizer.
    real = np.isfinite(t_canal) & np.isfinite(v_canal)
    if real.sum() < 2:
        return None
    t_canal, v_canal = t_canal[real], v_canal[real]

    ordem = np.argsort(t_canal)
    return np.interp(t_alvo, t_canal[ordem], v_canal[ordem])


def coletar_voltas(conn, voltas: list[VoltaEscolhida], grade: np.ndarray) -> dict:
    """Monta lat_acc(grade) e speed(grade) por volta, so as que deram certo."""
    linha_id, t_inicio_map = {}, {}
    for v in voltas:
        row = conn.execute(
            "select t_inicio_s, t_fim_s from volta where id = %s", (v.volta_id,)
        ).fetchone()
        t_inicio_map[v.volta_id] = (float(row[0]), float(row[1]))

    lat_acc_por_volta = []
    speed_por_volta = []
    usadas = []
    for v in voltas:
        t_inicio, t_fim = t_inicio_map[v.volta_id]
        eixo = serie_no_eixo_de_distancia(conn, v.session_id, t_inicio, t_fim)
        if eixo is None:
            print(f"  [pula] volta {v.lap_number} ({v.volta_id[:8]}): sem eixo de distancia")
            continue
        s_m, t_s, fator, origem = eixo
        if not (FATOR_MIN <= fator <= FATOR_MAX):
            print(f"  [pula] volta {v.lap_number}: fator {fator:.3f} fora da faixa")
            continue

        lat_acc_t = canal_interpolado_no_tempo(conn, v.session_id, ("lat_acc",), t_s)
        speed_t = canal_interpolado_no_tempo(conn, v.session_id, ("speed",), t_s)
        if lat_acc_t is None or speed_t is None:
            print(f"  [pula] volta {v.lap_number}: falta lat_acc ou speed")
            continue

        ordem = np.argsort(s_m)
        s_ord = s_m[ordem]
        lat_acc_grade = np.interp(grade, s_ord, lat_acc_t[ordem])
        speed_grade = np.interp(grade, s_ord, speed_t[ordem])
        lat_acc_por_volta.append(lat_acc_grade)
        speed_por_volta.append(speed_grade)
        usadas.append((v, fator, origem))
        print(
            f"  [ok]   volta {v.lap_number:>2} ({v.volta_id[:8]}) "
            f"lap_time={v.lap_time_s:.1f}s fator={fator:.4f} origem={origem}"
        )

    return {
        "usadas": usadas,
        "lat_acc": np.array(lat_acc_por_volta),
        "speed": np.array(speed_por_volta),
    }


@dataclass
class NucleoCurva:
    i_ini: int
    i_fim: int
    sinal: int  # +1 ou -1, direcao dominante de lat_acc no nucleo


def detectar_nucleos(lat_acc_mediana: np.ndarray, grade: np.ndarray) -> list[NucleoCurva]:
    """Regioes contiguas onde |lat_acc| > LIMIAR_FORTE, mesmo sinal dominante.

    Passo do "existe curva aqui": so o patamar forte, sem histerese ainda --
    a extensao com o patamar fraco acontece depois, em `expandir_zona`.
    """
    acima = np.abs(lat_acc_mediana) > LIMIAR_FORTE
    nucleos: list[NucleoCurva] = []
    i = 0
    n = len(acima)
    while i < n:
        if not acima[i]:
            i += 1
            continue
        j = i
        while j < n and acima[j]:
            j += 1
        nucleos.append(NucleoCurva(i, j - 1, int(np.sign(np.sum(lat_acc_mediana[i:j])))))
        i = j

    # funde nucleos vizinhos de MESMA direcao separados por um vao curto
    # (ruido dentro do mesmo pico, nao duas curvas)
    fundidos: list[NucleoCurva] = []
    for nu in nucleos:
        if fundidos:
            anterior = fundidos[-1]
            gap_m = grade[nu.i_ini] - grade[anterior.i_fim]
            if anterior.sinal == nu.sinal and gap_m < GAP_MERGE_MESMA_DIRECAO_M:
                fundidos[-1] = NucleoCurva(anterior.i_ini, nu.i_fim, anterior.sinal)
                continue
        fundidos.append(nu)

    # descarta nucleo estreito demais pra ter identidade propria
    largura_min_pts = max(1, int(LARGURA_MIN_NUCLEO_M / (grade[1] - grade[0])))
    return [n for n in fundidos if (n.i_fim - n.i_ini) >= largura_min_pts]


@dataclass
class Curva:
    s_start: float
    s_apex: float
    s_end: float
    sinal: int  # +1, -1, ou 0 se o grupo mistura sinal (complexo)
    apex_lat_acc_g: float
    valida_por_velocidade: bool
    dist_apex_minimo_velocidade_m: float
    n_subpicos: int
    sinais_subpicos: tuple[int, ...]


def expandir_zona(
    i_ini: int,
    i_fim: int,
    lat_acc_mediana: np.ndarray,
    grade: np.ndarray,
    limite_esq: int,
    limite_dir: int,
) -> tuple[int, int]:
    """Estende a zona pra tras/frente enquanto |lat_acc| > LIMIAR_FRACO.

    O nucleo forte sozinho so pega o miolo da curva (onde a forca lateral ja
    esta alta); a zona real de freada/saida comeca antes/depois disso, no
    ponto em que o carro ainda esta claramente arqueando mas nao no pico.
    """
    while i_ini > limite_esq and abs(lat_acc_mediana[i_ini - 1]) > LIMIAR_FRACO:
        i_ini -= 1
    while i_fim < limite_dir and abs(lat_acc_mediana[i_fim + 1]) > LIMIAR_FRACO:
        i_fim += 1
    return i_ini, i_fim


def minimos_locais(v: np.ndarray) -> np.ndarray:
    """Indices onde v[i] e minimo local (vizinho imediato maior ou igual)."""
    idx = []
    for i in range(1, len(v) - 1):
        if v[i] <= v[i - 1] and v[i] <= v[i + 1]:
            idx.append(i)
    return np.array(idx, dtype=int)


def agrupar_nucleos(nucleos: list[NucleoCurva], grade: np.ndarray) -> list[list[NucleoCurva]]:
    """Encadeia nucleos vizinhos (qualquer sinal) separados por vao curto.

    Isso e o que decide se um trecho vira 1 curva ou 2+: nucleos a menos de
    GAP_ESESSE_M um do outro nao tem espaco fisico pra serem duas curvas
    independentes (nao ha reta entre eles), entao viram UM registro de curva
    so, mesmo que troquem de sinal (Esesse) ou tenham 3+ sub-picos colados
    (complexo). A decisao de rotulo fica pra depois; aqui so agrupa.
    """
    grupos: list[list[NucleoCurva]] = [[nucleos[0]]]
    for nu in nucleos[1:]:
        gap_m = grade[nu.i_ini] - grade[grupos[-1][-1].i_fim]
        if gap_m < GAP_ESESSE_M:
            grupos[-1].append(nu)
        else:
            grupos.append([nu])
    return grupos


def montar_curvas(
    grupos: list[list[NucleoCurva]],
    lat_acc_mediana: np.ndarray,
    speed_mediana: np.ndarray,
    grade: np.ndarray,
) -> list[Curva]:
    idx_min_vel = minimos_locais(speed_mediana)
    s_min_vel = grade[idx_min_vel]

    curvas = []
    for k, grupo in enumerate(grupos):
        limite_esq = grupos[k - 1][-1].i_fim if k > 0 else 0
        limite_dir = grupos[k + 1][0].i_ini if k + 1 < len(grupos) else len(grade) - 1
        i_ini, i_fim = expandir_zona(
            grupo[0].i_ini, grupo[-1].i_fim, lat_acc_mediana, grade, limite_esq, limite_dir
        )

        janela = slice(grupo[0].i_ini, grupo[-1].i_fim + 1)
        i_apex_local = np.argmax(np.abs(lat_acc_mediana[janela]))
        i_apex = grupo[0].i_ini + i_apex_local
        s_apex = float(grade[i_apex])

        if len(s_min_vel):
            dist = float(np.min(np.abs(s_min_vel - s_apex)))
        else:
            dist = float("inf")

        sinais = tuple(nu.sinal for nu in grupo)
        sinal_grupo = sinais[0] if len(set(sinais)) == 1 else 0

        curvas.append(
            Curva(
                s_start=float(grade[i_ini]),
                s_apex=s_apex,
                s_end=float(grade[i_fim]),
                sinal=sinal_grupo,
                apex_lat_acc_g=float(lat_acc_mediana[i_apex]) / 9.80665,
                valida_por_velocidade=dist <= TOL_APEX_VELOCIDADE_M,
                dist_apex_minimo_velocidade_m=dist,
                n_subpicos=len(grupo),
                sinais_subpicos=sinais,
            )
        )
    return curvas


def escolher_setores(curvas: list[Curva], length_m: float) -> list[float]:
    """2 fronteiras internas de setor, nos tercos, sem cortar nenhuma curva.

    Fronteira valida = fora de todo intervalo [s_start, s_end] de curva (a
    trigger do banco so exige apex dentro do setor dono, mas cortar uma curva
    ao meio no tempo por trecho seria um numero sem sentido fisico mesmo
    passando no banco, entao a guarda aqui e mais estrita que a do banco de
    proposito).
    """
    ocupado = [(c.s_start, c.s_end) for c in curvas]

    def livre(s: float) -> bool:
        return all(not (a <= s <= b) for a, b in ocupado)

    def fronteira_mais_proxima(alvo: float) -> float:
        if livre(alvo):
            return alvo
        # anda pros dois lados a partir do alvo ate achar vao livre
        passo = 1.0
        while True:
            for cand in (alvo - passo, alvo + passo):
                if 0 < cand < length_m and livre(cand):
                    return cand
            passo += 1.0
            if passo > length_m:
                raise RuntimeError("nao achei fronteira de setor livre de curva")

    b1 = fronteira_mais_proxima(length_m / 3)
    b2 = fronteira_mais_proxima(2 * length_m / 3)
    return [round(b1, 1), round(b2, 1)]


def rotular(curvas: list[Curva]) -> list[str]:
    """Rotula por ordem, a partir da FORMA de cada curva, nunca da contagem.

    A tentacao seria "se deu 7, usa os nomes antigos por posicao" -- e foi o
    que a primeira versao deste script fazia, e é errado: contagem batendo
    com o levantamento antigo por coincidencia nao significa que a curva
    daquela posicao é a mesma curva. O rotulo aqui sai so de `n_subpicos` e
    `sinais_subpicos`, que sao propriedade da propria curva, nao da lista.

    - 2 sub-picos de sinal oposto (troca de direcao) = Esesse classico.
    - 3+ sub-picos colados = complexo, nomeado explicitamente como tal (o
      dado nao da pra saber se e "Curva 1 seguida de Esesse" ou uma curva so
      com re-arqueamento; nao adivinho, reporto o achado).
    - 1 sub-pico = curva simples, numerada em sequencia; a ultima antes da
      reta de chegada vira "Última" (mesma convencao do catalogo antigo).
    """
    n = len(curvas)
    rotulos = []
    numero = 1
    for i, c in enumerate(curvas):
        ultima = i == n - 1
        base = "Última" if ultima else f"Curva {numero}"
        if not ultima:
            numero += 1
        if c.n_subpicos == 2 and len(set(c.sinais_subpicos)) == 2:
            rotulos.append(f"{base} = Esesse (2 sub-picos)")
        elif c.n_subpicos >= 3:
            rotulos.append(
                f"{base} = complexo ({c.n_subpicos} sub-picos, "
                "possivelmente cobre 2 curvas do levantamento antigo)"
            )
        else:
            rotulos.append(base)
    return rotulos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layout", default="curitiba", help="id do layout no catalogo")
    ap.add_argument("--comprimento", type=float, default=None,
                    help="comprimento do layout em metros (default: o do banco)")
    ap.add_argument("--n-voltas", type=int, default=N_VOLTAS_PADRAO)
    ap.add_argument("--grade", type=float, default=GRADE_PASSO_M)
    ap.add_argument("--fundir-esesse", action="store_true", default=True)
    ap.add_argument("--nao-fundir-esesse", dest="fundir_esesse", action="store_false")
    args = ap.parse_args()

    globals()["LAYOUT_ID"] = args.layout
    if args.comprimento:
        globals()["LENGTH_M"] = args.comprimento
    else:
        with connect() as conn:
            linha = conn.execute(
                "select comprimento_m from layout where id = %s", (LAYOUT_ID,)
            ).fetchone()
        if linha is None:
            print(f"ERRO: layout {LAYOUT_ID} nao existe no catalogo.")
            return 1
        globals()["LENGTH_M"] = float(linha[0])

    grade = np.arange(0.0, LENGTH_M + args.grade, args.grade)

    with connect() as conn:
        candidatas = escolher_voltas(conn, args.n_voltas * 2)  # folga p/ descarte
        print(f"== {LAYOUT_ID}: {len(candidatas)} voltas candidatas (de {args.n_voltas * 2} pedidas) ==")
        coleta = coletar_voltas(conn, candidatas[: args.n_voltas], grade)

    lat_acc = np.asarray(coleta["lat_acc"], dtype=float)
    speed = np.asarray(coleta["speed"], dtype=float)
    usadas = list(coleta["usadas"])

    # Volta com buraco grande na grade (canal que nao cobre a volta inteira,
    # ou lacuna de amostragem) contamina a mediana ponto a ponto: `np.median`
    # propaga NaN, entao UMA volta sem cobertura zera o perfil inteiro e o
    # detector reporta "0 nucleos" como se a pista nao tivesse curva. Duas
    # protecoes, nesta ordem: descartar a volta que nao cobre o minimo da
    # grade, e usar `nanmedian` no que sobrou (buraco pontual de uma volta
    # nao derruba o ponto, as outras sustentam).
    cobertura = np.mean(np.isfinite(lat_acc), axis=1)
    tem_cobertura = cobertura >= COBERTURA_MIN_DA_VOLTA
    for i, (volta, _fator, _origem) in enumerate(usadas):
        if not tem_cobertura[i]:
            print(
                f"  [fora] volta {volta.lap_number} ({volta.volta_id[:8]}): "
                f"lat_acc cobre so {cobertura[i] * 100:.0f}% da grade "
                f"(minimo {COBERTURA_MIN_DA_VOLTA * 100:.0f}%)"
            )
    lat_acc = lat_acc[tem_cobertura]
    speed = speed[tem_cobertura]
    usadas = [v for i, v in enumerate(usadas) if tem_cobertura[i]]

    if len(usadas) < 5:
        print(f"ERRO: so {len(usadas)} voltas utilizaveis, menos que o minimo de 5.")
        return 1

    print(f"\n{len(usadas)} voltas entraram na mediana.")

    lat_acc_mediana = np.nanmedian(lat_acc, axis=0)
    speed_mediana = np.nanmedian(speed, axis=0)

    nucleos = detectar_nucleos(lat_acc_mediana, grade)
    print(f"\n{len(nucleos)} nucleos de curvatura sustentada (|lat_acc| > {LIMIAR_FORTE} m/s^2):")
    for i, nu in enumerate(nucleos):
        sinal_txt = "esquerda" if nu.sinal > 0 else "direita"
        print(f"  nucleo {i}: s=[{grade[nu.i_ini]:.1f}, {grade[nu.i_fim]:.1f}]  {sinal_txt}")

    grupos = agrupar_nucleos(nucleos, grade) if args.fundir_esesse else [[n] for n in nucleos]
    multi = [g for g in grupos if len(g) > 1]
    if multi:
        print(f"\n{len(multi)} grupo(s) com mais de 1 sub-pico colado (vao < {GAP_ESESSE_M} m):")
        for g in multi:
            sinais_txt = ["esquerda" if nu.sinal > 0 else "direita" for nu in g]
            print(f"  s=[{grade[g[0].i_ini]:.1f}, {grade[g[-1].i_fim]:.1f}]  sequencia: {sinais_txt}")
    else:
        print("\nNenhum grupo com sub-picos colados.")

    curvas_finais = montar_curvas(grupos, lat_acc_mediana, speed_mediana, grade)
    print(f"\n{len(curvas_finais)} curvas finais (apos agrupar sub-picos colados):")
    for i, c in enumerate(curvas_finais):
        ok = "OK" if c.valida_por_velocidade else "SEM min. de velocidade por perto"
        print(
            f"  [{i}] s=[{c.s_start:7.1f}, {c.s_apex:7.1f}, {c.s_end:7.1f}]  "
            f"{c.n_subpicos} sub-pico(s) {c.sinais_subpicos}  apex={c.apex_lat_acc_g:+.2f}g  "
            f"valida_vel={ok} (dist={c.dist_apex_minimo_velocidade_m:.0f}m)"
        )

    setores = escolher_setores(curvas_finais, LENGTH_M)
    rotulos = rotular(curvas_finais)

    print(f"\n== RESULTADO: {len(curvas_finais)} curvas, setores em {setores} ==")
    print("\nComparacao com o levantamento antigo (contra 3220 m errados):")
    print(f"  antigo:  sector_distances=[950.0, 2050.0, 3220.0], 7 curvas")
    print(f"  derivado: sector_distances=[{setores[0]}, {setores[1]}, {LENGTH_M}], {len(curvas_finais)} curvas")

    print("\n--- YAML pronto pra colar em seeds/tracks.yaml ---\n")
    print(f"    sector_distances: [{setores[0]}, {setores[1]}, {LENGTH_M}]")
    print("    corners:")
    for i, (c, label) in enumerate(zip(curvas_finais, rotulos), start=1):
        print(
            f'      - {{corner_id: T{i}, label: "{label}", '
            f"s_start: {c.s_start:.1f}, s_apex: {c.s_apex:.1f}, s_end: {c.s_end:.1f}}}"
        )

    print("\n--- voltas usadas ---")
    for v, fator, origem in usadas:
        print(f"  volta {v.lap_number} ({v.volta_id}) fator={fator:.4f} origem={origem}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
