---
titulo: "Modelos e Solvers"
data: "2026-07-15"
origem: "_arquivo/saru-docs/docs/fisica/modelos.md"
status: "vigente"
area: "fisica"
---

# Modelos e Solvers

Este documento destila o estado dos modelos fisicos a partir da SARU Knowledge
Base ([MOC Fisica e Simulacao](https://github.com/SARUSySLab/saru-KB/blob/develop/SARU_Fisica_e_Simulacao.md)).
Formulacao matematica completa (Pacejka, transferencia de carga, metricas) vive
nos modulos da KB; aqui fica o recorte que produto e engenharia precisam
compartilhar. Claims seguem os [gates de validacao](gates.md).

## Arquitetura 2-tier (ratificada, ADR-0010)

| Tier | Repo | Modelo | Papel | Status |
|---|---|---|---|---|
| Sincrono | `saru-physics-py` | QSS + 3-DOF (causal, Python) | Sim Reference do MVP, batch de setup, regressao | QSS com baseline GREEN 93,03 s vs oraculo 94 s +/- 1 s (Interlagos); 3-DOF validado vs Khalil 2018 (roll gradient, -5%) |
| Assincrono | `saru-physics-jl` | 14-DOF acausal (ModelingToolkit, Julia) | Alta fidelidade transiente via worker Redis/BullMQ | Beta interno; convergencia honesta ~100,7 s em Interlagos sem fatores artificiais |

A alternativa "modelo unico servido por surrogate neural" (PINN/CTESN) foi
avaliada e **rejeitada** para dev solo: retreino a cada mudanca de parametro
paralisa o fluxo de setup, o modelo viola fisica fora do envelope de treino e o
pipeline custa 6 a 18 meses. Padrao da industria (F1 DIL, VI-grade, IPG):
solver rigido em runtime + lookup tables; IA apenas em subcomponente lento.

## Modelo de pneu

- MF 5.2 no QSS: combined slip por funcoes de peso. Limitacao conhecida: a
  elipse de atrito simples superestima forcas limite em 15 a 25%.
- MF 6.2 no 14-DOF: ingere `.tir` reais; corrige o acoplamento combined
  slip e aplica sensibilidade de carga nao linear. P&D atual: relaxation
  length e decaimento termico acoplados ao solver acausal.
- Load sensitivity: implementada nos dois solvers Julia (fator `k` neutro
  aguardando tuning por telemetria). O QSS Python ainda nao tem o espelho
  dessa correcao; isso bloqueia calibracao definitiva cross-solver.

## Estado do 14-DOF

- Fatores artificiais de correcao (`grip_cal`, `torque_cal`) foram **removidos**;
  o atrito vem do YAML do veiculo (slicks com Pacejka D ~1,8).
- Estabilizacao numerica em condicao extrema usa TCS ativo, mitigacao de ABS no
  driver model, projecao de elipse de Kamm e piso de atrito cinetico.
- Solver: migracao de `QNDF` para `TRBDF2`/`Rodas5P` com Jacobianos esparsos e
  sysimage elimina o congelamento historico de ~50 s por volta.
- Status de claim: **beta interno** ate worker, CI, canais e runtime serem
  reproduziveis (regra dos gates).

## Termico

- Freios (Python): modo endurance com balanco termico estilo Limpert
  operando na faixa de ~646 C, engajando brake fade; identidade de qualificacao
  preservada quando frio.
- Pneus (Julia, P&D): 3 camadas termicas com decaimento de aderencia por
  temperatura, roadmap, nao claim.

## Parametros canonicos

| Item | Valor de referencia |
|---|---|
| Porsche 992 GT3 R | 1310 kg, ~565 hp, downforce ~1400 kg @ 250 km/h |
| McLaren 720S GT3 | 1300 kg, ~500 hp, downforce ~1300 kg @ 250 km/h |
| Pista | Extraida via OSM com elevacao interpolada -> HDF5 continuo (curvatura, banking, gradiente) |
| Superficie fina | OpenCRG apenas para simulacao vertical extrema; DEM bruto (~30 m) nao serve para geometria fina |

## Roadmap numerico (ordem de prioridade)

1. Sysimage + `TRBDF2` + actuator smoothing: TTFX < 3 s e fim do freeze.
2. Lookup tables K&C (padrao VI-CarRealTime) no lugar da cinematica algebrica
   online da suspensao.
3. Geometria de pista ASAM OpenDRIVE/OpenCRG para o 14-DOF (HDF5 segue
   suficiente para QSS 2D).
4. Export da planta 14-DOF para MuJoCo/CUDA (batch massivo em GPU com fonte
   unica de veiculo).
5. Driver model: NMPC assincrono sobre modelo bicicleta (nao o 14-DOF
   completo), com RL sintonizando pesos offline.

## Onde aprofundar

- [Paradigmas de simulacao](https://github.com/SARUSySLab/saru-KB/blob/develop/20_vehicle_dynamics/modules/01_1_paradigmas_de_simula_o_f_sica.md)
- [Modelos de pneu + formulacao](https://github.com/SARUSySLab/saru-KB/blob/develop/20_vehicle_dynamics/modules/02_2_modelos_de_pneu_pacejka_mf.md)
- [14-DOF: refinamentos e convergencia](https://github.com/SARUSySLab/saru-KB/blob/develop/20_vehicle_dynamics/modules/07_5_din_mica_veicular_e_refinamentos_cr_ticos_14_dof.md)
- [Metricas de analise (telemetria e tracado)](https://github.com/SARUSySLab/saru-KB/blob/develop/20_vehicle_dynamics/modules/12_10_m_tricas_de_an_lise_telemetria_tra_ado.md)
- [Estado dos repositorios de fisica](https://github.com/SARUSySLab/saru-KB/blob/develop/20_vehicle_dynamics/modules/13_11_auditoria_de_reposit_rios_e_estado_atual_atualiza_o_2026_07.md)
