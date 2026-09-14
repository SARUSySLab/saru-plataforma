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

## M2, 2026-09-14

R1 recebido; a medição do `.pds` do 992.1 vira `docs/pi-pds-medicao.md` na issue #25. As nove issues
da PoC agora vivem aqui (#25 a #33, mesma ordem). Três tarefas de medição, sem editar `src/`:

1. Inventário dos `.pds` do acervo (`Trabalho/Porsche_Cup/` e o que mais o índice
   `~/.cache/rclone/drive-index.tsv` listar): tabela com arquivo, tamanho, layout do dicionário
   (552 B com nome duplicado a +88 B, 304 B, ou outro), bytes por amostra e se `LeitorPiPds`
   abre hoje. É a tabela de medição da issue #25 e da #26.
2. Issue #26 (`.pid` entrega contagem crua): em três `.pid` do acervo, localizar no cabeçalho o
   fator e o offset de escala de cinco canais (velocidade, rpm, acelerador, pressão de freio, ax)
   e conferir contra o valor físico esperado de uma volta. Tabela por arquivo e canal.
3. Valores do GT3 Cup por OCR (decisão de 2026-09-14): inventário de `Trabalho/Porsche_Cup/`
   (Análise de Dados, Apostila Toolbox, REF38 26ET02.pds e demais), listando em qual arquivo e
   página aparece cada um de massa, distribuição de massa, CdA, rigidez de mola, relação de
   transmissão e raio de pneu. Só a lista; nenhum valor entra em `docs/` sem Vitor.
