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
| 2026-09-13 | Vitor, no chat | As nove perguntas de calibração, física e escopo da família Piloto | Ratificou Curitiba em 3.695 m; aprovou faixa [0,9; 1,1] com classificação de in/out/trânsito/aquecimento; aprovou limiar de frenagem em -3,5 m/s² com trail-braking combinado; ratificou PIL-RN-08; aprovou teste de plausibilidade física para canais sem unidade (PIL-RN-10); ratificou PIL-RN-16; aprovou tolerância de 0,05 s para GPS 1 Hz; determinou conscientização de pneus para o piloto e clima resumido/processado; determinou inclusão de plugins de terceiros (ACTI MoTeC no AC, .ibt no iRacing) para atender sim drivers e equipes de e-sports | Decisões ratificadas na matriz e catálogos | família Piloto v1.1 |

Validação com piloto de track day real: pendente para o N0 em campo. As personas P2 e P3
vieram de pesquisa de mercado de 2026-07-15. É o próximo marco de validação externa.

## Decisões ratificadas por Vitor em 2026-09-13

Todas as nove perguntas anteriores foram respondidas e ratificadas formalmente:

1. O comprimento nominal do Autódromo de Curitiba no circuito principal é de 3.695 m. O valor 3.220 m correspondia ao traçado curto. Com 3.695 m, as voltas de 3.749 m fecham com razão 0,9856.
2. A faixa de fechamento [0,90; 1,10] está aprovada. Voltas de entrada, saída, aquecimento e trânsito devem ser classificadas em categorias próprias no relatório.
3. O limiar de início de frenagem por desaceleração longitudinal é de -3,5 m/s² sustentado por 10 m. O cálculo de trail-braking combina velocidade, volante, aceleração lateral, frenagem e delta instantâneo.
4. A validade de volta por cobertura espacial e setores (PIL-RN-08) está ratificada, com velocidade média mínima de 20 km/h para descartar veículos rebocados ou parados no box.
5. Canais sem unidade comprovada (PIL-RN-10) passam por teste de plausibilidade física entre grandezas padrão. Se a unidade continuar incerta, o canal fica fora do vocabulário canônico.
6. A ambiguidade de autódromos em raio inferior a 5,0 km (PIL-RN-16) não se resolve por distância euclidiana ao centro, avançando para a comparação de extensão e setores.
7. A tolerância de sincronização para GPS de 1 Hz contra série rápida é de 0,05 s. Divergências superiores a 0,20 s disparam alerta de perda de sincronia.
8. Na família Piloto, dados meteorológicos entram resumidos e pré-processados, com incentivo ao registro consciente de calibragem a frio, pressão a quente e voltas por jogo de pneus.
9. A família Piloto atende simuladores e e-sports (PIL-RF-27) via exportações de plugins de terceiros (ACTI MoTeC para Assetto Corsa) e telemetria nativa do iRacing (`.ibt`).

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
