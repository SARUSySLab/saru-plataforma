---
titulo: "saru-core"
data: "2026-06-27"
origem: "_arquivo/saru-physics-py/README.md"
status: "vigente"
area: "fisica (futuro repo)"
---

# saru-core

Núcleo de física compartilhado da suíte **SARU** (simulador de volta). Biblioteca Python pura e
*category-agnostic*: solver quasi-steady-state (QSS) de lap-time, modelos de veículo (Pacejka,
aero, motor, freios, transmissão), pistas (HDF5/OSM) e schemas de telemetria.

**Não é um app.** É dependência dos serviços de cálculo do produto (`saru-os`), consumida via
git submodule. Quem expõe HTTP/fila é o `saru-os`; aqui só vive a física (sem I/O de serviço).
Para **rodar o produto** (UI + engine + esta lib, dockerizado): `saru-os` → `docs/GETTING_STARTED.md`.

## Instalação (dev)

```bash
uv sync                 # ambiente + deps (build C++ via scikit-build-core/pybind11)
pytest                  # suíte de testes
ruff check && mypy      # lint + types
```

> Requer toolchain C++ (cmake ≥3.16 + ninja + compilador) para o solver de suspensão em
> `ext/suspension_cpp`.

## Uso

```python
from saru_core.simulation import SimulationConfig, SimulationMode, run_simulation
from saru_core.vehicle import porsche_911_gt3_cup_991, get_default_setup
from saru_core.tracks.generate_br_tracks import build_interlagos_real

cfg = SimulationConfig(mode=SimulationMode.QUALIFYING, setup=get_default_setup())
res = run_simulation(cfg, porsche_911_gt3_cup_991(), build_interlagos_real(), save_csv=False)
print(res.lap_time)     # tempo de volta [s]
```

## Mapa do pacote

| Módulo | Conteúdo |
|---|---|
| `simulation/` | solver QSS de lap-time (`run_simulation`), modos, batch runner |
| `vehicle/` | params, pneus (Pacejka/térmico), aero, motor, freios, transmissão, presets |
| `tracks/` | `CircuitData`, IO HDF5, OSM, racing line, geradores (Interlagos etc.) |
| `dynamics/` | estado transiente, **3-DOF de handling** (pneu MF/linear; step/DLC/fishhook/sweep/SIS) + integração ODE |
| `schemas/` | contratos de dados (pydantic/pandera) |

## Validação física

Cross-checks do modelo contra referências externas (metodologia de research SARU,
`FullVehicleSimulation_Validacao_Fisica.md`):

| Harness | Referência | Âncora |
|---|---|---|
| `validation/khalil2018_roll_validation.py` | Khalil & Atia (2019), SAE 06-12-01-0003 (14-DOF Blazer) | roll gradient **7.5 °/g** vs 7.94 do 14-DOF (−5%) |

O tier roda pneu **linear** ou **Magic Formula** (satura em μ·Fz): a MF derruba o SIS de **16.5°→6.1°**, casando o Pacejka do 14-DOF (5.8°).

```bash
PYTHONPATH=src uv run --no-project --with numpy --with scipy --with pyyaml \
    python validation/khalil2018_roll_validation.py   # → validation/khalil2018_roll_report.md
```

Regressão: `tests/unit/test_khalil2018_roll.py`. Dados de referência: `data/benchmarks/khalil2018/`.

## Arquitetura

A física de alta-fidelidade 14-DOF é portada para **Julia** (repo `saru-core-jl`), executada como
worker assíncrono nos serviços de cálculo. Detalhe e regras de coerência: ver `CLAUDE.md`.

> **Branches:** `develop` é canônico (testes, CI, C++, docs); `main` é o snapshot promovido.
