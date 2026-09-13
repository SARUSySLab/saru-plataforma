# Diagrama de sequência: ingestão e diagnóstico N0

Fluxo dinâmico de processamento de um arquivo de telemetria desde o upload HTTP até a disponibilização do diagnóstico N0.

## Diagrama de sequência UML

```mermaid
sequenceDiagram
    autonumber
    actor Piloto as Piloto / Cliente HTTP
    participant API as API FastAPI (api.py)
    participant Auth as Autenticação (auth.py)
    participant Recepcao as Recepção (recepcao.py)
    participant Worker as Fila Assíncrona (ingestao.py)
    participant Reader as Leitor & Normalizador (leitura.py)
    participant Pista as Resolução de Pista (resolucao_pista.py)
    participant Corte as Corte de Voltas (corte_voltas.py)
    participant Decomp as Decomposição (decomposicao.py)
    participant Relatorio as Gerador de Relatório (relatorio.py)
    participant Storage as DuckDB / Postgres (storage.py)

    Piloto->>API: POST /api/gravacoes (arquivo binário)
    API->>Auth: Validar token JWT de sessão
    Auth-->>API: Identidade do piloto confirmada
    API->>Recepcao: Processar entrada e calcular SHA-256
    Recepcao->>Storage: Gravar arquivo original intacto
    Recepcao-->>API: Identificador da gravação gerado
    API->>Worker: Enfileirar processamento em segundo plano
    API-->>Piloto: 202 Accepted {id_gravacao, status: "processando"}

    Note over Worker: Início do processamento em segundo plano

    Worker->>Reader: Identificar formato e extrair canais
    Reader->>Reader: Converter grandezas para o Sistema Internacional (SI)
    Reader->>Storage: Persistir séries temporais em Parquet
    Reader-->>Worker: Séries normalizadas em memória

    Worker->>Pista: Resolver autódromo (GPS territorial ou declaração de jogo)
    Pista-->>Worker: Pista e layout identificados

    Worker->>Corte: Segmentar voltas e checar cobertura espacial
    Corte->>Corte: Classificar voltas (normal, in-lap, out-lap, aquecimento, tráfego)
    Corte-->>Worker: Lista de voltas válidas e anômalas

    Worker->>Decomp: Interpolar eixo de distância e calcular acelerações
    Decomp->>Decomp: Detectar frenagem (-3,5 m/s²), trail-braking e ápices
    Decomp-->>Worker: Setorização e deltas calculados

    Worker->>Relatorio: Gerar síntese N0 e correlacionar clima
    Relatorio-->>Worker: Diagnóstico N0 formatado
    Worker->>Storage: Persistir metadados e voltas no PostgreSQL
    Worker-->>Worker: Atualizar status para "concluido"

    Piloto->>API: GET /api/gravacoes/{id}/relatorio
    API->>Storage: Buscar diagnóstico consolidado
    Storage-->>API: Dados do relatório
    API-->>Piloto: 200 OK {resumo_n0, voltas, deltas}
```

## Pontos de controle do fluxo

1. Resposta rápida no passo 7: o piloto recebe confirmação imediata de recebimento antes de qualquer computação pesada.
2. Imutabilidade no passo 4: o arquivo original é gravado em disco ou bucket antes de qualquer transformação numérica.
3. Resiliência no passo 12: se a volta apresentar extensão anômala, o pipeline categoriza o tipo da volta sem interromper a execução das demais voltas.
4. Consulta sem processamento no passo 20: leituras posteriores do relatório consomem dados já agregados, garantindo resposta em poucos milissegundos.

