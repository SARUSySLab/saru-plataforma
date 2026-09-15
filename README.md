# saru-plataforma

Código da plataforma SARU, todas as famílias: Piloto, Equipe, Engenheiro, Campeonato e Aluno.
Criado em 2026-09-14 a partir da decisão em `SARUSySLab/saru-empresa`, `docs/decisions.md`. O ponto de partida é a PoC
`saru-poc-trackday` na `main` 0776381, portada inteira com histórico; a PoC fica congelada como repositório do Lucas.

Regras: `main` só muda por PR; nenhum agente mescla; número de física só com tabela de medição; toda issue
é validada por Vitor pelo protocolo em `SARUSySLab/saru-empresa`, `docs/processo/validacao-de-issue.md`.

## O que veio da PoC

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

Pipeline completo (7 etapas) mais a camada HTTP. Medido no catalogo em 29/08:
198 gravacoes, 686 series em Parquet, 141 voltas, 369 tempos de trecho.

| Etapa | Estado | Onde |
|---|---|---|
| 1. Recepcao | pronta | `pipeline/recepcao.py` |
| 2. Parse | pronta | `pipeline/ingestao.py` + `readers/` |
| 3. Normalizacao | pronta (camada bruta) | `storage.py`, `pipeline/leitura.py` |
| 4. Resolucao de pista | degrau alias | `pipeline/resolucao_pista.py` |
| 5. Corte de voltas | pronta | `pipeline/corte_voltas.py` |
| 6. Decomposicao | pronta | `pipeline/decomposicao.py` + `pipeline/tracado.py` |
| 7. Relatorio e insight | pronta | `relatorio.py` |
| API | pronta (leitura + upload) | `api.py` |

```bash
make pipeline   # etapas 4 a 6 sobre o que ja foi ingerido
make api        # API na 8010, que o vite ja proxia em /api
uv run saru-poc relatorio <gravacao_id> --fixture   # etapa 7 -> fixture do front
```

### Rotas

| Rota | O que devolve |
|---|---|
| `GET /api/saude` | ping do Postgres |
| `GET /api/gravacoes?com_volta=` | catalogo, com quantas voltas e trechos cada uma tem |
| `GET /api/relatorio/{id}?volta=&referencia=` | `Relatorio` do contrato, pro par em escopo |
| `GET /api/gravacoes/{id}/amostras?volta=` | `SerieAmostras` na grade comum (900 pontos) |
| `POST /api/gravacoes` | recebe bundle, devolve 202 e roda as etapas 2 a 6 em background |
| `POST /api/gravacoes/{id}/contexto` | captura de contexto de sessao (bloco 15) |

Toda resposta de leitura e validada contra `web/src/types/contract.ts` antes de
sair (`SARU_VALIDA_CONTRATO=1`, default). Divergencia de shape vira 500 no
servidor em vez de tela quebrada no cliente. O validador esta em `contrato.py`,
le o proprio `.ts` como fonte e nao precisou de dependencia nova no front.

### Dividas medidas, nao supostas

- **100 gravacoes PI** (`pi_pid`, `listhead_dat`) tem corte de volta dentro do
  arquivo (`EVNT_B0`) que o leitor ainda nao decodifica: nao cortam, com motivo.
- **17 gravacoes cortam por canal a 1 Hz**, o que da tempo de volta inteiro em
  segundos. Refinar o instante do corte contra serie de taxa alta segue aberto.
- **Curitiba: 67 voltas recusadas na decomposicao.** O catalogo diz 3.220 m e o
  carro anda 3.749 m (razao 1,164, medida em 67 voltas, com canal de distancia e
  integral da velocidade concordando entre si). O comprimento cadastrado
  provavelmente esta errado, ou e outro layout. Decisao de dominio, nao de
  codigo.
- **As 3 gravacoes GT7 tem GPS de Donington Park declarando Interlagos.** A
  pista esta certa (distancia por volta da 4.217 m contra 4.309 m de
  Interlagos); o exportador emite coordenada de outro lugar. Corte por GPS e
  tracado recusam as duas com o tamanho do erro na mensagem.
- **Zero tracado gravado**, por consequencia do item acima: `tracado` e
  `subtracado` estao implementados e vazios, esperando GPS coerente.
- **Consumo de combustivel**: existe `Fuel Level` como canal bruto no acervo,
  mas nao ha canal canonico de combustivel no vocabulario. O bloco 14 degrada
  com `sem_canal_combustivel` ate o canal entrar no mapa.
- **`fase` vazia no catalogo**, entao `tempo_por_fase` sai sempre declarado como
  indisponivel.
- O canal de volta e casado por NOME BRUTO, nao pelo vocabulario canonico. O
  acervo prova que nome igual nao garante semantica igual (um `Lap Number` que
  vai de 28 a 2572, rejeitado pela guarda de densidade).

## Regras que este repo carrega do plano

- **Sem venue resolvido nao existe setorizacao.** Default silencioso e proibido
  (fix estrutural do B2). A resolucao aparece no contrato de saida como
  `resolucao_pista`.
- **Volta ideal <= melhor volta**, sempre. Setor sem dado marca a volta como
  nao-setorizavel em vez de cair em fallback de escala misturada (fix do B1).
- **Reprocessar nunca sobrescreve.** `ingestao` e append-only; objeto Parquet e
  imutavel, identificado por sha256.
- **Degradacao e declarada.** Bloco sem dado diz por que, na tela.
