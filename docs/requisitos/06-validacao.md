# Validação da família Piloto

Este arquivo registra cada vez que os requisitos da família Piloto, ou o produto que os
implementa, foram mostrados a alguém que usa ou avalia, e o que mudou depois.

Versão 1, 2026-09-13. As três primeiras rodadas vêm do rascunho da PoC de 2026-09-12 e
aconteceram antes de a família existir como recorte; entram aqui porque foi delas que
saíram os requisitos desta família.

| Data | Com quem | O que foi mostrado | Feedback (paráfrase) | O que mudou | Versão resultante |
|---|---|---|---|---|---|
| 2026-08-20 | Giuliano, engenheiro de pista sênior, usando o `saru-app` em campo | Fluxo de importação e tela do Analyzer (hoje PIL-RF-01, PIL-RF-10, PIL-RF-12) | Erro ao entrar de novo trava o login; "delta OV" não quer dizer nada; velocidade GPS e traçado deviam ficar no topo; loggers amadores não têm pedal, mas todos têm acelerômetro, dá para derivar frenagem e viragem | Nasceram PIL-RF-23, PIL-RN-13, PIL-RNF-08 e a calibração de limiar de 2026-08-22 (F10). O bug de login ficou fora por decisão de Vitor | requisitos v1 |
| 2026-08-28 | Lucas Antunes, com Vitor | Plano canônico da PoC: granularidade, armazenamento, saída, formatos, funil de 4 níveis, 15 blocos | Curva e traçado entram na v0; Postgres com Parquet e DuckDB; repositório próprio sem tocar o `saru-app`; FuelTech e ProTune primeiro; 15 pedidos viram 13 blocos com 3 fusões | Base de PIL-RF-01 a PIL-RF-13, PIL-RN-01 a PIL-RN-04, PIL-RNF-01 a PIL-RNF-04 | requisitos v1 |
| 2026-08-29 | Respondentes do questionário da barra de comparação, consolidado por Lucas no commit 2b88627 | Barra de comparação e tela do dia de pista (PIL-RF-11) | Upload deve agrupar bundles como a CLI; acervo sem dono vazava entre contas; referência do sistema como fonte de comparação; analisada e referência nunca a mesma volta | PIL-RN-05, PIL-RN-14, PIL-RF-16 e a regra de escopo em todas as rotas de leitura | requisitos v1 |
| 2026-09-12 | Vitor | Os seis arquivos do rascunho da PoC inteira | Aprovou o recorte por famílias, a ordem das famílias e o mínimo viável da família Piloto. As regras de física (PIL-RN-07, PIL-RN-08, PIL-RN-10, PIL-RN-13) ficaram pendentes | Nasceu este conjunto de seis arquivos, só da família Piloto | família Piloto v1 |
| 2026-09-13 | Vitor, no chat | O recorte da família Piloto | A família atende também o piloto virtual de simulador, com o mesmo relatório da volta real, na ordem iRacing, ACC, Assetto Corsa e GT7. Gravação de simulador resolve a pista pelo que o jogo declara, nunca por GPS: a coordenada exportada é placeholder | No núcleo, E-RF-01 ampliado e E-RN-08. Nesta família, PIL-RF-27, PIL-RN-17, PIL-CT-44, PIL-CT-45 e PIL-US-30, que entra no MVP | família Piloto v1 |
| 2026-09-13 | Vitor (pendente) | Este conjunto, em especial as oito perguntas abertas da seção abaixo | | | |

Validação com piloto de track day real: nenhuma até 2026-09-13. As personas P2 e P3 vêm de
pesquisa de mercado de 2026-07-15, não de entrevista. É a lacuna mais importante desta
família: quem compra o resultado ainda não viu o N0.

## O que está aguardando decisão de Vitor

Cada item é uma pergunta com resposta objetiva. Nenhum deles avança sem ela.

1. Curitiba mede 3.220 m no catálogo e 3.749 m na telemetria de 67 voltas. Qual dos dois
   está certo, ou é outro layout da mesma pista?
2. A faixa de 0,9 a 1,1 para o fator de fechamento do eixo de distância está aprovada? Ela
   está no código desde 2026-08-29 sem aprovação registrada.
3. Qual o limiar de queda do G longitudinal que marca início de frenagem? A medição de
   2026-08-22 achou queda mediana entre 11 e 24 m/s² em 232 voltas com pedal real.
4. Uma volta é válida por cobertura da pista, sem piso de tempo absoluto (PIL-RN-08)? O
   ADR-0033 propôs isso em 2026-07-27 e nunca foi ratificado.
5. Canal sem unidade provada fica fora do vocabulário canônico (PIL-RN-10)? O ADR-0049
   propôs isso; falta ratificar para esta família.
6. Duas candidatas dentro do raio de 5,0 km mandam a resolução para o degrau seguinte, em
   vez de escolher a mais próxima (PIL-RN-16)? A regra veio do ADR-0048, que continua
   proposto. O raio de 5,0 km, esse sim, você aprovou em 2026-08-20.
7. Quando o único canal de volta é de 1 Hz, qual erro de instante é aceitável depois do
   refino contra a série rápida?
8. O piloto de track day precisa registrar pneu e clima da própria bateria, ou isso é só da
   família Equipe?
9. Para o piloto virtual, o Assetto Corsa da lista é o original ou o Competizione? O ACC já
   lê pelo container `.ld`; o original não tem leitor em lugar nenhum, e a resposta muda se
   sobra um leitor a escrever ou dois.

## Lições aprendidas

1. O feedback de campo de 2026-08-20 mostrou que as três queixas mais duras não eram de
   física nem de análise: um bug de operação, jargão na tela e uma capacidade ausente
   (frenagem sem pedal). Toda rodada de validação passa a registrar o que é relatado e o que
   é medido, separados, como o próprio relato de Giuliano faz.
2. Os dois defeitos que motivaram a PoC (volta ideal impossível e pista por default) eram
   defeitos de silêncio. Todo bloco sem dado declara motivo (PIL-RF-13), e todo requisito de
   confiabilidade tem um teste que prova a recusa, não só o caminho feliz.
3. O plano pediu amostras reais de FuelTech e ProTune em 2026-08-28 como item bloqueante e
   até 2026-09-13 não há nenhuma no acervo. Leitor de formato entra no backlog só com arquivo
   real anexado à issue (DoR item 8).
4. Das três regras de calibração que o código usa, só o raio de 5,0 km tem aprovação de
   Vitor registrada, de 2026-08-20, com a medição na mesa. A faixa de 0,9 a 1,1 e o limiar
   de frenagem entraram no código sem isso. Regra de física tem linha na tabela de aprovação
   da matriz, e o código que a usa cita o id da regra.
5. Uma regra aprovada pode carregar junto uma regra que ninguém aprovou. PIL-RN-06 dizia o
   raio e a ambiguidade numa frase só, e o ADR-0048 de origem está proposto desde
   2026-08-20: o que Vitor decidiu naquela data foi o número do raio. A ambiguidade virou
   PIL-RN-16, com a pendência dela. Uma regra por linha, uma procedência por regra.
6. Requisito de núcleo muda depois de a família estar escrita, e isso é normal. A decisão de
   2026-09-13 sobre o piloto virtual chegou com os seis arquivos prontos, e o que segurou o
   estrago foi a matriz: bastou acrescentar PIL-RF-27 e PIL-RN-17 e ligar os dois ao E-RF-01
   e ao E-RN-08. Mudança de núcleo entra por linha nova na tabela de impacto, nunca por
   reescrita do documento.
7. Um requisito pode estar implementado e mesmo assim não ter prova. A resolução de pista
   rodava em 198 gravações desde agosto sem um teste próprio, e o degrau que mais decide, o
   GPS, só ganhou teste em 2026-09-13. Requisito com status "implementado" e coluna de teste
   vazia na matriz é dívida, não conquista.
