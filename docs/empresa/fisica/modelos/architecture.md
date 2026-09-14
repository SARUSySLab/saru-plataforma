---
titulo: "saru-core-jl, Arquitetura"
data: "2026-06-30"
origem: "_arquivo/saru-physics-jl/docs/ARCHITECTURE.md"
status: "vigente"
area: "arquitetura_software"
---

# saru-core-jl, Arquitetura

> SoT de arquitetura do worker 14-DOF. Estado vivo → `SPM.md`. Decisões → `docs/adr/`.
> Referências/params/pesquisa → `docs/REFERENCES-AND-RESEARCH.md`. Última revisão: 2026-06-29.

## 1. Papel no ecossistema
Worker assíncrono (fila Redis no `saru-os`) de **dinâmica veicular transiente de alta-fidelidade**.
Contraparte do QSS Python (`saru-core`), que cobre lap-time **síncrono**. Este cobre sims pesadas/DoE.

- **Contrato (fronteira):** entrada = vehicle **YAML** + track **HDF5** → saída = `lap_time` + telemetria (canais).
- **Sem ponte em-processo** (juliacall/pyjulia). Desacoplado por fila.
- **Oráculo:** Porsche 992 GT3 R @ Interlagos, **94,0 s ± 1,0**. Guardrail: não regredir.

## 2. Fronteira QSS-port (baseline) vs 14-DOF (implementado)
| | QSS-port (`Harness.jl`, baseline) | 14-DOF (`Transient14DOF.jl`) |
|---|---|---|
| Método | ponto-massa fwd/bwd friction-circle | DAE acausal hand-rolled (`QNDF`) |
| Estados | 1 (v ao longo de s) | **14** (ver §3) |
| Tempo | pós-processo (v→t) | integração transiente real |
| Pneu | mu escalar | Pacejka MF6.2 pure-slip-por-eixo + Gxa/Gyk + load-sens. + térmico |
| Lap | 93,03 s ✅ | **🔴 DNF (150 s)**, regrediu do 94,42 s (`bb8f6c9`) |
| Valida | reproduz o método do oráculo (tautológico) | **não converge**, ver Fork #1 (`SPM.md`) |

> O QSS-port serve de **baseline/regressão** (intacto). O 14-DOF **batia** o oráculo em `bb8f6c9`
> (94,42 s), mas o commit `4f4a0dc` reestruturou o pneu p/ pure-slip-por-eixo e quebrou a convergência
> (DNF), o driver inalterado não dirige o novo campo de força. Diagnóstico: `docs/AUDIT-FINDINGS.md` §6.

## 3. Os 14 DOF (formulação canônica)
Corpo rígido (sprung) + rodas (unsprung), eixo **ISO 8855** (x-frente, y-**esquerda**, z-**cima**; downforce Fz **< 0**), convenção global do ecossistema (ver [MASTER_ADR.md](../../../docs/adr/MASTER_ADR.md) §3.1):
- **Chassi (6):** translação `x, y, z` + rotação `roll φ, pitch θ, yaw ψ`.
- **Curso vertical das 4 rodas (4):** `z_fl, z_fr, z_rl, z_rr` (massa não-suspensa).
- **Rotação (spin) das 4 rodas (4):** `ω_fl, ω_fr, ω_rl, ω_rr`.

Acoplamento: suspensão liga chassi↔unsprung (vertical); pneu liga unsprung↔solo (Fx/Fy/Fz + Mz) e spin↔chassi (tração/frenagem). Drivetrain injeta torque nos spins traseiros (RWD).

## 4. Hierarquia de fidelidade por subsistema
Cada subsistema sobe níveis (Lk) conforme params disponíveis. **Limite = params do YAML**, não inventar coeficiente sem fonte. Default de produção = L mais alto que os params sustentam.

| Subsistema | L0 | L1 | L2 | L3 | Params YAML disp. |
|---|---|---|---|---|---|
| **Tire** | linear (Cα) | Pacejka MF pure-slip | + combined-slip (elipse) | + térmico + load-sensitivity | B,C,D,E, Cα f/r, radius |
| **Suspension** | spring+damper linear | + bump/droop + ARB | multibody (motion ratio, camber) | + kinematics 3D | k, c, ARB f/r |
| **Brakes** | cap max-decel | bias + p→torque | + thermal fade |, | bias, max_force, response_t |
| **Transmission** | ratio fixo | gear-select + shift time | + diff (open/locked/LSD) |, | ratios, final, shift |
| **Engine** | max-T × throttle | mapa 2D `T(rpm,thr)` | + response lag + engine-brake (FMEP) | MVEM (overkill p/ NA) | torque_curve, rpm, power |
| **Aero** | Cd/Cl fixo | mapa vs speed | mapa 3D (speed, ride-h, sideslip) | + stall | cx, cl_f/r, area |

> Detalhe do modelo de torque escolhido + análise física dos fudge factors: `docs/AUDIT-FINDINGS.md` §4.

## 5. Stack
Julia ≥1.10 · `ModelingToolkit` v11 (DAE simbólico) · `DifferentialEquations` (FBDF/QNDF/Rodas5 p/ DAE stiff) · `YAML`+`HDF5` (I/O contrato) · `LinearAlgebra` · `Test`.

