# ADR-002 Adotar persistência híbrida com PostgreSQL e DuckDB Parquet

Status: aceito
Data: 2026-09-13
Requisitos motivadores: PIL-RNF-02, PIL-RNF-04, E-RNF-02

## Contexto
Uma sessão típica de track day de 20 minutos com 30 canais a 50 Hz gera mais de 1,8 milhão de pontos de dados numéricos. Gravar cada amostra como uma linha em tabelas relacionais convencionais degrada o desempenho de inserção e inflaciona os índices. Por outro lado, armazenar metadados de autenticação e voltas em arquivos soltos impede consultas relacionais estruturadas.

## Decisão
Segregar a persistência em dois mecanismos complementares: PostgreSQL para entidades relacionais (pilotos, sessões, metadados de voltas, setores e relatórios N0) e Apache Parquet consultado via DuckDB para matrizes de séries temporais de alta frequência.

## Alternativas descartadas
| Alternativa | Por que não |
|---|---|
| PostgreSQL para todas as amostras numéricas | Custo elevado de I/O em disco e degradação drástica de queries agregadas |
| SQLite para todo o sistema | Conflitos de escrita concorrente e incompatibilidade com as regras de governança de dados da SARU |
| InfluxDB ou TimescaleDB dedicado | Introduz dependência de serviço externo adicional desnecessária para a infraestrutura da PoC |

## Consequências
Fica mais fácil realizar consultas analíticas colunares ultra-rápidas em canais específicos sem sobrecarregar o banco de dados principal.
Fica mais difícil manter integridade referencial manual entre o identificador do arquivo Parquet e a chave primária no PostgreSQL.
Precisa monitorar a política de expurgo e caminhos relativos na variável `SARU_DATA_ROOT`.

## Componentes afetados
- `src/saru_poc/db.py`
- `src/saru_poc/storage.py`
- `src/saru_poc/pipeline/ingestao.py`
