---
titulo: "Tarefa 0, Auditoria de código existente (2026-07-25)"
data: "2026-08-22"
origem: "_arquivo/saru-app/docs/audit/TAREFA-0-AUDITORIA-2026-07-25.md"
status: "vigente"
area: "fisica (futuro repo)"
---

# Tarefa 0, Auditoria de código existente (2026-07-25)

> **Origem:** prompt "Plataforma de Telemetria e Simulação Motorsport" (Tarefa 0, identificar
> variantes de modelo de veículo, motores de simulação e módulos legados; decidir manter /
> refatorar / descartar antes de reestruturar).
> **Método:** leitura estática dos 5 repositórios em `HEAD` da branch de trabalho. Nada foi
> executado, onde há afirmação de calibração/número, a fonte é o teste ou o doc citado, não uma
> execução desta sessão.
> **Escopo:** `saru-app`, `saru-physics-py`, `saru-physics-jl`, `saru-telemetry-gt7`, `saru-KB`.
> **Complementa** (não substitui): `docs/audit/UIUX_AUDIT_2026-07-15.md`, §7 abaixo reconcilia.
>
> **Atualização 2026-07-25 (mesma data, pós-reposicionamento de produto):** os três conflitos que
> esta auditoria levantou foram **decididos**, ADR-0023 (simulação em background),
> ADR-0024 (SSoT de veículo interino, com retorno programado ao Julia) e ADR-0025 (gateway GT7
> headless). Ver §9. As seções abaixo mantêm o achado original e apontam para a decisão.

---

## 0. Veredito em um parágrafo

A premissa do prompt de que "tudo está desorganizado e disperso" **não se confirma** no estado
atual do repositório: existe hub modular de 5 produtos, borda NestJS completa com auth e fila,
engine FastAPI com 9 parsers de telemetria reais e solver QSS calibrado. O que de fato falta é
**profundidade em três pontos**, o workbook é um V1 de pilha vertical (não o painel MoTeC-like
especificado), o catálogo de veículos está espalhado por **5 fontes de verdade** sem dono, e
**vídeo, i18n e GGV exposto ao usuário não existem** (zero linhas). O item que mais destoa é o
`saru-telemetry-gt7`: é um segundo front-end, exatamente o anti-padrão que a arquitetura declara
combater. E há **um conflito formal**: o prompt desprioriza o 14-DOF em Julia, mas o ADR-0010
coloca o SSoT de setup veicular *dentro* do repo Julia, decisão vigente que precisa ser
superada antes de qualquer trabalho de catálogo de veículos.

Um quarto ponto, achado depois da primeira redação e igualmente estrutural: **a infraestrutura de
simulação em background existe e não tem consumidor** (§5.1). Como o produto decidiu que simulação
não é tarefa de primeiro plano, essa peça deixa de ser detalhe e passa a ser o caminho principal.

---

## 1. Motores de simulação (7 encontrados)

| # | Motor | Onde | Natureza | Estado verificado | **Veredito** |
|---|---|---|---|---|---|
| M1 | **QSS lap-time** (`_run_ggv_solver`, 2 passadas) | `saru-physics-py/src/saru_core/simulation/qss_solver.py` | GGV ponto-massa | Real, com teste-oracle; calibração 94,228 s @ Interlagos registrada na auditoria de 2026-07-15 | **MANTER, motor prioritário** (alinhado ao prompt) |
| M2 | **QSS `:endurance_thermal`** | mesmo módulo (+ port em `saru-physics-jl/src/simulation/QSS.jl`) | plugin de fade de disco sobre M1 | Envelopa M1 sem editá-lo | **MANTER** |
| M3 | **SD transiente 3-DOF** | `saru-physics-py/src/saru_core/dynamics/transient.py` | bicycle + rolagem, MF/linear | Real; validado vs benchmark Khalil 2018 (`tests/unit/test_khalil2018_roll.py`) | **MANTER**, é o motor do módulo SD |
| M4 | **`analytical` heurístico** | `saru-physics-py/src/saru_core/dynamics/analytical.py` | heurístico | É o **default** de `POST /api/simulate` (`model="analytical"`) | **REFATORAR**, default deve virar `transient3dof`; heurístico fica só como fallback declarado |
| M5 | **14-DOF transiente (Julia)** | `saru-physics-jl/src/simulation/Transient14DOF.jl` | DAE acausal, MTK | Converge honesto a 109,48 s contra oracle 94±1 s; fudges ainda no YAML (cx/cl, torque_cal, derate) | **SUSPENDER com retorno programado**, volta como motor do **SD** classe CarSim/TruckSim/VI-CarRealTime. É decisão de produto, **não** falha técnica ([ADR-0024](../adr/0024-ssot-veiculo-interino.md)) |
| M6 | **QSS ponto-massa (Julia)** | `saru-physics-jl/src/simulation/QSS.jl` + `validation/Harness.jl` | duplicata de M1 em Julia | Baseline de regressão interna (87,26 s) | **MANTER como oracle interno do repo Julia**, nunca expor ao produto (seria 2º QSS) |
| M7 | **"Solver" sintético do frontend** | `services/frontend/src/features/lts/model.ts` (`generateTelemetry`, `computeAero`, `computeTireThermo`) | fórmulas de display + `Math.random()` | Roda no browser, produz telemetria e aero/térmica que **parecem** físicas | **DESCARTAR**, física falsa na UI é o pior tipo de dívida num produto de engenharia |

**Achado M7 (grave).** `model.ts` calcula pressão a quente, mapa aero e círculo de atrito com
fórmulas próprias e gera telemetria com ruído aleatório. Os comentários no arquivo já admitem
"display-only; not sent to the solver", mas o usuário não vê essa distinção na tela. Ou vira
um solver real (chamada ao engine) ou some. Não existe terceira opção honesta.

**Achado M4.** O router `/api/simulate` documenta que o mock foi removido, mas o default do
`SimRequest` continua `analytical`. Na prática o caminho feliz do SD ainda é heurístico.

---

## 2. Variantes de modelo de veículo (5 fontes de verdade)

| # | Fonte | Conteúdo | **Veredito** |
|---|---|---|---|
| V1 | `saru-physics-py/src/saru_core/vehicle/parameters.py` | 4 presets **em código**: `porsche_911_gt3_r_992`, `mclaren_720s_gt3_default`, `porsche_911_gt3_cup_991`, `truck_diesel_default` | **MANTER como implementação**, **DESCARTAR como catálogo**, é o que `lapsim_service.VEHICLE_PRESETS` expõe hoje |
| V2 | `saru-physics-py/data/vehicles/*.yaml` | 5 arquivos: `992_gt3_r`, `corolla_cross`, `eclipse_cross`, `sng01_base`, `tracker` | **MANTER → promover a catálogo canônico** (é o único formato de dado, não de código) |
| V3 | `saru-physics-jl/reference/` | `vehicle_992_gt3_r.yaml` + `gt3_992_seed.tir` + `aero_maps/` | **CONGELAR** junto com o 14-DOF |
| V4 | `services/frontend/src/features/lts/data.ts` → `VehiclePreset` | Presets hardcoded na UI com massa, entre-eixos, h_cg, Cd, Cl, área frontal, potência, categorias `GT3 \| Formula \| Truck` | **DESCARTAR**, 4ª descrição do mesmo carro, não alimenta solver nenhum |
| V5 | `vehicles` (Postgres), `services/api/src/vehicles/entities/vehicle.entity.ts` + `DEFAULT_VEHICLES` no engine | Parâmetros físicos por carro, é onde o carro **do usuário** mora | **MANTER → é o destino** |

**Consequência.** Um "Porsche 992 GT3 R" existe hoje em **quatro** descrições independentes
(V1, V2, V3, V5) e um quinto carro genérico na UI (V4). A engenharia reversa de parâmetros a
partir de telemetria, pedida no prompt, **não tem onde escrever** enquanto não houver um dono
único. É o pré-requisito bloqueante de "cada nova volta retroalimenta o banco de modelos".

**Conflito formal com decisão vigente, RESOLVIDO por [ADR-0024](../adr/0024-ssot-veiculo-interino.md).**
O **ADR-0010** define que o SSoT de setup veicular mora em Julia (`saru-physics-jl`, módulo
`VehicleSetup.jl`) e que o tier rápido é **gerado** a partir dele. O prompt desprioriza o Julia.
As duas coisas não coexistiam: com o 14-DOF congelado, o SSoT ficaria num repo parado.

A resolução **não foi mover o SSoT em definitivo**. O Julia não foi descartado, foi reposicionado, volta como motor do produto **SD (Saru Dynamics)**, classe CarSim/TruckSim/VI-CarRealTime, e
nessa configuração torna a ser o dono natural do superconjunto de parâmetros. Mover em definitivo
para o Python seria ida e volta. O ADR-0024 portanto:
- torna V2 (`saru-physics-py/data/vehicles/*.yaml`) o **catálogo canônico interino**;
- rebaixa V1 de catálogo a implementação e **remove V4** (a UI não descreve veículo);
- mantém V5 (Postgres) como **instância do usuário**, não catálogo;
- **preserva a estrutura do formato** para acomodar campos que só o 14-DOF usa, de modo que o
  retorno não exija reescrever o YAML;
- fixa um **gatilho de retorno**: quando o SD entrar como produto de dinâmica veicular, o SSoT é
  reavaliado por ADR novo com o Julia como candidato primário.

O ADR-0013 (JSON-Schema-only) permanece integralmente válido.

---

## 3. Módulos legados citados no prompt

### 3.1 ERP, **existe, é demo, manter congelado**
- Frontend: `features/erp/views/ErpView.tsx` (+ CSS module).
- BFF: `services/api/src/erp/` completo (module, service, controller, DTOs, `erp.entities.ts`).
- Estado: dados semeados, sem fluxo real de compra/estoque. ADR-0009 já decide que CRM/ERP vivem
  na borda NestJS.
- **Veredito: MANTER CONGELADO.** Fora do caminho crítico do beta. Não refatorar agora, o custo
  não retorna feedback de piloto.

### 3.2 CRM, idem ERP
`features/crm/` + `services/api/src/crm/`. Demo. **MANTER CONGELADO.**

### 3.3 Academy, **NÃO EXISTE**
Zero código. A palavra aparece em exatamente 2 arquivos, ambos documentos
(`docs/research/2026-07-aquisicao-de-dados.md`, `docs/audit/UIUX_AUDIT_2026-07-15.md`).
- **Correção ao prompt:** Academy não é um módulo legado a reaproveitar, é **greenfield**.
- O embrião real já existe e tem outro nome: `features/sa/views/sections/SaDriver.tsx` (436 linhas, score de confiança, TBI, análise de brake trace por zona, já usa os `corners` de `tracks.yaml`),
  mais a especificação do **SARU Skill Score** em `UIUX_AUDIT_2026-07-15.md` §6 (6 skills, ganho
  estimado em segundos por skill, frase em PT).
- **Veredito: CONSTRUIR sobre `SaDriver`**, não do zero e não como módulo separado no MVP.

### 3.4 Lap Time Simulator (LTS), **existe em 3 camadas, refatorar a de cima**
| Camada | Onde | Estado |
|---|---|---|
| UI | `features/lts/`, 5 views (`Simulator`, `Setup`, `DataAnalysis`, `TrackBuilder`, `WorkspaceFrame`) + `data.ts`/`model.ts`/`store.ts` | Simulator já manda `vehicle_preset` real ao engine; `model.ts` é M7 (falso) |
| Serviço | `services/telemetry-api/.../application/lapsim_service.py` + `api/routers/lts.py` | Fronteira fina real sobre o saru-core |
| Física | M1 (QSS) | Real |
- **Duplicação SD ↔ LTS:** `LtsTrackBuilderView` e `SdTrackBuilderView` são dois construtores de
  pista; `SdVehicleEditorView` edita veículo sem alimentar o LTS. **REFATORAR: um só Track Builder.**
- **Veredito: MANTER serviço e física; REFATORAR a UI** (matar `model.ts` sintético, unificar
  Track Builder) e **integrar como função do workbook**, como pede o prompt, não como tela isolada.

### 3.5 Workbook, **existe, é V1, é o alvo da fatia (c)**
`features/workbooks/`, `registry.tsx` (catálogo de 8 widgets, 2 deles stubs "Em Desenvolvimento"),
`templates.ts` (5 templates: blank / piloto_amador / piloto_pro / eng_amador / eng_pro),
`views/WorkbookView.tsx` (213 linhas). Persistência real via `PUT /me/layouts/:key` →
tabela `user_layouts` (JSONB, único por usuário+chave). Rotas `/sa/workbooks` e
`/sa/workbooks/[slug]` existem.
- **Veredito: MANTER a espinha (registry + templates + persistência), SUBSTITUIR o renderizador.**
  A camada de dados está certa; o layout é que é uma pilha vertical.

### 3.6 Módulos não citados no prompt, mas existentes
`library` (378 linhas), `history` (336), `trackside` (run sheet com combustível/clima/pneus),
`sim-accounts` (contas de GT7/iRacing do usuário no BFF), `laptimes` (classificador de tempos de
referência). **MANTER**, `library`/`history` são exatamente a persistência que o prompt pressupõe
("cada volta retroalimenta o banco"). Nota: nenhum dos três aparece em `MODULE_NAV`/`MODULES` do
`shell.config.ts`, existem como rota, mas não têm entrada no rail. Dívida de descoberta.

---

## 4. Workbook: especificação do prompt × realidade

| # | Requisito do prompt | Estado hoje | Gap |
|---|---|---|---|
| W1 | Painéis redimensionáveis por drag nas bordas, sem grid travado | Pilha vertical (`flexDirection: column`), ordem por botões ↑/↓ | **Total**, nenhuma lib de resize nas dependências |
| W2 | Fullscreen restrito à área do workbook | Inexistente | **Total** |
| W3 | Clique no canal → propriedades rápidas inline (cor, escala, sobreposição) | Inexistente, widget é caixa-preta, sem seleção de canal | **Total** |
| W4 | Mapa de pista com zoom/pan sincronizado com gráfico e vídeo | `SaTrackMap.tsx` (171 linhas) renderiza, sem zoom, sem sync | **Alto** |
| W5 | Toggle eixo X distância/tempo em 1 clique (MoTeC i2) | Eixo fixo em distância (`s_common`) | **Médio**, o dado de tempo já vem do engine |
| W6 | Templates por perfil, editáveis ou do zero | **Feito**, 5 templates + `blank`, persistidos por usuário | ~Nenhum |
| W7 | Marcadores sincronizados pista + dado + vídeo | Inexistente; não há cursor compartilhado entre widgets | **Total** |

**Nota técnica que decide a fatia (c):** a única lib de gráfico é `recharts@^2.15.3` (SVG). Para
cursor sincronizado sobre telemetria a 20-100 Hz com múltiplas voltas sobrepostas, SVG vira
gargalo na casa de poucos milhares de pontos. **Decisão a tomar antes de codar o workbook**:
manter recharts com downsampling agressivo (rápido, teto baixo) ou introduzir renderização em
canvas para os traces (custo maior, é o que a especificação MoTeC-like pede). Recomendação:
canvas só para o trace principal, recharts fica no resto.

---

## 5. Gaps duros, zero código hoje

| Gap | Evidência | Impacto no prompt |
|---|---|---|
| **Vídeo** | `grep -ri "video"` em `services/` → **0 ocorrências** | W4/W7 e o `websocket-engineer` do prompt são greenfield completo |
| **i18n** | Sem `next-intl`/dicionário; nenhum arquivo de tradução. Strings PT e EN **misturadas no código** ("Speed Trace", "LAP SUMMARY", badge "A1 ACTIVE" ao lado de "Nenhuma sessão ativa") | Restrição "UI 100% PT-BR com estrutura i18n pronta" **não é atendida**, e não é só traduzir, é extrair |
| **GGV exposto** | O envelope existe no solver (`qss_solver.py`), mas nenhuma rota/UI o expõe | "refinar o envelope GGV" pede visualização do envelope; hoje não há por onde |
| **Engenharia reversa de parâmetros** | Nenhum módulo de estimação de parâmetros a partir de telemetria | Item explícito do prompt, 100% novo, e bloqueado pelo §2 (sem SSoT, não há onde gravar) |
| **Validação cruzada 4 fontes** | Parsers existem para GT7, iRacing, ACC, AMS2 + reais (AiM/WinDarab/WinTAX/`.ld`/`.xrk`), **9 datasources**. O que falta é o comparador entre fontes | Meio caminho andado; falta a camada de cima |

### 5.1 Simulação em background, infraestrutura pronta, sem consumidor

Achado posterior à primeira redação, e o mais acionável de todos:

- `services/api/src/simulation-jobs/` tem **fila BullMQ registrada** (`simulation-jobs`, job
  `solve-lap`, `simulation-jobs.service.ts:37`) e **stream SSE**
  (`@Sse('stream/:jobId')`, `simulation-jobs.controller.ts:40`). Produtor e canal de retorno
  estão construídos.
- **Nada consome a fila.** O próprio frontend documenta em `lib/api.ts:550`: *"hoje não há consumer
  de 'simulation-jobs'"*, e cai no solver síncrono da borda.
- O consumidor previsto era o `RedisWorker` em Julia, justamente o que sai de prioridade.
- O `ARCHITECTURE.md` §2 lista `sim-worker` como "futuro"; na prática é a **única peça faltando**
  para a fila existente render.

**Por que isso mudou de peso:** a decisão de produto (2026-07) é que **simulação não é tarefa de
primeiro plano**, o piloto não abre a ferramenta para simular, abre para entender a volta que
acabou de rodar; o resultado da simulação tem de já estar lá. Isso move o QSS do regime síncrono
para o assíncrono na jornada do usuário. **Resolvido por [ADR-0023](../adr/0023-simulacao-em-background.md)**:
implementar o consumidor Python da fila que já existe, sem infra nova.

---

## 6. `saru-telemetry-gt7`, decidido por [ADR-0025](../adr/0025-gateway-gt7-headless.md)

Gateway em **Go** que recebe UDP do PS4/PS5 (portas 33739/33740), parseia, e serve
**painel web próprio** em `web/` na porta 8080, com SQLite e exportação CSV.

- **Achado:** é um **segundo front-end**, o anti-padrão que `saru-physics-py/CLAUDE.md` §2 nomeia
  explicitamente ("um produto, uma borda, um front-end, nunca criar front-ends/serviços paralelos").
- **Integração atual com o produto: nenhuma em tempo real.** O caminho hoje é offline, exportar
  CSV e subir no SA (`sim_gt7_csv.py` no engine).
- **Veredito: REFATORAR para headless** (ADR-0025). O gateway vira produtor de dados (UDP →
  ingestão do BFF/engine); o painel `web/` sai do produto e fica **só como ferramenta de
  diagnóstico local**, com o README dizendo isso explicitamente. Beta tester de GT7 (o caso do
  Luiz) é justamente quem sofre com dois painéis. Ingestão em tempo real = follow-up pós-beta;
  o beta usa importação de arquivo.

---

## 7. Reconciliação com a auditoria UI/UX de 2026-07-15

Reverificado nesta sessão, no código atual:

| Achado | Situação hoje |
|---|---|
| P0-1 chip = logout seco | **Fechado**, `TopBar.tsx` tem `menuOpen` + menu |
| P0-2 landing = analyzer legado | **Fechado**, `(public)/page.tsx` é landing com personas e CTA (228 linhas) |
| P0-3 `/home` vazio | **Fechado**, hub home com módulos e dados recentes (156 linhas) |
| P0-4 unidade de pedal ACC | **Parcial**, normalização existe em `trackDayReport.ts:66`, **não** nos charts; a fronteira canônica ainda não é imposta |
| P0-5 logout fantasma | **Fechado**, `AuthContext.tsx` distingue 401 e faz retry |
| P0-6 sessão efêmera | **Fechado**, `library` + `history` + `laptimes` no BFF |
| P1-1 LTS sem escolha de carro | **Fechado**, `LtsSimulatorView` manda `vehicleId` |
| P1-2 ViewTabs global mentirosa | **Fechado**, `MODULE_NAV` por módulo em `shell.config.ts` |
| P1-9 busca placebo (⌘K) | **Aberto** |
| P1-4 track map sem GPS | **Aberto**, relevante para W4 |
| P1-5 score sem ação | **Aberto**, é o ponto de partida do Academy (§3.3) |

Ou seja: a dívida de **jornada** foi paga; a dívida de **profundidade analítica** (busca, mapa,
score acionável, workbook) é a que resta, e é exatamente o que o prompt pede.

---

## 8. Resumo dos vereditos

**Descartar (4):** `features/lts/model.ts` como física (M7) · `VehiclePreset` do frontend (V4) ·
painel web do `saru-telemetry-gt7` · um dos dois Track Builders (SD/LTS).

**Refatorar (5):** renderizador do workbook (manter registry/templates/persistência) ·
default de `/api/simulate` → `transient3dof` · gateway GT7 → headless · catálogo de veículos →
fonte única (V2 promovido, V1 vira implementação) · extração de strings para i18n.

**Manter (o núcleo):** QSS (M1/M2) · SD 3-DOF (M3) · engine FastAPI + 9 datasources · BFF NestJS
(auth, fila, layouts, library, history, laptimes, sim-accounts) · hub modular e AppShell ·
templates de workbook · `SaDriver` como semente do Academy.

**Suspender com retorno programado:** 14-DOF Julia (M5) + `reference/` (V3), voltam com o SD.
**Congelar sem data:** ERP · CRM.

**Construir (peça pequena, efeito grande):** consumidor Python da fila `simulation-jobs` (§5.1).

---

## 9. Conflitos levantados e como foram resolvidos

| Conflito | Resolução | Onde |
|---|---|---|
| SSoT de veículo no repo Julia (ADR-0010) × Julia fora de prioridade | SSoT **interino** no `saru-physics-py` (YAML), com formato preservado e **gatilho de retorno** ao Julia quando o SD virar produto. Não é supersessão definitiva | [ADR-0024](../adr/0024-ssot-veiculo-interino.md), supera ADR-0010 §1/§2 |
| Simulação em primeiro plano × "não adianta para piloto/engenheiro, tem que rolar em background" | QSS migra do regime síncrono para o assíncrono na jornada; consumidor Python fecha a fila BullMQ+SSE já existente; rota síncrona permanece como fallback declarado | [ADR-0023](../adr/0023-simulacao-em-background.md), reposiciona ADR-0007 |
| Painel web do gateway GT7 × regra "um produto, um front-end" | Gateway vira **headless**; painel fica só como diagnóstico de bancada | [ADR-0025](../adr/0025-gateway-gt7-headless.md) |
| Física falsa no browser (`features/lts/model.ts`) × produto de engenharia | Remoção, não conserto. Vira chamada ao engine ou some | §1 M7 · backlog F2-1 |
| Dois Track Builders (SD/LTS) · `VehiclePreset` na UI · default heurístico do `/simulate` | Itens de higiene, sem ADR, decisão já implícita nas regras vigentes | backlog F2 |
| "Academy é módulo legado a reaproveitar" (premissa do prompt) | Não existe: é greenfield, e nasce como profundidade do SA sobre `SaDriver.tsx` | §3.3 |
| Ordem de trabalho: profundidade (workbook) × largura (hub inteiro) | **Largura primeiro**, decisão de produto 2026-07-25 | `MVP-BETA-SPEC.md` §6 |

Nenhum conflito permanece aberto como bloqueio. O que resta são decisões técnicas de execução
(renderização de trace, escopo de i18n), registradas como decisões em aberto na spec.
