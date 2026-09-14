---
titulo: "5. Dinâmica Veicular e Refinamentos Críticos (14-DOF)"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/07_5_din_mica_veicular_e_refinamentos_cr_ticos_14_dof.md"
status: "vigente"
area: "dinamica_veicular"
---

## 5. Dinâmica Veicular e Refinamentos Críticos (14-DOF)

### 5.1 Correções Estruturais e Físicas
- **Aerodinâmica e Arfagem (Pitch):** Correção do sinal do momento de pitch e uso da altura do centro de pitch (não o CG) como braço de alavanca. Separação do *downforce* entre massa suspensa e não suspensa para remover lag transiente incorreto nas molas. Inclusão de *Pitch Damping* (coeficiente dinâmico de arfagem) para estabilização sob frenagens severas.
- **Dinâmica Vertical:** Inclusão de transferência de carga quase-estática (lateral/longitudinal) nas equações de carga normal, e remoção da dupla-contabilização de rigidez na barra estabilizadora (ARB).
- **Pneus e Combined-Slip:** Correção dimensional (separando slip longitudinal adimensional do ângulo de deriva lateral em radianos). Adoção da sensibilidade de carga não-linear (parabólica) de Pacejka em vez de decaimento linear. Acoplamento térmico de pneus (temperatura da banda modulariza a aderência de pico).

**Formulação (carga vertical e transferência):** carga por canto com *lift-off floor* (o $\max(0,\cdot)$ impõe não-negatividade, evitando crash no cálculo de força):

$$F_{z,i} = \max\!\left(0,\; F_{z,\text{static},i} + \Delta F_{z,\text{long},i} + \Delta F_{z,\text{lat},i} + K_t z_{u,i} + F_{\text{down,unsprung},i}\right)$$

$$\Delta F_{z,\text{long},f} = -\frac{m\,a_x h}{2(a+b)}, \qquad \Delta F_{z,\text{long},r} = +\frac{m\,a_x h}{2(a+b)}$$

$$\Delta F_{z,\text{lat},f} = \pm\frac{a_y}{w_f}\left[\frac{m_s h_{rc,f} b}{a+b} + K_{\phi f}\phi\right] \pm \frac{m_{s,f} a_y r_u}{w_f}, \qquad \Delta F_{z,\text{lat},r} = \pm\frac{a_y}{w_r}\left[\frac{m_s h_{rc,r} a}{a+b} + K_{\phi r}\phi\right] \pm \frac{m_{u,r} a_y r_u}{w_r}$$

Dinâmica de roll/pitch da massa suspensa (convenção downforce $F_{\text{down}}<0$):

$$I_{xx}\ddot{\phi} = \frac{w_f}{2}(F_{z1}-F_{z2}) + \frac{w_r}{2}(F_{z3}-F_{z4}) + m_s a_y (h - h_{rc})$$

$$I_{yy}\ddot{\theta} = a(F_{z1}+F_{z2}) - b(F_{z3}+F_{z4}) + m_s a_x(h - h_p) + a F_{\text{down\_front}} - b F_{\text{down\_rear}}$$

Barra estabilizadora (ARB), momento de yaw longitudinal, deriva e perfil de velocidade:

$$F_{\text{arb},f} = \frac{k_{\text{arb},f}}{w_f}\left[(z_{u1}-z_{s1}) - (z_{u2}-z_{s2})\right], \qquad \alpha_{\text{front}} = \delta - \operatorname{arctan2}(v_y + a\,r,\; v_x), \qquad v_{k+1}^2 = v_k^2 + 2\,a_{x,k}\,\Delta s$$

### 5.2 Estabilização Numérica e Controle (TCS/ABS)
Diante de colapsos numéricos em saídas de curva de baixa velocidade (DNF por wheelspin severo e zeramento do *weighting factor* lateral):
- **Kinetic Friction Floor:** Imposição de um limite inferior regularizado para a função de peso de força lateral, garantindo *yaw damping* mínimo estável sob spin extremo.
- **TCS e ABS Ativos:** Integração de um módulo TCS (PI-based) para limitar torque sob alto *slip*, e mitigador de ABS no Driver Model modulando a pressão de freio antes do *wheel-lock* para evitar singularidade do Jacobiano.
- **Filtro Passa-Baixa Inercial:** Aumento controlado da inércia rotacional da roda para filtrar picos de alta frequência (reduzindo rigidez numérica das DAEs).

**Formulação (as 4 alavancas da convergência 14-DOF, ~102 s honesto, commit `6eb34a6`):**

Alavanca 1, TCS (slip-limiter no torque de tração):

$$T_{d,\lim} = T_d\cdot\left(1.0 - K_{tc}\cdot\max\!\left(0,\;\kappa - \kappa_{\text{alvo}}\right)\right), \qquad \kappa_{\text{reg}} = \kappa_{\text{limite}}\cdot\tanh\!\left(\frac{\kappa}{\kappa_{\text{limite}}}\right)$$

Alavanca 2, floor em $G_{y\kappa}$ (força cruzada não colapsa a zero sob slip severo):

$$G_{y\kappa,\text{reg}} = \max\!\left(\cos\!\left(\arctan\!\left(B_{y\kappa}\cdot\kappa_{\text{reg}}\right)\right),\; G_{y\kappa,\text{floor}}\right)$$

Alavanca 3, elipse de Kamm (projeção honesta $|F|\le\mu F_z$):

$$\Gamma = \sqrt{\left(\frac{F_x}{\mu_x F_z}\right)^2 + \left(\frac{F_y}{\mu_y F_z}\right)^2}, \qquad F_{x,\text{restrita}} = \frac{F_x}{\max(1.0,\;\Gamma)}, \quad F_{y,\text{restrita}} = \frac{F_y}{\max(1.0,\;\Gamma)}$$

Alavanca 4, de-rate do alvo pelo envelope QSS (limita torque demandado ao atrito disponível):

$$T_{d,\text{limite}} \le \min\!\left(T_{d,\text{driver}},\; R_{\text{eff}}\cdot\mu_x F_{z,\text{traseiro,QSS}}\right)$$

Mitigador de ABS no Driver Model (modula a pressão de freio antes do wheel-lock):

$$\delta_{\text{Brake,ABS}}(s) = \begin{cases} \delta_{\text{Brake,driver}}(s), & s_{x,i} < s_{x,t} \\ \delta_{\text{Brake,driver}}(s)\cdot K_{\text{ABS}}(s_{x,i}), & s_{x,i} \ge s_{x,t} \end{cases}$$

### 5.3 Validação e Solver (MTK)
- **Eliminação de Crutches:** As correções físicas permitiram remover os multiplicadores artificiais empíricos (`grip_cal=1.30` e `torque_cal=1.15`).
- **Jacobianos Analíticos Esparsos:** Manutenção estrita de formulações contínuas e diferenciáveis (evitando truncamentos manuais) para preservar a esparsidade dos Jacobianos exatos via `DataInterpolations.jl` e Dual numbers. Solver preferencial: `Rodas5P` ou `FBDF` com fatoração KLU.

---
