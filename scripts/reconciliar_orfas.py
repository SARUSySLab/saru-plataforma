#!/usr/bin/env python3
"""Casa gravacao solta com saida vazia, numa instalacao remota, pela API.

Por que existe: na importacao do acervo do Nelson Piquet de 30/08 a espinha
subiu inteira (evento, piloto, sessao, saida) mas 32 gravacoes ficaram SEM
saida pendurada, e as saidas correspondentes ficaram sem telemetria. O
sintoma que o Lucas viu: "pedro fortes ficou sem telemetria em producao".

O que ele NAO faz: adivinhar. So propoe par quando o casamento e unico dos
dois lados dentro da tolerancia de tempo -- uma gravacao solta para uma saida
vazia e vice-versa. Par ambiguo (duas saidas vazias no mesmo minuto, dois
arquivos no mesmo minuto) sai listado como ambiguo e NAO e aplicado, porque
pendurar telemetria na saida errada e pior que deixar solta: vira analise de
volta de outro piloto com o nome de quem nao dirigiu.

Read-only por padrao. Escreve so com --aplicar.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta

import httpx

# Tolerancia entre `capturado_em` da gravacao e `went_out_at` da saida. A
# saida e criada com o instante de captura do proprio arquivo, entao um
# casamento certo bate quase exato; a folga cobre arredondamento de fuso e
# de segundos na etiqueta.
TOLERANCIA = timedelta(minutes=2)


def quando(valor: str | None) -> datetime | None:
    if not valor:
        return None
    return datetime.fromisoformat(valor.replace("Z", "+00:00"))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--api", required=True)
    p.add_argument("--email", required=True)
    p.add_argument("--senha", required=True)
    p.add_argument("--aplicar", action="store_true", help="pendura de verdade")
    args = p.parse_args()

    with httpx.Client(base_url=args.api.rstrip("/"), timeout=60.0, follow_redirects=True) as cli:
        r = cli.post("/api/auth/login", json={"email": args.email, "senha": args.senha})
        if r.status_code != 200:
            print(f"erro: login falhou ({r.status_code})", file=sys.stderr)
            return 2

        gravacoes = cli.get("/api/gravacoes").json()
        soltas = [g for g in gravacoes if not g.get("bateria_id")]

        # saidas vazias: varre a espinha inteira, evento por evento
        vazias = []
        for ev in cli.get("/api/eventos").json():
            for s in cli.get(f"/api/eventos/{ev['id']}/sessoes").json():
                for b in cli.get(f"/api/sessoes/{s['id']}/baterias").json():
                    if not b.get("gravacoes"):
                        vazias.append({
                            "bateria_id": b["id"],
                            "label": b.get("label"),
                            "quando": quando(b.get("went_out_at")),
                            "sessao": s.get("label"),
                            "evento": ev.get("name"),
                        })

        print(f"{len(soltas)} gravacao(oes) solta(s), {len(vazias)} saida(s) vazia(s)\n")

        pares, ambiguos, sem_par = [], [], []
        for g in soltas:
            t = quando(g.get("capturado_em"))
            if t is None:
                sem_par.append((g, "gravacao sem capturado_em"))
                continue
            perto = [v for v in vazias if v["quando"] and abs(v["quando"] - t) <= TOLERANCIA]
            if len(perto) == 1:
                # o outro lado tambem tem que ser unico, senao nao e casamento
                rivais = [
                    o for o in soltas
                    if o is not g and quando(o.get("capturado_em"))
                    and abs(quando(o["capturado_em"]) - perto[0]["quando"]) <= TOLERANCIA
                ]
                if rivais:
                    ambiguos.append((g, perto[0], f"{len(rivais) + 1} arquivos no mesmo minuto"))
                else:
                    pares.append((g, perto[0]))
            elif perto:
                ambiguos.append((g, perto[0], f"{len(perto)} saidas vazias no mesmo minuto"))
            else:
                sem_par.append((g, "nenhuma saida vazia no horario"))

        for g, v in pares:
            print(f"  [par]  {g.get('capturado_em')}  ->  {v['evento']} / {v['sessao']} / {v['label']}")
        for g, v, motivo in ambiguos:
            print(f"  [amb]  {g.get('capturado_em')}  ~  {v['label']}  ({motivo})")
        for g, motivo in sem_par:
            print(f"  [--]   {g.get('capturado_em')}  ({motivo})")

        print(f"\n{len(pares)} par(es) unico(s), {len(ambiguos)} ambiguo(s), {len(sem_par)} sem par")
        if not args.aplicar:
            print("(read-only: rode com --aplicar pra pendurar)")
            return 0

        ok = falhou = 0
        for g, v in pares:
            resp = cli.post(f"/api/baterias/{v['bateria_id']}/gravacoes/{g['gravacao_id']}")
            if resp.status_code in (200, 204):
                ok += 1
            else:
                falhou += 1
                print(f"  FALHA {g['gravacao_id']}: {resp.status_code} {resp.text[:140]}",
                      file=sys.stderr)
        print(f"\npendurado: {ok}, falhou: {falhou}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
