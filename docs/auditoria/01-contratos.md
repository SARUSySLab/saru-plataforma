# Problema 1: três contratos de trabalho convivendo na SaruSysLab

Data da auditoria: 2026-09-12. Escopo: só leitura dos clones em
`/home/vitor/Desktop/Motorsport/SARU/_arquivo/` e de `saru-poc-trackday`.

Existem três gerações de contrato escritas entre junho e agosto de 2026, e nenhuma delas
governa o repositório que está em uso hoje. O `saru-poc-trackday` não tem `CLAUDE.md`,
não tem `.claude/` e não tem `.github/`. Quem chegar ao time hoje não encontra regra
nenhuma no repositório principal, e encontra três regras conflitantes nos arquivados.

## 1. As gerações

### 1.1 Identificação

| Geração | Data | Repositórios | Arquivos de contrato |
|---|---|---|---|
| G1, guarda-chuva local | 2026-06-24 a 2026-06-29 | `_arquivo/SARU` | `CLAUDE.md`, `AGENTS.md` (cópia byte a byte), `SGM.md`, `.claude/rules/{git-workflow,python-workspace,calibration-guardrails}.md`, `.claude/context.md`, `.agents/skills/docs-auditor/SKILL.md`, `opencode.json`, `.github/copilot-instructions.md`, `implementation_plan.md` |
| G2, portal e base de conhecimento | 2026-07-08 a 2026-07-18 | `_arquivo/saru-docs`, `_arquivo/saru-KB`, `_arquivo/dot-github` | `saru-docs/docs/runbooks/github-flow.md`, `release.md`, `mvp-board.md`, `docs/onboarding/index.md`, `docs/arquitetura/repos.md`, `mkdocs.yml`, `.github/{CODEOWNERS,pull_request_template.md,workflows/docs.yml}`, `saru-KB/README.md`, `saru-KB/SPM.md`, `saru-KB/40_software_arch/adr/{README,MASTER_ADR}.md`, `saru-KB/scripts/check-docs.sh`, `dot-github/profile/README.md`, `dot-github/workflows/reusable-*.yml` |
| G3, produto | 2026-07-23 a 2026-08-22 | `_arquivo/saru-app`, `_arquivo/saru-physics-py`, `_arquivo/saru-physics-jl`, `_arquivo/saru-telemetry-gt7` | `saru-app/CLAUDE.md` (+ `AGENTS.md` symlink), `docs/STANDARDS.md`, `docs/ARCHITECTURE.md`, `docs/README.md`, `docs/adr/` (49 ADRs + `MASTER_ADR.md` + `RASTREABILIDADE.md`), `.claude/{settings.json,agents,commands,hooks,skills}`, `.github/{CODEOWNERS,pull_request_template.md,workflows/ci.yml}`, `scripts/check-docs.py`, `scripts/check-adr-drift.py`, `SPM.md`; `saru-physics-py/CLAUDE.md` e `saru-physics-jl/CLAUDE.md` (ambos com `AGENTS.md` symlink e `SPM.md`) |
| Linha atual, sem contrato | 2026-08-28 a 2026-08-30 | `saru-poc-trackday` | nenhum. Só `README.md`, `Makefile`, `pyproject.toml` e `docs/` de medição |

O `saru-telemetry-gt7` pertence à G3 por data e por ser submódulo do `saru-app`
(`saru-app/CLAUDE.md:23`), mas não tem `CLAUDE.md`, `AGENTS.md`, `SPM.md`, `.claude/` nem
`CODEOWNERS`. Só tem `.github/workflows/ci.yml`.

### 1.2 O que cada geração define

| Dimensão | G1 (`_arquivo/SARU`) | G2 (`saru-docs`, `saru-KB`, `dot-github`) | G3 (`saru-app` e física) | Linha atual (`saru-poc-trackday`) |
|---|---|---|---|---|
| (a) Processo git | Git Flow: `main` de release e `develop` no dia a dia, `feature/claude-*` e `feature/ag-*`, merge `--no-ff`, sem PR por ser dev solo (`CLAUDE.md:61-62`, `.claude/rules/git-workflow.md:4-17`) | GitHub Flow: branch curta a partir de `main`, PR pequeno, CI e CODEOWNERS, apagar a branch, sem self-merge em física, contrato, auth, segurança ou claim comercial (`saru-docs/docs/runbooks/github-flow.md:1-11`, `docs/onboarding/index.md:59-66`, `dot-github/profile/README.md:14-17`) | GitHub Flow no papel (`saru-app/docs/STANDARDS.md:148-160`, `docs/adr/0012-github-org-docs-mvp.md:35-41`) e Git Flow na prática (`saru-app/CLAUDE.md:6`, `.github/workflows/ci.yml:3-10`, `.claude/hooks/session-branch-guard.sh:80-86`, `saru-physics-py/CLAUDE.md:43-45`) | Não escrito. Os fatos: 1 PR mergeado (`front/funil-analyzer`), branches remotas `feat/pds-amostras`, `melhoria/analise`, base `main`, sem `develop` |
| (b) Nomes de repositório e serviço | `saru-os`, `saru-gateway`, `saru-core`, `saru-core-jl`, árvore `platform/`, `products/`, `partnerships/` (`_arquivo/SARU/README.md:14-34`) | `saru-app`, `saru-physics-py`, `saru-physics-jl`, `saru-docs`, `saru-research` (`saru-docs/docs/arquitetura/repos.md:3-9`); org escrita `SARUSySLab` (`saru-docs/mkdocs.yml:5`) | Repo canônico `saru-app`, produto "SARU Hub", módulo "SFL" (`saru-app/docs/adr/0022-nomenclatura-comercial-hub-sfl.md:33-42`); serviços `web`, `api`, `engine`, com `telemetry-api` a renomear (`docs/adr/0003-convencao-de-nomes.md:24-31`) | `saru-poc-trackday`, entidades e CLI em português (`README.md:37-52`); remote `git@github.com:SaruSysLab/saru-poc-trackday.git` |
| (c) Memória | Dois níveis: `SGM.md` na raiz e `SPM.md` por repo, nome fixo para não quebrar prompt (`CLAUDE.md:45-47`, `SGM.md:1-3`) | `SPM.md` por repo, git como fonte de verdade, Drive só com espelho curado (`saru-KB/SPM.md:1-4`, `saru-KB/README.md:4-6`) | `SPM.md` continua, mas virou arquivo gigante: `saru-app/SPM.md` tem 129 KB e `saru-physics-jl/SPM.md` 36 KB; `saru-physics-py/CLAUDE.md:55-57` manda ler `AGENTS.md` e `BACKLOG.md`, que não existe | Nenhuma. Estado vivo mora no `README.md` e no catálogo Postgres |
| (d) Documentação | Perene no repositório, em `docs/`, nunca em artefato de sessão (`CLAUDE.md:44`); pesquisa só nos 3 documentos mestre da base de conhecimento (`CLAUDE.md:48`, `.agents/skills/docs-auditor/SKILL.md:12-24`) | Portal MkDocs Material em `saru-docs` com `nav` manual (`saru-docs/mkdocs.yml:45-83`); taxonomia numerada na KB com ADR cross-ecossistema em fonte única (`saru-KB/40_software_arch/adr/README.md:3-7`) | `docs/` por repositório com front-matter obrigatório (`saru-app/docs/README.md:54-70`), ADR imutável e índice atualizado no mesmo commit (`docs/adr/README.md:24-28`), validadores determinísticos (`scripts/check-docs.py:9-18`, `scripts/check-adr-drift.py:4-20`) | `docs/` com cinco documentos de medição de formato de arquivo. Sem ADR, sem índice, sem front-matter |
| (e) Agentes de IA | `CLAUDE.md`, `GEMINI.md` e `AGENTS.md` como espelhos manuais (`CLAUDE.md:76-77`); roteamento por tipo de tarefa e tabela de modelos Haiku 4.5, Sonnet 4.6, Opus 4.8 (`CLAUDE.md:50-56`, `:64-67`); OpenCode com DeepSeek e 4 servidores MCP (`opencode.json:2-52`); skill em `.agents/skills/` | Nenhum arquivo de agente. `saru-docs` e `dot-github` não têm `CLAUDE.md`, `AGENTS.md` nem `.claude/` | `.claude/` completo no `saru-app`: 5 agentes com modelo no frontmatter (`sonnet`, `opus`, `haiku`), 3 comandos, 6 hooks, 9 skills, permissões em `settings.json:1-18`; `AGENTS.md` é symlink para `CLAUDE.md` em `saru-app`, `saru-physics-py` e `saru-physics-jl`; `saru-physics-py/CLAUDE.md:70-76` aponta para `.agents/skills/`, que está vazia | Nenhum |
| (f) Padrão visual | Anti-slop com HSL, fontes modernas, dark limpo e micro-animações (`CLAUDE.md:41`) | Tema `slate` com primária preta e acento âmbar no portal (`saru-docs/mkdocs.yml:17-20`) | Flat com dois temas, sem gradiente, glow ou sombra, tokens em `services/frontend/src/app/tokens.css`, fontes Outfit e Inter (`saru-app/CLAUDE.md:38-63`), apoiado na ADR-0046, que está Proposta e nunca foi ratificada (`docs/adr/README.md:77`) | Recharts e zustand, sem token declarado (`README.md:18`) |

## 2. Contradições

| Tema | O que cada geração diz | Evidência | O que vale hoje |
|---|---|---|---|
| Modelo de branch | G1 exige `develop`; G2 proíbe `develop`; G3 escreve GitHub Flow no padrão e mantém Git Flow no CI e no hook | `_arquivo/SARU/.claude/rules/git-workflow.md:4`; `saru-docs/docs/arquitetura/repos.md:11-12`; `saru-app/docs/STANDARDS.md:150` contra `saru-app/.github/workflows/ci.yml:3-10` e `.claude/hooks/session-branch-guard.sh:82` | Decisão: GitHub Flow, `main` protegida, branch por tarefa, sem `develop` (2026-09-12). Estado real em 2026-09-12: sem proteção de servidor na organização, plano Free devolve 403 (00 §1) |
| Pull request | G1 dispensa PR por ser dev solo; G2 e G3 exigem PR com CI verde | `_arquivo/SARU/CLAUDE.md:62`; `saru-docs/docs/runbooks/github-flow.md:3-7`; `saru-app/docs/STANDARDS.md:154` | PR obrigatório, aceito e validado antes do merge |
| Estratégia de merge | G1 manda merge `--no-ff`; G2 deixa em aberto entre squash e merge | `_arquivo/SARU/.claude/rules/git-workflow.md:15`; `saru-docs/docs/runbooks/github-flow.md:8` | Decisão pendente de Vitor |
| Prefixo de branch | G1 usa `feature/claude-*` e `feature/ag-*`; G2 e G3 usam `feat/`, `fix/`, `docs/`, `chore/`, `research/`; o repositório ativo usa `front/` e `melhoria/` | `_arquivo/SARU/.claude/rules/git-workflow.md:5-6`; `saru-app/docs/STANDARDS.md:153`; `git -C saru-poc-trackday branch -a` | Decisão pendente de Vitor. O padrão G2/G3 é o único compatível com um time |
| Onde mora o ADR mestre | G2 declara fonte única no `saru-KB`; `saru-app` mantém o seu próprio `MASTER_ADR.md`; o índice do `saru-app` diz que a decisão cross-ecossistema vive no `SGM.md`; o validador do `saru-app` procura o mestre no `saru-docs` | `saru-KB/40_software_arch/adr/README.md:3-7`; `saru-physics-py/docs/adr/MASTER_ADR.md:3-4`; `saru-app/docs/adr/MASTER_ADR.md` existe; `saru-app/docs/adr/README.md:13-16`; `saru-app/scripts/check-adr-drift.py:11-13` | Decisão pendente de Vitor. Quatro locais declarados para o mesmo arquivo |
| A base de conhecimento está viva | `saru-KB` se declara fonte de verdade desde 2026-07-15; o `saru-app` afirma que a `saru-KB` foi descontinuada em 2026-08 e que o ponteiro antigo aponta para repositório inexistente | `saru-KB/README.md:4-6`; `saru-app/CLAUDE.md:43-44` | O clone `_arquivo/saru-KB` existe e tem remote ativo. Decisão pendente de Vitor sobre arquivar de fato |
| Onde mora a documentação perene | G1 manda tudo para `docs/` do repositório e, três linhas depois, manda pesquisa para os 3 documentos mestre da KB; G2 cria o portal MkDocs; G3 volta para `docs/` por repositório | `_arquivo/SARU/CLAUDE.md:44` contra `:48`; `saru-docs/mkdocs.yml:45-83`; `saru-app/docs/README.md:24-52` | Documentação permanente no GitHub (decisão de 2026-09-12). O portal MkDocs é decisão pendente |
| Quem é o dono que ratifica | O front-matter dos ADRs diz `owner: vitor`; as linhas de status dizem ratificado pelo dono `@viniciusvieira00` | `saru-app/docs/adr/0012-github-org-docs-mvp.md:3-4` contra `docs/adr/0022-nomenclatura-comercial-hub-sfl.md:12` | Vitor. Vinicius contribuiu de junho a agosto e os repositórios estão arquivados |
| CODEOWNERS | Os quatro arquivos apontam tudo para `@viniciusvieira`, com comentário dizendo para acrescentar o handle do Vitor depois. O handle real usado nos commits e no SPM é `viniciusvieira00` | `saru-app/.github/CODEOWNERS:4`, `:20-21`; `saru-physics-py/.github/CODEOWNERS:2-4`; `saru-physics-jl/.github/CODEOWNERS:2-4`; `saru-docs/.github/CODEOWNERS:1`; `saru-KB/SPM.md:21` | Refazer. Vitor é dono de tudo hoje; Lucas é dono do `saru-poc-trackday` |
| Nome da organização | Os documentos escrevem `SARUSySLab`; os remotes de todos os 10 clones escrevem `SaruSysLab` | `saru-docs/mkdocs.yml:5` e `saru-KB/README.md:4` contra `git -C _arquivo/saru-app remote -v` | `SaruSysLab`, que é o que o GitHub responde |
| Nome do produto e do repositório | `saru-os`, `saru-gateway` e `saru-unified-platform` (G1); `saru-app` (G2); repo `saru-app` com produto "SARU Hub" e módulo "SFL" (G3) | `_arquivo/SARU/README.md:17`; `saru-docs/docs/arquitetura/repos.md:5`; `saru-app/docs/adr/0022-nomenclatura-comercial-hub-sfl.md:33-39` | Decisão pendente de Vitor. O produto hoje é o `saru-poc-trackday`, que não herdou nome comercial nenhum |
| Banco de dados | G1 proíbe SQLite em qualquer caso e a ADR-0004 repete a proibição; o `saru-telemetry-gt7`, submódulo do `saru-app`, persiste em SQLite | `_arquivo/SARU/CLAUDE.md:40`; `saru-app/docs/adr/README.md:35`; `_arquivo/saru-telemetry-gt7/internal/store/sqlite.go` | A regra global do operador mantém PostgreSQL. O caso do GT7 é local-first e precisa de exceção escrita ou de correção |
| Idioma | G1 a G3 usam código e commit em inglês com interface em português (`saru-physics-py/CLAUDE.md:49`); o repositório ativo usa português em tabela, função, CLI e mensagem de commit | `saru-physics-py/CLAUDE.md:49`; `saru-poc-trackday/migrations/001_identidade.sql`; `git -C saru-poc-trackday log` | Decisão pendente de Vitor |
| Modelos de IA | G1 fixa uma tabela com Haiku 4.5, Sonnet 4.6 e Opus 4.8, que não são nomes de modelo existentes; G3 põe o modelo no frontmatter de cada agente | `_arquivo/SARU/CLAUDE.md:50-56`; `saru-app/.claude/agents/code-reviewer.md:4` | A regra global atual: modelo no frontmatter do agente, nunca na conversa (`~/.claude/CLAUDE.md`, seção Modelos) |
| Padrão visual | G1 pede micro-animações; G3 proíbe sombra, glow e gradiente | `_arquivo/SARU/CLAUDE.md:41`; `saru-app/CLAUDE.md:59` | Decisão pendente de Vitor. A ADR-0046 que sustenta o visual atual está Proposta e a implementação a antecipou (`saru-app/docs/adr/README.md:77`) |

Dez ADRs do `saru-app` seguem Proposto e aguardam ratificação: 0033, 0038, 0040, 0041,
0043, 0044, 0046, 0047, 0048 e 0049 (`saru-app/docs/adr/README.md:64-80`). Um processo que
depende de ratificação e acumula dez pendências não está funcionando.

## 3. O que sobrevive à consolidação

| Peça | Origem | Por que fica |
|---|---|---|
| Runbook de GitHub Flow | `_arquivo/saru-docs/docs/runbooks/github-flow.md` | Sete passos, cabe numa tela, já é a decisão de 2026-09-12 |
| ADR-0012 | `_arquivo/saru-app/docs/adr/0012-github-org-docs-mvp.md` | É o registro formal da adoção do GitHub Flow e dos gates de claim físico |
| Processo de ADR | `_arquivo/saru-app/docs/adr/README.md:24-28` e `.claude/skills/adr/SKILL.md` | Imutabilidade, supersessão explícita e índice atualizado no mesmo commit. A skill automatiza |
| Front-matter de documento | `_arquivo/saru-app/docs/README.md:54-70` | `owner`, `status` e `updated` são o que separa documento consultável de arquivo velho |
| Validadores de documentação | `_arquivo/saru-app/scripts/check-docs.py`, `scripts/check-adr-drift.py` | Determinísticos, sem heurística, nasceram de 28 achados reais de auditoria |
| Seções 2 a 6 do STANDARDS | `_arquivo/saru-app/docs/STANDARDS.md:46-144` | Árvore por linguagem, configuração de ruff, mypy, pytest e uv, `.gitignore` e regra de Docker. Nada disso depende do modelo de branch |
| Hook de bloqueio de comando destrutivo | `_arquivo/saru-app/.claude/hooks/block-dangerous.sh` | Cinco regras, cada uma com motivo. Cobre `rm -rf`, pipe para shell, `chmod 777`, force push e escrita em `.env` |
| Hook de trava de branch por sessão | `_arquivo/saru-app/.claude/hooks/session-branch-guard.sh` | Nasceu de três incidentes medidos em 2026-08-08, documentados no cabeçalho. Precisa perder a regra de `develop` (linha 82) |
| Hook de lint do arquivo tocado | `_arquivo/saru-app/.claude/hooks/lint-changed.sh` | Advisory, por serviço, nunca bloqueia |
| Skills de disciplina | `_arquivo/saru-app/.claude/skills/{spec-first,tests-as-gate}/SKILL.md` | Spec curta antes do código e verificação verde antes de dizer pronto |
| Agentes segmentados | `_arquivo/saru-app/.claude/agents/{code-reviewer,evaluator,test-writer,repo-explorer,browser-tester}.md` | Já é a segmentação por área que Vitor quer, com modelo e ferramentas declarados por agente |
| Template de PR com gate de física | `_arquivo/saru-physics-py/.github/pull_request_template.md` | Fixture, unidade, nome de canal e banda de lap time. É a única coisa que trava claim físico |
| Template de PR de produto | `_arquivo/saru-app/.github/pull_request_template.md` | Proíbe apresentar demo como produto e exige fonte para claim público |
| Workflows reutilizáveis | `_arquivo/dot-github/workflows/reusable-{node,python-uv,mkdocs}-ci.yml` | Prontos e nunca usados. Um repositório novo passa a ter CI com cinco linhas |
| Perfil da organização | `_arquivo/dot-github/profile/README.md` | Já descreve GitHub Flow em três linhas. Só precisa da lista de repositórios atualizada |
| Regra anti-lixo de agente | `_arquivo/SARU/SGM.md:44-55` | Efêmero fica no chat, documento perene só com dono claro em `docs/`. Vale como regra, não como arquivo `SGM.md` |
| Guarda de origem de PR por workflow | `~/.claude/skills/projeto/referencias/LucasGSAntunes.md:87-98` | Regra de fluxo imposta pelo CI, não por combinado verbal. Adaptar de `develop` para o que o ruleset exigir |
| Makefile como interface única | `saru-poc-trackday/Makefile` e `~/.claude/skills/projeto/referencias/LucasGSAntunes.md:100-112` | Já é a prática do repositório ativo, com alvo autodocumentado |
| Dívida medida no README | `saru-poc-trackday/README.md:70-95` | Cada dívida vem com número, arquivo e motivo. É o padrão de honestidade que os arquivados não têm |

## 4. O que é lixo ou obsoleto

| Arquivo | Por quê |
|---|---|
| `_arquivo/SARU/AGENTS.md` | Cópia byte a byte de `_arquivo/SARU/CLAUDE.md`, que por sua vez é o `CLAUDE.md` global do operador de 2026-06-24, não um contrato de repositório |
| `_arquivo/SARU/opencode.json` | Configura OpenCode com DeepSeek e carrega regras de `~/.claude/rules/ecc/`, caminho que não existe mais |
| `_arquivo/SARU/implementation_plan.md` | Plano de sessão de junho de 2026 que pede aprovação para apagar arquivos já apagados |
| `_arquivo/SARU/.github/copilot-instructions.md` | Documenta comandos de `saru-desktop-app`, `lts-copatruck` e `lts-hase`, repositórios fora do escopo atual |
| `_arquivo/SARU/README.md:14-34` | Descreve a árvore `platform/`, `products/`, `partnerships/`, extinta em 2026-07-15 segundo `saru-app/docs/STANDARDS.md:35` |
| `_arquivo/SARU/SGM.md` | Aponta o estado global para `/home/vitor/Projects/SARU/SGM.md`. A pasta `/home/vitor/Projects` não existe |
| Referência a `sot-guard.sh` | `_arquivo/saru-app/.claude/settings.json:55` chama `$HOME/Projects/SARU/.claude/scripts/sot-guard.sh`, que não existe. O hook falha silenciosamente a cada Edit ou Write |
| `_arquivo/SARU/.agents/skills/docs-auditor/SKILL.md` e a cópia em `_arquivo/saru-physics-jl/.agents/skills/docs-auditor/SKILL.md` | Forçam escrita nos 3 documentos mestre em `/home/vitor/Projects/SARU/saru-knowledge-base/`, caminho inexistente |
| `_arquivo/saru-physics-py/.agents/` | Pasta vazia. O `CLAUDE.md:70-76` lista quatro skills que deveriam estar ali |
| `_arquivo/saru-KB/scripts/check-docs.sh` | Só dispara se existir um diretório `saru-KB` dentro da raiz git corrente. No repositório próprio a condição da linha 10 nunca é verdadeira |
| `_arquivo/saru-docs/docs/runbooks/mvp-board.md` | Depende de escopo OAuth `project` nunca concedido (linhas 7 a 20) e lista issues de julho de 2026 em repositórios arquivados |
| CODEOWNERS dos quatro repositórios | Apontam para `@viniciusvieira`, handle que não bate com `viniciusvieira00`, e não incluem Vitor em caminho nenhum |
| Tabela de modelos de `_arquivo/SARU/CLAUDE.md:50-56` | Nomeia Haiku 4.5, Sonnet 4.6 e Opus 4.8, que não existem |
| `_arquivo/saru-app/SPM.md` e `_arquivo/saru-physics-jl/SPM.md` | 129 KB e 36 KB de estado de sessão. Ninguém lê no início da sessão, que é para o que foram feitos |
| `_arquivo/saru-telemetry-gt7` como repositório governado | Sem `CLAUDE.md`, `AGENTS.md`, `SPM.md`, `.claude/` ou `CODEOWNERS`. É código com CI, não um repositório sob contrato |
| Gate de `develop` no CI | `_arquivo/saru-app/.github/workflows/ci.yml:8-10` e `_arquivo/saru-physics-py/.github/workflows/ci.yml:5-7` disparam em `develop`, branch que o GitHub Flow não tem |

## 5. Proposta de conjunto único

Três camadas, sem repetição entre elas. Regra que vale para todos os repositórios mora no
perfil `.github` da organização. Regra de engenharia mora no repositório de código. A
guarda-chuva só lista e aponta.

### 5.1 Repositório guarda-chuva (`SaruSysLab/saru`)

| Arquivo | Conteúdo |
|---|---|
| `CLAUDE.md` | Até 20 linhas. Lista de repositórios, uma frase cada, e ponteiro para o `CLAUDE.md` de cada um. Esboço na seção 5.5 |
| `AGENTS.md` | Symlink para `CLAUDE.md` |
| `README.md` | O que é a SARU, quem trabalha nela, por onde começar |
| `docs/decisions.md` | Decisão de organização, data, motivo, alternativa descartada. Recebe o que hoje está espalhado em `SGM.md` e nos ADRs cross-ecossistema |
| `.claude/rules/` | Só regra que vale em toda a organização e não cabe no `.github` |

Sem `docs/` de engenharia, sem `SGM.md`, sem `SPM.md`.

### 5.2 Cada repositório de código

| Arquivo | Conteúdo |
|---|---|
| `CLAUDE.md` | Até 80 linhas, no idioma do projeto. Propósito, stack, estrutura, comandos, regras de engenharia, política de mudança, o que significa pronto. Nunca repete o que está no `.github` da organização |
| `AGENTS.md` | Symlink para `CLAUDE.md`. Exceção: pasta de serviço cuja ferramenta injeta bloco próprio, como `saru-app/services/frontend/AGENTS.md` |
| `.claude/rules/` | Regra por caminho: `python.md`, `sql.md`, `web.md` |
| `.claude/skills/` | Procedimento que se repete no repositório. Herda `adr`, `spec-first`, `tests-as-gate` do `saru-app` |
| `.claude/agents/` | Agentes por área, com modelo e ferramentas no frontmatter |
| `.claude/hooks/` | `block-dangerous.sh` e `lint-changed.sh` como estão; `session-branch-guard.sh` sem a regra de `develop` |
| `.claude/settings.json` | Permissões e registro dos hooks. Sem caminho absoluto para fora do repositório |
| `docs/` | `decisions.md`, `adr/` com índice, `notas/`, `pesquisa/`, `html/`. Front-matter obrigatório |
| `.github/workflows/ci.yml` | Chama o workflow reutilizável da organização. Dispara em `push` para `main` e em `pull_request` |
| `.github/CODEOWNERS` | Dono por caminho, com pelo menos um revisor humano nos caminhos de física, contrato e segurança |

### 5.3 Perfil `.github` da organização

| Arquivo | Conteúdo |
|---|---|
| `profile/README.md` | Página pública da organização. Atualizar a lista de repositórios: `saru-poc-trackday` como linha principal e os demais como arquivados |
| `CONTRIBUTING.md` | Como contribuir: abrir issue, criar branch a partir de `main`, Conventional Commits, abrir PR, esperar CI e CODEOWNERS, apagar a branch. É o documento que falta hoje em toda a organização |
| `CODEOWNERS` | Modelo a copiar; o GitHub não herda CODEOWNERS do repositório da organização, cada repositório de código precisa do seu |
| `PULL_REQUEST_TEMPLATE.md` | Fusão do template de produto do `saru-app` com o gate de física do `saru-physics-py` |
| `ISSUE_TEMPLATE/bug.yml`, `tarefa.yml`, `fisica.yml` | Três formulários. O de física exige fixture, unidade e canal antes de aceitar claim |
| `SECURITY.md` | Como reportar falha sem abrir issue pública |
| `workflows/reusable-python-uv-ci.yml`, `reusable-node-ci.yml`, `reusable-mkdocs-ci.yml` | Já existem em `_arquivo/dot-github/workflows/`. Passar a ser chamados |
| `workflows/guard-pr.yml` | Falha o PR que não siga a regra de origem de branch, no modelo de `LucasGSAntunes.md:87-98` |

Rulesets de branch em `main`, por repositório:

1. Bloquear push direto e force push.
2. Exigir pull request com pelo menos uma aprovação.
3. Exigir revisão de CODEOWNERS nos caminhos de física, contrato e segurança.
4. Exigir o job de CI verde como status check obrigatório.
5. Apagar a branch no merge.

### 5.4 Como `AGENTS.md` e `CLAUDE.md` convivem

`CLAUDE.md` é o arquivo real e único. `AGENTS.md` é symlink para ele, como já acontece em
`_arquivo/saru-app`, `_arquivo/saru-physics-py` e `_arquivo/saru-physics-jl`. Isso resolve o
problema que a G1 tentou resolver com espelho manual e script de conferência
(`_arquivo/SARU/CLAUDE.md:76-77`): dois arquivos que sempre divergem.

A exceção é a pasta cuja ferramenta escreve um bloco próprio no `AGENTS.md`, como
`_arquivo/saru-app/services/frontend/AGENTS.md`. Nesse caso o `AGENTS.md` é arquivo real e o
`CLAUDE.md` da pasta aponta para ele.

### 5.5 Esboço do `CLAUDE.md` da guarda-chuva

```markdown
# SARU Systems Lab

Pasta guarda-chuva. Regra de engenharia mora em cada repositório, não aqui.
Processo da organização: `SaruSysLab/.github/CONTRIBUTING.md`.

## Repositórios

| Repositório | O que é | Contrato |
|---|---|---|
| `saru-poc-trackday` | Linha principal. Do arquivo do piloto ao insight num track day. | `saru-poc-trackday/CLAUDE.md` |
| `saru-app` | Arquivado. Plataforma web multi-serviço, fonte de peças a portar. | `_arquivo/saru-app/CLAUDE.md` |
| `saru-physics-py` | Arquivado. Física Python, solver QSS de tempo de volta. | `_arquivo/saru-physics-py/CLAUDE.md` |
| `saru-physics-jl` | Arquivado. Física Julia, 14 graus de liberdade. | `_arquivo/saru-physics-jl/CLAUDE.md` |
| `saru-telemetry-gt7` | Arquivado. Captura GT7 por UDP, em Go. | sem contrato |
| `saru-docs`, `saru-KB`, `saru-research` | Arquivados. Documentação e pesquisa de 2026. | leitura apenas |

## Regras desta pasta

Sessão de trabalho abre no repositório, nunca aqui. Clone em `_arquivo/` é só leitura.
Repositório com nome parecido é projeto diferente.
```

## 6. Perguntas para Vitor

1. Estratégia de merge no GitHub Flow: squash com um commit por PR, ou merge commit
   preservando o histórico da branch?
2. A guarda-chuva vira repositório no GitHub, ou continua pasta local com `CLAUDE.md` e sem
   git?
3. Idioma do código e das mensagens de commit: o `saru-poc-trackday` está inteiro em
   português e os arquivados estão em inglês. Qual dos dois vale para quem chega?
4. Documentação de produto e arquitetura: cada repositório com `docs/` próprio, ou volta um
   portal central no modelo do `saru-docs`?
5. `SPM.md` acaba, substituído por `docs/decisions.md` mais issues, ou o padrão de memória
   por repositório continua com limite de tamanho?
