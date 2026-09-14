---
titulo: "7. R&D: Surrogates Neurais na Dinâmica Veicular"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/09_7_r_d_surrogates_neurais_na_din_mica_veicular.md"
status: "vigente"
area: "ia_agentes"
---

## 7. R&D: Surrogates Neurais na Dinâmica Veicular

- **Separação Arquitetural:** O Driver Model (determinista) é estritamente separado do Vehicle Plant (onde os surrogates operam). Redes puras falham em saturação de pneus, perda abrupta de downforce e limites ativos de ESC.
- **CTESN (JuliaSim):** Surrogates implementados como Continuous-Time Echo State Networks. NPCTESN (Não linear) é preferido pois requer até 1000x menos footprint de memória, viabilizando edge-ECUs (SDV).
- **Ganhos Reais:** Os ganhos absurdos comerciais (340x) não se aplicam a 14-DOF rígido. Ganhos reais seguros giram entre 3x-5x online e 20x-70x offline.
- **Safeguards (XRePIT):** Os surrogates predizem coeficientes intermediários (não o estado final). Divergências entre previsões single/dual step ativam gate de fallback imediato para o solver físico (CasADi/Julia).

**Formulação (CTESN / Neural ODE):** planta de referência vs reservoir (estado latente $r$, readout RBF com pesos dependentes do parâmetro $p$):

$$\frac{dy_p}{dt} = f_p(t, y, p), \qquad \frac{dr}{dt} = \sigma\!\left(A\,r(t) + V\,y_p^*(t)\right), \qquad \tilde{y}_p(t) = \Phi(r(t)),\quad W_{out}(p) = \operatorname{RBF}(p)$$

Gatilho de re-treino (residual acima do alvo) e métrica de consistência (self-composition de semi-volta, base do safeguard XRePIT):

$$\text{Residual} > \tau_{target} \;\Rightarrow\; \text{re-treinar}, \qquad E(t) = \left\|\tilde{y}_T(t) - \left(\tilde{y}_{T/2}\circ\tilde{y}_{T/2}\right)(t)\right\|$$

---
