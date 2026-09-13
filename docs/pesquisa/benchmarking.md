---
titulo: "Benchmark e Referencias"
data: "2026-07-08"
origem: "_arquivo/saru-docs/docs/research/benchmarking.md"
status: "vigente"
area: "arquitetura_software"
---

# Benchmark e Referencias

Este documento organiza referencias externas para orientar o SARU sem copiar o
escopo de ferramentas consolidadas. A leitura de mercado e tecnica aponta para
um posicionamento claro: **nao competir como logger, dashboard generico ou
simulador isolado**. O espaco do MVP e transformar telemetria real em sessao
canonica, comparar voltas, gerar uma referencia simulada e produzir decisao
tecnica rastreavel.

## Como usar este benchmark

- Inspiracao de mercado: entender fluxos, vocabulario, expectativas de
  usuarios e nivel minimo de credibilidade.
- Referencia tecnica: escolher formatos, bibliotecas e contratos que reduzem
  retrabalho.
- Limite de claim: separar o que o SARU pode prometer no alpha do que deve
  ficar como beta ou pesquisa.
- Roadmap: transformar referencias em epicos, nao em features copiadas.

## Ferramentas de mercado

| Referencia | O que ela prova no mercado | Implicacao para SARU |
|---|---|---|
| [McLaren Applied ATLAS](https://atlas.motionapplied.com/) | Telemetria de alto nivel opera como pipeline vivo entre carro, pit wall e fabrica. | SARU nao deve prometer substituir ATLAS no MVP; deve focar decisao pos-sessao e rastreabilidade. |
| [MoTeC Data Analysis / i2](https://www.motec.com.au/dataanalysis-currentrange/dataanalysis-directory/) | Analise desktop profunda, overlays, math channels e workflows de engenheiro sao padrao esperado. | O MVP precisa overlay real vs simulado e export tecnico, mas nao precisa replicar toda a suite. |
| [AiM Race Studio 3](https://www.aimtechnologies.com/support/downloads/software-downloads/race-studio-3/) | Usuarios esperam layouts de time/distance, histogramas, video e relatorios de canais. | UI deve priorizar timebase, canais e comparacao, nao uma pagina de marketing. |
| [VBOX Circuit Tools](https://www.vboxmotorsport.co.uk/us/circuit-tools) | Auto-deteccao de pista, math channels e metricas como coasting/understeer viraram linguagem comum. | SARU deve incluir metricas guiadas e explicaveis, especialmente em SA. |

### Leitura de produto

Mercado maduro valoriza velocidade de leitura e confianca. O usuario nao quer
apenas "ver graficos"; ele quer responder perguntas:

- onde perdi tempo?
- qual canal prova isso?
- a referencia simulada e plausivel?
- qual mudanca de setup ou pilotagem vale testar?
- o resultado e reproduzivel ou apenas uma demo?

Por isso o SARU deve vender **decisao tecnica com evidencia**, nao "mais um
dashboard".

## Projetos open-source e ferramentas reutilizaveis

| Area | Projeto | Uso recomendado |
|---|---|---|
| Lap-time simulation QSS | [TUMFTM/laptime-simulation](https://github.com/TUMFTM/laptime-simulation) | Referencia direta para QSS, sensibilidade de parametros e raceline minima. |
| Raceline / minimum-time | [TUMFTM/global_racetrajectory_optimization](https://github.com/TUMFTM/global_racetrajectory_optimization) | Inspirar backlog de raceline, OCP e validacao futura; nao bloquear MVP. |
| LTS educacional | [OpenLAP](https://github.com/mc12027/OpenLAP-Lap-Time-Simulator) | Referencia de decomposicao simples: OpenVEHICLE, OpenTRACK, OpenLAP. |
| Vehicle dynamics | [Project Chrono](https://projectchrono.org/) | Referencia de simulacao multifisica e futura integracao/benchmark, nao dependencia do MVP. |
| Vehicle dynamics C++ | [TUMFTM/Open-Car-Dynamics](https://github.com/TUMFTM/Open-Car-Dynamics) | Referencia de modelagem modular "as detailed as necessary, as simple as possible". |
| Track data | [TUMFTM/racetrack-database](https://github.com/TUMFTM/racetrack-database) | Referencia para tracks, centerlines, widths e racelines derivadas. |
| MDF/MF4 | [asammdf](https://asammdf.readthedocs.io/) | Biblioteca candidata para adapter `asam_mdf` pos-MVP. |
| CAN | [python-can](https://python-can.readthedocs.io/) | Base futura para adapter `can`, hardware-in-the-loop e logging passivo. |
| DBC/ARXML | [cantools](https://github.com/cantools/cantools) | Base futura para decodificar sinais CAN com DBC/KCD/SYM/ARXML. |
| Telemetry UI | [NASA Open MCT](https://nasa.github.io/openmct/) | Inspiracao para visualizacao operacional e composicao de views, nao dependencia inicial. |
| Timeseries UI | [uPlot](https://github.com/leeoniya/uPlot) | Candidato forte para graficos densos de telemetria no frontend. |
| Storage analitico | [Apache Arrow / Parquet](https://arrow.apache.org/docs/python/parquet.html) | Export/arquivo colunar quando volume crescer. |
| Time-series DB | [TimescaleDB](https://github.com/timescale/timescaledb) | Opcao pos-MVP para dados densos por tempo, se Postgres simples deixar de bastar. |

## Standards e formatos

| Standard/formato | Fonte | Decisao SARU |
|---|---|---|
| ASAM MDF/MF4 | [ASAM MDF wiki](https://www.asam.net/standards/detail/mdf/wiki/) | Adapter futuro obrigatorio para logs automotivos robustos. MVP aceita arquivo simples, mas contrato deve prever MDF. |
| ASAM ODS | [ASAM ODS](https://www.asam.net/standards/detail/ods/) | Inspirar modelo de persistencia de teste/medicao; nao implementar ODS completo no MVP. |
| ASAM OpenDRIVE | [ASAM OpenDRIVE](https://www.asam.net/standards/detail/opendrive/) | Referencia futura para geometria de pista e simulacao. |
| ASAM OpenCRG | [ASAM OpenCRG](https://www.asam.net/standards/detail/opencrg/) | Referencia futura para superficie de pista, tire/vibration/driving simulation. |
| ASAM OpenSCENARIO | [ASAM OpenSCENARIO](https://www.asam.net/standards/detail/openscenario/v200/) | Relevante para simulacao de cenarios, mas fora do MVP motorsport performance. |
| DBC/ARXML | [cantools](https://github.com/cantools/cantools) | Contrato de hardware deve aceitar definicao externa de sinais. |
| Parquet | [Apache Arrow Parquet](https://arrow.apache.org/docs/python/parquet.html) | Bom candidato para exports analiticos e datasets versionados. |

## Artigos e livros de lastro

| Tema | Referencia | Uso no SARU |
|---|---|---|
| Minimum lap time | [Minimum-lap-time optimisation and simulation](https://www.research.unipd.it/retrieve/e14fb26e-b9c2-3de1-e053-1705fe0ac030/2021%20-%20Minimum-lap-time%20optimization%20and%20simulation%20PP.pdf) | Fundamentar diferenca entre QSS, modelos transientes e OCP. |
| Tire model | [Pacejka, Tire and Vehicle Dynamics](https://shop.elsevier.com/books/tire-and-vehicle-dynamics/pacejka/978-0-08-097016-5) | Lastro para Magic Formula e claims de pneu. |
| Vehicle dynamics | [Rajamani, Vehicle Dynamics and Control](https://link.springer.com/book/10.1007/978-1-4614-1433-9) | Base para modelos dinamicos e controle veicular. |
| Optimal control tooling | [CasADi OCP blog](https://web.casadi.org/blog/ocp/) | Referencia futura para OCP/raceline; nao dependente do MVP. |
| Architecture diagrams | [C4 Model](https://c4model.com/) | Padrao leve para diagramas de contexto/container/componente. |
| Architecture docs | [arc42](https://arc42.org/) | Referencia para manter docs tecnicos pragmaticos. |
| Product inception | [Lean Inception](https://caroli.org/en/lean-inception-4/) | Workshop base para alinhar MVP, personas, jornada, features e incrementos. |
| Domain discovery | [EventStorming](https://www.eventstorming.com/) | Metodo complementar para eventos de dominio e fronteiras entre BFF, engine e fisica. |

## Decisoes de arquitetura derivadas

1. **Canal canonico antes de integracao ampla.** Antes de MDF, CAN ou hardware,
   o MVP precisa provar que qualquer fonte vira `CanonicalTelemetrySession`.
2. **File adapter primeiro.** ASAM MDF e CAN sao importantes, mas entram como
   adapters pos-MVP para nao atrasar a prova de valor.
3. **QSS como referencia inicial.** TUMFTM e OpenLAP reforcam que QSS/point-mass
   e um caminho legitimo para trend/sensitivity. Claim de validacao por canal
   segue dependendo dos gates de fisica.
4. **UI densa e orientada a pergunta.** Inspiracao de MoTeC/AiM/VBOX indica que
   o produto precisa acelerar leitura tecnica, nao esconder dados atras de cards
   promocionais.
5. **14-DOF beta.** Project Chrono, OCP e modelos transientes indicam direcao,
   mas a fronteira de MVP continua SA + Sim Reference.

## Backlog de pesquisa

| Prioridade | Item | Resultado esperado |
|---|---|---|
| P0 | Definir lista canonica de canais do MVP | Contrato de import, quality flags e unidade por canal. |
| P0 | Mapear math channels de SA | Coasting, braking point, throttle pickup, steering consistency, speed delta. |
| P1 | Avaliar `asammdf` com fixture real | Adapter MDF com fixture e teste. |
| P1 | Avaliar `uPlot` com volta real | Benchmark visual com 50k, 250k e 1M pontos. |
| P1 | Curar pistas de teste | Interlagos/Barcelona com fonte, geometria e tolerancia. |
| P2 | Investigar Parquet/Arrow export | Dataset reprodutivel para treino/analise offline. |
| P2 | Investigar TimescaleDB | Apenas se query densa em Postgres comum virar gargalo. |
| P2 | Desenhar hardware adapter | CAN/serial/MQTT/WebSocket com contrato unico, sem hardware no MVP. |
