---
titulo: "Stage 3, NMPC Driver Plan (Track A: 102s → 94s honesto)"
data: "2026-07-14"
origem: "_arquivo/saru-physics-jl/docs/STAGE3-NMPC-DRIVER-PLAN.md"
status: "rascunho"
area: "dinamica_veicular"
---

# Stage 3, NMPC Driver Plan (Track A: 102s → 94s honesto)

> Plano de escopo (sem mudança de solver). Continuação da sessão 2026-06-30 (Track A convergiu).
> Ler junto com: memória `honest-14dof-lap-vs-qss`, `SPM.md`, e a seção "Controller hierarchy" de
> `saru-KB/20_vehicle_dynamics/PACEJKA_MF62_COMBINEDSLIP_BCDE.md`.

## 1. Contexto e meta

O 14-DOF converge honesto em **~102 s** (commits `6eb34a6` + `92805ac`), pneu dentro da elipse de
atrito (utilização ≤1,05). O gap **102→94 é linha de corrida / driver, NÃO grip** (util≈1,0 = o pneu
já tem grip de GT3; GT3 real roda Interlagos ~91-95 s). O driver atual, feedforward de curvatura +
P-controllers algébricos dentro do DAE, dirige **no limite mas não na linha ótima**, e over-dirige a
seção técnica (desliza). **Meta do Stage 3:** substituir esse driver por controle ótimo (NMPC) que
extraia o limite na linha ótima → fechar 94±1 **honestamente** (sem fake grip).

## 2. Ativos atuais

> ⚠️ **2026-07-10, os módulos `src/ai/*` NÃO estão no `develop`.** Foram removidos do `develop` em
> `890a2a2` e o scaffold completo (~2.3k linhas: `DriverMPC`, `DriverPredictor`, `GaussianGripEstimator`,
> `TubeGenerator`) foi **arquivado na tag `archive/phase3-scaffold-baf4536`** (decisão de 2026-07-10, > dossiê `saru-os/docs/plans/mvp-decisoes-research.md` §Decisão 4). O branch `feature/claude-phase3-scaffold`
> estava 36 commits à frente / 1 atrás do `develop`, sobre um `Transient14DOF.jl` que já divergiu 244 linhas
>, reaproveitar como base de merge é dívida crescente. **A Fase 3 reconstrói incremental** (padrão ETH/AMZ
> MPCC + AMZ fssim: núcleo enxuto e testável), sobre o 14-DOF atual, **depois** de fechar o 2.4 (channel
> validation, pré-req do GP/tube). Os itens abaixo descrevem o **design a preservar** (recuperável da tag),
> não código vivo no `develop`.

- **`src/ai/DriverMPC.jl`, MPC funcional (NÃO é stub):** horizonte recuado, predição por bicycle
  cinemático 3-DOF (estado `[X,Y,psi,v]`, controle `[delta, a]`), custo = cross-track + heading + vel +
  esforço/rate, L-BFGS com caixa (`Fminbox`, respeita `lb/ub` de δ∈[−0.5,0.5], a∈[−10,5]), AD-safe
  (`AutoForwardDiff`). API: `solve_mpc_step!(solver, current_state, target_traj[3×N], u0_guess)` →
  `([delta,a], seq)`. **Testado isoladamente** (`runtests.jl`), mas **não conectado** ao lap loop.
- **Driver atual no solver** (`Transient14DOF.jl`, eqs algébricas): `delta ~ clamp(wheelbase·κ − K_p_delta·(e_y+L_preview·e_psi), ±0.5)`, `throttle ~ f(v_target−vx)`, `brake ~ f(vx−v_target)`.
  Alvo vem do `run_qss_prepass` (perfil `v_target`, `gear`, linha = centerline do HDF5).

## 3. Problema arquitetural central

O MPC é um **otimizador iterativo** (L-BFGS), **não pode ser uma equação algébrica do MTK**. Logo
não dá pra colocar `solve_mpc_step!` dentro de `eqs`. Precisa de **co-simulação**: o DAE integra e,
em intervalos de controle, um **callback** chama o MPC e atualiza os inputs (δ, throttle, brake),
mantidos **constantes por partes** entre atualizações. Isso exige transformar `delta/throttle/brake`
de **leis algébricas (função do estado)** em **inputs (parâmetros) atualizados pelo callback**.

## 4. Abordagens

| # | Abordagem | Invasividade | Teto de pace | Veredito |
|---|---|---|---|---|
| **A** | **Outer-loop setpoint:** MPC ajusta o alvo (`v_target`/offset de linha) em intervalo grosso; P-law interno rastreia | Baixa | Limitado (gargalo = P-law no limite) | Passo intermediário barato |
| **B** | **NMPC in-loop (`PeriodicCallback`):** δ/throttle/brake viram inputs por-partes, atualizados a cada `dt` por `solve_mpc_step!` | Média-alta | Alto (NMPC online real) | **Recomendado** |
| **C** | **Colocação direta offline:** resolver o OCP de min-lap-time uma vez (14-DOF ou modelo reduzido), depois rastrear | Alta | Máximo (benchmark da literatura) | Oráculo futuro / validação |

**Recomendação: B** como caminho principal (NMPC online, usa o `DriverMPC` que já existe). **C** fica
como oráculo de referência depois (a literatura trata colocação direta como o benchmark de min-lap-time;
ver COMBINEDSLIP doc). **A** só se quiser um ganho rápido antes de B.

## 5. Milestones (rota B)

- **M1, Plumbing sem mudar física.** Extrair `delta/throttle/brake` das eqs algébricas → parâmetros do
  integrador, dirigidos por um `PeriodicCallback(dt_ctrl)` que **replica a lei feedforward+P atual**.
  Critério: lap inalterado (~102 s), suite verde. De-risca a fiação antes de meter o otimizador.
- **M2, Alimentador de trajetória-alvo.** Mapear `s_pos → próximos N pontos` da linha + `v_target` do
  prepass, no frame que o MPC usa. **Decisão de frame** (ver Riscos): reformular o MPC em curvilíneo
  (`s, e_y, e_psi`), alvo trivial `e_y=0`, OU adicionar estados globais `X,Y` ao solver.
- **M3, Trocar o corpo do callback por `solve_mpc_step!`.** Mapear `a → throttle/brake` (inverso do
  powertrain/freio), `delta → steer`. Warm-start (`u0` = solução anterior deslocada). Tunar `Q/R`,
  `N`, `dt_ctrl`. Medir lap + estabilidade + util por canal.
- **M4, Empurrar p/ 94 + validar.** Overlay de canais (util, slip, g-g), confirmar |F|≤μFz, lap→94±1.
  Aí **apertar o guardrail** (`runtests.jl`) de `96≤lap≤112` p/ `94±1` e re-travar.

## 6. Interfaces

- `MPCSolver(; horizon=N, dt=dt_ctrl, L_f=a, L_r=b)`, `L_f/L_r` da geometria do YAML (`lf_m`,`lr_m`).
- `current_state = [X, Y, psi, v]` lido do integrador. **O solver hoje NÃO tem `X,Y`** (rastreia
  curvilíneo `s_pos/e_y/e_psi`). Opções: (a) adicionar `D(X)=vx·cos(psi)−vy·sin(psi)`,
  `D(Y)=vx·sin(psi)+vy·cos(psi)` (2 estados baratos); (b) reformular o custo do MPC em curvilíneo.
- `target_traj[3×N] = [X;Y;v]` (ou `[s;e_y;v]` se curvilíneo) dos próximos N passos do prepass.
- Saída `[delta, a]`: `delta` → input de esterço; `a` → throttle (a>0, via inverso do mapa de torque
  na marcha/rpm atuais) ou brake (a<0, via `max_brake_torque`).

## 7. Riscos e mitigações

- **🔴 Custo de solve.** MPC L-BFGS por passo de controle × ~milhares de passos/volta → cada lap pode ir
  de ~50 s p/ minutos. Mitigar: `dt_ctrl` grosso (0.05-0.1 s), horizonte curto (N~10-20), **warm-start**
  agressivo, predição cinemática (barata, já é). Medir custo no M3 cedo.
- **🔴 Mismatch cinemático×dinâmico.** O MPC prediz com bicycle **cinemático** (sem slip/transferência
  de carga); a planta é 14-DOF no limite → predição otimista → MPC pode over-dirigir (mesmo problema do
  driver atual). **Este é o ponto crítico p/ chegar em 94 limpo.** Mitigar: de-rate no alvo de vel do
  MPC, OU **subir a predição p/ bicycle dinâmico com limite de atrito** (single-track não-linear). Sem
  isso, NMPC repete o over-drive.
- **🟠 Frames de coordenada.** Bicycle do MPC em `X,Y` global; solver em curvilíneo. Resolver no M2
  (reformular curvilíneo é mais limpo, alvo é `e_y=0` e `s` avança).
- **🟠 Mapa `a → throttle/brake`.** Inverter o powertrain (dado `a` desejado, achar throttle na marcha/
  rpm) e o freio. Não-trivial; testável isolado.
- **🟢 AD/callback.** Callback que chama otimizador quebra AD **através** do lap, mas o lap é sim
  forward (não precisa de AD através dele). O AD interno do MPC (`AutoForwardDiff` no custo) é isolado. OK.

## 8. Validação e guardrails

- QSS regressão **93,03 s** intacto (não tocar `Harness.jl`). Suite verde a cada milestone.
- Validar **canais, não só lap-time** (anti-padrão fake-grip): util≤~1,05, slip diant.≤~5°/tras. em
  faixa, g-g plausível, |F|≤μFz. Overlay vs referência quando houver telemetria real.
- Guardrail em `runtests.jl` só aperta p/ `94±1` **quando** o NMPC entregar 94 limpo com canais físicos.
- Mudança de lap ≥0,5 s → reportar + aprovar com Vitor antes de commitar (regra viva).

## 9. Pesquisa de apoio

- **COMBINEDSLIP doc, "Controller hierarchy" / "Practical recommendation":** NMPC p/ tracking online do
  transiente; colocação direta p/ o benchmark min-lap-time; pure-pursuit/Stanley só como baseline.
- **Refinamento doc, Exp 4:** limitar torque demandado ao envelope QSS (já feito via de-rate; NMPC faz
  isso nativamente por restrições).
- **g-g-v envelope:** gerar o envelope do próprio 14-DOF (não ponto-massa) p/ o alvo do MPC (COMBINEDSLIP
  "Achievable target speed"). Fecha o loop com o mismatch cinemático×dinâmico (Risco 2).
