# Plano de resolução dos problemas abertos em 2026-09-13

Leitor: Vitor, para decidir o que é viável. Cada problema traz a causa, a resolução proposta
de raiz, o requisito ou decisão que a sustenta, o custo em horas de agente e o que só Vitor
decide. Ordem: do que trava mais para o que trava menos.

## 1. Dois agentes no mesmo repositório sem protocolo

Causa. O Antigravity e o Claude Code trabalharam hoje na mesma pasta e nos mesmos repositórios
sem saber um do outro: sete PRs mesclados em uma hora, arquivos modificados sem commit em dois
clones, números de física escritos como aprovados sem a tabela que a regra exige, e um
runbook de fusão de repositórios que contradiz uma decisão da manhã.

Resolução. Um protocolo de convivência escrito e versionado, não um combinado de chat:

1. Divisão por área, registrada em `saru/docs/processo/agentes.md`: Antigravity cuida de
   mock, validação visual, blueprint de tela e documento de interface; Claude Code cuida de
   requisitos, física, código de pipeline, processo e revisão. Quem sai da sua área pede por
   mensagem.
2. Caixa de mensagens em arquivo (`~/.claude/handoff/caixa-antigravity.md` e
   `caixa-claude.md`), já montada hoje, vira regra no `GEMINI.md` e no `CLAUDE.md` global:
   antes de tocar num repositório, o agente lê a caixa e o quadro de branches.
3. Quadro de branches vivas em `~/.claude/handoff/quadro.tsv` (já existe para sessões):
   uma linha por branch aberta, com dono, pasta e o que está fazendo. Agente que abre branch
   escreve a linha; agente que fecha, apaga.
4. Regra dura nos dois arquivos globais: nenhum agente mescla PR; nenhum agente escreve
   número de física como aprovado sem a tabela do E-UC-02; nenhum agente deixa árvore de
   trabalho suja ao encerrar.

Sustenta: E-RN-06 (decisão antes de código), E-RN-02 (física com medição), regra 5 do
CLAUDE.md global. Custo: 2 horas. Decisão de Vitor: aceitar a divisão por área.

## 2. Proteção da `main` sem plano pago

Causa. A organização está no plano gratuito; repositório privado dela não aceita proteção
pelo servidor. Hoje só o `saru`, no seu usuário com Pro de estudante, tem `main` protegida.
A PoC, onde está o código, aceita push direto de qualquer administrador.

Resolução em três degraus, cada um com data de gatilho:

1. Agora: CI da PoC ganha o workflow `guard-pr` (já escrito no perfil da organização),
   que acusa push direto em `main`, e cada clone ganha um gancho local de pré-push que
   recusa push para `main` (`.claude/hooks/`, copiado do `saru-app`). Não impede, mas
   nenhum push direto passa em silêncio.
2. Quando a família Campeonato abrir: fusão em monorepo dentro do `saru`, pelo runbook já
   escrito, com o Lucas avisado antes e adicionado como colaborador. A partir daí todo o
   código fica sob a `main` protegida do `saru` sem pagar nada.
3. Quando houver receita ou parte pública: transferência do monorepo para a organização com
   plano Team, ou tornar público o que não expõe cliente.

Sustenta: decisão de 2026-09-13 (PoC continua com o Lucas; monorepo na segunda família).
Custo: degrau 1, 1 hora; degrau 2, 4 horas. Decisão de Vitor: nenhuma nova.

## 3. Regras de física entram no código sem medição

Causa. O limiar de frenagem de -3,5 m/s², a velocidade mínima de 20 km/h, a tolerância de
0,05 s e a faixa de 0,9 a 1,1 foram escritos como aprovados sem a tabela de medição no acervo
que E-RN-02 e E-UC-02 exigem. Constante solta no código não diz de onde veio nem quando foi
aprovada.

Resolução. Um registro único de regras de física, lido pelo código e conferido por teste:

1. Arquivo `seeds/regras_fisica.yaml` na PoC: uma entrada por regra, com id (`PIL-RN-13`),
   valor, unidade, data da aprovação de Vitor, caminho da tabela de medição e status
   (medida, aprovada, provisória). O código lê o valor dali; constante literal em módulo é
   proibida por teste.
2. Pasta `tests/medicoes/` com um script por regra, reproduzível contra o acervo, que gera a
   tabela em `docs/fisica/calibracao/<regra>.md`. A medição do limiar de frenagem que está
   rodando agora é a primeira; as outras três entram na fila.
3. Teste de coerência: se o YAML diz "provisória", o relatório do produto mostra o aviso
   "regra provisória" no bloco que a usa (E-RNF-03, honestidade de claim).
4. E-UC-02 ganha o passo final "gravar no YAML", e a matriz da família aponta para a linha do
   YAML em vez de para um número no texto.

Sustenta: E-RN-02, E-UC-02, E-RNF-03, E-RF-04 (rastrear cada número). Custo: 6 horas mais
1 a 2 horas por regra medida. Decisão de Vitor: aprovar cada valor depois da tabela.

## 4. Parâmetros do 911 GT3 Cup com proveniência pendente

Causa. O módulo de parâmetros tem 109 valores, dos quais 11 confirmados em fonte oficial,
27 divergentes e 14 que dependem dos manuais que só Vitor tem. `lf` e `lr` estão trocados
nas três gerações, o mesmo erro corrigido em julho no 992 GT3 R. As classes de proveniência
existem e não são usadas.

Resolução. Parâmetro vira dado com fonte, não código com número:

1. Um arquivo por geração em `seeds/veiculos/porsche_911_gt3_cup_991_1.yaml`, `991_2` e
   `992_1`, cada campo com valor, unidade, fonte (documento do Drive com página, ou URL) e
   proveniência (manual oficial, regulamento, fornecedor, estimativa). O módulo Python passa
   a carregar o YAML e a usar `ParameterValue` e `Provenance`, que hoje estão sem uso.
2. Teste de plausibilidade física por geração: `lr` dividido pelo entre-eixos tem que dar a
   fração de carga dianteira declarada; a soma `lf` mais `lr` tem que dar o entre-eixos;
   massa de corrida maior que massa seca; potência e torque dentro do que a Porsche publica.
   É o teste que teria pegado a inversão de `lf` e `lr`.
3. Sessão de conferência com os manuais do Drive (`Trabalho/Porsche_Cup/Docs/Manuais/`): o
   agente abre cada PDF, extrai o valor com a página, e Vitor confirma campo a campo. Os 14
   valores pendentes e os 27 divergentes saem dessa sessão com fonte.
4. O que a Porsche não publica (distribuição de peso, aerodinâmica) fica marcado
   "estimativa" no YAML e aparece assim em qualquer tela (E-RNF-03).

Sustenta: E-RF-08 (catálogo de engenharia com versão e fonte), E-RF-09, E-RN-02. Custo: 4
horas de agente mais 1 hora sua na conferência. Decisão de Vitor: confirmar valores.

## 5. Escopo real do E-RF-09

Causa. O requisito pede estimar o carro a partir da telemetria e simular a volta com modelo
de piloto. A pesquisa mostrou que, com os canais de um logger de Cup, só massa e arrasto
agregado são estimáveis com confiança; pneu completo e balanço aerodinâmico exigem sensor
que o carro de cliente não tem. E o modelo de piloto não existe em nenhum repositório.

Resolução. Reescrever o E-RF-09 em três níveis, cada um com critério e status próprio:

1. Nível 1, estimação viável: massa por mínimos quadrados recursivos e arrasto agregado por
   coastdown, em Python, validados contra o acervo da Porsche Cup (critério: erro de massa
   até 5%, como a literatura lida). Entra na família Engenheiro.
2. Nível 2, preset por geração com incerteza declarada (item 4), usado pelo QSS que já
   existe para produzir a volta parecida. Critério: tempo de volta simulado dentro de uma
   faixa que Vitor aprova contra a volta real.
3. Nível 3, modelo de piloto e 14 graus de liberdade em Julia, fase seguinte, com o
   `DriverMPC.jl` recuperado da tag de julho como ponto de partida e as bases abertas
   `MPCC` e `TUM-CONTROL` como referência. Sem data até o nível 2 fechar.

Sustenta: relatório 07 (recomendação de linguagem), relatório 08 (o que existe), E-RN-01
(não vender o que o código não sustenta). Custo: reescrita do requisito, 2 horas; nível 1,
uma semana; nível 2, uma semana. Decisão de Vitor: aceitar os três níveis e a ordem.

## 6. Resolução de pista sem guarda entre venue e GPS

Causa. As três gravações GT7 declaram Interlagos com coordenadas de Donington e resolvem por
alias sem aviso. Não há guarda de coerência em `resolucao_pista.py`, e a regra E-RN-08
(simulador resolve pelo jogo, nunca por GPS) ainda não está no código. Teste marcado como
falha esperada.

Resolução. Implementar a regra, não contornar o caso:

1. `resolucao_pista.py` lê `perfil_origem.simulado`; perfil de simulador nunca entra no
   degrau GPS e nunca gera alias novo a partir de posição.
2. Para logger real, guarda de coerência: venue resolvido por alias com GPS a mais de um
   raio da referência do layout gera a marcação "divergência venue x GPS" no relatório, sem
   trocar a pista (o alias é o sinal mais forte). O valor do raio é medido no acervo e entra
   no YAML do item 3.
3. O teste de falha esperada vira teste que passa; a issue #10 fecha com ele.

Sustenta: E-RN-08, E-RNF-01 (nada em silêncio), PIL-RN-17. Custo: 4 horas. Decisão de Vitor:
o raio da divergência, depois da medição.

## 7. Requisitos das famílias e validação com gente real

Causa. Só a família Piloto tem requisitos completos; Campeonato tem o arquivo 01 esperando
seu ok. Nenhum piloto de track day nem organizador viu o produto ou os requisitos. As
personas vêm de pesquisa de julho.

Resolução:

1. Sequência das famílias como aprovada: Campeonato (02 a 06 depois do seu ok no 01),
   Engenheiro (reaproveitando os 254 documentos do `saru-app`), Equipe, Aluno. Um arquivo
   por vez, com você.
2. Cada família só fecha a versão 1 com uma sessão de validação registrada em `06` com uma
   pessoa real do nicho: um piloto de track day para Piloto, um organizador de evento para
   Campeonato. Proposta: recrutar os dois em Brasília, com o N0 e o N1 já mesclados como
   material da sessão, dentro de duas semanas.
3. Toda validação segue a régua do relato de Giuliano: o que foi relatado e o que foi
   medido, separados.

Sustenta: OBJ-01, OBJ-04, E-CT-05, lição 1 de `06-validacao.md`. Custo: 3 horas por família
de escrita, mais as sessões. Decisão de Vitor: quem são as duas pessoas.

## 8. Onde mora cada documento

Causa. Hoje há requisitos e arquitetura na PoC, requisitos e física no `saru`, acervo
migrado para `saru/docs/`, um índice modificado sem commit, e ADRs nascendo em série (sete
em um dia) contra a decisão de "poucos ADR".

Resolução. Uma regra de moradia, escrita em `saru/CLAUDE.md` e no `CLAUDE.md` da PoC:

1. `saru/docs/`: empresa (decisões, negócio, marca, processo), requisitos de cada família,
   física validada (documentos e calibrações, sem código), pesquisa validada, auditorias.
2. Repositório de código: `docs/requisitos/` da família que ele implementa, `docs/modelos/`
   (dado, fluxo, tela, antes do código), `docs/arquitetura/` com um DAS e ADR só para
   mudança de estrutura, `docs/fisica-*.md` só para o que se refere ao código daquele
   repositório.
3. ADR novo exige citar a decisão em `saru/docs/decisions.md` que o motivou; os sete ADRs de
   hoje passam por essa conferência e os que forem decisão de produto (não de estrutura)
   viram linha em `decisions.md`.
4. `docs/INDICE.md` do `saru` é gerado por script a partir das pastas, não editado à mão.

Sustenta: E-RN-06, decisão de 2026-09-13 sobre documentação por repositório. Custo: 3 horas.
Decisão de Vitor: aprovar a regra de moradia.

## 9. Drive

Causa. As decisões D14 a D16 do plano consolidado continuam abertas: segredo em
`03_Marketing/.env`, instaladores de 459 MB, notas de trabalho fora do git, Apuama com nome
de SARU.

Resolução. Executar as três com a skill `quarentena`, na ordem: segredo e instaladores
(lista já pronta no relatório 05), depois as quatro áreas de `Trabalho/SARU`, depois Apuama
(pneu e dinâmica veicular para `saru/docs/fisica/`, CAD nunca). Cada lote com simulação
mostrada antes e manifesto reversível.

Sustenta: D14, D15, D16 do plano consolidado. Custo: 2 horas de agente, três aprovações
suas. Decisão de Vitor: aprovar cada lista.

## 10. Lucas

Causa. Sete PRs entraram na `main` do repositório dele hoje sem revisão dele, e há três PRs
em rascunho esperando.

Resolução. Uma mensagem sua ao Lucas, curta, com: o que mudou hoje e por quê, o convite para
colaborador do `saru`, o pedido de revisão dos PRs 17, e dos das issues #2 e #6, e o aviso
de que a fusão em monorepo só acontece com ele. Eu escrevo o rascunho; você envia.

Sustenta: decisão "Lucas não pode ter problema", E-RN-07. Custo: 30 minutos. Decisão de
Vitor: enviar.

## Ordem proposta e o que depende de quem

| Ordem | Item | Depende de | Prazo |
|---|---|---|---|
| 1 | Protocolo de dois agentes (1) e regra de moradia (8) | aprovação sua | hoje |
| 2 | Registro de regras de física com medição (3) e parâmetros com fonte (4) | tabela do limiar; sua sessão com os manuais | esta semana |
| 3 | Guarda venue x GPS e regra do simulador (6) | raio medido | esta semana |
| 4 | Campeonato 02 a 06 (7) e E-RF-09 em três níveis (5) | seu ok no 01 | esta semana |
| 5 | Mensagem ao Lucas (10) e gancho de pré-push (2, degrau 1) | seu envio | esta semana |
| 6 | Drive (9) | três aprovações suas | próxima semana |
| 7 | Validação com piloto e organizador reais (7) | as duas pessoas | duas semanas |
| 8 | Monorepo (2, degrau 2) | abertura da família Campeonato com o Lucas dentro | quando a família abrir |
