# Validação

Rascunho 1, 2026-09-12. Cada vez que os requisitos, ou o produto que os implementa, foram
mostrados a quem usa ou a quem decide.

| Data | Com quem | O que foi mostrado | Feedback (paráfrase) | O que mudou | Versão |
|---|---|---|---|---|---|
| 2026-07-15 | Vitor, com Vinicius | Documento mestre de produto e negócios, personas, GTM | Cinco decisões ratificadas: Turbotec mantém o nome; pitch só afirma o que o código sustenta; consultoria antes de SaaS; mídia paga começa por busca; mascote saruê | Base de E-RN-01, F2 e F3 | anterior |
| 2026-08-20 | Giuliano, engenheiro de pista sênior, em campo com o `saru-app` | Importação e tela do Analyzer | Erro ao logar de novo; "delta OV" sem sentido; velocidade e traçado no topo; loggers amadores sem pedal, todos com acelerômetro | PRB-01, PRB-03, E-RNF-06, E-UC-02 exemplo de calibração | anterior |
| 2026-08-28 | Lucas Antunes, com Vitor | Plano canônico da PoC | Curva e traçado na v0; Postgres com Parquet; repositório próprio; FuelTech e ProTune primeiro; funil de 4 níveis; 15 blocos viram 13 | E-RF-01 a E-RF-06, E-RNF-01, E-RNF-02, E-UC-01 | anterior |
| 2026-08-29 | Respondentes do questionário da barra de comparação, via Lucas | Barra de comparação e dia de pista | Upload agrupa bundles; acervo sem dono vazava entre contas; referência do sistema; "outing" na tela | E-RF-06, E-UC-03 cenário 1c | anterior |
| 2026-09-12 | Vitor | 00 guia, 01 problema e objetivos | Cinco nichos, aluno em duas formas, Hase parceiro, hardware depois da DashAuto; metas de OBJ-05 e OBJ-06 a definir; Catalyst 2 como régua | 01 v1 com famílias e referência de mercado | 1 |
| 2026-09-12 | Vitor | 02 catálogos | 22 comentários: status "implementado" não é verdade, tudo parcial; E-RF-04 e E-CT-04 confusos; compartilhar entre famílias é must desde o início; E-RF-08 obrigatório; chega de ADR; uma semana de documentação antes de codar; prefixo também em issue | 02 v1 revisado | 1 |
| 2026-09-12 | Vitor | 03 backlog | Ordem das famílias ok; semana de documentação sim; Whisper na UnB; DoR tinha coisa a mais e misturada; papéis: o agente segue as regras, Vitor orienta | DoR de 8 itens, DoD com o sétimo, item "modelo antes do código" para E-RN-06 | 1 |
| 2026-09-12 | Vitor | 04 casos de uso, rascunho 1 | Não entendeu quase nada; UC de formato novo é caso raro; o que importa é o caminho do arquivo até cada família, que nunca fechou; passo 5 é descobre e corta, não "ou declara" | 04 v2 com E-UC-01 em 7 passos e exceções do acervo como tarefas; E-RF-03 reescrito | 2 |
| 2026-09-12 | Vitor | 05 rastreabilidade e 06 validação | Aprovados sem mudança | Os seis arquivos da empresa fecham a versão 1 | 1 |
| pendente | um piloto de track day | N0 da família Piloto | Nenhum piloto real viu o produto até hoje | | |
| pendente | Lucas | os seis arquivos e as mudanças aditivas na PoC | | | |

## Lições aprendidas

1. Handoff de outra sessão não é aprovação. Seis arquivos escritos de uma vez sem mostrar
   exemplo custaram uma rodada inteira. Regra: um arquivo por vez, conceito explicado em
   uma linha leiga antes da tabela. Já está na skill `requisitos`, passo 0.
2. Status "implementado" sem prova vira mentira em tabela. Regra: status só sobe com o
   critério verificado; até lá é "parcial" com a medida ao lado.
3. Caso de uso escrito no formato do livro não é lido por quem decide. Regra: cada caso abre
   com uma frase em português corrente, e o formato completo vem depois.
4. O caminho principal do produto (arquivo até uso por família) nunca foi fechado de ponta a
   ponta porque cada geração começou pela tela ou pela física. Regra: E-UC-01 é o primeiro
   épico a fechar em qualquer família, com as nove exceções do acervo como tarefas.
5. Regras de física existem no código sem aprovação registrada (faixa 0,9 a 1,1, raio de
   5 km). Regra: validação conjunta contra o acervo antes de entrar, id na regra, teste que
   reproduz a medição.
