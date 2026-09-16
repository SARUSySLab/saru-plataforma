"""Etapa 6, segunda parte: tracado medido.

`tracado` e a linha que o carro FEZ, nao o layout da pista (a tabela carrega
esse aviso no proprio comentario). Sai do GPS de uma volta, projetado em metros
locais, e serve o mapa da pista (bloco 8 do funil) e o eixo do traco.

Duas guardas antes de gravar qualquer ponto, as duas herdadas do B2:

1. **O perimetro tem que fechar o comprimento do layout**, na mesma faixa da
   decomposicao (0,9 a 1,1). GPS que descreve um contorno de tamanho errado nao
   e a pista resolvida.
2. **Quando o layout tem coordenada de referencia, o GPS tem que passar perto
   dela.** Esta segunda guarda existe por causa de um caso medido: as 3
   gravacoes GT7 do acervo declaram "Autodromo de Interlagos", e a distancia
   percorrida por volta confirma Interlagos (4.217 m contra 4.309 m), mas as
   COORDENADAS estao em Donington Park, 9.500 km de distancia. O perimetro
   delas fecha na faixa (Donington tem 4.020 m), entao a guarda 1 sozinha
   deixaria passar, e o mapa desenharia a pista errada com a pista certa
   escrita em cima.

O par de guardas e o ponto: uma checa tamanho, a outra checa lugar. Nenhuma das
duas sozinha separa "GPS bom" de "GPS de outro continente com tamanho parecido".
"""

from __future__ import annotations

import hashlib
import math
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from ..config import CONFIG
from .decomposicao import FATOR_MAX, FATOR_MIN, distancia_por_gps
from .leitura import ler_colunas, par_gps

METODO = "gps_projetado"
METODO_VERSAO = "tracado_gps-1"

R_TERRA_M = 6_371_000.0

# Quao longe da coordenada de referencia do layout o tracado pode passar. Um
# quilometro e folgado de proposito: o ref e um ponto na linha de chegada e a
# pista tem quilometros de extensao, entao a guarda so pega erro de LUGAR, nao
# de precisao.
DISTANCIA_MAX_DO_REF_M = 1_000.0

MIN_PONTOS = 20


@dataclass
class TracadoDaVolta:
    volta_id: str
    numero: int
    n_pontos: int = 0
    fator: float | None = None
    uri: str | None = None
    motivo: str | None = None
    subtracados: int = 0

    @property
    def gravou(self) -> bool:
        return self.uri is not None


@dataclass
class ResumoTracado:
    gravados: int = 0
    nao_gravados: int = 0
    ja_gravados: int = 0
    subtracados: int = 0
    por_motivo: dict[str, int] = field(default_factory=dict)


def projetar(
    lat: np.ndarray, lon: np.ndarray, lat0: float, lon0: float
) -> tuple[np.ndarray, np.ndarray]:
    """Lat/lon em metros locais, com origem em (lat0, lon0)."""
    k = math.cos(math.radians(lat0))
    x = np.radians(lon - lon0) * R_TERRA_M * k
    y = np.radians(lat - lat0) * R_TERRA_M
    return x, y


def distancia_ao_ponto_m(
    lat: np.ndarray, lon: np.ndarray, lat0: float, lon0: float
) -> float:
    """Menor distancia entre a linha e um ponto de referencia, em metros."""
    x, y = projetar(lat, lon, lat0, lon0)
    return float(np.hypot(x, y).min())


def montar(
    lat: np.ndarray,
    lon: np.ndarray,
    *,
    comprimento_m: float,
    ref: tuple[float, float] | None,
) -> tuple[dict[str, np.ndarray] | None, float, str | None]:
    """Pontos do tracado (x, y, s_m) ou o motivo de nao ter tracado.

    A origem da projecao e a referencia do layout quando existe, senao o
    primeiro ponto da volta: o mapa e relativo, mas ancorar na linha de chegada
    deixa duas voltas da mesma pista comparaveis ponto a ponto.
    """
    if len(lat) < MIN_PONTOS:
        return None, 0.0, f"menos de {MIN_PONTOS} pontos de GPS na volta"

    s = distancia_por_gps(lat, lon)
    medido = float(s[-1])
    if medido <= 0:
        return None, 0.0, "GPS nao se desloca na janela da volta"
    fator = comprimento_m / medido
    if not (FATOR_MIN <= fator <= FATOR_MAX):
        motivo = (
            f"perimetro do GPS mede {medido:.0f} m contra {comprimento_m:.0f} m do "
            f"layout (fator {fator:.2f}, fora de {FATOR_MIN} a {FATOR_MAX})"
        )
        return None, fator, motivo

    if ref is not None:
        perto = distancia_ao_ponto_m(lat, lon, ref[0], ref[1])
        if perto > DISTANCIA_MAX_DO_REF_M:
            motivo = (
                f"GPS passa a {perto / 1000:.1f} km da referencia do layout: o "
                "contorno tem o tamanho certo mas esta no lugar errado"
            )
            return None, fator, motivo
        lat0, lon0 = ref
    else:
        lat0, lon0 = float(lat[0]), float(lon[0])

    x, y = projetar(lat, lon, lat0, lon0)
    return {"x_m": x, "y_m": y, "s_m": s * fator}, fator, None


def _escrever(volta_id: str, pontos: dict[str, np.ndarray]) -> tuple[str, str, int]:
    """Grava o tracado em Parquet enderecado pelo conteudo. Devolve (uri, sha, n).

    Mesma regra do `storage`: objeto imutavel, nome carregando o sha256, e
    reprocessar que produz bytes identicos cai no mesmo caminho, de graca.
    """
    tabela = pa.table({k: pa.array(v, type=pa.float64()) for k, v in pontos.items()})
    fd, bruto = tempfile.mkstemp(suffix=".parquet")
    os.close(fd)
    temporario = Path(bruto)
    try:
        pq.write_table(tabela, temporario, compression="zstd")
        sha = hashlib.sha256(temporario.read_bytes()).hexdigest()
        destino_dir = CONFIG.data_root / "tracado" / f"volta={volta_id}"
        destino_dir.mkdir(parents=True, exist_ok=True)
        destino = destino_dir / f"{sha[:12]}.parquet"
        if destino.exists():
            temporario.unlink(missing_ok=True)
        else:
            # mesmo motivo do storage.py: rename nao atravessa dispositivo, e
            # em producao o temporario e o destino ficam em dispositivos
            # diferentes (overlay do container contra volume montado)
            shutil.move(str(temporario), str(destino))
    finally:
        temporario.unlink(missing_ok=True)
    return destino.as_uri(), sha, tabela.num_rows


def derivar_volta(conn, volta_id: str, *, rederivar: bool = False) -> TracadoDaVolta:
    """Deriva e grava o tracado medido de uma volta. Idempotente."""
    linha = conn.execute(
        """select v.session_id, v.lap_number, v.layout_id, v.t_inicio_s, v.t_fim_s,
                  l.comprimento_m, l.ref_lat, l.ref_lon
             from volta v left join layout l on l.id = v.layout_id
            where v.id = %s""",
        (volta_id,),
    ).fetchone()
    if linha is None:
        return TracadoDaVolta(volta_id=volta_id, numero=0, motivo="volta nao existe")
    gid, numero, layout_id, t_ini, t_fim, comprimento, ref_lat, ref_lon = linha
    r = TracadoDaVolta(volta_id=volta_id, numero=numero)

    if layout_id is None:
        r.motivo = "volta sem layout resolvido: tracado nao tem contra o que fechar"
        return r

    ja = conn.execute(
        """select id from tracado
            where volta_id = %s and tipo = 'medido' and metodo_versao = %s""",
        (volta_id, METODO_VERSAO),
    ).fetchone()
    if ja and not rederivar:
        r.motivo = "ja derivado"
        return r
    if ja and rederivar:
        conn.execute("delete from subtracado where tracado_id = %s", (ja[0],))
        conn.execute("delete from tracado where id = %s", (ja[0],))

    par = par_gps(conn, str(gid))
    if par is None:
        r.motivo = "sem GPS mapeado na mesma serie"
        return r
    lat_c, lon_c = par
    dados = ler_colunas(lat_c.uri, [lat_c.nome_bruto, lon_c.nome_bruto])
    if "t_s" not in dados or lat_c.nome_bruto not in dados:
        r.motivo = "serie de GPS sem as colunas esperadas"
        return r
    t = dados["t_s"]
    m = (t >= float(t_ini)) & (t <= float(t_fim))
    lat = lat_c.valores(dados)[m]
    lon = lon_c.valores(dados)[m]

    ref = (
        (float(ref_lat), float(ref_lon))
        if ref_lat is not None and ref_lon is not None
        else None
    )
    pontos, fator, motivo = montar(lat, lon, comprimento_m=float(comprimento), ref=ref)
    r.fator = fator
    if pontos is None:
        r.motivo = motivo
        return r

    uri, sha, n = _escrever(volta_id, pontos)
    gemeo = conn.execute(
        "select volta_id from tracado where sha256 = %s", (sha,)
    ).fetchone()
    if gemeo is not None:
        # A mesma captura recebida em duas gravacoes (.xrk e .xrz em pastas
        # diferentes, #53) produz voltas e objeto identicos. O tracado ja esta
        # gravado na outra volta; gravar de novo fura `uq_tracado_sha256`.
        if str(gemeo[0]) != volta_id:
            (
                CONFIG.data_root
                / "tracado"
                / f"volta={volta_id}"
                / f"{sha[:12]}.parquet"
            ).unlink(missing_ok=True)
        r.motivo = (
            f"tracado identico ao da volta {gemeo[0]}: mesma captura em outra gravacao"
        )
        return r
    tracado_id = conn.execute(
        """insert into tracado (volta_id, layout_id, tipo, metodo, metodo_versao,
                                n_pontos, uri, sha256)
           values (%s,%s,'medido',%s,%s,%s,%s,%s) returning id""",
        (volta_id, layout_id, METODO, METODO_VERSAO, n, uri, sha),
    ).fetchone()[0]

    # Subtracado: a janela deste tracado dentro de cada segmento do layout. `uri`
    # fica nula de proposito (a tabela documenta o caso): o recorte e uma faixa
    # do mesmo objeto, e duplicar bytes pra cada setor nao pagaria nada.
    s_m = pontos["s_m"]
    segmentos = conn.execute(
        """select id, s_inicio_m, s_fim_m from segmento
            where layout_id = %s and tipo in ('setor','curva')""",
        (layout_id,),
    ).fetchall()
    for seg_id, s_ini, s_fim in segmentos:
        dentro = int(((s_m >= float(s_ini)) & (s_m <= float(s_fim))).sum())
        if dentro == 0:
            continue
        conn.execute(
            """insert into subtracado (tracado_id, segmento_id, layout_id, n_pontos)
               values (%s,%s,%s,%s)""",
            (tracado_id, seg_id, layout_id, dentro),
        )
        r.subtracados += 1

    r.uri = uri
    r.n_pontos = n
    return r


def derivar_todos(
    conn, *, rederivar: bool = False
) -> tuple[ResumoTracado, list[TracadoDaVolta]]:
    resumo = ResumoTracado()
    saidas: list[TracadoDaVolta] = []
    ids = [
        str(x[0])
        for x in conn.execute(
            "select id from volta order by session_id, lap_number"
        ).fetchall()
    ]
    for vid in ids:
        r = derivar_volta(conn, vid, rederivar=rederivar)
        saidas.append(r)
        if r.gravou:
            resumo.gravados += 1
            resumo.subtracados += r.subtracados
        elif r.motivo == "ja derivado":
            resumo.ja_gravados += 1
        else:
            resumo.nao_gravados += 1
            chave = _familia(r.motivo or "")
            resumo.por_motivo[chave] = resumo.por_motivo.get(chave, 0) + 1
    return resumo, saidas


_FAMILIAS = (
    ("sem layout resolvido", "volta sem layout resolvido"),
    ("sem GPS mapeado", "sem canal de GPS"),
    ("lugar errado", "GPS no lugar errado (contorno certo, coordenada de outra pista)"),
    ("perimetro do GPS", "perimetro do GPS discorda do comprimento do layout"),
    ("nao se desloca", "GPS parado na janela"),
    ("pontos de GPS", "poucos pontos de GPS na volta"),
    (
        "mesma captura em outra gravacao",
        "mesma captura em outra gravacao (tracado identico)",
    ),
)


def _familia(motivo: str) -> str:
    for chave, familia in _FAMILIAS:
        if chave in motivo:
            return familia
    return motivo[:70] or "motivo nao classificado"
