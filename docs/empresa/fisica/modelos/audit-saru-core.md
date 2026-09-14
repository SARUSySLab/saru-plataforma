---
titulo: "Prompt, Auditoria do `saru-core` (física)"
data: "2026-08-13"
origem: "_arquivo/saru-app/docs/prompts/audit-saru-core.md"
status: "vigente"
area: "fisica (futuro repo)"
---

# Prompt, Auditoria do `saru-core` (física)

> Cole no Claude Code dentro do repo `saru-core`. Read-only até o relatório final.

---

Atue como engenheiro de dinâmica veicular sênior auditando a lib `saru-core` (Python, solver
QSS de lap-time + 3-DOF transiente). **Não altere código nesta sessão**, a entrega é um
relatório em `docs/reports/2026-07-auditoria.md` deste repo.

## Contexto de produto (decidido no saru-app, 2026-07)

- Plataforma focada em **track day no Brasil** (motorsport secundário), pistas-alvo:
  **Interlagos (4.309 m, recape 2024 com ondulações)**, **Brasília (novo traçado 11/2025:
  5.384 m, 16 curvas, 6 configurações, ~1.000-1.100 m de altitude)** e **Goiânia (3.835 m,
  asfalto sendo refeito jul-out/2026, ~730-750 m)**.
- Veículos em **3 tiers**: S = populares de rua (Onix/HB20/Up!, FWD, pneu de rua TW200+,
  ajuste só de pressão/combustível/peso do piloto), P = esportivos (Golf GTI, 911 Carrera,
  ajustes parciais), R = competição (GT3 Cup/R, o que já existe). Fidelidade declarada por
  tier ("estimativa" no S, "calibrado vs oracle" no R).
- Condição de simulação prioritária: **volta ideal em condição de track day**, pneu de rua,
  pista sem borracha de slick (grip ~0,90-0,95 da condição de corrida), temperatura da tarde,
  efeito de altitude na potência (NA −8/−12%, turbo compensa parcialmente).
- O `saru-app` precisa ligar `lts_setups` (compound, fuel %, asa, bias, altura, preload) ao
  run do solver, hoje o painel de setup é decorativo lá.

## O que auditar (nesta ordem)

1. **Mapa da estrutura** (1 página): módulos, entrypoints, o que o solver QSS consome
   (`VehicleParams` / `SimulationConfig` / `CircuitData`), suíte de testes e o que o oracle
   de calibração (`test_qss_calibration`) trava.
2. **Costura com o engine** (`saru-app/services/telemetry-api/.../lapsim_service.py` importa
   `saru_core.vehicle.parameters`, `tracks.generator.load_bundled_track`,
   `generate_br_tracks.build_interlagos_real`): liste **todos os campos de setup que o core
   consegue receber por run** hoje (bias? pressão? asa? altura? combustível?) e o custo de
   expor cada um sem quebrar a calibração. Isso responde o Gap nº 1 do LTS.
3. **Tier S, o que falta para simular um carro de rua popular?** Cheque honestamente:
   modelo de pneu (Pacejka atual serve p/ pneu de rua TW200+? existe preset de pneu de rua?),
   diferencial aberto/FWD, curva de motor de rua (dado de ficha técnica basta?), arrasto/área
   frontal, freio sem ABS-race. Para cada lacuna: esforço (B/M/A) e dado mínimo necessário.
4. **Ambiente**: o solver modela densidade do ar / altitude / temperatura (potência E
   arrasto/downforce)? Existe knob de grip global de pista (superfície verde × emborrachada ×
   TD)? Se não: onde entraria com menor cirurgia.
5. **Pistas**: qual o pipeline real de pista hoje (TUM/OSM/HDF5)? O que é preciso para
   construir **Brasília novo (5.384 m, traçado de 2025, não o histórico!)** e **Goiânia
   (3.835 m, 3 configurações)** com perfil de elevação? Existe fonte de centerline confiável
   ou precisamos gravar GPS in-loco (nossa telemetria SA pode fornecer)?
6. **Higiene**: testes quebrados/lentos, TODOs críticos, deps desatualizadas, docs internas
   divergindo do código (ex.: `vehicle_calibrations.md` vs presets reais).

## Formato do relatório

- Sumário executivo (≤10 linhas), depois seções 1-6.
- Cada gap com: evidência (arquivo:linha), esforço B/M/A, risco de quebrar o oracle,
  pré-requisitos de dados.
- Final: **plano incremental em PRs pequenos** (ordem, cada PR com critério de aceite e
  teste que o protege) para: (a) expor setup no run; (b) knob de grip/ambiente; (c) preset
  Tier S nº 1; (d) pista de Brasília. Nada de big-bang.
