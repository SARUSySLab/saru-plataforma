---
titulo: "2. Modelos de Pneu (Pacejka MF)"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/02_2_modelos_de_pneu_pacejka_mf.md"
status: "vigente"
area: "pneu"
---

## 2. Modelos de Pneu (Pacejka MF)

A geração das forças e o modelo térmico seguem uma política de duplo estágio conforme a necessidade computacional.

- **Magic Formula 5.2 (QSS):** O solver Causal em Python utiliza a MF 5.2. O modelo mescla forças puras transversais e longitudinais via aproximações e funções de peso (`Gxa`, `Gyk`) para resolver condições de *combined slip*. Identificou-se que a abordagem básica de elipse de atrito superestima as forças limites em cerca de 15-25% e falha no acoplamento lateral-longitudinal correto.
- **Magic Formula 6.2 Completa (14-DOF):** É o alvo de pesquisa em Julia para corrigir as falhas da elipse de atrito. Ao invés de *fudges*, a MF 6.2 permite ingerir bibliotecas `.tir` reais para aplicar a *sensibilidade exata de carga vertical* e o acoplamento real. O P&D atual foca em acoplar o *Relaxation Length* (atraso transiente das forças induzidas pelas vibrações) e o *Thermal Decay* (balanço de convecção/fricção) no núcleo do solver acausal sem quebrar o compilador simbólico.

### 2.7 Formulação matemática (pneu)

Magic Formula (forma canônica) e decomposição combined-slip:

$$F = F_z\,\mu\,\sin\!\left(C\arctan\!\left(B\sigma - E\left(B\sigma - \arctan(B\sigma)\right)\right)\right)$$

$$F_x = F\cdot\frac{\sigma_x}{\sigma}, \qquad F_y = F\cdot\frac{\sigma_y}{\sigma}$$

MF6.2 combined-slip, fator de peso $G_{y\kappa}$ que corrige a superestimativa (~15-25 %) da elipse simples:

$$F_y = F_{y0}(\alpha, F_z)\cdot G_{y\kappa}(\alpha,\kappa,F_z)$$

$$G_{y\kappa} = \cos\!\left(\arctan\!\left(B_{y\kappa}\cdot\kappa\right)\right), \qquad B_{y\kappa} = r_{By1}\cdot\cos\!\left(\arctan\!\left(r_{By2}\cdot\alpha\right)\right)$$

Slips normalizados:

$$\kappa^* = \frac{K_{x\kappa}\cdot\kappa}{D_x}, \qquad \alpha^* = \frac{K_{y\alpha}\cdot\tan\alpha}{D_y}$$

Relaxamento transiente (lag de 1ª ordem, comprimento de relaxação $L_y$ / $\sigma$):

$$\frac{dF_y}{dt} = \frac{V_x}{L_y}\left(F_{y,\text{steady}} - F_y\right) \quad\Longleftrightarrow\quad \sigma\,\dot{F}_y + |V_x|\,F_y = |V_x|\,F_{y,\text{steady}}$$

Calibração de referência (GT3):

$$C_\alpha = 22\cdot1.40\cdot(1.80\cdot4000) = 221{,}760\ \text{N/rad}$$

$$B_f = \frac{C_{\alpha,\text{front}}}{C\,\mu\,F_{z0}} \approx 8.43, \qquad B_r = \frac{C_{\alpha,\text{rear}}}{C\,\mu\,F_{z0}} \approx 9.92, \qquad p_{Dy1}\approx1.80,\quad p_{Dy2}\approx-0.15\text{ a }-0.25$$

Dinâmica de spin da roda:

$$I_{yy}\,\dot{\omega}_w = T_d - T_b - F_x R_{\text{eff}}$$

---
