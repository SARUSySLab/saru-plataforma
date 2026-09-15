---
titulo: Backend por widget
---

# Backend por widget

Dos 22 widgets que aparecem nos mocks, no saru-app e na PoC, 6 já têm o dado pronto no backend da plataforma, 10 precisam de capacidade nova de backend na primeira versão e 6 ficam para depois. A base comum dos 10 é a mesma: canal com nome e unidade medidos, um sentido de sinal único, canais matemáticos com origem declarada e estatística por canal calculada no servidor.

Este documento é o contrato entre o backend deste repositório e a interface desenhada no `SARUSySLab/saru-empresa`. Cada linha diz o que o servidor entrega para o widget funcionar, o estado disso hoje e quanto do acervo tem o dado.

## O que o backend entrega para cada widget

A Tabela 1 diz o que o servidor precisa entregar e em que fase. "V1" é a primeira versão; "V2" fica para depois.

Tabela 1. Widget unificado, entrega de backend, estado em 2026-09-15 e fase.

| # | Widget | O backend entrega | Hoje | Fase |
|---|---|---|---|---|
| 1 | Indicadores da volta e da sessão | blocos N0 e N1 do relatório: melhor volta, volta ideal, velocidade máxima, litros, acelerador pleno | pronto, menos o índice de trail-braking (PIL-RF-23) | V1 |
| 2 | Traço por distância com qualquer canal | `SerieAmostras` com todo canal da gravação e rótulo de qualidade | pronto no PR #60 | V1 |
| 3 | Delta e comparação entre voltas | grade comum de 900 pontos por volta; referência de outra gravação (PIL-RF-11) | pronto | V1 |
| 4 | Onde ganhar tempo por curva e micro-setor | bloco N2 por curva e por micro-setor | pronto; a lista "tudo" é montada no front e deve vir pronta do servidor | V1 |
| 5 | Mapa da pista com cor por canal | traçado por GPS e trechos do layout | pronto com GPS | V1 com GPS, V2 sem GPS |
| 6 | Tabela estatística por canal | mínimo, máximo, média e percentis de cada canal por volta | não existe no servidor; a PoC calcula no front com 5 canais fixos | V1 |
| 7 | Dispersão entre dois canais | pares de canais na grade comum | a série do PR #60 já basta | V1 |
| 8 | Diagrama G-G e uso de aderência | aceleração lateral e longitudinal em m/s², G_Sum e envelope por direção | aceleração com nome; G_Sum e envelope não existem | V1 |
| 9 | Frenagem e trail-braking por curva | início da frenagem pela queda de G longitudinal (-3,5 m/s² por 10 m, PIL-RN-13), pico de pressão, transição freio e volante | regra aprovada, código não existe | V1 |
| 10 | Histograma de amortecedor | velocidade de haste derivada da posição, contagem por faixa de velocidade | não existe; amortecedor sem nome canônico | V1 depois da medição |
| 11 | Cinemática de chassi | rolagem, arfagem, heave e warp a partir da posição dos amortecedores e da geometria do carro | não existe | V2 |
| 12 | Subesterço e erro de guinada | ângulo de Ackermann, ângulo de subesterço, guinada cinemática e erro de guinada, com sinal ISO 8855 | não existe; depende da issue #61 | V1 depois da #61 |
| 13 | Temperatura e pressão de pneu por zona | temperatura por zona, gradientes de temperatura em °C (Tabela 5 do guia), pressão | temperatura do centro com nome; gradiente e pressão não | V1 no código |
| 14 | Canais matemáticos e expressão livre | série derivada na mesma grade, com fórmula, entradas e versão | só a marcha derivada | V1 com G_Sum, curvatura e velocidade de haste; resto V2 |
| 15 | Evolução de métricas por volta | uma métrica escalar por volta, com as novas (G_Sum médio, subesterço médio, pico de frenagem) | 4 métricas | V1 |
| 16 | Vitais de motor com alerta | canais canônicos de água, óleo, pressão de óleo e de combustível, lambda, bateria, pressão de admissão e faixa de plausibilidade | não existe | V1 nos canais, faixa depois de ratificada |
| 17 | Consumo de combustível | litros por volta a partir do canal de tanque | cálculo pronto; canal canônico de combustível não existe | V1 depois da medição |
| 18 | Estimadores de sessão | massa efetiva, coeficiente de arrasto e rigidez de rolagem por regressão sobre trechos da sessão | não existe; ligado à calibração da issue #49 | V2 |
| 19 | Torre de cronometragem e estratégia | live timing, janela de box, modelo de degradação | módulo de live timing existe; fora do tratamento de canal | V2 |
| 20 | Ficha de setup e dados de oficina | cadastro manual versionado: setup, balança de cantos, consumíveis, checklist, planilha de rodagem | ficha de setup versionada existe; o resto não | V2 |
| 21 | Nota do piloto | nota composta de pilotagem | fora: pesos sem regra ratificada; a PoC removeu a nota (decisão 12) | fora |
| 22 | Sincronização com vídeo | deslocamento de tempo entre vídeo e gravação | não existe | V2 |

## Onde cada widget aparece e quanto do acervo tem o dado

A Tabela 2 usa a mesma numeração da Tabela 1. A contagem de gravações vem do acervo local com 1.234 gravações.

Tabela 2. Fontes de cada widget e dado disponível no acervo em 2026-09-15.

| # | Onde aparece | Dado no acervo |
|---|---|---|
| 1 | 6 mocks; saru-app `overview`; PoC blocos 1, 4 e 5 | velocidade em 853 gravações |
| 2 | mock piloto N0 e unificado; saru-app `channel_trace`, `time_trace`; PoC bloco 10 | todo canal com série guardada |
| 3 | mock unificado (pacote de 4 traços, confronto de companheiros); saru-app `delta`, `comparison`; PoC bloco 6 | velocidade |
| 4 | mock piloto N0 e unificado; saru-app `micro_sectors`, `corner_insights`; PoC bloco 9 | depende de pista e trechos resolvidos |
| 5 | mocks piloto N0 e pitwall; saru-app `track_map`; PoC bloco 8 | GPS com nome em 758 gravações |
| 6 | mock unificado; saru-app `data_table`; PoC bloco 7 | todo canal |
| 7 | saru-app `xy_scatter` | todo canal |
| 8 | 4 mocks; saru-app `friction_ellipse`, `driver_coach` | aceleração em 764 `.xrk`, 39 `.ld`, 25 `.dat` e 24 `.pid` depois do PR #52 |
| 9 | mock piloto N0 (nota por curva); saru-app `brake_trace`, `braking_reference` | pressão de freio em 136 gravações; G longitudinal em cerca de 850 |
| 10 | mock unificado e bakeoff engenheiro; saru-app `DamperHistogram` sem backend | `Damper FL..RR` em 50 gravações `.pid`, `.pds` e `.dat`; escala do `.pid` a medir contra o `.dat` |
| 11 | mock unificado | `RollRate` e `PitchRate` em 618 `.xrk`, em graus por segundo e sem nome; amortecedor em 50 |
| 12 | mock unificado; saru-app `math_channels` | guinada em 764 `.xrk` sem nome; direção com nome em 125 |
| 13 | mocks pitwall e unificado; saru-app `tyres`; PoC blocos 15 e 16 | só gravações de simulador (39) e 5 `.xrk` sem amostra |
| 14 | mock unificado; saru-app `math_channels`, `math_expr` | depende das entradas de cada fórmula |
| 15 | saru-app `run_chart`; PoC bloco 5 | depende das entradas de cada métrica |
| 16 | mock pitwall (alerta de rádio); spec de canal do saru-app | `EDL8_*` em 86 `.xrk`; `Water Temp` e `Battery Voltage` nos `.dat` e `.pid` |
| 17 | mocks; PoC bloco 14 | `Tank Fuel` em 51 gravações `.pid` e `.pds`, escala a medir |
| 18 | mock unificado e bakeoff engenheiro | exige força ou torque de motor e trecho de desaceleração livre |
| 19 | mock pitwall e unificado | não é telemetria do carro |
| 20 | mocks equipe e unificado; saru-app `setup_sheet`; PoC gaveta 13 | dado de oficina, não de logger |
| 21 | mock piloto; saru-app `driver_score` | não se aplica |
| 22 | saru-app `video_sync` | não se aplica |

## A base comum que destrava a V1

Os 10 widgets de V1 com capacidade nova dependem de oito peças de backend. A Tabela 3 lista as peças e os widgets que cada uma destrava.

Tabela 3. Peça de backend, estado em 2026-09-15 e widgets da Tabela 1 que dependem dela.

| Peça | Estado | Widgets |
|---|---|---|
| Canal com nome e unidade medidos: apelidos novos, 7.023 canais `.xrk` que o leitor não decodifica, todas as famílias de `.pds` | apelidos em fila; `.pds` em medição; `.xrk` sem issue | 8, 10, 12, 13, 16, 17 |
| Sinal único ISO 8855 por perfil (eixo y e guinada positivos à esquerda) | issue #61 aberta | 8, 12 |
| Motor de canais matemáticos na grade comum, com fórmula, entradas e versão | não existe | 8, 10, 12, 13, 14, 15 |
| Estatística por canal e por volta no servidor | não existe | 6, 15, 16 |
| Parâmetros de veículo por gravação: entre-eixos, bitola, relação de direção, relação de instalação do amortecedor | presets do 911 GT3 Cup existem; ligação com a gravação não | 10, 11, 12 |
| Faixa de plausibilidade por canal canônico, para o rótulo `out_of_range` | a ratificar por Vitor | 16 |
| Reingestão que aplica mapa novo ao acervo sem quebrar | travada pela issue #53 | todos os que dependem de apelido novo |
| Tamanho da resposta: 356 KB por volta com 49 canais | medido na gravação `1e3443e0`; seleção de canal por parâmetro só se medir lentidão | 2, 7 |

## Ordem de ataque

1. Mesclar os PRs #52, #55, #57 e #60, que dão canal cru com qualidade, aceleração nas 830 gravações e nomes certos no `.pds`.
2. Resolver a issue #53, para a reingestão aplicar cada mapa novo ao acervo inteiro.
3. Calcular estatística por canal no servidor e mover para lá a lista "tudo" do bloco 9.
4. Criar o motor de canais matemáticos começando por G_Sum e curvatura, e a rota do diagrama G-G.
5. Fechar a issue #61 e entregar ângulo de subesterço e erro de guinada.
6. Medir contra o `.dat` a escala de amortecedor, freio traseiro, direção e combustível do `.pid`; ligar os apelidos; entregar velocidade de haste e histograma.
7. Implementar frenagem e trail-braking por curva (PIL-RF-23).
8. Criar os canais vitais de motor e levar as faixas de plausibilidade para Vitor ratificar.

## Limitações deste levantamento

Os caminhos e linhas do saru-app vêm de um levantamento automático sobre a pasta em quarentena e não foram conferidos um a um. Antes de portar código de lá, a linha citada precisa ser aberta.

Dos 26 mocks do bakeoff, 11 foram abertos. Os outros 15 repetem as mesmas três páginas (equipe, engenheiro e piloto) em estilo visual diferente, conferido pelo nome do arquivo e pelo `README.md` do bakeoff.

A contagem de gravações vem do banco local em 2026-09-15, depois da ingestão da pasta `Telemetria/` inteira e antes de a reingestão terminar. Números de canal sem nome (guinada, amortecedor, combustível) mudam quando os apelidos entrarem.

## Fontes

- Mocks: `SARUSySLab/saru-empresa`, `docs/mocks/plataforma-saru-unificada.html`, `mock-piloto-n0-desktop.html`, `mock-pitwall-desktop.html` e `bakeoff/`.
- saru-app: `services/frontend/src/features/workbooks/registry.tsx` e `services/telemetry-api/saru_lapanalyzer/`.
- PoC: `web/src/` e `src/saru_poc/relatorio.py` deste repositório, no branch `eng/59-mostrar-todo-canal`.
- Guia de análise: `SARUSySLab/saru-empresa`, `docs/referencias/engenharia-de-pista.md`, seções 4 a 13.
- Cobertura de canal: consultas ao banco local e medição de faixa das amostras em 2026-09-15.
