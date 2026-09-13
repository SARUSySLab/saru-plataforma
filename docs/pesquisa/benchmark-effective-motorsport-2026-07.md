---
titulo: "Benchmark, Effective Motorsport × SARU Hub"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/product/benchmark-effective-motorsport-2026-07.md"
status: "vigente"
area: "produto"
---

# Benchmark, Effective Motorsport × SARU Hub

> **Status:** análise 2026-07-25, para priorização. **Não é decisão**, verdito vai para ADR.
> **Fonte concorrente:** mapeamento de frontend (11 módulos) capturado em 2026-07-25, > `~/.gemini/antigravity-ide/brain/cf95729d.../effectivemotorsport_frontend_mapping.md`.
> **Base SARU:** [`ARCHITECTURE.md`](../ARCHITECTURE.md) · [`adr/`](../adr/) (0001-0026) ·
> [`matriz-gaps-release-hub.md`](matriz-gaps-release-hub.md) · código em `develop` (`10db6c8`).
>
> **Limite de evidência:** o mapeamento da concorrente é **de frontend**. Rotas e rótulos são
> observáveis; fidelidade de solver, calibração e modelo de dados **não são**. Toda comparação de
> física abaixo compara *nossa implementação verificada* contra *o que a UI deles alega*. Não
> tratar como paridade medida.

---

## 1. Gap analysis módulo a módulo

Legenda: ✅ temos e é real · 🟡 parcial/demo/dívida · 🔴 ausente · ⭐ somos superiores

### 1.1 Planejamento

| Capacidade (Effective) | SARU hoje | Estado | Evidência |
|---|---|---|---|
| Run Sheets (registro de run: pneu, combustível, comentário, problema) | `/trackside` tem os *widgets* (calc de combustível, temp de pneu, notas) mas persiste em **blob JSONB** `user_layouts.layout`, não é registro relacional, não tem histórico, não liga a voltas | 🟡 | `features/trackside/views/TracksideView.tsx` · `user_layouts` |
| Controle/lacre de pneus (conjuntos PL/PR/RL/RR, aprovação) | nada. Só `lts_setups.tire_compound` (escalar de simulação) | 🔴 |, |
| Folha de setup (comparação entre sessões, delta, export PDF) | `vehicles` guarda parâmetros (ADR-0010/0013) e SA tem sub-view `setup/compare` + `SetupSheetWidget`; **sem versionamento por sessão, sem delta, sem export** | 🟡 | `shell.config.ts` MODULE_NAV.sa |
| Checklist pré-etapa / por sessão | nada | 🔴 |, |
| Planejamento de etapa (plano de voltas, km de pneu, pit, tempo restante) | nada | 🔴 |, |
| Comentários de sessão (pré/pós) | notas livres no blob do trackside + `label`/`notes` em `telemetry_sessions` | 🟡 | `history` |
| Lista de problemas (issue tracker por subsistema) | nada | 🔴 |, |
| Relatórios consolidados (fim de semana / setup / pneus) | workbooks do SA são o parente mais próximo (ADR-0020), escopo é análise, não relatório de etapa | 🟡 | `features/workbooks` |
| Calendário de eventos | `championships` + `teams` existem; **não existe evento/etapa/sessão** | 🔴 | `tenancy` |
| Carros e circuitos (cadastro) | `user_cars`, `vehicles`, `tracks.yaml` (catálogo com comprimento e traçado) | ✅ | `library`, `engine/tracks` |

**Diagnóstico estrutural, o gap dominante.** Não é a falta de 8 telas. É a falta de **uma
hierarquia de evento**. Hoje tudo pendura em `telemetry_sessions`, que é *um arquivo importado*,
não uma sessão de pista. Não existe `Evento → Sessão(tipo) → Run`. Sem essa espinha, km de pneu
não tem onde acumular, checklist não tem a que se ligar, vida de peça não tem odômetro e
classificação não tem resultado. **Todos os outros gaps de Planejamento e Oficina são derivados
deste.**

### 1.2 Simulação

| Capacidade | Effective (alegado na UI) | SARU (verificado no código) | Estado |
|---|---|---|---|
| Ponto-de-massa / laptime | "simulação 1D, otimizador de volta", gráficos V-x, RPM, G-G | QSS two-pass Brayshaw & Harrison, `lap_time_solver.py` + `qss_solver.py`; Pacejka + térmico, load sensitivity **k=−0,12 real**, `AeroMap` 3-D, BSFC de combustível, fade térmico de freio; calibrado vs oráculo 992 GT3R | ⭐ |
| Multibody | "Chrono + Pacejka Magic Formula" | 3-DOF transiente real em Python (`dynamics/transient.py`, ADR-0005); **14-DOF vive no `saru-core-jl`, suspenso com retorno programado** (ADR-0024) | 🟡 deliberado |
| Cinemática de suspensão 3D (camber, toe, roll center, motion ratio, bump steer) + viewer WebGL | tem | `SuspensionCorner` (rampas de camber/toe, anti-dive/squat) existe no core; **zero UI, zero relatório de curvas, zero viewer** | 🔴 UI |
| CFD (upload STL/OBJ) | tem | nada | 🔴 (ver §3.3, recomendação é **não** perseguir) |

### 1.3 Dados & Telemetria

| Capacidade | SARU hoje | Estado |
|---|---|---|
| Análise de pilotagem (deltas de velocidade, freio, esterço) | suite completa: `overview`, `driver`, `sectors`, `brake-trace`, `braking-points`, `driver-score`, `math-channels`, `tyres`, `micro-sectors`, `run-chart`, `overlay` com `alignment_method` e `missing_channels` expostos | ⭐ |
| Telemetria multi-fonte (AiM, MoTeC, WinTAX, Cosworth) | 9 datasources com auto-detecção por fingerprint: `.ld/.ldx`, `.xrk`, `.vbo`, CSV iRacing/ACC/AMS2/GT7/`saru_gt7`/WinTAX/PiToolbox. Cosworth `.pds/.drk` adiado | ✅ ⭐ |
| ECU (ingestão de log) | coberto de fato pelo `.ld`/CSV; **não existe rótulo "ECU" nem parser dedicado Bosch/Life** | 🟡 |
| KPIs automáticos (consumo, temperaturas, pressões) | `kpi_engine`: lap time, Vmax, utilização de GG, TAI, BEI, fade, combustível/volta | ✅ |
| Tempos de volta (DB, parciais S1/S2/S3, volta ideal) | `laps` + `reference_laptimes` (classify/benchmarks). **Sem parciais setorizados persistidos, sem volta ideal composta** | 🟡 |
| Live timing (4Sure, Al Kamel LT2) | WS `telemetry-live` (frame/status/lap/sector, single-owner) + gateway GT7 Go. **Sem integração com provedor de cronometragem** | 🔴 |
| Pontuação / classificação (descarte, punição, bônus, lastro) | nada | 🔴 |
| Estação meteorológica IoT | `crm_weather` + widget no trackside, **entrada manual** | 🟡 |

### 1.4 Oficina

| Capacidade | SARU hoje | Estado |
|---|---|---|
| Vida das peças por km acumulado de Run Sheet | nada. `erp_parts` tem `sku/name/stock/min_stock/status`, é estoque, não ciclo de vida | 🔴 |
| Almoxarifado (entradas/saídas, localização física, custo) | `erp_parts` + `erp_orders`; sem razão de movimentação, sem localização, sem custo | 🟡 demo |
| Lista de compras | `erp_orders` (id, sku, qty, eta, status) | 🟡 demo |
| Lista de tarefas (Kanban, responsável, prazo) | nada | 🔴 |

> ✅ **Conflito resolvido em 2026-07-25.** Este parágrafo apontava que a
> [`MVP-BETA-SPEC`](MVP-BETA-SPEC.md) §2 congelava CRM/ERP sem data, bloqueando toda recomendação de
> Oficina. O Vitor descongelou no mesmo dia, decisão registrada em
> [ADR-0030](../adr/0030-descongelamento-crm-erp.md), com mandato estreito (ERP = hub de ativos;
> CRM = só piloto-como-entidade).

### 1.5 Fora de engenharia (registro, não recomendação)

Loja Stripe · assinatura com créditos de IA · Google Drive OAuth para documentação · i18n PT/EN/IT/ES ·
tabela de permissões por membro. SARU tem só `waitlist`. É gap **comercial**, não arquitetural, não entra em V1 nem V2 técnicos.

---

## 2. Diferenciais do SARU

### 2.1 Engine Python + `saru-core`, real e auditável

O que sustenta a afirmação (arquivos, não marketing):

- **QSS two-pass com GGV** (`qss_solver.py`), não tabela de aceleração: seleção de marcha por RPM
  ótimo, transferência longitudinal de carga, curvatura + elevação da pista.
- **Pneu em três níveis** (`vehicle/tires.py`): `LinearTire` (validação) → `PacejkaTire` (Magic
  Formula B/C/D/E) → `ThermalPacejkaTire` (entrada de calor por escorregamento, convecção
  dependente de velocidade, condução para o aro, degradação de μ por parábola em torno de `T_opt`).
- **Load sensitivity real k=−0,12** (`μ_eff = μ·max(0, 1 + k·(Fz−Fz₀)/Fz₀)`), espelhado
  Python↔Julia, dentro da banda de slick GT3 (−0,10…−0,15).
- Calibração declarada: oráculo 992 GT3R, 87,26 s (Python) × 86,87 s (Julia), gap 0,39 s.
- **Fade térmico de freio** por temperatura de disco (modo `ENDURANCE_THERMAL`) e consumo por
  **mapa BSFC**, não por constante l/volta.

Contra um "ponto-de-massa 1D" genérico, a diferença não é a existência do modelo, é que o nosso é
**calibrado contra referência e rastreável por ADR**. Quando um engenheiro perguntar *de onde vem
esse número*, temos resposta com arquivo e linha. Esse é o argumento defensável; "somos mais
precisos que eles" **não é**, não vimos o solver deles.

### 2.2 Borda NestJS, o moat de fato

- Fronteira HTTP única: frontend só fala URL relativa; engine é inalcançável de fora e exige
  `X-Internal-Key` *fail-closed* (503 sem chave).
- **Auth com rotação + reuse-detection** de refresh token por família (ADR-0006/0008), bem acima
  do padrão de um monolito Next com sessão de cookie.
- **DDL de dono único** via migrations versionadas (ADR-0014): schema é código revisável.
- **Jobs em background** (BullMQ + SSE, ADR-0007/0023): simulação pesada não derruba
  telemetria/CRUD, e a UI não pede simulação, o resultado já está lá.
- Consequência: trocar o solver (Python → Julia 14-DOF, ADR-0024) **não toca o frontend**. Um
  concorrente com a simulação acoplada à UI paga esse refactor inteiro.

### 2.3 Correção de premissa, buffer binário `Float32Array` **não existe**

A pergunta do briefing assume que já entregamos telemetria por buffer binário. **Não entregamos.**
Estado verificado: engine serializa canais como **arrays JSON** (`ndarray.tolist()`); `Float32Array`
zero-copy está em [`ARCHITECTURE.md` §3](../ARCHITECTURE.md) como **deferido atrás de gargalo
medido**, junto com o parser Rust e o wrapper Tauri. MinIO segue ocioso.

Não usar essa alegação em pitch, ADR ou landing até existir. O que **é** verdade hoje no caminho de
dados, e já é diferencial: interpolação canônica para `s_common` (2000 pts) com mapeamento de canais
para nomes canônicos, proveniência por `SourceFile`, e store durável de sessão/análise. É isso que
sustenta comparação entre fontes diferentes, que é o problema real do usuário.

---

## 3. Recomendações, V1 × V2

### 3.1 V1, mínimo viável de pista

Ordenado por dependência. **O item 1 é pré-requisito de 2-6.**

| # | Item | Por que agora | Esforço |
|---|---|---|---|
| 1 | **Espinha `Evento → Sessão → Run`**, 3 tabelas novas, `session.type` enum (treino/classificação/corrida/bateria), `run` com voltas, combustível in/out, piloto | destrava tudo abaixo; sem ela nada acumula | M |
| 2 | **Run sheet relacional**, trackside deixa de gravar blob e passa a gravar `runs`. UI permanece; muda a persistência. `telemetry_sessions.run_id` liga a volta importada ao run | vira registro histórico e evidência; é o gap #1 da §1.1 | M |
| 3 | **Conjunto de pneus com lacre + km**, `tyre_sets` (4 cantos, composto, id de lacre) + uso por run; km derivado de `voltas × comprimento_pista` (já temos comprimento em `tracks.yaml`) | valor imediato, zero física | B-M |
| 4 | **Vida de peça por km de run**, instância de componente + **razão append-only** de uso alimentada pelo km do run; alerta por intervalo de serviço | é exatamente o vínculo Run Sheet→Oficina pedido; alto valor percebido, custo baixo | M |
| 5 | **Checklist por sessão**, template + instância com persistência | trivial, uso real no box | B |
| 6 | **Lista de problemas**, issue ligada a run + subsistema, 3 estados | alimenta tarefas depois; barato | B |
| 7 | **Setores persistidos + volta ideal**, gravar parciais e compor volta ideal por sessão | o engine já calcula setores; falta persistir | B |

**Fora do V1, apesar de tentador:** pontuação/classificação (depende de resultado oficial, que o
track day BR não tem, cf. [`oportunidades-track-day.md`](oportunidades-track-day.md) §P4);
almoxarifado completo; estação IoT.

### 3.2 V2, expansão

| Item | Nota |
|---|---|
| **Comparador 3D de cinemática de suspensão** | `SuspensionCorner` já existe no core; falta expor curvas (camber/toe/roll center/motion ratio/bump steer) + viewer WebGL. Casa com o SD e com o retorno do 14-DOF (ADR-0024) |
| **Folha de setup versionada + delta + export** | por sessão, com destaque de mudanças; export é PDF/JSON (ADR-0020 já cobre o padrão de export de workbook) |
| **Integração de live timing** | provedor externo (Al Kamel/MYLAPS/4Sure), só faz sentido no tier de equipe/campeonato, não em track day |
| **Almoxarifado completo** | razão de movimentação, localização, custo, fornecedor. Depende de descongelar ERP |
| **Kanban de tarefas + permissões por membro** | depende de papéis em `teams` (hoje só `owner_id`) |
| **14-DOF multibody** | já decidido, volta como motor do SD via fila (ADR-0024). Nada novo a decidir |
| **Pontuação de campeonato** | descarte, punição, bônus, lastro, quando existir cliente de campeonato |

### 3.3 Recomendação explícita de **não fazer**: CFD

CFD dentro do produto é ou (a) um fino invólucro sobre job OpenFOAM que ninguém da persona P1 sabe
configurar, ou (b) vitrine. Custo de malha, convergência e validação é desproporcional ao valor no
track day, e o `AeroMap` 3-D já dá o que o QSS consome. **Registrar o "não" em ADR**, decisão
negativa também é decisão, e evita que volte a cada benchmark.

---

## 4. Arquitetura proposta

### 4.1 Frontend, sem módulo novo (respeitar ADR-0026)

O erro fácil aqui é clonar a IA da concorrente (`/planejamento`, `/oficina`) e reintroduzir
navegação **por produto**, exatamente o que o [ADR-0026](../adr/0026-ia-por-fase-do-loop.md)
acabou de derrubar. Manter 7 módulos e usar `MODULE_NAV` (`?view=&sub=`, derivado da URL):

| Fase | Rota | `view` novos | Conteúdo |
|---|---|---|---|
| Pista | `/trackside` | `run` \| `tyres` \| `checklist` \| `issues` | run sheet, conjuntos+lacre+km, checklist da sessão, problemas |
| Preparar | `/sfl` (existente) + `/trackside?view=plan` | `plan` | planejamento de etapa (voltas por sessão, alocação de pneu) |
| Evoluir | `/history` | agrupar por **evento/sessão**, não por arquivo | linha do tempo do evento |
| Mais (engenheiro) | `/erp` | `stock` \| `part-life` \| `purchase` \| `tasks` | vida de peça é sub-view do ERP, não módulo novo |

### 4.2 BFF NestJS, módulos e schema

DDL é do BFF via migration (ADR-0014). **O engine não cria nenhuma destas tabelas.**

| Módulo novo | Entidades | Rotas |
|---|---|---|
| `events` | `events` (championship_id, track_id, starts_at, name) · `event_sessions` (event_id, type, planned_laps, starts_at) · `runs` (session_id, driver, laps, fuel_in_l, fuel_out_l, started_at, notes) | `/me/events` · `/me/events/:id/sessions` · `/me/sessions/:id/runs` |
| `tyres` | `tyre_sets` (team_id, compound, seal_code, corners jsonb, retired_at) · `tyre_set_usage` (tyre_set_id, run_id, km, **append-only**) | `/me/tyre-sets` · `/me/tyre-sets/:id/usage` |
| `maintenance` (dentro de `erp`) | `part_instances` (sku, serial, installed_on_vehicle, service_interval_km) · `part_usage` (part_instance_id, run_id, km, **append-only**) | `/me/parts/instances` · `/me/parts/:id/usage` · `/me/parts/due` |
| `checklists` | `checklist_templates` (scope: event\|session) · `checklist_instances` (session_id, items jsonb, completed_by) | `/me/checklists` |
| `issues` | `issues` (run_id, subsystem, state, severity, assignee) | `/me/issues` |

**Alterações em tabela existente:** `telemetry_sessions` ganha `run_id` FK (nullable). Essa é a
junção que a concorrente **não tem** pelo próprio mapa deles, lá Run Sheet e Telemetria são módulos
separados. Ligar o run à volta importada transforma o run sheet de *anotação* em *evidência*: o
tempo registrado à mão passa a ser conferível contra o canal.

**Duas regras não-negociáveis nas tabelas novas:**

1. **Escopo de dono desde a migration.** `user_id`/`team_id` + filtro no service. Não repetir o erro
   de `lts_setups`/`lts_results` e `analysis`, que nasceram sem escopo e viraram **IDOR**
   ([matriz de gaps §2](matriz-gaps-release-hub.md); o de `analysis` fechou em `e32f198`, o de `lts`
   segue aberto). Tabela nova nascendo sem escopo = dívida de segurança criada de propósito.
2. **Uso é razão append-only, nunca contador mutável.** `UPDATE parts SET km = km + x` perde
   auditoria, quebra em concorrência e impede estorno de run cancelado. Km atual é `SUM` da razão
   (materializar depois, se medir gargalo).

### 4.3 ADRs, **escritas e aceitas em 2026-07-25**

| ADR | Título | Escopo da decisão |
|---|---|---|
| [0027](../adr/0027-espinha-evento-sessao-run.md) | Espinha do track day: `Evento → Sessão → Run` como agregado raiz | cria a hierarquia; declara `telemetry_sessions` como *evidência* de um run. **Absorveu** o "run sheet relacional" (era 0030 na proposta), é a mesma decisão, não duas |
| [0028](../adr/0028-vida-util-por-km-de-run.md) | Vida útil de componente por km de run | odômetro **derivado** (`voltas × comprimento de pista`), razão append-only, alerta por intervalo. É a ADR que o briefing pediu nominalmente |
| [0029](../adr/0029-pneu-como-ativo-do-erp.md) | Pneu é ativo do ERP: conjunto com lacre e uso derivado | ciclo de vida do jogo; reusa a razão da 0028. **É o "ADR-B"** que a spec da reforma §7 (removido em 716a258) já devia |
| [0030](../adr/0030-descongelamento-crm-erp.md) | Descongelamento de CRM/ERP | virou ADR (não só emenda de spec): reverte posição declarada em 4 docs, então merece registro rastreável |
| [0031](../adr/0031-cfd-fora-do-produto.md) | CFD fora do produto | decisão negativa (§3.3), com gatilho de reabertura |
|, | **ADR-C**, validade de volta por distância+setores | **segue pendente**, número não alocado (spec da reforma §7 (removido em 716a258)) |

Execução em fatias verticais: `plans/gaps-trackday-espinha-2026-07.md` (removido em 716a258).

---

## 5. Resumo executivo

1. O gap real não são 20 telas, é **uma hierarquia de evento** que não temos. Ela sozinha destrava
   pneu, peça, checklist, problema e relatório.
2. Onde já ganhamos: **física calibrada e auditável** (QSS + Pacejka térmico + k=−0,12 real) e
   **arquitetura de borda** (fronteira HTTP única, auth com rotação, DDL versionado, jobs em fila).
3. Onde a premissa do briefing estava errada: **buffer binário `Float32Array` não existe**, é
   deferido. Não alegar.
4. O que copiar já: vínculo run sheet → km → vida de peça. O que **não** copiar: CFD, loja, IoT de
   clima.
5. ~~Bloqueio a resolver antes de codar Oficina: ERP está **congelado** pela MVP-BETA-SPEC.~~
   **Resolvido no mesmo dia**, [ADR-0030](../adr/0030-descongelamento-crm-erp.md). ADRs 0027-0031
   escritas e aceitas; execução em `plans/gaps-trackday-espinha-2026-07.md` (removido em 716a258).
