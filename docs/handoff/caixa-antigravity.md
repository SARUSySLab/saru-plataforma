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

## M3, 2026-09-14

Sobre `docs/handoff/direcao-rascunho-antigravity.md`: Vitor decidiu que as 17 perguntas de
`docs/empresa/negocio/direcao-2026-09-14.md` são respondidas por ele, não por agente. O rascunho
não entra em `docs/empresa/` nem serve de fonte para requisito. Os números dele (60 dias, 10 s,
custódia pela vigência do plano, Aluno fora de 2026) não foram medidos nem ditos por Vitor.
O que aproveitar: o item 14, referências externas por família, vira pauta de leitura para Vitor.
Regra a partir de agora: resposta de pergunta dirigida a Vitor fica em branco; agente entrega
dado, medição e lista de fontes. M2 continua valendo, na ordem 1, 2, 3.

## M4, 2026-09-14

Documentação antes do código. Vitor aprovou cinco tarefas de preparação; nenhuma escreve
requisito ou arquitetura nova, porque a decisão de 2026-09-14 reserva isso para depois das 17
respostas de `docs/empresa/negocio/direcao-2026-09-14.md`. Cada entrega vai em R4 como
tabela; nada entra em `docs/` sem passar pelo Claude e por Vitor. Ordem: 1, 2, 5 agora;
3 e 4 quando Vitor responder as perguntas. Estimativas por tarefa em minutos de agente.

### 1. Auditoria de `docs/requisitos/` e `docs/empresa/requisitos/` (60 min)

Molde: `~/.claude/skills/requisitos/SKILL.md` (problema, objetivos, catálogos RF/RNF/RN,
backlog, casos de uso, critérios de aceitação, rastreabilidade, validação). Para cada um dos
13 arquivos (7 da Piloto em `docs/requisitos/`, 6 da empresa em `docs/empresa/requisitos/`):

| arquivo | seção do molde que falta | id sem dono (citado e não definido) | contradição com outro arquivo ou com `decisions.md` | caminho de código citado que não existe neste repositório |

Contradição inclui: ordem das famílias antiga (Campeonato em segundo), repositório `saru`
como destino, PoC como repositório da Piloto, "uma semana de documentação". Cada linha cita
o arquivo e a linha. Sem reescrever nada.

### 2. Matriz de rastreabilidade conferida (45 min)

Fonte: `docs/requisitos/05-rastreabilidade.md` e `docs/empresa/requisitos/05-rastreabilidade.md`.
Para cada requisito da matriz: existe? o caminho de código existe em `src/`? o teste citado
existe em `tests/`? alguma issue (#25 a #33) o cita? algum ADR de `docs/arquitetura/adr/` o
cita? Tabela: id, caminho citado, existe (sim/não), caminho real se mudou, issues, ADRs.
Já sabido: `docs/fisica/parameters_gt3_cup.py` não existe aqui; achar onde o código foi parar
(PR #6 `pil/fisica-parametros-cup` ou PoC congelada).

### 3. ADR único (90 min, depois das respostas)

Reescrever os sete ADRs de `docs/arquitetura/adr/` no molde de
`~/.claude/skills/arquitetura/SKILL.md`, um arquivo por ADR em `docs/arquitetura/adr/`,
mantendo número e título. Campos novos obrigatórios: decisão de `docs/empresa/decisions.md`
que o motiva (data e texto) ou "sem decisão registrada"; requisito(s) de origem; famílias a
que se aplica. Sua tabela do R1 é o ponto de partida; o ADR-006 já tem decisão de
2026-09-13. Sem criar ADR novo e sem mudar decisão. Entregar como PR em rascunho na branch
`emp/adr-unico`, nunca em `main`.

### 4. Glossário do domínio (60 min, depois das respostas)

Arquivo proposto: `docs/empresa/glossario.md`. Uma tabela: termo em português, definição em
uma frase para leigo, termo em inglês quando consagrado (slip angle, downforce, understeer,
oversteer, outing, beacon, apex), onde aparece no código (`src/saru_poc/`, um caminho) e em
qual família importa. Fonte: `seeds/aliases.yaml`, `migrations/*.sql`, `docs/requisitos/`,
`docs/empresa/fisica/`. Mínimo 60 termos. Decisão de 2026-09-14: português em tudo, termo
técnico consagrado fica em inglês.

### 5. Inventário do acervo de telemetria (120 min, roda em segundo plano)

Fonte: `~/.cache/rclone/drive-index.tsv`, nunca `find` no mount. Extensões: xrk drk rrk xrz
gpk bmsbin pds pwb pid ld ldx i2wkb vbo mf4 csv de simulador (skill `saru-telemetria`).
Tabela por arquivo: caminho, tamanho, hash md5 (via `rclone md5sum` ou `rclone lsjson --hash`),
logger, extensão, pista, carro, data e sessão quando o nome ou a pasta diz, duplicata de
(mesmo hash). Entregar como TSV em `docs/handoff/agy/inventario-telemetria-2026-09-14.tsv`
mais um resumo em R4: arquivos únicos por formato, MB por formato, quantas duplicatas.
É a base das tabelas de medição de toda issue de leitor (E-RN-02) e substitui o item 1 do M2.

M2 (itens 2 e 3) e M3 continuam valendo.
