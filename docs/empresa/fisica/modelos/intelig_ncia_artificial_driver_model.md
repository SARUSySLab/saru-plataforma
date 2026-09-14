---
titulo: "3. Inteligência Artificial: Driver Model"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/05_3_intelig_ncia_artificial_driver_model.md"
status: "vigente"
area: "ia_agentes"
---

## 3. Inteligência Artificial: Driver Model

Divergindo de aplicações acadêmicas (PIBIC IA), o escopo de produto da plataforma foca estritamente em **clareza e transparência matemática**, rejeitando algoritmos puros de caixa-preta para funções core.

- **AMPC e Machine Learning:** O "Driver Model" (algoritmo encarregado de traçar a rota ótima e corrigir instabilidades em simulação) deve operar exclusivamente com **Machine Learning** emparelhado com o algoritmo de controle ótimo **AMPC (Advanced Model Predictive Control)**.
- **Tube MPC:** Utiliza limites estatísticos para mitigar o ruído entre a simulação e a telemetria física extraída (Mismatch Loss).
- **Sem Redes Neurais Cegas:** Projetos experimentais como PINNs, Reservatórios CTESN, ou algoritmos de clonagem comportamental (Behavioral Cloning) foram oficialmente substituídos por otimizações matemáticas NLP (Colocação Direta via IPOPT/CasADi) e ML estatístico.

**Lei de esterço (Stanley + preview de curvatura), forma completa:**

$$\delta(t) = \Delta\psi_{\text{heading}}(t) + \arctan\!\left(\frac{k_{\text{stanley}}\cdot e_{\text{lateral}}(t)}{V_x(t) + \epsilon_{\text{low\_speed}}}\right) + k_{\text{preview}}\cdot\kappa_{\text{curvature}}(t + t_{\text{preview}})$$

> O termo de preview de curvatura foi cortado em versões MVP anteriores; esta é a forma completa. Na arquitetura híbrida, o RL treinado offline sintoniza os pesos do NMPC online (mantendo as garantias físicas do controle ótimo).

---
