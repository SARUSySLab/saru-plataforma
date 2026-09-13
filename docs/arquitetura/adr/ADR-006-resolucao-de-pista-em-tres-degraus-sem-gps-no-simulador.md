# ADR-006 Adotar resolução de pista em três degraus com bypass para simuladores

Status: aceito
Data: 2026-09-13
Requisitos motivadores: PIL-RF-07, PIL-RN-06, PIL-RN-16, PIL-RN-17, E-RN-08

## Contexto
Autódromos podem ter múltiplos traçados (longo, curto, oval) que compartilham as mesmas coordenadas geográficas. Além disso, exportadores de simuladores (como Assetto Corsa e Gran Turismo 7) frequentemente exportam coordenadas geográficas fixas ou irreais (ex. Donington Park gravado em arquivo que declara Interlagos).

## Decisão
Implementar a resolução de pista em três degraus sucessivos para loggers reais: degrau 1 por proximidade geográfica dentro de raio de 5,0 km; degrau 2 por comprimento de layout caso haja ambiguidade espacial; degrau 3 por comparação de setores. Para gravações com perfil de simulador, aplicar bypass imediato resolvendo a pista pelo nome e traçado declarados pelo jogo.

## Alternativas descartadas
| Alternativa | Por que não |
|---|---|
| Seleção puramente euclidiana da pista mais próxima | Escolhe incorretamente layouts adjacentes ou pistas paralelas sem validar a extensão real percorrida |
| Forçar resolução por GPS em telemetria de simuladores | Provoca falso positivo de localização em autódromos britânicos para corridas virtuais brasileiras |

## Consequências
Fica mais fácil resolver pistas corretamente mesmo quando o traçado interno difere do circuito principal e atender pilotos de simulador.
Fica mais difícil manter a tabela de correspondência de nomes entre jogos e autódromos reais.
Precisa monitorar a criação de aliases automáticos para impedir que coordenadas de simuladores poluam o catálogo de pistas reais.

## Componentes afetados
- `src/saru_poc/pipeline/resolucao_pista.py`
- `src/saru_poc/acervo.py`
- `src/saru_poc/seeds/tracks.yaml`
