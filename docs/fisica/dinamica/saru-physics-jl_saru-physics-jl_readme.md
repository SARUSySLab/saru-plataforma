---
titulo: "saru-core-jl"
data: "2026-06-29"
origem: "_arquivo/saru-physics-jl/README.md"
status: "stale"
area: "dinamica_veicular"
---

# saru-core-jl

14-DOF transient vehicle dynamics in Julia (ModelingToolkit.jl, hand-rolled acausal DAE).

**Status (2026-06-29):** test suite GREEN 4/4. Two solvers, both validated against the oracle:
- **14-DOF transient** (`src/simulation/Transient14DOF.jl`): **94.42 s** (target 94.0 ± 1.0,
  deterministic). Full chassis 6-DOF + 4 unsprung + 4 wheel-spin + curvilinear tracking, ISO 8855.
- **QSS point-mass** (`src/validation/Harness.jl`): **93.03 s**, isolated regression baseline.

⚠️ **Not clean physics yet.** Convergence relies on 2 empirical calibration factors
(`grip_cal=1.30`, `torque_cal=1.15`) plus inherited prepass fudges, and all physics is inlined in
the solver (the `src/components/*` modules are edited but only `Engine` is called). This is a
lap-time match, **not** channel-validated physics. See
[docs/REFERENCES-AND-RESEARCH.md](docs/REFERENCES-AND-RESEARCH.md) (params vs reference + research
agenda), [docs/AUDIT-FINDINGS.md](docs/AUDIT-FINDINGS.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/ROADMAP.md](docs/ROADMAP.md).

## Setup

```bash
# Install Julia 1.10+ (recommended: juliaup)
curl -fsSL https://install.julialang.org | sh

# Instantiate dependencies (run from repo root)
julia --project -e 'using Pkg; Pkg.instantiate()'

# Run harness (will fail, TDD RED)
julia --project -e 'include("test/runtests.jl")'
```

## Structure

```
saru-core-jl/
├── Project.toml                  # Julia project + deps
├── src/
│   ├── SaruCore.jl               # Module entry point
│   ├── simulation/
│   │   └── Transient14DOF.jl     # 14-DOF solver (solve_lap_14dof), physics inlined here
│   ├── validation/
│   │   └── Harness.jl            # QSS point-mass regression baseline (93.03 s)
│   └── components/               # ⚠️ edited but only Engine is on the solve path (DRY debt)
│       ├── Engine.jl             # called by the solver (torque map + brake)
│       ├── Transmission.jl Brakes.jl Aero.jl Suspension.jl Tire.jl  # orphan modules
└── test/
    └── runtests.jl               # QSS baseline + 14-DOF vs oracle (94.0 ± 1.0 s)
```

## Validation

`solve_lap_14dof(vehicle_yaml, track_hdf5)` returns the lap time; pass `return_internals=true`
for `(sol, sys, grids, vars)` telemetry. The oracle is the QSS Python solver (saru-core, 94.0 s).
**Gate:** validate *channels* (speed, ay/ax, slip, RPM, deflections), not just the lap-time number, the current match is calibration, not physics. See `docs/REFERENCES-AND-RESEARCH.md`.
