---
titulo: "Regras SARU Workspace, Guardrails de Calibração"
data: "2026-06-29"
origem: "_arquivo/saru-research/.claude/rules/calibration-guardrails.md"
status: "vigente"
area: "dinamica_veicular"
---

# Regras SARU Workspace, Guardrails de Calibração

## Baseline Oficial (Oráculo)
- Veículo Baseline: 992 GT3 R
- Pista: Interlagos (track smoothed)
- Tempo Alvo (Real): 94.4 s (WEC LMGT3)
- Tempo Simulado Canônico: **94.0 s**

## Regras
- **Pré-requisito para Calibração:** A reimplementação da *load sensitivity* no solver QSS é fundamental antes de realizar qualquer calibração de pneus definitiva, para evitar superestimar a aderência mecânica.
- O Tempo Simulado Canônico de 94.0s foi obtido utilizando a *smoothed track* e um conjunto de parâmetros antigos (antes de correções pendentes).
- Qualquer alteração nos solvers de física que mude o lap time em **≥ 0.5 s** DEVE ser reportada e aprovada pelo operador ANTES do commit.
- Fatores de performance globais (`perf_factor_lat` / `perf_factor_lon`) devem ter default = `1.0`.
- Alterar esse default em commits de produção é proibido.
