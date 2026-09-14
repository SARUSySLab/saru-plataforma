# Modelo de dados e persistência híbrida

Estratégia de segregação de dados entre banco relacional para metadados e arquivos colunares para séries temporais de alta frequência.

## Arquitetura de persistência

```mermaid
erDiagram
    PILOTO ||--o{ GRAVACAO : possui
    GRAVACAO ||--o{ VOLTA : contem
    GRAVACAO ||--o| RELATORIO_N0 : sintetiza
    VOLTA ||--o{ SETOR : divide
    VOLTA ||--o{ CURVA : decompoe
    VOLTA ||--o| SERIE_TEMPORAL_PARQUET : mapeia

    PILOTO {
        uuid id PK
        string email
        string senha_hash
        string nome
        timestamp criado_em
    }

    GRAVACAO {
        uuid id PK
        uuid piloto_id FK
        string sha256_hash
        string formato_detectado
        string pista_resolvida
        string layout_resolvido
        string status_processamento
        string motivo_degradacao
        timestamp recebido_em
    }

    VOLTA {
        uuid id PK
        uuid gravacao_id FK
        int numero
        float tempo_segundos
        float distancia_metros
        boolean valida
        string classificacao
        float velocidade_media_ms
    }

    SETOR {
        uuid id PK
        uuid volta_id FK
        int numero
        float tempo_segundos
        float distancia_inicio_m
        float distancia_fim_m
    }

    CURVA {
        uuid id PK
        uuid volta_id FK
        int numero
        float velocidade_minima_ms
        float ponto_frenagem_m
        float desaceleracao_pico_ms2
        float trail_braking_indice
    }

    RELATORIO_N0 {
        uuid id PK
        uuid gravacao_id FK
        uuid volta_referencia_id FK
        uuid volta_analisada_id FK
        float delta_tempo_segundos
        string texto_diagnostico
        json condicoes_clima
    }

    SERIE_TEMPORAL_PARQUET {
        string caminho_arquivo PK
        uuid gravacao_id
        int volta_numero
        int total_amostras
        string hash_colunas
    }
```

## Divisão de responsabilidades de armazenamento

1. Banco Relacional (PostgreSQL):
Armazena entidades com relacionamentos estritos, regras de integridade referencial e filtros de controle de acesso por piloto. Consultas de listagem, tempos de volta e relatórios N0 são resolvidas diretamente nesta camada.

2. Séries Temporais (Apache Parquet e DuckDB):
Armazena as medições contínuas de sensores (taxas de 10 Hz a 1000 Hz). Cada volta gera um arquivo Parquet imutável particionado pelo identificador da gravação. O formato colunar permite consultas rápidas de canais específicos sem carregar o conjunto inteiro na memória.

3. Armazenamento de Arquivos Brutos:
Mantém o binário original recebido do piloto, identificado pelo hash SHA-256 em diretório particionado pelos dois primeiros caracteres do hash. Permite reprocessamento futuro com versões atualizadas dos algoritmos sem perda da fonte primária.

