# ADR-003 Adotar normalização de canais em dois estágios

Status: aceito
Data: 2026-09-13
Requisitos motivadores: PIL-RF-05, PIL-RNF-09, PIL-RN-10, E-RNF-04

## Contexto
Fabricantes de telemetria utilizam nomenclaturas distintas para a mesma variável física (ex. `Speed`, `GPS_Speed`, `V_Car`, `SPEED_MPH`) e unidades heterogêneas (km/h, mph, m/s). Misturar conversão de unidades dentro da lógica de análise gera inconsistências e dificulta a portabilidade entre loggers.

## Decisão
Normalizar canais em dois estágios estritos: o primeiro estágio extrai o canal com nome original do fabricante preservado; o segundo estágio traduz o identificador para o vocabulário canônico SARU via `aliases.yaml` e converte a série numérica para unidades do Sistema Internacional (SI).

## Alternativas descartadas
| Alternativa | Por que não |
|---|---|
| Normalização direta dentro de cada reader | Duplica código de conversão e impede reutilização de tabelas de equivalência |
| Manter unidades de origem até a interface web | Transfere complexidade matemática de cinemática para a camada visual |

## Consequências
Fica mais fácil adicionar suporte a novos modelos de aquisição mantendo os algoritmos de física imutáveis.
Fica mais difícil depurar casos em que o fabricante declara uma unidade errada no cabeçalho original.
Precisa monitorar canais sem unidade comprovada para aplicação de testes de plausibilidade física.

## Componentes afetados
- `src/saru_poc/readers/base.py`
- `src/saru_poc/pipeline/leitura.py`
- `src/saru_poc/seeds/aliases.yaml`

