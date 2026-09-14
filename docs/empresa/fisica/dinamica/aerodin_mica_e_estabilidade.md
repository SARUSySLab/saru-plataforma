---
titulo: "2.5. Aerodinâmica e Estabilidade"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/03_2_5_aerodin_mica_e_estabilidade.md"
status: "vigente"
area: "dinamica_veicular"
---

## 2.5. Aerodinâmica e Estabilidade

- **Sinal do Momento de Arfagem (Pitch):** Durante as auditorias do simulador 14-DOF transiente, detectou-se um erro crítico de implementação onde o momento de pitch aerodinâmico estava com o sinal invertido. Isso causava comportamento catastrófico (levantamento da frente em vez de downforce) em altas velocidades. Sempre validar o sistema de coordenadas (ISO vs SAE) ao acoplar o centro de pressão (CoP).

---
