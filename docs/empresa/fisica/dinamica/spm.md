---
titulo: "SPM, saru-physics-jl (estado vivo)"
data: "2026-07-15"
origem: "_arquivo/saru-physics-jl/SPM.md"
status: "vigente"
area: "dinamica_veicular"
---

# SPM, saru-physics-jl (estado vivo)

> Estado vivo único do repo (padrão SARU). Ler no início, atualizar no fim da sessão.
>
> **2026-07-15d (integração pós-reorg + aplicação da pesquisa S1/S2/S5, sessão principal):**
> - **Branches integradas** (`417dcab`): restauração pós-reorg + k012. Testset load-sens virou
>   **k-relativo** (varre 0/−0.10/−0.20, monotônico) + pino no −0.12 do YAML. **Semântica Fz0
>   decidida e documentada**: ΔFz relativo ao ESTÁTICO (fz0=m·g) ≡ linearização nominal-estática
>   do doc Gemini (fonte do −0.12); não re-linearizar em carga operacional sem re-derivar k.
> - **mu_scale MORTO** (proxy de load-sens, dupla contagem c/ k real, AUDIT §4.1) →
>   **re-baseline QSS 87,26 s** (cadeia: 87,54 pré-k → 88,19 k+mu_scale → 87,26 troca completa).
>   Python: sem knob equivalente (auditado pela sessão py; KB módulo 11).
> - **S1 APLICADO:** lf/lr corrigidos p/ **40F/60R** (lf=1.504/lr=1.003; antigo codificava 56%F, >   suspeita da auditoria confirmada). ⚠️ o doc S1 da pesquisa lista lf/lr **trocados** vs o
>   próprio 40/60 (inconsistência interna, aplicar o doc literalmente re-introduz o bug invertido).
>   Iz 1650 (sem fonte) → 2450 (S1, k=0.45·L). 14-DOF pós-geometria: 109,28 → **107,20 limpo**
>   (traseira carregada = tração RWD melhor, físico). Massa base 1330 MANTIDA (S1 propõe 1265+80
>   mas é BoP-variável e re-baselinaria o QSS, segurada, registrada).
> - **S5 APLICADO:** térmica de disco real no YAML (massa 8.5 kg, área 0.094 m², h 135 W/m²K vs
>   default 60 passeio). Pico diant. 657,9 °C (banda AP 400-600 + picos), fade diagnóstico 0.884,
>   não binda volta única ✓. Split 390/370 por eixo segue V2.
> - **S2 APLICADO (parcial honesto):** chave nova `tires.tir_file` (ausente→defaults legado;
>   explícita+arquivo faltando→**erro duro**, fallback silencioso rodaria física diferente da
>   declarada; worker absolutiza o path ao materializar YAML temp) + `reference/gt3_992_seed.tir`
>   c/ combined-slip pesquisado (rB/rC/rH, mata o sintético permissivo rC=1/rH=0).
>   `Tire.mf62_combined` ganhou **clamp suave positivo** nos pesos Gxa/Gyk (com rC>1 real o
>   cosseno cruzava zero → força invertia sinal → DNF). **pDy2=−0.20 pesquisado fica documentado
>   no seed mas travado em −0.05**: plant per-tire 4× mais sensível que o alvo agregado do prepass
>   (sem transferência lateral) diverge o driver (isolado: e_y 16 m, slip 112°, DNF-class), >   ativar JUNTO da troca do prepass por g-g-v do próprio 14-DOF (Critical Review Fase 2).
> - **ESTADO FINAL: QSS 87,26 s · 14-DOF 109,48 s limpo** (derate re-ladder 0.70→**0.68**; e_y
>   1,45 m, slips 5,7/11,2°, util ≤0,794, driver P segue o gargalo, não grip). Ladder no YAML.
> - S3 aero (Cl −3.2 = upper-bound não-primário) + S4 motor 2D/FMEP (estimativas) = **V2**
>   (AUDIT §7.7). ⚠️ Clone novo só tem remote `origin`, espelho `vitormtt` não recriado
>   (dual-push suspenso; decisão do Vitor: recriar ou aposentar).
>
> **2026-07-15c (k real de load sensitivity, branch `feature/claude-load-sensitivity-k012`):**
> pesquisa do Vitor (`saru-KB/20_vehicle_dynamics/research/`, 2 fontes independentes) convergiu
> **k = −0.12** (slick GT3 Michelin PS GT/Pirelli DHE, banda −0.10..−0.15). YAML de referência
> `tires.load_sensitivity: 0.0 → −0.12`; **re-baseline QSS 87.54 → 88.19 s** (+0.65,
> `QSS_REFERENCE_S`, banda ±1.0, validação PASS). Espelho Python idem (+0.69 no Porsche →
> 86.87; gap cross-solver estável 1.32 s). 14-DOF: k entra no prepass+solver, suite completa
> valida no CI da branch. ⚠️ Integração 15c+15b deixou pendências fechadas na sequência (mesma
> sessão): testset load-sens k-relativo, semântica Fz0, mu_scale, canais 14-DOF, ver bloco 15d.
>
> **2026-07-15b (pós-reorg de pastas, auditoria de perda):** workspace reorganizado pelo Vitor:
> `platform/saru-core-jl` → **`saru-physics-jl/`** (dir local = nome do repo org; idem py/app;
> `platform/` deletado). Auditoria: **zero perda de commits**, `origin/develop` íntegra (topo
> `58daeb7`, fix batch 2026-07-15), `main` nova (`22a4268` "governance") é **ancestral limpo** de
> develop (0×11). Perdas reais só untracked: `Manifest.toml` (gitignored, regenerar via
> `Pkg.instantiate`, suite re-validada nesta sessão) e `reference/aero_maps/*.csv` (placeholders
> malformados, mortos pelo `*.csv` do .gitignore, **recriados bem-formados** + exceção
> `!reference/aero_maps/*.csv` + README PLACEHOLDER). Memória de agente + scripts de sessão
> migrados p/ o path novo. saru-KB intacta (research load-sens de 2026-07-15 preservada, local).
> Espelho Python load-sens salvo no org (`saru-physics-py` `823f516`). Pendente cross-repo:
> SGM/topologia global ainda citam paths `platform/*` (sessão umbrella).
>
> **2026-07-15 (auditoria física → fix batch, branch `feature/claude-audit-fixes`):**
> - **G3 FECHADO** (`0cebd75`): `RedisWorker` resolve `vehicle`/`track` por **nome** em `reference/`
>   (nome inexistente = erro honesto listando disponíveis, matou o track-label mentiroso: antes
>   `track:"monza"` devolvia física de Interlagos rotulada monza) + `setup_overrides` (dict parcial
>   no schema do YAML) deep-merged via novo **`src/io/VehicleSetup.jl`** (seed ADR-0010 §1: loader
>   + `validate_setup_keys` c/ `@warn` por chave fora do schema; `KNOWN_UNUSED` documentado).
> - **FLAG 1 RESOLVIDO** (`dbf1a42`): **B por eixo** derivado de `C_α/(C·D·Fz0)` = **8,43/9,92**
>   (`pacejka_B: 22` removido do YAML; fallback legado no código) + feedforward de esterço ganha
>   termo físico **K_us·vx²·κ** (understeer gradient bicycle, mesmo C_α). **Re-baseline honesto
>   14-DOF: 109,28 s**, re-ladder do derate por canais 0,78→**0,70** (e_y 1,53 m, slips 6,8/9,8°,
>   util ≤0,907). **O 100,7 era co-calibrado c/ pneu 2,6× rígido** (mesma lição do T03). Util <1 =
>   gargalo agora é o driver P cinemático, não grip → NMPC. Gate de slip diant. 5°→12° (banda GT3;
>   pico do MF p/ B_f=8,43 ≈ 14°). Ladder completo em `AUDIT-FINDINGS §7.2`.
> - **torque_cal 1.15 → YAML** (`328a17c`, `qss_calibration.torque_cal`, default 1,0 neutro;
>   comprovado behavior-preserving: 100,72 s pré-FLAG1 idêntico). Último fudge hardcoded morto.
> - QSS **87,54 intocado** (B não entra no QSS). `cl_total` removido (redundante/contradição).
> - **🔴 ACHADO NOVO (pesquisa, NÃO mexido):** `lf_m=1,100/lr_m=1,410` ⇒ **56% peso DIANTEIRO**
>   estático, suspeito p/ 992 (motor traseiro, real ~41/59F). Se lf/lr invertidos, toda a
>   transferência de carga roda espelhada. Confirmar antes de tocar (AUDIT-FINDINGS §7.4).
> - Fila de pesquisa consolidada: `AUDIT-FINDINGS §7.4`. Correção de doc: `interlagos.hdf5` ESTÁ
>   trackeado (nota antiga abaixo dizia gitignored, stale); aero CSVs = placeholder malformado.
>
> **2026-07-14 (auditoria KB↔repos, sessão umbrella), correções + backlog:**
> - **CORREÇÃO de memória stale:** `src/ai/` (DriverMPC/GaussianGrip/TubeGenerator) foi **removido**
>   em `890a2a2` ("remove phase 3 stubs"), as seções abaixo que dizem "commitado + coberto" são
>   históricas; NMPC hoje = só plano (`docs/STAGE3-NMPC-DRIVER-PLAN.md`). **T03 espelho Python:
>   JÁ aplicado** no saru-core (`qss_solver.py:193`, merged 2026-07-04), task chip quitada.
> - `docs/adr/MASTER_ADR.md` sincronizado c/ rev cross-eco 2026-07-14 (canônica no saru-KB).
> - **Backlog da auditoria:** (1) RedisWorker: plumbar setup do payload → `solve_qss`/`solve_lap_14dof`
>   (hoje hardcode `reference/vehicle_992_gt3_r.yaml`+`interlagos.hdf5`, `RedisWorker.jl:78-79`;
>   = gap G3/ADR-0010 §4); (2) `VehicleSetup.jl` master SSoT (ADR-0010 §1, grafia canônica
>   `VehicleSetup`), não iniciado; (3) `export_protobuf.jl` (raiz): **não deletar nem regenerar**
>   até decisão ⚖️ proto×JSON-Schema (T-A pendente, MASTER_ADR §3).
> Última atualização: 2026-07-04 (**T03 LANDED por ordem do Vitor** + re-baseline QSS
> **87,54 s** + de-rate exposto no YAML e re-tunado **0.78** por ladder de canais físicos, > 14-DOF **~100,7 s limpo**. Diretriz nova: física primeiro, zero hardcode p/ bater número
>, memória `physics-first-no-result-tuning`).
>
> **2026-07-01, PR #2 MERGED:** 14-DOF honesto (~102s) + Stage 3 NMPC plan + módulos AI merged em
> `develop` (`--no-ff`, pushed). Conflito de docs (CLAUDE/SPM) resolvido mantendo a versão **honesta
> 102s** (descartada a stale "94.42s GREEN"). Física segue deferida até saru-os back+front funcional.
>
> **2026-07-02, QSS ENDURANCE THERMAL portado (saru-core `28c3258`) + verificado:** núcleo QSS
> ponto-massa extraído do Harness p/ `src/simulation/QSS.jl` (`solve_qss`; baseline **93,03 s
> byte-idêntico**, harness delega) + modelo térmico de disco/fade (`thermal_brake_model` + modo
> `:endurance_thermal`, ponto-fixo fade→frenagem, Limpert 1999). Suite 43 pass + 1 broken.
> **Verificação (auditoria de energia + cross-check):** frenagem Julia = **10,46 MJ/volta** → pico
> diant. **~646 °C** (teto adiabático 742 °C; consistente c/ AP Racing: bulk 400-600 °C em corrida).
> Python fica frio (419 °C) porque a config default dele roda Interlagos em **69,7 s (pace F1,
> irreal)** → só 6,46 MJ/volta de frenagem, artefato de config, não bug do port. **Calibração
> aplicada:** YAML de referência agora com pastilha racing endurance (Pagid RSL29-class:
> `fade_onset=600`/`fade_full=850`) → fade engaja como diagnóstico (min 0,908) mas **não binda**
> em volta única (byte-idêntico ao qualifying), coerente c/ GT3 real. **V2 (backlog térmico):**
> (a) radiação εσT⁴ (pico superestimado ~5-10% acima de 550 °C); (b) disco por eixo (390/370 mm);
> (c) massa/área/h0 do disco validar c/ datasheet AP/PFC (hoje defaults 8 kg/0,12 m²/60);
> (d) multi-lap c/ carry-over de T (fim de volta = 581 °C diant. → stint esquenta até equilíbrio);
> (e) tolerância de convergência no ponto-fixo. Gap de migração restante: **3-DOF** (QSS ✅).
>
> **2026-07-03, CI VERDE (Dates/Julia 1.12) ✅ RESOLVIDO:** CI falhava toda run com "Unsatisfiable
> requirements … Dates": compat `Dates = "1.11.0"` insatisfazível em Julia 1.10 (stdlib lá = 1.10.0)
> + Manifest gerado em 1.12.6 (grava versão de stdlib, ilegível p/ Pkg 1.10). Fix em `0f6994c`+`be7abd1`:
> compat `Dates` **removido** (stdlib sem pin) + CI (`ci.yml`) e `Dockerfile` alinhados em **Julia 1.12**
> (versão real de dev/Manifest). Últimas 3 runs `develop` = **success** (~50 min, suite completa);
> `Pkg.instantiate()` local 1.12.6 OK. Nada pendente neste tema.
>
> **2026-07-03b, MISSÃO VI-CRT P0 (GAP_ANALYSIS T02/T03/T11-lite), resultado:**
> - **T02 JÁ RESOLVIDA** (nada a fazer): `Project.toml` sem `Multibody`, `instantiate` OK, CI verde.
> - **T11-lite FEITO** (commit `a032512`): fudges do QSS extraídos p/ YAML, `qss_calibration:`
>   (cx_offset 0.06 / cl_offset −0.12 / mu_scale 0.968) + `tires.rolling_resistance` 0.015;
>   defaults neutros no código; baseline **93,03 s byte-idêntico** verificado (sem o bloco: 92,22 s
>   = física crua). T=65 °C já não existia (sumiu na extração p/ QSS.jl). Prepass 14-DOF intacto.
> - **✅ T03 LANDED (2026-07-04, ordem do Vitor, "testar + recalibrar a cadeia corretamente"):**
>   seleção de marcha unificada em `Engine.torque_at` nos 2 paths (QSS + prepass 14-DOF delega p/
>   `QSS._select_gear_optimal`); curva synth T=505 morta; teste unit 16/16 na suite. Causa do Δ:
>   synth zerava torque >6000 rpm → seletor subia marcha cedo (co-calibração: fudges + de-rate +
>   driver afinados em cima do seletor errado, memória `t03-gear-selector-cocalibrated`).
>   **Re-baseline QSS: 93,03 → 87,54 s** (`QSS_REFERENCE_S=87.54`, banda ±1,0 mantida; raw sem
>   fudges = 87,12, fudges agora valem só 0,42 s). **De-rate do prepass exposto no YAML**
>   (`qss_calibration.prepass_grip_derate`, default neutro 1.0, padrão Performance Factor VI-CRT)
>   e **re-tunado por ladder de canais físicos** (nunca lap): 0.85→estoura (e_y 37,7 m) · 0.82→54 m ·
>   0.80→sujo (slip tras 25°) · **0.78→limpo e mais rápido (lap 100,7 s, e_y 1,58, slips 4,1/11,6°,
>   util 1,033)** · 0.75→mais limpo/lento (0,74 m; 101,2 s). Não-monotônico em 0.80-0.85 (driver P
>   caótico na borda de factibilidade). **Python: mesmo bug, fix espelho = task chip criada**
>   (`task_642bb600`, sessão saru-core; `qss_solver.py:205` → `_torque_curve_interp`).
>   **Próximo passo da recalibração honesta (pesquisa Vitor):** matar fudges restantes com física, >   load sensitivity μ(Fz) no QSS (pré-req da rule calibration-guardrails) + aero real GT3 (cx/cl/
>   ride-height maps) + coefs de pneu slick reais → re-baseline final.
> - **✅ Load sensitivity: ESTRUTURA implementada (2026-07-04b, TDD):** μ_eff = μ·(1+k·ΔFz/Fz0) nos
>   passes do QSS **e** do prepass 14-DOF (mesma equação/parâmetro, `tires.load_sensitivity`).
>   **k=0.0 neutro no YAML de referência**, baseline 87,54 byte-idêntico; teste na suite prova
>   k=−0.10 → +0,54 s (direção correta). **VALOR real vem da pesquisa** (slick ~−0.05..−0.20);
>   quando entrar: setar k real + revisar/deletar `mu_scale` + re-baseline (gate ±0,5 s). Zero
>   hardcode: decisão do Vitor "estrutura agora, valores depois da pesquisa".
>
> 🎯 **PRÓXIMA SESSÃO:** ver **`docs/NEXT-SESSION-PROMPT.md`** (handoff completo). Agenda (ordem do Vitor):
> (1) ✅ **mover arquivos KB, JÁ FEITO** (commit `a90995b` auto-filou os 8 `- EQUATIONS.md` na taxonomia);
> (2) **conferir** os 8 `- EQUATIONS.md` (cross-check interno; deep-research só o Vitor); (3) **auditar
> branches `saru-core`+`saru-os`** e a conexão entre eles p/ adaptar ao `saru-core-jl`, **APENAS DOCUMENTAR**;
> (4) **M1 (MPC plumbing) DEFERIDO** p/ análise junto com o acima. Fix do **B=22 → M2**.
> Ver memórias `honest-14dof-lap-vs-qss` · `drive-gdoc-equation-recovery`.

## Status real (verificado empiricamente, 2026-06-30, Track A CONVERGIU)
- **Suite verde.** QSS ponto-massa (`Harness.jl`) **93,03 s** intacto (SAE J670, baseline regressão).
  14-DOF agora com guardrail real (`@test lap<140 && 96≤lap≤112`), não mais `@test_broken`.
- **✅ 14-DOF CONVERGE:** `solve_lap_14dof` fecha Interlagos em **~102,3 s determinístico**, linha limpa
  (max e_y **1,8 m**), pneu **fisicamente dentro da elipse** (utilização ≤1,05; slip diant. ≤5°/tras. ≤13°).
- **Fork #1 resolvido pela rota B (estabilizar pure-slip, sem reverter).** 4 alavancas cumulativas, todas
  da pesquisa (`Refinamento Dinâmica Veicular 14-DOF.md`), medidas por experimento (1 solve cada):
  1. **TCS**, slip-limiter suave (tanh) no torque de tração traseiro, alvo κ=0,05. Mata o rodaspin
     κ≈2,8 que colapsava `Gyk=cos(atan(10κ))→0,04`. (DNF s≈579m → completa.)
  2. **Floor Gxa/Gyk** (0,40), força cruzada não colapsa a zero sob slip severo (atrito cinético
     residual). Mata as excursões de trail-braking (traseira aliviada). (115,9s → 101,6s limpo.)
  3. **Elipse de Kamm** (p=12, |F|≤μFz), **revelou que o 101,6s usava grip fake (u>1)**; impô-la
     honesta desestabilizou o driver cru (128s). Fisicamente obrigatória.
  4. **De-rate do alvo QSS** (0,85), alvo ponto-massa é otimista demais p/ o transiente; de-ratado,
     o driver para de over-dirigir → **102,3s limpo e honesto** (util≤1,05).
- **🔑 94±1 é artefato do QSS ponto-massa.** util≈1,0 em todo lugar = o pneu **já tem** grip de GT3
  (μ~1,8; GT3 real roda Interlagos ~91-95s). O gap 102→94 é **linha de corrida / driver, NÃO grip**, o driver centerline-tracking dirige no limite mas não na linha ótima. **94 honesto = NMPC**
  (`DriverMPC.jl`, stub). Tunar pneu p/ 94 = fake grip (anti-padrão que pesquisa+audit alertam).
- **14-DOF:** chassi 6-DOF + 4 unsprung + 4 spin + tracking curvilíneo, DAE acausal `MTK`/`QNDF`,
  ISO 8855. Driver: feedforward curvatura (bicycle) + feedback path + P-controllers (cru, limita o pace).

## Dívida técnica (ressalvas críticas, NÃO é física limpa ainda)
1. **🔴 14-DOF não converge (DNF).** Bloqueador #1. Ver "Status real" + "Fork #1" abaixo. `grip_cal`
   **já é 1.0** (doc antiga dizia 1.30, falso desde `4f4a0dc`). `torque_cal=1.15` permanece.
   μ peak agora vem do **YAML `pacejka_D`=1.8** (slick documentado), não mais do `dummy.tir` placeholder
   (pDx1=1.2), corrigido esta sessão. Combined-slip Gxa/Gyk **corrigido** p/ forma canônica MF6.2.
2. **`dummy.tir` não existe** → `parse_tir` retorna defaults genéricos. Sem `.tir` GT3 real, os coefs
   B/C/D/E + combined (rB/rC/rH) são sintéticos. **Bloqueador de fidelidade** (ver `REFERENCES` C.2).
3. **Fudges de calibração → YAML** (2026-07-03/04): extraídos p/ `qss_calibration` (cx_offset/
   cl_offset/mu_scale/prepass_grip_derate) + `tires.rolling_resistance`; defaults neutros no código.
   **Ainda são dívida**: substituir por física real (load sensitivity μ(Fz), aero medido), pesquisa.
4. ~~Dois modelos de torque divergentes~~ **RESOLVIDO 2026-07-04 (T03)**: seleção de marcha unificada
   em `Engine.torque_at` nos 2 solvers; re-baseline 87,54 s. Python = fix espelho pendente (task chip).
5. **DRY parcial:** `Tire.mf62_combined` agora é fonte única do pneu (solver chama 4×, esta sessão).
   **Faltam** `Suspension`/`Brakes`/`Aero`/`Transmission`, ainda inline no solver, módulos órfãos.

## Próximos passos (ordem), ✅ FORK #1 RESOLVIDO (rota B)
> Instrumento: `solve_lap_14dof(...; return_internals=true)` + `export_telemetry(res)` → CSV/HDF5 com
> Fz/alpha/kappa/**Fx_tire/Fy_tire**/T_tire por canto (canais de força adicionados p/ validar a elipse).

1. **✅ FORK #1, convergência restaurada (rota B, pure-slip estabilizado).** Feito: TCS + floor Gxa/Gyk
   + elipse de Kamm + de-rate do alvo QSS → **102,3s limpo/honesto** (ver "Status real"). Guardrail
   re-travado (`@test`, não `@test_broken`). **94±1 fica p/ o driver NMPC** (é linha/driver, não grip).
2. **✅ Refino de pace, TAPADO** (feito esta sessão): de-rate ótimo em 0,85 (0,88 mais lento), throttle
   suave (`K_p_throttle` 2,0→1,0) → 102,0s. Ganhos de driver rendem só ~0,3s → **98/94 exige NMPC**, não
   tuning. Aberto p/ depois (menor prioridade): balanço oversteer (tras. util 1,05 > diant. 0,92, via ARB/bias).
3. **Driver NMPC** → dirigir no limite na linha ótima p/ 94 honesto. `DriverMPC.jl` é MPC **funcional**
   (bicycle cinemático + L-BFGS c/ caixa, testado), só falta **conectar** ao lap loop. Plano de escopo
   completo (arquitetura, milestones, riscos): **`docs/STAGE3-NMPC-DRIVER-PLAN.md`**.
4. **`.tir` GT3 real** (ou MF6.2 genérico slick) → substituir B/C/D/E + rB/rC/rH sintéticos. Hoje só
   há Pirelli SUV em `~/Projects/_shared/tire_data/`. Parser `.tir` (`TirParser`) já existe.
3. **DRY restante:** extrair `Suspension`/`Brakes`/`Aero`/`Transmission` inline → módulos (padrão de
   `Tire.mf62_combined`: função que constrói expressão simbólica, chamada do solver, preserva AD).
4. **Validação por canais** (não só lap-time): usar a telemetria nova p/ overlay vs referência.

## Decisões da sessão (Vitor, 2026-06-29)
- **"Tunar agressivo até passar":** priorizar fazer `solve_lap_14dof` cair em 94 ± 1, calibração aceita como dívida explícita (registrada acima), docs honestas no fim. (Escolha do Vitor via prompt.)
- Mantidas as decisões de 2026-06-28: descarte do `Multibody` (hand-rolled MTK), 14-DOF com todos os subsistemas no path, ISO 8855 obrigatório no 14-DOF / QSS fica em SAE J670 isolado.

## Fase 3 (AI Driver Model), commitado + parcialmente real (2026-06-30)
`src/ai/{DriverMPC,GaussianGripEstimator,TubeGenerator}.jl` agora **commitados** + com cobertura de teste.
- [x] **(a)** Bug de bounds do MPC **CORRIGIDO**: `solve(prob, LBFGS())` → `Fminbox(LBFGS())`
  (`OptimizationOptimJL`, sem dep nova). **Achado bônus:** `mpc_cost` não era genérico de tipo
  (`x`/`dx` `Float64` fixos → `Float64(::Dual)` quebrava sob `AutoForwardDiff`), também corrigido.
  Teste real de `solve_mpc_step!` prova que o bound morde (accel trava em 5.0).
- [x] **(e)** Commitado + testado (cobertura em `src/ai/` + telemetria).
- [ ] **(b)** Decidir `ModelPredictiveControl.jl` (pacote dedicado) vs hand-rolled em `Optimization.jl`.
- [ ] **(c)** `GaussianGripEstimator.jl` ainda **stub** (`predict_grip_band` retorna banda fixa, nem
  importa `AbstractGPs`), implementar GP de verdade. **Fora de escopo desta sessão.**
- [ ] **(d)** `TubeGenerator.jl`/`init_ancillary_controller` ainda **stub** (ganho identidade), resolver CARE de verdade (precisa `MatrixEquations.jl`, não é dep). **Fora de escopo desta sessão.**

## Anotado p/ próxima sessão (achados fora de escopo, NÃO mexidos)
- **GP real** (`GaussianGripEstimator`): hoje retorna banda fixa. Implementar `AbstractGPs` (dep já existe).
- **LQR/CARE real** (`TubeGenerator.init_ancillary_controller`): hoje ganho identidade. Precisa `MatrixEquations.jl`.
- **Gear-selection duplicada:** `run_qss_prepass` usa `select_gear_optimal` inline (curva sintética
  `T_max=505`+exp), diverge de `Transmission.select_gear` (módulo órfão). Unificar fonte de marcha.

## Sessão 2026-06-30 (refino tire-dynamics + Phase 3), log
- **Diagnóstico:** 14-DOF está RED (DNF 150 s), não 94,42 s. Regressão = `4f4a0dc` (ver Status real).
- **Feito:** (1) Gxa/Gyk MF6.2 corrigido (forma canônica, usava `κ²·rBx2·α` dimensionalmente errado +
  `rBx2`/`rHx1` órfãos); (2) μ peak sourced do YAML `pacejka_D` (não `dummy.tir` placeholder);
  (3) DRY do pneu p/ `Tire.mf62_combined` (behavior-preserving, AD-safe); (4) bug duplo do MPC;
  (5) `export_telemetry` HDF5/CSV (`src/io/TelemetryExport.jl`, 28 canais c/ Fz/slip/temp por canto);
  (6) `runtests.jl` honesto (`@test_broken` no guardrail). Nada disso restaura convergência (esperado, é Fork #1). QSS 93,03 s **intacto**.
- **Inconsistências de doc corrigidas** (pedido do Vitor): SPM/ROADMAP/CLAUDE(repo)/ARCHITECTURE diziam
  "94,42 s GREEN" + "grip_cal=1.30", falso desde `4f4a0dc`. Reconciliado p/ estado RED real.

## Sessão 2026-07-01 (recuperação equações KB + revisão doc-vs-código), log
- **Achado:** os research docs da `saru-KB` synced do Drive têm as **equações como imagem PNG
  embutida** (export Gemini→GDoc rasteriza a math); `read_file_content` e export markdown **perdem** tudo.
- **Recuperado (8 docs):** pipeline extrai base64 → filtra por tamanho (>1,5KB = eq real, ~15-40/doc de
  ~100-190) → `montage` → OCR visual → LaTeX. Escritos **8 companheiros `- EQUATIONS.md`** (não-destrutivo,
  não toca o original). Método na memória `drive-gdoc-equation-recovery`.
- **Optimal Lap MPC recuperado 100%**, fecha os gaps M2/M3 do NMPC (single-track curvilíneo, elipse
  soft+slack, mapa inverso atuador, actuator smoothing 1ª ordem = o risco 🔴 do crash do stiff solver).
- **Revisão doc-vs-código** (`docs/AUDIT-FINDINGS.md §2026-07-01`): **FLAG 1** `pacejka_B=22.0` contradiz
  `cornering_stiffness=85k/100k` na mesma YAML (2,6×); fix `B_f=8,43/B_r=9,92` documentado em 2 docs, nunca
  aplicado (mascarado pela elipse de Kamm no pico, mas erra transiente/slip angles + importa p/ NMPC).
  **FLAG 2** `torque_cal=1.15` ativo. **FLAG 3** `QNDF` vs `TRBDF2` recomendado. `grip_cal=1,0` ✓, MF6.2 ✓.
- **Ordem do Vitor:** M1 **deferido**; próxima sessão = mover arquivos + conferir equações + auditar
  branches saru-core/saru-os (só documentar). Ver `docs/NEXT-SESSION-PROMPT.md`. Commit `09f4fa5`
  (saru-core-jl, docs); os 8 `- EQUATIONS.md` já commitados no workspace por `a90995b` (auto-reorg).

## Sessão 2026-07-01b (conferência equações + audit integração item 2), log
- **8 `- EQUATIONS.md` conferidos** (cross-check interno + re-extração de imagem onde precisou). 6/8 limpos.
  3 flags reais → memória `kb-equation-flags-f1-f2-f3`: **F1** transferência lateral (erro de FONTE, OCR
  fiel, confirmado por `image54/55`: `a_y` fora do colchete multiplica termo elástico `K_φ·φ`, dim-errado;
  + typo OCR `m_{s,f}`→`m_{u,f}`); **F2** `B=C_α/(C·μ·Fz0)` OK (= B=22 fix já conhecido); **F3** mapa de
  freio sem `R_eff` no numerador. Todos verificáveis por análise dimensional, **sem deep-research**.
- **Deep-research:** prompt preparado **inline no chat** (Física/Sim/Otim + Julia zero-alloc + F1/F2/F3),
  NÃO filed (corrigido: violei SGM §5 criando `.md` de prompt → deletado; memória `no-prompt-files-inline`).
  Plataforma recomendada: **Gemini Deep Research** (amplo) + **Perplexity** (cross-check F1/F2/F3).
- **Draft arquitetura de módulos (Física/Sim/Otim)** feito como texto (provisório, reconciliar c/ pesquisa).

## Integração worker (item 2, SITUAÇÃO, não implementar)
> Auditoria read-only cross-repo (saru-core / saru-os / saru-core-jl). Fonte: MASTER_ADR, ADR-0005, ADR-0007, SGM.
- **Contrato como DESENHADO** (ADR-0007): BFF NestJS = borda única. 2 regimes: síncrono (lap-time QSS Python,
  `/api/v1/lts/run`→engine) · **assíncrono** (14-DOF Julia → **enfileira Redis** → worker consome → polling/ws).
  14-DOF entra "atrás do mesmo contrato `/simulate`, novo valor de `model`" (ADR-0005).
- **GAPS p/ saru-core-jl virar worker de verdade:**
  - **G1 ✅** Fila Redis + módulo Nest `jobs` = **Implementados** (via `BullMQ` no BFF e `RedisWorker.jl` no Julia, conectando SSE).
  - **G2 🟠** Contrato não formalizado: `shared/` (MASTER_ADR §1) reservado p/ protos mas **vazio**. YAML+HDF5→
    lap_time+telemetria só documentado em prosa, sem schema versionado na fronteira.
  - **G3 🟠** Mismatch de serialização: engine fala **JSON/HTTP**; worker Julia fala **arquivo** (YAML/HDF5 in,
    HDF5 out via `TelemetryExport`). O esqueleto de consumo JSON via Redis existe, mas parse de setup ainda precisa acoplar ao `solve_lap_14dof`.
  - **G4 ✅** Ambiguidade de dono do 14-DOF: ADR-0010 (saru-os) decidiu que `saru-core-jl` é o dono e a Single Source of Truth do setup.
  - **G5 ✅** Worker Julia sem entrypoint de consumo de fila. **Implementado:** `src/io/RedisWorker.jl` é o daemon de consumo que emite telemetria via Pub/Sub.
- **Branches ativas:** saru-core `feature/tire-dynamics-refinement`(+`claude-test-hardening`); saru-os
  `feature/claude-shell-2tier-weather-lts`[ahead 1]; saru-core-jl `feature/tire-dynamics-refinement`[ahead 1, PR#2];
  umbrella `SARU` (`vitormtt/SARU`) `feature/claude-ignore-platform`(HEAD=`a90995b`, repo onde drive-reorg
  committa, **é o meta-hub, não `telemetry-service`**; este último é dir vazio dentro de `platform/`, sem git próprio).
- **Recomendação:** ADR novo em `saru-os/docs/adr/` (job contract assíncrono + integração worker Julia), criar
  em **sessão saru-os** (isolamento), quando Vitor der OK. Não criado aqui (cross-repo + anti-lixo).

## Decisão arquitetural, 2-tier + auto-gen do tier rápido (ADR-0010 pendente)
> Fonte: deep-research **"Unificação Modelos GT3 via Surrogate/ROM"** (Drive 2026-07-01 18:06, lido).
- **Veredito:** ❌ REJEITAR surrogate neural / unificação end-to-end (custo de dados proibitivo p/ solo dev
  ~10⁴ sims; violação física fora do envelope; latência de retreino mata interatividade; CTESN/MOR.jl/
  Multibody.jl imaturos p/ DAE mecânica c/ descontinuidade ABS/marcha/Filippov). ✅ MANTER 2 tiers.
- **Adotar "Unificação Física-Cinemática":** (1) fonte única de params em Julia (`VeiculoSetup.jl`);
  (2) tier rápido **gerado do master Julia** via MTK simbólico (3-DOF/QSS) → UI via C-API/PyCall.jl;
  (3) K&C via **lookup tables** (14-DOF offline mapeia cinemática → online 1000 Hz, padrão VI-CarRealTime).
  IA só modular em subcomponente lento/contínuo (térmico pneu/freio), nunca o carro end-to-end (Astemo AI-MBD).
- **🔴 TENSÃO → ADR-0010:** auto-gen via PyCall contradiz "sem ponte em-processo (juliacall/pyjulia), fila"
  (CLAUDE.md saru-core-jl / MASTER_ADR). Reconciliar distinguindo **tier-rápido-UI** (bridge leve OK) vs
  **worker-14DOF-pesado** (fila, ADR-0007). Também: saru-core (Python) viraria **artefato gerado** do
  saru-core-jl, não oráculo independente → reconciliar c/ ADR-0005 (dono 3-DOF) + MASTER_ADR §4.
- **ADR-0010** (saru-os) draft pronto (Status/Contexto/Decisão/Consequências), **aguarda ratificação +
  commit em sessão saru-os** (isolamento). Doc-fonte está **fora da pasta-KB** (`0AHG9...`) → não sincroniza.

## Digest pesquisa Julia/solver (3 docs Drive 2026-07-01, lidos na íntegra, comparados c/ corpus)
- **"Simulação 14-DOF Julia" + "Otimização Simulador Julia"** (convergem forte, escopo saru-core-jl):
  - **Causa-raiz do 50s/volta = QNDF colapsa passo em descontinuidade** (zebra/step throttle); **TRBDF2**
    (single-step L-estável, sem história) recupera na hora → **valida AUDIT FLAG 3 (agora 3 fontes)**.
  - **Actuator smoothing 1ª ordem** (`τ·du/dt=u_cmd−u`) mata descontinuidade C0 → **é o lever M1 do NMPC**
    (STAGE3), agora validado externamente. **sysimage PackageCompiler** TTFX 15min→<3s → resolve pendência
    do **Dockerfile**. Zero-alloc **StaticArrays** (draft J1). Batch = **EnsembleThreads CPU >> GPU**
    (branch-divergence do Pacejka mata SIMD; 25ms vs 210ms/1000 runs). Init = **ShampineCollocationInit**
    (endereça nossa warning "overdetermined init"). **acados** (C/C++) como opção de solver NMPC rápido.
- "Análise Telemetria Automobilística": escopo **saru-os/telemetria** (não física saru-core-jl). 2 personas
  (driver-coaching × engineering-analysis) + arquitetura de ingestão.
  - **🔴 C1 CONTRADIÇÃO (higiene, regra pt3):** recomenda **Kafka+ClickHouse+Flink**; V1 do SGM/ADR-0004 =
    **Postgres simples** (Kafka/Timescale = V2 diferido). Research = **V2-aspiracional, NÃO adotar em V1** →
    tratar na sessão dedicada de telemetria (task filada) + saru-os.
  - **Dedup:** ~4 docs de telemetria sobrepostos na KB (este + "Telemetria e KPIs" + "Análise Telemetria e
    Simulação" + "Telemetry Interface Arch") → consolidar.
- Equações rasterizadas de novo nos 3 (Table1 freq, actuator, oversteer, Δt), padrão/código, baixa perda.

## Scope R1 (térmico/pressão pneu), gaps de código + padrão VI-CRT (2026-07-01)
> Inspeção do plant real ([Transient14DOF.jl:689-719](src/simulation/Transient14DOF.jl)) + corpus VI-CRT
> (`VI_CRT_Architecture_Analysis.md` · `EMS_vs_SARU §13` = doc oficial 2025.1/1505pág · `SARU_Fisica §1.5`).
- **Plant = MTK acausal puro** (ODESystem→structural_simplify→ODEProblem). Sem `f!` manual, sem StaticArrays, codegen MTK cuida de alloc/tipo (type-generic, Dual flui). StaticArrays/lookup-3D valem SÓ p/ modelos
  hand-written (tier rápido ADR-0010, predição NMPC). **⚠️ Anti-pattern: Interpolations.jl no plant MTK
  quebra simbólico/AD**, no plant, μ(T) fica simbólico.
- **GAP T1, térmico 1-nó:** `D(T_tire)=(Q_fric−hA·(T−25))/C_th`, C_th=5000/hA=50 (τ=100s), Q_fric=
  |Fx·(ωR−vx)|+|Fy·vy|. Sem pressão interna, sem nós surface/tread/carcass. Research pede 2-3 nós.
- **GAP T2, μ_eff ALGÉBRICO** (instantâneo f(T_tire)); sem τ de preparação de borracha. Alternativas:
  μ memory-state (τ 15-45s GT3, sugestão R1) OU 2º nó térmico, **escolher 1, não ambos** (memória já
  existe via T_tire). + cold-start: `T_init=80°C` hardcoded, sem sigmoid de largada.
- **Padrão VI-CRT (interno, doc oficial):** 14-DOF paramétrico igual ao nosso; **K&C = lookup XML**
  (Adams/K&C-rig, zero multibody online) → responde R1 ponto 5; pneu via **STI** (MF-Tyre/FTire plug),
  normais injetadas >1000 Hz; SpeedGen QSS bisseção + demand gates; Performance Factors/Tables =
  calibração oficial; SpeedGenEvo (5-body+splines) = nosso degrau A4→A5.
- **Insight numérico (validar na pesquisa):** ODE térmica LENTA (τ=100s) **não enrijece** o DAE, stiffness
  vem de autovalor RÁPIDO. Estado lento no mesmo DAE ≈ inofensivo (custo = Jacobiano maior). Multi-rate
  só se justifica p/ CUSTO, não estabilidade. VI-CRT roda fixed-step 1kHz c/ térmico junto (a confirmar).
- **Falta pesquisar (add-on curto, Vitor cola):** como VI-CRT/FTire-TGM/TameTire acoplam térmico↔força
  (in-step vs co-sim multi-rate) + como STI passa T/P/μ-scaling (λ_μ) + MF-Tyre thermal add-on oficial.
- **R1 pontos 1,2,4,5 rodando**, Vitor avisa quando fechar. Resposta factual sobre nosso `f!` (pergunta
  do AI) entregue no chat (plant é MTK-codegen, não hand-f!).

## Pendências de infra
- Testes unitários por componente são inexistentes.
- Dockerfile de produção não validado.
- ~~Versionamento do HDF5 do circuito~~ **RESOLVIDO de facto** (verificado 2026-07-15):
  `reference/interlagos.hdf5` + `vehicle_992_gt3_r.yaml` estão trackeados no git (CI roda com eles).
- Sincronização com origin: `develop`==`origin/develop` (sync); `feature/tire-dynamics-refinement`
  **pushado** + **PR #2** aberto p/ `develop` (reviewer viniciusvieira00), aguarda review/confirmação.
  `main` local ainda à frente de `origin/main` (release pendente, OK do Vitor p/ push da main).
- Warning MTK na init: "Initialization system is overdetermined (1 eq / 0 unknowns)", usa least-squares, não bloqueia; revisar.

## Sessão 2026-06-30 (Track A, convergência 14-DOF), log
- **Ordem dos 4 experimentos confirmada pela pesquisa** (`Refinamento Dinâmica Veicular 14-DOF.md`):
  TCS → floor Gyk → elipse Kamm → reconciliar alvo driver. Cada um = 1 solve (~50s) + telemetria.
- **Feito (ladder empírico):** baseline DNF(s≈579m) → Exp1 TCS κ=0,10 DNF(s≈1412m, rodaspin morto) →
  Exp1b TCS κ=0,05 **completa 115,9s** → Exp2 +floor 0,40 **101,6s limpo** → Exp3 +elipse Kamm 128,5s
  (expôs grip fake u>1 do 101,6) → Exp4 +de-rate 0,85 **102,3s limpo+honesto** (util≤1,05).
- **Descoberta-chave:** 94±1 é artefato QSS ponto-massa; gap 102→94 = linha/driver, não grip → NMPC.
  Detalhe na memória `honest-14dof-lap-vs-qss`. Canais de força (`Fx_tire`/`Fy_tire`) add à telemetria.
- **Commit:** `feat(tire-dynamics)` c/ as 4 alavancas + guardrail re-travado (`@test`). QSS 93,03s intacto.
- **Aprovado pelo Vitor:** rota B (pure-slip), path físico (Exp 3+4), commit 102 → refinar → NMPC.
- **Refino (pace):** de-rate **ótimo em 0,85** (0,88 → mais lento: driver desliza mais). `K_p_throttle`
  2,0→1,0 (throttle suave, mata over-drive de saída) → **101,96s** + mais limpo (e_y 1,53m, slip tras.
  10° vs 13°). Ganhos de driver tapam só ~0,3s → **98/94 exige NMPC**, não tuning. Commits: `6eb34a6`
  (baseline 4 alavancas) + `92805ac` (refino throttle) + `7946a14` (plano Stage 3 NMPC).
- **Push + PR:** `feature/tire-dynamics-refinement` pushado; **PR #2** aberto p/ `develop`
  (reviewer viniciusvieira00), https://github.com/vitormtt/saru-core-jl/pull/2.
- **Prompt de pesquisa Stage 3** gerado (p/ Vitor colar no Gemini/Perplexity), cenário atualizado
  (102s honesto, gap driver/linha, MPC funcional-mas-não-conectado, mismatch cinemático×dinâmico).

## Guardrail
QSS de regressão: **87,54 s** (re-baseline 2026-07-04 pós-T03, aprovado Vitor; antes 93,03 co-calibrado
c/ seletor errado). Não pode regredir (≥0,5 s → reportar + aprovar antes do commit). **Interim**: novo
re-baseline previsto quando fudges morrerem c/ física real (load sensitivity + aero medido).
14-DOF **CONVERGE 109,28 s limpo** (2026-07-15 pós-FLAG1: B por eixo de C_α, derate 0.70; e_y ≤1,8,
slips ≤12/13°, util ≤1,05, canais são o critério, não o número; o 100,7 anterior era co-calibrado
c/ pacejka_B=22 rígido demais). `@test_broken 94±1` mantido como alvo NMPC. Anti-padrão fake-grip
continua valendo: nunca tunar pneu/grip p/ bater lap, memória `physics-first-no-result-tuning`.
