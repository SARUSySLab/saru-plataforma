---
titulo: "saru-core-jl, Auditoria de Gaps (achados)"
data: "2026-07-15"
origem: "_arquivo/saru-physics-jl/docs/AUDIT-FINDINGS.md"
status: "vigente"
area: "dinamica_veicular"
---

# saru-core-jl, Auditoria de Gaps (achados)

> Sessão 2026-06-28 · branch base `develop` · resposta ao prompt `docs/AUDIT-AND-RESEARCH-PROMPT.md`.
> Read-only + 2 artefatos novos (`SPM.md`, este). Nada mergeado. Guardrail 94.0 s não tocado.

> **Atualização 2026-06-28 (pós-auditoria):** `feature/engine-final` **mergeada** em `develop` (opção A,
> `--no-ff`), proibidos removidos, branch deletada. `develop` agora = **GREEN 93.03 s** (QSS-port baseline).
> `.gemini/` removido. O TL;DR abaixo é o estado **no momento da auditoria** (pré-merge), mantido como registro.

## TL;DR (snapshot da auditoria, pré-merge)
1. **`develop` era RED** (todos os componentes stub, `solve_lap → -1.0`). Reproduzido.
2. **GREEN 93.03 s reproduzido**, só em `feature/engine-final` (então não-mergeado) e é um **clone QSS
   ponto-massa**, não 14-DOF. Match com o oráculo é **tautológico** (mesmo método). *Continua válido pós-merge.*
3. **Docs do `develop` mentiam o status** ("Fase 1 GREEN"). Corrigido.
4. Higiene quebrada: `.gemini/` presente, `hot.md`/`SARU_PROJECT_MEMORY.md` no branch (proibidos). Resolvido.

---

## Track 1, GREEN reproduzido + real-vs-stub

### Reprodução
| Branch | `solve_lap` | Harness | Verificado |
|---|---|---|---|
| `develop` (atual) | retorna `-1.0` | **RED** (`95.0 > 1.0`, 2 testes falham) | ✅ `julia --project -e include(runtests)` |
| `feature/engine-final` | QSS forward/backward | **GREEN 93.03 s**, PASS=true | ✅ runner isolado (só YAML+HDF5) |

> Repro do GREEN não precisou de MTK/DiffEq/Multibody, `solve_lap` usa só YAML+HDF5+LinearAlgebra.
> Sinal de que a Fase 2 (DAE) **ainda não começou**.

### Tabela componente-a-componente (`feature/engine-final`)
| Componente | Real/Stub | No caminho de `solve_lap`? | Teste unitário | Paridade vs Python (oracle) |
|---|---|---|---|---|
| Engine | Real (interp tabela) | ✅ `torque_at` | ❌ nenhum | raso: 1 fn vs `engine.py` 349 L (sem térmico, sem fricção, sem mapa throttle) |
| Aero | Real (mas lê só `table[1]`) | ✅ `compute_forces` | ❌ | raso: "mapa 3D" é escalar; vs `aerodynamics.py` 172 L |
| Transmission | Real (API completa) | ❌ **morto**, `solve_lap` usa `select_gear_optimal` inline | ❌ | API existe mas não usada; vs `drivetrain.py` 157 L |
| Tire | Real (mu escalar) | ❌ **morto**, usa `mu_x/mu_y` direto | ❌ | raso: sem Pacejka real, sem combined-slip, sem térmico; vs `tires.py` 270 L |
| Suspension | Real (spring/damper) | ❌ **morto** | ❌ | nunca instanciado |
| Brakes | Real | ❌ **morto**, usa `max_decel_g` do YAML direto | ❌ | vs `brakes.py` 180 L |

**Conclusão:** 6 componentes "implementados", **só 2 no caminho real**. 4 são código morto. O número
93.03 s sai de ~200 L de QSS dentro do `Harness.jl`, não dos componentes.

### Onde o Julia está raso (vs Python)
- Python = QSS real (`qss_solver.py` 559 L + `lap_time_solver.py` 739 L) com componentes ricos.
- Julia = **port do QSS** com componentes-casca + fudge factors p/ casar o número:
  - `cd = cx + 0.06`, `cl_front/rear -= 0.12`, `mu = pacejka_D * 0.968`, rolling-res `0.015`, temp `65.0`.
  - **Viola `calibration-guardrails.md`** (perf factors default 1.0; calibração só após load-sensitivity).
  - Dois modelos de torque divergentes: gear-select usa curva sintética inline (`T_max=505`, `exp(-0.0015·…)`),
    tração usa tabela YAML. Inconsistência física silenciosa.

### Docker
- `Dockerfile` existe só em `feature/engine-final`. **Não validado** (pendência do HANDOFF segue aberta).

---

## Track 2, Gaps de infra/higiene (priorizado)

| # | Severidade | Gap | Ação |
|---|---|---|---|
| 1 | 🔴 Alta | Docs `develop` afirmam GREEN; código é RED | Corrigir `CLAUDE.md`/`README` p/ status honesto |
| 2 | 🔴 Alta | `feature/engine-final` carrega `hot.md` + `SARU_PROJECT_MEMORY.md` (proibidos pelo padrão) | Remover antes de qualquer merge; estado vai p/ `SPM.md` |
| 3 | 🟠 Média | `.gemini/rules/julia-strict.md` presente = viola "ZERO `.gemini`" | Remover `.gemini/`; migrar regra p/ `.claude/rules` ou `CLAUDE.md` |
| 4 | 🟠 Média | `Project.toml` (develop) UUID `Multibody` = `deb0b741-0000-4a0a-8000-000000000000` (placeholder fake) | `Pkg.instantiate()` no develop **quebra**; corrigir UUID real ou remover dep |
| 5 | 🟠 Média | Sem `SPM.md` | ✅ criado nesta sessão |
| 6 | 🟡 Baixa | Sem `docs/ARCHITECTURE.md` / `docs/ROADMAP.md` | Criar mínimos (proposta abaixo) |
| 7 | 🟡 Baixa | 1 só teste; zero unitário por componente | Adicionar `test/test_<componente>.jl` |
| 8 | 🟡 Baixa | HANDOFF aponta `shared/saru-core-jl` (path errado; hoje `platform/`) | Corrigir referência |

### Decisão pendente: `feature/engine-final`
Opções (Vitor decide):
- **A) Merge `--no-ff`** após limpar `hot.md`/`SARU_PROJECT_MEMORY.md` + corrigir docs → develop fica GREEN-honesto (QSS port).
- **B) Cherry-pick** só componentes + harness, deixar lixo p/ trás.
- **C) Descartar** e refazer direto como Fase 2 (14-DOF), tratando o QSS port como throwaway.
> Recomendo **A** com ressalva no doc: marcar explicitamente como "QSS port (baseline), não 14-DOF".

### Propostas mínimas de docs
- `docs/ARCHITECTURE.md`: contrato (YAML+HDF5→lap_time), papel worker, fronteira QSS-port vs 14-DOF-alvo.
- `docs/ROADMAP.md`: Fase 1 (QSS port ✅ baseline) → Fase 2 (14-DOF DAE) faseada vertical.

---

## Track 3, Pesquisa externa (paste-ready p/ Fase 2)

### Perplexity (best-practice / comparativo 2026)
```
1. ModelingToolkit.jl: padrão acausal component-based p/ dinâmica veicular, como compor corpo 6-DOF +
   4 rodas + drivetrain/freios via @mtkmodel + connectors. Index reduction (structural_simplify) p/
   DAE de alto índice em multibody. Exemplos canônicos 2025/2026.
2. Multibody.jl (JuliaComputing): maturidade 2026 p/ chassi+suspensão (double-wishbone). Suporta
   loops cinemáticos fechados? Custo vs montar a álgebra à mão. Casos reais publicados.
3. MTK vs Modelica/Simscape Multibody p/ vehicle dynamics: gotchas, o que NÃO funciona (eventos de
   contato pneu-solo, atrito stick-slip, descontinuidades). Quando cair p/ ODE causal explícito.
4. SciML claim "40× vs solve_ivp": onde é real vs benchmark cherry-picked. Solver DAE recomendado
   (FBDF/QNDF/Rodas5), tolerâncias (abstol/reltol) p/ sim transiente de lap inteiro estável.
```

### NotebookLM (sobre os PDFs de dinâmica do Vitor)
```
1. Formulação canônica 14-DOF: enumerar os 14 estados (6 corpo + 4 vertical roda + 4 spin roda?)
   e o acoplamento corpo↔roda. Convenção **ISO 8855** (y-esquerda/z-cima, Fz downforce < 0) já fixada por ADR-001.
2. Pacejka Magic Formula combined-slip (Fx,Fy) + modelo térmico: equações exatas e conjunto de
   parâmetros (B,C,D,E + load sensitivity) validados p/ slick GT3. Como acoplar temp→mu.
```

### Gemini deep research
```
Relatório: como um LTS transiente 14-DOF profissional (Canopy LapSim / VI-CarRealTime) estrutura o
solver (multibody + pneu + powertrain) e VALIDA contra telemetria real (overlay de canais, métricas
de erro, quais sinais comparar). O que tratam como "validado", e como evitar o anti-padrão de calibrar
o solver p/ casar 1 número (lap time) em vez dos canais.
```

> ⚠️ Munição direta p/ o gap central: o GREEN atual casa **1 número** (lap time) via fudge factors.
> Validação 14-DOF séria exige overlay de **canais** (vel, aceleração lat/long, slip, temp) vs telemetria.

---

## §4, Análise física: fudge factors + modelo de torque

### 4.1 Fudge factors, o que cada um *compensa* (ask 5)
Quase todos são **proxy de física ausente**. Implementar os subsistemas (Fase 2) remove a maioria.

| Fudge | Valor | O que compensa fisicamente | Substituto correto |
|---|---|---|---|
| `cd = cx + 0.06` | +0.06 sobre 0.50 | drag **induzido** pelo downforce + drag de arrefecimento, não no `cx` "limpo" | `Cd = Cd0 + k·Cl²` (polar de arrasto) |
| `cl_f/r −= 0.12` | +24% downforce | Cl de referência subestimado / sem mapa vs velocidade | mapa aero real `Cl(speed, ride_h)` |
| `mu = pacejka_D·0.968` | −3.2% grip | pneu não atinge pico de `D` em combined-slip + **sem load-sensitivity** | elipse de atrito + `mu(Fz)` decrescente |
| temp `65°C` fixo | hard-coded | **sem modelo térmico** → grip não varia com temp | modelo térmico do pneu (energia→temp→mu) |
| rr `0.015` | hard-coded | Crr legítimo, mas chumbado | `Crr` de dado de pneu, via YAML |

> Conexão com `calibration-guardrails.md`: a regra já avisa "reimplementar *load sensitivity* antes de
> calibrar pneu". O `mu·0.968` é exatamente o sintoma. **Não calibrar pneu enquanto load-sensitivity
> + combined-slip não existirem**, senão superestima aderência mecânica.

### 4.2 Modelo de torque, recomendação (ask 6)
Pesquisa (MathWorks Powertrain Blockset, EPA SAE 2018-01-1412, SNE MVEM):

| Modelo | Fidelidade | Params | Veredito p/ GT3 lap-sim |
|---|---|---|---|
| Max-T × throttle (atual `Engine.torque_at`) | baixa | curva 1D | **insuficiente**, throttle linear é irreal em part-throttle |
| **Mapa 2D `T(rpm, throttle)`** | média-alta | mapa 2D | **base recomendada**, padrão indústria (Mapped SI Engine) |
| + **first-order lag** `τ·dT/dt = T_map − T` | + transiente | +`τ` (~0.05-0.1 s) | **somar**, barato, casa com "14-DOF transiente" |
| + **engine-brake (FMEP)** | + over-run | +coef FMEP | **somar**, torque negativo no trail-braking importa no lap |
| MVEM (manifold-filling ODE + RSM) | alta | volume coletor, τ turbo, … | **overkill**, NA flat-6, sem turbo; params indisponíveis |
| Willans line (`T = e·fuel − T_loss`) | média (economia) | e, T_loss | fora de escopo (foco lap, não consumo) |

**Decisão proposta:** **mapa 2D + lag de 1ª ordem + engine-braking (FMEP) + limitadores** (rev-limit, power-cap).
- É o approach "Mapped SI Engine", **realista E implementável**, e expõe **muitos params tunáveis**
  (mapa, `τ`, FMEP, rev-limit) → casa com o objetivo de DoE/otimização.
- **Combina** o melhor: mapa estático (preciso em regime) + dinâmica de 1ª ordem (transiente) sem o
  custo/params de um MVEM completo.
- **Mata o bug dos 2 modelos:** fonte única de torque = o mapa 2D. Elimina a curva sintética inline
  do `select_gear_optimal`.
- MVEM fica como L3 opcional **só se** houver dados de bancada (improvável p/ motor de corrida fechado).

**Fontes:** [MathWorks Mapped SI Engine](https://www.mathworks.com/help/autoblks/ref/mappedsiengine.html) ·
[EPA SAE 2018-01-1412, Engine Maps for Full Vehicle Sim](https://www.epa.gov/sites/default/files/2018-10/documents/sae-paper-2018-01-1412.pdf) ·
[SNE, Open-Source MVEM](https://www.sne-journal.org/fileadmin/user_upload_sne/SNE_Issues_OA/SNE_28_4/articles/sne.28.4.10451.tn.OA.pdf)

---

## §5, Achados de follow-up (2026-06-28)

| # | Achado | Status | Ação |
|---|---|---|---|
| A | `.gitignore` não bloqueava `.gemini/`, se recriado, voltava ao git | ✅ corrigido | `.gemini/` + `GEMINI.md` adicionados |
| B | `reference/` está gitignored → oracle inputs (vehicle YAML + track HDF5) **fora do git** → CI `julia-runtest` roda **sem** os arquivos do harness | ⚠️ aberto | Versionar ao menos `reference/*.yaml` (`!reference/*.yaml`); decidir HDF5 (LFS vs commit). **Precisa OK** |
| C | **ADR-010** (stack Julia/LTS, "Vitor aprovou 2026-06-15") referenciado em `SARU_GLOBAL_MEMORY.md` mas **não existe** como arquivo. `saru-os/docs/adr/` tem 0001-0008. **0009, 0010, 0011 todos fantasma** (0009 citado no `SARU/CLAUDE.md`; 0011 no GLOBAL_MEMORY) | ⚠️ aberto | Materializar ADRs no `saru-os` (cross-repo). Conteúdo já existe no GLOBAL_MEMORY, copiar p/ `saru-os/docs/adr/00{09,10,11}-*.md`. **Sessão saru-os** |
| D | `.tir` MF6.2 real disponível (Pirelli Scorpion SUV) em `~/Projects/_shared/tire_data/`, fora do workspace SARU | ℹ️ referência | Template p/ parser `.tir` Julia (Fase 2.2 Tire). Ligado no `ROADMAP.md` |

> Nota cross-repo (C): ADRs são do `saru-os` (padrão: "decisão de arquitetura cross-repo → ADR no saru-os").
> Respeitando isolamento de projeto, **não** escritos a partir desta sessão `saru-core-jl`.

---

## §6, Regressão do 14-DOF: DNF (diagnóstico empírico, 2026-06-30)

> Sessão de refino tire-dynamics. O 14-DOF estava documentado como "94,42 s GREEN" mas **não converge**.
> Diagnóstico por experimento (cada linha = 1 solve), não argumentação.

### 6.1 Sintoma
`solve_lap_14dof` retorna **150,0 s** = teto do `tspan`, não um lap. O `ContinuousCallback` de fim de
volta nunca dispara: o carro **sai da pista em s≈590 m**, `e_y` (erro lateral) explode p/ **−188 m**,
`e_psi` (erro de heading) → π. Aí `D(s_pos) ~ (vx·cos e_psi − vy·sin e_psi)/(1 − e_y·κ)` fica singular
(`e_y·κ`→1) e `s_pos` congela em ~710/4148 m → integra os 150 s restantes parado.

### 6.2 Causa-raiz: commit `4f4a0dc`
Diff `bb8f6c9`(94,42 s working) → `4f4a0dc`(HEAD, DNF): **só o modelo de pneu mudou** (driver/tracking/
handling idênticos, verificado por grep no diff). Pneu passou de:
- **Antes (`bb8f6c9`):** *resultant-slip similarity*, `F = Fz·μ·MF(√(κ²+α²))` projetado por `κ/σ`, `α/σ`.
  Algébrico, μ = `pacejka_D·grip_cal` = 1,8·1,30 = **2,34**. Sem Gxa/Gyk, sem relaxation, sem térmico.
- **Depois (`4f4a0dc`):** *pure-slip-por-eixo*, `Fx0(κ)`, `Fy0(α)` separados, pesados por Gxa/Gyk,
  passados por relaxation de 1ª ordem + dinâmica térmica. μ vinha do `dummy.tir` (placeholder, **1,2**).

### 6.3 Experimentos (o que foi descartado)
| Hipótese | Teste | Resultado | Veredito |
|---|---|---|---|
| Grip baixo (μ=1,2 do `dummy.tir`) | μ → 1,8 (YAML `pacejka_D`) | DNF idêntico (s≈710) | **descartada** |
| Relaxation lag desestabiliza | bypass algébrico (sem lag) | DNF idêntico (s≈710) | **descartada** |
| Combined-slip Gxa/Gyk | HEAD(bug→≈1) vs fix(ativo) | ambos DNF | **não-binding** |
| **Reestrutura resultant→pure-slip/eixo** | (só o pneu mudou no diff) |, | **causa-raiz** |

### 6.4 Hipótese p/ Fork #1-B (estabilizar, a investigar)
Mecanismo provável: o modelo pure-slip-por-eixo pode (a) **violar a elipse de atrito** (|F|=√(Fx0²+Fy0²)
pode passar de μ·Fz), e/ou (b) a roda dianteira livre desenvolve **κ espúrio** → `Gyk(κ)<1` mata a força
lateral dianteira → understeer → departure. Ambos a checar com a telemetria nova (`export_telemetry`:
canais Fz/alpha/kappa por canto). Alternativa (Fork #1-A): reverter o pneu p/ resultant-slip de `bb8f6c9`.

### 6.5 Correções aplicadas nesta sessão (não restauram convergência, são pré-requisitos corretos)
- **Gxa/Gyk** reescritos p/ forma canônica MF6.2 reduzida (Pacejka cap.4). O HEAD usava
  `cos(rCx1·atan(rBx1·κ²·rBx2·α))`, dimensionalmente errado **e** inativo (`rBx2`=0 default zerava o arg).
- **μ peak** sourced do YAML `pacejka_D` (1,8 documentado) em vez do `dummy.tir` (1,2 placeholder). `grip_cal`=1,0.
- **DRY:** física do pneu extraída p/ `Tire.mf62_combined` (fonte única, AD-safe), solver chama 4×.
- **Telemetria:** `export_telemetry` (HDF5/CSV) p/ inspeção por canal, instrumento do Fork #1.

---

## Sessão 2026-07-01, Revisão doc-vs-código (KB research recuperada × código)

> Após recuperar as equações das 8 research docs da `saru-knowledge-base` (estavam como imagem;
> ver `- EQUATIONS.md` companheiros + memória `drive-gdoc-equation-recovery`), cruzei o
> `Critical Review 14-DOF` + `Vehicle Dynamics Model Review` contra o código real. Read-only.

### 🔴 FLAG 1 (acionável), `pacejka_B=22.0` contradiz a própria YAML
`reference/vehicle_992_gt3_r.yaml` tem **ao mesmo tempo**:
- `pacejka_B: 22.0` → C_α implícito = B·C·D·Fz0 = 22·1.40·1.80·4000 ≈ **221.760 N/rad**
- `cornering_stiffness_front: 85000`, `cornering_stiffness_rear: 100000` (campos **não usados** pelo código)

**2.6× de discrepância na mesma YAML.** `mf62_combined` usa `p.B` no Magic Formula puro
(`Fy0 = Fz·μ·sin(C·atan(B·α − E(B·α − atan(B·α))))`), então B=22 governa a força; os campos
`cornering_stiffness_*` são letra morta. **Critical Review §1.c E o Vehicle Dynamics Model Review**
derivaram o fix: **B_f=8,43, B_r=9,92** (`= C_α/(C·D·Fz0)`), nunca aplicado. Também: **B único**
p/ os dois eixos (sem split F/R, apesar de 85k≠100k).

**Impacto:** pneu ~2,6× rígido demais na região linear → satura em slip pequeno demais → ângulos de
slip irreais (SPM: ≤5° diant.; GT3 real ~8-12° a 2g). A **elipse de Kamm mascara no PICO** (lap 102s
honesto se mantém), mas erra o **transiente/handling** e importa p/ o NMPC (o single-track de predição
usa cornering stiffness). Fix é barato (YAML) mas **muda a física → re-validar os 102s** (guardrail).

### 🟠 FLAG 2, `torque_cal=1.15` ainda ativo (`Transient14DOF.jl:463,745`)
Critical Review §2 (Fase 2: substituir prepass QSS por g-g-v do próprio 14-DOF + controle
feedforward) **não feito** → `torque_cal` permanece como dívida de calibração. SPM reconhece.
O de-rate 0,85 do alvo QSS é o mesmo anti-padrão heurístico que a Critical Review manda trocar por g-g-v.

### 🟠 FLAG 3, Solver `QNDF` + tol 1e-5/1e-7 (`Transient14DOF.jl:848`)
Critical Review §4 **e** o MVP PDF recomendam **`TRBDF2`** (melhor p/ descontinuidades: troca de marcha,
clamps de throttle/brake) + `reltol=1e-6/abstol=1e-8`, alegando **2-3× speedup**. Não adotado. Oportunidade,
não bug (QNDF converge).

### ✅ Consistente (sem flag)
- 14-DOF usa **MF6.2 real** (`mf62_combined`: Gxa/Gyk canônico + floor + Kamm p=12), bate com as
  alavancas 2&3 do `Refinamento, EQUATIONS`. `grip_cal=1,0` ✓.
- **Similarity method** (`compute_forces`, criticado pela Critical Review §1.a) **NÃO é usado pelo 14-DOF**
  (só path QSS/legacy). Os wrappers legados (`lateral_force`/`longitudinal_force`) parecem **sem chamador**
  = código morto leve.

### 🧭 Meta-flag, tensão "94 honesto?" (Critical Review × SPM)
- **Critical Review:** com tire+target+driver corrigidos → **94,0±0,3 honesto**. Cita GT3 real ~94s em
  Interlagos, pico a_y 2,5-3,0g, μ_eff 2,0-2,3.
- **SPM/memória `honest-14dof-lap-vs-qss`:** "94 é artefato do QSS ponto-massa; honesto ~102; gap é
  driver/linha → NMPC."
- **Reconciliação:** ambos concordam que o pneu já é honesto e o gap é driver/alvo. Mas o dado de
  referência da própria Critical Review (GT3 real roda ~94) indica que **94 É honestamente alcançável por
  um driver/linha ótimos** → o enquadramento "94 = artefato" do SPM é levemente pessimista. Leitura honesta:
  **94 ≈ alvo honesto de driver ótimo (meta do NMPC), 102 = driver P centerline cru.** Ambos levam ao NMPC
  (Stage 3), mas **B=22 + de-rate 0,85 são compensadores que mascaram**; o caminho p/ 94 honesto inclui
  corrigir B e trocar o de-rate QSS por g-g-v-do-14-DOF (= Fase 2 da Critical Review), não só plugar NMPC.

---

## §7, Auditoria física 2026-07-15 + fix batch (branch `feature/claude-audit-fixes`)

> Auditoria (worker hardcoded, schema drift, convergência) → ordem do Vitor "fix tudo".
> Suite pós-fix: **97 pass + 1 broken (94±1 NMPC), 0 fail**. QSS **87,539 s** intacto.

### 7.1 Fixes aplicados
| Gap | Fix | Commit |
|---|---|---|
| **G3** worker hardcoded (`RedisWorker.jl:78-79`) + track-label mentiroso (payload `track` era só rótulo, física sempre Interlagos) | `vehicle`/`track` resolvidos por nome em `reference/` (inexistente = erro honesto listando disponíveis); `setup_overrides` deep-merged → YAML temp → solver (contrato de path preservado); testes de resolução/traversal/override | `0cebd75` |
| Schema drift (Julia = Dict solto; chave obsoleta passava calada) | **`src/io/VehicleSetup.jl`** (seed ADR-0010 §1): loader + `validate_setup_keys` (`@warn` por chave fora do schema) + `KNOWN_UNUSED` documentado (§7.5) | `0cebd75` |
| FLAG 2 parcial: `torque_cal=1.15` hardcoded no código | → `qss_calibration.torque_cal` (default neutro 1,0); comprovado behavior-preserving (lap 100,72 s idêntico pré-FLAG1) | `328a17c` |
| **FLAG 1**: `pacejka_B=22` vs `cornering_stiffness_*` (2,6× na mesma YAML) | **B por eixo = C_α/(C·D·Fz0) = 8,43/9,92** (pacejka_B removido do YAML, fallback legado no código); feedforward + termo K_us·vx²·κ (understeer gradient bicycle, mesmo C_α); derate re-ladder → 0,70; gate slip diant. 5°→12° (banda física GT3) | `dbf1a42` |
| `cl_total` redundante (mesma classe de contradição do FLAG 1) | removido do YAML | `0cebd75` |

### 7.2 Ladder do derate pós-FLAG 1 (critério = canais, nunca lap)
| derate | lap | e_y | slip F/R | util | veredito |
|---|---|---|---|---|---|
| 0.88 | 126,95 | 14,19 | 112/88° | 0,953 | spin total |
| 0.85 | 121,74 | 7,40 | 109/88° | 0,950 | spin |
| 0.82 | 111,89 | 5,27 | 25/40° | 0,945 | sujo |
| 0.78 (antigo) | 109,32 | 2,76 | 8,8/19,2° | 0,938 | sujo (traseira além do pico) |
| 0.75 | 108,87 | 2,61 | 7,6/17,2° | 0,929 | sujo |
| **0.70** | **109,28** | **1,53** | **6,8/9,8°** | **0,907** | **✓ limpo** |

K_us teve efeito marginal (e_y 2,84→2,76 em 0.78): o erro residual é **transiente/oversteer**
(traseira soltando em trail-braking), não understeer de regime, reforça que o próximo ganho real
é o NMPC, não tuning de P-driver (precedente: refino 2026-06-30 rendeu ~0,3 s).

### 7.3 Leitura honesta do re-baseline
**109,28 s substitui 100,7 s.** O 100,7 era co-calibrado com o pneu 2,6× rígido (B=22), mesma
classe de co-calibração do T03 (seletor de marcha). Com rigidez real: slips na banda física GT3
(6,8/9,8° vs artefato ≤5°), util ≤0,907 (grip **sobrando**, μ=1,8 continua lá). O caminho p/ 94
não regride: **driver NMPC** (+ .tir real + aero real). Não tunar nada p/ "recuperar" 100,7.

### 7.4 Fila de pesquisa (Vitor pesquisa → coloca na pasta certa da KB)
1. **Load sensitivity k real** de slick GT3 (faixa esperada −0,05..−0,20) → `tires.load_sensitivity`.
2. **`.tir` MF6.2 slick GT3 real** (ou B/C/D/E + rB/rC/rH publicados) → mata defaults sintéticos
   do `dummy.tir` (combined-slip rB/rC/rH ainda genéricos).
3. **Mapas aero reais** Cd/Cl(h_front, h_rear, yaw) do 992 GT3 R, os CSVs atuais em
   `reference/aero_maps/` são **placeholder malformado** (`\n` literal no texto, 4 pontos, yaw só 0).
4. **Mapa de motor 2D** T(rpm, throttle) + FMEP/engine-brake → mata `torque_cal=1.15`
   (recomendação §4.2 desta auditoria segue válida).
5. **Datasheet de disco** AP/PFC 390/370 mm (massa, área, h0) → térmico V2 (hoje defaults 8 kg/0,12 m²/60).
6. **🔴 Distribuição de peso do 992 GT3 R:** YAML tem `lf_m=1,100/lr_m=1,410` ⇒ **56% estático
   na DIANTEIRA**, suspeito p/ carro de motor traseiro (spec real ≈ 41/59 F/R ⇒ lf≈1,48/lr≈1,03).
   Se lf/lr estiverem invertidos, transferência de carga/bias/marcha rodam espelhados. **NÃO mexido**
   (muda toda a física + o oráculo QSS Python usa o mesmo YAML, precisa dado confirmado + re-baseline).

### 7.5 Chaves mortas remanescentes (agora documentadas como `KNOWN_UNUSED` no VehicleSetup)
`vehicle.*` (metadata) · `mass.fuel_capacity_l/fuel_density` · `geometry.wheelbase_m` ·
`powertrain.drive_type/max_torque_nm/gearbox/rpm_redline` · `aerodynamics.aero_map_cd_file/cl_file`
(alvo Fase 2) · `tires.supplier/compound` · `brakes.brake_response_time`. Reaparecer chave fora
dessa lista + schema = `@warn` do validador (drift catcher).

### 7.6 Status dos achados antigos
- §5-B (reference/ fora do git): **RESOLVIDO de facto**, YAML + HDF5 trackeados (verificado).
- FLAG 3 (QNDF vs TRBDF2): **aberto** (oportunidade de perf, não bug; 3 fontes recomendam TRBDF2).
- Componentes órfãos (Suspension/Brakes/Aero/Transmission inline no solver): **aberto** (dívida DRY).

### 7.7 Status da fila §7.4 (atualização 2026-07-15c/d, pesquisa entregue + aplicada)
| Item §7.4 | Status |
|---|---|
| 1. load_sensitivity k | ✅ **APLICADO k=−0.12** (2 fontes; semântica Fz0 = ΔFz relativo ao estático, documentada no YAML) + **mu_scale morto** (dupla contagem, §4.1) → QSS re-baseline **87,26 s** |
| 2. .tir MF6.2 real | 🟠 **PARCIAL**: combined rB/rC/rH pesquisados em `reference/gt3_992_seed.tir` (chave `tires.tir_file`); **pDy2=−0.20 documentado mas travado em −0.05** até o prepass virar g-g-v do 14-DOF (plant 4× mais sensível que o alvo agregado diverge o driver); .tir de fornecedor segue pendente |
| 3. aero maps | ❌ **V2**, S3 é estimativa não-primária (fact-check confirma; Cl −3,2 = upper bound); placeholders bem-formados versionados |
| 4. mapa motor 2D + FMEP | ❌ **V2**, S4 traz forma (Chen-Flynn A/B/C, f(α), I_engine≈0,12) mas coefs são estimativa; `torque_cal` segue como dívida explícita |
| 5. disco AP/PFC | ✅ **APLICADO** (S5: massa 8,5 kg, área 0,094 m², h 135 W/m²K; pico 657,9 °C na banda AP; split 390/370 por eixo = V2) |
| 6. lf/lr (peso 56%F) | ✅ **CORRIGIDO p/ 40F/60R** (lf=1,504/lr=1,003; Iz→2450). ⚠️ o doc S1 lista lf/lr **internamente trocados** vs o próprio 40/60, aplicar o doc literalmente re-introduz o bug invertido |

Estado pós-aplicação: **QSS 87,26 s · 14-DOF 109,48 s limpo** (derate 0.68; e_y 1,45 m, slips
5,7/11,2°, util ≤0,794). Robustez nova: clamp suave positivo nos pesos combined (`Tire.mf62_combined`), com rC>1 real o cosseno cruzava zero e invertia o sinal da força (DNF); pesos são pesos, ∈[0,1].

