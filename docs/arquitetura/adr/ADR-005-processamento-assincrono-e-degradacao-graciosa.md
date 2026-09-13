# ADR-005 Adotar processamento assíncrono com degradação graciosa

Status: aceito
Data: 2026-09-13
Requisitos motivadores: PIL-RNF-01, PIL-RNF-03, E-RNF-01, E-RN-07

## Contexto
O processamento de arquivos de telemetria pode durar de centenas de milissegundos a vários segundos dependendo do tamanho da gravação e taxa de amostragem. Manter a requisição HTTP bloqueada provoca timeouts e bloqueia a navegação do piloto no paddock. Além disso, a ausência de sensores secundários (como pressão de freio ou temperatura de pneu) não deve impedir a geração do relatório básico de tempos e acelerações.

## Decisão
Desacoplar o upload da análise respondendo imediatamente com código HTTP 202 Accepted e identificador da tarefa, executando o pipeline em worker em segundo plano. Em caso de ausência de canais secundários, o pipeline aplica degradação graciosa marcando o campo `motivo_degradacao` sem abortar a síntese N0.

## Alternativas descartadas
| Alternativa | Por que não |
|---|---|
| Processamento síncrono no endpoint POST | Gera travamento do cliente HTTP e quebra a experiência mobile no box |
| Abortar a execução inteira na falta de um sensor | Inviabiliza a análise para mais de 70% dos carros de track day que possuem apenas GPS e ECU básica |

## Consequências
Fica mais fácil atender múltiplos uploads simultâneos sem sobrecarregar a porta de entrada da API.
Fica mais difícil para o cliente web saber o momento exato da conclusão sem implementar polling ou conexão WebSocket.
Precisa monitorar a fila de processamento e a correta transição de status no banco de dados.

## Componentes afetados
- `src/saru_poc/api.py`
- `src/saru_poc/pipeline/ingestao.py`
- `src/saru_poc/relatorio.py`
