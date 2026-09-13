---
titulo: "9. R&D: Critical Review do Simulador 14-DOF"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/11_9_r_d_critical_review_do_simulador_14_dof.md"
status: "vigente"
area: "dinamica_veicular"
---

## 9. R&D: Critical Review do Simulador 14-DOF

- **Falhas Críticas Identificadas:** 
  1. O pneu (combined-slip) estava irrealista e inflado em ~25% devido à falta da função de peso $G_{yx}$ / $G_{xa}$.
  2. QSS pre-pass presumia um Friction Circle inatingível onde os 4 pneus atingem pico de grip ao mesmo tempo.
  3. Load transfer geométrico (via roll center) estava inexistente (apenas o elástico operava).
- **Melhorias de Física Planejadas:** 
  - Correção dos fatores de forma do MF6.2 e aumento da sensibilidade de carga vertical para casar com pneus Slick de GT3 aerodinâmicos.
  - Inserção de Roll Center heights explícitos (ex: 60mm na frente, 100mm atrás).
- **Roadmap do Solver:** Trocar o solver QNDF pelo **TRBDF2** (melhor para as descontinuidades de marchas/freio) e usar Jacobianos Esparsos, almejando 3-5x de aceleração.
- **Controle:** Refatorar o modelo do piloto p/ um controlador feedforward e "Stanley" adaptativo de velocidade.

---
