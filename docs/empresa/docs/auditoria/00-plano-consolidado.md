# Plano consolidado da auditoria SARU

Data: 2026-09-12. Leitor: Vitor Toledo. Fontes: relatórios 01 a 06 desta pasta.

A organização tem quatro repositórios ativos, um deles o produto e sem contrato, e nove arquivados com três gerações de
contrato que se contradizem. O caminho é criar o padrão uma vez no perfil `.github` da
organização, um repositório da empresa para decisão e documentação, e mudanças aditivas na
PoC combinadas com Lucas. Antes disso, 16 decisões são suas.

## 1. Situação medida

| Item | Valor | Fonte |
|---|---|---|
| Repositórios na organização | 13 (4 ativos, 9 arquivados em 2026-08-29) | `gh repo list` |
| Plano GitHub | Free, 12 repositórios privados | `gh api orgs/SaruSysLab` |
| Proteção de branch em `main` | Bloqueada (HTTP 403 no plano Free) | `gh api .../rulesets` |
| Membros da organização | 6 (admins: `vitormtt`, `ciro-c`) | `gh api orgs/SaruSysLab/members` |
| Contrato no repositório ativo | Nenhum (sem CLAUDE.md, .claude, CI, CODEOWNERS) | 04-poc-trackday.md §5 |
| Documentos inventariados | 427 (140 em docs, KB e research; 287 em app e física) | 02 e 03 .tsv |
| Documentos vigentes | 222 | 02 e 03 .tsv |
| Documentos para portar à PoC | 91 (28 docs, 50 portar, 13 docs) | 02 e 03 .tsv |
| Documentos para o repositório da empresa | 54 | 02 e 03 .tsv |
| Documentos de física sem casa | 53 | 02 e 03 .tsv |
| ADRs do saru-app | 49, dos quais 10 valem para a PoC e 8 pedem adaptação | 03 §Os 49 ADRs |
| Segredo real em repositório | Nenhum encontrado | 04 §6 |
| Branches da PoC já mescladas e vivas no remoto | 2 (`front/funil-analyzer`, `melhoria/analise`) | 04 §4 |

## 2. Decisões que só você toma

Cada linha traz a recomendação e o que muda se você escolher diferente.

| Nº | Decisão | Recomendação | Motivo |
|---|---|---|---|
| D1 | Plano GitHub | Assinar Team (4 USD por usuário por mês no primeiro ano) só para quem faz commit; reduzir membros para 2 ou 3 | Sem Team, nada bloqueia push direto em `main` de repositório privado. Tornar público expõe acervo e caminho de cliente |
| D2 | Membros e papéis | Decidido em 2026-09-12: só Vitor e Lucas. `ciro-c` removido (confirmado na API: único admin é `vitormtt`); Vinicius saiu por conta própria e não é mais referência. Pendente: `Borges061`, `gustavolima973`, `refalrsf` seguem com leitura | Admin pode apagar repositório. Cada assento custa no Team |
| D3 | Repositório da empresa | Criar `SaruSysLab/saru` novo; manter `SARU` arquivado | O `SARU` antigo carrega caminhos mortos e CLAUDE.md global de junho (01 §4) |
| D4 | Estratégia de merge | Squash com histórico linear | Um commit por PR, changelog limpo para release-please |
| D5 | Prefixo de branch | `feat/`, `fix/`, `docs/`, `chore/` mais número da issue (`feat/12-corte-de-volta`) | A PoC usa `front/` e `melhoria/`; o número no nome facilita a busca, e o vínculo formal com a issue vem de `gh issue develop` |
| D6 | Idioma | Português em código, commit e documentação nos repositórios da SARU; inglês fica nos arquivados | Time, cliente e acervo são brasileiros. A PoC já está inteira em português. Exige exceção à regra global de commit em inglês |
| D7 | Documentação | `docs/` por repositório mais `docs/` do repositório da empresa; sem portal MkDocs agora | O portal morreu em julho com 33 páginas. Volta quando houver 3 repositórios ativos |
| D8 | SPM.md | Acaba; estado vivo vira issue e milestone, decisão vira `docs/decisions.md` ou ADR | 129 KB de SPM que ninguém lia no início da sessão (01 §4) |
| D9 | ADR mestre | Um só, em `saru/docs/adr/`, para decisão cross-repositório; ADR de repositório fica no repositório | Hoje declarado em 4 lugares (01 §2) |
| D10 | Física | Os 53 documentos de física vão para `saru/docs/fisica/` até existir o repositório de física | Sem repositório de código, não há por que criar um só para docs |
| D11 | PoC, mudanças aditivas | CLAUDE.md, CI com ruff e pytest, CODEOWNERS, template de PR, nota de dívida do bmsbin. Abrir como issue e combinar com Lucas antes de CLAUDE.md, CI e `.claude/` | 04 §8 lista o que exige combinar |
| D12 | Branches da PoC | Apagar `front/funil-analyzer` e `melhoria/analise` do remoto; abrir PR de `feat/pds-amostras` | Duas já são ancestrais de `main`; a sua tem 12 commits sem conflito |
| D13 | Sprint e issue | Sprint de 1 semana, issue form com história, critérios de aceite, restrições e rastreabilidade; milestone por marco; um Projects por repositório | Modelo da conversa do Gemini, gratuito no Free |
| D14 | Drive, estrutura | `Trabalho/SARU` vira 4 áreas: `marca/`, `referencias/` (papers e Porsche_Cup/Docs), `notas/` (consumidas para o git e movidas para processado) e `dados/` (só o que não cabe no git). Acervo bruto fica onde está; `dados_telemetria` recebe amostra por formato e categoria onde a cobertura é fraca (AiM moto e F3 em 15%, MoTeC e PI `.pds` pela metade) | 05 §C. Espelhos de repositório no Drive (01_ Saru-KB, 03_Marketing) saem depois de conferir que o git tem tudo |
| D15 | Drive, quarentena imediata | Mover para quarentena `03_Marketing/.env` (rotacionar a chave), os 6 instaladores RaceCon (459 MB) e `03_Marketing/logs/` (transcrições de agente) | 05 §Segredos. Duplicatas de vídeo e zips só depois de comparar hash |
| D16 | Apuama | Levar TIRE, VD_NOVO, ARB e o que de VD_antigo e Trainee/Tyre não repetir TIRE para `saru/docs/fisica/`; `sobras_restos` para quarentena; `Historico_SARU_KB` renomeado para `Estudo/Apuama/historico` | 05 §B. CAD nunca entra em cópia, incluindo os 4 soltos fora de Engenharia_CAD |

## 3. O que sobrevive dos arquivados

Peças que entram no padrão sem reescrever, com origem em `_arquivo/`:

- Runbook de GitHub Flow em 7 passos (`saru-docs/docs/runbooks/github-flow.md`).
- Processo de ADR com imutabilidade e supersessão, e a skill `adr` que o automatiza
  (`saru-app/docs/adr/README.md`, `saru-app/.claude/skills/adr/`).
- Hooks `block-dangerous.sh`, `lint-changed.sh` e `session-branch-guard.sh` sem a linha de
  `develop` (`saru-app/.claude/hooks/`).
- Skills `spec-first` e `tests-as-gate` (`saru-app/.claude/skills/`).
- Agentes por área: `code-reviewer`, `evaluator`, `test-writer`, `repo-explorer`,
  `browser-tester` (`saru-app/.claude/agents/`).
- Template de PR com gate de física (`saru-physics-py/.github/pull_request_template.md`)
  fundido com o de produto (`saru-app/.github/pull_request_template.md`).
- Três workflows reutilizáveis nunca chamados (`dot-github/workflows/`).
- Seções 2 a 6 do `saru-app/docs/STANDARDS.md` (árvore, ruff, mypy, pytest, uv, gitignore).
- Validadores `check-docs.py` e `check-adr-drift.py` (`saru-app/scripts/`).

## 4. O que a PoC absorve do saru-app

Código e documento com caminho em `_arquivo/saru-app/`:

- Leitores em `services/telemetry-api/saru_lapanalyzer/infra/datasources/` que a PoC ainda
  não tem: `drk_file.py`, simuladores (`sim_gt7_csv.py`, `sim_acc_motec.py`,
  `sim_ams2_csv.py`, `sim_iracing_csv.py`) e exportações (`real_aim_csv.py`,
  `real_windarab_csv.py`, `real_wintax_csv.py`, `track_addict_csv.py`).
- `aliases.yaml` de 1736 linhas e `channel_mapper.py` (a PoC já tem cópia em `seeds/`;
  conferir diferença).
- Contrato canônico de canais, ADR-0049 (`shared/proto/telemetry-channels.json`).
- Cascata de pista por GPS, ADR-0048 (`domain/track_map.py`, `tests/test_track_resolution.py`).
- Tokens de marca, ADR-0046 (`services/frontend/src/app/tokens.css`).
- Os 10 ADRs marcados "sim" e os 8 "adaptar" em 03 §Os 49 ADRs.
- Auditorias de formato em `docs/audit/` (PI Cosworth em nível de byte, fronteira de volta
  `.pid`, calibração de frenagem por G, censo de canais) e `docs/architecture/formato-dlf-esparso.md`.
- Único feedback de engenheiro de pista sênior (`docs/execution/2026-08-20-feedback-giuliano-engenheiro.md`).

## 5. Execução por fase

Estimativas em minutos de trabalho do agente, depois das decisões.

| Fase | O que | Minutos | Depende de |
|---|---|---|---|
| 0 | Suas respostas às 16 decisões | | |
| 1 | Perfil `.github`: CONTRIBUTING, SECURITY, CODEOWNERS padrão, template de PR, 4 issue forms, `guard-pr.yml`, workflows chamáveis, README do perfil atualizado | 60 | D1, D2, D4, D5, D6 |
| 2 | Repositório `saru`: CLAUDE.md de 20 linhas, `AGENTS.md`, README, `docs/decisions.md` com as 16 decisões, `docs/adr/` com o ADR mestre, migração dos 54 documentos da empresa e dos 53 de física, cada um com front-matter e origem | 120 | D3, D7, D9, D10 |
| 3 | PoC: issue para Lucas com as 6 mudanças aditivas; CODEOWNERS, template de PR e nota do bmsbin de imediato; CLAUDE.md, CI e `.claude/` após o ok dele; limpeza das 2 branches; PR de `feat/pds-amostras` | 60 | D11, D12 |
| 4 | Migração dos 91 documentos para `saru-poc-trackday/docs/`, com índice e front-matter, em PR próprio | 90 | Fase 3 |
| 5 | Ruleset em `main` dos dois repositórios, labels, milestones, Projects, sprint 1 com issues no modelo | 45 | D1, D13 |
| 6 | Drive: quarentena de segredo e instaladores; lista origem e destino das 4 áreas; comparação por hash das duplicatas de vídeo e zip; simulação da quarentena; execução após seu ok | 90 | D14, D15, D16 |
| 7 | Validação dos links das pesquisas de mercado antes de virarem fonte citável | 90 | Fase 2 |
| 8 | Fechar caminhos mortos nos arquivados só se algum for reativado; senão, nada | 0 | |

Total após as decisões: cerca de 9,5 horas de agente, em 4 ou 5 sessões.

## 6. O que não foi verificado

- Nenhum link das pesquisas de mercado de `saru-KB/50_company/research/` foi aberto.
- Hash de arquivo entre Drive e `dados_telemetria` não foi comparado; o índice do Drive só
  tem nome e tamanho.
- Comportamento do Antigravity com `AGENTS.md` na raiz não tem fonte oficial (06 §Não confirmado).
- Preço do plano Team após o primeiro ano não aparece na página capturada.
