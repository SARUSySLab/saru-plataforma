---
titulo: "4. Cockpit Físico e Hardware (HiL/DiM)"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/06_4_cockpit_f_sico_e_hardware_hil_dim.md"
status: "vigente"
area: "dinamica_veicular"
---

## 4. Cockpit Físico e Hardware (HiL/DiM)

A simulação perpassa para a vida real em setups de Hardware-in-the-Loop.

- **Infraestrutura:** Sistemas acoplados via rede Beckhoff EtherCAT, onde computadores *Concurrent* processam as respostas do veículo em *hard-real-time*.
- **dSPACE MicroAutoBox III:** Emula placas ECUs reais do carro (usando `.dbc` files) para acionar freios BSM emulados sob *feedback* do solver Julia 14-DOF e trocando tráfego com *ML Toolkits* via UDP (100-1000Hz).

---
