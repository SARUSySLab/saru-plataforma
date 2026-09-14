---
titulo: "Load sensitivity de pneus slick GT3 no formato \(\mu_\text{eff} = \mu (1 + k\,\Delta F_z/F_{z0})\)"
data: "2026-07-15"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/research/Load sensitivity de pneus slick GT3 no formato μ_eff = μ·(1 + k·ΔFz Fz0).md"
status: "vigente"
area: "pneu"
---

# Load sensitivity de pneus slick GT3 no formato \(\mu_\text{eff} = \mu (1 + k\,\Delta F_z/F_{z0})\)

## Visão geral

Este documento sintetiza valores típicos e faixas plausíveis para o coeficiente de load sensitivity \(k\) em pneus slick de corrida, com foco em aplicações GT3, usando o modelo simplificado \(\mu_\text{eff} = \mu (1 + k\,\Delta F_z/F_{z0})\). A análise baseia‑se em exemplos numéricos clássicos (Milliken RCVD), explicações de Pacejka sobre \(F_y\propto F_z^n\), material didático de dinâmica veicular, dados TTC/FSAE e documentação técnica de pneus de competição.[^1][^2][^3][^4]

A conclusão geral é que pneus slick de competição, incluindo aplicações GT/GT3, apresentam tipicamente um \(k\) da ordem de −0,10 a −0,15 em torno de uma carga de referência \(F_{z0}\) representativa, com uma faixa realista de incerteza de aproximadamente −0,05 a −0,20 dependendo de composto, temperatura, faixa de carga e condição de pista.[^5][^4][^6][^1]

## Exemplo clássico Milliken / Wikipedia

### Dados e equação

Milliken & Milliken (Race Car Vehicle Dynamics, cap. 2) apresentam um exemplo didático de pneu de turismo/performance onde se traça \(\mu = F_y/F_z\) em função de \(F_z\), posteriormente reproduzido em materiais didáticos e na página “Tire load sensitivity” da Wikipedia. A figura de referência mostra, em unidades imperiais, três pontos típicos de operação:[^2][^1]

- \(F_z = 900\,\text{lbf}\): \(\mu \approx 1{,}10\)
- \(F_z = 1350\,\text{lbf}\): \(\mu \approx 1{,}08\)
- \(F_z = 1800\,\text{lbf}\): \(\mu \approx 0{,}97\)

Esses valores ilustram claramente a carga sublinear (\(F_y\) cresce com \(F_z\), mas \(\mu\) decresce).[^1]

### Ajuste de k no modelo linearizado

Considerando o modelo linearizado em torno de \(F_{z0} = 1350\,\text{lbf}\):

\[\mu_\text{eff} = \mu_0\left(1 + k\,\frac{F_z - F_{z0}}{F_{z0}}\right),\quad \mu_0 = \mu(F_{z0})\]

Pode‑se ajustar \(k\) por mínimos quadrados aos três pontos acima. Usando \(X = (F_z-F_{z0})/F_{z0}\) e \(Y = \mu/\mu_0 - 1\), um ajuste linear fornece \(k \approx -0{,}18\). Se o ajuste for feito apenas entre \(F_z = 1350\) e \(F_z = 1800\,\text{lbf}\), o valor obtido é \(k \approx -0{,}31\), refletindo uma queda relativamente forte de \(\mu\) na extremidade superior da faixa de carga.[^7]

Embora este exemplo não seja um slick GT3, ele fixa a ordem de grandeza da load sensitivity de pneus de alto desempenho de passeio, sugerindo \(|k|\) na faixa de 0,1-0,3, dependendo da exata linearização.[^1][^2]

## Interpretação pelo expoente n em \(F_y \propto F_z^n\)

### Relação \(F_y\)-\(F_z\) sublinear

Pacejka discute que, em regime de pico de força lateral, a força máxima de pneu pode ser aproximada por uma lei de potência \(F_y \propto F_z^n\), com expoente \(n\) tipicamente entre 0,7 e 0,9 para pneus de passeio e de alto desempenho. Como a relação de atrito é \(\mu = F_y/F_z\), segue que:[^8][^1]

\[\mu(F_z) \propto F_z^{n-1}\]

Assim, para \(n = 0{,}8\), tem‑se \(\mu \propto F_z^{-0{,}2}\), isto é, \(\mu\) decresce com \(F_z\) com um expoente em módulo de aproximadamente 0,2.[^1]

### Conversão aproximada para k

Linearizando \(\mu(F_z) \propto F_z^{n-1}\) em torno de \(F_{z0}\), obtém‑se uma expressão equivalente à forma \(1 + k\,\Delta F_z/F_{z0}\), em que \(k\) é aproximadamente igual a \(n-1\), isto é, \(k \approx -0{,}2\) quando \(n \approx 0{,}8\). Pequenas variações de \(n\) dentro da faixa 0,7-0,9 levam a \(k\) efetivo entre cerca de −0,3 e −0,1, que coincide bem com a faixa inferida do exemplo de Milliken.[^8][^1]

## Parâmetros de load sensitivity em modelos tipo Pacejka

### Parâmetros a1/b1 (Pacejka ’94/’96)

Na formulação Pacejka ’94/’96 para o Magic Formula em regime lateral puro, os parâmetros de sensibilidade à carga, usualmente denotados por a1, a2, b1, b2, etc., controlam como o pico de \(\mu\) varia com \(F_z\). A documentação técnica que explica esses parâmetros mostra faixas típicas em que b1 (ou a1) assume valores negativos para representar a queda de \(\mu\) com o aumento de \(F_z\).[^9]

Guias de identificação de parâmetros MF relatam que, para pneus de passeio e de performance, esses coeficientes levam a curvas \(\mu(F_z)\) com decréscimo de \(\mu\) na faixa de 10-25% quando \(F_z\) cresce da carga mínima à máxima considerada nos ensaios, consistente com \(k\) efetivo na ordem de −0,1 a −0,25 quando se traduz para a forma linearizada.[^10][^11]

### Faixas típicas sugeridas

A partir dessas publicações, pode‑se resumir um intervalo plausível associado à família de conjuntos MF produzidos em provas de pneus de alta performance:

- Valor central: \(k \approx -0{,}15\)
- Faixa aproximada: \(k \approx -0{,}05 \dots -0{,}25\)

Esses números são consistentes com o expoente \(n\) discutido anteriormente e com o exemplo de Milliken.[^11][^10][^1]

## Dados TTC/FSAE (Hoosier slick 10")

### Observações de \(\mu(F_z)\) em TTC

Trabalhos acadêmicos com dados do Formula SAE Tire Test Consortium (TTC) mostram curvas \(\mu_y\) versus \(F_z\) para pneus slick Hoosier (R20, R25B etc.), em que \(\mu\) costuma cair da ordem de 10-25% na faixa de carga efetivamente usada em FSAE, tipicamente de algumas centenas a pouco mais de 1 kN por pneu.[^3][^4][^12]

Uma tese de Lateral Tire Model Parameter Estimation baseada em dados TTC, por exemplo, ilustra claramente esse comportamento: o pico de \(\mu_y\) diminui à medida que \(F_z\) aumenta, sendo a load sensitivity caracterizada como um fator importante para o desempenho em curva.[^4]

### Interpretação em termos de k

Tomando uma queda típica de \(\mu\) de ~15% ao aumentar \(F_z\) num fator próximo de 2 (por exemplo, de 400 para 800 N), a expressão linearizada \(\mu_\text{eff} = \mu (1 + k\,\Delta F_z/F_{z0})\) implica um \(k\) efetivo próximo de −0,15, assumindo \(F_{z0}\) no meio da faixa de carga.[^3][^4]

Trabalhos de otimização e seleção de pneus para FSAE relatam explicitamente “high load sensitivity” e adotam modelos em que variar \(k\) entre aproximadamente −0,10 e −0,25 impacta sensivelmente o desempenho simulado, o que reforça essa ordem de grandeza.[^12]

## Pneus de corrida GT/GT3

### Documentação aberta e inferência indireta

Manuais Michelin e Pirelli para pneus GT/GT3 do tipo 30/31‑680‑18 (slicks radiais) fornecem especificações de dimensões, pressões recomendadas, limites de carga por eixo e faixas de temperatura, mas não publicam diretamente curvas \(\mu(F_z)\) ou parâmetros detalhados de load sensitivity.[^13][^14][^15][^16]

Fontes indiretas incluem documentação e artigos da OptimumG, que apresentam gráficos de “lateral coefficient of friction” versus \(F_z\) para diversos pneus de competição, e textos explicativos sobre a perda de \(\mu\) com aumento de carga. Esses gráficos mostram, em diferentes pneus de corrida, uma redução de \(\mu\) típica da ordem de 10-20% ao longo da faixa de carga relevante, coerente com \(k\) em torno de −0,10 a −0,20 quando se utiliza o modelo linearizado.[^17][^5]

Além disso, artigos e material de simulação (por exemplo, documentação de presets de pneus de corrida em simuladores de dinâmica veicular) apontam coeficientes de atrito estático de pico para slicks de corrida na ordem de 1,7-1,9, com comportamento de load sensitivity similar ao de outros pneus de alto desempenho discutidos por Pacejka.[^18][^19]

### Modelos de F1/GT de domínio público

Modelos simplificados usados em estratégias e simuladores abertos inspirados em F1/GT incluem frequentemente um parâmetro de “lateral load sensitivity” equivalente ao \(k\) aqui discutido, calibrado para reproduzir curvas \(\mu(F_z)\) consistentes com dados de pneus de competição. Esses modelos costumam assumir magnitudes de sensibilidade que produzem quedas de \(\mu\) de cerca de 5-20% em torno de um \(F_{z0}\) típico, levando a \(k\) num intervalo muito semelhante ao inferido de TTC, Pacejka e Milliken.[^20][^21]

## Síntese dos intervalos de k por tipo de pneu

A tabela a seguir resume valores centrais e faixas plausíveis de \(k\) para diferentes categorias de pneus, todos referidos ao modelo \(\mu_\text{eff} = \mu (1 + k\,\Delta F_z/F_{z0})\), com \(F_{z0}\) escolhido como carga média de operação.

| Categoria de pneu | Valor central de k | Faixa plausível de k | Fontes principais |
|-------------------|--------------------|----------------------|-------------------|
| Passeio/performance (exemplo RCVD) | \(k \approx -0{,}18\) | \(\approx -0{,}10 \dots -0{,}30\) | Exemplo Milliken/RCVD, figura também em Wikipedia (Tire load sensitivity). [^1][^2] |
| Pneus de passeio/alto desempenho genéricos (Pacejka) | \(k \approx -0{,}15\) | \(\approx -0{,}05 \dots -0{,}25\) | Expoente \(n\) em \(F_y \propto F_z^n\) (\(n\) em torno de 0,7-0,9) e faixas típicas de parâmetros a1/b1. [^1][^10][^11][^8] |
| Slick FSAE (Hoosier TTC) | \(k \approx -0{,}15\) | \(\approx -0{,}10 \dots -0{,}25\) | Curvas \(\mu_y(F_z)\) TTC e teses FSAE com dados Hoosier; queda de \(\mu\) de ~10-25% na faixa de carga. [^3][^4][^12] |
| Slick de corrida GT/GT3 (Michelin/Pirelli 30/31‑680‑18, inferido) | \(k \approx -0{,}12\) | \(\approx -0{,}05 \dots -0{,}20\) | Documentação OptimumG sobre coeficiente lateral vs carga, modelos de pneus de competição, presets F1/GT e valores típicos de \(n\). [^5][^18][^19][^17][^21] |

## Orientações para uso em modelos de dinâmica veicular

Para modelos de volta rápida, NMPC ou simulação de GT3 baseados em um pneu slick tipo 30/31‑680‑18, é razoável adotar os seguintes valores como ponto de partida:

- Escolher \(F_{z0}\) como a carga média por pneu em uma curva representativa, incluindo downforce, por exemplo \(F_{z0} \approx 9\)-10 kN em um GT3 típico.
- Usar valores centrais de \(k\) por eixo, por exemplo:
  - Eixo dianteiro: \(k_\text{front} \approx -0{,}10\)
  - Eixo traseiro: \(k_\text{rear} \approx -0{,}12 \dots -0{,}15\)
- Realizar análise de sensibilidade explorando \(k \in [-0{,}05, -0{,}20]\) para cobrir incertezas de composto, temperatura, pressão, desgaste e faixa de carga.

Esses valores são compatíveis com as ordens de grandeza observadas em dados laboratoriais (Milliken, TTC), com as discussões teóricas de Pacejka (expoente \(n\)) e com as curvas publicadas por OptimumG e outros autores para pneus de competição, embora não substituam calibração específica a partir de dados reais de pneus GT3 da Michelin ou Pirelli.[^21][^5][^4][^17][^3][^1]

---

## References

1. [Tire load sensitivity - Wikipedia](https://en.wikipedia.org/wiki/Tire_load_sensitivity)

2. [The Absolute Guide to Racing Tires - Part 1 - Lateral Force](https://racingcardynamics.com/racing-tires-lateral-force/) - Lateral Force Coefficient Where LFC is the lateral force coefficient, Fy is the lateral force and Fz...

3. [Tire Modeling and Data Analysis in the FSAE Context](https://openscholarship.wustl.edu/cgi/viewcontent.cgi?article=1311&context=mems500) - The rate at which a tire's friction coefficient decreases with increasing load is its load sensitivi...

4. [Lateral Tire Model Parameter Estimation ...](https://webthesis.biblio.polito.it/34676/1/tesi.pdf) - The tire load sensitivity is the phenomenon for which the peak of lateral friction coefficient falls...

5. [Lateral thinking on tire load variations](https://optimumg.com/235300-2/) - In Figure 6, we are looking at the lateral coefficient of friction (lateral force divided by the ver...

6. [Tyres - Load Sensitivity » theRACINGLINE.net](https://theracingline.net/2018/race-car-tech/race-tech-explained/tyres-load-sensitivity/) - Andrea Quintarelli discusses racing tyres. In Part 5 of a 7 part series, we look at load sensitivity...

7. [[PDF] Mathematical modelling of tire response curves](http://www.ingveh.ulg.ac.be/uploads/education/MECA0525/10bis_MECA0525_TYRE3_2021-2022.pdf)

8. [Tire Modeling and Friction Estimation Svendenius, Jacob](https://lucris.lub.lu.se/ws/files/4401399/27004.pdf)

9. [Pacejka '94 parameters explained, a comprehensive guide](https://www.edy.es/dev/docs/pacejka-94-parameters-explained-a-comprehensive-guide/) - This guide explains how each parameter of the Pacejka ’94 specification affects the resulting curve,...

10. [A Methodology for Identification of Magic Formula Tire ...](https://publications.lib.chalmers.se/records/fulltext/239258/239258.pdf) - by A JONSON · Cited by 11, Pacejka (2012, [3]) describes the behavior and modeling of tires meticul...

11. [Magic Formula - an overview](https://www.sciencedirect.com/topics/engineering/magic-formula) - Pacejka (2012). stiffness divided … the model predicts a transient increase in friction coefficient,...

12. [Optimising Tire Selection, IJERT](https://www.ijert.org/optimising-tire-selection) - ... load sensitivity) which basically measures that, how will a car ... Hoosier R25B is qualified to...

13. [TYRE PROFESSIONAL GUIDE CUSTOMER RACING](https://www.ranksport.racing/WebRoot/Store25/Shops/11546804/MediaGallery/Michelin_Broschuere_2022_komplett.pdf) - Ensure that the pressure, bodywork, speed and axle load values are those recommended by Michelin in ...

14. [[PDF] TECHNICAL BOOKLET 2021 INTERNATIONAL GT](https://www.internationalgt.net/pirelli_tires/P_Book%20-%20International%20GT%202021.pdf)

15. [1](http://rogerkrausracing.com/pdfpricing/Porsche%20Michelin%20App%20and%20Pressures%20Apr-18.pdf)

16. [Appendix O, Section F, PIRELLI Tire GT](https://www.casc.on.ca/sites/default/files/Documents/2021%20Appendix%20O%20Section%20F%20-%20PIRELLI%20Tire%20GT-v0.9.pdf)

17. [[PDF] Help File Version 1.0.14 - OptimumG](https://optimumg.com/wp-content/uploads/2019/08/OptimumTire_Documentation.pdf)

18. [Tires](https://vehiclephysics.com/blocks/tires/) - Racing slick tires can perform in the range of 1.7 - 1.9. The slip applied to the tire friction curv...

19. [Friction Preset - NWH Vehicle Physics 2 Documentation](https://nwhcoding.com/VehiclePhysics/manual/FrictionPreset.html)

20. [GGV Map for MATLAB: Full Reference Variable ...](https://www.studocu.com/en-us/document/university-of-texas-at-austin/intro-to-aerospace-engineering/ggv-map-for-matlab-full-reference-variable-mapping-table/165231951) - Explore the GGV variable mapping for Python and MATLAB, focusing on tire coefficients, aerodynamic f...

21. [Tyres and degradation models - Formula One Wiki](https://formula1.wiki/index.php?title=Tyres_and_degradation_models)

