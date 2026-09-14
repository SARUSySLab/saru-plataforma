# Backlog da empresa

Rascunho 1, 2026-09-12. Aqui mora a ordem em que as famílias entram, o que é o mínimo de
cada uma e as regras de entrada e saída de trabalho. Histórias detalhadas ficam no backlog
de cada família. Fontes F1 a F10 em `01-problema-e-objetivos.md`.

## Épicos

| Id | Épico | Objetivo | O que fecha o épico |
|---|---|---|---|
| E-EP-00 | Processo e documentação da empresa | OBJ-01, OBJ-02 | Fases 1 e 2 do plano feitas: perfil `.github`, repositório da empresa, estes seis arquivos aprovados, decisões registradas. Uma semana de documentação e modelagem antes de qualquer código |
| E-EP-01 | Núcleo compartilhado | OBJ-02, OBJ-03 | E-RF-01 a E-RF-08 com os critérios E-CT verdes no acervo inteiro |
| E-EP-02 | Família Piloto | OBJ-04 | `PIL` com requisitos, modelo e MVP validado por um piloto real |
| E-EP-03 | Família Campeonato | OBJ-05, OBJ-06 | `CAM` com comparativo do dia e pit wall local-first num evento real |
| E-EP-04 | Família Engenheiro | OBJ-02 | `ENG` com o que o `saru-app` já tinha de análise e simulação, portado e documentado |
| E-EP-05 | Família Equipe | OBJ-06 | `EQP` com operação do evento, setup e histórico |
| E-EP-06 | Família Aluno | OBJ-04 | `ALU` com trilha e pontuação sobre o dado do próprio aluno |
| E-EP-07 | Hardware próprio | OBJ-05 | Só após E-EP-01 a E-EP-03 e conversa com a DashAuto (F10) |

## Ordem das famílias

Aprovada por Vitor em 2026-09-12. Critério: o que já existe, o que gera receita
primeiro (F2: consultoria antes de SaaS) e o que você pediu como prioridade (presencial).

| Ordem | Família | Por quê agora | Mínimo viável (uma frase) |
|---|---|---|---|
| 1 | Piloto | A PoC já cobre a maior parte; foco decidido em julho (P3); régua do Catalyst 2 pronta | O piloto sobe o cartão do logger e recebe, em linguagem dele, onde perdeu tempo e o que treinar |
| 2 | Campeonato | Apoio presencial é a sua prioridade; pesquisa do pit wall recém-feita; PoC já tem cronometragem e ao vivo | O organizador vê o comparativo do dia e a torre de tempos do evento sem internet no box |
| 3 | Engenheiro | É a ferramenta da consultoria, que o documento mestre coloca como primeira receita; muito já existe no `saru-app` | O engenheiro compara voltas de loggers diferentes no mesmo gráfico e registra a decisão de setup |
| 4 | Equipe | Depende do Engenheiro (setup, histórico) e do Campeonato (operação do evento) | O chefe de equipe vê carro, piloto e setup por etapa, com histórico |
| 5 | Aluno | Depende do Piloto (é o mesmo dado, com trilha por cima) e da definição com o Hase | O aluno recebe uma trilha de exercícios sobre a própria volta e uma pontuação |
| depois | Hardware | Pré-condição declarada por você: consolidação e DashAuto | Um logger da SARU que grava no formato do núcleo |

## Regras de trabalho

Sprint de uma semana. Issue no modelo de requisito (história, critérios, restrições,
rastreabilidade), com prefixo da família no título e no rótulo. Milestone por marco, não
por sprint. Um Projects por repositório.

Antes de codar qualquer família: uma semana só de documentação e modelagem (E-RN-06). O
material da disciplina de requisitos é a base; a transcrição dos áudios da aula com Whisper
fica com a sessão da UnB (handoff de 2026-09-12).

## Definition of Ready (entra em desenvolvimento se)

Na ordem em que se confere. Base: INVEST (Agile Alliance) e "cabe em um sprint" (Scrum
Guide 2020). Revisado por Vitor em 2026-09-12.

1. Tem id com prefixo e está no catálogo da família.
2. Tem fonte na coluna Origem.
3. Diz para quem e para quê, e aponta um objetivo (OBJ).
4. Tem pelo menos um critério em Dado, Quando, Então.
5. Dependências listadas e nenhuma bloqueada; dependência aceita fica escrita na issue.
6. Estimada e cabe em uma semana de sprint; senão, quebrada antes de entrar.
7. Quem vai fazer entendeu; dúvida aberta vira pergunta a Vitor antes de começar, não no meio.
8. Se toca física, calibração ou validação, a regra está validada com Vitor contra o acervo e
   aprovada com o valor (E-RN-02); se toca formato de arquivo, o arquivo real está anexado.

## Definition of Done (está pronto se)

1. Cada critério verificado por teste automatizado ou demonstração registrada em `06-validacao.md`.
2. Lint e testes verdes no CI.
3. Catálogo e matriz da família atualizados no mesmo PR.
4. Documentação de uso atualizada quando a interface muda.
5. PR revisado por outra pessoa; nenhum push direto em `main`.
6. Se o item toca o núcleo, o catálogo da empresa também foi atualizado.
7. O incremento foi demonstrado a Vitor e aceito: teste verde prova que funciona, não que é o
   que ele queria.
