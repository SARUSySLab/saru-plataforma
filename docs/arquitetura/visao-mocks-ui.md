# Arquitetura e Especificação de Mocks de Interface (Desktop PC)

Data: 2026-09-13. Autor: Vitor Toledo / SARU.
Norma: conformidade com o fluxo UnB (FGA0208: problema, objetivos, requisitos, modelagem, arquitetura, mocks, desenvolvimento, validação) e diretrizes de engenharia de pista.

## 1. Objetivo dos Mocks de Interface

Os protótipos em HTML consolidam o entendimento compartilhado entre produto, piloto amador e engenheiro de pista antes da implementação no frontend React. Eles materializam os requisitos funcionais RF-05, RF-07, RF-08 e RF-09 em telas verificáveis.

A prioridade declarada é desktop PC (resoluções 1440x900 e 1920x1080 em formato widescreen). O formato mobile fica explicitamente adiado para a fase de produto comercial de pista.

## 2. Separação de Níveis de Usuário

### Nível N0: Piloto Amador e Trackday

O piloto em evento de trackday busca diagnóstico imediato e acionável. Apresentar gráficos de telemetria brutos gera sobrecarga cognitiva e rejeição.

Diretrizes implementadas no arquivo docs/mocks/mock-piloto-n0-desktop.html:
1. Resumo executivo com tempo de volta real, referência ideal e delta acumulado.
2. Destaque para as 3 maiores perdas de tempo por volta, ordenadas por magnitude em segundos.
3. Diagnóstico causal em linguagem direta (frenagem antecipada, velocidade mínima baixa ou atraso na reaceleração).
4. Ação corretiva clara informando ponto de referência visual na pista e modulação de pedal.
5. Índice de Trail-Braking expresso em pontuação de 0 a 100 com base na elipse de atrito G-G.
6. Mapa interativo do circuito (AIC Curitiba 3.695 m) com curvas codificadas por criticidade de tempo.

### Nível N1: Engenheiro de Pista e Pitwall

O engenheiro de pista necessita de alta densidade de informação em tempo real e pós-sessão.

Diretrizes implementadas no arquivo docs/mocks/mock-pitwall-desktop.html:
1. Torre de cronometragem padrão HH Timing com gaps, intervalos e parciais de setores S1, S2 e S3.
2. Telemetria transiente multicanal (velocidade, aceleração lateral Ay, aceleração longitudinal Ax, rotação do motor).
3. Matriz de degradação térmica e de desgaste de pneus por eixo e lado do veículo.
4. Gráficos de traçado de pedais e ângulo de esterço sobrepostos com delta temporal contínuo.
5. Diagrama de elipse de atrito bidimensional dinâmico a 50 Hz.

## 3. Rastreabilidade com os Requisitos

| Requisito | Título | Artefato de Interface | Elemento Visual |
|---|---|---|---|
| RF-05 | Detecção de perdas de tempo | Mock N0 | Cards de Top 3 perdas de tempo com delta em segundos |
| RF-06 | Decomposição de frenagem | Mock N0 e N1 | Tabela de pontos de frenagem e pico de pressão |
| RF-07 | Índice de trail-braking | Mock N0 e N1 | Gauge circular 0-100 e diagrama de elipse G-G |
| RF-08 | Relatório executivo do piloto | Mock N0 | Faixa de KPIs rápidos e recomendação do engenheiro virtual |
| RF-09 | Telemetria avançada de engenheiro | Mock N1 | Faixas contínuas de canais, torre HH e mapa vetorial |

## 4. Roteiro de Transição para o Frontend React

A transição dos arquivos HTML para a aplicação em web/ seguirá o padrão já existente:
1. Reutilização dos design tokens de web/src/estilo/tokens.css para cores, fontes e raios de borda.
2. Componentização em React com Vite e TypeScript.
3. Canvas 2D nativo ou SVG para renderização de alta taxa de quadros (60 fps) nos gráficos de telemetria por distância.
4. Conexão com os endpoints FastAPI de ingestão e relatório (/api/v1/sessoes/{id}/relatorio).
