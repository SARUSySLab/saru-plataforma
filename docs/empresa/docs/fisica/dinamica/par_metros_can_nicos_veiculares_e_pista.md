---
titulo: "8. Parâmetros Canônicos Veiculares e Pista"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/10_8_par_metros_can_nicos_veiculares_e_pista.md"
status: "vigente"
area: "dinamica_veicular"
---

## 8. Parâmetros Canônicos Veiculares e Pista

- **Veículos Referência:** 
  - Porsche 992 GT3 R: 1310 kg, ~565 hp, Downforce ~1400 kg @ 250 km/h.
  - McLaren 720S GT3: 1300 kg, ~500 hp, Downforce ~1300 kg @ 250 km/h.
- **Pneus:** Modelagem MF 5.2 a 6.2 (.tir). Implementação obrigatória de Combined Slip, Relaxation Length (rigidez transiente) e Thermal Decay (3 camadas térmicas).
- **Pista (Ex: Brasília BRB 2026):** Extraída via OSM, com elevação interpolada, gerando HDF5 contínuo de curvatura, banking e gradiente. Uso de LiDAR 0.1m OpenCRG apenas para simulação vertical extrema (MBS).

**Formulação (geometria de pista e reparametrização):** curvatura a partir do traçado, fator espacial tempo→distância e registro de nuvem de pontos ao centerline:

$$\kappa(s) = \frac{\dot{x}\,\ddot{y} - \dot{y}\,\ddot{x}}{\left[\dot{x}^2 + \dot{y}^2\right]^{3/2}}, \qquad SF(s) = \frac{dt}{ds} = \frac{1 - n(s)\,\kappa(s)}{v(s)\cos(\xi(s) + \beta(s))}$$

$$\mathcal{L}_{\text{align}} = \min_{\theta,\mathbf{t},\sigma}\ \frac{1}{N}\sum_{i=1}^{N}\left\|\sigma\mathbf{R}(\theta)\mathbf{p}_i + \mathbf{t} - \mathbf{c}_{\pi(i)}\right\|$$

> DEM GLO-30 (~30 m) é grosseiro vs meia-largura de pista (~6 m), não usar DEM bruto para geometria fina. Massas por classe (kg): 850/2150/2400 · 900/2200/2500 · 750/1950/2200; rigidez de mola (N/mm): 119.0/149.5 · 166.0/184.0 · 120.0/100.0.

---
