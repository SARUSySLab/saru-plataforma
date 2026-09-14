# Backlog da família Piloto

Este arquivo diz em que ordem o trabalho da família Piloto entra, o que é o mínimo que
precisa funcionar, e quando uma tarefa pode começar e quando ela está pronta.

Versão 1, 2026-09-13. As histórias apontam para os `PIL-RF` de `02-catalogos.md`. O sufixo
de cada história é o do rascunho da PoC de 2026-09-12: `US-09` virou `PIL-US-09`. As
histórias que saíram para outra família não têm sufixo aqui.

## Épicos

| Id | Épico | Objetivo | Histórias |
|---|---|---|---|
| PIL-EP-01 | Ingerir qualquer arquivo de logger com rastreabilidade | PIL-OBJ-03, PIL-OBJ-06 | PIL-US-01 a PIL-US-05, PIL-US-19 |
| PIL-EP-02 | Resolver pista e cortar voltas sem default silencioso | PIL-OBJ-01, PIL-OBJ-02 | PIL-US-06, PIL-US-07, PIL-US-08 |
| PIL-EP-03 | Entregar o insight em quatro níveis | PIL-OBJ-01, PIL-OBJ-02 | PIL-US-09 a PIL-US-12 |
| PIL-EP-06 | Servir logger sem canal de pedal | PIL-OBJ-05 | PIL-US-16 |
| PIL-EP-09 | Fechar as exceções do E-UC-01 que caem nesta família | PIL-OBJ-02 | PIL-US-24 a PIL-US-29 |
| PIL-EP-10 | Atender o piloto virtual de simulador | PIL-OBJ-01, PIL-OBJ-03 | PIL-US-30 |

O épico da empresa que esta família fecha é o E-EP-02 (`saru/docs/requisitos/03-backlog.md`).

## Histórias de usuário

| Id | História | PIL-RF | PIL-CT | MoSCoW | Valor | Esforço | MVP | Justificativa |
|---|---|---|---|---|---|---|---|---|
| PIL-US-01 | Como piloto, quero enviar o cartão do logger inteiro de uma vez, para não ter que saber qual arquivo importa | PIL-RF-01, PIL-RF-02 | PIL-CT-01, PIL-CT-02, PIL-CT-03 | must | alto | baixo | sim | Já implementado; é a porta de entrada do loop |
| PIL-US-02 | Como piloto, quero que arquivo desconhecido seja recusado com motivo, para não receber número inventado | PIL-RF-02, PIL-RF-04 | PIL-CT-03, PIL-CT-05 | must | alto | baixo | sim | Conserto estrutural do defeito de silêncio (F5) |
| PIL-US-03 | Como piloto, quero que o sistema leia os 12 formatos com leitor, para cobrir AiM, MoTeC, VBOX, Pi, ProTune e MDF4 do acervo | PIL-RF-03 | PIL-CT-04 | must | alto | alto | sim | Implementado; 6 dos 12 leem amostra completa (F5) |
| PIL-US-04 | Como piloto, quero cada tentativa de leitura registrada com versão e motivo, para conseguir refazer qualquer resultado | PIL-RF-04 | PIL-CT-05, PIL-CT-06 | must | alto | baixo | sim | Implementado; base do PIL-OBJ-06 |
| PIL-US-05 | Como piloto, quero todo canal em nome e unidade únicos, para comparar arquivo de logger diferente no mesmo gráfico | PIL-RF-05, PIL-RF-06 | PIL-CT-07, PIL-CT-08 | must | alto | médio | sim | Implementado; PIL-RN-10 herdada do ADR-0049 |
| PIL-US-06 | Como piloto, quero que o sistema descubra a pista sozinho pelo GPS, para não escolher em lista | PIL-RF-07 | PIL-CT-09, PIL-CT-10 | must | alto | médio | sim | Implementado; os testes próprios entram nesta sprint |
| PIL-US-07 | Como piloto, quero ser perguntado quando a pista não é reconhecida, em vez de receber setores de outra pista | PIL-RF-07, PIL-RF-13 | PIL-CT-11 | must | alto | baixo | sim | Conserto do B2; PIL-RN-01 |
| PIL-US-08 | Como piloto, quero minhas voltas cortadas mesmo quando o logger não marca volta, para analisar log contínuo de ECU | PIL-RF-08 | PIL-CT-12 | must | alto | alto | sim | Implementado em cascata de 3 degraus |
| PIL-US-09 | Como piloto, quero saber em 5 segundos se a sessão foi boa e onde perdi tempo, para decidir o que treinar na próxima bateria | PIL-RF-10, PIL-RF-13 | PIL-CT-15, PIL-CT-16, PIL-CT-19, PIL-CT-39 | must | alto | médio | sim | N0 do funil; PIL-RN-02 e PIL-RN-03 |
| PIL-US-10 | Como piloto, quero ver curva a curva quanto perdi e em que fase, para saber se freei cedo ou saí devagar | PIL-RF-09, PIL-RF-10 | PIL-CT-13, PIL-CT-14 | must | alto | alto | sim | N2; decisão 1 do plano (curva na v0) |
| PIL-US-11 | Como piloto, quero comparar minha volta com outra minha ou com uma referência do sistema, para ver a diferença por trecho | PIL-RF-11 | PIL-CT-17 | should | alto | médio | sim | Implementado na rodada 2 (F7) |
| PIL-US-12 | Como piloto, quero ver os canais no tempo e na distância de uma volta, para entender o que fiz com pés e mãos | PIL-RF-12 | PIL-CT-18 | should | médio | baixo | sim | N3; implementado |
| PIL-US-16 | Como piloto com Garmin ou AiM sem pedal, quero saber onde freei e virei em relação à referência, para treinar ponto de frenagem | PIL-RF-23 | PIL-CT-30 | should | alto | médio | não | Bloqueado por PIL-RN-13: o limiar é número de física e exige aprovação de Vitor |
| PIL-US-19 | Como piloto com FuelTech ou ProTune, quero enviar o CSV da minha ECU, para receber o mesmo relatório | PIL-RF-24 | PIL-CT-31 | should | alto | médio | não | Bloqueado: zero amostra no acervo (PIL-PRB-07). Entra no MVP assim que houver arquivo real |
| PIL-US-23 | Como piloto, quero um HTML do relatório para imprimir ou guardar, para reler sem login | PIL-RF-26 | PIL-CT-33 | could | médio | médio | não | Decisão 3 do plano, degradada pela opção C |
| PIL-US-24 | Como piloto, quero saber quando meu arquivo entrou só como inventário, para não achar que o sistema engoliu a sessão | PIL-RF-03, PIL-RF-13 | PIL-CT-52 | should | médio | baixo | não | Exceção 3e do E-UC-01; o status parcial já existe na ingestão, falta chegar ao relatório |
| PIL-US-25 | Como piloto, quero saber quantos canais do meu arquivo ficaram sem tradução, para saber o que o relatório não consegue mostrar | PIL-RF-05, PIL-RF-13 | PIL-CT-53 | should | médio | baixo | não | Exceção 4e do E-UC-01; a contagem já existe na tabela `ingestao` |
| PIL-US-26 | Como piloto com logger Pi, quero minhas voltas cortadas pelo marcador que já está no arquivo, para não depender do GPS | PIL-RF-08 | PIL-CT-54 | should | alto | alto | não | Exceção 5e do E-UC-01; 100 gravações do acervo sem corte |
| PIL-US-27 | Como piloto de Curitiba, quero minhas 67 voltas decompostas, para ver onde perdi tempo na minha pista | PIL-RF-09 | PIL-CT-55 | should | alto | baixo | não | Exceção 5f do E-UC-01; depende de Vitor decidir o comprimento certo do layout |
| PIL-US-28 | Como piloto cujo logger só marca volta a 1 Hz, quero o tempo de volta com casas decimais, para comparar duas voltas parecidas | PIL-RF-08 | PIL-CT-58 | should | alto | médio | não | Exceção 5i do E-UC-01; 17 gravações com tempo em segundos inteiros |
| PIL-US-29 | Como piloto, quero que todo bloco vazio da tela diga por que está vazio, para não confundir ausência com zero | PIL-RF-13 | PIL-CT-60 | must | alto | baixo | não | Exceção 7e do E-UC-01; 1 dos 7 motivos tem teste |
| PIL-US-30 | Como piloto de simulador, quero subir a gravação do iRacing, do ACC, do Assetto Corsa ou do GT7 e receber o mesmo relatório de quem roda na pista, para treinar no simulador com a mesma régua | PIL-RF-27, PIL-RF-07 | PIL-CT-44, PIL-CT-45 | must | alto | médio | sim | Decisão de Vitor de 2026-09-13. ACC e GT7 já leem pelo container `.ld`; iRacing e Assetto Corsa precisam de leitor e de arquivo real |

## MVP

Entram PIL-US-01 a PIL-US-12 e PIL-US-30. As doze primeiras estão implementadas na `main` de
2026-08-30. O que falta para o MVP ser declarado validado:

1. Os testes que a matriz marcava como "a escrever" para a resolução de pista e para o fator
   de fechamento do eixo de distância, entregues nesta sprint.
2. PIL-US-29, porque um bloco vazio sem motivo é o defeito que a PoC nasceu para matar.
3. PIL-US-30, o piloto virtual, entrou no MVP por decisão de Vitor em 2026-09-13. ACC e GT7
   já leem; o que falta dentro do MVP é a regra PIL-RN-17 valer na resolução de pista, sem a
   qual a gravação de simulador cai no degrau GPS com coordenada de placeholder. iRacing e
   Assetto Corsa dependem de arquivo real e ficam fora até haver um.
4. A validação com um piloto de track day real, que nunca aconteceu (`06-validacao.md`).

Ficam fora, com a razão:

| História | Razão |
|---|---|
| PIL-US-16 frenagem por G | O limiar é número de física; só entra com aprovação de Vitor (PIL-RN-13) |
| PIL-US-19 FuelTech e ProTune | Sem arquivo real não se escreve leitor (regra do plano) |
| PIL-US-23 HTML estático | Não muda o veredito do N0 |
| PIL-US-24 a PIL-US-28 | Exceções do E-UC-01 com custo maior que uma semana ou com decisão pendente de Vitor |

Fora de qualquer versão desta família: live timing, pit wall ao vivo, clima, assistente
Sarue, espinha operacional do evento e ferramentas de box. Cada um tem família de destino em
`01-problema-e-objetivos.md`.

## Definition of Ready

Os oito itens são os da empresa (`saru/docs/requisitos/03-backlog.md`), na ordem em que se
confere. Uma tarefa entra em desenvolvimento se:

1. Tem id com prefixo `PIL` e está no catálogo da família.
2. Tem fonte na coluna Origem.
3. Diz para quem e para quê, e aponta um `PIL-OBJ`.
4. Tem pelo menos um critério em Dado, Quando, Então.
5. Dependências listadas e nenhuma bloqueada; dependência aceita fica escrita na issue.
6. Estimada e cabe em uma semana de sprint; senão, quebrada antes de entrar.
7. Quem vai fazer entendeu; dúvida aberta vira pergunta a Vitor antes de começar.
8. Se toca física, calibração ou validação, a regra está validada com Vitor contra o acervo e
   aprovada com o valor (E-RN-02); se toca formato de arquivo, o arquivo real está anexado.

## Definition of Done

Os sete itens da empresa. Uma tarefa está pronta se:

1. Cada critério foi verificado por teste automatizado ou demonstração registrada em
   `06-validacao.md`.
2. Lint e testes verdes.
3. Catálogo e matriz da família atualizados no mesmo PR.
4. Documentação de uso atualizada quando a interface muda.
5. PR revisado por outra pessoa; nenhum push direto em `main`.
6. Se o item toca o núcleo, o catálogo da empresa também foi atualizado.
7. O incremento foi demonstrado a Vitor e aceito.
