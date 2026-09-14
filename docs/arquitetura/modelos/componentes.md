# Diagrama de componentes

Estrutura interna dos componentes do SARU PoC Trackday organizada pelo estilo arquitetural Pipes and Filters com Repositório de Dados.

## Diagrama C4 componentes (Nível 2)

```mermaid
flowchart TD
    subgraph Borda["Camada de Borda e Entrada"]
        CLI["CLI de Operação<br>(cli.py)"]
        API["FastAPI App & Rotas<br>(api.py / rotas/)"]
        AUTH["Autenticação & Escopo<br>(auth.py)"]
    end

    subgraph Pipeline["Pipeline Pipes and Filters (Orquestrado por ingestao.py)"]
        F1["1. Recepção & Hash<br>(pipeline/recepcao.py)"]
        F2["2. Leitura & Normalização<br>(readers/ & pipeline/leitura.py)"]
        F3["3. Resolução de Pista<br>(pipeline/resolucao_pista.py)"]
        F4["4. Corte de Voltas<br>(pipeline/corte_voltas.py)"]
        F5["5. Decomposição & Traçado<br>(pipeline/decomposicao.py & tracado.py)"]
        F6["6. Relatório N0/N1<br>(relatorio.py)"]
    end

    subgraph Persistencia["Repositório de Dados"]
        DB["PostgreSQL (db.py)<br>[Sessões, pilotos, metadados de voltas e permissões]"]
        PARQUET["DuckDB & Parquet (storage.py)<br>[Séries temporais em alta frequência no formato SI]"]
        BLOB["Armazenamento Bruto<br>[Arquivos binários originais intactos indexados por SHA-256]"]
    end

    subgraph Suporte["Módulos de Apoio"]
        CLIMA["Serviço de Clima<br>(clima.py)"]
        CONTRATO["Validador de Contrato<br>(contrato.py)"]
    end

    API --> AUTH
    AUTH --> DB
    API --> F1
    CLI --> F1

    F1 -->|"Arquivo bruto validado"| BLOB
    F1 --> F2
    F2 -->|"Canais canônicos em SI"| F3
    F3 -->|"Autódromo e layout resolvidos"| F4
    F4 -->|"Voltas válidas e classificadas"| F5
    F5 -->|"Curvas, frenagens e deltas espaciais"| F6
    F6 --> CONTRATO
    CONTRATO --> API

    F2 -.->|"Persiste amostras normalizadas"| PARQUET
    F4 -.->|"Salva tempos de volta"| DB
    F5 -.->|"Salva vetores de curva"| DB
    F6 -.->|"Salva diagnóstico N0"| DB
    CLIMA -.->|"Temperatura e umidade"| F6
```

## Responsabilidades por componente

1. `api.py` e `rotas/`: expõe endpoints REST e WebSockets, gerenciando uploads multipart assíncronos e consultas de relatórios.
2. `auth.py`: aplica controle de acesso baseado em escopo (PIL-RNF-07), garantindo que nenhum piloto acesse dados alheios.
3. `recepcao.py`: calcula o hash SHA-256 para idempotência e salva o arquivo binário original sem qualquer alteração.
4. `readers/` e `leitura.py`: detecta o formato do arquivo, extrai canais brutos e mapeia grandezas para o vocabulário canônico em unidades SI.
5. `resolucao_pista.py`: identifica o autódromo por proximidade geográfica das coordenadas ou por nome declarado no simulador.
6. `corte_voltas.py`: localiza cruzamentos da linha de largada e chegada, valida cobertura da pista e classifica voltas anômalas.
7. `decomposicao.py` e `tracado.py`: interpola séries no eixo de distância, detecta zonas de frenagem, calcula trail-braking e métricas de curva.
8. `relatorio.py`: sintetiza deltas de tempo, consistência de pilotagem e orientações em linguagem natural direta para o nível N0.
9. `storage.py` e `db.py`: implementam o padrão Repositório, isolando o mecanismo físico de armazenamento do restante da lógica.

