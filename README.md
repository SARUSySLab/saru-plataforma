# saru-poc-trackday

PoC core do SARU: do arquivo do piloto ao insight, ponta a ponta num track day.
Repo proprio, **zero toque no `saru-app`** (decisao 3 do plano).

Plano canonico: `../plano-poc-core-trackday.md`.
Catalogo de entidades: `../catalogo-entidades-saru.html` (snapshot `aa94872`).

## Stack

| Camada | Escolha | Por que |
|---|---|---|
| Linguagem | Python 3.14 via uv (pyproject exige >= 3.12) | acervo, parsers e analise |
| Catalogo (26 entidades) | Postgres 18 em Docker, porta **5442** | 5432 e 5433 ja ocupadas nesta maquina |
| Schema | SQL puro versionado em `migrations/` | o catalogo ja define coluna, tipo e chave: o DDL e transcricao |
| Amostra | Parquet em `data/parquet/`, particionado por gravacao e taxa nativa | amostra nunca entra no Postgres; `serie_amostral` guarda o ponteiro |
| Analise | DuckDB sobre os Parquet | migrar pra S3/MinIO troca so o path do ponteiro |
| Frontend | Vite + React 19 + TypeScript, zustand, recharts | decisao A: frontend proprio; funil de 4 niveis (N0-N3, 12 blocos) mais Contexto e Box (fora do funil, acessiveis de qualquer nivel), portando o que existe do `saru-app` e construindo o que falta |
| Testes | pytest + ruff | |

## Subir do zero

```bash
make setup      # venv, deps, .env
make up         # Postgres 18 na 5442
make migrate    # aplica as migrations
make doctor     # confere ambiente e inventaria o acervo
make web-setup  # deps do frontend
make web        # dev server em :5177
```

## Estado

Ambiente pronto. Pipeline ainda nao existe: `src/saru_poc/{readers,pipeline}`
estao vazios de proposito, e `migrations/` so tem o bookkeeping. O schema das
26 entidades e o proximo passo.

## Regras que este repo carrega do plano

- **Sem venue resolvido nao existe setorizacao.** Default silencioso e proibido
  (fix estrutural do B2). A resolucao aparece no contrato de saida como
  `resolucao_pista`.
- **Volta ideal <= melhor volta**, sempre. Setor sem dado marca a volta como
  nao-setorizavel em vez de cair em fallback de escala misturada (fix do B1).
- **Reprocessar nunca sobrescreve.** `ingestao` e append-only; objeto Parquet e
  imutavel, identificado por sha256.
- **Degradacao e declarada.** Bloco sem dado diz por que, na tela.
