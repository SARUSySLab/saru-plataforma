---
titulo: "1. Paradigmas de Simulação Física"
data: "2026-07-14"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/modules/01_1_paradigmas_de_simula_o_f_sica.md"
status: "stale"
area: "fisica"
---

## 1. Paradigmas de Simulação Física

A arquitetura do SARU se divide em duas frentes de fidelidade mecânica para lidar com os limites da simulação.

### 1.1 Solver Causal QSS (Python / `saru-core`)
- Utilizado como camada síncrona para análises **Quasi-Steady State (QSS)** em massa (usando paralelismo CUDA/NVIDIA Warp para avaliação extensiva de *setup*).
- O modelo baseia-se num fluxo explícito clássico (forças que induzem acelerações que são integradas), e usa componentes matemáticos validados e rígidos (ex: integradores `ode15s`).

### 1.2 Solver Acausal Transiente (Julia / `saru-core-jl`)
- Alvo de P&D focado na **Modelagem Acausal** (usando `ModelingToolkit.jl`). A física é baseada puramente em equações de conservação de energia, sem fluxo de sinal forçado.
- Permite a implementação robusta do **Modelo 14-DOF** (14 Graus de Liberdade: 6 da massa suspensa, 8 das rodas) e a integração implícita de DAEs (Differential-Algebraic Equations) complexas usando Redução de Índice (Algoritmo de Pantelides).
- **Problema de Integração Numérica:** Identificou-se que o uso do solver `QNDF` com `reltol=1e-5` é subótimo para as DAEs descontínuas do modelo 14-DOF. A migração estrutural para o solver `TRBDF2` (ou similar) aproveitando Jacobianos esparsos (*Sparse Jacobians*) é estritamente necessária para garantir a convergência em tempo real.

### 1.3 Two-Tier vs Surrogate Neural, decisão (pesquisa 2026-07-01)

> Fonte: gdoc *Unificação de Modelos Veiculares: 2 Tiers vs Surrogate*.

Avaliou-se substituir os dois tiers (QSS/3-DOF Python + 14-DOF Julia) por um **modelo único servido via surrogate neural** (PINN/CTESN/DeepONet). **Rejeitado para dev solo:** latência de retreino paralisa o setup (mexeu num parâmetro → regerar dataset + retreinar); viola física fora do envelope (erro de yaw até ~91% sem combined-slip); 6-18 meses de pipeline + gargalo de dados (dezenas de milhares de runs de 50 s).

- **Padrão da indústria** (F1 DIL, VI-grade, IPG CarMaker): hi-fi offline → **tabelas de lookup K&C** (cinemática/complacência pré-mapeadas) → solver rígido em tempo real @1000 Hz. IA entra **só em subcomponente lento/contínuo** (amortecedor AI-MBD Astemo, calor de pneu), nunca o carro inteiro.
- **Alvo de longo prazo Oficial (Approach-3: "MuJoCo / CUDA Integration"):** manter two-tier, mas com fonte única de veículo. A planta física de alta fidelidade (14-DOF) descrita simbolicamente no Julia (`ModelingToolkit.jl`) deve ser exportada para o ecossistema Google DeepMind (XML `MJCF` + `MuJoCo Warp` ou `Brax/MJX`). Isso permite ao Python (QSS/Batch) disparar dezenas de milhares de simulações na GPU (CUDA) sem perder a matemática rigorosa do Julia. (Decisão iniciada em 2026-07-02).

### 1.4 Worker 14-DOF: viabilidade real-time + otimização (pesquisa 2026-07-01)

> Fontes: gdocs *Simulação Veicular 14-DOF Julia* + *Otimização de Simulador Julia*.

- **Real-time só desacoplado em 2 camadas de frequência** (padrão DIL): a planta 14-DOF (TRBDF2, sysimage, zero-alloc/`StaticArrays`) roda **<1 ms/passo** @333-1000 Hz; o driver NMPC roda **assíncrono** sobre modelo **bicicleta simplificado** (não o 14-DOF completo), com RTI (1 iteração SQP) + look-ahead. 14-DOF+NMPC síncrono <100 ms = inviável.
- **Os 50 s/volta NÃO são inerentes**, é o `QNDF` colapsando o passo em descontinuidade. Correção priorizada (esforço baixo × ganho alto):
  1. **Sysimage** (`PackageCompiler.jl`) com `ForwardDiff.Dual` no snoop + `cpu_target` fat-binary → TTFX 15 min → **<3 s**.
  2. **Actuator smoothing** (filtro 1ª ordem nos pedais) + `QNDF`→**`TRBDF2`** + `ShampineCollocationInit` + `linsolve=KLU` → **acaba o freeze de 50 s**.
  3. **Docker multiestágio** (slim + `JULIA_DEPOT_PATH` + chmod, −50%). **Batch = `EnsembleThreads` (CPU)**, NÃO GPU (branch-divergence do Pacejka mata o SIMD).
- **Driver híbrido:** RL treinado offline **sintoniza os pesos do NMPC** online (mantém as garantias físicas do NMPC + adaptação), casa com o AMPC/Tube-MPC do §3.

### 1.5 Arquitetura de Suspensão (Inspiração VI-CRT)

- **Gap Atual vs Indústria:** O nosso 14-DOF (Julia/MTK) muitas vezes pena com DAEs pesadas ao tentar resolver a cinemática da suspensão online.
- **Otimização (K&C Lookup):** Conforme benchmarking da arquitetura do VI-CarRealTime (VI-CRT), a estabilidade real-time é atingida substituindo a cinemática algébrica pura por **Lookup Tables (K&C)**. O deslocamento da roda e as forças aplicadas interpolam diretamente Camber, Toe, Track Width e forças anti-geometria (anti-dive/squat) via curvas estáticas (XML/JSON), reduzindo drasticamente o esforço do solver em runtime, sem perder precisão fenomênica.

---
