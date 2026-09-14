---
titulo: "Formatos de Pistas no Ecossistema SARU"
data: "2026-06-26"
origem: "_arquivo/saru-physics-py/docs/track_formats.md"
status: "vigente"
area: "dinamica_veicular"
---

# Formatos de Pistas no Ecossistema SARU

Este documento descreve os padrões de armazenamento de pistas (HDF5 para solvers QSS e OpenCRG para solvers transientes 14-DOF), bem como o pipeline para modelar o Autódromo de Brasília Nelson Piquet (configuração 2026).

---

## 1. HDF5 (Solvers QSS / 3-DOF)

Os solvers de estado quase-estacionário (QSS) da SARU em Python consomem uma malha estruturada discreta armazenada em arquivos `.h5` ou `.hdf5`. Essa malha deve ter passo de discretização longitudinal uniforme ($\Delta s \le 1.0\text{ m}$).

### 1.1 Schema do HDF5
O arquivo de pista deve respeitar a seguinte hierarquia de datasets:

```text
/
├── track/
│   ├── geometry/
│   │   ├── distance    [double]  # Distância acumulada s (m) [0, s_max]
│   │   ├── x           [double]  # Coordenada UTM X / Leste (m)
│   │   ├── y           [double]  # Coordenada UTM Y / Norte (m)
│   │   ├── z           [double]  # Altitude/Elevação z (m)
│   │   ├── curvature   [double]  # Curvatura local κ (1/m) (raio = 1/κ)
│   │   ├── banking     [double]  # Inclinação lateral / superelevação (rad)
│   │   ├── gradient    [double]  # Inclinação longitudinal dz/ds (rad ou %)
│   │   └── width       [double]  # Largura da pista local (m)
│   └── metadata/
│       ├── name        [string]  # Nome da pista (ex: "Brasilia_Completo_2026")
│       ├── length      [double]  # Extensão total da pista (m)
│       └── direction   [string]  # Sentido ("clockwise" ou "counter-clockwise")
```

---

## 2. OpenCRG (Solvers Transientes 14-DOF)

O padrão ASAM OpenCRG (Curved Regular Grid) é utilizado nos solvers dinâmicos 14-DOF em C++ e Julia para representar a pista em 3D de forma contínua com alta fidelidade (resolução milimétrica).

### 2.1 Estrutura do Grid CRG
- **Linha de Referência:** Define o eixo da pista ($u$, coordenada longitudinal) a partir de um ponto inicial ($x_0, y_0$), heading ($\phi_0$) e curvature map.
- **Elevation Grid ($KD\_DATA\_GRID$):** Matriz bidimensional indexada por $(u, v)$, onde $v$ representa o deslocamento lateral em relação à linha de referência. Cada ponto da matriz armazena a elevação vertical local $z$ (m).
- **Parâmetros Típicos:**
  - `ROAD_CRG_U_INC` (Longitudinal resolution): $\le 0.1\text{ m}$ (essencial para capturar zebras e ondulações).
  - `ROAD_CRG_V_WIDTH` (Track width): $\sim 12.0$ a $15.0\text{ m}$.
  - `ROAD_CRG_V_INC` (Lateral resolution): $\approx 0.1\text{ m}$.

### 2.2 Requisitos do Solver 14-DOF
- O solver lê o arquivo `.crg` e projeta as coordenadas globais de cada pneu $(x, y)$ em coordenadas locais do grid $(u, v)$.
- A função de interpolação retorna de forma rápida e segura: a elevação $z$, as derivadas espaciais ($\partial z/\partial u$, $\partial z/\partial v$) e o coeficiente de atrito local $\mu$.

---

## 3. Autódromo de Brasília BRB (2026)

### 3.1 Especificações da Pista (Layout Completo)
- **Extensão:** $5476\text{ m}$
- **Número de Curvas:** 15
- **Largura Média:** $12.0$ a $15.0\text{ m}$
- **Maior Reta:** $\sim 900\text{ m}$
- **Sentido:** Anti-horário (Counter-clockwise)

### 3.2 Pipeline de Extração e Suavização
Devido ao ruído em dados topográficos de satélite (como SRTM de 30m), a centerline bruta gera oscilações espúrias na curvatura que travam os solvers. O pipeline oficial de extração e suavização da SARU executa o seguinte algoritmo em Python:

```python
import numpy as np
from scipy.interpolate import splprep, splev
import h5py

def build_saru_track(x_raw, y_raw, z_raw, s_step=0.5):
    """
    Interpola dados brutos (x, y, z) usando splines cúbicas parametrizadas
    pela distância acumulada (s) para evitar ruído de amostragem.
    """
    # 1. Ajuste de Spline Paramétrica
    tck, u = splprep([x_raw, y_raw, z_raw], s=1.0, per=True)
    
    # 2. Re-amostragem com passo uniforme
    u_fine = np.arange(0, 1.0001, 1.0 / 10000)
    x, y, z = splev(u_fine, tck)
    
    # Calcular distância acumulada real (s)
    dx = np.diff(x)
    dy = np.diff(y)
    dz = np.diff(z)
    ds = np.sqrt(dx**2 + dy**2 + dz**2)
    s = np.concatenate(([0], np.cumsum(ds)))
    
    # 3. Interpolação para grade uniforme final (ex: passo de 0.5m)
    s_grid = np.arange(0, s[-1], s_step)
    x_fine = np.interp(s_grid, s, x)
    y_fine = np.interp(s_grid, s, y)
    z_fine = np.interp(s_grid, s, z)
    
    # 4. Cálculo Analítico da Curvatura (κ = 1/R)
    dx_ds = np.gradient(x_fine, s_grid)
    dy_ds = np.gradient(y_fine, s_grid)
    d2x_ds2 = np.gradient(dx_ds, s_grid)
    d2y_ds2 = np.gradient(dy_ds, s_grid)
    
    curvature = (dx_ds * d2y_ds2 - dy_ds * d2x_ds2) / (dx_ds**2 + dy_ds**2)**(1.5)
    
    # 5. Gradiente Longitudinal
    gradient = np.gradient(z_fine, s_grid)
    
    return s_grid, x_fine, y_fine, z_fine, curvature, gradient
```

---

## 4. Análise de Desempenho: Causal vs Acausal

### 4.1 Limitações do Python QSS (Causal)
Os solvers QSS tradicionais programados em Python resolvem o sistema de dinâmica veicular de forma sequencial-causal passo a passo. 
- **Problema:** O overhead de chamadas de função e laços do interpretador de Python, somado à rigidez (stiffness) do acoplamento do modelo de pneu Pacejka com o chassi, limita o desempenho da simulação a taxas muito superiores a $200\text{ ms}$ por volta.

### 4.2 Vantagens do Julia ModelingToolkit (Acausal)
O solver do `saru-core-jl` (Julia) migra as equações diferenciais e algébricas (DAE) para uma formulação acausal:
- **Redução Simbólica:** O ModelingToolkit.jl reorganiza e simplifica o sistema de equações em tempo de compilação, gerando jacobianos analíticos otimizados e eliminando estados redundantes.
- **Sub-50ms:** A geração de código nativo via LLVM e o uso de integradores rígidos (como Radau ou BDF do DifferentialEquations.jl) reduzem o tempo de integração de uma volta completa em Brasília para **menos de 50 milissegundos**, viabilizando análises de sensibilidade em larga escala (sweeps) na nuvem.
