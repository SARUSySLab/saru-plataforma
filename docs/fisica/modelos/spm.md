---
titulo: "SARU Project Memory, saru-core"
data: "2026-07-17"
origem: "_arquivo/saru-physics-py/SPM.md"
status: "vigente"
area: "fisica (futuro repo)"
---

# SARU Project Memory, saru-core

> Última atualização: 2026-07-17
> LER ao iniciar. ATUALIZAR ao final de cada tarefa.
>
> **2026-07-17 (paridade standing-start, load-sens wired, RACE +1.19s):** fechou a paridade
> pendente do bloco 15c. `_run_standing_start` (lap_time_solver.py) usava `mu*F_normal` cru
> nos 4 pontos de grip (launch clutch ramp, friction-circle forward longitudinal, cap lateral
> `v_lat_max`, backward decel), k ignorado. Aplicado `_load_sens_factor` (import de qss_solver)
> dobrando em `mu_eff = mu·factor`, espelho exato da cadeia GGV não-Pacejka. **k=0 byte-idêntico**
> (`mu·1.0==mu` IEEE-exact; golden pin 87.78217401247005s). TDD: RED (`test_standing_start_lap_
> slower_with_negative_k`, laps iguais antes) → GREEN; +golden `test_standing_start_k_zero_byte_
> identical`. Suite **214 passed** (era 212). **Oráculo QUALIFYING 86.87 INTACTO**, roteia
> `_run_ggv_solver`, nunca toca `_run_standing_start`. Δ RACE (preset k=−0.12): Interlagos
> 87.782→**88.975 (+1.19s)**, ≥ gate 0.5s, **aprovado por Vitor antes do commit** (calibration-
> guardrails); consistente c/ GGV não-Pacejka (+1.07s mesmo k). Commit a51f16e, merge 8710746.
>
> **2026-07-15c (auditoria mu_scale-equivalente, NADA a remover, gap 0.39s):** espelho da
> remoção do `qss_calibration.mu_scale=0.968` no Julia (`be55cee`, proxy de load-sens →
> dupla contagem c/ k=−0.12; QSS 88.19→**87.26**, branch k012, o commit pediu "Python
> mirror review"). Auditoria aqui: **não existe knob equivalente**, cadeia de grip do
> oráculo = `friction_coefficient(2.50 efetivo) × perf_factor(1.0 neutro) ×
> _load_sens_factor(k)`; grep mu_scale/0.968/grip-scale = zero; Cd/Cl puros + trim de asa;
> C_rr do preset. A "dupla contagem" está FUNDIDA no μ=2.50 (pré-k absorveu média da
> penalidade de carga + compensação oposta de racing line/aero) e é inseparável, morre na
> re-derivação honesta μ/Cl (gate: aero real), não em delete pontual; inventar μ novo agora
> = tuning por resultado (proibido). **Baseline 86.87 INALTERADO** (medido 86.872, 212
> passed). Gap cross-solver 87.26×86.87 = **0.39s ≤ gate ±0.5 pela 1ª vez** (era 1.36).
> Docs sync: vehicle_calibrations §4.1, KB módulo 13 §11.1, rule calibration-guardrails.
> Paridade pendente notada: `_run_standing_start` (modo RACE) não aplica `_load_sens_factor`
> (k entrou só nos 3 loops GGV), irrelevante p/ oráculo QUALIFYING, corrigir à parte.
> → **RESOLVIDO 2026-07-17** (ver bloco no topo; RACE +1.19s, oráculo intacto).
>
> **2026-07-15b (k real aplicado + reorganização de pastas):** pesquisa do Vitor
> (`saru-KB/20_vehicle_dynamics/research/`, Perplexity+Gemini) convergiu **k = −0.12**
> (banda −0.10..−0.15, slick GT3 Michelin PS GT/Pirelli DHE). Aplicado nos presets GT3
> (992 GT3 R + 720S GT3) e no YAML Julia. Δ medido Python: Porsche 86.18→**86.87** (+0.69) ·
> McLaren 99.36→**100.56** (+1.20) · centerline 88.57→**89.64** (+1.07), bandas re-baselined,
> suite 212 passed. Física real substituindo fudge (laps aproximam do alvo 94s). FSAE k≈−0.15
> (TTC) = follow-up; Cup/trucks seguem 0.0. **Reorganização:** `platform/saru-core` →
> **`SARU/saru-physics-py`** (clone org; espelho vitormtt aqui NÃO configurado, decidir),
> `platform/saru-core-jl` → `SARU/saru-physics-jl`, `platform/saru-os` → `SARU/saru-app`.
> Auditoria da pasta antiga (Trash): todo histórico pushed; únicos locais eram os 2 edits
> k=−0.12 (resgatados via patch p/ esta branch). Branch vazia `feature/claude-jl-job-params`
> do saru-os antigo = só marcador, recriável.
>
> **2026-07-15 (auditoria física + espelho load sensitivity, TDD):** μ(Fz) implementado no QSS
> Python, espelho exato do Julia: `_load_sens_factor` (`qss_solver.py`), μ_eff = μ·max(0,
> 1+k·(Fz−Fz0)/Fz0), Fz0=m·g, aplicado nos 3 loops (forward, backward, endurance-backward) ×
> 2 paths (escalar + Pacejka). Plumbing: `TireParams.load_sensitivity` (default 0.0) →
> `to_solver_dict`/`from_solver_dict` → `_LegacyVehicleParams`; schema SoT `Tire.load_sensitivity`
> (le=0, paridade chave YAML Julia). **k=0.0 neutro = byte-idêntico** (suite 212 passed, oráculos
> intactos 86.18/99.36, zero mypy novo). TDD: `tests/unit/test_load_sensitivity.py` (4 testes:
> neutro exato, direção ±50% Fz, clamp ≥0, integração k=−0.10 → lap mais lento). **Falta só o
> valor real de k (pesquisa Vitor, slick ~ −0.05..−0.20)** → setar k + recalibrar μ/Cl +
> re-baseline conjunto c/ Julia (gate ±0.5s). Docs sincronizados: vehicle_calibrations §4.1,
> rule calibration-guardrails (matou claim stale "T03 pendente no Python"), KB módulo 13
> (§11.1 baselines vigentes 87.54/86.18; §11.2 correção, 646°C era resultado Julia, não Python)
> e módulo 18-gaps (item load sensitivity → resolvido estrutural).
>
> **2026-07-14 (auditoria KB↔repos, sessão umbrella):** `docs/adr/MASTER_ADR.md` sincronizado c/ a
> rev cross-eco 2026-07-14 (canônica no `saru-KB/40_software_arch/adr/`; anti-número-fantasma).
> Backlog recebido da auditoria: (1) **load sensitivity μ(Fz) no QSS Python**, Julia já tem
> (k=0 neutro nos 2 solvers); aqui é o espelho pendente e bloqueia calibração definitiva (KB
> módulo 18-gaps corrigido, o claim antigo estava invertido); (2) `generate_vehicle_setup_schema`
> (JSON Schema c/ bounds dinâmicos, KB módulo 4), **NÃO implementar** antes da decisão
> proto×JSON-Schema (⚖️ T-A pendente, ver MASTER_ADR §3).
>
> **2026-07-04 (T03 gear selector, espelho do fix Julia, MERGED na develop):**
> `_select_gear_optimal` (`qss_solver.py`) ranqueava marchas com a curva de torque SINTÉTICA
> (decai ao redline) enquanto a tração usa a tabela real do YAML → upshift prematuro, lap
> inflado. Fix: seletor recebe `torque_map_rpm/nm` opcional e usa `_torque_curve_interp` quando
> há mapa (mesmo critério da tração; fallback sintético preservado). 3 call sites
> (`_run_ggv_solver` ×2, `_run_standing_start`). TDD: RED `test_select_gear_ranks_with_torque_map_t03`
> → GREEN; 208 passed pós-rebase na develop. Δ lap (medido na develop): Porsche hi-fi Interlagos
> 94.23→**86.18** (−8.05s) · McLaren Barcelona 103.81→99.36 (−4.44s) · centerline TUM
> (`build_interlagos_real`) 96.00→88.57 (−7.43s). **Δ≥0.5s aprovado pelo Vitor 2026-07-04.**
> Bandas re-baselined INTERIM nos 2 oráculos (travam regressão, não realismo, fudges μ/Cl eram
> co-calibrados com o seletor errado; recalibrar após load sensitivity + aero real, ver
> calibration-guardrails + docs/vehicle_calibrations.md §4.1). Gap cross-solver Python 86.18 vs
> Julia 87.54 (re-baseline aprovado) = 1.36s, comparação válida pós-espelho, investigar depois.
> Merge `--no-ff` da branch `claude/amazing-bardeen-299e34` (fix + test rebaseline + docs).
>
> **2026-07-03 (reconciliação Linux×SSD, R1):** triados dirty/untracked locais + cópia SSD.
> `develop` +4 commits (ahead 5, **não-pushado**): `test:` rebaseline qss+thermal p/ a pista real
> TUM FTM (o +1 `9cdea5d` moveu o baseline low-poly 70s→96s e deixou o oráculo `test_qss_baseline_lap_time`
> vermelho, corrigido, docstring stale citava `test_qss_calibration.py`/`interlagos.hdf5` inexistentes);
> `chore(lint)` I001; `chore` gitignore telemetria raw/outputs; `feat` harness de validação QSS-vs-telemetria
> (+ vendored MoTeC `ldparser` MIT). 7 arquivos de experimento (scratch/patch/check_acc*/debug/ls.patch)
> removidos (preservados no scratchpad). Telemetria raw (103M `.ld`) → quarentena/`.gitignore`, versionada
> via `data/telemetry/catalog.yaml`.
> **SSD (bundle `saru-core-ssd-2026-07-03`) = 100% ruído CRLF** sobre base velha `16b693f` (22 atrás),
> zero arquivo único, zero conteúdo real (`--ignore-cr-at-eol` shortstat vazio) → **DESCARTADO**, sem PORT/merge (Step 4 void).
> **Correção ao DIVERGENCE_REPORT:** o "SSD dirty é REAL, não é CRLF" está **errado**, `core.autocrlf=false`
> não remove CR de blobs já commitados no Windows. **Cross-repo:** rechecar saru-os(276)/LTS(128)/umbrella(91)
> com `--ignore-cr-at-eol` ANTES de assumir trabalho de PORT.
>
> **2026-07-01:** `develop` recebeu os 4 commits de docs/tooling (docs-auditor, GAP-AUDIT,
> MASTER_ADR) via merge `--no-ff` (pushed). A física ENDURANCE_THERMAL segue **uncommitted/parked**
> na `feature/tire-dynamics-refinement`, deferida por ordem do Vitor até o saru-os (back+front)
> estar funcional. Papel confirmado: **tier rápido** do saru-os (não vai pro lts-copatruck, que já é independente).

---

## Handoff 2026-07-17
- Feito: paridade standing-start fechada (`a51f16e`+`8710746`+`f14b8be`, pushed, CI verde).
- Próximo passo: recalibração honesta μ/Cl, gate segue **aero real** (cx/cl/ride-height maps); FSAE k≈−0.15 follow-up.
- Bloqueio: nenhum.

---

## 1. Identidade

- Papel: Biblioteca de física compartilhada (QSS solver, vehicle models, tracks, schemas)
- Tipo: Python puro + C++ extension (pybind11/scikit-build-core), **não é app, não tem HTTP**
- GitHub: `vitormtt/saru-core` (manter ativo, lib central do ecossistema)
- Local: `~/Projects/SARU/platform/saru-core/`
- Branch ativa: `develop` (submodule do saru-os fixa develop)
- Último commit: `32da21b`, feat: harness de validação QSS-vs-telemetria (reconciliação R1, 2026-07-03)

---

## 2. Estado da venv (2026-06-27)

- Python: 3.11.15 (via uv)
- Venv: `platform/saru-core/.venv/`
- Problema resolvido: cmake cache stale após mover de `shared/saru-core` → `platform/saru-core`
  - Fix: deletar `build/` e rodar `uv sync`, C++ ext (`ext/suspension_cpp`) recompilou OK
- Rodar testes: `cd platform/saru-core && uv run pytest -x -q`
- Dependências: numpy, scipy, h5py, pydantic, pandera, polars, pyyaml; matplotlib/plotly como extra `[viz]`

---

## 3. Arquitetura

```
src/saru_core/
  vehicle/
    engine.py         ← ICEEngine + ElectricMotor + BsfcMap (superset do lts-copatruck)
    parameters.py     ← VehicleParams, EngineParams, TireParams, etc.
    drivetrain.py
    tire_thermo.py
  simulation/
    lap_time_solver.py   ← run_simulation (QSS two-pass)
    simulation_modes.py  ← SimulationConfig com flags (use_pacejka, use_thermal, use_aero_map)
    qss_solver.py
  tracks/
    hdf5.py           ← CircuitHDF5Reader/Writer (schema diferente do lts-copatruck)
    circuit.py
    generator.py
  dynamics/           ← 3-DOF handling transiente (bicycle + roll, validado vs Khalil 2018)
  schemas/            ← Pydantic/Pandera contracts
  telemetry/kpis/
  racing_line.py
ext/
  suspension_cpp/     ← C++ pybind11 (cmake, precisa compilar)
tests/
  unit/               ← 15+ unit tests
  integration/        ← batch_runner, full_simulation, optimize (migrados de LTS_SARU)
```

---

## 4. Diferenças críticas vs lts-copatruck

| Módulo | saru-core | lts-copatruck | Consequência |
|---|---|---|---|
| `vehicle/engine.py` | `fuel_density` hardcoded 0.85 | lê do config dict | OK: lts-copatruck passa 0.85; resultado idêntico |
| `simulation/simulation_modes.py` | flags `use_thermal`, sem `ENDURANCE_THERMAL` mode, sem `qualifying()` | `ENDURANCE_THERMAL` como `SimulationMode`; tem `qualifying()` | lts-copatruck NÃO pode usar saru-core simulation_modes |
| `tracks/hdf5.py` | schema diferente, extra attrs diferentes | schema próprio com `n_points`, `average_width` | lts-copatruck NÃO pode usar saru-core reader (HDF5 existentes incompatíveis) |

---

## 5. Merge Repos, Estado (2026-06-27)

Contexto completo: `/home/vitor/Projects/SARU/MERGE-REPOS-DELETE.md`

### O que foi absorvido de repos externos
- **LTS_SARU** (morto): 3 testes integração migrados (`batch_runner`, `full_simulation`, `optimize`), commit `e5b2c67`
- lts-copatruck: ICEEngine agora importa de `saru_core.vehicle.engine`, commit `a5704cd` (no lts-copatruck)

### Fase 3b, ENDURANCE_THERMAL extraction (CONCLUÍDA 2026-06-30)
- Portado de `lts-copatruck` commit `321dcd1` (achado via `git log --all` na branch `develop`
  do parceiro, a versão atual do lts-copatruck HEAD tinha perdido o mode num rewrite
  posterior "physics v2"; só sobrou o comentário em `vehicle/parameters.py:255`).
- Implementação em `simulation/qss_solver.py`:
  - `_LegacyVehicleParams` ganhou 9 campos de disco/fade (`disc_mass_kg`,
    `disc_specific_heat`, `disc_convection`, `disc_area_m2`, `disc_initial_temp_c`,
    `disc_thermal_efficiency`, `fade_onset_temp_c`, `fade_full_temp_c`, `fade_min_factor`).
  - `_run_thermal_brake_model()`: marcha de temperatura por eixo (2 discos), convecção
    escalada por velocidade, fade linear acima de `fade_onset_temp_c`.
  - `_run_endurance_thermal()`: **wrapper puro**, chama `_run_ggv_solver()` sem
    nenhuma alteração de assinatura/corpo, depois itera ponto-fixo (fade → backward
    pass escalado → novo fade) só quando fade realmente engata. Zero mudança no
    solver QSS existente.
  - `SimulationMode.ENDURANCE_THERMAL` + `SimulationConfig.ambient_temp_c` /
    `.thermal_iterations` / `.is_thermal()` em `simulation_modes.py`.
  - `BrakeParams` em `vehicle/parameters.py` ganhou os mesmos 9 campos (nomes verbosos,
    plumbed via `to_solver_dict`/`from_solver_dict` com defaults `.get()`).
  - `SimulationResult` ganhou `disc_temp_front_c`/`disc_temp_rear_c`/`brake_fade_factor`
    (None fora do modo) + `peak_disc_temp_c`/`min_fade_factor` + export gated no CSV.
- Validado byte-idêntico: com defaults (`fade_onset_temp_c=450`), ENDURANCE_THERMAL
  == QUALIFYING (`diff == 0.0`, testado em `tests/unit/test_endurance_thermal.py`).
  Fade agressivo (`fade_onset_temp_c=300`) só atrasa a volta, nunca acelera.
- Oráculo intacto: Porsche 992 GT3 R @ Interlagos segue 94.0-94.4s (suíte completa
  196 passed/1 skipped/2 xfailed, skip é o `matplotlib` opcional, xfail pré-existente).
- mypy: 3 erros pré-existentes em `lap_time_solver.py` (pandas-stubs + racing_line),
  confirmado idênticos antes/depois via `git stash`, zero erros novos.

---

## 6. Regras Críticas

1. **Zero HTTP/FastAPI/estado**, quem expõe HTTP é o saru-os
2. **Física testada**: toda mudança de física passa pelos testes + oracle QSS (Interlagos ~94s)
3. **C++ ext**: `uv sync` compila automaticamente; se falhar, `rm -rf build/` e re-sync
4. **Baselines**: não alterar `perf_factor_lat/lon` default de 1.0 em commits de produção
5. **ENDURANCE_THERMAL**: ao extrair para saru-core, saída byte-idêntica ao modo qualifying quando fade desabilitado

---

## 7. Pendências

- [x] **Fase 3b**: ENDURANCE_THERMAL extraction como plugin, ver seção 5 (2026-06-30)
- [x] **Load sensitivity μ(Fz)**: estrutura espelhada do Julia no QSS (2026-07-15, k=0 neutro)
- [ ] **Calibração pneu definitiva**: aguarda valor real de k (pesquisa) → setar
  `load_sensitivity` + recalibrar μ/Cl + re-baseline conjunto Python×Julia (gate ±0.5s)
- [ ] **saru-core-jl** (Julia 14-DOF): worker assíncrono, repo separado, contrato via YAML+HDF5
- [ ] **lts-copatruck venv**: adicionar saru-core como dep local no pyproject.toml do lts-copatruck (eliminar dependência cruzada de venv)
