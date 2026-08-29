"""Reparo one-off: desfaz vinculo canal->serie apontando pra Parquet sem a coluna.

Ate 29/08 a ingestao ligava `canal_gravado.serie_id` so pela TAXA, entao um
canal catalogado mas nunca materializado (bytes_amostra indecodificavel, sem
registro M) podia ficar pendurado num Parquet que nao tem a coluna dele. O
vinculo novo (por nome, ver ingestao.py) nao cria mais o caso, mas o legado
fica no banco e fazia `relatorio.amostras` estourar KeyError ('RPM').

Roda com o venv do projeto, contra o banco do ambiente corrente:

    python scripts/reparar_vinculos_serie.py [--aplicar]

Sem `--aplicar` so lista o que faria. Idempotente.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pyarrow.parquet as pq  # noqa: E402

from saru_poc.db import connect  # noqa: E402
from saru_poc.storage import caminho_de_uri  # noqa: E402


def main() -> int:
    aplicar = "--aplicar" in sys.argv
    ruins: list[str] = []
    with connect() as conn:
        linhas = conn.execute(
            """select cg.id::text, cg.nome_bruto, s.uri
                 from canal_gravado cg join serie_amostral s on s.id = cg.serie_id"""
        ).fetchall()
        colunas_por_uri: dict[str, set[str] | None] = {}
        for cid, nome, uri in linhas:
            if uri not in colunas_por_uri:
                try:
                    colunas_por_uri[uri] = set(
                        pq.ParquetFile(caminho_de_uri(uri)).schema_arrow.names
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"aviso: nao li {uri}: {exc}")
                    colunas_por_uri[uri] = None
            cols = colunas_por_uri[uri]
            if cols is not None and nome not in cols:
                ruins.append(cid)
                print(f"vinculo podre: canal '{nome}' -> serie sem essa coluna")
        print(f"{len(linhas)} vinculos conferidos, {len(ruins)} podres")
        if aplicar and ruins:
            conn.execute(
                "update canal_gravado set serie_id = null where id = any(%s::uuid[])",
                (ruins,),
            )
            conn.commit()
            print(f"{len(ruins)} vinculos desfeitos")
        elif ruins:
            print("(simulacao; rode com --aplicar pra desfazer)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
