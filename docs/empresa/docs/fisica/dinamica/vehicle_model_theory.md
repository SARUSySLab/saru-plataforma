---
titulo: "Vehicle Model Theory"
data: "2026-06-26"
origem: "_arquivo/saru-physics-py/docs/vehicle_model_theory.md"
status: "vigente"
area: "dinamica_veicular"
---

# Vehicle Model Theory

Reference axes: ISO 8855 (x forward, y left, z up), origin at CG.

---

## Coordinate System

```
        z (up)
        |
        |_____ y (left)
       /
      x (forward)
```

- Slip angle α: positive when velocity points right (tires slip left) → positive Fy
- Camber γ: positive when top tilts right (rightward lean)
- Longitudinal slip κ: positive under drive (κ = (Vx_wheel - Vx) / Vx)
- Yaw r: positive counterclockwise (left turn from above)

---

## Model Hierarchy

| Model | DOFs | Use case | File |
|-------|------|---------|------|
| 3-DOF bicycle | yaw r, x, y | Quick sanity, optimizer FF | `chassis_3dof.m` |
| 7-DOF double-track | + roll φ + 4 wheel ω | Skidpad, acceleration | `chassis_7dof.m` |
| 14-DOF full | + pitch θ + 4 vertical z_wheel | Endurance, bump response | `chassis_14dof.m` |

---

## 14-DOF State Vector

```
State x (14 elements):
  [1]  u, longitudinal velocity [m/s] (body frame)
  [2]  v, lateral velocity [m/s] (body frame)
  [3]  w, vertical velocity [m/s] (body frame)
  [4]  p, roll rate [rad/s]
  [5]  q, pitch rate [rad/s]
  [6]  r, yaw rate [rad/s]
  [7]  ω_FL, front-left wheel spin [rad/s]
  [8]  ω_FR, front-right wheel spin
  [9]  ω_RL, rear-left wheel spin
  [10] ω_RR, rear-right wheel spin
  [11] z_FL, front-left unsprung vertical displacement [m]
  [12] z_FR, front-right unsprung vertical displacement
  [13] z_RL, rear-left unsprung vertical displacement
  [14] z_RR, rear-right unsprung vertical displacement

Integrated separately (position/attitude, not in ODE state):
  X, Y, Z, global position [m]
  φ, θ, ψ, Euler angles roll/pitch/yaw [rad]
```

---

## Tire Forces (MF5.2)

### Pure lateral (Fy)
```
SHy = pHy1 + pHy2·dFz + pHy3·γ
SVy = Fz·(pVy1 + pVy2·dFz + (pVy3 + pVy4·dFz)·γ)
αy  = α + SHy
Ky  = pKy1·Fz0·sin(2·atan(Fz/(pKy2·Fz0))) · (1 - pKy3·|γ|)
Cy  = pCy1
Dy  = Fz·(pDy1 + pDy2·dFz)·(1 - pDy3·γ²)
By  = Ky / (Cy·Dy)
Ey  = (pEy1 + pEy2·dFz)·(1 - (pEy3 + pEy4·γ)·sign(αy))
Fy0 = Dy·sin(Cy·atan(By·αy - Ey·(By·αy - atan(By·αy)))) + SVy
```

### Pure longitudinal (Fx)
```
SHx = pHx1 + pHx2·dFz
SVx = Fz·(pVx1 + pVx2·dFz)
κx  = κ + SHx
Dx  = Fz·(pDx1 + pDx2·dFz)·(1 - pDx3·γ²)
Cx  = pCx1
Bx  = (pKx1 + pKx2·dFz)·exp(-pKx3·dFz) / (Cx·Dx)
Ex  = pEx1 + pEx2·dFz + pEx3·dFz² + pEx4·sign(κx)
Fx0 = Dx·sin(Cx·atan(Bx·κx - Ex·(Bx·κx - atan(Bx·κx)))) + SVx
```

### Combined slip (Fx, Fy with interaction)
Uses weighting functions Gxa (Fx reduction under slip angle) and Gyk (Fy reduction under longitudinal slip):
```
Gxa  = cos(rCx1·atan(rBx1·(κ + rHx1)^2 · rBx2·α)) [reduces Fx with α]
Gyk  = cos(rCy1·atan(rBy1·(α + rHy1)^2 · rBy2·κ)) [reduces Fy with κ]
Fx   = Fx0 · Gxa
Fy   = Fy0 · Gyk + SVyk
```

### Camber input
γ (camber angle [rad]) comes from suspension kinematics:
```
γ = γ_static + camber_gain_body_roll × φ_body + dcamber_dz × Δz_wheel
```

---

## Restrictor Flow Model (IC Engine)

FSAE rule: 20mm diameter intake restrictor for IC vehicles.

Isentropic orifice flow (choked when P_manifold < P_crit):
```
P_crit = P_ambient · (2/(γ+1))^(γ/(γ-1))

If P_manifold > P_crit (subsonic):
  ṁ_max = Cd · A_restrict · P_ambient · sqrt(γ/(R·T)) ·
           (P_manifold/P_ambient)^(1/γ) ·
           sqrt(2/(γ-1) · (1 - (P_manifold/P_ambient)^((γ-1)/γ)))

If P_manifold ≤ P_crit (choked):
  ṁ_max = Cd · A_restrict · P_ambient · sqrt(γ/(R·T)) ·
           (2/(γ+1))^((γ+1)/(2(γ-1)))
```
Torque is then limited by the air mass flow:
`T_max = min(T_map(RPM), torque_from_mair(ṁ_max, RPM, AFR, eta_vol))`

---

## Lateral Load Transfer (LTD)

Total lateral load transfer ΔFz = m·ay·h_cg / track_width

Distributed front/rear by roll stiffness proportions:
```
K_φ_total = K_φ_f + K_φ_r + K_ARB_f + K_ARB_r

LTD_f = ΔFz · [K_φ_f/K_φ_total + m_f·h_rcf/track_f]
LTD_r = ΔFz · [K_φ_r/K_φ_total + m_r·h_rcr/track_r]
```
where h_rcf and h_rcr are the roll center heights.

---

## Numerical Integration

**Default solver:** `ode15s` (BDF, stiff)
- `RelTol = 1e-4`
- `AbsTol = 1e-6`
- Event detection: gear shifts (state discontinuity at upshift), wheel lift (Fz→0), track boundaries

**Gear shift handling:**
1. ODE integrates to gear shift event (RPM = rpm_shift_up)
2. Stop integration, update gear, recompute initial conditions
3. Resume ODE with new gear

**Why ode15s:**  
Tire contact patch stiffness (~190 kN/m) + suspension stiffness (~30 kN/m) creates eigenvalue spread of ~100x, making the system stiff. `ode45` would require ~1e6 steps per second → ~30 min for a 75m acceleration run.
