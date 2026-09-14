---
titulo: "Fundamentação técnica do Saru Analyzer, fontes canônicas × o que medimos hoje"
data: "2026-08-19"
origem: "_arquivo/saru-app/docs/research/2026-07-fundamentacao-tecnica-analyzer.md"
status: "vigente"
area: "dinamica_veicular"
---

# Fundamentação técnica do Saru Analyzer, fontes canônicas × o que medimos hoje

> Blocos 5 (fontes ampliadas) e 7 do mapeamento de arquitetura/customização (2026-07-20).
> Compara as metodologias e KPIs de Suellio Almeida, Carroll Smith, Jorge Segers, OptimumG,
> Ross Bentley, Buddy Fey, Adam Brouillard e Samir Abid com o que o engine
> (`services/telemetry-api/saru_lapanalyzer/domain/`) calcula de fato. Conclusão em §5-6:
> **o que vale a pena o Analyzer analisar**, priorizado por convergência das fontes e custo.
> Companheiros: `2026-07-ui-ux-telemetria-ao-vivo.md` · `2026-07-ui-ux-analise-pos-sessao.md` ·
> `2026-07-ui-ux-video-sincronizado.md`.

## 0. Duas correções factuais antes de tudo

1. **"Race to Win" não é de Carroll Smith.** A série é: *Prepare to Win* (1975), *Tune to Win*
   (1978), *Engineer to Win* (1984), *Drive to Win* (1996), mais dois companheiros, *Nuts,
   Bolts, Fasteners and Plumbing Handbook* (1990; "Screw to Win" era só uma capa de brincadeira)
   e *Engineer in Your Pocket* (1998). "Race to Win" (2008) é de **Derek Daly**
   ([carrollsmith.com/books](https://www.carrollsmith.com/books/),
   [racefans.net](https://www.racefans.net/2008/06/19/race-to-win-how-to-become-a-complete-champion-driver-derek-daly/)).
2. **Suellio Almeida não é ex-Stock Car.** Trajetória verificada: sim racer/coach (>1.100
   sessões) que estreou na pista real em 2024 e foi **campeão rookie da Radical Cup North
   America** pela Graham Rahal Performance; 2025 no Michelin Pilot Challenge (TCR)
   ([Wikipedia](https://en.wikipedia.org/wiki/Suellio_Almeida),
   [radicalmotorsport.com](https://radicalmotorsport.com/news/sim-star-suellio-almeida-joins-radical-cup-grid)).
   Isso o torna *mais* relevante para o Saru (ponte sim↔real), não menos.

## 1. As fontes em uma frase cada (metodologia)

| Fonte | Framework central | Material |
|---|---|---|
| **Suellio Almeida** (Almeida Racing Academy) | Diagnóstico → causa-e-efeito → reforço; **"4 Stages of a Corner"** (entry/rotação, mínima no apex, apex→exit, exit); **Maximum Rotation Point** (release do freio coincide com pico de volante); técnica antes de setup ("setup é os últimos 2%"); prática deliberada, um problema por vez | [4 Stages](https://almeidaracingacademy.com/blog/4-stages-corner-highlevel-racing-technique) · [Trail braking em 5 passos](https://almeidaracingacademy.com/blog/5-steps-finally-master-trail-braking-sim-racing) · [Motor Racing Book Vol. 1](https://www.amazon.com/Motor-Racing-Book-Car-Handling/dp/B0CJWZ75W7) |
| **Carroll Smith** | Confiabilidade antes de performance; **uma mudança por vez, medir, registrar** (log book/setup sheet); pirômetro como diagnóstico, **cronômetro como juiz**; matriz sintoma→ajuste por fase de curva (*Engineer in Your Pocket*) | [Tune to Win](https://archive.org/details/tunetowinartscie0000smit) · [método das temps](https://calltogrid.com/tuning-tire-temperature/) |
| **Jorge Segers** (*Analysis Techniques…*, SAE R-408, **lido do PDF no Drive**: sumário + caps. 1-3 integrais) | 4 categorias de análise (veículo, piloto, desenvolvimento, confiabilidade); *vital signs* primeiro; do macro (segmentos, volta ideal teórica) ao micro; **análise é comparativa por distância** (variance Eq. 3.2/3.3 = o delta do Saru); **cap. 17: reduzir canais a métricas escalares por volta + run charts** | [SAE R-408](https://www.sae.org/publications/books/content/r-408/) |
| **OptimumG** (Claude Rouelle) | Medir → modelar → validar → iterar; tudo nasce no contact patch; método **Yaw Moment Diagram** → grip/balance/stability/control; seminário DDPE ensina KPIs de piloto (throttle/brake efficiency) e correlação sim×pista como entregável | [AVD Seminar](https://optimumg.com/our-seminars/applied-vehicle-dynamics/) · [Magic Number](https://optimumg.com/rolling-about/) |
| **Ross Bentley** (Speed Secrets) | Dado → mudança de comportamento; comparar a melhor volta com as **3-4 seguintes** (consistência primeiro); **End of Braking** e a *release* importam mais que o ponto de frenagem; metas comportamentais ("+3% da volta em full throttle") | [Coaching with Data](https://rossbentley.substack.com/p/speed-secrets-coaching-with-data) |
| **Buddy Fey** (*Data Power*, 1993) | Diagnóstico visual "de relance" por segmento de curva (entry/mid/exit), herança viva nos sector reports modernos | [Amazon](https://www.amazon.com/Data-Power-Acquisition-Practical-Interpretation/dp/1881096017) · [datamc.org](https://www.datamc.org/data-acquisition/software-and-analysis/creating-a-lap-file-and-sectors/) |
| **Adam Brouillard** (*The Perfect Corner*) | Física do traçado ótimo (espiral de Euler); apex = ponto de transição de força; maximizar velocidade mínima e antecipar full throttle | [Amazon](https://www.amazon.com/Perfect-Corner-Drivers-Step-Step/dp/0997382422) |
| **Samir Abid** (Your Data Driven) | Para o amador: speed trace primeiro, consistência antes de velocidade, priorizar achados | [yourdatadriven.com](https://www.yourdatadriven.com/learn-motorsports-data-analysis/) |

## 2. O que o Saru Analyzer já mede (inventário real do código)

`services/telemetry-api/saru_lapanalyzer/domain/`:
- Comparação: delta instantâneo + cumulativo (`analysis_lap.py::compute_delta`, é literalmente a *variance* de Segers Eq. 3.2/3.3), volta ideal teórica, setores e micro-setores com speed min/avg/max (`analysis_sector.py`).
- **Frenagem** (`brake_trace.py`, cita Segers R-408): initial application, aggression, pico, **release smoothness**, over-slowing, lock-up (via slip), coasting, stability KPI e **Driver Confidence Index 0-100**; braking points comparados vs referência; eficiência de frenagem.
- **Pilotagem** (`analysis_driving.py`): fases BRAKING/ENTRY/APEX/EXIT por curva, **CornerInsight ordenado por perda total** com fase dominante e explicação textual; **trail-braking index** (Pearson freio×|lat g|).
- **Inputs** (`analysis_inputs.py`): % full throttle, coasting %, overlap de pedais, suavidade (FFT), correlação de inputs vs referência.
- **Veículo** (`analysis_math_channels.py`): slip ratio por roda, slip angle (do chassi), aero balance (fração estática), roll rate e pitch rate [°/s], grip factor (G_sum/μg com filtro IQR).
- **Pneus** (`analysis_tyre.py`): spread de temperatura com diagnóstico de cambagem e pressão, **implementação direta do método do pirômetro do Tune to Win**.
- Sessão: `consistency_pct` (σ dos lap times / melhor).

## 3. Veredicto das fontes sobre cada métrica atual

| Métrica Saru | Veredicto | Quem sustenta |
|---|---|---|
| Delta + volta ideal | ✅ CONFIRMA | Segers (Eq. 3.2/3.3), Bentley, Abid |
| Setores/micro-setores | ✅ CONFIRMA | Segers §3.2, Fey |
| Brake trace + DCI + release smoothness | ✅ CONFIRMA (forte) | Segers cap. 5, Bentley (a *release* é a métrica), Almeida (spike firme → release suave) |
| Trail-braking index | ✅ CONFIRMA | Almeida (proporcionalidade freio×volante), Bentley (hockey stick), Brouillard |
| Corner insights por fase, ordenados por perda | ✅ CONFIRMA | Almeida (4 Stages + "onde ganhar mais"), Fey, Smith (corner sequence), Abid |
| % full throttle / coasting / overlap | ✅ CONFIRMA | Bentley ("+3% em WOT"), Segers cap. 14, Almeida (coasting = tempo perdido) |
| Spread de temperatura de pneus c/ diagnóstico | ✅ CONFIRMA | Smith (é o método dele em código), Segers §8.8-8.9 |
| Grip factor, slip ratio, slip angle, aero balance | ✅ CONFIRMA | Segers, OptimumG (visão pneu-cêntrica) |
| Eficiência de frenagem | ⚠️ RESSALVA | Bentley: não premiar frear tarde/forte; a qualidade da *release* deve pesar mais que o ponto |
| Volta ideal como referência default | ⚠️ RESSALVA | Bentley/Almeida: comparar também com as próprias 3-4 melhores voltas; consistência antes de pico |
| Roll rate / pitch rate [°/s] | ❌ PRIORIDADE ERRADA | Segers cap. 9 e OptimumG pedem **gradientes** [°/g] steady-state (regressão ângulo × lat-g), não velocidades |
| Métricas de engenharia na cara do piloto | ⚠️ RESSALVA de UI | Almeida: "setup é 2%", grip/slip/aero/roll pertencem à camada engenheiro, não à visão default do piloto |

## 4. Lacunas, o que as fontes consideram essencial e o Saru não mede

Ordenadas por **convergência entre fontes × custo de implementação** (canais necessários já
existem no contrato, salvo indicação):

| # | Lacuna | Fontes | Custo/nota |
|---|---|---|---|
| 1 | **Minimum corner speed (velocidade no apex) por curva, vs referência** | Almeida (1ª métrica que compara), Bentley, Brouillard, Fey, Segers | Baixo, o apex já é detectado; falta expor `speed[apex]`. Grep `min_speed|apex_speed` no engine: zero |
| 2 | **Understeer angle** (esterço real − Ackermann `l/R`, R=v²/a_lat) como canal contínuo + média por volta | Segers §7.5 (canal clássico), OptimumG (understeer gradient é O KPI de balanço), Smith (Engineer in Your Pocket) | Baixo/médio, precisa do canal `steering`, que **hoje não é usado em nenhuma análise** |
| 3 | **Run charts / métrica-por-volta na sessão** (tendência de qualquer KPI ao longo do run: understeer médio, temp de pneu, braking point…) | Segers §2.2.5 + cap. 17 (coração da 2ª edição), Smith (antes/depois de cada mudança) | Médio, infra de "1 número por volta" que multiplica o valor de todos os KPIs existentes |
| 4 | **Consistência multi-volta por curva** (spread de min speed/braking point entre voltas; melhor vs 3-4 seguintes) | Bentley, Almeida, Segers §14.8, Abid | Baixo, estatística sobre dados já calculados |
| 5 | **Exit speed / carry-over por curva** | Almeida (estágio 4), Segers cap. 4 (velocidade de saída define a reta) | Baixo, análogo ao item 1 |
| 6 | **Roll gradient e pitch gradient [°/g]** (regressão, não rate) | Segers cap. 9, OptimumG (+ "Magic Number"/LLTD como evolução) | Baixo, mesmos canais `susp_pos_*` do roll rate atual |
| 7 | **Histograma de velocidade de amortecedor** (4 zonas, simetria) | Segers cap. 11, OptimumG tech tips | Médio, canais `susp_pos_*` existem; exige derivada + binning |
| 8 | **Log book / setup sheet vinculado à sessão** ("mudança X → efeito Y medido") | Smith (lacuna nº 1 dele), Segers §2.3 (session constants) | Médio, produto, não física: o BFF já tem vehicles/vehicle-setup-sot; falta amarrar setup→sessão→delta |
| 9 | **Steering/MRP**: pico de volante vs ponto de 90% de release do freio | Almeida (conceito-assinatura) | Baixo, depende do item 2 (usar `steering`) |
| 10 | **Vital signs / saúde do carro** (min/máx/média de óleo, água, freio por volta + alarmes condicionais) | Segers §3.1 ("primeiro passo de qualquer análise"), Smith (confiabilidade antes de performance) | Médio, para telemetria real; em sim é secundário |
| 11 | **Brake balance F/R** | Segers §5.5 | Requer canais de pressão por eixo (nem todo logger tem) |
| 12 | **Histograma de throttle + time-to-full-throttle pós-apex** | Segers §14.3, Bentley | Baixo |
| 13 | **Análise de linha/traçado** (turn-in, uso da largura, apex angle vs linha ótima) | Almeida, Brouillard, Segers §14.7 | Alto, exige dados posicionais confiáveis (GPS/x-y); deixar para depois |
| 14 | **Correlação sim×pista como KPI de produto** | OptimumG (sim + dado + piloto é o método) | **Vantagem estrutural única do Saru**: o `saru-core` já simula (LTS/QSS) e o SaDashboard já plota referência simulada, falta transformar o desvio sim×real em número acompanhável |

## 5. Recomendações, o que o Analyzer deve efetivamente analisar

**Onda 1 (barato, máxima convergência das fontes, só expõe/deriva o que já existe):**
1. Min corner speed + exit speed por curva, com delta vs referência (itens 1 e 5), vira a
   linguagem dos cartões de insight ("2 km/h a menos no apex da Curva 4").
2. Consistência por curva e "melhor vs 3-4 seguintes" como comparação default alternativa (item 4).
3. Trocar roll/pitch *rate* por *gradient* [°/g] (item 6), mesma matéria-prima, KPI certo.
4. Usar o canal `steering`: understeer angle (item 2) e MRP (item 9). Com isso o Saru passa a
   dizer **"o carro está understeer na entrada"** (engenheiro) e **"você abriu o volante antes
   do release"** (piloto), as duas personas do Company Book com o mesmo canal.

**Onda 2 (infra que multiplica tudo):**
5. Run charts / métrica-por-volta (item 3), qualquer KPI escalar ganha eixo "ao longo da
   sessão"; é também o pré-requisito do log book.
6. Log book de sessão + setup sheet (item 8), fecha o laço de Smith: mudança → efeito medido.
   O widget de workbook correspondente já tem onde morar (registry + `user_layouts`).
7. Damper histogram (item 7) e throttle histogram (item 12) como widgets novos do catálogo.

**Onda 3 (diferencial competitivo):**
8. KPI de correlação sim×real (item 14), nenhum concorrente amador tem física preditiva
   acoplada; transformar o overlay simulado que já existe em número de confiança acompanhável
   por run chart.
9. Análise de linha (item 13) quando houver dado posicional confiável.

**Regras de apresentação (das fontes, valem para qualquer layout):**
- Camadas por persona: métricas de input do piloto na frente (Almeida: "setup é 2%"); canais de
  engenharia na camada engenheiro, coincide com os templates piloto/engenheiro já existentes.
- Um problema por vez, com explicação causal e evidência um clique abaixo (Almeida, Bentley,
  Track Titan na pesquisa 5b), o `CornerInsight` ordenado por perda já é o motor disso; a UI
  deve mostrá-lo como cartão nº 1.
- O cronômetro é o juiz (Smith): todo KPI novo se justifica mostrando o delta de tempo associado.

## 6. Nota de método

Segers foi lido do PDF do Drive (sumário integral + caps. 1-3 completos; caps. 4-19 pelo
sumário + fontes web citadas). Carroll Smith, Almeida, OptimumG, Bentley, Fey e Brouillard vêm
de fontes públicas indexadas (vários sites bloquearam fetch direto; URLs citadas em cada seção
para verificação). Conteúdo pago (18 técnicas do checklist do Almeida, slides completos da
OptimumG, corpo de *Data Power*) está sinalizado como não verificado, nada foi inventado.
"Tire energy" (OptimumG) ficou sem definição pública verificável.
