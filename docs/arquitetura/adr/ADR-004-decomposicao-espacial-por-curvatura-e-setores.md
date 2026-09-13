# ADR-004 Adotar decomposição espacial no eixo de distância por curvatura

Status: aceito
Data: 2026-09-13
Requisitos motivadores: PIL-RF-09, PIL-RN-07, PIL-RN-13

## Contexto
Comparar duas voltas no domínio do tempo falha porque voltas com tempos distintos não têm alinhamento geométrico de curvas e frenagens. Além disso, pilotos utilizam trajetórias variadas que alteram a extensão percorrida em pequenas porcentagens.

## Decisão
Interpolar todas as variáveis no eixo de distância espacial da pista normalizado pelo comprimento nominal do layout, detectando início, ápice e saída de curvas através do pico de curvatura do traçado e limites de aceleração lateral.

## Alternativas descartadas
| Alternativa | Por que não |
|---|---|
| Comparação temporal direta por delta de tempo decorrido | Impede correlação precisa com a posição física da curva na pista |
| Comparação por raio euclidiano entre pontos de GPS | Sofre com ruído de amostragem de receptores de 1 Hz e drift de satélite |

## Consequências
Fica mais fácil identificar exatamente onde o piloto freou mais cedo ou perdeu tração na saída de uma curva específica.
Fica mais difícil processar voltas em que a extensão calculada diverge significativamente do layout oficial.
Precisa monitorar a tolerância do fator de fechamento da distância (restrito à faixa de 0,90 a 1,10).

## Componentes afetados
- `src/saru_poc/pipeline/decomposicao.py`
- `src/saru_poc/pipeline/tracado.py`
- `src/saru_poc/relatorio.py`
