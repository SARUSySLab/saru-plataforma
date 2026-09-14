# Linguagem e arquitetura do núcleo de simulação veicular (E-RF-09)

Pesquisa de apoio à decisão de arquitetura do núcleo de simulação da SARU, requisito E-RF-09
(2026-09-13): estimar parâmetros do Porsche 911 GT3 Cup a partir de telemetria real e rodar uma
simulação de volta comparável, com modelo de piloto, usando os modelos quase-estático (QSS),
transiente 3 a 14 graus de liberdade (GDL) e pneu Pacejka Magic Formula.

## Recomendação

Manter duas linguagens principais no núcleo, preservando a extensão pontual em C++. Python continua a camada de orquestração, dados e o solver quase-estático (QSS) de varredura de setup. Julia continua o solver transiente de 14 GDL de alta fidelidade, como worker assíncrono, sem ponte em processo com Python. A cinemática de suspensão existente em C++ via pybind11 é mantida como extensão compilada. Não há caso para reescrever o núcleo inteiro em C++: as bibliotecas C++ "estilo MATLAB" (Armadillo, Eigen, Blaze, xtensor) não têm ODE nem otimização embutidas (seção 2), e teriam que ser combinadas com Boost.odeint e CasADi de qualquer forma, sem ganho sobre o que Julia já entrega pronto (DifferentialEquations.jl, Optimization.jl) com uma linguagem mais perto de Python.

Camadas:

| Camada | Linguagem | O que faz | Estado |
|---|---|---|---|
| Dados de veículo (presets, pneu, aero, motor) | Python | Parâmetros do Porsche 991/992 por geração | 991 existe (`saru-core`, fonte manual Carrera Cup 2021); 992.1 falta |
| QSS lap time (varredura de setup) | Python | Solver de duas passadas, `saru-core` | Existe, em produção |
| Suspensão (corner, cinemática) | C++ via pybind11 | Solver de suspensão, `ext/suspension_cpp` | Existe, mantido |
| Handling transiente 3-DOF | Python | Bicicleta + rolagem, manobras SD | Existe, validado contra Khalil 2018 (roll gradient) |
| Transiente 14-DOF alta fidelidade | Julia (ModelingToolkit + DifferentialEquations.jl) | Corpo 6-DOF + 4 rodas + powertrain, worker assíncrono | Existe (`saru-core-jl`), com fatores de calibração não físicos (`grip_cal`, `torque_cal`) ainda a remover |
| Modelo de piloto | Julia | Seguidor de trajetória e otimizador de comandos (NMPC) | Não existe, planejado (STAGE3-NMPC-DRIVER-PLAN.md) |
| Estimação de parâmetros (E-RF-09) | Python (RLS/EKF) sobre canais do logger | Massa e CdA agregado a partir da telemetria real | Não existe, escopo abaixo |
| Integração | `saru-os` (FastAPI) | Chama `saru-core` em processo (submodule); chama `saru-core-jl` fora de processo, fila Redis | Já é o desenho documentado nos dois `CLAUDE.md` |

Critério objetivo de decisão de linguagem por camada: primeiro medir o throughput atual do QSS em
`saru-core` (simulações por minuto). Se esse número já cobre a varredura de setup que o produto
promete (algumas centenas de simulações por sessão em poucos minutos), não mexer na linguagem
dessa camada. Se não cobrir, a ordem de tentativa é Numba no laço quente do QSS (continua Python,
sem custo de empacotamento novo), depois vetorização com JAX, e só então reescrita em Julia ou C++
se nenhuma das duas anteriores fechar a meta. Reescrever o QSS em Julia só compensa se ele passar
a rodar dentro do mesmo processo Julia de longa duração que já serve o 14-DOF; hoje não há essa
necessidade. Para o 14-DOF a decisão é por fidelidade, não por throughput: fica em Julia
independente do número de simulações por minuto, porque roda como worker de fila que absorve o
custo de aquecimento (JIT) uma vez por processo, não uma vez por chamada (seção 1).

Escopo real do E-RF-09, dado o logger de um carro cliente de Porsche Cup (velocidade de roda, RPM,
marcha, throttle/freio, ax/ay do IMU do logger, GPS, sem célula de carga e sem sensor de força de
pneu): é viável estimar massa (erro documentado de 1 a 5% na literatura) e arrasto aerodinâmico
agregado (CdA, via coastdown SAE J1263) a partir da telemetria real. Não é viável estimar
coeficientes completos da Pacejka nem separar sustentação (Cl) de arrasto (Cd) nem obter balanço
aerodinâmico só com esses canais (seção 5). A Porsche também não publica distribuição de peso nem
coeficiente aerodinâmico do GT3 Cup em nenhuma geração (seção 6). Consequência prática: o núcleo
deve tratar pneu completo e aero como parâmetro de preset (da equipe, de manual, ou de literatura),
e usar a telemetria só para ajustar massa e CdA, mais rigidez de curva por eixo com incerteza alta
via EKF sobre modelo de bicicleta. Declarar isso explicitamente na saída do E-RF-09, não apresentar
como medição o que é suposição herdada de preset. Essa limitação técnica restringe o que a telemetria
isolada consegue calibrar sem ensaio de bancada ou instrumentação dedicada; o requisito E-RF-09 e o
critério E-CT-10 devem explicitar que pneu e aero partem de presets canônicos e que a calibração por
telemetria atua sobre massa, CdA e rigidez de curva equivalente.

Vale continuar de onde os dois repositórios pararam, com dois pré-requisitos antes de tratar
E-RF-09 como pronto. Em `saru-core` (Python, QSS): completar o preset do 992.1 com os dados
levantados na seção 6, marcando "não encontrado" o que a Porsche não publica (distribuição de peso,
aerodinâmica numérica), em vez de estimar sem fonte. Em `saru-core-jl` (Julia, 14-DOF): o próprio
`CLAUDE.md` do repositório já registra que a convergência atual depende de dois fatores de
calibração sem base física (`grip_cal=1.30`, `torque_cal=1.15`); esses fatores precisam sair antes
de usar o 14-DOF para reconstruir comandos de piloto reais, porque hoje ele ainda é ajuste de tempo
de volta, não física validada por canal. O modelo de piloto (driver model) ainda não existe nesse
repositório e é o item que falta para o E-RF-09 rodar de ponta a ponta; as bases abertas mais
maduras para essa peça são `alexliniger/MPCC` (Apache-2.0, MPC de contorno sobre bicicleta com
Magic Formula, testado em Formula Student real) e `bzarr/TUM-CONTROL` (LGPL-3.0, NMPC com
single-track e Pacejka em CasADi), detalhadas na seção 4.

Teste contra o acervo: o padrão já existe em `saru-core` (`validation/khalil2018_roll_validation.py`)
e é citado como meta em `saru-core-jl` ("validar canais, não só o número de lap time"). Estender
esse mesmo padrão de harness para o acervo real da Porsche Cup Brasil (PI Toolbox e MoTeC): rodar o
14-DOF com o preset da geração certa e os parâmetros estimados (massa, CdA) contra uma volta real,
comparar canal a canal (velocidade, ax, ay, slip, marcha, RPM), não só o tempo de volta agregado.

## 1. Julia contra C++ contra Python para dinâmica veicular

| Critério | Julia | C++ | Python (NumPy/SciPy + Numba/JAX) |
|---|---|---|---|
| Desempenho bruto | Comparável a C no benchmark oficial, que exclui compilação [26]; SciMLBenchmarks mostra Rodas4/Rodas5 rápidos no problema stiff ROBER, CVODE_BDF falha em tolerância alta no mesmo teste [27] | Referência de comparação nos benchmarks acima | Numba: 0,33 s na primeira chamada, 6,68 microssegundos nas seguintes no exemplo oficial [40]; comparação direta Julia vs Boost.odeint não encontrada em fonte aberta |
| Latência de primeira execução | Julia 1.9 com pkgimages reduziu o carregamento de `ModelingToolkit.jl` de 73,53 s para 4,81 s, e de `DataFrames.jl` de 17,39 s para 0,38 s, ao custo de 10 a 50% a mais de tempo de precompilação [28]; relato de 2021, anterior a essa melhoria, descrevia o problema como maior [29] | Não se aplica (binário compilado antes da distribuição) | Numba tem custo de JIT na primeira chamada (0,33 s no exemplo oficial) [40]; JAX com `diffrax` mostrou 23,97 s de compilação contra 2,56 s do `odeint` nativo do JAX num caso relatado por usuário, não benchmark oficial [42] |
| ODE/DAE | `DifferentialEquations.jl` cobre stiff e DAE, com `Sundials.jl` como wrapper de CVODE/IDA | `CasADi` resolve DAE semi-explícita via CVodes/IDAS com diferenciação automática forward e adjoint [30]; `Boost.odeint` só resolve ODE, sem DAE | SciPy `solve_ivp` cobre apenas ODE explícitas (sem suporte nativo a DAE, que exige bibliotecas como CasADi ou Assimulo); sem verificação de paridade direta com Julia neste levantamento |
| Otimização e estimação | `JuMP.jl` para problema declarativo estruturado, `Optimization.jl` para código imperativo [31] | `NLopt` com bindings C, C++, Python e Julia, otimização local e global [32]; Ceres Solver não confirmado nesta pesquisa (falha de conexão) | SciPy `optimize`, mesma cobertura de mínimos quadrados não linear que a SARU já usa |
| Chamar de Python | `PythonCall.jl`/`juliacall`: overhead de 1,1x a 2,4x sobre Python puro (680 microssegundos contra 280, ou 300 com `pydel!`); `PyCall` mais antigo tem overhead de 5,4x [33] | `nanobind` cerca de 3x mais rápido que `pybind11` em chamada simples, até 10x com objetos complexos, compila até 4x mais rápido, gera binário 3 a 5x menor [34] | Nativo, sem custo de fronteira |
| Empacotamento sem toolchain no cliente | `PackageCompiler.jl` gera app com runtime Julia embutido, mas a sysimage não é realocável entre caminhos de instalação [35] | Binário estático compilado é a forma mais simples de distribuir, sem dependência de linguagem de script | `cibuildwheel` gera wheels para Linux, macOS e Windows já com as dependências nativas, instala com `pip` sem toolchain [36] |
| Programadores disponíveis | Stack Overflow 2024: 1,1% dos respondentes usam Julia; TIOBE setembro 2026: 21ª posição, 0,74% [37][38]; Octoverse 2024: fora do top 10 de linguagens do GitHub [39] | Stack Overflow 2024: 23%; TIOBE setembro 2026: 3ª posição, 8,67% [37][38] | Stack Overflow 2024: 51%, a mais usada; TIOBE setembro 2026: 1ª posição, 17,76% [37][38] |
| Disponibilidade no Brasil | Não confirmado nesta pesquisa, sem fonte aberta com corte por país | Não confirmado | Não confirmado |
| Risco de manutenção para time de 2 pessoas | Sem fonte que quantifique risco para equipe pequena; um relato de usuário de 2021 descreve pacotes jovens do ecossistema quebrando com mais frequência e regressão de desempenho de até 100x sem violar API pública [29] | Ecossistema maduro, risco concentrado em complexidade de build e gestão manual de memória | Ecossistema mais maduro e com mais gente contratável; risco é o desempenho já conhecido do time |

Sobre o produto rodar local no box do usuário: como o `saru-os` já empacota o engine com a
toolchain C++ via submodule e Docker (conforme `saru-core/CLAUDE.md`), o mesmo caminho de imagem
Docker resolve a distribuição do worker Julia sem exigir `PackageCompiler.jl` nem instalação de
Julia pelo usuário final; isso já está coberto pelo desenho atual, não é um problema novo a
resolver.

## 2. "MATLAB em C++ open source"

| Biblioteca | Versão | Licença | Cobre | Não cobre |
|---|---|---|---|---|
| Armadillo | 15.6 | Apache 2.0 desde a 7.800 | Álgebra densa e esparsa, decomposições, FFT, interpolação, k-means | ODE, otimização não linear, gráfico [51] |
| Eigen | 5.0.1 (2025-11-08) | MPL2, header-only, C++14 | Álgebra linear e geometria | ODE, gráfico; Levenberg-Marquardt só no módulo "unsupported", não oficial [52] |
| Blaze | 3.8 (2020, sem release desde então) | BSD | Álgebra com BLAS/LAPACK | ODE, otimização, gráfico; projeto sem atividade recente |
| xtensor | 0.27.1 (2025-09-19) | BSD-3 | Broadcasting estilo NumPy, leitura CSV/NPY | ODE; álgebra linear só via `xtensor-blas`, complemento separado |

Nenhuma das quatro tem ODE, otimização não linear ou gráfico embutido. Um núcleo em C++ nesse
estilo exigiria compor Armadillo ou Eigen com `Boost.odeint` (BSL 1.0, Runge-Kutta 4, Dormand-Prince,
Rosenbrock) para ODE, `CasADi` (LGPL-3.0, diferenciação automática, IPOPT, SUNDIALS, roda como C++
autônomo) para otimização, e `matplotlib-cpp` (MIT) para gráfico, que por sua vez exige Python e
NumPy disponíveis no build. Isso é mais peças para integrar manualmente do que o pacote que Julia
já entrega coeso.

MATLAB Coder é pago (licença MathWorks), gera C e C++ royalty-free a partir de código MATLAB, mas
não cobre `try`/`catch`, GPU, Java, `containers.Map`, tall arrays nem funções de importação de
arquivo. Simulink Coder também é pago, exige MATLAB e Simulink instalados, e a geração para
produção de fato passa pelo Embedded Coder, outro produto pago. GNU Octave não tem gerador de C++
oficial da própria comunidade Octave; existe um pacote de terceiros chamado `coder` (Octave Forge,
licença AGPL, versão 1.11.1) que gera um módulo `.oct` ainda dependente do runtime do Octave, com
ganho de desempenho de 3 a 4 vezes sobre o interpretado, não um binário independente. Uma
ferramenta comercial, o emmtrix Code Generator, converte MATLAB e Octave para C89 até C++17 sem
suporte a orientação a objeto. Não foi encontrado nenhum conversor aberto e maduro de Simulink para
C++.

## 3. Referência de mercado

| Produto | Modelo | Plataforma | Tempo real | Preço público |
|---|---|---|---|---|
| VI-grade VI-CarRealTime | 14 GDL (6 do chassi mais 2 por roda), gerado automaticamente a partir de Adams/Car ou ensaio K&C; pneu Pacejka, MF-Tyre, MF-Swift, FTire | Código ANSI C, integração Simulink via S-Function | Faster than real time; HIL em dSPACE, NI, Concurrent, xPC | Não [16][17][18] |
| Canopy Simulations | Modelo totalmente dinâmico em nuvem, otimização de trajetória por colocação, 200 voltas em paralelo em 25 minutos | Nuvem, assinatura por nível | Não é o foco (é offline, em lote) | Não [19] |
| ChassisSim | Multicorpo genérico, mesmo motor de física para lap time e driver-in-the-loop | PC, Cloud, Online Sim | Sim, no modo driver-in-the-loop | Online Sim: US$ 100 por 150 simulações, US$ 5 por simulação extra [20] |
| OptimumLap | Ponto de massa quase-estático, precisão declarada até 10% | Planilha | Não | Gratuito [21] |
| OptimumDynamics | Transiente, hoje legacy sem suporte ativo | Aplicativo dedicado | Não confirmado | US$ 295 por ano na edição estudantil [22] |
| Dymola + Modelica (Vehicle Dynamics Library) | Topologias de suspensão prontas (McPherson, duplo A, multilink, eixo de viga), corpos flexíveis, benchmark de 72 GDL em tempo real | Modelica | Sim, no benchmark citado | Licença perpétua ou leasing; preço da biblioteca não público [23][24] |
| IPG CarMaker | Foco ADAS e condução autônoma | Variantes HIL real-time e Office | Sim, na variante HIL | Não [25] |

O que a SARU não precisa replicar desses produtos: GUI multiusuário em nuvem (Canopy, ChassisSim
Cloud), certificação e integração HIL com hardware de bancada (VI-CRT, CarMaker), e biblioteca
comercial de topologias de suspensão genéricas (Modelica VDL), porque o GT3 Cup é um carro único
com suspensão já conhecida da equipe. O que é relevante para copiar como prática, não como produto:
usar formato de pneu Pacejka como padrão mínimo de entrada (como o VI-CRT aceita MF-Tyre/MF-Swift),
e gerar um modelo reduzido a partir de dado de ensaio quando disponível, em vez de multicorpo full
vehicle completo. O que o VI-CRT faz que um 14-DOF próprio tipicamente não faz, segundo a
documentação do próprio fabricante: derivar automaticamente o modelo reduzido a partir de um modelo
Adams/Car completo ou de ensaio K&C de bancada, e rodar em hardware-in-the-loop com garantia de
passo de tempo determinístico para bancada física. Nenhuma dessas duas coisas é necessária para o
uso da SARU hoje, que não tem bancada HIL nem modelo Adams de referência.

## 4. Projetos abertos de referência

| Projeto | Linguagem | Licença | Último commit | O que implementa | Uso |
|---|---|---|---|---|---|
| TUMFTM/laptime-simulation | Python | LGPL-3.0 | 2026-04-13 | QSS ponto de massa, artigo publicado | Base para arquitetura QSS [1] |
| mc12027/OpenLAP-Lap-Time-Simulator | MATLAB | GPL-3.0 | 2022-09-24 | OpenVEHICLE/OpenTRACK/OpenDRAG/OpenLAP, referência acadêmica mais citada do gênero | Base de arquitetura, não de código direto [7] |
| juanmanzanero/fastest-lap | C++ com API Python | MIT | 2023-08-16 | Transiente 3-DOF carro e 6-DOF kart | Base para o lado transiente, com custo de ler C++ [5] |
| dstrassera/OpenLapSim | Python | GPL-3.0 | 2023-09-12 | Steady state | Leitura [2] |
| drypatrick/OpenLAP-Lap-Time-Simulator-Python | Python | GPL-3.0 | 2022 | Porte do OpenLAP | Leitura [4] |
| RoseGPE/RoseLap | Python | Sem licença | 2018 | QSS | Leitura, abandonado [3] |
| projectchrono/chrono (Chrono::Vehicle) | C++ | BSD-3 | 2026-09-12 | Multicorpo, pneus Pacejka 89/2002, TMeasy, Fiala; veículos militares e utilitários | Leitura de arquitetura multicorpo, não base direta (sem carro de corrida) [9][10][11] |
| bzarr/TUM-CONTROL | C++/CasADi | LGPL-3.0 | 2026-07-23 | NMPC com modelo de bicicleta e Pacejka, validado em veículo real | Base para modelo de piloto por otimização [13] |
| alexliniger/MPCC | C++/MATLAB | Apache-2.0 | 2026-04-25 | Model Predictive Contouring Control, bicicleta com Magic Formula, testado em Formula Student real | Base mais madura de piloto por MPC [14] |
| mathworks/vehicle-pure-pursuit | Simulink | Licença MathWorks | 2020 | Pure pursuit (seguidor de trajetória geométrico) | Especificação de algoritmo, não código a copiar [12] |
| urosolia/RacingLMPC | Python | Sem licença | 2020 | Learning MPC de corrida | Leitura [15] |

Em Julia, não foi encontrado nenhum projeto mantido de lap time ou dinâmica veicular de
competição. `sisl/AutomotiveDrivingModels.jl` e o sucessor `AutomotiveSimulator.jl` existem, mas
tratam tráfego 2D para condução autônoma, sem modelo de pneu, e o último push é de 2020 e 2022
respectivamente [8]. Esse é um nicho pouco coberto no ecossistema Julia hoje, o que reforça a
recomendação de manter a física no `saru-core-jl` próprio em vez de esperar por uma base externa.
Trabalhos de universidades como TU Delft e Politecnico di Milano sobre modelo de piloto aparecem
como artigo publicado, sem repositório de código aberto correspondente encontrado.

## 5. Estimação de parâmetros a partir de telemetria

Massa: mínimos quadrados recursivos (RLS) com fator de esquecimento sobre a equação de movimento
longitudinal, `M dv/dt = Te/rg − Ffb − Faero − Fgrade`, método de Vahidi, Stefanopoulou e Peng,
publicado em Vehicle System Dynamics em 2004, com erro dentro de 5% quando há excitação persistente
de aceleração [43]. Um trabalho híbrido mais recente, combinando RLS com fator de esquecimento e
filtro de Kalman estendido (FFRLS + EKF), aplicado a ônibus, em Sensors 2025, reporta erro abaixo
de 10% e RMSE entre 100 e 274 kg [44].

Pneu: o método TRIP-ID de Farroni et al., publicado em Mechanical Systems and Signal Processing em
2018, identifica micro-parâmetros da Magic Formula, mas o grupo usa célula de carga na roda para
isso; o texto completo ficou atrás de paywall nesta pesquisa e não foi confirmado em detalhe. Sem
canal de força lateral direta, o que é viável é uma rigidez de curva efetiva por eixo, ou um
coeficiente de atrito agregado, via filtro de Kalman estendido sobre um modelo de bicicleta usando
aceleração lateral, ângulo de esterço e velocidade, contaminado por transferência de carga e
downforce desconhecidos, ou seja, com incerteza alta.

Aerodinâmica: coastdown segundo SAE J1263, ajustando `F = a + b·v + c·v²` sobre velocidade e tempo
em desaceleração livre, confirmado na documentação da MathWorks sobre estimação de coeficiente de
arrasto por ensaio de coastdown [45]. Esse método usa só velocidade contra tempo em trechos de
desaceleração natural da volta, que existem no acervo da SARU. Não foi encontrado nenhum artigo
revisado por pares que separe sustentação (Cl) de arrasto (Cd) usando apenas telemetria de pista,
sem túnel de vento ou sensor de força.

Resumo de viabilidade com os canais de um logger de Porsche Cup (velocidade de roda, RPM, marcha,
throttle/freio, ax/ay de IMU do logger, GPS, sem célula de carga, sem força de pneu, sem altura de
suspensão): viável com boa confiança, massa (erro de 1 a 5% na literatura) e CdA agregado por
coastdown. Viável só com incerteza alta, rigidez de curva por eixo e indicação de balanço de peso.
Inviável sem sensor adicional, coeficientes completos da Pacejka, separação de Cl e Cd, e balanço
aerodinâmico numérico.

## 6. Parâmetros públicos do Porsche 911 GT3 Cup

| Item | 991.1 (2013-2016) | 991.2 (2017-2020) | 992.1 (2021+) |
|---|---|---|---|
| Massa | 1.175 kg | 1.200 kg pronto para corrida | 1.260 kg |
| Distribuição de peso | Não encontrado | Não encontrado | Não encontrado |
| Potência | 460 cv (338 kW) a 7.500 rpm, boxer 3,8 L | 357 kW (485 cv) a 7.500 rpm, 3.996 cm³, 480 Nm a 6.250 rpm | 375 kW (510 cv) a 8.400 rpm, 470 Nm a 6.150 rpm, 3.996 cm³, corte a 8.750 rpm |
| Dimensões | Comprimento 4.547 mm, entre-eixos 2.463 mm | 4.564 × 1.980 × 1.246 mm, entre-eixos 2.456 mm | Largura 1.920 mm dianteira / 1.902 mm traseira (oficial); comprimento 4.585 mm e entre-eixos 2.459 mm só em fonte de imprensa |
| Pneu | Michelin 27/65-18 e 31/71-18 | Michelin 270 mm e 310 mm, aro 18 | Michelin Pilot Sport Cup N3, 30/65-18 e 31/71-18 |
| Aerodinâmica | Não encontrado | Não publicada numericamente | Asa traseira de 11 posições, sem coeficiente publicado |
| Transmissão | Sequencial dog-type de 6 marchas por paletas | Sequencial de 6 marchas | Sequencial de 6 marchas, 72 kg, atuador eletrônico, autoblocante mecânico |

Fonte do 991.1: imprensa especializada (motorauthority, stuttcars, racecarsforyou), citando um
comunicado de 2013 que não foi localizado diretamente nesta pesquisa; tratar como fonte secundária,
não oficial primária [46]. Fonte do 991.2: comunicado oficial Porsche Newsroom número 13026 e o
media guide da Porsche Cars North America [47]. Fonte do 992.1: comunicados oficiais Porsche
Newsroom números 23150 e 23202; comprimento e entre-eixos só aparecem em stuttcars.com, sem
confirmação em fonte oficial [48][49]; medida de pneu confirmada em tyre-trends.com [50]. A
Porsche não publica distribuição de peso nem coeficiente aerodinâmico do GT3 Cup em nenhuma
geração, nas fontes consultadas.

## 7. Arquitetura recomendada, prós e contras

| Camada | Onde fica | Prós | Contras |
|---|---|---|---|
| QSS lap time (varredura de setup) | Python, `saru-core` | Já existe e roda; sem custo de nova linguagem; time já sabe manter | Se o throughput não bastar, precisa de Numba/JAX antes de cogitar reescrita |
| Suspensão (corner) | C++/pybind11, já em `ext/` | Já existe, isolado, não precisa mexer | Exige toolchain C++ no build de desenvolvimento (não no cliente final) |
| Transiente 14-DOF | Julia, `saru-core-jl`, worker assíncrono | DAE simbólico com ModelingToolkit, ecossistema de otimização (Optimization.jl/JuMP.jl) coeso, chamada Python com overhead baixo se algum dia precisar (PythonCall) | Latência de primeira execução por processo, hoje ainda com dois fatores de calibração sem base física a remover |
| Modelo de piloto | Julia, a construir | Reaproveita o mesmo processo do 14-DOF, sem fronteira de linguagem extra | Não existe ainda; melhor base aberta encontrada é MPCC/TUM-CONTROL, ambos exigem adaptar de single-track genérico para o GT3 Cup |
| Estimação de parâmetros (massa, CdA) | Python, RLS/EKF | Simples, mesma linguagem da orquestração, não precisa do worker Julia para essa etapa | Escopo limitado (seção 5); não cobre pneu completo nem aero separada |
| Integração backend | `saru-os` FastAPI | Já documentado nos dois `CLAUDE.md`: Python em processo via submodule, Julia fora de processo via fila Redis | Exige manter o contrato YAML/HDF5 estável entre os dois repositórios |

Backend chama a camada Python em processo, como import de submodule git, sem custo de rede. Chama
a camada Julia como worker assíncrono atrás de fila Redis, contrato de entrada YAML de veículo mais
HDF5 de pista, saída lap_time mais telemetria, sem ponte em processo (nem `juliacall` nem `pyjulia`
no caminho síncrono), exatamente como os dois `CLAUDE.md` já descrevem. Teste contra o acervo
estende o padrão de harness já usado em `saru-core` (`validation/khalil2018_roll_validation.py`,
comparação contra referência externa por canal), aplicado à telemetria real de Porsche Cup Brasil:
rodar o preset da geração certa com os parâmetros estimados (massa, CdA) contra uma volta real do
acervo, e comparar velocidade, ax, ay, slip, marcha e RPM canal a canal, não só o tempo de volta.

## Fontes consultadas

Todas acessadas em 13 de setembro de 2026.

1. https://github.com/TUMFTM/laptime-simulation
   QSS ponto de massa em Python, LGPL-3.0, último push 2026-04-13.
2. https://github.com/dstrassera/OpenLapSim
   Simulador steady state em Python, GPL-3.0, último push 2023-09-12.
3. https://github.com/RoseGPE/RoseLap
   Projeto sem licença, sem atividade desde 2018.
4. https://github.com/drypatrick/OpenLAP-Lap-Time-Simulator-Python
   Porte Python do OpenLAP, GPL-3.0, 2022.
5. https://github.com/juanmanzanero/fastest-lap
   Núcleo C++ com API Python, transiente 3-DOF carro e 6-DOF kart, MIT.
6. https://github.com/jianminw/Lap-Time-Simulation
   Projeto sem licença, 2017.
7. https://github.com/mc12027/OpenLAP-Lap-Time-Simulator
   OpenLAP em MATLAB, autor Michael Chalkiopoulos, GPL-3.0, último push 2022-09-24.
8. https://github.com/sisl/AutomotiveDrivingModels.jl
   Tráfego 2D em Julia, sem modelo de pneu, último push 2020.
9. https://github.com/projectchrono/chrono
   Chrono::Vehicle, BSD-3, multicorpo, último push 2026-09-12.
10. https://api.projectchrono.org/wheeled_tire.html
   Modelos de pneu implementados em Chrono::Vehicle (Pacejka 89/2002, TMeasy, Fiala).
11. https://api.projectchrono.org/vehicle_models.html
   Veículos de referência do Chrono::Vehicle, militares e utilitários, nenhum carro de corrida.
12. https://github.com/mathworks/vehicle-pure-pursuit
   Especificação do algoritmo pure pursuit em Simulink.
13. https://github.com/bzarr/TUM-CONTROL
   NMPC com single-track e Pacejka em CasADi, LGPL-3.0.
14. https://github.com/alexliniger/MPCC
   Model Predictive Contouring Control, Apache-2.0, testado em Formula Student real.
15. https://github.com/urosolia/RacingLMPC
   Learning MPC de corrida, sem licença, 2020.
16. https://vi-grade.com/en/products/vi-carrealtime/
   Página oficial do VI-CarRealTime: 14 GDL, faster than real time.
17. Brochura VI-CarRealTime v17 (cosin.eu)
   Formatos de pneu suportados, MF-Tyre, MF-Swift, FTire.
18. mathworks.com, página de integração VI-CarRealTime
   Confirma S-Function e código ANSI C.
19. simulation.michelin.com/canopy
   Canopy Simulations, adquirida pela Michelin em 2023, otimização de trajetória em nuvem.
20. chassissim.com
   Preço do Online Sim, US$ 100 por 150 simulações, US$ 5 por simulação extra.
21. optimumg.com
   OptimumLap gratuito, precisão declarada até 10%.
22. students.optimumg.com
   OptimumDynamics, edição estudantil US$ 295 por ano, hoje legacy.
23. Flyer da Vehicle Dynamics Library (dofware.com)
   Topologias de suspensão prontas e benchmark de 72 GDL em tempo real.
24. blog.technia.com
   Nota complementar sobre Dymola/Modelica e a Vehicle Dynamics Library.
25. ipg-automotive.com
   CarMaker, foco ADAS e condução autônoma, variantes HIL e Office.
26. https://julialang.org/benchmarks/
   Benchmark oficial Julia vs C, exclui tempo de compilação.
27. SciMLBenchmarks, problema ROBER (benchmarks.sciml.ai)
   CVODE_BDF falha em tolerância alta; Rodas4/Rodas5 rápidos no mesmo teste.
28. https://julialang.org/blog/2023/04/julia-1.9-highlights/
   Pkgimages reduz carregamento de ModelingToolkit de 73,53 s para 4,81 s.
29. viralinstruction.com/posts/badjulia
   Relato de 2021 sobre latência e regressão de desempenho em Julia, anterior à melhoria do 1.9.
30. web.casadi.org/docs
   CasADi resolve DAE semi-explícita via CVodes/IDAS com diferenciação automática.
31. discourse.julialang.org, tópico 112736
   Comparação de uso entre JuMP (declarativo) e Optimization.jl (imperativo).
32. nlopt.readthedocs.io
   NLopt, bindings C, C++, Python e Julia, otimização local e global.
33. https://github.com/JuliaPy/PythonCall.jl, arquivo BENCHMARKS.md
   Overhead de PythonCall de 1,1x a 2,4x sobre Python puro, PyCall 5,4x.
34. nanobind.readthedocs.io, página de benchmark
   Nanobind cerca de 3x mais rápido que pybind11 em chamada simples.
35. julialang.github.io/PackageCompiler.jl
   Gera app com runtime Julia embutido; sysimage não é realocável entre caminhos.
36. cibuildwheel.pypa.io
   Gera wheels para Linux, macOS e Windows sem exigir toolchain no cliente.
37. Stack Overflow Developer Survey 2024
   Python 51%, C++ 23%, Julia 1,1% dos respondentes (65.415 respostas).
38. TIOBE Index, edição de setembro de 2026
   Python 1º lugar (17,76%), C++ 3º (8,67%), Julia 21º (0,74%).
39. GitHub Octoverse 2024
   Python como linguagem mais usada no GitHub; Julia fora do top 10.
40. numba.readthedocs.io, guia de 5 minutos
   0,33 s na primeira chamada, 6,68 microssegundos nas chamadas seguintes.
41. docs.jax.dev, página de instalação
   GPU NVIDIA não funciona no Windows nativo, exige WSL2.
42. https://github.com/patrick-kidger/diffrax/issues/94
   Relato de usuário: compilação JIT de 23,97 s contra 2,56 s do odeint nativo do JAX.
43. Vahidi, Stefanopoulou e Peng, Vehicle System Dynamics, 2004 (PDF em cecas.clemson.edu)
   RLS com fator de esquecimento para massa veicular, erro dentro de 5%.
44. Sensors, 2025, artigo PMC11945728
   FFRLS combinado com EKF em ônibus, erro abaixo de 10%, RMSE de 100 a 274 kg.
45. mathworks.com/help/sldo, estimativa de coeficiente de arrasto por coastdown
   Método SAE J1263, `F = a + b·v + c·v²`.
46. motorauthority.com, stuttcars.com, racecarsforyou.com
   Especificações de imprensa do 991.1, sem comunicado oficial localizado.
47. newsroom.porsche.com, comunicado 13026, e media guide da Porsche Cars North America
   Especificações oficiais do 991.2.
48. newsroom.porsche.com, comunicados 23150 e 23202
   Especificações oficiais do 992.1.
49. stuttcars.com
   Comprimento e entre-eixos do 992.1, sem confirmação em fonte oficial.
50. tyre-trends.com
   Medida do pneu Michelin do 992.1.
51. arma.sourceforge.net
   Armadillo 15.6, Apache 2.0 desde a versão 7.800, sem ODE, otimização ou gráfico.
52. libeigen.gitlab.io
   Eigen 5.0.1, publicado em 2025-11-08, MPL2, sem ODE nem gráfico nativo.

## Não confirmado

- Comparação direta de desempenho entre Boost.odeint e DifferentialEquations.jl no mesmo problema (falha de conexão na fonte).
- Cobertura completa do Ceres Solver (conexão com a fonte falhou).
- Artigo em tandfonline, DOI 10.1080/00423114.2024.2379546 (erro 403 no acesso).
- Método "virtual elevation" para separar arrasto de outros efeitos por telemetria (erro 403 na fonte).
- Texto completo do método TRIP-ID de Farroni et al., 2018, atrás de paywall.
- Disponibilidade de programadores Julia, C++ e Python especificamente no Brasil.
- Tamanho típico em megabytes de um executável gerado por PackageCompiler.jl.
- Comunicado oficial da Porsche de 2013 com as especificações do 991.1 (só fonte de imprensa localizada).
- Distribuição de peso e coeficiente aerodinâmico numérico do 911 GT3 Cup, em qualquer geração.
