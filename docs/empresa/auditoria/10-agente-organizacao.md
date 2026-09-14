# Relatório: perfil `.github` da organização SaruSysLab

Data: 2026-09-13. Escopo: repositório `SaruSysLab/.github`, branch `docs/processo`, clone
local em `/home/vitor/Desktop/Motorsport/SARU/org-github`. Pull request aberto como
rascunho, não mesclado.

Pull request: https://github.com/SARUSySLab/.github/pull/4

## Arquivos criados ou atualizados

- `profile/README.md`: descrição da SARU, lista de repositórios ativos
  (`saru-poc-trackday` como família Piloto, `dados_telemetria` como acervo), processo em
  três linhas e ponteiro para o `CONTRIBUTING.md`.
- `CONTRIBUTING.md`: passo a passo de contribuição, Definition of Ready de 8 itens e
  Definition of Done de 7 itens copiados do backlog da empresa, seção de uso de IA e
  regra de segredo.
- `SECURITY.md`: como reportar falha de segurança sem abrir issue pública.
- `CODEOWNERS`: dono padrão `@vitormtt`, com comentário de que cada repositório
  sobrescreve.
- `PULL_REQUEST_TEMPLATE.md`: fusão do template de produto do `saru-app` com o gate de
  física do `saru-physics-py`, mais checklist do DoD e linha de uso de IA.
- `ISSUE_TEMPLATE/bug.yml`: formulário de bug com dropdown de prefixo de família.
- `ISSUE_TEMPLATE/tarefa.yml`: modelo de requisito completo, com história, critérios em
  checklist, restrições, notas técnicas e rastreabilidade (milestone, épico, depende de,
  bloqueia, cabe em uma semana).
- `ISSUE_TEMPLATE/pesquisa.yml`: formulário de pesquisa com pergunta e fonte consultada.
- `ISSUE_TEMPLATE/dado.yml`: formulário de dado novo no acervo, com checagem de
  privacidade.
- `ISSUE_TEMPLATE/config.yml`: `blank_issues_enabled: false`.
- `workflows/guard-pr.yml`: workflow reutilizável que falha quando um commit em `main`
  não está associado a um pull request mesclado; comentário no topo explica que o plano
  GitHub Free não permite bloquear o push em si.

## O que ficou definido por Vitor

- Contato de segurança em `SECURITY.md`: endereço `vitormttoledo@gmail.com` aprovado e registrado em `docs/decisions.md:24`, publicado no arquivo.

## Validação dos arquivos YAML

Comando usado em cada arquivo:
`python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <arquivo>`

| Arquivo | Resultado |
|---|---|
| `ISSUE_TEMPLATE/bug.yml` | OK |
| `ISSUE_TEMPLATE/tarefa.yml` | OK |
| `ISSUE_TEMPLATE/pesquisa.yml` | OK |
| `ISSUE_TEMPLATE/dado.yml` | OK |
| `ISSUE_TEMPLATE/config.yml` | OK |
| `workflows/guard-pr.yml` | OK |

O script Python embutido em `workflows/guard-pr.yml` foi extraído e testado à parte com
`python3 -m py_compile` (sintaxe válida) e executado duas vezes com um `pulls.json`
simulado: com pull request mesclado associado ao commit, o script imprime a confirmação
e sai com código 0; sem pull request mesclado, imprime o erro e sai com código 1.

## Commits na branch `docs/processo`

Um commit por entrega, todos depois de `a78fec6` (bootstrap):

1. `docs: atualiza perfil da organizacao com repos ativos`
2. `docs: adiciona guia de contribuicao com DoR e DoD`
3. `docs: adiciona politica de seguranca`
4. `docs: adiciona CODEOWNERS padrao da organizacao`
5. `docs: funde templates de PR arquivados com gate de fisica`
6. `docs: adiciona formularios de issue com prefixo de familia`
7. `chore: adiciona guarda de push direto em main`

## Como revisar

1. Ler `profile/README.md` e `CONTRIBUTING.md` primeiro.
2. Abrir uma issue de teste com `tarefa.yml` para conferir os campos do formulário.
3. Ler o comentário no topo de `workflows/guard-pr.yml` antes do código.
4. O pull request está como rascunho; a decisão de mesclar é de Vitor.
