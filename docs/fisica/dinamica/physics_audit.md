---
titulo: "Auditoria Física SARU Core (QSS Solver)"
data: "2026-06-27"
origem: "_arquivo/saru-physics-py/docs/PHYSICS_AUDIT.md"
status: "obsoleto"
area: "dinamica_veicular"
---

# Auditoria Física SARU Core (QSS Solver)

## Discrepância #9: Load Sensitivity Ausente

- **Descrição:** A modelagem de degradação do coeficiente de atrito (`mu`) devido à transferência de carga transversal/longitudinal (*load sensitivity*) está ausente no `qss_solver.py`.
- **Referência Cruzada:** No simulador legado (`partnerships/lts-hase/src/simulation/lap_time_solver.py:508-517`), havia a redução empírica: `mu_eff = mu * (1.0 - K_LS * delta_fz_frac)`.
- **Consequência:** Picos irreais de forças G (2.4-2.8g) nas curvas, distorcendo os tempos de volta (ex: 75s ao invés de 94.4s em Interlagos com certos setups de teste). A integração com o pneu de Pacejka no core não substitui esse efeito por si só.
- **Ação Recomendada:** Reintroduzir os cálculos de load sensitivity nas avaliações de aceleração e limite de aderência do passo à frente (`qss_solver.py`).
