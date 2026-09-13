---
titulo: "Especificação de Dinâmica Veicular: Modelo OptimumG & Calculadoras de Pista"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/physics/load_transfer_optimumg.md"
status: "vigente"
area: "dinamica_veicular"
---

# Especificação de Dinâmica Veicular: Modelo OptimumG & Calculadoras de Pista

Este documento define a especificação física e matemática integrada ao **saru-app** (`saru-core` / `services/telemetry-api`), baseada nas planilhas e seminários numéricos da **OptimumG** e MoTeC i2.

---

## 1. Transferência de Carga Tridimensional (4-Wheels Load Transfer)

A força vertical em cada uma das quatro rodas ($F_{z,FL}, F_{z,FR}, F_{z,RL}, F_{z,RR}$) é a soma da carga estática ($F_{z,static}$), carga aerodinâmica ($F_{z,aero}$), transferência longitudinal ($\Delta F_{z,long}$) e transferência lateral ($\Delta F_{z,lat}$).

### 1.1 Carga Estática & Aerodinâmica

$$F_{z,static,front} = \frac{m \cdot g \cdot (1 - \text{WD})}{2}$$
$$F_{z,static,rear} = \frac{m \cdot g \cdot \text{WD}}{2}$$

$$F_{z,aero} = \frac{1}{2} \rho \cdot V_x^2 \cdot C_L \cdot A \cdot \text{AeroBal}$$

Onde $\text{WD}$ é a distribuição de peso estática traseira ($0.0 - 1.0$), $C_L A$ é a área de downforce e $\text{AeroBal}$ é o balanço aerodinâmico dianteiro.

### 1.2 Transferência de Carga Longitudinal ($\Delta F_{z,long}$)

Durante aceleração ($a_x > 0$) ou frenagem ($a_x < 0$):

$$\Delta F_{z,long} = \frac{m \cdot a_x \cdot h_{cg}}{2 \cdot L}$$

- Carga Dianteira: $F_{z,front} = F_{z,static,front} - \Delta F_{z,long}$
- Carga Traseira: $F_{z,rear} = F_{z,static,rear} + \Delta F_{z,long}$

### 1.3 Transferência de Carga Lateral ($\Delta F_{z,lat}$)

Composta por 3 componentes independentes (OptimumG Load Transfer Formulation):

1. **Componente Não-Massa Suspensa (Unsprung Load Transfer):**
   $$\Delta F_{z,us,f} = \frac{m_{us,f} \cdot a_y \cdot r_w}{t_{w,f}}$$

2. **Componente Cinemática/Centro de Rolagem (Geometric Load Transfer):**
   $$\Delta F_{z,geom,f} = \frac{m_s \cdot a_y \cdot h_{rc,f} \cdot (1 - \text{WD})}{t_{w,f}}$$

3. **Componente Elástica/Molas e Anti-roll Bar (Elastic Load Transfer):**
   $$\Delta F_{z,elastic,f} = \left( \frac{K_{\phi,f}}{K_{\phi,f} + K_{\phi,r}} \right) \cdot \frac{m_s \cdot a_y \cdot (h_{cg} - h_{rc,avg})}{t_{w,f}}$$

Onde $K_{\phi,f}$ é a rigidez de rolagem total da suspensão dianteira ($\text{N}\cdot\text{m/rad}$), combinando molas principais e barras estabilizadoras (ARB).

---

## 2. Modelo de Amortecedores Não-Lineares (4-Way Dampers)

A força de amortecimento em cada canto $i \in \{FL, FR, RL, RR\}$ é função da velocidade da haste do amortecedor ($v_d = \dot{z}_{susp}$):

$$F_d(v_d) = \begin{cases}
c_{ls,bump} \cdot v_d & \text{se } 0 \le v_d \le v_{knee} \quad (\text{Low Speed Bump}) \\
F_{knee,bump} + c_{hs,bump} \cdot (v_d - v_{knee}) & \text{se } v_d > v_{knee} \quad (\text{High Speed Bump}) \\
c_{ls,reb} \cdot v_d & \text{se } -v_{knee} \le v_d < 0 \quad (\text{Low Speed Rebound}) \\
-F_{knee,reb} + c_{hs,reb} \cdot (v_d + v_{knee}) & \text{se } v_d < -v_{knee} \quad (\text{High Speed Rebound})
\end{cases}$$

---

## 3. Algoritmo de Calculadora de Combustível

Cálculo de combustível mínimo necessário para a corrida com margem de segurança:

$$V_{fuel,total} = (N_{laps} \cdot \bar{c}_{lap}) + V_{formation} + V_{safety}$$

- $\bar{c}_{lap}$: Consumo médio por volta (medido via taxa de fluxo $\int \dot{m}_{fuel} dt$ da telemetria real).
- $V_{safety}$: Margem de segurança (geralmente 1.5 a 2.0 voltas adicionais).

---

## 4. Algoritmo de Janela Térmica de Pressão de Pneus

Relação da pressão fria no box ($P_{cold}$) para atingir a pressão de trabalho ideal na pista ($P_{target}$):

$$P_{hot} = (P_{cold} + P_{atm}) \cdot \left( \frac{T_{hot} + 273.15}{T_{cold} + 273.15} \right) - P_{atm} + \Delta P_{moisture}$$

Onde $T_{hot}$ é estimado empiricamente a partir da temperatura da pista ($T_{track}$) e energia de fricção acumulada pelo pneu durante o stint.
