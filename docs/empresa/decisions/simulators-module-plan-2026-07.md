---
titulo: "Módulo de Simuladores do SARU, Plano Mestre"
data: "2026-08-19"
origem: "_arquivo/saru-app/docs/plans/simulators-module-plan-2026-07.md"
status: "obsoleto"
area: "produto"
---

# Módulo de Simuladores do SARU, Plano Mestre

> Escopo: o produto voltado ao mercado (hub de sim racing) sobre a arquitetura BFF-borda-única já ratificada.
> Fundamentação: `docs/research/competitive-sim-telemetry-2026-07.md` + código do repo (services/api, services/telemetry-api, services/frontend, vendor/saru-telemetry-gt7).
> Direção herdada: ADR-0002 (borda BFF + engine Python), ADR-0007 (BFF orquestra cálculo), ADR-0014 (DDL dono do BFF), ADR-0015 (gt7 microserviço poliglota). ADRs novos: 0016-0019.
> Última síntese: 2026-07-18.

## 1. Tese e diferencial

O mercado está partido entre análise crua (MoTeC, Garage 61, Racelab, SimHub, SRT, não recomendam nada) e AI-coaching em expansão (Track Titan, trophi.ai, Coach Dave, Full Grip, RaceCrewAI). **Todos os coaches dizem o QUE mudar por correlação com uma volta-referência; nenhum explica o PORQUÊ em dinâmica veicular** (pesquisa §3.1). Esse é o espaço aberto que o motor de física do SARU (14-DOF, load sensitivity k=−0,12, elipse de atrito, oráculo 86.18/99.36) ocupa. Somado a isso, o console é quase greenfield (quase tudo é PC-Windows-only) e o SARU já tem a ponte GT7.

**Posicionamento (pesquisa §5):** "O coach de sim racing que explica o PORQUÊ, fundamentado em física real, do Desktop ao console." Quatro pilares: coaching causal (não correlacional); credibilidade científica (física validada, não pedigree de piloto); cobertura Desktop + console real; setup engineer preditivo por física.

**Princípio de projeto:** não inventar. Cada faceta é reuso do que já existe, o schema canônico (domain.Sample / export.csv), o /lap-data com source_override, o proxy fino do Gt7Service, os jobs BullMQ+SSE do simulation-jobs, e os primitivos causais que o SA analyzer já produz.

## 2. As quatro facetas

### 2.1 Ingestão multi-fonte (ADR-0016)

Generaliza o padrão gt7 (gateway Go local-first + módulo BFF proxy + perfil de aliases) numa camada de N sims sobre **dois arquétipos**, ambos falando o mesmo **Sim Capture Gateway API** (o contrato HTTP que o `internal/httpapi/server.go` já expõe: `/api/status`, `/api/laps`, `/api/source/start|stop`, `/api/laps/{id}/export.csv`):

1. **UDP-push LAN poliglota**, GT7 (feito), F1 (porta 20777, spec oficial EA/Codemasters), Forza (porta 5607, Data Out), AMS2 (opcional). Um único binário `saru-telemetry-udp` evoluído do `saru-telemetry-gt7`, com o decoder de pacote abstraído atrás de uma interface `Driver{Run(ctx,cfg,emit), DefaultPort, ID}`. O esqueleto (`engine.go` accept/store/hub/session + `httpapi` + `stream.Hub`) é 100% reusado; só o decoder é novo por sim. Cobre as 3 famílias de console só com protocolos oficiais (zero RE novo, o RE só resta no GT7/Salsa20).
2. **Windows shared-memory**, ACC/iRacing/rF2-LMU/R3E (não fazem UDP-push; expõem mmap só no Windows). Agente Windows local-first (`saru-telemetry-agent-win`) que traduz mmap -> domain.Sample e expõe o MESMO contrato. Variante recomendada: agente fino .NET -> push loopback no formato saru_v1 -> instância do gateway Go (reuso máximo de um só esqueleto de servidor). Fase separada (lift real fora do Go).

No BFF, `services/api/src/gt7/` evolui para `services/api/src/sims/` com rotas `/api/v1/sims/:sim/*` e um `SimRegistry` (sim -> {arquétipo, gatewayEnvKey, engineProfile, platforms, defaultPort}). `Gt7Service` vira `SimGatewayService` parametrizado por `:sim`, herdando `rethrow`/`decodeUpstreamDetail`/502-gracioso/`exportLapCsv` verbatim. No engine, cada sim é um perfil `saru_<sim>` no `aliases.yaml` herdando o baseline `saru_v1`, nenhum datasource Python novo obrigatório, porque o gateway já emite o CSV canônico e o `/lap-data` já honra `source` (Form, `sessions.py`). **A ponte captura->SA passa `source=SIM_REGISTRY[sim].engineProfile` explícito**, o que corrige de passagem uma fragilidade real do gt7 atual: o `gt7.controller.ts:analyzeLap` NÃO passa `source`, dependendo de `detect_sim` por colunas, que deixa de ser determinístico quando F1 e Forza compartilham o header base saru_v1.

`SimType` (GT7/ACC/IRACING) estende para F1/FORZA/AMS2/RF2/R3E via migration TypeORM (DDL dono do BFF, ADR-0014); o `settings jsonb` já modela IP/porta por sim. Back-compat: `/api/v1/gt7/*` como alias fino delegando a `sim='gt7'` por 1 release.

**Matriz (pesquisa §2.1):** GT7 (feito), F1 (agora #1, cobre PS+Xbox+PC), Forza (agora #2, único caminho Xbox), AMS2 (bônus); ACC/iRacing/rF2/R3E depois via agente Windows. Armadilha documentada: ACC de console NÃO emite telemetria, surfacear `platforms` do registry em `GET /api/v1/sims`.

### 2.2 Motor de recomendações causais, SARU Coach Engine (ADR-0017)

Camada de **derivação** sobre o `FullAnalysisResult` já cacheado no store do engine, zero recomputação, fora do hot-path de 60Hz. Os primitivos causais já saem de `run_full`:

| Primitivo | Onde já existe | O que habilita |
|---|---|---|
| Perda por curva ranqueada | `driving_insights: list[CornerInsight]` (já sorted por total_time_loss) | eixo "por segundos perdidos" (pesquisa §4 #2) |
| Perda por fase (BRAKING/ENTRY/APEX/EXIT) | `CornerInsight.phases[].time_delta` | localiza o erro na curva |
| Elipse de atrito | `MathChannelsReport.grip_factor` (cornering/braking/accel pct = G_sum/(mu*g)) | o "porquê" causal, física real |
| Slip angle / slip ratio | `slip_angle_deg`, `wheel_slip_ratio` | mecanismo de deriva |
| Ponto de freio vs ref | `braking_points[].delta_to_ref_m` | "freou X m cedo/tarde" |
| Trail-brake/over-slow/coasting | `BrakeTraceReport.zones[]`, `compute_trailbraking_index()` | diagnóstico de técnica |
| Contrafactual de lap-time | `lapsim_service.run_lap`, `build_setup_sweep`, `simulate.py` transient | quantificar recuperação (Tier-1) |

**Contrato central `CoachingEvent`:** `{corner, phase, channel, delta, time_loss_s (chave de ranking), instruction{novice,engineer}, why_physics{novice,engineer}, evidence[], confidence, tier, predicted_gain_s?, voice_text}`. Dois campos de persona por evento (não dois payloads), o toggle novato<->engenheiro é troca de campo, um fetch, zero re-render. `voice_text` por template no mesmo passo (TTS-ready, pesquisa §4 #10) sem retrabalho futuro.

**Tier-0 (AGORA):** `RecommendationEngine.derive` (Python puro, sem I/O) itera os CornerInsight ranqueados e casa assinaturas de métricas já computadas com instruction + why_physics + evidence. Já entrega causalidade `confidence='measured'` via grip_factor (física real, resolve o "genérico para experts" da pesquisa §3.1 sobre o estado real do carro do piloto). Rota `GET /api/v1/analysis/{id}/coaching?persona=&tier=0`; passthrough no `AnalysisController`. Fallback para as `lossZones` de 4 setores (`trackDayReport.computeLossZones`) quando a pista não tem corners (caso GT7), degrada com `phase=SECTOR, confidence=heuristic`, nunca fabrica.

**Tier-1 (DEPOIS):** job BullMQ+SSE (clona `simulation-jobs`) que, para os top-N corners de maior time_loss_s, orquestra o saru-core (`run_lap` / `simulate transient3dof` / `build_setup_sweep`), preenche `predicted_gain_s` e valida o fix dentro da elipse (`confidence='physics_validated (interim)'`). O `simulate.py` já faz `asyncio.to_thread`, a física nunca bloqueia o event loop. Variante Setup Engineer (gap adjacente §3.2): prevê o efeito de wing/pressão/bias no lap-time e explica, em vez de lookup de database.

Guardrail de honestidade (já é cultura do repo, `trackDayReport.provenance`): todo evento carrega `confidence`; a UI rotula medido / validado por física (interim 86/99) / heurístico. Nada de cronômetro oficial. LLM só reescreve `why_physics` em NL no debrief (§2.3), nunca gera o evento estruturado.

### 2.3 Camada de IA via OpenRouter (ADR-0018)

Novo módulo `services/api/src/coach/` no BFF, a **única** porta para o OpenRouter (proxy fino cópia estrutural de `EngineService`, chave só no env do BFF, atrás de `JwtAuthGuard`). Não no engine (mantém o núcleo Python determinístico/testável sem rede não-determinística) nem no frontend (não vaza chave, preserva borda única ADR-0002).

**Anchor-first:** o LLM NUNCA vê os 60Hz crus. Consome só as conclusões estruturadas (`FullAnalysisResult` via `/api/v1/analysis/{id}/*` + `TrackDayReport`), que o `AnchorBuilder` monta em `CoachAnchors` (só escalares/labels, piloto pseudonimizado). O LLM só traduz/formata/explica o "porquê".

**Guardrail de 2 camadas contra alucinação numérica:** (a) prompt com `<anchors>{JSON}</anchors>` + regra dura "só cite números presentes nas âncoras"; (b) `AnchorGuard` determinístico pós-geração que extrai tokens numéricos e valida contra o conjunto de âncoras (tolerância + allowlist de ordinais), número órfão -> rejeita/repara/loga. `provenance` obrigatória (herda a frase do TrackDayReport).

**Três agentes** (Race Engineer / Driving Coach / Setup Engineer) com prompt versionado e tier de modelo próprios via roteamento OpenRouter (`COACH_MODEL_FAST`/`COACH_MODEL_STRONG`), mapeia P1/P2/P3 e a decomposição multi-agente que a pesquisa §3.3 aponta (RaceCrewAI, Simulator-Controller).

**MVP:** `POST /api/coach/debrief` -> job BullMQ+SSE (reusa `simulation-jobs`) -> `CoachDebrief` (Zod), cache idempotente por `analysis_id+anchors_hash`; o `TrackDayReport` determinístico é o fallback offline garantido. Text-only, PT-BR. **Futuro:** `POST /api/coach/ask` (Q&A + memória cross-session via `driver_profile`/`coach_thread`/`coach_message`, DDL dono do BFF, `consent_ai` p/ LGPD), Setup Engineer preditivo, voz/TTS sobre os corner_cards estruturados.

### 2.4 Frontend, módulo garage + LIVE/REVIEW (ADR-0019)

Um 6º `ModuleId` **`garage`** entra no rail como a casa de captura/fontes/voltas (o **produtor** de telemetria), distinto da SA (o **consumidor** que lê `activeTelemetryData`). Escolhe-se `garage` (metáfora da Biblioteca, neutro entre P1/P2/P3) e não estender a SA (poluiria o analyzer com estado de captura) nem `sims` no frontend (soletra implementação; reservado ao módulo BFF). O handoff garage->SA reusa `setActiveTelemetryData` (mesmo caminho de `runLapSimAsSession` do LTS).

**Duas superfícies SEPARADAS** (pesquisa §4 #6, restrições incompatíveis, não CSS responsivo): **REVIEW** = garage + SA dentro do shell `(hub)` (denso, comparativo, track-map bidirecional, cards ranqueados, debrief IA); **LIVE** = route-group novo `(live)/live` FORA do AppShell (fullscreen in-cockpit, near-black, sem rail/topbar, sob AuthContext). ⚠️ `ModuleId` é hardcoded em 3 pontos, `shell.config.ts`, `(hub)/layout.tsx` `validModules`, `tokens.css`, os três no mesmo commit sob pena de módulo em branco.

**Padrões de UX ratificados (pesquisa §4):** track map = índice espacial bidirecional (store `saSelection` {hoveredCorner, selectedCorner, cursorS}; três assinantes: mapa/traces/cards; usa corner.s_start/s_end de /tracks); cards ranqueados por segundos perdidos (nunca cronológico; hero + resto); toggle novato<->engenheiro (estado Zustand, não muda a query); cores por canal tokenizadas (`--ch-throttle`=verde, `--ch-brake`=vermelho, etc., idênticas em trace/mapa/card); biblioteca de voltas-referência com overlay de ghost (moat).

## 3. Roadmap faseado

| Fase | Objetivo | Esforço |
|---|---|---|
| **1. Fatia vertical GT7 + fundação garage** | Fechar o gap órfão (endpoints /api/v1/gt7/* sem consumidor). Zero mudança engine/BFF. | M |
| **2. Coach Engine Tier-0** | Coaching causal 'measured' via grip_factor sobre o FullAnalysisResult. O diferencial, MVP. | L |
| **3. Ingestão UDP N-sims (gt7->sims + F1 + Forza)** | Cobrir as 3 famílias de console com protocolos oficiais. | XL |
| **4. IA OpenRouter (debrief textual)** | Verbalizar o 'porquê' com guardrail anti-alucinação. | L |
| **5. LIVE HUD + Tier-1 contrafactual + biblioteca de referência** | Superfície in-cockpit + coaching quantificado + moat de ghosts. | L/XL |
| **6. Agente Windows (ACC/iRacing) + memória do coach** | Trio PC alta-fidelidade + coaching que evolui. | XL |

A **Fase 1** é a prioridade zero: os endpoints existem e `analyzeLap` já devolve o `LapDataResponse` que a SA consome. Fechar o loop `start(demo) -> status -> laps -> analyze -> setActiveTelemetryData -> /sa` prova a ponte captura->análise autenticada end-to-end e vira a demo vendável, sem tocar engine/BFF.

## 4. Scaffold imediato (Fase 1)

**Editar:** `lib/api.ts` (client gt7: getGt7Status/getGt7Laps/startGt7Capture/stopGt7Capture/analyzeGt7Lap); `lib/shell/shell.config.ts` (ModuleId += 'garage' + MODULES + MODULE_NAV.garage); `app/(hub)/layout.tsx` (validModules += 'garage'); `app/tokens.css` ([data-module=garage] accent violeta + tokens de canal).

**Criar:** `app/(hub)/garage/page.tsx` (dispatcher por activeView); `features/garage/views/GarageSourcesView.tsx` (capturar Demo, trata 502, Demo padrão); `features/garage/views/GarageLapsView.tsx` (laps ranqueadas -> Analisar -> SA); `features/garage/views/GarageReferenceView.tsx` (placeholder); `features/garage/hooks/useCaptureStatus.ts` (polling).

**Verificação:** `npm run type-check`; validar o loop demo end-to-end; regressão visual da SA intacta (refator de SaTrackMap/SaDriver é Fase 2, não Fase 1).

## 5. Reuso máximo (mapa)

- **Esqueleto Go** (engine.go accept/store/hub/session/httpapi), 100% reusado; só o decoder é novo por sim.
- **domain.Sample + export.csv**, já é o schema saru_v1; estende com campos opcionais por ponteiro.
- **Gt7Service** (rethrow, decodeUpstreamDetail, 502 gracioso, exportLapCsv), vira SimGatewayService por :sim.
- **EngineService.postForm + /lap-data source Form**, reusado sem mudança; só perfis novos no aliases.yaml.
- **simulation-jobs (BullMQ+SSE)**, template para coaching-jobs (Tier-1) e coach/debrief (IA).
- **SA analyzer (CornerInsight/GripFactorReport/BrakeTraceReport)**, a fonte dos eventos causais, sem recomputar.
- **activeTelemetryData (Zustand)**, o handoff garage->SA, idêntico ao LTS->SA.
- **trackDayReport.ts (computeLossZones, provenance)**, fallback de coaching e guardrail de honestidade.

## 6. Riscos e mitigações

- **Física interim (oráculo 86/99, em recalibração):** claims quantitativos do Tier-1 (predicted_gain_s) podem imprecisar, rotular `confidence='physics_validated (interim)'`, herdar a disciplina de provenance. Tier-0 já supera incumbentes sem depender do contrafactual.
- **F1 UDP spec varia por ano (PacketFormat no header):** ler PacketFormat e testar por fixture por ano; sem versionamento, um update do jogo quebra a captura silenciosamente.
- **Header saru_v1 comum entre sims UDP:** detect_sim fica ambíguo, mitigado passando `source=saru_<sim>` explícito na ponte; teste de regressão do bridge por sim.
- **Armadilha ACC-console:** build de console não emite shmem/UDP, surfacear platforms do registry em GET /api/v1/sims para não gerar churn.
- **Agente Windows = componente novo (fora do esqueleto Go):** isolar como fase separada (6) pós-UDP; não tratar como "só mais um sim".
- **Alucinação numérica do LLM:** AnchorGuard determinístico + corpus de teste de tolerância; preferir expandir/formatar o texto determinístico (CornerInsight.explanation) a reescrevê-lo.
- **Proliferação de eventos (spam):** ranking por time_loss_s + corte de top-N por sessão é obrigatório (a pesquisa marca anti-spam como o que separa coaching usável de irritante).
- **ModuleId hardcoded em 3 pontos:** adicionar `garage` nos três no mesmo commit.
- **Gateway opt-in (502):** GarageSourcesView trata 502 explícito; Demo é sempre o caminho padrão.

## 7. Decisões abertas para o Vinicius

Ver lista consolidada no dossiê (nome do módulo garage vs sims; empacotamento do gateway UDP; variante/linguagem/prioridade do agente Windows; back-compat gt7; Tier-0 eager vs lazy; calibração de thresholds; modelos/custo/ZDR/idioma da IA; Garage absorve o CRUD da Biblioteca; guarda de auth do route-group live).

---

*Fundamentado em: services/api/src/gt7, services/api/src/engine, services/api/src/simulation-jobs, services/telemetry-api/saru_lapanalyzer, services/frontend/src/lib/shell + features/sa, vendor/saru-telemetry-gt7, e docs/research/competitive-sim-telemetry-2026-07.md. ADRs novos 0016-0019 referenciam ADR-0002/0007/0014/0015 e atualizam o índice docs/adr/README.md no mesmo commit (skill /adr).*
