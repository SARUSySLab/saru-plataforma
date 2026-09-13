# Diagrama de contexto

Visão de fronteira do sistema SARU PoC Trackday (família Piloto), identificando os usuários humanos, fontes de dados e integrações externas.

## Diagrama C4 contexto (Nível 1)

```mermaid
flowchart TD
    subgraph Atores["Atores do Sistema"]
        P1["Piloto de Track Day (P1/P2)<br>[Usuário principal no box]"]
        P2["Piloto Virtual / Sim Racer (P3)<br>[Usuário de simulador]"]
        ENG["Chefe de Equipe / Coach<br>[Usuário avançado]"]
    end

    subgraph Fontes["Fontes de Telemetria e Sensores"]
        LOG["Loggers Reais de Pista<br>[AiM, MoTeC, Cosworth, VBOX, FuelTech]"]
        SIM["Simuladores e Plugins<br>[iRacing .ibt, Assetto Corsa ACTI .ld, ACC]"]
    end

    subgraph SARU["SARU PoC Trackday"]
        CORE["Sistema SARU PoC<br>[API FastAPI, Pipeline Pipes and Filters, Relatório N0/N1]"]
    end

    subgraph Externo["Serviços Externos"]
        METEO["API Open-Meteo<br>[Condições meteorológicas históricas e em tempo real]"]
        CLOUDOBJ["Armazenamento de Objetos<br>[MinIO / S3 compatível para arquivos brutos e Parquet]"]
    end

    LOG -->|"Arquivos binários (.xrk, .ld, .pds, .vbo, .mf4)"| CORE
    SIM -->|"Arquivos de simulador (.ibt, .ld)"| CORE
    P1 -->|"Faz upload de telemetria e consulta relatório N0"| CORE
    P2 -->|"Envia volta de simulador e compara tempos"| CORE
    ENG -->|"Analisa setores e consistência do piloto"| CORE
    CORE -->|"Consulta temperatura e condição de pista"| METEO
    CORE -->|"Persiste e recupera séries temporais e blobs"| CLOUDOBJ
```

## Elementos e interfaces

1. Piloto de Track Day: envia o lote de arquivos após a bateria e consome o diagnóstico N0 em menos de cinco segundos no smartphone ou tablet.
2. Piloto Virtual: envia arquivos gravados no iRacing ou Assetto Corsa para receber a mesma análise da pista real sem depender de coordenadas GPS.
3. Chefe de Equipe e Coach: consome relatórios consolidados para orientar o piloto entre as sessões.
4. Loggers e Simuladores: sistemas proprietários que geram arquivos binários com taxas de aquisição entre 1 Hz e 1000 Hz.
5. API Open-Meteo: fornece dados meteorológicos para correlacionar desempenho com temperatura e condição de pista.
