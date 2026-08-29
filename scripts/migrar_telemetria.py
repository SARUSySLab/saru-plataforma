"""Sobe a telemetria local para uma instancia remota, pelo proprio endpoint.

**Por que pelo upload, e nao copiando banco mais Parquet.** Copiar exigiria
escrever direto no Postgres remoto (TCP proxy) E colocar 316 MB de Parquet no
volume do container, para o que nao ha canal. O upload resolve os dois de uma
vez: `POST /api/gravacoes` roda o pipeline la, e o Parquet nasce no volume do
jeito que nasceria em producao. E o caminho que o produto ja tem, entao o que
esta sendo testado aqui e o caminho real, nao um atalho de migracao.

Sobe so as gravacoes que tem volta cortada: sem volta nao ha N0 nem N1, e o
resto do acervo (158 gravacoes que nao renderam volta) so ocuparia o volume.

Idempotente pelo lado do servidor: a recepcao deduplica por sha256 e devolve
`ja_existia: true` sem reprocessar. Rodar duas vezes nao duplica nada.

Uso:
    python scripts/migrar_telemetria.py --base https://saru.lassoftware.com.br \\
        --email voce@exemplo.com --senha ... [--limite N] [--simular]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from saru_poc.db import connect  # noqa: E402


def _caminho(objeto_uri: str) -> Path | None:
    """`file:///...` com percent-encoding vira caminho de disco.

    Nome de piloto tem espaco e acento, entao o URI vem escapado; sem o
    `unquote` o arquivo "nao existe" por um motivo que nao e o real.
    """
    if not objeto_uri or not objeto_uri.startswith("file://"):
        return None
    return Path(unquote(urlparse(objeto_uri).path))


def bundles() -> list[tuple[str, str, list[Path]]]:
    """(gravacao_id, rotulo, arquivos) de cada gravacao COM volta cortada.

    Os arquivos de uma gravacao sobem JUNTOS numa requisicao so porque um bundle
    pode ter ate 6 arquivos para a mesma volta (o `.ld` e o `.ldx` do MoTeC, por
    exemplo). Mandar separado faria a recepcao criar gravacoes distintas.
    """
    with connect() as conn:
        linhas = conn.execute(
            """select g.id, coalesce(g.label, l.nome, 'sem pista'), a.objeto_uri
                 from gravacao g
                 join arquivo_bruto a on a.gravacao_id = g.id
                 left join layout l on l.id = g.layout_id
                where g.id in (select distinct session_id from volta)
                order by g.id, a.papel"""
        ).fetchall()

    por_gravacao: dict[str, tuple[str, list[Path]]] = {}
    for gid, rotulo, uri in linhas:
        caminho = _caminho(uri)
        if caminho is None or not caminho.exists():
            continue
        rot, arquivos = por_gravacao.setdefault(str(gid), (rotulo, []))
        arquivos.append(caminho)
    return [(gid, rot, arqs) for gid, (rot, arqs) in por_gravacao.items() if arqs]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", required=True, help="ex.: https://saru.lassoftware.com.br")
    p.add_argument("--email", required=True)
    p.add_argument("--senha", required=True)
    p.add_argument("--limite", type=int, default=0, help="0 = todas")
    p.add_argument("--simular", action="store_true", help="lista e nao envia")
    args = p.parse_args()

    lotes = bundles()
    if args.limite:
        lotes = lotes[: args.limite]
    total_mb = sum(a.stat().st_size for _, _, arqs in lotes for a in arqs) / 1e6
    print(f"{len(lotes)} gravacoes, {sum(len(a) for _, _, a in lotes)} arquivos, {total_mb:.0f} MB\n")

    if args.simular:
        for gid, rot, arqs in lotes:
            mb = sum(a.stat().st_size for a in arqs) / 1e6
            print(f"  {gid[:8]}  {rot[:38]:38}  {len(arqs)} arq  {mb:6.1f} MB")
        return 0

    # timeout alto: um `.ld` de centenas de MB nao sobe em 30 s, e o servidor so
    # responde depois de gravar o arquivo inteiro (a recepcao e sincrona)
    with httpx.Client(base_url=args.base, timeout=600.0, follow_redirects=True) as cli:
        r = cli.post("/api/auth/login", json={"email": args.email, "senha": args.senha})
        if r.status_code != 200:
            print(f"login falhou: {r.status_code} {r.text[:200]}")
            return 1
        print(f"logado como {args.email}\n")

        enviadas = repetidas = falhas = 0
        for i, (gid, rot, arqs) in enumerate(lotes, 1):
            mb = sum(a.stat().st_size for a in arqs) / 1e6
            print(f"[{i}/{len(lotes)}] {rot[:40]:40} {len(arqs)} arq {mb:6.1f} MB ... ", end="", flush=True)
            try:
                abertos = [("arquivos", (a.name, a.open("rb"))) for a in arqs]
                try:
                    resp = cli.post("/api/gravacoes", files=abertos)
                finally:
                    for _, (_, fh) in abertos:
                        fh.close()
            except httpx.HTTPError as e:
                print(f"FALHOU rede: {e}")
                falhas += 1
                continue

            if resp.status_code != 202:
                print(f"FALHOU {resp.status_code}: {resp.text[:160]}")
                falhas += 1
                continue
            corpo = resp.json()
            if corpo.get("ja_existia"):
                print("ja estava la")
                repetidas += 1
            else:
                print(f"ok, {corpo['gravacao_id'][:8]}, pipeline rodando")
                enviadas += 1

        print(f"\nenviadas {enviadas}, ja existiam {repetidas}, falhas {falhas}")
        print("O pipeline roda em background no servidor. Acompanhe por GET /api/gravacoes:")
        print("as colunas `voltas` e `trechos` saem de zero quando cada etapa termina.")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
