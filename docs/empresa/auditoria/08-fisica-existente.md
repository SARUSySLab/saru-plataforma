# Física e simulação existente para o E-RF-09

Varredura só leitura, em 2026-09-13, de sete fontes arquivadas (`saru-physics-py`, `saru-physics-jl`, `saru-KB`, `saru-docs`, `saru-app`, `saru-research`, `dados_telemetria`) e do índice local do Drive. Nenhum clone foi alterado. Foco: Porsche 911 GT3 Cup, gerações 991.1, 991.2 e 992.1.

## 1. Resposta direta

O E-RF-09 pede quatro coisas: estimar parâmetros do veículo a partir de telemetria real, simular a volta com modelo de piloto, comparar contra o dado real, e fazer isso para o GT3 Cup. Nenhuma das quatro está pronta. Existem pedaços de cada uma, calibrados para o carro errado (992 GT3 R, categoria internacional, não o Cup brasileiro).

O que existe e funciona:

Solver QSS (quasi steady state) em Python, `_arquivo/saru-physics-py/src/saru_core/simulation/qss_solver.py` e `lap_time_solver.py`. 191 funções de teste em `tests/`, 180 passando, 6 puladas, 2 esperadas para falhar no último gate registrado (`_arquivo/saru-physics-py/docs/GAP-AUDIT-2026-06-28.md`). Calibração é regressão contra um número fixo, não contra realismo físico (`docs/vehicle_calibrations.md` usa essa palavra).

Modelo de pneu Pacejka Magic Formula, MF 5.2 em Python (`vehicle/tires.py`) e MF 6.2 em Julia (`saru-physics-jl/src/components/Tire.jl`, função `mf62_combined`). Roda nos dois solvers. Nenhum coeficiente vem de pneu real do Cup, só de estimativa de engenharia.

Otimização de traçado por mínima curvatura, `_arquivo/saru-physics-py/tracks/racing_line.py` (258 linhas, programação dinâmica).

Uma fixture de dado real já formatada: telemetria GT7 do 992 GT3 R em Interlagos, piloto Vitor, volta de 94,40 s, 5.664 amostras a 60 Hz (`_arquivo/saru-app/docs/calibration/gt7-992gt3r-interlagos-calibration.json`).

Um preset de parâmetros já escrito para o Cup 991 (991.1 e 991.2 juntos), com fonte citada: `_arquivo/saru-physics-py/src/saru_core/vehicle/parameters.py`, função `porsche_911_gt3_cup_991()`, linha 643.

O que existe só parcial ou só como documento:

Modelo transiente 14 DOF em Julia (`_arquivo/saru-physics-jl/src/simulation/Transient14DOF.jl`, 866 linhas). Converge, mas o repositório contradiz a si mesmo sobre o resultado (seção 3). Suspensão, freio e aero têm código real mas desconectado do solver principal.

Modelo de transferência de carga e freio térmico: só documento (`_arquivo/saru-app/docs/physics/load_transfer_optimumg.md`, `_arquivo/saru-KB/20_vehicle_dynamics/modules/04_2_6_modelo_t_rmico_de_freios_lumped_mass.md`), sem código encontrado nesta varredura.

Otimização de traçado por QP: só relatório (`_arquivo/saru-app/docs/research/relatorio_tecnico_racing_line_minima_curvatura.md`, 668 linhas), recomenda Julia com OSQP, sem código.

O que não existe:

Estimação de parâmetros a partir de telemetria. Não encontrado em nenhum dos sete repositórios. `_arquivo/saru-physics-py/telemetry/motec_importer.py` só lê CSV, não estima nada.

Modelo de piloto que decide comandos. O que roda em `simulation/driver_model.py` deriva throttle, freio e volante a partir de uma aceleração já resolvida pelo solver (método Segers 2014), não dirige o carro. Um modelo de piloto por NMPC foi desenhado (`_arquivo/saru-physics-jl/docs/STAGE3-NMPC-DRIVER-PLAN.md`) e chegou a ter código, `src/ai/DriverMPC.jl`, removido do branch principal em 2026-07-10 e preservado só na tag `archive/phase3-scaffold-baf4536`.

Qualquer parâmetro, YAML ou preset específico do 992.1 Cup. Tudo que existe com o rótulo "992" nos três repositórios de física é o GT3 R internacional, carro diferente do Cup 992.1.

Calibração automatizada contra telemetria real do Cup. A calibração que existe roda contra oráculo sintético (seção 2), não contra um arquivo `.pds` ou `.vbo` real de sessão.

O que reaproveitar de imediato: o QSS em Python e o catálogo Pacejka MF 5.2/6.2 são a base mais sólida, com teste e execução real. A estrutura `VehicleParams` de `parameters.py` já aceita um preset novo sem mudar código, só somando uma função `porsche_911_gt3_cup_992_1()` ao lado da que já existe para o 991. O traçado por programação dinâmica resolve a parte de otimização sem esperar o QP. A fixture GT7 mostra o formato que uma fixture de validação real precisa ter.

## 2. Tabela por componente

| Componente | Onde está | Linguagem | Estado | Testes | Última mudança | Fonte de validação | O que falta para o E-RF-09 |
|---|---|---|---|---|---|---|---|
| Estimação de parâmetros | não encontrado | | não existe | nenhum | | nenhuma | tudo: motor de engenharia reversa telemetria → parâmetros |
| Modelo de pneu (Pacejka) | `saru-physics-py/src/saru_core/vehicle/tires.py` (MF 5.2), `tires_transient.py` (segunda classe `PacejkaTire`, nome colide com a primeira), `saru-physics-jl/src/components/Tire.jl` (MF 6.2, `mf62_combined`) | Python e Julia | funciona nos dois solvers | dentro dos 191 `def test_` do Python; Julia coberto pelos 90 `@test` gerais de `runtests.jl`, sem teste isolado de pneu | Python: HEAD `a060e64`, 2026-07-18. Julia: 2026-07-15 (aplicação de k=-0,12) | nenhuma contra pneu real do Cup; coeficientes de engenharia (`gt3_992_seed.tir`) e pesquisa cruzada de load sensitivity na KB | dado de pneu real (TTC ou fornecedor) do slick Michelin do Cup; resolver a colisão de nome das duas classes `PacejkaTire` em Python |
| Modelo de veículo QSS | `saru-physics-py/src/saru_core/simulation/qss_solver.py`, `lap_time_solver.py` | Python | funciona, calibração é regressão contra número fixo, não realismo (`docs/vehicle_calibrations.md`) | 191 `def test_` no código; GAP-AUDIT 2026-06-28 coletou 188 testes regulares (180 passed, 6 skipped, 2 xfailed) e 3 de estresse isolados | 2026-07-18 (HEAD do repo); k=-0,12 aplicada em 2026-07-15 e 07-17 | `tests/test_qss_calibration.py` trava o 992 GT3 R em Interlagos em 86,7 a 87,1 s contra alvo real de 94,0 a 94,4 s | parâmetros e calibração para o Cup; fechar o intervalo de cerca de 7 s entre travado e real |
| Modelo transiente 3 DOF | `saru-physics-py/src/saru_core/dynamics/transient.py` | Python | parcial, cobre manobras isoladas (step steer, DLC, fishhook), não a volta completa | incluído nos 191, sem contagem isolada extraída nesta varredura | 2026-07-18 (repo-wide) | comparado contra Khalil 2018 em `saru-docs/docs/fisica/modelos.md`, roll gradient com erro de 5% | estender para volta completa, ou justificar por que 3 DOF não serve ao E-RF-09, que pede volta inteira |
| Modelo 14 DOF | `saru-physics-jl/src/simulation/Transient14DOF.jl` (866 linhas) | Julia, ModelingToolkit | parcial. Converge, número contestado (seção 3) | `test/runtests.jl`, 90 `@test` em 9 `@testset`, contra pista sintética `reference/interlagos.hdf5`; o teste que compara com 94,0 s está marcado `@test_broken` | último commit do repo 2026-07-18 (promoção de branch); último trabalho de física 2026-07-15 | nenhuma contra telemetria real; comparado só contra o QSS Python como oráculo | parâmetros do Cup; corrigir o teste marcado quebrado; suspensão, freio e aero têm código real mas órfão, só `Engine.torque_at` é chamado pelo solver |
| Modelo de piloto | `saru-physics-py/src/saru_core/simulation/driver_model.py` (deriva comandos pós-solução); `saru-physics-jl/src/ai/DriverMPC.jl` (removido do branch principal em 2026-07-10, na tag `archive/phase3-scaffold-baf4536`); plano em `docs/STAGE3-NMPC-DRIVER-PLAN.md`; diretriz de arquitetura em `saru-KB/20_vehicle_dynamics/modules/05` e `08` (AMPC, Tube-MPC, lei de esterço Stanley, NMPC em frame curvilíneo) | Python e Julia | não existe um modelo que decide o comando antes do resultado | nenhum teste de modelo de piloto ativo encontrado | `DriverMPC.jl` removido em 2026-07-10; plano NMPC de 2026-07-14 | nenhuma | implementar o NMPC do plano, ou reaproveitar o `DriverMPC.jl` da tag arquivada como ponto de partida |
| Otimização de traçado | `saru-physics-py/tracks/racing_line.py` (258 linhas, programação dinâmica, Casanova 2000 e Heilmeier 2019); `saru-app/docs/research/relatorio_tecnico_racing_line_minima_curvatura.md` (668 linhas, recomenda QP com OSQP em Julia) | Python implementado; Julia recomendado, não implementado | funciona em Python por DP; a versão recomendada não tem código | não extraído nesta varredura se `racing_line.py` tem teste próprio | relatório: 2026-08-11 (saru-app) | métodos da literatura (Casanova, Heilmeier, TUMFTM), não telemetria real do Cup | decidir entre DP e QP, e validar o traçado ótimo contra o traçado real de um piloto do Cup |
| Calibração contra dado real | `saru-physics-py/tests/test_qss_calibration.py` (contra oráculo sintético); `saru-app/docs/calibration/gt7-992gt3r-interlagos-calibration.json` (fixture simulada no simulador de jogo GT7, não telemetria de pista); `saru-research/.claude/rules/calibration-guardrails.md` (regra de aprovação para mudar o baseline) | Python, JSON, regra em markdown | parcial. Existe fixture simulada e regra de governança, mas a calibração automatizada roda contra oráculo sintético | `test_qss_calibration.py` trava valores fixos (ver linha QSS acima) | `calibration-guardrails.md`: 2026-06-29; fixture GT7: commit `chore: snapshot pre-audit`, 2026-06-15 | GT7 é simulador de jogo, não telemetria oficial de carro do campeonato | fixture com telemetria real de carro (não simulador) do Cup, ligada ao teste automatizado |
| Catálogo de parâmetros de veículo | `saru-physics-py/src/saru_core/vehicle/parameters.py` (presets Python) e `data/vehicles/*.yaml`; `saru-physics-jl/reference/vehicle_992_gt3_r.yaml`; `saru-KB/20_vehicle_dynamics/modules/10_8_par_metros_can_nicos_veiculares_e_pista.md`; `saru-docs/docs/fisica/validation-pack.md` (formato de fixture e canais) | Python, YAML, markdown | existe para o 992 GT3 R em 3 lugares com números diferentes (seção 3); existe para o Cup 991.1/991.2 em 1 lugar só | usado pelos testes de calibração acima | physics-py: 2026-07-18; physics-jl: 2026-07-15; KB: 2026-07-14 | mista: parte fact-checada (`gt3_factcheck_report.md`), parte estimativa de engenharia sem fonte | um catálogo único por geração do Cup (991.1, 991.2, 992.1), com fonte e status de verificação por parâmetro, no formato de `validation-pack.md` |

## 3. Parâmetros de veículo já registrados

### Porsche 911 GT3 R (992), carro internacional, não o Cup

| Parâmetro | Valor | Unidade | Fonte no documento | Verificado |
|---|---|---|---|---|
| Massa total | 1330 | kg | `saru-physics-py/parameters.py`, `porsche_911_gt3_r_992()`, docstring cita Porsche Motorsport technical data MY2023, FIA WEC, Endurance Brasil | não. Docstring já registra faixa "~1250 dry, ~1330 race-ready" |
| Massa total | 1330, piloto 80 | kg | `saru-physics-jl/reference/vehicle_992_gt3_r.yaml` | não |
| Massa | 1310 | kg | `saru-KB/20_vehicle_dynamics/modules/10_8_par_metros_can_nicos_veiculares_e_pista.md` | não, sem fonte citada no próprio documento |
| Massa base | 1250 a 1265 | kg | `saru-KB/20_vehicle_dynamics/research/Parâmetros Dinâmicos, Porsche 911 GT3 R (992, 2023).md`, chamado aqui de doc S1 | parcial, o próprio documento marca como faixa dependente de classificação BoP |
| Massa em trim de corrida | ≈1345 (1265 base + 80 piloto) | kg | mesmo doc S1 | não |
| Massa, homologação pública | 1250 | kg | `saru-KB/20_vehicle_dynamics/research/gt3_factcheck_report.md` | sim, ficha técnica oficial pública, sem distribuição por eixo |
| Massa, BoP LMGT3 em 2025-04-11 | 1336 | kg | `saru-KB/20_vehicle_dynamics/research/relatorio_14dof_notas.md` | sim, fonte é o próprio boletim de BoP |
| Entre-eixos | 2,507 | m | `parameters.py` e `vehicle_992_gt3_r.yaml` | não |
| Bitola frente / trás | 2,039 / 2,050 | m | `parameters.py` | não |
| lf / lr (yaml, corrigido) | 1,504 / 1,003 | m | `vehicle_992_gt3_r.yaml`, corrigido em 2026-07-15 depois de inversão detectada; a KB avisa que o doc S1 tem lf e lr trocados | não |
| Iz | estimativa, sem valor fechado | kg·m² | `vehicle_992_gt3_r.yaml` diz textualmente "estimativa"; `relatorio_14dof_notas.md` cita ~2450 sem fechar | não |
| Altura de CG | estimativa, faixa 0,34 a 0,46 | m | `vehicle_992_gt3_r.yaml` | não |
| Rigidez de curva frente / trás | 85000 / 100000 | N/rad | `parameters.py` e `vehicle_992_gt3_r.yaml` | não |
| Rigidez de curva (KB) | 221760 | N/rad | `saru-KB/20_vehicle_dynamics/modules/02_2_modelos_de_pneu_pacejka_mf.md`, calibração de referência GT3 | não, conflita com os 85000/100000 acima |
| Coeficiente de atrito (mu) | 2,50 | adimensional | `parameters.py`, comentário registra que foi calibrado para bater o oráculo de 94 s | não, o próprio comentário do código diz que é calibração, não medição |
| Pacejka B, C, D, E | 22,0 / 1,40 / 1,80 / 0,90 | adimensional | `parameters.py` e `vehicle_992_gt3_r.yaml` | não |
| Load sensitivity (k) | -0,12 | 1/N | `parameters.py`, cita pesquisa 2026-07-15 da KB, banda -0,10 a -0,15 | parcial, duas pesquisas independentes convergem no mesmo valor, sem dado de fornecedor |
| Potência | ~565 (421) | hp (kW) | `saru-KB/10_8` | não, sem fonte inline |
| Downforce a 250 km/h | ~1400 | kg | `saru-KB/10_8` | não, sem fonte inline; `gt3_factcheck_report.md` trata Cd 0,45-0,50 e Cl 1,5-2,0 como estimativa, não valor primário |
| Disco de freio | 390×36 | mm | citado em pesquisa da KB | não confirmado, segundo `gt3_factcheck_report.md` |
| Pastilha de freio | Pagid RSL29, atrito 0,41 a 0,44 | adimensional | `gt3_factcheck_report.md` | sim, fonte de fabricante |
| Pneu | Michelin 30/68-18 | polegada | `gt3_factcheck_report.md`, confirmado em guia oficial de 2022 | sim |

### Porsche 911 GT3 Cup 991 (991.1 e 991.2 juntos), único preset existente

| Parâmetro | Valor | Unidade | Fonte no documento | Verificado |
|---|---|---|---|---|
| Massa | 1250 (homologado mínimo ~1200, corrida ~1250 com piloto) | kg | `saru-physics-py/parameters.py`, `porsche_911_gt3_cup_991()`, linha 643, docstring cita Porsche Carrera Cup Brasil, Manual Técnico 991 Fase 1 e 2 (2021), e Porsche 911 GT3 Cup (991) Vehicle Description (IMSA/Porsche Motorsport) | não fact-checada nesta varredura, mas com fonte primária nomeada |
| Entre-eixos | 2,463 | m | mesma função | não |
| Bitola frente / trás | 1,545 / 1,530 (média 1,537) | m | mesma função | não |
| lf / lr | 1,08 / 1,38 | m | mesma função | não |
| Altura de CG | 0,46 | m | mesma função | não |
| Iz | 1500 | kg·m² | mesma função | não |
| Rigidez de curva frente / trás | 75000 / 90000 | N/rad | mesma função | não |
| Coeficiente de atrito (mu) | 1,55 | adimensional | mesma função | não |
| Pacejka B, C, D, E | 22,0 / 1,35 / 1,55 / 0,95 | adimensional | mesma função | não |
| Potência máxima | 338 (460) | kW (cv) a 7500 rpm | docstring da mesma função | não |
| Torque máximo | 440 | N·m a 6250 rpm | docstring | não |
| Motor | 3,8 L flat-6 (991.1) / 4,0 L flat-6 (991.2) | | docstring | não |
| Freio | 380×32 mm 6 pistões (frente) / 380×30 mm 4 pistões (trás) | mm | docstring | não |
| Pneu | Michelin slick 245/650-18 (frente), 305/660-18 (trás) | polegada | docstring | não |

Nenhum parâmetro específico do 992.1 Cup foi encontrado em nenhum dos três repositórios de física. O que existe com o nome "992" é sempre o GT3 R.

### Três conflitos de número, sem reconciliação registrada

Massa do GT3 R (992). Quatro valores circulam para o mesmo carro: 1250 kg (homologação pública confirmada, `gt3_factcheck_report.md`), 1310 kg (`saru-KB/10_8`, sem fonte), 1330 kg (presets Python e Julia, "race-ready com piloto e combustível") e ≈1345 kg (doc S1 da KB, 1265 base mais 80 kg de piloto). Nenhum documento explica a diferença entre eles nem diz qual usar.

Lap time do 14 DOF. Três números descrevem o "estado honesto" do mesmo solver, todos de julho de 2026: `saru-docs/docs/fisica/modelos.md` (2026-07-15) registra 100,7 s; `saru-KB/20_vehicle_dynamics/modules/13_11_auditoria...md` (auditoria de 2026-07) registra 109,48 s; o README mais antigo do próprio `saru-physics-jl` (2026-06-29) registrava 94,42 s "GREEN". Três documentos, três números, sem um só marcado como o vigente.

README contra CLAUDE.md do `saru-physics-jl`. Dentro do mesmo repositório, o `README.md` (2026-06-29) afirma "test suite GREEN 4/4" com o 14-DOF em 94,42 s contra alvo de 94,0 ± 1,0 s, usando `grip_cal 1.30`. O `CLAUDE.md` (2026-07-15, mais recente) corrige esse resultado para 109,48 s, chama isso de convergência "honesta", e registra que o valor de 94 s exigia fator de pneu não realista (memória interna do repositório citada como `honest-14dof-lap-vs-qss`). O README não foi atualizado para refletir a correção.

### O que precisa ser refeito por geração

991.1: preset existe, mas compartilhado com o 991.2 na mesma função. Falta separar o que muda entre as duas fases (motor 3,8 L contra 4,0 L, principalmente) e checar se rigidez de pneu e mu são realmente iguais entre as duas.

991.2: mesma situação do 991.1, preset comum. Falta o mesmo trabalho de separação.

992.1: nenhum preset. Precisa de ficha nova inteira (massa, geometria, pneu, freio, motor), a partir de manual técnico do Cup 992.1 (não do GT3 R), e fact-check no mesmo padrão de `gt3_factcheck_report.md`.

## 4. Dado real disponível por geração

Fonte: `_arquivo/dados_telemetria` (clone parcial, listado por `git ls-tree`, sem baixar blob) e o índice local do Drive (`~/.cache/rclone/drive-index.tsv`, sem montar o Drive).

| Geração | Arquivos de sessão real no `dados_telemetria` | Formato | Pista / evento |
|---|---|---|---|
| 991.1 | 1 arquivo de referência de engenharia (`Referencias/3.8 - 991.1/REF 3.8 - 22ET3.pds`). Nenhuma sessão de treino ou corrida além da referência | `.pds` (PI Toolbox) | referência interna, sem pista de sessão registrada no nome |
| 991.2 | 1 referência (`Referencias/4.0 - 991.2/REF 991.2.pds`) mais 2 onboards VBOX (`Onboards/991.2/Ref_40Rookie_23ET1_0001.vbo`, `Ref_40_23ET1.vbo`) | `.pds`, `.vbo` (VBOX ASCII) | etapa 1 de 2023 (`23ET1`) |
| 992 / 992.1 | 1 referência (`Referencias/992.1/REF 992.pds.zst`) mais 9 arquivos de shakedown de 2025-11 (um por piloto, `.pds`/`.pds.zst`) mais 4 arquivos de 2022 do carro #3 (3 `.vbo` de treino e corrida mais 1 `.xlsm`) mais 1 onboard (`Onboards/992/Ref_992_23ET1.vbo`). Total 15 arquivos de sessão real | `.pds`, `.pds.zst`, `.vbo`, `.xlsm` | shakedown 2025-11 (Interlagos, pelo calendário do repositório) e etapas de 2022 e 2023 |

O repositório inteiro sob `telemetria/porsche-cup/` soma 144 arquivos rastreados, a maior parte manuais em PDF (23), templates PI (6) e planilhas (6), não telemetria bruta. Manuais que cobrem as três gerações juntas: `Manuais/ENG210319_V4_DAG_Manual 991.1 E 991.2.pdf` (2021) e, só no índice do Drive, uma versão mais recente, `Docs/Dados_SSD_Windows/MANUAIS/ENG260410_V5_JOM_Manual 991.1 E 991.2.pdf` (2026-04-10). Apresentação e calibração específicas do 992, achadas só no `dados_telemetria`: `Manuais/ENG220308_V8_LUB_Apresentação 992.pdf` (2022-03-08) e `Manuais/ENG220422_LUB_V1_Calibração de Sensor de Volante 992.1.pdf`.

O índice do Drive tem 603 ocorrências de caminho contendo `Porsche_Cup`, a maior parte fora do que já está no `dados_telemetria`: a temporada 2026 inteira (`Trabalho/Porsche_Cup/2026/26ET07/`, telemetria, onboards em vídeo e planilha de race report, datado até 2026-09-08) e uma pasta `Dados_SSD_Windows/MANUAIS/` com manuais mais recentes que os do git, até `ENG260709` (2026-07-09, Algarve). Esse material não foi clonado para o `dados_telemetria` e é o dado mais atual disponível hoje.

O acervo Apuama de pneu (Fórmula SAE, não Cup) acrescenta método, não dado do carro certo. `Estudo/Apuama/Historico_SARU_KB/Apuama/TIRE/data/` tem arquivos `.mat` de ensaio TTC (Tire Test Consortium) de pneu Hoosier de Fórmula SAE (`B2356run17`, `run18`, `run51`, `run52`, e os `raw` correspondentes), acompanhados de scripts MATLAB de ajuste Pacejka MF 5.2 (`Projeto Trainee/Bill Cobb/ttc2.m`, `MF5.2 GUI/`). `Estudo/Apuama/OptimumTire2/` tem projetos OptimumTire2 com pneu Hoosier R20 ajustado (`.tir`, `.t2pro`, `.t2ti`). Nenhum desses arquivos é do pneu Michelin ou Pirelli do Cup. O que se aproveita é o método de ajuste de Pacejka a partir de ensaio real, não o coeficiente em si.

## 5. Documentos para migrar a `saru/docs/fisica/`

Ordem de leitura sugerida, do índice para o detalhe. Lista prioriza o que serve ao E-RF-09; o inventário completo de 53 documentos de física está em `_auditoria/02-inventario-docs-kb.tsv` e `_auditoria/03-inventario-app-fisica.tsv`.

| Ordem | Origem | Resumo em uma linha |
|---|---|---|
| 1 | `saru-KB/SARU_Fisica_e_Simulacao.md` | Índice mestre que aponta para os 13 módulos de física e dinâmica veicular da KB |
| 2 | `saru-docs/docs/fisica/index.md` | Página índice da seção de física do portal, com as três camadas do solver |
| 3 | `saru-docs/docs/fisica/modelos.md` | Destila a arquitetura 2-tier (QSS/3-DOF e 14-DOF), inclui o número de lap time hoje contestado |
| 4 | `saru-physics-py/docs/vehicle_model_theory.md` | Teoria do modelo de veículo, eixos ISO 8855, hierarquia 3/7/14 DOF |
| 5 | `saru-physics-py/docs/tire_physics.md` | Catálogo de coeficientes Pacejka MF 5.2 e MF-Swift usados no QSS |
| 6 | `saru-physics-py/docs/vehicle_calibrations.md` | Fichas de calibração do 992 GT3 R e do McLaren 720S GT3, marcadas como regressão, não realismo |
| 7 | `saru-physics-py/docs/track_formats.md` | Formatos de pista HDF5 (QSS) e OpenCRG (14-DOF) |
| 8 | `saru-KB/20_vehicle_dynamics/modules/02_2_modelos_de_pneu_pacejka_mf.md` | Especifica MF 5.2 e MF 6.2 nos dois solvers, com combined-slip e relaxamento transiente |
| 9 | `saru-KB/20_vehicle_dynamics/modules/10_8_par_metros_can_nicos_veiculares_e_pista.md` | Parâmetros canônicos de veículo GT3, revisar antes de portar porque tem número sem fonte |
| 10 | `saru-KB/20_vehicle_dynamics/research/gt3_factcheck_report.md` | Fact-check do 992 GT3 R, separa o que tem fonte primária do que é estimativa |
| 11 | `saru-KB/20_vehicle_dynamics/research/Parâmetros Dinâmicos, Porsche 911 GT3 R (992, 2023).md` | Relatório de parâmetros do 992 GT3 R com faixas por classificação BoP |
| 12 | `saru-KB/20_vehicle_dynamics/research/relatorio_14dof_notas.md` | Notas fechando lacunas do 14-DOF: combined-slip, momentos de inércia, envelope g-g-v |
| 13 | `saru-KB/20_vehicle_dynamics/research/Load sensitivity de pneus slick GT3...md` | Pesquisa do coeficiente k de sensibilidade de carga, cruzando Milliken, Pacejka, TTC e FSAE |
| 14 | `saru-KB/20_vehicle_dynamics/modules/04_2_6_modelo_t_rmico_de_freios_lumped_mass.md` | Modelo térmico lumped-mass de freio GT3, sem código associado encontrado |
| 15 | `saru-KB/20_vehicle_dynamics/modules/03_2_5_aerodin_mica_e_estabilidade.md` | Registra bug de sinal invertido no momento de arfagem aerodinâmico do 14-DOF |
| 16 | `saru-KB/20_vehicle_dynamics/modules/05_3_intelig_ncia_artificial_driver_model.md` | Diretriz do modelo de piloto: AMPC/Tube-MPC, rejeita rede neural pura, lei de esterço Stanley |
| 17 | `saru-KB/20_vehicle_dynamics/modules/08_6_integra_o_do_driver_model_optimal_lap_mpc.md` | Formula a integração do modelo de piloto via NMPC em frame curvilíneo |
| 18 | `saru-physics-jl/docs/STAGE3-NMPC-DRIVER-PLAN.md` | Plano do modelo de piloto por NMPC, não implementado no branch principal |
| 19 | `saru-physics-jl/docs/ARCHITECTURE.md` | Arquitetura do worker 14-DOF, contrato YAML e HDF5 até lap_time |
| 20 | `saru-physics-jl/docs/AUDIT-FINDINGS.md` | Achados comparando componente real contra stub no solver Julia |
| 21 | `saru-KB/20_vehicle_dynamics/modules/07_5_din_mica_veicular_e_refinamentos_cr_ticos_14_dof.md` | Correções físicas e numéricas do 14-DOF: transferência de carga, ARB, TCS/ABS, elipse de Kamm |
| 22 | `saru-docs/docs/fisica/gates.md` | Regras de gate para um claim físico entrar no produto |
| 23 | `saru-docs/docs/fisica/validation-pack.md` | Níveis de claim, matriz de canais canônicos, estrutura mínima de fixture |
| 24 | `saru-research/.claude/rules/calibration-guardrails.md` | Baseline oficial de calibração e regra de aprovação para mudar o número de referência |
| 25 | `saru-app/docs/physics/load_transfer_optimumg.md` | Modelo de transferência de carga em quatro rodas, baseado em seminário OptimumG |
| 26 | `saru-app/docs/calibration/gt7-992gt3r-interlagos-calibration.json` | Fixture real de telemetria (GT7), formato de referência para uma fixture de validação |
| 27 | `saru-app/docs/research/relatorio_tecnico_racing_line_minima_curvatura.md` | Relatório de traçado ótimo por QP de mínima curvatura, ainda sem código |

## 6. Perguntas que só Vitor responde

A massa do GT3 R (992) tem quatro valores registrados (1250, 1310, 1330, 1345 kg) sem reconciliação. Existe algum documento primário, ficha FIA ou boletim de BoP, que Vitor já tenha e resolva isso, ou a equipe assume um valor único e marca os outros como descartados?

O `DriverMPC.jl`, removido do branch principal do `saru-physics-jl` em 2026-07-10 e preservado só na tag `archive/phase3-scaffold-baf4536`, deve ser recuperado como ponto de partida do modelo de piloto do E-RF-09, ou o time reescreve do zero a partir do plano `STAGE3-NMPC-DRIVER-PLAN.md`?

A calibração do E-RF-09 usa telemetria real de carro do Cup desde o início, ou a fixture GT7 (`gt7-992gt3r-interlagos-calibration.json`) segue servindo de referência de desenvolvimento até haver acesso a um `.pds` ou `.vbo` real de sessão do Cup?

O 991.1 e o 991.2 entram no E-RF-09 com um preset só, como hoje em `parameters.py`, ou cada geração ganha ficha própria desde o início, já considerando a diferença de motor (3,8 L contra 4,0 L)?

O 14 DOF em Julia, parcial e com número contestado, entra no escopo do E-RF-09 agora, ou o requisito começa só com QSS e 3-DOF, que já rodam e têm teste, deixando o 14-DOF para uma fase seguinte?
