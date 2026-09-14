---
titulo: "saru-core-jl, CLAUDE.md"
data: "2026-07-15"
origem: "_arquivo/saru-physics-jl/CLAUDE.md"
status: "vigente"
area: "dinamica_veicular"
---

# saru-core-jl, CLAUDE.md

Solver de **dinâmica veicular transiente 14-DOF** em **Julia** (ModelingToolkit.jl, DAE acausal
hand-rolled, Multibody **descartado**). Contraparte de alta-fidelidade do solver QSS de lap-time do
`saru-core` (Python). Roda como **worker assíncrono** nos serviços de cálculo do produto `saru-os`
(fila Redis), **não** em-processo.

> Status real (2026-07-15d, ver `SPM.md`):
> - **Suite verde.** **QSS ponto-massa** (`src/validation/Harness.jl`) = **87,26 s** (re-baseline
>   2026-07-15c: load sensitivity real **k=−0,12** aplicado, pesquisa 2 fontes, semântica Fz0
>   documentada no YAML, e fudge `mu_scale` morto por dupla contagem).
> - **✅ 14-DOF transiente CONVERGE honesto = 109,48 s** (`src/simulation/Transient14DOF.jl`):
>   Interlagos determinístico, e_y 1,45 m, slips 5,7/11,2°, util ≤0,794. Cadeia 2026-07-15 de
>   fixes por física (cada um re-validado por canais): **FLAG 1** B por eixo de C_α (8,43/9,92;
>   o 100,7 antigo era co-calibrado c/ B=22, lição T03) → **geometria 40F/60R** (lf/lr estavam
>   codificando 56% DIANTEIRA; Iz→2450) → **seed .tir S2** (combined rB/rC/rH reais via
>   `tires.tir_file`; clamp positivo nos pesos Gxa/Gyk). Derate re-ladder por canais → **0,68**.
>   Guardrail = "completa + fisicamente sã", não 94±1. Fudges restantes no YAML (cx/cl offsets,
>   torque_cal, derate); matar c/ física = `AUDIT-FINDINGS §7.7` (aero S3 + motor S4 = V2;
>   **pDy2 −0,20 travado até prepass virar g-g-v**).
> - **94±1 = alvo do driver NMPC.** util ≤0,79 = grip sobrando; gargalo é o **driver P
>   cinemático** (plano: `docs/STAGE3-NMPC-DRIVER-PLAN.md`). Tunar pneu p/ lap = fake grip
>   (anti-padrão). Ver memória `honest-14dof-lap-vs-qss`.
> - **Worker G3 fechado (2026-07-15):** `RedisWorker` resolve `vehicle`/`track` por nome em
>   `reference/` (erro honesto se inexistente) + `setup_overrides` via `src/io/VehicleSetup.jl`
>   (loader + validador de schema c/ warn de drift, seed do ADR-0010 §1).

## 1. Stack
- Julia ≥1.10. Deps: `ModelingToolkit` (DAE simbólico), `DifferentialEquations` (integração ODE/DAE,
  `QNDF`/`FBDF` p/ stiff), `HDF5`+`YAML` (I/O contrato), `LinearAlgebra`, `Test`. (Multibody descartado.)
- Comandos: instanciar = `julia --project -e 'using Pkg; Pkg.instantiate()'` ·
  testes = `julia --project -e 'include("test/runtests.jl")'`

## 2. Arquitetura & papel no ecossistema
- **O que computa (alvo Fase 2):** 14-DOF transiente (corpo 6-DOF + 4 rodas + drivetrain/freios),
  suspensão multibody, pneu Pacejka+térmico, mapa aero 3D. Saída: telemetria + `lap_time`.
  Hoje o que existe (branch) é um QSS ponto-massa, esta é a meta, não o estado atual.
- **Onde roda:** worker assíncrono (fila Redis) nos serviços de cálculo do `saru-os`, para sims
  pesadas/DoE. O QSS (Python, `saru-core`) cobre o lap-time **síncrono**; este cobre alta-fidelidade.
- **Contrato (fronteira):** entrada = vehicle **YAML** + track **HDF5**; saída = `lap_time`
  (+ telemetria). **Sem ponte em-processo** (juliacall/pyjulia), desacoplado por fila.
  Ver `saru-os/docs/adr/` e o `CLAUDE.md` do `saru-core`.
- **Validação (oracle):** `src/validation/Harness.jl` compara contra o QSS Python, Porsche 992 GT3 R @ Interlagos, **94,0 s ± 1,0 s**. Nenhuma física entra sem bater o oracle.

## 3. Estrutura
- `src/SaruCore.jl`, entrypoint do módulo.
- `src/simulation/Transient14DOF.jl`, **solver 14-DOF** (`solve_lap_14dof`). Física **inline** aqui
  (Pacejka combined-slip, suspensão, LSD, freios, aero) + prepass QSS p/ perfil-alvo.
- `src/components/{Engine,...}.jl`, subsistemas. **Só `Engine` é chamado** pelo solver; o resto
  foi editado mas está órfão (**débito DRY**, extrair p/ módulos ou remover). Ver `REFERENCES-AND-RESEARCH.md` §B.
- `src/simulation/QSS.jl`, **QSS ponto-massa** (`solve_qss`, extraído do Harness) + **modo
  `:endurance_thermal`** (térmico de disco/fade, port do `saru-core` `28c3258`).
- `src/validation/Harness.jl`, baseline regressão (delega p/ `QSS.solve_qss`) · `test/runtests.jl`.
- `src/io/{VehicleSetup,TelemetryExport,RedisWorker}.jl`, loader/validador de setup (seed
  ADR-0010 §1) · export HDF5/CSV · worker da fila BullMQ (payload → solver, Pub/Sub → SSE).
- `docs/{ARCHITECTURE,ROADMAP,AUDIT-FINDINGS,REFERENCES-AND-RESEARCH}.md`.

## 4. Diretrizes
- **TDD primeiro:** implementar um subsistema = preencher o stub + manter o harness convergindo p/
  o oracle. Nunca "passa mas está errado".
- **Estilo Julia:** docstring `"""` acima da function. Testes: `julia --project -e 'include("test/runtests.jl")'`.
- Simplicidade (Karpathy-mode); PT na interface, EN no código/commits (Conventional Commits,
  **sem `Co-Authored-By`**, **zero `GEMINI.md`/`.gemini`**, Antigravity lê `AGENTS.md`→`CLAUDE.md`).
- Decisão de arquitetura cross-repo → ADR no `saru-os`.

## Mapa de modelos (papéis)
- **RÁPIDO:** exploração. **BALANCEADO (default):** implementação/testes.
- **AVANÇADO:** física de domínio (DAE/multibody), validação numérica, decisões de arquitetura.
