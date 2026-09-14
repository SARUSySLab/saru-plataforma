---
titulo: "6. Integração do Driver Model (Optimal Lap MPC)"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/08_6_integra_o_do_driver_model_optimal_lap_mpc.md"
status: "vigente"
area: "ia_agentes"
---

## 6. Integração do Driver Model (Optimal Lap MPC)

### 6.1 Arquitetura de Co-Simulação
- O veículo (14-DOF) atua como planta Index-1 DAE no `ModelingToolkit.jl`. O MPC roda via `Optimization.jl` (L-BFGS/SQP).
- **Controles Discretos:** Inputs de controle são parâmetros atualizados (via `setp` no `PeriodicCallback`) a 10-20 Hz em vez de variáveis de estado, mitigando overhead do solver linear ($O(N^3)$).
- **Benchmarking Offline (Minimum-Lap-Time):** Resolvido via *Direct Collocation* espacial (sobre a distância $s$, não $t$). Exige colocação *Radau* (L-stable) para amortecer oscilações DAE em alta frequência nos limites de tração.

### 6.2 Restrições e Mapeamento Inverso
- **Elipse de Atrito:** Modelada como restrição *soft* (com variáveis de folga severamente penalizadas) para evitar inviabilidade numérica durante picos transientes de transferência de peso.
- **Atuadores e Smoothing:** Comandos do MPC passam por filtros passa-baixa de 1ª ordem ($C^0$ continuity) para suavizar a entrada no solver implícito, evitando rejeição de passo de integração. Mapeamento inverso aloca torque e aplica bias de freio proporcional à distribuição de carga dinâmica.

### 6.3 Formulação NMPC (single-track dinâmico, frame curvilíneo)

Estado (tempo como variável independente): $\mathbf{x} = [\,u\;\; v\;\; r\;\; s\;\; e_y\;\; e_\psi\,]^T$

$$\dot{u} = vr + \tfrac{1}{m}\left(F_{x,f}\cos\delta - F_{y,f}\sin\delta + F_{x,r} - F_{drag}\right), \qquad \dot{v} = -ur + \tfrac{1}{m}\left(F_{x,f}\sin\delta + F_{y,f}\cos\delta + F_{y,r}\right)$$

$$\dot{r} = \tfrac{1}{I_z}\left(l_f\left(F_{x,f}\sin\delta + F_{y,f}\cos\delta\right) - l_r F_{y,r}\right)$$

$$\dot{s} = \frac{u\cos e_\psi - v\sin e_\psi}{1 - e_y\,\kappa(s)}, \qquad \dot{e}_y = u\sin e_\psi + v\cos e_\psi, \qquad \dot{e}_\psi = r - \kappa(s)\,\dot{s}$$

> $\dot{e}_\psi$ na forma padrão curvilínea, **confirmar corte no doc-fonte**.

Cargas verticais (com downforce) e derivas regularizadas ($u_\epsilon$ evita singularidade em $u\to0$):

$$F_{z,f} = mg\frac{l_r}{L} + \tfrac{1}{2}\rho\,C_{L,f}A_f u^2 - \frac{m\,a_x h_{cg}}{L}, \qquad F_{z,r} = mg\frac{l_f}{L} + \tfrac{1}{2}\rho\,C_{L,r}A_f u^2 + \frac{m\,a_x h_{cg}}{L}$$

$$\alpha_f = \delta - \arctan\!\left(\frac{v + l_f r}{u + u_\epsilon}\right), \qquad \alpha_r = -\arctan\!\left(\frac{v - l_r r}{u + u_\epsilon}\right)$$

Elipse de atrito, restrição *soft* (folga $\epsilon_i$ penalizada, $w_\epsilon\sim10^4$):

$$\left(\frac{F_{x,i}}{F_{z,i}\mu_i}\right)^2 + \left(\frac{F_{y,i}}{F_{z,i}\mu_i}\right)^2 \le 1.0 + \epsilon_i, \qquad \mathcal{J}_{cost} = \mathcal{J}_{tracking} + \sum_{k=1}^{N}\left(w_\epsilon\,\epsilon_{f,k}^2 + w_\epsilon\,\epsilon_{r,k}^2\right)$$

Velocidade crítica enriquecida por downforce e integração espacial (envelope mínimo a partir dos ápices):

$$v_{crit}(s) = \sqrt{\frac{\mu m g}{m\,\kappa(s) - \tfrac{1}{2}\mu\rho(C_{L,f}+C_{L,r})A_f}}, \qquad v^2(s\pm\Delta s) = v^2(s) \pm 2\,a_x(v)\,\Delta s$$

Benchmark offline, OCP de *min-lap-time* (colocação direta *Radau* L-stable, variável independente $s$):

$$\min\; T = \int_0^{s_{lap}} \frac{1 - e_y(s)\kappa(s)}{u(s)\cos e_\psi(s) - v(s)\sin e_\psi(s)}\,ds$$

Suavizações $C^1$ para o solver gradiente (Ipopt/MadNLP), mapa inverso controle→atuador e suavização de atuador de 1ª ordem (estado extra no DAE, garante $C^1$); métrica de validação = utilização por eixo:

$$\mathrm{abs}(x) \approx \sqrt{x^2 + \epsilon}, \quad \mathrm{sign}(x) \approx \tanh\!\left(\tfrac{x}{\epsilon}\right), \qquad P_{brk} = \frac{-F_{x,req}\,K_{bias}}{A_{caliper}\,\mu_{pad}\,R_{rotor}}, \qquad K_{bias}(s) = \frac{F_{z,f}(s)}{F_{z,f}(s)+F_{z,r}(s)}$$

$$\tau_{act}\,\dot{\mathbf{u}}_{act} = \mathbf{u}_{NMPC} - \mathbf{u}_{act}, \qquad \sigma_{util,i} = \sqrt{\left(\frac{F_{x,i}}{F_{z,i}\mu_i}\right)^2 + \left(\frac{F_{y,i}}{F_{z,i}\mu_i}\right)^2} \le 1.05$$

---
