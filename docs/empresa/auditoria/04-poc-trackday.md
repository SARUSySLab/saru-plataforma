# Auditoria do saru-poc-trackday

Repositorio auditado em modo leitura, branch main em 59afd77, checado em
2026-09-12. Autor de todos os 10 commits de main: Lucas Antunes. 408 testes
coletam sem erro (`uv run pytest -q -x --co`). `uv run ruff check .` acusa 66
avisos, 40 corrigiveis com `--fix`, nenhum bloqueia build ou teste.

## 1. Mapa do repositorio

Pacote `src/saru_poc/`, 17.203 linhas em 44 modulos Python. Tabela por
responsabilidade, com o teste que cobre cada modulo.

| Modulo | Responsabilidade | Linhas | Teste |
|---|---|---|---|
| `acervo.py` | carrega catalogo de canal a partir de `seeds/aliases.yaml` | 283 | `tests/test_acervo.py` (7) |
| `api.py` | monta o app FastAPI, decide o que e publico | 683 | `tests/test_api.py` (16) |
| `auth.py` | login, JWT em cookie httpOnly, argon2 | 278 | `tests/test_auth.py` (9) |
| `clima.py` | previsao do tempo com cache e cascata de fonte | 607 | `tests/test_clima.py` (8) |
| `cli.py` | comandos `saru-poc migrate/doctor/sniff/...` | 1.008 | sem teste dedicado, exercitado de raspao em `test_reingestao.py` |
| `config.py` | leitura do `.env`, uma fonte so | 108 | sem teste dedicado |
| `contrato.py` | valida resposta HTTP contra `contract.ts` | 286 | `tests/test_contrato.py` (6) |
| `db.py` | conexao Postgres | 22 | sem teste dedicado (usado por quase todos) |
| `livetiming.py` | parse e ingestao do XML de cronometragem | 631 | `tests/test_livetiming.py` (14) |
| `migrate.py` | runner de migrations SQL | 67 | sem teste |
| `pista.py` | carrega catalogo de pista de `seeds/tracks.yaml` | 322 | sem teste direto, so uso indireto em fixtures de outros testes |
| `relatorio.py` | etapa 7, relatorio e insight | 1.262 | `tests/test_relatorio.py` (14), `tests/test_relatorio_entre_gravacoes.py` (4) |
| `sarue.py` | assistente de IA (texto livre via OpenRouter) | 232 | sem teste |
| `storage.py` | escrita e leitura de amostra em Parquet/DuckDB | 214 | `tests/test_storage.py` (9) |
| `vivo.py` | ingestao ao vivo do gateway do carro | 214 | `tests/test_vivo.py` (8) |

Pipeline, `src/saru_poc/pipeline/`:

| Modulo | Etapa | Linhas | Teste |
|---|---|---|---|
| `recepcao.py` | 1, recepcao de bundle | 216 | `tests/test_pipeline.py` (9) |
| `ingestao.py` | 2, parse e registro | 500 | `tests/test_pipeline.py`, `tests/test_desempate_perfil.py` (3), `tests/test_reingestao.py` (3) |
| `leitura.py` | leitura de serie compartilhada pelas etapas 5 a 7 | 130 | sem teste dedicado, exercitada dentro de outros |
| `resolucao_pista.py` | 4, alias e GPS | 277 | `tests/test_contrato.py` cobre de raspao, sem teste proprio |
| `corte_voltas.py` | 5, cascata canal/beacon/GPS | 726 | `tests/test_corte_voltas.py` (20) |
| `corte_incremental.py` | corte ao vivo, maquina de estado | 167 | `tests/test_corte_incremental.py` (6) |
| `decomposicao.py` | 6, tempo por trecho | 376 | `tests/test_decomposicao.py` (13) |
| `tracado.py` | 6, tracado medido | 300 | `tests/test_tracado.py` (9) |

Leitores, `src/saru_poc/readers/` (12 registrados, ver secao 3):

| Modulo | Formato | Linhas | Teste |
|---|---|---|---|
| `base.py` | contrato do leitor | 141 | sem teste proprio, contrato exercitado por todos os leitores |
| `formatos.py` | catalogo de assinatura por bytes magicos | 314 | `tests/test_formatos.py` (8) |
| `vbo.py` | Racelogic VBOX `.vbo` | 461 | `tests/test_reader_vbo.py` (30) |
| `ldx.py` | sidecar MoTeC `.ldx` | 160 | `tests/test_reader_ldx.py` (10) |
| `ld.py` | container MoTeC `.ld` | 523 | `tests/test_reader_ld.py` (17) |
| `xrk.py` | AiM RaceStudio 3 `.xrk` | 1.799 | `tests/test_reader_xrk.py` (25), `tests/test_reader_xrk_gps.py` (11), `tests/test_xrk_desempenho.py` (2) |
| `dlf.py` | Pro Tune TDL `.dlf` | 488 | `tests/test_reader_dlf.py` (29) |
| `pi_pid.py` | Pi/Cosworth `.pid` | 510 | `tests/test_reader_pi.py` (25, compartilhado com listhead) |
| `pi_listhead_dat.py` | Pi/Cosworth LISTHEAD `.dat` | 466 | `tests/test_reader_pi.py` |
| `pi_pds.py` | Pi Toolbox `.pds` | 447 | `tests/test_reader_pi_pds.py` (11) |
| `aim_rs2.py` | AiM RaceStudio 2 `.drk`/`.bak` | 264 | `tests/test_reader_aim_rs2.py` (13) |
| `asam_mf4.py` | ASAM MDF4 `.mf4` | 590 | `tests/test_reader_mf4.py` (10) |
| `aim_gpk.py` | inventario AiM RS2 sidecar GPS `.gpk` | 205 | `tests/test_reader_aim_gpk_rrk.py` (22, compartilhado com rrk) |
| `aim_rrk.py` | inventario AiM RS2 run `.rrk` | 190 | `tests/test_reader_aim_gpk_rrk.py` |

Rotas HTTP, `src/saru_poc/rotas/`:

| Modulo | Area | Linhas | Teste |
|---|---|---|---|
| `auth.py` | cadastro, login, logout | 67 | `tests/test_auth.py` |
| `clima.py` | proxy de previsao do tempo | 51 | `tests/test_clima.py` |
| `campeonato.py` | live timing externo | 251 | `tests/test_livetiming.py` |
| `operacao.py` | espinha operacional (evento, sessao, bateria, setup) | 935 | `tests/test_operacao.py` (9) |
| `vivo.py` | ingestao ao vivo, pit wall | 133 | `tests/test_vivo.py` |
| `sarue.py` | pergunta livre ao assistente | 206 | sem teste |

`scripts/` tem 11 arquivos, 1.351 linhas, todos utilitarios de operacao
(importar acervo real, migrar telemetria entre instalacoes, relay de live
timing, reparo one-off). Nenhum tem teste, por serem scripts de operacao e
nao pacote importavel; `replay_sessao.py` e excecao parcial, coberto por
`tests/test_replay_sessao.py` (7) porque suas funcoes puras sao importadas
por caminho.

Achado: `sarue.py`, `rotas/sarue.py` e `migrate.py` nao tem nenhum teste
automatizado, nem direto nem indireto. `pista.py` e
`pipeline/resolucao_pista.py` so aparecem em teste de outro modulo, nunca
como alvo proprio.

## 2. Pipeline de dados ponta a ponta

Sete etapas, cada uma com estado proprio no Postgres, mais a camada HTTP e o
front. Fonte de cada afirmacao: docstring do proprio modulo.

1. Recepcao (`pipeline/recepcao.py:1`). Upload vira 1 `gravacao` e N
   `arquivo_bruto`. So registra proveniencia (hash sha256, formato
   declarado pelos bytes), nao le amostra. Dedupe pelo sha256 do arquivo
   primario.
2. Parse (`pipeline/ingestao.py:1`, `readers/`). Cada tentativa de leitura
   vira linha append-only em `ingestao`, com a versao do leitor e do mapa de
   canal usadas. Arquivo sem leitor registrado tambem gera linha, com
   `status='falhou'` e o motivo: silencio e o defeito, nao a falha.
3. Normalizacao, camada bruta (`storage.py:1`, `pipeline/leitura.py:1`). A
   amostra vira `RecordBatch` do Arrow e e escrita em Parquet, particionada
   por gravacao e taxa nativa, objeto imutavel enderecado pelo sha256. O
   Postgres guarda so o ponteiro (`serie_amostral`). `pipeline/leitura.py`
   aplica o fator do mapa de canal pra sair do valor nativo do fabricante
   (grau, km/h) pro canonico (metro, m/s).
4. Resolucao de pista (`pipeline/resolucao_pista.py:1`). Cascata:
   alias do venue declarado no arquivo contra `pista`/`layout` do catalogo,
   depois posicao mediana do GPS contra a coordenada de referencia do
   layout. Regra dura: sem venue resolvido nao existe setorizacao, sem
   default silencioso.
5. Corte de voltas (`pipeline/corte_voltas.py:1`, `corte_incremental.py:1`).
   Cascata por prioridade de fonte: canal de volta dentro da amostra,
   depois tempos de beacon do sidecar `.ldx`, depois cruzamento de linha de
   chegada por GPS. `corte_incremental.py` reusa as mesmas funcoes de
   debounce e gate por importacao, nunca copia, pro corte ao vivo bater com
   o offline.
6. Decomposicao (`pipeline/decomposicao.py:1`, `tracado.py:1`). Cruza o
   eixo de distancia (canal proprio, senao integral da velocidade, senao
   GPS) contra os limites de trecho do layout (em distancia) pra gerar
   tempo por trecho. O eixo de distancia e fechado no comprimento do layout
   por um fator medido, com faixa de aceitacao 0,9 a 1,1. `tracado.py` gera
   a linha que o carro fez a partir do GPS, com a mesma guarda de tamanho e
   uma segunda guarda de posicao contra a coordenada de referencia.
7. Relatorio (`relatorio.py:1`). Emite o shape de
   `web/src/types/contract.ts`. Volta ideal nunca passa a melhor volta;
   setor sem dado marca a volta como nao setorizavel em vez de fallback com
   escala misturada.

Camada HTTP (`api.py:1`, `rotas/`). Serve o relatorio e a serie de amostras
no shape do contrato, recebe upload de bundle. `GET /api/relatorio/{id}` e
`GET /api/gravacoes/{id}/amostras` sao os unicos dois pontos de saida de
leitura, e os dois passam por `contrato.py` antes de sair
(`SARU_VALIDA_CONTRATO=1` por default): o validador le o proprio
`contract.ts` como fonte, extrai interface e type alias por regex, e
divergencia de shape vira 500 no servidor em vez de tela quebrada no
cliente (`contrato.py:1`, `README.md` secao Rotas).

Front (`web/src/`). Funil de quatro niveis (N0 a N3, 12 blocos em
`web/src/blocos/`) mais Contexto e Box fora do funil
(`web/src/gavetas/`, `web/src/box/`), consumindo `services/relatorio.ts` e
`services/gravacoes.ts` contra o mesmo `contract.ts`.

## 3. Formatos de telemetria suportados

Catalogo em `readers/formatos.py`, 13 formatos com assinatura medida
(`src/saru_poc/readers/formatos.py:55`). 12 tem leitor registrado em
`readers/__init__.py:60`; `bosch_bmsbin` esta catalogado e medido, mas sem
leitor:

| formato_id | Leitor | Teste | Medicao em docs/ |
|---|---|---|---|---|
| `vbox_vbo` | `readers/vbo.py` | `tests/test_reader_vbo.py` | sem doc dedicado, medicao no docstring do leitor |
| `motec_ldx` | `readers/ldx.py` | `tests/test_reader_ldx.py` | sem doc dedicado |
| `motec_ld` | `readers/ld.py` | `tests/test_reader_ld.py` | sem doc dedicado |
| `aim_xrk` | `readers/xrk.py` | `tests/test_reader_xrk.py`, `test_reader_xrk_gps.py`, `test_xrk_desempenho.py` | sem doc dedicado |
| `protune_dlf` | `readers/dlf.py` | `tests/test_reader_dlf.py` | sem doc dedicado |
| `pi_pid` | `readers/pi_pid.py` | `tests/test_reader_pi.py` | sem doc dedicado |
| `pi_listhead_dat` | `readers/pi_listhead_dat.py` | `tests/test_reader_pi.py` | sem doc dedicado |
| `pi_pds` | `readers/pi_pds.py` | `tests/test_reader_pi_pds.py` | sem doc dedicado |
| `aim_drk` | `readers/aim_rs2.py` | `tests/test_reader_aim_rs2.py` | `docs/aim-rs2-medicao.md` |
| `asam_mf4` | `readers/asam_mf4.py` | `tests/test_reader_mf4.py` | sem doc dedicado |
| `aim_gpk` | `readers/aim_gpk.py` | `tests/test_reader_aim_gpk_rrk.py` | `docs/aim-gpk-rrk-medicao.md` |
| `aim_rrk` | `readers/aim_rrk.py` | `tests/test_reader_aim_gpk_rrk.py` | `docs/aim-gpk-rrk-medicao.md` |
| `bosch_bmsbin` | nenhum | nenhum | `docs/bosch-bmsbin-medicao.md` |

`docs/mapa-parsing-dois-motores.md` compara este pacote contra o parser
legado do `saru-app`: 15 arquivos de leitor aqui contra 19 mais
`vendor/ldparser` la, deteccao por assinatura binaria aqui contra cascata de
extensao la, celula sem amostra vira `NaN` aqui contra interpolacao
(`np.interp`) la.

`aim_gpk` e `aim_rrk` tem leitor que le so inventario (cabecalho, contagem
de registro), nao decodifica canal: a semantica do payload nao foi
confirmada mesmo com o banco de configuracao AiM extraido
(`docs/aim-gpk-rrk-medicao.md:8`). `bosch_bmsbin` tem 505 linhas de medicao
em `docs/bosch-bmsbin-medicao.md` (96 arquivos, 920 MB) e nenhum leitor:
divida documentada, nao lacuna silenciosa.

## 4. Branches remotas

Quatro branches no remoto, `main` inclusa.

`feat/pds-amostras`. Autor Vitor Toledo. 12 commits a frente de `main`,
todos partindo do commit atual de `main` (59afd77): merge-base igual ao
tip de `main`, zero risco de conflito hoje. Toca
`src/saru_poc/storage.py`, `web/src/types/contract.ts` (123 linhas),
`web/src/box/PressaoAFrio.tsx`, `web/src/box/modeloPressao.ts` (novo),
`web/src/blocos/PneuResumo.tsx`, mais `tests/test_analise.py` (novo, 419
linhas) e `tests/test_calculadoras.py` (novo). Parece ser o WIP de Vitor
para a camada de analise de pilotagem e o modelo de pressao de pneu
(Gay-Lussac), incluindo dado do formato `.pds` a 304 bytes por registro.
Nao e trabalho de Lucas, e mexe em contrato e em teste que Lucas tambem usa
(`test_auth.py`, `test_clima.py`, `test_operacao.py`, `test_vivo.py`
aparecem no diffstat com poucas linhas, provavel ajuste de fixture, nao
reescrita).

`front/funil-analyzer`. Ja e ancestral de `main` (mesmo commit do merge
`c3c8309`). Branch historica, sem trabalho pendente.

`melhoria/analise`. Aponta pro mesmo commit de `main` (59afd77). Sem
divergencia, sem trabalho pendente: e so um rotulo sobre o tip atual.

## 5. Convencoes

Presentes no repo hoje:

- Nomes de tabela, coluna, funcao e variavel em portugues, sem excecao
  observada em `src/saru_poc/`.
- Sem travessao em texto versionado: commit `be8690633` existe justamente
  pra tirar travessao do nome de uma pista (regra dura da casa).
- Commits em Conventional Commits (`feat`, `fix`, `chore`), em portugues no
  corpo.
- `Makefile` como interface unica de operacao (`up`, `migrate`, `doctor`,
  `pipeline`, `api`, `test`, `fmt`, `web`).
- `.env.example` comentado linha a linha, com o motivo de cada default e um
  aviso de incidente real (limite do Open-Meteo, `.env.example:38`).
- Divida medida, nao suposta: secao propria no `README.md` com contagem
  exata (100 gravacoes PI sem corte, 17 gravacoes a 1 Hz, 67 voltas de
  Curitiba recusadas com a razao 1,164 medida).
- Docstring de modulo com procedencia: quando o codigo vem de porte do
  `saru-app`, o docstring cita arquivo e linha do snapshot (`aa94872`), e
  separa MANTIDO de DESCARTADO (`readers/pi_pid.py:1`, `readers/vbo.py:75`).

Ausentes:

- Sem `CLAUDE.md` e sem `.claude/` no repo.
- Sem CI (nenhum `.github/workflows`, `.gitlab-ci.yml` ou equivalente).
- Sem `CONTRIBUTING.md`.
- Sem `CODEOWNERS`.
- Sem template de PR (`.github/pull_request_template.md` ausente).
- Sem protecao de branch declarada em arquivo (nao verificavel via clone
  local; GitHub guarda isso no lado do servico, nao no `.git`).
- `web/README.md` e o boilerplate padrao do Vite, nunca customizado
  (`web/README.md:1`), unica inconsistencia encontrada frente ao resto do
  repo, que documenta tudo com o motivo local.

## 6. Segredos e caminhos pessoais

Nenhum segredo real (valor de token, senha ou chave de API) foi encontrado
no clone. Os dois arquivos apontados pela tarefa carregam so instrucao e
placeholder:

- `relay-prod.txt:34`, variavel `SARU_SMB_PASSWORD='<senha-do-PC-de-cronometragem>'`,
  placeholder entre `<>`, nunca preenchido.
- `criar-token-relay.txt`, script que IMPRIME um token ao rodar, mas o
  arquivo em si nao carrega valor nenhum.
- `.env.example:22`, `SARU_OPENROUTER_KEY=sk-or-v1-troque-por-uma-chave-real`,
  placeholder.
- `.env.example:26`, `SARU_JWT_SECRET=gere-o-seu-com-secrets-token-urlsafe-48`,
  placeholder.

Caminho pessoal de maquina, achado por grep:

- `.env.example:14` e `.env.example:18`, `/home/lucas-antunes/...`.
- `scripts/auditar_xrk_contra_libxrk.py:35`, mesmo prefixo
  `/home/lucas-antunes/...`.
- `criar-token-relay.txt:2` (comando `cd`), caminho
  `~/Desktop/trabalho/clientes/saru/saru-poc-trackday`, que so existe na
  maquina do Lucas.

Dado operacional sensivel, sem ser segredo de autenticacao:
`relay-prod.txt:34` cita o endereco IP (`192.125.125.10`, fora das faixas privadas RFC 1918) e o usuario
(`amelio`) do PC de cronometragem do autodromo, dentro do comando de
exemplo do relay.

## 7. O que a PoC ainda referencia do saru-app

`SARU_APP_REF` (`.env.example:18`, `config.py:36`) e usado como FALLBACK, ja
sem ser fonte de producao. `acervo.py:124` e `pista.py:145` documentam a
regra: a copia versionada em `seeds/aliases.yaml` e `seeds/tracks.yaml`
vence o snapshot do saru-app, e o snapshot so entra se alguem quiser
reimportar do zero. Ou seja, a PoC ja copiou o que precisa para rodar sem
o `saru-app` montado: `seeds/aliases.yaml`, `seeds/tracks.yaml`,
`seeds/alias_layout.csv`.

O que resta como referencia, sem ser dependencia de runtime:

- Comentario de procedencia em docstring, citando arquivo e linha do
  snapshot `aa94872` (`readers/pi_pid.py:1`, `readers/pi_listhead_dat.py:1`,
  `readers/vbo.py:75`, `readers/dlf.py:11`, `readers/ldx.py:32`). Serve
  para auditoria do porte, nao e lido em runtime.
- `SARU_ACERVO_ROOT` (`.env.example:14`), acervo de telemetria REAL usado
  so em teste, com `pytest.skip` quando a pasta nao esta montada
  (`tests/test_reader_ld.py:1`, `tests/test_formatos.py:1`, entre outros).
  Nao entra em producao.
- `scripts/derivar_curvas.py` e `scripts/auditar_xrk_contra_libxrk.py`
  citam caminho do `saru-app` como fonte de dado ja processado uma vez
  (derivacao de curva, auditoria contra `libxrk`), tarefa pontual ja
  concluida, nao reexecutada em cada deploy.

Para a PoC ficar independente do disco do Lucas de vez, falta so isso:
mover `SARU_ACERVO_ROOT` de teste real pra fixture sintetica onde ainda
depende dele (a maioria dos leitores ja tem fixture sintetica versionada
em `tests/fixtures/`; a comparacao contra acervo real e complemento, pulada
sem a pasta), e decidir se os comentarios de procedencia continuam citando
o snapshot ou passam a citar so o commit deste repo daqui pra frente.

## 8. Propostas de mudanca aditiva minima

Ordenadas pelo que destrava mais com menor atrito.

1. Criar `CLAUDE.md` curto na raiz do repo, so com o que e especifico
   deste projeto (porta 5442, Parquet fora do Postgres, contrato validado
   em `contrato.py`, regra de nao tocar `saru-app`). Justificativa: hoje
   esse contexto so existe no README e nos docstrings, que um agente novo
   tem que ler modulo por modulo pra reconstruir. Combinar com Lucas antes:
   sim, porque `CLAUDE.md` na raiz e visivel toda vez que ele abrir o
   repo.
2. Criar `.github/workflows/ci.yml` rodando `ruff check` e `pytest` a cada
   push. Justificativa: hoje nada barra um commit com teste quebrado antes
   do merge, e o proprio `Makefile` ja tem `make test` e `make fmt` prontos
   pra virar job. Combinar com Lucas antes: sim, CI pode falhar em PR dele
   e bloquear merge sem aviso previo.
3. Criar `CODEOWNERS` com Lucas dono de `src/saru_poc/` e `web/`.
   Justificativa: formaliza o que ja e verdade (todo commit de main e
   dele) sem mudar nenhum fluxo. Combinar com Lucas antes: nao, e so
   registro do que ja acontece.
4. Criar `.github/pull_request_template.md` curto (o que mudou, como
   testar). Justificativa: o repo ja tem uma PR mesclada (`#1`,
   `front/funil-analyzer`) sem template, e Lucas escreve descricao de commit
   detalhada por habito, o template so espelha isso. Combinar com Lucas
   antes: nao, template nao obriga preenchimento.
5. Criar `docs/formatos-medicao-pendente.md` ou anexar a
   `docs/bosch-bmsbin-medicao.md` uma secao "leitor: nenhum" explicita,
   linkada do `README.md` na tabela de dividas. Justificativa: hoje a
   divida do `.bmsbin` sem leitor so aparece pra quem le
   `readers/__init__.py` contra `formatos.py` linha a linha; a secao de
   dividas do README ja tem o habito de listar isso pra outros formatos.
   Combinar com Lucas antes: nao, e edicao aditiva de documentacao
   existente, no padrao que ele mesmo criou.
6. Criar `.claude/` com skill de projeto se e quando este repo passar a ser
   trabalhado por agente com regularidade. Justificativa: e a estrutura
   padrao que Vitor usa em outros repositorios da SARU; aqui so faz
   sentido depois do `CLAUDE.md` do item 1 existir. Combinar com Lucas
   antes: sim, e mudanca de estrutura de projeto, nao so documentacao.

Nenhum item exige mover, renomear ou apagar arquivo existente. Nenhum muda
`Makefile`, `pyproject.toml`, migration ou schema.

## 9. Perguntas

1. `feat/pds-amostras` esta pronta pra virar PR contra `main`, ou ainda em
   desenvolvimento. Ela nao conflita hoje, mas isso muda a cada commit novo
   em qualquer um dos dois lados.
2. `melhoria/analise`, que aponta pro mesmo commit de `main`, pode ser
   apagada do remoto, ou tem uso planejado.
3. O CI do item 8.2 roda so `ruff` e `pytest -q` (rapido, sem Docker), ou
   Vitor quer subir o Postgres em servico do workflow pra rodar os testes
   que hoje dependem de banco real.
4. `SARU_ACERVO_ROOT` continua apontando pro disco do Lucas
   (`/home/lucas-antunes/...`) como convencao do time, ou cada maquina deve
   ter seu proprio `.env` com o caminho local.
5. O `CLAUDE.md` do item 8.1 pode citar o plano canonico
   (`../plano-poc-core-trackday.md`, hoje so no Drive do Vitor) ou deve
   ficar restrito ao que esta neste repo.
