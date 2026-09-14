#!/usr/bin/env python3
"""Reprodutor de sessao em tempo real: gravacao do acervo, amostra a amostra,
no ritmo em que o carro rodou (ou mais rapido, com --velocidade).

E o que destrava o desenvolvimento do pit wall ao vivo sem gateway, sem 4G e
sem carro na pista: qualquer gravacao ja ingerida vira um fluxo que se
comporta como se estivesse sendo capturada agora.

NOTA DE ARQUITETURA: este script so imprime JSON Lines (stdout ou arquivo).
Ele NAO fala HTTP, nem como servidor nem como cliente. O contrato de ingestao
ao vivo (endpoint, formato de payload, autenticacao) e decisao pendente com o
dono do projeto; entra depois que essa decisao for fechada. Ate la, quem
quiser mandar isso pra algum lugar encadeia com um pipe (`| meu_cliente.py`).

Modelo de dados (migrations/005_telemetria.sql): o Postgres nunca guarda
amostra, so o PONTEIRO pro Parquet (serie_amostral: uri, frequencia_hz,
linhas). canal_gravado liga um canal canonico a coluna bruta e a serie onde
ela mora. Uma gravacao real tem series em taxas nativas bem diferentes (1 Hz
a 200 Hz) vivendo lado a lado: reamostrar tudo pra uma taxa so mentiria sobre
a fonte, entao este reprodutor preserva o instante de cada serie e so
intercala na saida.

Uso:
    python scripts/replay_sessao.py --gravacao <uuid>
    python scripts/replay_sessao.py --gravacao <uuid> --velocidade 10 \\
        --canais speed,rpm,throttle --limite-s 60 --saida /tmp/sessao.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Limiar de atraso: acima disso a amostra e "entregue atrasada" no relatorio
# final (diagnostico honesto, requisito 5). 250 ms e o mesmo criterio citado
# na tarefa; nao ha flag pra isso porque ainda nao apareceu um caso real que
# pedisse outro valor.
LIMIAR_ATRASO_S = 0.25


@dataclass(frozen=True)
class Evento:
    """Um instante da reproducao: tempo desde o inicio da gravacao e os
    canais que tinham amostra naquele instante (so os que tinham, nunca os
    que nao tinham: e assim que a saida nao mente sobre taxas diferentes)."""

    t_s: float
    canais: dict[str, float] = field(default_factory=dict)


def montar_eventos_grupo(t_s: np.ndarray, canais: dict[str, np.ndarray]) -> list[Evento]:
    """Uma serie (mesma taxa nativa, mesmo eixo t_s) vira uma lista de eventos.

    O eixo t_s de uma serie e a uniao dos timestamps da taxa (contrato do
    leitor, ver comentario em relatorio.amostras): canal esparso dentro do
    grupo fica NaN num instante em que os outros amostraram. Por isso o valor
    so entra no evento quando e finito, e o evento inteiro e descartado
    quando nenhum canal amostrou naquela linha.
    """
    eventos: list[Evento] = []
    for i in range(t_s.shape[0]):
        valores: dict[str, float] = {}
        for nome, arr in canais.items():
            v = float(arr[i])
            if np.isfinite(v):
                valores[nome] = v
        if valores:
            eventos.append(Evento(float(t_s[i]), valores))
    return eventos


def mesclar_eventos(grupos: list[list[Evento]]) -> list[Evento]:
    """Intercala eventos de series com taxas diferentes por instante, sem
    reamostrar nenhuma delas.

    Quando duas series caem EXATAMENTE no mesmo t_s (por exemplo t=0.0, onde
    varias taxas nativas costumam comecar juntas), os canais se juntam num
    unico evento: senao a saida teria dois objetos JSON pro mesmo instante, o
    que quebraria a leitura de "um objeto por instante" do contrato.
    """
    # Comparar instante com `==` entre series de taxas diferentes NAO funciona:
    # 3 passos de 1/10 s e 15 passos de 1/50 s descrevem o mesmo instante e dao
    # doubles diferentes (0.30000000000000004 contra 0.3), entao a mesma amostra
    # virava dois eventos. A chave de agrupamento e o microssegundo inteiro:
    # resolucao 5000 vezes mais fina que o passo de 200 Hz, a serie mais rapida
    # do acervo, logo nao funde amostras que sao de fato distintas.
    def _chave(t: float) -> int:
        return round(t * 1_000_000)

    todos = sorted((e for grupo in grupos for e in grupo), key=lambda e: _chave(e.t_s))
    mesclados: list[Evento] = []
    for e in todos:
        if mesclados and _chave(mesclados[-1].t_s) == _chave(e.t_s):
            mesclados[-1].canais.update(e.canais)
        else:
            mesclados.append(Evento(round(e.t_s, 6), dict(e.canais)))
    return mesclados


def linha_jsonl(seq: int, gravacao_id: str, evento: Evento) -> dict:
    return {
        "t_s": evento.t_s,
        "seq": seq,
        "gravacao_id": gravacao_id,
        "canais": evento.canais,
    }


def reproduzir(
    eventos: list[Evento],
    gravacao_id: str,
    velocidade: float,
    saida: IO[str],
    limiar_atraso_s: float = LIMIAR_ATRASO_S,
) -> int:
    """Emite os eventos no ritmo real (dividido por velocidade), sem
    acumular atraso: cada instante e medido contra o t0 fixo do inicio da
    reproducao, nunca contra o instante anterior (senao um sleep que atrasa
    um pouco empurra todos os seguintes, e o atraso vira permanente).

    Devolve quantas amostras saíram atrasadas (> limiar) e avisa em stderr.
    """
    t0 = time.monotonic()
    atrasadas = 0
    pior_atraso_s = 0.0
    for seq, evento in enumerate(eventos, start=1):
        alvo = t0 + evento.t_s / velocidade
        atraso = time.monotonic() - alvo
        if atraso > 0:
            if atraso > limiar_atraso_s:
                atrasadas += 1
                pior_atraso_s = max(pior_atraso_s, atraso)
        else:
            time.sleep(-atraso)
        saida.write(json.dumps(linha_jsonl(seq, gravacao_id, evento), ensure_ascii=False))
        saida.write("\n")
        saida.flush()
    if atrasadas:
        print(
            f"aviso: {atrasadas}/{len(eventos)} amostras entregues atrasadas "
            f"(> {limiar_atraso_s * 1000:.0f} ms; pior caso {pior_atraso_s * 1000:.0f} ms)",
            file=sys.stderr,
        )
    return atrasadas


def descobrir_canais(conn, gravacao_id: str, pedidos: list[str] | None):
    """Resolve canais canonicos da gravacao pra `CanalEscolhido` (mesma logica
    de `relatorio.amostras`, via `escolher_canal`), um a um.

    Com --canais explicito, canal sem serie utilizavel e ERRO: o dono pediu
    aquele canal por nome, devolver silencio no lugar dele seria inventar
    dado por omissao. Sem --canais (default = todos os canonicos disponiveis
    da gravacao), canal sem mapa so fica de fora, porque "todos disponiveis"
    ja e uma degradacao honesta por definicao.
    """
    from saru_poc.pipeline.leitura import escolher_canal

    if pedidos:
        candidatos = pedidos
        exigir_todos = True
    else:
        linhas = conn.execute(
            """select distinct canal_canonico_id from canal_gravado
                where gravacao_id = %s and canal_canonico_id is not null
                order by 1""",
            (gravacao_id,),
        ).fetchall()
        candidatos = [linha[0] for linha in linhas]
        exigir_todos = False

    resolvidos = []
    faltando = []
    for nome in candidatos:
        canal = escolher_canal(conn, gravacao_id, (nome,))
        if canal is None:
            faltando.append(nome)
        else:
            resolvidos.append(canal)

    if exigir_todos and faltando:
        raise ValueError(
            f"gravacao {gravacao_id}: canal(is) pedido(s) sem serie utilizavel "
            f"(sem mapa de unidade ou sem dado gravado): {', '.join(faltando)}"
        )
    if not resolvidos:
        raise ValueError(
            f"gravacao {gravacao_id}: nenhum canal canonico com serie utilizavel. "
            "Sem dado real nao ha o que reproduzir (regra dura: nunca inventar amostra)."
        )
    return resolvidos


def montar_eventos_da_gravacao(conn, gravacao_id: str, pedidos, limite_s) -> list[Evento]:
    from saru_poc.pipeline.leitura import ler_colunas

    canais = descobrir_canais(conn, gravacao_id, pedidos)

    # Agrupado por URI, nao por canal: series de mesma taxa nativa moram no
    # mesmo Parquet (chave unica em serie_amostral e gravacao+camada+taxa+
    # mapa), entao varios canais canonicos compartilham o mesmo eixo t_s e a
    # mesma leitura de arquivo.
    grupos_por_uri: dict[str, list] = {}
    for canal in canais:
        grupos_por_uri.setdefault(canal.uri, []).append(canal)

    eventos_por_grupo: list[list[Evento]] = []
    for uri, grupo in grupos_por_uri.items():
        colunas = list(dict.fromkeys(c.nome_bruto for c in grupo))
        dados = ler_colunas(uri, colunas)
        t_s = dados["t_s"]
        mascara = t_s <= limite_s if limite_s is not None else np.ones_like(t_s, dtype=bool)
        canais_valores = {c.canonico: c.valores(dados)[mascara] for c in grupo}
        eventos_por_grupo.append(montar_eventos_grupo(t_s[mascara], canais_valores))

    eventos = mesclar_eventos(eventos_por_grupo)
    if not eventos:
        raise ValueError(
            f"gravacao {gravacao_id}: nenhuma amostra dentro da janela pedida "
            f"(--limite-s {limite_s})"
        )
    return eventos


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--gravacao", required=True, help="id (uuid) da gravacao no acervo")
    p.add_argument(
        "--velocidade", type=float, default=1.0,
        help="multiplicador do ritmo real (10 = 10x mais rapido). Default 1.0",
    )
    p.add_argument(
        "--canais", default=None,
        help="lista separada por virgula de canais canonicos (ex: speed,rpm). "
        "Default: todos os canonicos disponiveis na gravacao",
    )
    p.add_argument(
        "--limite-s", type=float, default=None,
        help="para de reproduzir apos N segundos de gravacao (default: ate o fim)",
    )
    p.add_argument(
        "--saida", default="-",
        help="caminho do arquivo de saida, ou '-' para stdout (default)",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    pedidos = [c.strip() for c in args.canais.split(",") if c.strip()] if args.canais else None

    from saru_poc.db import connect

    with connect(autocommit=True) as conn:
        eventos = montar_eventos_da_gravacao(conn, args.gravacao, pedidos, args.limite_s)

    arquivo_saida = sys.stdout
    fecha_no_fim = False
    if args.saida != "-":
        arquivo_saida = open(args.saida, "w", encoding="utf-8")
        fecha_no_fim = True
    try:
        reproduzir(eventos, args.gravacao, args.velocidade, arquivo_saida)
    finally:
        if fecha_no_fim:
            arquivo_saida.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
