# ADR-007 Adotar classificação explícita de voltas anômalas

Status: aceito
Data: 2026-09-13
Requisitos motivadores: PIL-RF-08, PIL-RN-07, PIL-RN-08, PIL-RN-12

## Contexto
Em track days, sessões contêm voltas de saída dos boxes (out-lap), voltas de retorno (in-lap), voltas de aquecimento de pneus e voltas prejudicadas por tráfego ou bandeiras amarelas. O descarte silencioso dessas voltas gera perplexidade no piloto, que não vê todas as voltas completadas no painel.

## Decisão
Substituir o descarte binário por uma máquina de estados de classificação explícita. O sistema rotula cada volta como `NORMAL`, `IN_LAP`, `OUT_LAP`, `AQUECIMENTO` ou `TRAFEGO`. O painel exibe todas as voltas e exclui as anômalas da volta ideal.

## Alternativas descartadas
| Alternativa | Por que não |
|---|---|
| Rejeição silenciosa e exclusão da lista de voltas | Cria divergência entre a contagem do painel do carro e o relatório SARU |
| Considerar todas as voltas como válidas para médias | Distorce a volta ideal e o cálculo de consistência com voltas lentas de pit lane |

## Consequências
Fica mais fácil para o piloto auditar a sessão completa e entender por que determinada volta foi classificada como anômala.
Fica mais difícil implementar os filtros de agregação estatística no relatório, que precisam filtrar pelo enum de classificação.
Precisa monitorar a sensibilidade dos limiares de velocidade média (piso de 20 km/h) e fator de fechamento [0,90; 1,10].

## Componentes afetados
- `src/saru_poc/pipeline/corte_voltas.py`
- `src/saru_poc/pipeline/decomposicao.py`
- `src/saru_poc/relatorio.py`

