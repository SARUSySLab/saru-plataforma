#!/usr/bin/env python3
"""Importa o acervo do Nelson Piquet para uma instalacao REMOTA, pela API.

Por que existe, e nao basta o `importar_nelson_piquet.py`: aquele fala direto
com o Postgres e usa o pipeline local, que escreve os Parquet em disco. Rodar
ele apontando para o banco de producao criaria gravacao sem amostra nenhuma,
porque o Parquet ficaria na maquina de quem rodou. Aqui tudo entra pelo mesmo
caminho que o front usa: upload de arquivo, e o servidor faz o resto.

A curadoria de identidade (fusoes de piloto, acento, numero do carro) vem
importada do script local, para as duas rotas produzirem exatamente os mesmos
13 pilotos a partir das 24 grafias do acervo.
"""

from __future__ import annotations

import argparse
import collections
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))

from importar_nelson_piquet import (  # noqa: E402
    CORTE_DE_SESSAO_MIN,
    SAIDA_LONGA_MIN,
    agrupar_em_sessoes,
    levantar,
)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("raiz", type=Path)
    p.add_argument("--api", required=True, help="ex. https://saru.lassoftware.com.br")
    p.add_argument("--email", required=True)
    p.add_argument("--senha", required=True)
    p.add_argument("--track-id", default="brasilia_gp")
    p.add_argument("--limite", type=int, help="importa so os N primeiros arquivos")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    itens = levantar(args.raiz)
    if args.limite:
        itens = itens[: args.limite]
    grafias = collections.defaultdict(set)
    for i in itens:
        grafias[i["piloto"]].add(i["grafia"])
    print(f"{len(itens)} arquivos, {len(grafias)} pilotos, "
          f"{len({i['quando'].date() for i in itens})} dias")
    if args.dry_run:
        return 0

    base = args.api.rstrip("/")
    # timeout generoso no upload: o maior arquivo do acervo tem 5,7 MB e a
    # recepcao e sincrona (o pipeline e que roda em background)
    with httpx.Client(base_url=base, timeout=180.0, follow_redirects=True) as cli:
        r = cli.post("/api/auth/login", json={"email": args.email, "senha": args.senha})
        if r.status_code != 200:
            print(f"erro: login falhou ({r.status_code}) {r.text[:200]}", file=sys.stderr)
            return 2
        print(f"logado em {base} como {args.email}")

        criados = collections.Counter()
        pilotos_id: dict[str, str] = {}
        por_dia = collections.defaultdict(list)
        for i in itens:
            por_dia[i["quando"].date()].append(i)

        for dia, do_dia in sorted(por_dia.items()):
            nome_evento = f"Dia de pista, Nelson Piquet, {dia:%d/%m/%Y}"
            # idempotencia por NOME: reexecutar nao cria evento duplicado, o que
            # importa porque upload de 103 arquivos pode ser interrompido
            ja = [e for e in cli.get("/api/eventos").json() if e.get("name") == nome_evento]
            if ja:
                evento_id = ja[0]["id"]
            else:
                resp = cli.post("/api/eventos", json={
                    "track_id": args.track_id, "name": nome_evento,
                    "starts_at": do_dia[0]["quando"].isoformat(),
                    "tipo": "track_day", "local_date": str(dia),
                })
                resp.raise_for_status()
                evento_id = resp.json()["id"]
                criados["evento"] += 1
            print(f"\n{nome_evento}")

            por_piloto = collections.defaultdict(list)
            for i in do_dia:
                por_piloto[i["piloto"]].append(i)

            for piloto, saidas in sorted(por_piloto.items()):
                if piloto not in pilotos_id:
                    resp = cli.post("/api/pilotos", json={
                        "nome": piloto, "apelidos": sorted(grafias[piloto]),
                    })
                    resp.raise_for_status()
                    pilotos_id[piloto] = resp.json()["id"]
                    criados["piloto"] += 1
                piloto_id = pilotos_id[piloto]

                sessoes_do_evento = cli.get(f"/api/eventos/{evento_id}/sessoes").json()
                for bloco in agrupar_em_sessoes(saidas):
                    rotulo = f"{bloco[0]['quando']:%Hh%M} a {bloco[-1]['quando']:%Hh%M}"
                    # idempotencia por (rotulo, piloto): 103 uploads levam
                    # tempo e a rodada pode cair no meio. Sem isso, reexecutar
                    # criava a espinha inteira de novo -- foi exatamente o que
                    # aconteceu na importacao local antes do conserto.
                    ja_s = [
                        s for s in sessoes_do_evento
                        if s.get("label") == rotulo and str(s.get("piloto_id")) == str(piloto_id)
                    ]
                    if ja_s:
                        sessao_id = ja_s[0]["id"]
                    else:
                        resp = cli.post(f"/api/eventos/{evento_id}/sessoes", json={
                            "type": "trackday_battery", "label": rotulo,
                            "piloto_id": piloto_id,
                            "starts_at": bloco[0]["quando"].isoformat(),
                        })
                        resp.raise_for_status()
                        sessao_id = resp.json()["id"]
                        criados["sessao"] += 1
                    print(f"  {piloto}: sessao {rotulo}, {len(bloco)} saida(s)")
                    baterias_da_sessao = cli.get(f"/api/sessoes/{sessao_id}/baterias").json()

                    for i in bloco:
                        minutos = i["duracao_s"] / 60
                        etiqueta = f"{i['quando']:%Hh%M}, {i['veiculo']}"
                        if minutos > SAIDA_LONGA_MIN:
                            etiqueta += f" ({minutos:.0f} min, logger ligado entre idas)"
                        ja_b = [b for b in baterias_da_sessao if b.get("label") == etiqueta]
                        if ja_b:
                            bateria_id = ja_b[0]["id"]
                        else:
                            resp = cli.post(f"/api/sessoes/{sessao_id}/baterias", json={
                                "label": etiqueta,
                                "went_out_at": i["quando"].isoformat(),
                            })
                            resp.raise_for_status()
                            bateria_id = resp.json()["id"]
                            criados["saida"] += 1

                        caminho: Path = i["caminho"]
                        with caminho.open("rb") as fh:
                            envio = cli.post(
                                "/api/gravacoes",
                                files={"arquivos": (caminho.name, fh, "application/octet-stream")},
                                data={"finalidade": "piloto"},
                            )
                        if envio.status_code not in (200, 201, 202):
                            print(f"    FALHA no upload de {caminho.name}: "
                                  f"{envio.status_code} {envio.text[:160]}", file=sys.stderr)
                            criados["upload_falhou"] += 1
                            continue
                        # a rota devolve {"gravacoes": [{"gravacao_id": ...}]},
                        # nao o id na raiz: cada captura do bundle vira a sua
                        # gravacao (D1 de 29/08), entao a resposta e uma lista.
                        corpo = envio.json()
                        gravacoes = corpo.get("gravacoes") or []
                        if not gravacoes:
                            print(f"    FALHA: resposta sem gravacao para {caminho.name}: "
                                  f"{str(corpo)[:160]}", file=sys.stderr)
                            criados["upload_falhou"] += 1
                            continue
                        gravacao_id = gravacoes[0]["gravacao_id"]
                        if gravacoes[0].get("ja_existia"):
                            criados["telemetria_ja_existia"] += 1
                        else:
                            criados["telemetria"] += 1

                        v = cli.post(f"/api/baterias/{bateria_id}/gravacoes/{gravacao_id}")
                        if v.status_code not in (204, 200):
                            print(f"    aviso: nao pendurou {caminho.name}: "
                                  f"{v.status_code} {v.text[:120]}", file=sys.stderr)
                        # o pipeline roda em background no servidor; um respiro
                        # entre uploads evita empilhar 103 processamentos de uma vez
                        time.sleep(0.4)
                        print(f"    {etiqueta}  ({caminho.stat().st_size/1e6:.1f} MB)")

        print("\ncriado:", dict(criados))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
