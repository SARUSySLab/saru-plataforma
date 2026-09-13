---
titulo: "saru-core-jl, Referências & Agenda de Pesquisa"
data: "2026-07-07"
origem: "_arquivo/saru-physics-jl/docs/REFERENCES-AND-RESEARCH.md"
status: "vigente"
area: "dinamica_veicular"
---

# saru-core-jl, Referências & Agenda de Pesquisa

> Materiais usados na modelagem 14-DOF + o que falta pesquisar para tirar o solver da
> calibração empírica e levá-lo a física grounded. Companheiro de `ROADMAP.md` (o que fazer)
> e `AUDIT-FINDINGS.md` (dívida atual). Última revisão: 2026-06-29.

---

## 0. TL;DR, por que este documento existe

O 14-DOF (`src/simulation/Transient14DOF.jl`) **bate o oráculo (94,42 s vs 94,0 ± 1,0)**, mas
com **2 fatores de calibração empíricos** (`grip_cal=1.30`, `torque_cal=1.15`) que mascaram física
ausente/imprecisa e parâmetros não-grounded. Este doc lista **(A)** as fontes que já existem no
ecossistema e foram usadas, **(B)** a comparação parâmetro-a-parâmetro do que rodamos vs a
referência, e **(C)** o que pesquisar para substituir os fudges por física real.

---

## A. Materiais utilizados (existem no ecossistema, PORTAR, não reinventar)

### A.1 Equações do chassi 14-DOF (fonte canônica)
- **`~/Projects/01_UnB/FullVehicleSimulation/docs/equations_reference.md`**, Khalil et al. (2018)
  Eq. 1-26 mapeadas linha-a-linha em `classes/VehicleModel14DOF.m`. Cobre handling (Eq. 11-13),
  ride (Eq. 2-10), kinematics/slip (Eq. 16-17), tire (Eq. 20-23), wheel spin (Eq. 24).
  - **Ref. primária:** Khalil et al., *"Dynamic characterization and stability control of an
    experimental heavy-duty vehicle with an active anti-roll bar system"*, Vehicle System
    Dynamics, 2018. ⚠️ **SAE J670** (converter p/ ISO 8855 ao portar, ver [MASTER_ADR §3.1]).
- **`~/Projects/01_UnB/FullVehicleSimulation/docs/Modeling, Simulation and Validation of 14 DOF.PDF`**, paper de referência do modelo 14-DOF completo.

### A.2 Teoria de modelo + pneu (saru-core, Python)
- **`platform/saru-core/docs/vehicle_model_theory.md`**, vetor de estado 14-DOF, Pacejka **MF5.2**
  (Fx/Fy puros + combined-slip via `Gxa`/`Gyk`), LTD (load transfer por rigidez de roll +
  roll-center heights), solver `ode15s` (BDF stiff, RelTol 1e-4).
- **`platform/saru-core/docs/tire_physics.md`**, catálogo completo de coeficientes **MF6.2/MF-Swift**
  (`.tir` TNO): Fx/Fy puros, combined, pressão, transiente (relaxation length), térmico.
- **`platform/saru-core/docs/PHYSICS_AUDIT.md`**, **Discrepância #9 (load sensitivity):**
  `mu_eff = mu·(1 − K_LS·ΔFz_frac)`. Sem ela → picos irreais 2,4-2,8 g → 75 s ao invés de 94,4 s
  em Interlagos. **Confirma que o oráculo de 94,4 s depende de load-sensitivity.**

### A.3 Modelos de pneu de referência (MATLAB, prontos)
- `~/Projects/01_UnB/FullVehicleSimulation/classes/TireModelLinear.m`, `Fy=Cα·α`, `Fx=Cσ·σ`
  (modelo validado contra Khalil).
- `.../classes/TireModelMF62.m`, Magic Formula MF6.2 completa.
- `.../classes/TireModelPacejka.m`, Pacejka clássico.

### A.4 Parâmetros de veículo grounded (MATLAB)
- `~/Projects/01_UnB/FullVehicleSimulation/common/params/params_khalil2018.m`, **único conjunto
  validado** (veículo pesado, 1905 kg). Estrutura de referência p/ um YAML correto.
- `.../params/{params_apuama_fsae, params_toro, params_suv, params_caminhao}.m`, outros veículos.
- ⚠️ **Nenhum é o Porsche 992 GT3 R**, ver gap B.3.

### A.5 Dados de pneu (.tir)
- `~/Projects/_shared/tire_data/225_60R18_65J_SCORPN_IP38393_TIR_V001.tir`, **Pirelli Scorpion SUV**,
  MF6.2 completo. **Único `.tir` disponível.** Serve de *template de parser*, **não** de dado GT3.

### A.6 Livros-texto (PDFs em `FullVehicleSimulation/docs/`)
- Pacejka, *Tire and Vehicle Dynamics* (implícito via MF) · Gillespie, *Fundamentals of Vehicle
  Dynamics* (SAE) · Guiggiani, *The Science of Vehicle Dynamics* · Rajamani, *Vehicle Dynamics and
  Control* · Nicolazzi, *Dinâmica de Veículos* (PT) · Khalil 2018 PDF.

### A.7 Justificativa de arquitetura (acausal/MTK)
- `saru-KB/domain-knowledge/guia_essencial_modelagem_causal_vs._acasual_no_design_de_sistemas.md`
- `.../relatório_de_pesquisa_técnica_simulação_avançada_modelagem_acausal_e_arquitetura_de_veículos_definidos_por_software_(sdv).md`
- `.../2026_04_06_modelagem_veicular_e_controle_nmpc.md`

---

## B. Comparação: o que rodamos vs a referência

### B.1 Chassi (Eq. 11-13 Khalil vs nosso solver)
| Item | Khalil/MATLAB (ref) | `Transient14DOF.jl` | Veredito |
|---|---|---|---|
| Estrutura handling (dvx/dvy/dr) | Eq. 11-13 | mesma topologia (proj cosδ/sinδ, momentos a/b, diff track) | ✅ fiel |
| Coriolis (sinais) | SAE J670 (`−vy·r`, `+vx·r`) | ISO 8855 (`+vy·r`, `−vx·r`) | ✅ consistente c/ ISO; **mapear conversão explícita** |
| Ride (Ps, bounce, pitch, roll) | Eq. 2-10 | mesma topologia spring+damper+ARB | ✅ fiel |

### B.2 Pneu, **principal divergência**
| Item | Referência | Nosso solver | Problema |
|---|---|---|---|
| Modelo | TireModelLinear (Cα) validado; MF6.2 disponível | "resultant-slip" 1-mu (similarity) | modelo cru, não MF |
| Combined-slip | `Gxa`/`Gyk` (cosseno, MF6.2) | split vetorial `κ/√(κ²+α²)` | aproximação grosseira |
| Load-sensitivity | `Dy=Fz·(pDy1+pDy2·dFz)` (dado) | `(1 − 0.20·(Fz−4000)/4000)` (K_LS chutado) | proxy, não calibrado |
| Cornering stiffness | YAML traz `Cα_f=85000`, `Cα_r=100000` | **IGNORADO** (usa B/C/D/E) | B=22·C·D ⇒ Cα≈220k N/rad = **2,6× o spec** |
| Coefs Pacejka | de `.tir` real | B22/C1.4/D1.8/E0.9 **sintéticos** | sem dado GT3 |

### B.3 Parâmetros hardcoded no solver (deveriam vir do YAML)
| Param | Valor hardcoded | Khalil ref | Ação |
|---|---|---|---|
| `m_u` (não-suspensa/roda) | **45 kg** (L370) | 95,5 kg | mover p/ YAML |
| `Iw` (inércia roda) | **1,5 kg·m²** (L421) | 1,0 (estimado) | mover p/ YAML |
| `Kt` (rigidez radial pneu) | **250000 N/m** (L420) |, (`Cz0` no `.tir`) | mover p/ YAML / `.tir` |
| `Fz0` (carga nominal) | **4000 N** (L411) | `FNOMIN` do `.tir` | vir do `.tir` |

### B.4 Fatores de calibração (dívida, o que cada um mascara)
| Fator | Valor | Mascara |
|---|---|---|
| `grip_cal` | 1.30 | combined-slip cru + coefs pneu não-grounded + sem load-transfer lateral por roll-center |
| `torque_cal` | 1.15 | tração RWD per-axle (só 2 pneus) + ausência de mapa de potência limitado por marcha |
| `cd+0.06`, `cl−0.12`, `mu·0.968`, rr `0.015` (prepass) |, | herdados do Harness QSS (drag induzido, mapa aero, load-sensitivity, Crr) |

---

## C. O que pesquisar para complementar (agenda)

### C.1 Física (substituir fudges por modelo)
- [ ] **MF6.2 combined-slip completo** (`Gxa`/`Gyk`) portado de `TireModelMF62.m` →
      elimina `grip_cal` e o split vetorial cru. **Maior alavanca.**
- [ ] **Load-sensitivity calibrada** de dado (`pDy1/pDy2`), não `K_LS` chutado (PHYSICS_AUDIT #9).
- [ ] **Transferência de carga lateral (LTD)** por rigidez de roll + roll-center heights
      (`vehicle_model_theory.md` §LTD), hoje o roll sai só das forças de mola.
- [ ] **Self-aligning moment `Mz`** no yaw (equations_reference "ERRO 6" pendente).
- [ ] **Relaxation length / pneu transiente** (`σ = (dFy/dα)/Cα`), atraso do patch.
- [ ] **Modelo térmico do pneu** (`μ_thermal`, geração `Q=F·V_slip`) → remove temp `65°C`.
- [ ] **Aero induzido + mapa 3D** (`Cd0+k·Cl²`, ride-height) → remove `cd+0.06`/`cl−0.12`.
- [ ] **Restritor de admissão** (FSAE 20 mm, choked flow), **só p/ veículo FSAE**, não GT3.

### C.2 Parâmetros (grounding)
- [ ] **`.tir` real do Michelin slick LMGT3** (ou GT3 genérico MF6.2) → substituir B/C/D/E sintéticos.
      Hoje só há o Pirelli SUV. **Bloqueador de fidelidade do pneu.**
- [ ] **Inércias/CG/massa não-suspensa reais do 992 GT3 R** (homologação LMGT3 / ficha técnica).
- [ ] **Parser `.tir` (MF6.2/MF-Swift) em Julia**, template: o `.tir` Pirelli; estrutura em `tire_physics.md`.
- [ ] **Mapa de aero do GT3 R** (Cl/Cd vs ride-height/yaw) e **rampa do LSD** (preload, ramp angles).
- [ ] Mover `m_u`, `Iw`, `Kt`, `Fz0`, `Cα` p/ o YAML/`.tir` (sem magic numbers, ver B.3).

### C.3 Estudos de caso / validação (validar canais, não 1 número)
- [ ] **Testes isolados por equação** vs figuras Khalil (Fig. 17 yaw, Fig. 21 pitch), replicar a
      suíte MATLAB (`test_steering_coupling`, `verify_equilibrium`) em Julia.
- [ ] **Manobras-padrão:** skidpad (ay constante), aceleração 0-100, frenagem, double-lane-change,
      fishhook (roll). Métricas por canal (ay, r, φ, slip, RPM), não só lap-time.
- [ ] **Overlay vs telemetria real** (quando houver dado de pista), gate anti-"casar 1 número".

### C.4 Simulação de uso (produto)
- [ ] **DoE / otimização de setup:** varrer k/c/ARB/bias/ratios/aero via YAML (sem magic numbers).
- [ ] **Endurance:** consumo de combustível (massa variável) + degradação de pneu (térmico/desgaste).
- [ ] **Multi-pista:** generalizar além de Interlagos (parser HDF5 de centerline genérico já existe).
- [ ] **Integração worker:** teste end-to-end na fila Redis do `saru-os` (contrato YAML+HDF5 → lap+telemetria).

---

## D. Gate de validação (não esquecer)
> **Anti-padrão:** calibrar para casar **1 número** (lap-time). O 94,42 s atual é exatamente isso.
> Física só "entra" quando os **canais** (vel, ay/ax, slip, RPM, deflexões, temp) batem a referência.
> Cada fudge removido em C.1/C.2 deve **manter** o lap em 94 ± 1 **e** melhorar um canal.
