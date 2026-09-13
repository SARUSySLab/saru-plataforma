# NFR Framework: grafo de interdependência de metas flexíveis

Análise de requisitos não funcionais e trade-offs arquiteturais usando a abordagem de Chung et al. (2000), adotada no módulo Base de Arquitetura e Desenho de Software (FGA0208).

## Grafo de interdependência de metas flexíveis (SIG)

```mermaid
flowchart TD
    subgraph Metas["Metas Não Funcionais Principais (Softgoals)"]
        G_DESEMP["[Desempenho]<br>Processamento rápido"]
        G_CONF["[Confiabilidade]<br>Exatidão e reprodutibilidade"]
        G_USAB["[Usabilidade]<br>Fácil leitura no box"]
        G_SUPORT["[Suportabilidade]<br>Manutenção e novos formatos"]
        G_SEG["[Segurança]<br>Isolamento de dados"]
    end

    subgraph Operacionalizacoes["Decisões de Operacionalização Arquitetural"]
        OP_ASYNC["OP-01: Fila assíncrona<br>(Retorno 202 Accepted)"]
        OP_PARQUET["OP-02: Armazenamento colunar<br>(DuckDB / Apache Parquet)"]
        OP_PIPE["OP-03: Estilo Pipes and Filters<br>(Filtros desacoplados)"]
        OP_SI["OP-04: Normalização SI canônica<br>(Unidades físicas estritas)"]
        OP_N0["OP-05: Síntese N0 sem clique<br>(Três métricas e frases diretas)"]
        OP_AUTH["OP-06: Escopo por dono e JWT<br>(Filtro obrigatório em consultas)"]
        OP_HASH["OP-07: Imutabilidade SHA-256<br>(Gravação bruta intocada)"]
    end

    OP_ASYNC -->|"++"| G_DESEMP
    OP_ASYNC -->|"-"| G_CONF

    OP_PARQUET -->|"++"| G_DESEMP
    OP_PARQUET -->|"+"| G_SUPORT

    OP_PIPE -->|"++"| G_SUPORT
    OP_PIPE -->|"+"| G_CONF

    OP_SI -->|"++"| G_CONF
    OP_SI -->|"+"| G_SUPORT

    OP_N0 -->|"++"| G_USAB
    OP_N0 -->|"-"| G_CONF

    OP_AUTH -->|"++"| G_SEG
    OP_AUTH -->|"+"| G_CONF

    OP_HASH -->|"++"| G_CONF
    OP_HASH -->|"+"| G_SEG
```

## Análise de impactos e trade-offs

1. Fila assíncrona contra simplicidade operacional:
A resposta 202 com execução em segundo plano melhora o tempo de percepção do usuário no upload (impacto ++ em Desempenho). Exige monitoramento do ciclo de vida da tarefa e recuperação de falhas em workers (impacto - em Confiabilidade operacional simples).

2. Síntese N0 contra detalhamento analítico:
Exibir apenas três números e três recomendações no box permite leitura em cinco segundos sem distração (impacto ++ em Usabilidade). Suprime dados avançados de engenharia de pista na primeira tela (impacto - em completude imediata, resolvido pelo acesso posterior ao nível N1).

3. Normalização canônica no Sistema Internacional (SI):
A conversão prévia de todos os canais para metros por segundo, radianos e pascals elimina divergências entre loggers diferentes (impacto ++ em Confiabilidade e Suportabilidade). Aumenta o custo computacional no estágio de ingestão (impacto neutro mitigado pela escrita vetorial em Parquet).

