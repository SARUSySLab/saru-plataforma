---
titulo: "saru-core-jl, Roadmap"
data: "2026-07-07"
origem: "_arquivo/saru-physics-jl/docs/ROADMAP.md"
status: "stale"
area: "dinamica_veicular"
---

# saru-core-jl, Roadmap

> Tasks faseadas, corte vertical. SoT de arquitetura → `docs/ARCHITECTURE.md`. Estado → `SPM.md`.
> Última revisão: 2026-06-29.

## Fase 1, QSS port (baseline) ✅
Port do solver QSS ponto-massa p/ Julia concluído e mergeado na develop (93,03 s). Serve de regressão para o lap-time.
- ✅ Remover `hot.md` + `SARU_PROJECT_MEMORY.md` antes de mergear.
- ✅ Corrigir docs p/ "QSS port baseline, não 14-DOF" (feito no `develop`).
- ✅ Unificar os dois modelos de torque em uma fonte única.
- ✅ Remover dependência do `Multibody` fake do `Project.toml`.

## Fase 2, 14-DOF DAE acausal 🔴 (REGREDIU p/ DNF, não converge)
Objetivo: substituir o ponto-massa por modelo 14-DOF (ver `ARCHITECTURE.md` §3), com **todos** os subsistemas no caminho de cálculo simbólico. Guardrail: lap-time não regride 94,0 ± 1,0.

> **Estado 2026-06-30:** `solve_lap_14dof` **não converge**, DNF (150 s = teto `tspan`). Regrediu do
> 94,42 s (working em `bb8f6c9`). O commit `4f4a0dc` reestruturou o pneu (resultant-slip →
> pure-slip-por-eixo MF6.2 + Gxa/Gyk) e o driver inalterado não dirige o novo campo de força (sai da
> pista em s≈590 m). **Restaurar = Fork #1** (`SPM.md`). `grip_cal` já é 1.0 (não 1.30); μ peak vem do
> YAML; pneu agora DRY em `Tire.mf62_combined`. Diagnóstico empírico: `docs/AUDIT-FINDINGS.md` §6.

### 2.0, Andaime DAE + chassi 6-DOF ✅
- [x] Corpo rígido 6-DOF hand-rolled (massa suspensa, inércias do YAML, Newton-Euler), inline no solver.
- [x] `structural_simplify` + solver `QNDF` estável na volta completa de Interlagos.
- [x] `ModelingToolkit` v9/v11 + `@register_symbolic` p/ interpolações de pista (black-box).

### 2.1, Rodas: 4 vertical + 4 spin (→ 14 DOF) ✅
- [x] Massa não-suspensa + curso vertical por canto (4 DOF).
- [x] Spin de roda + acoplamento drivetrain→spin traseiro com LSD (4 DOF, RWD).

### 2.2, Subsistemas no path ✅ física / 🔴 arquitetura
Toda a física está no caminho de cálculo, porém **inline no `Transient14DOF.jl`**, os módulos
`src/components/*` foram editados mas **não são chamados** (só `Engine`). **Débito DRY: extrair p/
os módulos ou remover órfãos** (ver `SPM.md` próximos passos).
- [x] **Tire**, Pacejka combined-slip (resultant-slip) + load-sensitivity (`K_LS=0.20`), inline.
  - [ ] Parser `.tir` (MF6.2) p/ substituir B/C/D/E do YAML por dado real. **Template:**
    `~/Projects/_shared/tire_data/225_60R18_65J_SCORPN_..._TIR_V001.tir`.
- [x] **Suspension**, spring + damper + bump + ARB por canto, acoplada a roll/pitch/heave, inline.
- [x] **Transmission**, gear-select (perfil do prepass) + LSD smooth, inline.
- [x] **Brakes**, bias + pressão→torque por canto + ABS-tanh, inline.
- [x] **Engine**, tabela 2D (`Engine.torque_at`) + lag 1ª ordem + engine-brake. **Único módulo chamado.**
- [x] **Aero**, downforce/drag vs v² (ISO: `Fz<0`), inline.

### 2.3, Eliminar fudge factors 🔴 (pioraram nesta fase)
A convergência adicionou **2 novos fatores de calibração** (`grip_cal`, `torque_cal`) além dos
herdados no prepass. Substituir cada um por física (análise em `docs/AUDIT-FINDINGS.md` §4):
- [ ] **`grip_cal=1.30`** (novo) → calibrar grip lateral/longitudinal com dado de pneu `.tir`, não escalar `mu`.
- [ ] **`torque_cal=1.15`** (novo) → reconciliar tração RWD/combined-slip na saída de curva.
- [ ] `cd+0.06`, `cl−0.12`, `mu·0.968`, rr `0.015` (prepass) → física correta (ver itens originais).
- [ ] temp `65°C` → modelo térmico do pneu.
- [ ] **Params hardcoded no solver** → mover p/ YAML/`.tir`: `m_u=45`, `Iw=1.5`, `Kt=250000`, `Fz0=4000`.
- [ ] **`cornering_stiffness` do YAML é ignorado** (solver usa B/C/D/E ⇒ Cα≈2.6× o spec). Reconciliar.

> Comparação param-a-param vs referência + agenda de pesquisa: **`docs/REFERENCES-AND-RESEARCH.md`**.

### 2.4, Validação por canais (não só lap-time)
- [ ] Overlay vs telemetria: vel, acel lat/long, slip, temp pneu, RPM/marcha. Métricas de erro por canal.
- [ ] Anti-padrão a evitar: calibrar p/ casar **1 número**. Validar os **canais**.

## Configurabilidade (meta de produto)
Expor params/configs do veículo p/ otimização (DoE): níveis Lk por subsistema, mapas, k/c/ARB, bias, ratios, aero. Tudo via YAML, sem magic numbers no código.

## Fontes canônicas p/ Fase 2 (PORTAR, não reinventar)
A física já está documentada/implementada no ecossistema. Evitar a duplicação ou divergência de modelos (ver [MASTER_ADR.md](../../../docs/adr/MASTER_ADR.md) §3.2). Ordem de prioridade:
- **14-DOF de referência (mais maduro):** `~/Projects/01_UnB/FullVehicleSimulation/` (MATLAB), `classes/VehicleModel14DOF.m`, `VehicleSystem14DOF.m`, tese `docs/thesis_draft_unb/modelagem_14dof.tex`.
  ⚠️ Está em **SAE J670** → converter p/ **ISO 8855** ([MASTER_ADR.md](../../../docs/adr/MASTER_ADR.md) §3.1) ao portar.
- **State-vector + equações + solver:** `platform/saru-core/docs/vehicle_model_theory.md` (14 estados, MF5.2, LTD, `ode15s` → Julia FBDF/QNDF).
- **Params reais + Pacejka MF6.2 GT3 calibrado + inércias:** pesquisa bruta arquivada no Drive (`04_ARCHIVE`); destilada em `saru-KB/SARU_Fisica_e_Simulacao.md`.
- **Pneu (catálogo .tir, térmico, relaxation):** `platform/saru-core/docs/tire_physics.md`.
- **Justificativa acausal/MTK:** `saru-KB/30_simulation/Guia Modelagem Causal vs Acausal.md`.

