---
titulo: "Modelo de Pneu Pacejka Magic Formula (MF 5.2+ / MF-Swift)"
data: "2026-06-26"
origem: "_arquivo/saru-physics-py/docs/tire_physics.md"
status: "vigente"
area: "pneu"
---

# Modelo de Pneu Pacejka Magic Formula (MF 5.2+ / MF-Swift)

Este documento consolida os coeficientes, equações e lógicas físicas utilizadas para modelagem de pneus no solver `saru-core`.

---

## 1. Estrutura Geral de Coeficientes MF 5.2+

Os arquivos `.tir` (formato padrão TNO) organizam os dados do pneu nas seguintes categorias:

### 1.1 Dimensões e Operação Básica
- **`R0` (UNLOADED_RADIUS):** Raio livre do pneu sem carga (m).
- **`Rrim` (RIM_RADIUS):** Raio nominal do aro/roda (m).
- **`w` (WIDTH):** Largura nominal da seção do pneu (m).
- **`Fz0` (FNOMIN):** Carga vertical nominal de referência (N).
- **`Vref` (LONGVL):** Velocidade linear nominal de referência (m/s).
- **`P0` (NOMPRES):** Pressão de inflação nominal de referência (Pa).
- **`P` (INFLPRES):** Pressão de operação do pneu (Pa).

### 1.2 Faixas de Validade
- **`FZMIN` / `FZMAX`:** Limites de carga vertical suportados pelo modelo.
- **`KPUMIN` / `KPUMAX`:** Faixa de validade do slip longitudinal ($\kappa$).
- **`ALPMIN` / `ALPMAX`:** Faixa de validade do slip lateral / ângulo de deriva ($\alpha$).
- **`CAMMIN` / `CAMMAX`:** Faixa de validade do ângulo de cambagem ($\gamma$).

---

## 2. Coeficientes Fx Puros (Frenagem/Tração)
Equacionamento longitudinal em pista seca sob slip puro ($\kappa$):

| Parâmetro | Palavra-chave | Papel Físico |
|-----------|---------------|--------------|
| **`pCx1`** | PCX1 | Fator de forma $C_{fx}$ (comportamento de "stretch" em x) |
| **`pDx1`** | PDX1 | Atrito longitudinal nominal $\mu_x$ em $F_{z0}$ (pico D) |
| **`pDx2`** | PDX2 | Variação de $\mu_x$ com a carga vertical $F_z$ |
| **`pDx3`** | PDX3 | Variação de $\mu_x$ com cambagem $\gamma$ |
| ****`pKx1`**** | PKX1 | Rigidez de slip nominal $K_{fx}/F_{z0}$ (inclinação inicial) |
| **`pKx2`** | PKX2 | Variação de $K_{fx}/F_{z0}$ com $F_z$ |
| **`pKx3`** | PKX3 | Expoente de dependência não-linear com $F_z$ |
| **`pEx1`** | PEX1 | Curvatura de cauda $E_{fx}$ na carga nominal |
| **`pEx2`** | PEX2 | Variação de $E_{fx}$ com $F_z$ |
| **`pEx3`** | PEX3 | Variação quadrática de $E_{fx}$ com $F_z$ |
| **`pEx4`** | PEX4 | Fator de curvatura durante rodagem |
| **`pHx1`** | PHX1 | Deslocamento horizontal $S_{hx}$ na carga nominal (offset de offset $\kappa$) |
| **`pHx2`** | PHX2 | Variação de $S_{hx}$ com $F_z$ |
| **`pVx1`** | PVX1 | Deslocamento vertical $S_{vx}/F_{z0}$ na carga nominal |
| **`pVx2`** | PVX2 | Variação de $S_{vx}$ com $F_z$ |

---

## 3. Coeficientes Fy Puros (Força Lateral)
Equacionamento lateral sob ângulo de deriva puro ($\alpha$) e cambagem ($\gamma$):

| Parâmetro | Palavra-chave | Papel Físico |
|-----------|---------------|--------------|
| **`pCy1`** | PCY1 | Fator de forma $C_{fy}$ para força lateral |
| **`pCy2`** | PCY2 | Fator de forma $C_{fc}$ para rigidez de cambagem |
| **`pDy1`** | PDY1 | Atrito lateral nominal $\mu_y$ em $F_{z0}$ |
| **`pDy2`** | PDY2 | Variação de $\mu_y$ com carga vertical $F_z$ |
| **`pDy3`** | PDY3 | Variação de $\mu_y$ com cambagem $\gamma^2$ |
| **`pKy1`** | PKY1 | Pico de rigidez lateral adimensional $K_{fy}/F_{z0}$ |
| **`pKy2`** | PKY2 | Carga vertical onde $K_{fy}$ atinge o valor de pico |
| **`pKy3`** | PKY3 | Variação de $K_{fy}/F_{z0}$ com cambagem $\gamma$ |
| **`pKy4`** | PKY4 | Variação de rigidez com $\gamma^2$ |
| **`pKy5`** | PKY5 | Dependência não-linear da rigidez com cambagem |
| **`pKy6`** | PKY6 | Fator de rigidez de cambagem nominal |
| **`pKy7`** | PKY7 | Variação da rigidez de cambagem com a carga $F_z$ |
| **`pEy1`** | PEY1 | Fator de curvatura lateral $E_{fy}$ em $F_{z0}$ |
| **`pEy2`** | PEY2 | Variação de $E_{fy}$ com $F_z$ |
| **`pEy3`** | PEY3 | Dependência de $E_{fy}$ com cambagem (termo fixo) |
| **`pEy4`** | PEY4 | Variação de $E_{fy}$ com cambagem |
| **`pEy5`** | PEY5 | Curvatura de cambagem lateral $E_{fc}$ |
| **`pHy1`** | PHY1 | Deslocamento horizontal $S_{hy}$ em $F_{z0}$ |
| **`pHy2`** | PHY2 | Variação de $S_{hy}$ com $F_z$ |
| **`pHy3`** | PHY3 | Variação de $S_{hy}$ com cambagem $\gamma$ |
| **`pVy1`** | PVY1 | Deslocamento vertical $S_{vy}/F_{z0}$ na carga nominal |
| **`pVy2`** | PVY2 | Variação de $S_{vy}$ com $F_z$ |
| **`pVy3`** | PVY3 | Variação de $S_{vy}$ com cambagem $\gamma$ |
| **`pVy4`** | PVY4 | Variação combinada de $S_{vy}$ com $\gamma$ e $F_z$ |

---

## 4. Combined Slip (Escorregamento Combinado)

Sob aceleração e curva simultâneas (derrapagem combinada), as forças longitudinais e laterais sofrem atenuação:

$$F_x^{\text{combined}} = \frac{S_x}{\sqrt{S_x^2 + S_y^2}} \cdot F_x^{\text{pure}}(S_{\text{combined}})$$

$$F_y^{\text{combined}} = \frac{S_y}{\sqrt{S_x^2 + S_y^2}} \cdot F_y^{\text{pure}}(S_{\text{combined}})$$

### Coeficientes de Atenuamento (Seção `[COMBINED_COEFFICIENTS]`):
- **`rBx1`, `rBx2`, `rBx3`:** Modificam a inclinação longitudinal devido ao slip lateral.
- **`rBy1`, `rBy2`, `rBy3`, `rBy4`:** Modificam a inclinação lateral devido ao slip longitudinal.
- **`rCx1` / `rCy1`:** Fator de forma para combined slip em x / y.
- **`rEx1`, `rEx2` / `rEy1`, `rEy2`:** Coeficientes de curvatura em combinado.
- **`rHy1`, `rHy2` / `rVy1` a `rVy6`:** Efeitos de offset e plysteer/kappa steer combinados.

---

## 5. Efeito da Pressão do Pneu (MF 5.2+)
- **`pPx1`, `pPx2` / `pPy1`, `pPy2`:** Efeito linear/quadrático da pressão na rigidez longitudinal e lateral ($K_{fx}$ e $K_{fy}$).
- **`pPx3`, `pPx4` / `pPy3`, `pPy4`:** Efeito linear/quadrático da pressão na aderência máxima ($\mu_x$ e $\mu_y$).
- **`pPy5`:** Efeito da pressão sobre a rigidez de cambagem.

---

## 6. Modelo Estrutural, Transiente e Térmico (14-DOF / MF-Swift)

### 6.1 Transiente e Relaxation Length
Modelagem do atraso elástico do patch em relação ao movimento da roda ($\sigma$):

$$\sigma = \frac{dF_y}{d\alpha} \cdot \frac{1}{C_\alpha}$$

- **`PTX1`, `PTX2`, `PTX3`:** Coeficientes de comprimento de relaxamento fore/aft ($S_x$).
- **`PTY1`, `PTY2`:** Coeficientes de comprimento de relaxamento lateral ($S_y$).

### 6.2 Parâmetros Estruturais (MF-Swift)
Utilizados no acoplamento acausal do 14-DOF:
- **`Cz0` (VERTICAL_STIFFNESS):** Rigidez vertical do pneu (N/m).
- **`qre0` / `qv1` / `qFz2`:** Crescimento centrífugo e variações do raio de rolamento dinâmico.
- **`mtyre` (MASS):** Massa total do pneu (kg).
- **`mbelt` (BELT_MASS):** Massa do cinturão (belt) estrutural (kg).
- **`IXXtyre` / `IYYtyre`:** Inércias polares e transversais do pneu.
- **`flong` / `flat` / `fyaw` / `fwindup`:** Frequências naturais de vibração dos modos fore/aft, lateral, torção e torção do belt.

### 6.3 Modelo Térmico (Friction Decay)
Queda de aderência com base na temperatura de trabalho ($T_{\text{tire}}$):

$$\mu_{\text{thermal}} = \mu_{\text{opt}} \cdot \left[ 1 - k_{\text{decay}} \cdot (T_{\text{tire}} - T_{\text{opt}}) \right]$$

- **`TEMP_LONG_REF` / `TEMP_LAT_REF`:** Temperatura nominal ótima de operação ($\sim 80^\circ\text{C}$ a $100^\circ\text{C}$).
- **`DFX_DTEMP` / `DFY_DTEMP`:** Coeficiente linear de decaimento de grip por grau adicional ($k_{\text{decay}} \approx 0.001$ a $0.003\text{ /}^\circ\text{C}$).
- **Canais de Calor:** A geração de energia térmica $Q$ é calculada passo a passo via dissipação por atrito: $Q_{\text{gen}} \approx F_x \cdot V_{\text{slip},x} + F_y \cdot V_{\text{slip},y}$.
