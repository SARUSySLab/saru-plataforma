"""Etapa 6: decomposicao.

Setor e curva moram em DISTANCIA (`segmento.s_inicio_m` e `s_fim_m`); a amostra
vem em TEMPO. Decompor uma volta e cruzar os dois eixos: descobrir em que
instante o carro passou por cada fronteira de trecho, e a diferenca entre dois
instantes e o tempo daquele trecho.

O eixo de distancia vem por cascata, decisao do Lucas (29/08):

  1. canal de distancia do proprio arquivo (16 gravacoes do acervo);
  2. integral da velocidade no tempo (40);
  3. deslocamento acumulado do GPS (3);
  4. nao decompoe, com o motivo.

Depois de medido, o eixo e FECHADO no comprimento do layout por um fator
linear, gravado em `volta.dist_fator`. Integrar velocidade acumula erro de
calibracao, e sem fechar a volta o ultimo setor absorve toda a sobra enquanto
as fronteiras internas escorregam. Escalar sem declarar seria maquiagem; por
isso o fator e coluna, nao constante escondida aqui.

A guarda de faixa (0,9 a 1,1) e da familia do B1: fora dela nao e calibracao, e
pista errada ou volta mal cortada, e a volta fica SEM decomposicao em vez de
receber setor de outra pista. O B1 original somava setores de Interlagos
(4.309 m) numa volta de kart de 1,1 km: aqui isso daria fator 3,9 e a volta
seria recusada antes de virar numero.

Duas bordas sao ancoradas de proposito: o inicio do primeiro setor e o fim do
ultimo recebem `volta.t_inicio_s` e `volta.t_fim_s` em vez do valor
interpolado. Os setores particionam a volta inteira (medido no catalogo: 3
setores por layout, de 0 ao comprimento), entao a soma dos tempos de setor TEM
que dar o tempo da volta. Sem ancorar, a interpolacao deixa sobra nas pontas e
a soma discorda do arquivo, que e justamente o que o trigger da 006 barra.

Curva nao entra nessa soma: e subdivisao de um setor, e somar os dois niveis
contaria o mesmo pedaco de pista duas vezes. O trigger da 006 tambem filtra por
tipo='setor' pelo mesmo motivo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .leitura import escolher_canal, ler_colunas, par_gps

METODO_VERSAO = "interp_por_distancia-1"

# Fora desta faixa a divergencia entre o eixo medido e o comprimento do layout
# deixa de ser calibracao. Espelha o CHECK da migration 012: o codigo recusa
# antes, o banco recusa depois, e nenhum dos dois confia no outro.
FATOR_MIN, FATOR_MAX = 0.9, 1.1

R_TERRA_M = 6_371_000.0

# Minimo de amostras dentro da janela de uma volta pra interpolar fronteira.
# Com menos que isso a volta existe no relogio mas nao tem forma: o canal de
# volta era de 1 Hz e a volta durou 5 s, ou a janela caiu fora da serie.
MIN_AMOSTRAS = 8


@dataclass
class Decomposicao:
    volta_id: str
    numero: int
    dist_origem: str | None = None
    dist_fator: float | None = None
    tempos: dict[str, float] = field(default_factory=dict)
    curvas: int = 0
    setores: int = 0
    motivo: str | None = None

    @property
    def decompos(self) -> bool:
        return bool(self.tempos)


@dataclass
class ResumoDecomposicao:
    decompostas: int = 0
    nao_decompostas: int = 0
    ja_decompostas: int = 0
    trechos: int = 0
    por_origem: dict[str, int] = field(default_factory=dict)
    por_motivo: dict[str, int] = field(default_factory=dict)
    fatores: list[float] = field(default_factory=list)


# --- motor puro ----------------------------------------------------------


def distancia_por_canal(dist_bruta: np.ndarray) -> np.ndarray:
    """Eixo de distancia a partir do canal de distancia do arquivo.

    `Lap Distance` zera a cada passagem pela linha. Dentro da janela de uma
    volta o reset cai na fronteira, mas cai: por isso a conta e sobre o
    incremento, descartando o salto negativo, em vez de `dist - dist[0]`. O
    metro perdido no instante do reset e menor que a resolucao do canal; usar a
    diferenca crua trocaria o sinal do trecho inteiro.
    """
    if len(dist_bruta) < 2:
        return np.zeros(len(dist_bruta))
    passo = np.diff(dist_bruta)
    passo[passo < 0] = 0.0
    return np.concatenate([[0.0], np.cumsum(passo)])


def distancia_por_velocidade(t_s: np.ndarray, v_ms: np.ndarray) -> np.ndarray:
    """Integral trapezoidal da velocidade. Velocidade negativa nao anda pra tras.

    Marcha a re em track day nao existe, e canal de velocidade sem sinal as
    vezes devolve valor negativo por ruido de sensor. Somar isso encurtaria a
    volta.
    """
    if len(t_s) < 2:
        return np.zeros(len(t_s))
    v = np.clip(v_ms, 0.0, None)
    dt = np.diff(t_s)
    passo = 0.5 * (v[:-1] + v[1:]) * dt
    return np.concatenate([[0.0], np.cumsum(passo)])


def distancia_por_gps(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Deslocamento acumulado entre pontos consecutivos, em metros.

    Projecao equiretangular na latitude media da janela: numa volta de pista o
    alcance e de poucos quilometros, e o erro da projecao fica ordens de
    grandeza abaixo do ruido do proprio GPS.
    """
    if len(lat) < 2:
        return np.zeros(len(lat))
    lat0 = float(np.mean(lat))
    k = math.cos(math.radians(lat0))
    x = np.radians(lon) * R_TERRA_M * k
    y = np.radians(lat) * R_TERRA_M
    passo = np.hypot(np.diff(x), np.diff(y))
    return np.concatenate([[0.0], np.cumsum(passo)])


def fechar_no_layout(
    s_m: np.ndarray, comprimento_m: float
) -> tuple[np.ndarray | None, float, str | None]:
    """Escala o eixo pra fechar o comprimento do layout. Guarda de faixa dura.

    Devolve (eixo, fator, motivo). Com motivo preenchido o eixo vem nulo: a
    volta fica sem decomposicao, que e o resultado correto quando o eixo e o
    layout discordam por algo que nao e calibracao.
    """
    medido = float(s_m[-1]) if len(s_m) else 0.0
    if medido <= 0:
        return None, 0.0, "eixo de distancia nao avanca (volta parada ou canal morto)"
    fator = comprimento_m / medido
    if not (FATOR_MIN <= fator <= FATOR_MAX):
        motivo = (
            f"eixo de distancia mede {medido:.0f} m contra {comprimento_m:.0f} m do "
            f"layout (fator {fator:.2f}, fora de {FATOR_MIN} a {FATOR_MAX})"
        )
        return None, fator, motivo
    return s_m * fator, fator, None


def tempos_por_segmento(
    t_s: np.ndarray,
    s_m: np.ndarray,
    segmentos: list[tuple[str, str, float, float]],
    *,
    t_inicio: float,
    t_fim: float,
) -> dict[str, float]:
    """Tempo de cada segmento, por interpolacao do tempo na distancia.

    `segmentos` e uma lista de (id, tipo, s_inicio_m, s_fim_m) do layout. As
    bordas externas dos setores sao ancoradas em `t_inicio`/`t_fim` da volta,
    ver a nota no topo do modulo.
    """
    if len(t_s) < 2:
        return {}
    tempos: dict[str, float] = {}
    s_total = float(s_m[-1])
    for seg_id, tipo, s_ini, s_fim in segmentos:
        a = float(np.interp(s_ini, s_m, t_s))
        b = float(np.interp(s_fim, s_m, t_s))
        if tipo == "setor":
            if s_ini <= 0.0:
                a = t_inicio
            if s_fim >= s_total:
                b = t_fim
        if b <= a:
            # Trecho que nao avanca no tempo nao e trecho: acontece quando o
            # eixo tem platô (carro parado) exatamente na fronteira.
            continue
        tempos[seg_id] = b - a
    return tempos


# --- leitura, cascata e persistencia -------------------------------------


def _segmentos_do_layout(conn, layout_id: str) -> list[tuple[str, str, float, float]]:
    return [
        (str(sid), tipo, float(a), float(b))
        for sid, tipo, a, b in conn.execute(
            """select id, tipo, s_inicio_m, s_fim_m from segmento
                where layout_id = %s and tipo in ('setor','curva')
                order by tipo, ordem""",
            (layout_id,),
        ).fetchall()
    ]


def _eixo_da_volta(
    conn, gravacao_id: str, t_inicio: float, t_fim: float
) -> tuple[np.ndarray, np.ndarray, str] | tuple[None, None, str]:
    """Cascata do eixo de distancia dentro da janela de uma volta.

    Devolve (t da janela, s da janela, origem) ou (None, None, motivo).
    """
    canal = escolher_canal(conn, gravacao_id, ("distance", "distance_m"))
    if canal is not None:
        dados = ler_colunas(canal.uri, [canal.nome_bruto])
        if "t_s" in dados and canal.nome_bruto in dados:
            t = dados["t_s"]
            m = (t >= t_inicio) & (t <= t_fim)
            if m.sum() >= MIN_AMOSTRAS:
                return t[m], distancia_por_canal(canal.valores(dados)[m]), "canal"

    canal = escolher_canal(conn, gravacao_id, ("speed",))
    if canal is not None:
        dados = ler_colunas(canal.uri, [canal.nome_bruto])
        if "t_s" in dados and canal.nome_bruto in dados:
            t = dados["t_s"]
            m = (t >= t_inicio) & (t <= t_fim)
            if m.sum() >= MIN_AMOSTRAS:
                return (
                    t[m],
                    distancia_por_velocidade(t[m], canal.valores(dados)[m]),
                    "velocidade",
                )

    par = par_gps(conn, gravacao_id)
    if par is not None:
        lat_c, lon_c = par
        dados = ler_colunas(lat_c.uri, [lat_c.nome_bruto, lon_c.nome_bruto])
        if "t_s" in dados and lat_c.nome_bruto in dados:
            t = dados["t_s"]
            m = (t >= t_inicio) & (t <= t_fim)
            if m.sum() >= MIN_AMOSTRAS:
                return (
                    t[m],
                    distancia_por_gps(lat_c.valores(dados)[m], lon_c.valores(dados)[m]),
                    "gps",
                )

    motivo = (
        f"nenhum eixo de distancia com pelo menos {MIN_AMOSTRAS} amostras na janela "
        "(sem canal de distancia, sem velocidade e sem GPS utilizaveis)"
    )
    return None, None, motivo


def decompor_volta(conn, volta_id: str, *, redecompor: bool = False) -> Decomposicao:
    """Decompoe uma volta em tempo por trecho. Idempotente."""
    linha = conn.execute(
        """select v.session_id, v.lap_number, v.layout_id, v.t_inicio_s, v.t_fim_s,
                  v.lap_time_s, l.comprimento_m
             from volta v left join layout l on l.id = v.layout_id
            where v.id = %s""",
        (volta_id,),
    ).fetchone()
    if linha is None:
        return Decomposicao(volta_id=volta_id, numero=0, motivo="volta nao existe")
    gravacao_id, numero, layout_id, t_ini, t_fim, _lap_time, comprimento = linha
    d = Decomposicao(volta_id=volta_id, numero=numero)

    ja = conn.execute(
        "select count(*) from tempo_trecho where volta_id = %s", (volta_id,)
    ).fetchone()[0]
    if ja and not redecompor:
        d.motivo = f"ja decomposta: {ja} trecho(s)"
        return d
    if ja and redecompor:
        conn.execute("delete from tempo_trecho where volta_id = %s", (volta_id,))

    if layout_id is None:
        d.motivo = "volta sem layout resolvido: nao existe setor pra medir contra"
        return d
    segmentos = _segmentos_do_layout(conn, layout_id)
    if not segmentos:
        d.motivo = f"layout {layout_id} sem setor nem curva no catalogo"
        return d

    t, s, origem = _eixo_da_volta(conn, str(gravacao_id), float(t_ini), float(t_fim))
    if t is None or s is None:
        d.motivo = origem
        return d

    s_fechado, fator, motivo = fechar_no_layout(s, float(comprimento))
    if s_fechado is None:
        d.motivo = motivo
        d.dist_origem = None
        return d

    tempos = tempos_por_segmento(
        t, s_fechado, segmentos, t_inicio=float(t_ini), t_fim=float(t_fim)
    )
    if not tempos:
        d.motivo = "nenhuma fronteira de trecho caiu dentro da janela da volta"
        return d

    tipo_por_id = {sid: tipo for sid, tipo, _, _ in segmentos}
    for seg_id, tempo in tempos.items():
        conn.execute(
            """insert into tempo_trecho (volta_id, segmento_id, layout_id, tempo_s)
               values (%s,%s,%s,%s)""",
            (volta_id, seg_id, layout_id, tempo),
        )
    conn.execute(
        """update volta set dist_origem = %s, dist_fator = %s, updated_at = now()
            where id = %s""",
        (origem, fator, volta_id),
    )
    d.tempos = tempos
    d.dist_origem = origem
    d.dist_fator = fator
    d.setores = sum(1 for sid in tempos if tipo_por_id[sid] == "setor")
    d.curvas = sum(1 for sid in tempos if tipo_por_id[sid] == "curva")
    return d


def decompor_todas(
    conn, *, redecompor: bool = False
) -> tuple[ResumoDecomposicao, list[Decomposicao]]:
    """Decompoe toda volta cortada. Nao para no primeiro fracasso."""
    resumo = ResumoDecomposicao()
    saidas: list[Decomposicao] = []
    ids = [
        str(r[0])
        for r in conn.execute(
            "select id from volta order by session_id, lap_number"
        ).fetchall()
    ]
    for vid in ids:
        d = decompor_volta(conn, vid, redecompor=redecompor)
        saidas.append(d)
        if d.decompos:
            resumo.decompostas += 1
            resumo.trechos += len(d.tempos)
            chave = d.dist_origem or "?"
            resumo.por_origem[chave] = resumo.por_origem.get(chave, 0) + 1
            if d.dist_fator is not None:
                resumo.fatores.append(d.dist_fator)
        elif d.motivo and d.motivo.startswith("ja decomposta"):
            resumo.ja_decompostas += 1
        else:
            resumo.nao_decompostas += 1
            chave = _familia(d.motivo or "")
            resumo.por_motivo[chave] = resumo.por_motivo.get(chave, 0) + 1
    return resumo, saidas


_FAMILIAS = (
    ("sem layout resolvido", "volta sem layout resolvido"),
    ("sem setor nem curva", "layout sem setor no catalogo"),
    ("fora de", "eixo de distancia discorda do comprimento do layout"),
    ("nao avanca", "eixo de distancia parado"),
    ("nenhum eixo de distancia", "sem canal pra montar o eixo de distancia"),
    ("nenhuma fronteira", "fronteiras fora da janela da volta"),
)


def _familia(motivo: str) -> str:
    for chave, familia in _FAMILIAS:
        if chave in motivo:
            return familia
    return motivo[:70] or "motivo nao classificado"


# --- frenagem e trail-braking (PIL-RN-13) --------------------------------


def detectar_pontos_frenagem_g(
    distancia_m: np.ndarray,
    acc_long_ms2: np.ndarray,
    limiar_ms2: float = -3.5,
    distancia_min_m: float = 10.0,
) -> list[tuple[float, float, float]]:
    """Detecta zonas de frenagem por desaceleracao longitudinal (PIL-RN-13).

    Retorna lista de tuplas (s_inicio_m, s_fim_m, pico_desaceleracao_ms2) onde a
    desaceleracao longitudinal fica abaixo do limiar (padrao -3,5 m/s2) sustentada
    por pelo menos distancia_min_m (padrao 10 m).
    """
    if len(distancia_m) < 2 or len(acc_long_ms2) < 2:
        return []

    zonas = []
    em_zona = False
    s_ini = 0.0
    s_ultimo = 0.0
    pico = 0.0

    for s, ax in zip(distancia_m, acc_long_ms2):
        if ax <= limiar_ms2:
            if not em_zona:
                em_zona = True
                s_ini = float(s)
                pico = float(ax)
            else:
                if ax < pico:
                    pico = float(ax)
            s_ultimo = float(s)
        else:
            if em_zona:
                em_zona = False
                s_fim = s_ultimo
                if (s_fim - s_ini) >= distancia_min_m:
                    zonas.append((s_ini, s_fim, pico))

    if em_zona:
        s_fim = s_ultimo
        if (s_fim - s_ini) >= distancia_min_m:
            zonas.append((s_ini, s_fim, pico))

    return zonas


def calcular_indice_trail_braking(
    distancia_m: np.ndarray,
    acc_long_ms2: np.ndarray,
    acc_lat_ms2: np.ndarray,
    volante_graus: np.ndarray | None = None,
    velocidade_ms: np.ndarray | None = None,
    delta_s: np.ndarray | None = None,
) -> float:
    """Calcula o indice de trail-braking (0.0 a 1.0) conforme PIL-RN-13.

    Combina desaceleracao longitudinal, aceleracao lateral, angulo de esterco,
    velocidade e delta instantaneo. Mede a transicao fisica na elipse de atrito
    onde o piloto alivia o pedal de freio enquanto insere o carro na curva.
    """
    if len(distancia_m) < 2 or len(acc_long_ms2) < 2 or len(acc_lat_ms2) < 2:
        return 0.0

    frenagem = acc_long_ms2 < -1.0
    curva = np.abs(acc_lat_ms2) > 1.5

    if volante_graus is not None and len(volante_graus) == len(distancia_m):
        curva = curva | (np.abs(volante_graus) > 5.0)

    sobreposicao = frenagem & curva
    if not sobreposicao.any():
        return 0.0

    g = 9.80665
    intensidade = np.sqrt((acc_long_ms2 / g) ** 2 + (acc_lat_ms2 / g) ** 2)
    pico_combinado = float(np.max(intensidade[sobreposicao]))

    dist_diff = np.diff(distancia_m)
    dist_frenagem = np.sum(dist_diff[frenagem[:-1]])
    dist_sobreposta = np.sum(dist_diff[sobreposicao[:-1]])

    if dist_frenagem <= 0:
        return 0.0

    razao = min(1.0, float(dist_sobreposta / dist_frenagem))
    indice = 0.6 * razao + 0.4 * min(1.0, pico_combinado / 1.5)
    return float(np.clip(indice, 0.0, 1.0))

