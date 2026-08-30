#!/usr/bin/env python3
"""Relay de live timing: rede local do autodromo -> backend do SARU.

Roda num notebook na pista, do lado de dentro da LAN onde o Orbits/MyLaps
publica o `resultspage`. Le a fonte (URL http da rede local, ou arquivo, pra
teste), e POSTa o XML pro `/api/campeonato/ingest` sempre que ele MUDA (hash
sha256; o backend dedupa de novo por hash, entao repostar e inofensivo).

Autenticacao: usuario maquina (decisao do Lucas, 29/08). Crie um em
`POST /api/campeonato/maquinas` logado como owner/admin, guarde o token que so
aparece uma vez, e exporte `SARU_MAQUINA_TOKEN` aqui.

Uso:
    SARU_MAQUINA_TOKEN=saru_mq_... \\
    python scripts/relay_livetiming.py \\
        --fonte http://192.168.0.10/livetiming/current.xml \\
        --api https://saru.lassoftware.com.br \\
        --intervalo 2

    # teste local com o arquivo baixado:
    python scripts/relay_livetiming.py --fonte ~/Downloads/current.xml \\
        --api http://127.0.0.1:8010 --uma-vez

Proposital: stdlib + httpx, sem importar o pacote da PoC. O relay roda numa
maquina que NAO e a do backend; quanto menos ele precisar, mais facil e
carregar so este arquivo no notebook da pista.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
from pathlib import Path

import httpx


def ler_fonte(fonte: str, cliente: httpx.Client) -> bytes:
    if fonte.startswith(("http://", "https://")):
        resposta = cliente.get(fonte, timeout=5.0)
        resposta.raise_for_status()
        return resposta.content
    return Path(fonte).expanduser().read_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description="Relay resultspage -> SARU")
    parser.add_argument(
        "--fonte", required=True, help="URL na LAN ou caminho de arquivo XML"
    )
    parser.add_argument(
        "--api",
        required=True,
        help="base do backend, ex. https://saru.lassoftware.com.br",
    )
    parser.add_argument(
        "--intervalo", type=float, default=2.0, help="segundos entre leituras da fonte"
    )
    parser.add_argument(
        "--uma-vez", action="store_true", help="le e posta uma vez, sem loop"
    )
    # Feed separado, arquivo separado: os avisos da direcao de prova (track
    # limits e penalidades) vem em announcements.xml, que nao tem os labels de
    # evento do resultspage. Por isso ele exige o id do evento no destino, e
    # so e enviado quando os dois argumentos vierem juntos.
    parser.add_argument(
        "--avisos",
        help="fonte do announcements.xml (arquivo ou URL), opcional",
    )
    parser.add_argument(
        "--evento",
        help="id do evento no SARU, obrigatorio junto com --avisos",
    )
    args = parser.parse_args()

    token = os.environ.get("SARU_MAQUINA_TOKEN", "").strip()
    if not token:
        print(
            "erro: exporte SARU_MAQUINA_TOKEN (crie em POST /api/campeonato/maquinas)",
            file=sys.stderr,
        )
        return 2

    if bool(args.avisos) != bool(args.evento):
        print("erro: --avisos e --evento andam juntos", file=sys.stderr)
        return 2

    destino = args.api.rstrip("/") + "/api/campeonato/ingest"
    destino_avisos = (
        args.api.rstrip("/") + f"/api/campeonato/{args.evento}/avisos/ingest"
        if args.avisos
        else None
    )
    ultimo_sha_avisos: str | None = None
    cabecalhos = {"Authorization": f"Bearer {token}", "Content-Type": "application/xml"}
    ultimo_sha: str | None = None
    atraso_erro = 5.0

    with httpx.Client(headers={"User-Agent": "SARU-relay/0.1"}) as cliente:
        while True:
            try:
                corpo = ler_fonte(args.fonte, cliente)
                sha = hashlib.sha256(corpo).hexdigest()
                if sha != ultimo_sha:
                    resposta = cliente.post(
                        destino, content=corpo, headers=cabecalhos, timeout=10.0
                    )
                    if resposta.status_code == 401:
                        print(
                            "erro: token de máquina rejeitado (revogado?)",
                            file=sys.stderr,
                        )
                        return 3
                    resposta.raise_for_status()
                if destino_avisos:
                    # Mesmo controle por hash do feed principal: o arquivo de
                    # avisos muda poucas vezes por dia, e reenviar identico so
                    # gastaria banda (o servidor ja deduplica, mas o certo e
                    # nao mandar).
                    corpo_avisos = ler_fonte(args.avisos, cliente)
                    sha_avisos = hashlib.sha256(corpo_avisos).hexdigest()
                    if sha_avisos != ultimo_sha_avisos:
                        r_avisos = cliente.post(
                            destino_avisos,
                            content=corpo_avisos,
                            headers=cabecalhos,
                            timeout=10.0,
                        )
                        r_avisos.raise_for_status()
                        ultimo_sha_avisos = sha_avisos
                    ultimo_sha = sha
                    dado = resposta.json()
                    print(
                        f"[{time.strftime('%H:%M:%S')}] postado sha={sha[:10]} "
                        f"novo={dado.get('novo')} passagens={dado.get('passagens_novas')}"
                    )
                atraso_erro = 5.0
            except KeyboardInterrupt:
                return 0
            except Exception as e:  # noqa: BLE001
                # fonte fora do ar ou backend inalcancavel: o relay NAO morre no
                # meio do evento, espera e tenta de novo (teto de 60 s)
                print(
                    f"[{time.strftime('%H:%M:%S')}] falha: {e} (tento em {atraso_erro:.0f}s)",
                    file=sys.stderr,
                )
                if args.uma_vez:
                    return 1
                time.sleep(atraso_erro)
                atraso_erro = min(atraso_erro * 2, 60.0)
                continue

            if args.uma_vez:
                return 0
            time.sleep(args.intervalo)


if __name__ == "__main__":
    sys.exit(main())
