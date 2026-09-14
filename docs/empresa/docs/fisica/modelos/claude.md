---
titulo: "saru-core, CLAUDE.md"
data: "2026-07-07"
origem: "_arquivo/saru-physics-py/CLAUDE.md"
status: "vigente"
area: "fisica (futuro repo)"
---

# saru-core, CLAUDE.md

Núcleo de **física compartilhado** da suíte SARU (simulador de volta). Biblioteca Python pura,
*category-agnostic*: solver QSS de lap-time, modelos de veículo (Pacejka, aero, motor, freios,
transmissão), pistas (HDF5/OSM) e schemas de telemetria. **É dependência dos serviços de cálculo
do produto, não é um app.**

> Regra de ouro: este arquivo é CURTO e orientativo. O que crescer vira regra em `docs/` ou skill;
> o inegociável vira hook/CI. **Memória real = Git** (este arquivo, `AGENTS.md`, ADRs, `docs/`).

## 1. Stack & versões
- Python ≥3.11 (libs/produtos) · 3.12 nos serviços do gateway.
- Numérico: numpy 2 · scipy · pandas · h5py. Contratos: pydantic 2 · polars · pandera.
- Build: **scikit-build-core + pybind11** (solver C++ de suspensão em `ext/suspension_cpp` → exige
  cmake ≥3.16 + ninja + compilador).
- `matplotlib`/`plotly` são **extra `viz`** (opcional): serviços headless (engine / sim-worker) não
  os instalam; só `saru_core.tracks.visualize` precisa, `pip install 'saru-core[viz]'`.
- Comandos: testar=`pytest` · lint=`ruff check` · types=`mypy` · build=`uv build`.

## 2. Arquitetura & papel no ecossistema (ler antes de mexer em fronteiras)
saru-core é a **camada de física**, consumida pelos **serviços de cálculo** do produto `saru-os`:

- **Lap-time QSS, ESTE repo (Python):** `run_simulation(config, vehicle_params, circuit)`, solver de
  duas passadas. É o que o `engine` (FastAPI) do saru-os chama hoje, via **git submodule**.
- **Transiente 14-DOF, repo `saru-core-jl` (Julia):** alvo de alta-fidelidade (ModelingToolkit +
  Multibody). Roda como **worker assíncrono** nos serviços de cálculo (fila Redis), **não** em-processo.
  Contrato: vehicle YAML + track HDF5 → `lap_time`; validado contra o **oracle QSS** (Porsche 992
  GT3 R @ Interlagos, ~94 s).
- **Suspensão, C++/pybind11 (`ext/`):** cinemática/forças de corner expostas ao Python.
- **Handling transiente (SD), `dynamics/transient.py`:** modelo **3-DOF** (bicycle + rolagem, pneu
  Magic Formula/linear) p/ manobras (step/DLC/fishhook/sweep/SIS), reusa `SARUSolver`. Suficiente para o produto SD. O **14-DOF**
  de alta-fidelidade NÃO mora aqui, é do `chassis-solver` externo (`saru_chassis`) / `saru-core-jl`
  (Julia). A cópia órfã quebrada (`solver_14dof.py` + `simulation/rl_driver/`, que importavam
  `saru_chassis`) foi **removida**. **Validado** vs benchmark Khalil 2018 (14-DOF Blazer): roll
  gradient ~7.5 °/g (−5% vs 14-DOF), ver `validation/` + `tests/unit/test_khalil2018_roll.py`.

> **Regra de coerência (anti-monstro):** este repo é category-agnostic e **sem I/O de serviço**
> (zero FastAPI, zero estado, zero UI). Quem expõe HTTP/fila é o `saru-os`. **Um produto, uma borda,
> um front-end**, nunca replicar solver nem criar front-ends/serviços paralelos (o anti-padrão que
> inflou o projeto legado). Mudança de fronteira → registrar em ADR no `saru-os`.

## 3. Branches
- `develop` = **integração** (testes, CI, C++, docs, calibração). `main` = **release estável**,
  promovido de `develop` via PR (com CI verde, não mais "snapshot pelado"). O submodule do
  `saru-os` fixa **`develop`** (`.gitmodules` branch=develop; traz a toolchain C++ ao build do engine).

## 4. Diretrizes de Código e Estilo
- **Simplicidade:** código minimalista e direto (Karpathy-mode).
- **Linguagem:** interface em português; código e commits em inglês (Conventional Commits, sem `Co-Authored-By`).
- Evitar abstração prematura/especulativa; erro explícito e robusto.
- **Física é testada:** toda mudança de física passa pela suíte (`tests/`, oracle em
  `tests/test_qss_solver.py`). Confiança = testes verdes + ruff + mypy. Nunca aceitar "só compila".

## 5. Memória e Contexto do Projeto
- **Memória Persistente:** leia sempre `AGENTS.md` no início da sessão (histórico + decisões locais).
- **Tarefas Pendentes:** consulte `BACKLOG.md` (ou `tasks/todo.md`).

## 6. Ingestão de Documentação (Anti-Token Burn / Second Brain & Privacidade)
- **NUNCA** leia a pasta `docs/` inteira.
- A biblioteca universal (Second Brain) mora em `~/Documents/SARU_Library/`. **NUNCA** carregue arquivos de lá diretamente (use apenas via NotebookLM).
- Ao ler o Obsidian (`~/Documents/Obsidian/`), é TERMINANTEMENTE PROIBIDO acessar qualquer pasta ou arquivo contendo `personal/` ou `Personal/`. Acesse apenas as subpastas `/SARU/` ou `/saru/`.
- A pasta `~/Documents/MATLAB` está 100% blindada e excluída de qualquer leitura ou alteração.
- Leia `docs/tire_physics.md` APENAS se a tarefa envolver modificação no modelo de pneu Pacejka ou coeficientes.
- Leia `docs/vehicle_calibrations.md` APENAS se a tarefa envolver ajuste de parâmetros (Porsche, McLaren, Stock Car) ou BoP.
- Leia `docs/track_formats.md` APENAS se a tarefa envolver representações de pista (HDF5/OpenCRG) ou comparação causal vs acausal.
- Leia `PHYSICS_AUDIT.md` APENAS se for auditar validações de tempo de volta e algoritmos QSS.

## 7. Skills disponíveis (`.agents/skills/`)

| Skill | Quando acionar |
|---|---|
| `lint-and-validate` | Antes de commit; sempre que o CI falhar |
| `test-driven-development` | Features novas ou correções com comportamento observável; qualquer mudança no solver |
| `create-pr` | Hora de abrir PR, base `develop`, não `main` |
| `docs-auditor` | Mudança arquitetural ou de física, decide se os Documentos Mestre em `saru-KB/` precisam de update |

## Mapa de modelos (papéis, atualizar quando a oferta mudar)
- **RÁPIDO:** busca em repo, classificação, exploração de codebase.
- **BALANCEADO (default ~90%):** features, refactors médios, geração, testes.
- **AVANÇADO:** arquitetura, física de domínio, refactor cross-repo, papel de avaliador independente.
- Regra: mais inteligência onde se **decide**, mais barato onde se **lê**.
