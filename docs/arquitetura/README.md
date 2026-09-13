# Documento de Arquitetura de Software (DAS)

Visão consolidada da arquitetura da família Piloto do SARU PoC Trackday, estruturada conforme as diretrizes da disciplina FGA0208 (FCTE/UnB) e os requisitos formais do projeto.

## 1. Visão geral e estilo arquitetural

O sistema atende pilotos de track day e pilotos virtuais, transformando arquivos brutos de telemetria em um diagnóstico N0 legível em menos de cinco segundos no box.

O estilo arquitetural central é Pipes and Filters (tubos e filtros) integrado ao padrão Repositório e camada de borda Cliente-Servidor. Cada estágio da telemetria opera como um filtro autônomo e testável que consome dados tipados e produz estruturas normalizadas no Sistema Internacional (SI).

## 2. Requisitos arquiteturais restritivos

As decisões estruturais respondem diretamente aos requisitos não funcionais e regras da família:

1. Resposta assíncrona (PIL-RNF-03): o endpoint de upload responde imediatamente com HTTP 202 Accepted, liberando a interface enquanto o processamento ocorre em segundo plano.
2. Imutabilidade e reprodutibilidade (PIL-RNF-02, PIL-RN-05): arquivos originais são identificados por hash SHA-256 e nunca sofrem alteração; o reprocessamento preserva o histórico.
3. Degradação graciosa (PIL-RNF-01, E-RN-07): a ausência de sensores secundários gera sinalização de degradação sem abortar a síntese N0.
4. Normalização canônica no SI (PIL-RNF-09, PIL-RN-10): séries temporais operam exclusivamente em m/s, radianos e pascals, isolando conversões de unidade na exibição.
5. Isolamento de dados (PIL-RNF-07, E-RN-05): controle estrito de acesso multitenant garantindo que dados de telemetria nunca vazem entre pilotos.

O detalhamento completo com o que cada requisito exige e descarta está em [requisitos-arquiteturais.md](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/requisitos-arquiteturais.md).

## 3. Componentes e padrões de projeto

O sistema divide-se em quatro subsistemas principais:

1. Borda e Interface: FastAPI (`api.py`, `rotas/`) e CLI (`cli.py`), aplicando o padrão Controlador (GRASP) para gerenciar requisições e segurança com JWT (`auth.py`).
2. Pipeline de Processamento (Pipes and Filters): orquestrado por `ingestao.py`, conectando recepção, leitura com padrão Factory Method para instanciar leitores específicos em `readers/`, resolução de pista, corte de voltas, decomposição cinemática e geração de relatório N0 (`relatorio.py`).
3. Repositório Híbrido: PostgreSQL (`db.py`) para entidades relacionais e Apache Parquet com DuckDB (`storage.py`) para séries temporais de alta frequência.
4. Serviços de Suporte: cliente assíncrono para a API Open-Meteo (`clima.py`) e validador de contratos de dados (`contrato.py`).

## 4. Modelos arquiteturais

Os diagramas formais estão versionados na pasta `modelos/`:

- [Diagrama de contexto (C4 Nível 1)](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/modelos/contexto.md): atores, loggers de pista, simuladores e integrações externas.
- [Diagrama de componentes (C4 Nível 2)](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/modelos/componentes.md): acoplamento do pipeline, repositórios e serviços.
- [Diagrama de sequência da ingestão](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/modelos/sequencia-ingestao.md): ciclo dinâmico do upload HTTP até o relatório N0.
- [Modelo de dados híbrido](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/modelos/dados.md): diagrama entidade-relacionamento e esquema colunar Parquet.
- [NFR Framework SIG](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/modelos/nfr-framework.md): análise de interdependência de metas não funcionais e trade-offs.

## 5. Registros de decisão arquitetural (ADR)

Decisões estruturais registradas individualmente:

- [ADR-001 Adotar estilo Pipes and Filters com Repositório](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/adr/ADR-001-estilo-pipes-and-filters-e-repositorio.md)
- [ADR-002 Adotar persistência híbrida com PostgreSQL e DuckDB Parquet](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/adr/ADR-002-persistencia-hibrida-postgres-e-parquet-duckdb.md)
- [ADR-003 Adotar normalização de canais em dois estágios](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/adr/ADR-003-normalizacao-em-dois-estagios-raw-e-canonico.md)
- [ADR-004 Adotar decomposição espacial no eixo de distância por curvatura](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/adr/ADR-004-decomposicao-espacial-por-curvatura-e-setores.md)
- [ADR-005 Adotar processamento assíncrono com degradação graciosa](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/adr/ADR-005-processamento-assincrono-e-degradacao-graciosa.md)
- [ADR-006 Adotar resolução de pista em três degraus com bypass para simuladores](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/adr/ADR-006-resolucao-de-pista-em-tres-degraus-sem-gps-no-simulador.md)
- [ADR-007 Adotar classificação explícita de voltas anômalas](file:///home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday/docs/arquitetura/adr/ADR-007-classificacao-explicita-de-voltas-anomalas.md)

## 6. Riscos técnicos

1. Latência na reconstrução do traçado quando o arquivo possui mais de duas horas contínuas de pista.
2. Variações bruscas de amostragem em receptores GPS de 1 Hz em trechos sinuosos sem canal de odômetro de roda.
3. Necessidade de sincronização futura com a família Equipe caso surja demanda por telemetria ao vivo sem conectividade de internet no box.

## 7. O que ainda não foi decidido

1. Protocolo de sincronização bidirecional entre o modo local de box e a nuvem corporativa (E-RNF-05).
2. Modelo analítico para estimativa de desgaste térmico de freios quando o canal de temperatura física está ausente.
3. Biblioteca final de componentes visuais do frontend para a renderização de mapas de calor no traçado.

