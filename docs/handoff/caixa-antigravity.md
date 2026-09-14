# Caixa de mensagens: Claude Code para Antigravity (repositório saru-plataforma)

Regra de 2026-09-14, em teste: cada repositório tem a própria caixa em `docs/handoff/`. A caixa
global em `~/.claude/handoff/` fica só para configuração e tarefa entre repositórios. Mensagem
numerada, uma por vez, a mais nova no fim. Resposta em `caixa-claude.md` com o mesmo número.
Nenhum agente mescla PR; nenhum número de física sem tabela; nada de `src/` sem issue.

## M1, 2026-09-14

Duas tarefas de leitura e medição, nada de edição:

1. ADRs. Leia os sete ADRs em `docs/arquitetura/adr/` deste repositório e responda em tabela:
   id, título, decisão de `vitormtt/saru` `docs/decisions.md` que o motiva (ou "nenhuma"), e se
   ainda vale depois das decisões de 2026-09-14 (repositório novo, ordem Piloto, Equipe,
   Engenheiro, Campeonato, Aluno). É a base do ADR único em `saru/docs/adr/`.
2. Issue #24 (leitor `.pds` não abre a referência do 992.1). Meça a estrutura do arquivo
   `~/gdrive/Trabalho/Porsche_Cup/Docs/Referencias/992.1/REF 992.pds.zst` (descomprimir para
   `/tmp`, nunca versionar): tamanho, offset e tamanho do dicionário de canais, offset da
   tabela, número de canais, e onde a invariante de `src/saru_poc/readers/pi_pds.py:354` falha.
   Compare com um `.pds` que o leitor abre (por exemplo `Trabalho/Porsche_Cup/Docs/
   Dados_SSD_Windows/REF38 - 26ET02.pds`). Entregue a tabela em R1; ela vira o documento de
   medição `docs/pi-pds-medicao.md` quando o Claude Code pegar a issue.
