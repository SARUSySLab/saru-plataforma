# Padrão de organização GitHub para a SARU Systems Lab

Contexto: organização SaruSysLab, GitHub Flow já decidido (main protegida, branch por tarefa,
merge só por PR aprovado, sem develop), polyrepo com um repositório guarda-chuva mais
repositórios de código, agentes de IA segmentados por área (Claude Code, Antigravity, Codex),
Conventional Commits, documentação permanente no GitHub. Fundador Vitor Toledo, colaborador
Lucas Antunes, plano é crescer o time.

Os repositórios de código do projeto (ex.: saru-app) são privados. Isso muda o custo de
várias recomendações abaixo, porque o GitHub Free para organizações libera proteção de branch,
rulesets, code owners e secret scanning só em repositórios públicos [3][5][6].

## 1. Repositório .github da organização

Um repositório chamado `.github`, criado dentro da organização SaruSysLab, guarda arquivos
que os outros repositórios herdam quando não têm o arquivo próprio: CONTRIBUTING, SUPPORT,
CODE_OF_CONDUCT, modelo de issue e de pull request [1]. A herança organization-wide só
funciona se o repositório `.github` for público ou interno; para modelo de issue e de PR
especificamente, precisa ser público [1]. GitHub lançou esse mecanismo em fevereiro de 2019 [2].

Não herdam automaticamente: CODEOWNERS padrão, workflows reutilizáveis e FUNDING.yml. Esses
três precisam existir em cada repositório de código, ou ser referenciados a partir dele
(workflow reutilizável é chamado por `uses: SaruSysLab/repo/.github/workflows/arquivo.yml@ref`,
não herdado por presença de pasta) [29][30].

Como o repositório `.github` da SARU teria conteúdo institucional e não segredo de produto,
ele pode ser público sem expor código de telemetria ou simulação.

Passos:

1. Criar o repositório `SaruSysLab/.github`, visibilidade pública.
2. Adicionar `profile/README.md` com a descrição da organização, exibido na página
   github.com/SaruSysLab.
3. Adicionar `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` na raiz.
4. Adicionar `.github/ISSUE_TEMPLATE/bug.yml`, `feature.yml`, `pesquisa.yml`, `dado.yml`
   (ver seção 3) e `.github/ISSUE_TEMPLATE/config.yml` com `blank_issues_enabled: false`.
5. Adicionar `.github/PULL_REQUEST_TEMPLATE.md` com checklist curto: o que mudou, como testar,
   issue relacionada.
6. Não adicionar FUNDING.yml agora: a SARU não capta patrocínio individual por repositório.

Custo: zero. Repositório `.github` público não conta contra nenhum limite de plano.

## 2. Rulesets e branch protection para main

GitHub tem dois sistemas. Branch protection rules é o mais antigo, configurado em
Settings > Branches. Rulesets é o mais novo, em Settings > Rules > Rulesets, permite
combinar várias regras e aplicar a vários repositórios de uma vez [3]. Para GitHub Flow,
a regra central é exigir pull request antes do merge na branch main, com número mínimo de
aprovações, status checks obrigatórios, histórico linear e bloqueio de force push e de
exclusão de branch [4].

Detalhe de cada regra, segundo a documentação [4]:

- Exigir pull request antes do merge: bloqueia push direto na branch de destino.
- Aprovações exigidas: de zero a dez revisores, configurável.
- Status checks obrigatórios: modo strict exige que a branch esteja atualizada com main
  antes do merge; modo loose não exige.
- Histórico linear: impede push de merge commit, obrigando squash merge ou rebase merge.
- Bloqueio de force push: ativado por padrão em ruleset.
- Bloqueio de exclusão de branch: ativado por padrão em ruleset.
- Bypass: administradores do repositório, donos da organização, times específicos ou
  GitHub Apps podem ser listados como exceção à regra.

Limitação de plano, ponto central para a SARU: rulesets e branch protection ficam
disponíveis em repositórios privados de organização só a partir do plano GitHub Team
(rulesets são descritos como recurso "para clientes em GitHub Team e GitHub Enterprise") [3].
Em repositório privado de uma organização no plano Free, não há como configurar essas regras
pela interface [3][5][6]. Em repositório público, GitHub Free já libera proteção de branch,
incluindo restrição de quem pode dar push [5].

GitHub Team custa 4 dólares por usuário por mês na cobrança inicial [6]. Com dois
desenvolvedores (Vitor e Lucas), o custo mensal fica em 8 dólares; cada novo colaborador
soma 4 dólares por mês.

Recomendação para a SARU:

1. Se o repositório de código puder ser público sem expor segredo comercial (ex.: SDK de
   parser, ferramentas internas sem dado de pista real), manter público e usar ruleset no
   plano Free.
2. Se o repositório precisa ser privado (ex.: saru-app com dado de telemetria de cliente),
   assinar GitHub Team antes de abrir a organização para mais colaboradores. Sem isso, um
   push direto na main de um repositório privado não é bloqueado por ferramenta nenhuma,
   só por acordo verbal.
3. Configurar o ruleset assim que o plano permitir: target branch `main`, exigir PR,
   1 aprovação (2 quando o time passar de 3 pessoas), status check da suíte de teste do
   repositório, histórico linear, bloqueio de force push e de delete.
4. Bypass list: só a conta do fundador, para emergência, nunca um time inteiro.

Esqueleto do comando via `gh` (a criação real exige o JSON completo com `conditions.ref_name`
apontando para `main` e a lista de `rules`; este trecho só mostra a chamada, não cria a proteção):

```bash
gh api --method POST /repos/SaruSysLab/saru-app/rulesets \
  -f name="main-protection" -f target="branch" \
  -f enforcement="active"
```

O corpo completo da regra é mais fácil de montar pela interface web em Settings > Rules >
Rulesets > New ruleset, pelo volume de campos aninhados.

## 3. Issues, labels, milestones e GitHub Projects

Issues, labels, milestones e Projects são gratuitos em qualquer plano, inclusive Free [11].

Convenção de rótulo recomendada para time de 2 a 6 pessoas, por dimensão, sem sobreposição:

- Tipo: `tipo:bug`, `tipo:feature`, `tipo:pesquisa`, `tipo:dado`, `tipo:doc`.
- Prioridade: `prio:alta`, `prio:media`, `prio:baixa`.
- Estado de triagem: `triagem` (aplicado automaticamente via issue form, removido quando
  alguém assume a issue).

Ligação entre branch e issue: `gh issue develop <numero> --checkout` cria a branch a partir
da issue e já a associa a ela no painel de "linked branches" [7]. Alternativa manual: incluir
`Closes #12` ou `Fixes #12` na descrição do pull request; GitHub fecha a issue 12
automaticamente quando o PR é mesclado na branch padrão [8][9]. Palavras aceitas: close,
closes, closed, fix, fixes, fixed, resolve, resolves, resolved [9].

Modelo de issue por tipo, usando issue forms (YAML, não markdown simples), porque forms
obrigam preenchimento de campo antes de abrir a issue [10]. Campos obrigatórios do arquivo:
`name`, `description`, `body`; opcionais: `title`, `labels`, `assignees`, `projects` [10].

Esqueleto de `.github/ISSUE_TEMPLATE/bug.yml`:

```yaml
name: Bug
description: Reportar comportamento incorreto
title: "[bug] "
labels: ["tipo:bug", "triagem"]
body:
  - type: textarea
    id: comportamento
    attributes:
      label: O que aconteceu
    validations:
      required: true
  - type: textarea
    id: esperado
    attributes:
      label: O que deveria acontecer
    validations:
      required: true
  - type: input
    id: versao
    attributes:
      label: Versão ou commit
    validations:
      required: true
```

Repetir a estrutura para `feature.yml` (campo "problema que resolve" e "critério de aceite"),
`pesquisa.yml` (campo "pergunta de pesquisa" e "fonte consultada") e `dado.yml` (campo
"origem do dado" e "formato").

Milestones: um por marco de produto (ex.: "PoC trackday", "V1 dashboard"), não por sprint
de tempo fixo, dado o tamanho do time. GitHub Projects (o board novo, item por issue ou PR):
um projeto por repositório de código é suficiente para 2 a 6 pessoas; projeto único da
organização só se o trabalho cruzar repositórios com frequência.

## 4. ADR (Architecture Decision Records)

O formato original é de Michael Nygard, publicado em 15 de novembro de 2011: cada decisão em
um arquivo curto com as seções Title, Status, Context, Decision e Consequences [12]. MADR
(Markdown Architectural Decision Records) é uma variação mais estruturada, com campos como
alternativas consideradas e critério de decisão, e existe em quatro tamanhos de template,
do completo ao mínimo [13][14].

Para um time de 2 a 6 pessoas, o template mínimo de Nygard basta. MADR compensa quando a
decisão envolve comparação explícita entre opções técnicas (ex.: escolher banco de dados,
escolher biblioteca de parsing).

Estado de cada ADR: proposed, accepted, deprecated ou superseded [12]. Um ADR marcado como
superseded aponta para o número do ADR que o substitui, nunca é apagado.

Local no polyrepo: decisão que vale para mais de um repositório (linguagem padrão, política
de branch, escolha de banco de dados da empresa) vai em `docs/adr/` no repositório
guarda-chuva. Decisão interna de um repositório de código (estrutura de módulo, biblioteca
usada só ali) vai em `docs/adr/` daquele repositório. Cada pasta `docs/adr/` mantém um
`README.md` como índice, numeração sequencial independente por repositório
(`0001-titulo.md`, `0002-titulo.md`).

Esqueleto de ADR, formato Nygard:

```markdown
# 0001. Título da decisão

Status: accepted

## Contexto

Forças em jogo: técnica, prazo, custo.

## Decisão

Frase afirmativa, no que foi decidido.

## Consequências

Positivas, negativas e neutras, sem filtro.
```

O projeto já tem a skill `adr` em `_arquivo/saru-app/.claude/skills`, que cria e supersede
ADR mantendo o índice sincronizado. Ela cobre o repositório de código; falta o equivalente
para o repositório guarda-chuva quando ele existir.

## 5. AGENTS.md, CLAUDE.md e convivência entre agentes

AGENTS.md é um formato aberto, markdown puro, sem campo obrigatório, mantido pela Agentic AI
Foundation sob a Linux Foundation; em dezembro de 2025 já tinha mais de 60 mil projetos
usando e mais de vinte ferramentas de IA com suporte [15][16]. Serve como o README voltado
a agente: comando de build e teste, convenção de código, regra de commit e PR [15].

Claude Code não lê AGENTS.md diretamente. A documentação oficial recomenda um CLAUDE.md que
importa o AGENTS.md com a sintaxe `@AGENTS.md` na primeira linha, seguido de instrução
específica de Claude abaixo; alternativa é symlink (`ln -s AGENTS.md CLAUDE.md`), que só
funciona em Linux e macOS sem privilégio extra, porque no Windows criar symlink exige
administrador [17]. A rules skill-level da SARU, em `.claude/rules/`, continua específica de
Claude Code e não precisa duplicar conteúdo do AGENTS.md.

Antigravity, segundo o codelab oficial do Google, usa uma pasta própria `.agents/` com
`agents.md` dentro dela (não na raiz) e uma subpasta `.agents/skills/` com um arquivo markdown
por habilidade [18]. O documento oficial não menciona compatibilidade com o padrão aberto
agents.md; é descrito como reconhecido nativamente só pelo Antigravity [18]. Blogs de
terceiro (não confirmados aqui como fonte oficial) descrevem também um AGENTS.md na raiz do
projeto, com prioridade AGENTS.md > GEMINI.md > padrão embutido; essa camada de raiz não
apareceu no codelab oficial consultado, então fica como não confirmado.

Recomendação de estrutura, sem duplicar conteúdo entre ferramentas:

1. `AGENTS.md` na raiz de cada repositório: conteúdo comum a qualquer agente. Comando de
   build e teste, estrutura de pasta, convenção de commit, o que nunca fazer (ex.: não
   commitar dado de telemetria de cliente).
2. `CLAUDE.md` na raiz: uma linha `@AGENTS.md`, seguida só do que é específico de Claude Code
   (uso de skill, hook, hierarquia de subagente).
3. `.agents/agents.md` do Antigravity: mesmo conteúdo do AGENTS.md, ou symlink apontando para
   ele, já que o Antigravity não lê o arquivo da raiz segundo a documentação oficial [18].
4. Codex e Cursor leem AGENTS.md e `.cursor/rules/` respectivamente; Codex já segue o padrão
   agents.md nativamente, sem arquivo extra.

Isso evita manter a mesma regra em quatro lugares: o conteúdo comum mora uma vez em
AGENTS.md, e cada ferramenta aponta para ele.

## 6. Segredos: prevenção e resposta

Gitleaks é a ferramenta de varredura de segredo mais citada para uso como pre-commit hook e
como passo de CI [20][21]. Configuração como pre-commit, arquivo `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.30.1
    hooks:
      - id: gitleaks
```

O hook local pode ser contornado com `git commit --no-verify` (proibido pela regra 6 do
CLAUDE.md global da SARU); por isso o mesmo gitleaks deve rodar de novo em GitHub Actions a
cada push e pull request, como camada que não depende de disciplina local.

GitHub Secret Scanning é o recurso nativo equivalente. Em repositório público, secret
scanning roda de graça, incluindo alguns tipos de segredo com push protection ativado por
padrão [22][23]. Em repositório privado de organização, secret scanning completo com push
protection exige GitHub Secret Protection, add-on pago sobre GitHub Team ou Enterprise
Cloud [23]. Como os repositórios de código da SARU são privados, gitleaks via pre-commit e
via Actions é a camada que funciona sem custo adicional, independente do plano.

Arquivo `.env.example` na raiz de cada repositório, listando toda variável de ambiente sem
valor real, com comentário do que cada uma configura. `.env` real nunca commitado, sempre em
`.gitignore`. Segredo de produção mora em GitHub Secrets (Settings > Secrets and variables >
Actions), nunca em arquivo de configuração do repositório.

Se um segredo já foi commitado:

1. Rotacionar o segredo primeiro (trocar a chave, revogar o token). A partir do momento do
   commit, o segredo é considerado comprometido, mesmo que o repositório seja privado [24].
2. Remover o segredo do histórico com `git filter-repo`, ferramenta que a documentação do
   Git recomenda no lugar do antigo `filter-branch` [24].
3. Avisar o time: todo mundo precisa clonar de novo depois da reescrita de histórico, porque
   force-push não limpa cópia local nem cache de terceiro [24].

## 7. Releases e versionamento

Semantic Versioning (semver) numera cada release como major.minor.patch: major quebra
compatibilidade, minor adiciona funcionalidade compatível, patch corrige bug [26]. Para um
produto interno em fase de prova de conceito, como o saru-app hoje, a prática comum é manter
major em zero (`0.x.y`) enquanto a interface ainda muda sem aviso, e só subir para `1.0.0`
quando o primeiro time externo passar a depender da API ou do formato de dado sem
supervisão direta.

Release-please automatiza o ciclo inteiro a partir de Conventional Commits: mantém um pull
request de release sempre atualizado com o changelog, e ao mesclar esse PR ele atualiza o
`CHANGELOG.md`, sobe a versão, cria a tag e publica o GitHub Release [25]. Commit `fix:` sobe
patch, `feat:` sobe minor, `!` no tipo ou `BREAKING CHANGE` no corpo sobe major [25]. Isso
elimina o passo manual de decidir o número da próxima versão.

GitHub Releases embrulha uma tag git com changelog e anexo de arquivo; o próprio GitHub
gera notas de release automáticas a partir do título dos PRs mesclados desde a tag
anterior [27], mas release-please substitui essa geração automática por uma baseada no tipo
do commit, mais previsível.

Passos:

1. Adicionar `.github/workflows/release-please.yml` chamando a action
   `googleapis/release-please-action`, tipo de release `simple`, arquivo de versão
   `package.json` ou equivalente do stack do repositório.
2. Commits seguem Conventional Commits, já decidido pela SARU.
3. Merge do PR de release automático publica tag e GitHub Release; nenhum passo manual de
   changelog.

Custo: zero, release-please e GitHub Releases não dependem de plano pago.

## 8. Onboarding

Ordem de leitura recomendada para quem entra no time, do mais geral para o mais específico:

1. `SaruSysLab/.github/profile/README.md`: o que é a SARU, o que a organização faz.
2. `SaruSysLab/.github/CONTRIBUTING.md`: como abrir issue, como abrir PR, convenção de commit.
3. `README.md` do repositório específico: o que o repositório faz, como rodar localmente.
4. `AGENTS.md` e `CLAUDE.md` do repositório: convenção de código e de agente.
5. `docs/adr/README.md`: por que o sistema é como é, decisão por decisão.

Guias de onboarding de empresas de ferramenta de desenvolvedor convergem em dois pontos:
meta explícita por período (frequentemente descrita como plano de 30, 60 e 90 dias) no lugar
de "se ambientar" sem prazo, e uma primeira tarefa pequena e concreta já na primeira semana,
mesmo que trivial, para o novo colaborador praticar o fluxo de branch e PR do zero [32][33].

Checklist de primeiro PR para a SARU:

1. Clonar o repositório, rodar o comando de setup do README.
2. Ler o `AGENTS.md` do repositório.
3. Escolher uma issue com rótulo `tipo:doc` ou de escopo pequeno.
4. `gh issue develop <numero> --checkout` para criar a branch ligada à issue.
5. Commit em Conventional Commits, PR com `Closes #<numero>`.
6. Esperar checagem automática e revisão antes do merge, nunca push direto em main.

## 9. Uso de IA declarado no projeto

Exemplo público de política de divulgação: o repositório `github/spec-kit`, do próprio
GitHub, exige em `CONTRIBUTING.md` que qualquer assistência de IA usada numa contribuição seja
declarada no PR ou na issue, citando a ferramenta e o alcance da ajuda, com frases modelo como
"This PR was written primarily by GitHub Copilot" [34]. A justificativa dada é que a omissão
dificulta calibrar o nível de revisão necessário e é considerada desrespeitosa com quem revisa
o código [34]. O projeto ghostty (ghostty-org/ghostty) tem prática equivalente, discutida
publicamente em pull request de política do repositório [35]. Como abordagem alternativa e
mais ampla que uma linha de CONTRIBUTING.md, a GitLab publica uma página inteira dedicada,
o AI Transparency Center, descrevendo princípios de uso de IA no produto e no processo [36].

Recomendação para a SARU, dado que Claude Code, Antigravity e Codex já geram parte do
código: adicionar ao `CONTRIBUTING.md` do repositório `.github` uma seção "Uso de IA", com
três regras. Toda contribuição gerada majoritariamente por agente de IA leva a marca do
agente na descrição do PR (ex.: "Gerado por Claude Code, revisado por Vitor Toledo"). Revisão
humana antes do merge é sempre obrigatória, sem exceção para PR de agente, reforçando a regra
1 do CLAUDE.md global ("Vitor aprova, o agente executa"). Nenhum agente tem permissão de
aprovar ou mesclar PR sozinho; isso já é garantido pela regra de PR obrigatório na main,
seção 2 deste relatório.

## Fontes consultadas

Todas acessadas em 12 de setembro de 2026.

1. https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file
   Confirma quais arquivos (CONTRIBUTING, SUPPORT, CODE_OF_CONDUCT, templates de issue e PR)
   são herdados do repositório `.github` e que o repositório precisa ser público ou interno.
2. https://github.blog/changelog/2019-02-21-organization-wide-community-health-files/
   Anúncio oficial do GitHub sobre o lançamento dos arquivos de saúde de comunidade
   organization-wide, em fevereiro de 2019.
3. https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
   Confirma que rulesets, no nível de organização, são recurso de clientes GitHub Team e
   GitHub Enterprise.
4. https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
   Lista as regras disponíveis em ruleset: exigir PR, número de aprovações, status check
   strict ou loose, histórico linear, bloqueio de force push e de exclusão de branch, e
   bypass.
5. https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
   Confirma que restrição de push em branch protegida funciona em repositório público de
   organização Free, e em todo repositório de organização Team ou Enterprise Cloud.
6. https://github.com/pricing
   Mostra que regra de repositório, code owners e secret scanning completo aparecem restritos
   a repositório público no plano Free, e confirma o preço de 4 dólares por usuário por mês
   do plano Team na cobrança inicial.
7. https://cli.github.com/manual/gh_issue_develop
   Documentação oficial do comando `gh issue develop`, que cria e lista branch vinculada a
   uma issue.
8. https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue
   Explica como vincular PR a issue e fechamento automático ao mesclar na branch padrão.
9. https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/using-keywords-in-issues-and-pull-requests
   Lista as palavras-chave aceitas (close, closes, fix, fixes, resolve, resolves, e variações)
   para fechar issue a partir de PR ou commit.
10. https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms
    Sintaxe do YAML de issue forms: campos obrigatórios e tipos de elemento de formulário
    (markdown, textarea, input, dropdown, checkboxes).
11. https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/creating-and-editing-milestones-for-issues-and-pull-requests
    Confirma que milestone é recurso disponível em qualquer plano, incluindo Free.
12. https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
    Post original de Michael Nygard, 15 de novembro de 2011, com o template de ADR (Title,
    Status, Context, Decision, Consequences).
13. https://adr.github.io/madr/
    Descrição do formato MADR e onde colocar o arquivo (`docs/decisions`).
14. https://github.com/adr/madr
    Repositório oficial do MADR, com os quatro templates (completo, mínimo, bare, bare
    mínimo).
15. https://agents.md/
    Especificação do formato AGENTS.md, sem campo obrigatório, seções recomendadas.
16. https://github.com/agentsmd/agents.md
    Repositório do padrão, confirma a governança pela Agentic AI Foundation sob a Linux
    Foundation e mais de 60 mil projetos adotantes em dezembro de 2025.
17. https://code.claude.com/docs/en/memory
    Documentação oficial de Claude Code: confirma que Claude Code lê CLAUDE.md, não
    AGENTS.md, e recomenda `@AGENTS.md` como import ou symlink para evitar duplicação.
18. https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity
    Codelab oficial do Google mostrando `.agents/agents.md` e `.agents/skills/` como
    convenção nativa do Antigravity, sem menção a compatibilidade com o padrão agents.md.
19. https://antigravity.google/docs/cli/commands/agents/
    Documentação oficial do comando `/agents` do Antigravity, mostrando `agent.md` por
    subagente em `.agents/agents/{nome}/agent.md`.
20. https://gitleaks.org/
    Página oficial do Gitleaks, ferramenta de varredura de segredo.
21. https://github.com/gitleaks/gitleaks
    Repositório oficial do Gitleaks, com instrução de uso como pre-commit hook e GitHub
    Action.
22. https://docs.github.com/en/code-security/concepts/secret-security/push-protection
    Explica o funcionamento de push protection do GitHub e sua relação com secret scanning.
23. https://docs.github.com/en/get-started/learning-about-github/about-github-advanced-security
    Confirma que secret scanning completo com push protection em repositório privado de
    organização exige GitHub Secret Protection sobre plano Team ou Enterprise Cloud.
24. https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
    Procedimento oficial do GitHub para remover segredo do histórico do git, com recomendação
    de rotacionar o segredo antes de reescrever o histórico.
25. https://github.com/googleapis/release-please
    Repositório oficial do release-please, explica geração de changelog e versão a partir de
    Conventional Commits.
26. https://semver.org
    Especificação oficial de Semantic Versioning.
27. https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes
    Explica a geração automática de notas de release do GitHub a partir de PRs mesclados.
28. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
    Sintaxe e localização do arquivo CODEOWNERS.
29. https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations
    Explica como um workflow reutilizável é chamado por outro repositório via `uses:`, e que
    não é herdado automaticamente pela presença no repositório `.github`.
30. https://docs.github.com/en/actions/creating-actions/sharing-actions-and-workflows-with-your-organization
    Explica como restringir workflow reutilizável ao uso interno da organização.
31. https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/displaying-a-sponsor-button-in-your-repository
    Sintaxe do FUNDING.yml e onde ele precisa estar (branch padrão, pasta `.github`).
32. https://sourcegraph.com/blog/developer-onboarding
    Guia de onboarding de engenharia com estrutura de metas por período e ênfase em primeira
    tarefa pequena na primeira semana.
33. https://www.cortex.io/post/developer-onboarding-guide
    Segundo guia de onboarding de engenharia, convergente com o anterior sobre primeira tarefa
    pequena e pareamento com pessoa mais sênior.
34. https://github.com/github/spec-kit/blob/main/CONTRIBUTING.md
    Exemplo público de política de divulgação de uso de IA em contribuição, mantido pelo
    próprio GitHub.
35. https://github.com/ghostty-org/ghostty/pull/8289/files
    Segundo exemplo público de discussão e adoção de política de divulgação de uso de
    ferramenta de IA em projeto open source.
36. https://about.gitlab.com/blog/introducing-the-gitlab-ai-transparency-center/
    Exemplo de página dedicada de transparência de uso de IA, abordagem mais ampla que uma
    seção de CONTRIBUTING.md.

## Não confirmado

- Se o Antigravity, além de `.agents/agents.md`, também lê um `AGENTS.md` na raiz do
  workspace com prioridade sobre `GEMINI.md`. O codelab oficial do Google não menciona essa
  camada; só blogs de terceiro descrevem esse comportamento.
- Se existe alguma configuração parcial de proteção de branch disponível em repositório
  privado de organização no plano Free, além do que a documentação oficial descreve. A
  documentação e o comparativo de preço indicam que não, mas não há uma frase única e
  explícita de que "nenhuma proteção" funciona nesse caso.
- Preço exato do plano GitHub Team após os primeiros 12 meses de assinatura; a página de
  preços mostra o valor promocional de 4 dólares por usuário por mês para o primeiro ano, sem
  detalhar o valor de renovação no texto capturado.
