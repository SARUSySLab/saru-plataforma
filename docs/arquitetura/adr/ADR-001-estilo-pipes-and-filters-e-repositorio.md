# ADR-001 Adotar estilo Pipes and Filters com Repositório

Status: aceito
Data: 2026-09-13
Requisitos motivadores: PIL-RNF-01, PIL-RNF-02, PIL-RNF-05, E-RNF-01

## Contexto
O processamento de telemetria envolve etapas sequenciais independentes: leitura binária, normalização para unidades do Sistema Internacional, identificação de traçado, corte de voltas, decomposição cinemática e síntese de relatório. Algoritmos monolíticos dificultam testes isolados e impedem substituição modular de etapas com falhas parciais.

## Decisão
Estruturar o processamento no estilo arquitetural Pipes and Filters orquestrado por `ingestao.py`. Cada estágio opera como um filtro puro que recebe dados tipados e repassa o resultado. A persistência intermediária utiliza o padrão Repositório.

## Alternativas descartadas
| Alternativa | Por que não |
|---|---|
| Monólito procedural em script único | Acopla o parsing binário às regras de física e impede testes unitários por estágio |
| Orientação a eventos distribuída com brokers Kafka | Complexidade operacional excessiva para o volume e escopo da PoC em container único |

## Consequências
Fica mais fácil testar cada estágio do pipeline com fixtures isoladas e implementar novos leitores sem alterar cálculos físicos.
Fica mais difícil compartilhar estados globais voláteis entre etapas distantes sem passar pelo contrato do pipeline.
Precisa monitorar a passagem de parâmetros e o consumo de memória durante a transformação de grandes vetores numéricos.

## Componentes afetados
- `src/saru_poc/pipeline/ingestao.py`
- `src/saru_poc/pipeline/recepcao.py`
- `src/saru_poc/pipeline/leitura.py`
- `src/saru_poc/pipeline/resolucao_pista.py`
- `src/saru_poc/pipeline/corte_voltas.py`
- `src/saru_poc/pipeline/decomposicao.py`
- `src/saru_poc/relatorio.py`

