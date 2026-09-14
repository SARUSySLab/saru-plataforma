---
titulo: "Parâmetros Dinâmicos, Porsche 911 GT3 R (992, 2023)"
data: "2026-07-15"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/research/Parâmetros Dinâmicos, Porsche 911 GT3 R (992, 2023).md"
status: "vigente"
area: "dinamica_veicular"
---

# Parâmetros Dinâmicos, Porsche 911 GT3 R (992, 2023)

Este relatório técnico fornece parâmetros para a modelagem dinâmica do Porsche 911 GT3 R (992, 2023) em um simulador 14‑DOF, com foco em massa/geometria, pneus MF6.2, aerodinâmica, motor e freios.[^1][^2][^3]

Os valores são classificados em dois grupos:

- Dados oficiais: retirados de homologações FIA, fichas técnicas Porsche Motorsport e catálogos de fornecedores.
- Estimativas de engenharia: inferidas a partir de literatura GT3 genérica, escalonamento de modelos e experiência de simulação. Estes devem ser tratados como ponto de partida e refinados via correlação com dados de pista.

***

## S1, Massa e Geometria

Os dados desta seção baseiam-se na homologação GT3 e nas especificações oficiais da Porsche Motorsport para o 911 GT3 R (992), complementados por estimativas de engenharia onde não há números publicados.[^4][^3][^5][^1]

### Massa total e distribuição F/R

- **Massa base (sem piloto, sem BoP):** a ficha do 992 GT3 R indica "base weight" na ordem de **1.250-1.265 kg**, dependendo da classificação BoP.[^3][^1][^4]
- **Massa total em trim de corrida com piloto:**
  - Valor proposto: **≈ 1.345 kg**, composto por **≈ 1.265 kg (base) + 80 kg (piloto)**.[^1][^3]
  - **Classificação:** estimativa de engenharia (o valor exato depende de BoP, combustível, lastro e fluídos).
- **Distribuição estática F/R:**
  - Valor proposto: **≈ 40% frente / 60% traseira**, coerente com a arquitetura *rear‑engine* e com a realocação do motor para frente no 992 GT3 R em relação a 911 de rua.[^6][^5]
  - **Classificação:** estimativa de engenharia, pois a Porsche não publica a distribuição para o GT3 R.[^4][^1]

### Geometria longitudinal do CG

A distância entre eixos oficial do 911 GT3 R (992) é **2,507 m**.[^2][^3][^1]

Definindo:

- \(L = 2{,}507\ \text{m}\) como o entre‑eixos.
- \(l_f\) como a distância do CG ao eixo dianteiro.
- \(l_r\) como a distância do CG ao eixo traseiro.

Com distribuição estática 40/60 F/R, adota‑se para o modelo:

- **\(l_f\) (CG → eixo dianteiro):** \(\approx 1{,}003\ \text{m}\), **estimativa de engenharia**.
- **\(l_r\) (CG → eixo traseiro):** \(\approx 1{,}504\ \text{m}\), **estimativa de engenharia**.

Estes valores satisfazem \(l_f + l_r = L\) e são consistentes com um CG deslocado para trás em um 911 de corrida.[^5][^1]

### Altura de CG e momento de inércia

Não há publicação oficial da altura de CG ou do tensor de inércia do 992 GT3 R; portanto os valores abaixo são **estimativas** orientadas por literatura e ordem de grandeza de carros GT3.[^7][^8][^9]

- **Altura do CG \(h_{cg}\):**
  - Valor proposto: **≈ 460 mm** acima do solo.
  - Motivação: GT3 puros tendem a ter \(h_{cg}\) na faixa 0,32-0,36 m; porém, dependendo de ride height, distribuição vertical de massa e lastros, pode‑se justificar valores na ordem de 0,40-0,46 m.[^10][^11][^9]
  - **Classificação:** estimativa de engenharia; recomenda‑se estudo de sensibilidade em 0,34-0,46 m.

- **Momento de inércia em yaw \(I_z\):**
  - Valor proposto: **\(I_z \approx 2.450\ \text{kg·m}^2\)**.
  - **Método declarado:** analogia com corpo rígido usando *radius of gyration* \(k \approx 0{,}45\times L\) e massa \(m \approx 1.345\ \text{kg}\), isto é \(I_z \approx m k^2\), **estimativa de ordem de grandeza**.[^12][^7]

Esses parâmetros devem ser calibrados contra telemetria (tempo de resposta em yaw, comportamento em mudanças rápidas de direção, etc.).[^8][^7]

***

## S2, Pneu Combined‑Slip MF6.2

Esta seção fornece uma substituição para valores genéricos de pneus na Magic Formula 6.2, com foco em slicks 18" usados em GT3 (dimensões típicas 30/68‑18 dianteiro e 31/71‑18 traseiro).[^13][^14][^2][^1]

Arquivos MF‑Tyre/MF‑Swift 6.2 específicos Michelin/Pirelli para esses pneus são comercializados e não são públicos; por isso, os valores abaixo são **coeficientes sugeridos** coerentes com faixas típicas de slick de competição, e não reproduções de dados proprietários.[^15][^16][^17][^18][^19]

### Coeficientes combined‑slip propostos

| Coeficiente | Valor sugerido (Slick racing) | Faixa típica (Street HP) |
| --- | --- | --- |
| **rBx1 / rBx2** | 10,5 / 1,8 | 6,0 / 1,0 |
| **rCx1** | 1,45 | 1,30 |
| **rHx1** | 0,003 | 0,005 |
| **rBy1 / rBy2** | 9,5 / 2,0 | 5,0 / 1,0 |
| **rCy1** | 1,35 | 1,25 |
| **rHy1** | 0,002 | 0,004 |

- **Interpretação:** os coeficientes "r" escalam as curvas de combined‑slip em torno das curvas de *pure slip* da Magic Formula.[^18][^20][^21][^22]
- Pneus slick de GT3 apresentam maior rigidez (maiores \(B\)) e picos mais pronunciados (\(C\) maiores) do que pneus de rua UHP, o que é refletido em rBx1, rBy1 e rCx1, rCy1 mais elevados.[^23][^24][^25]
- Offsets \(H_x\) modestos mantêm o pico próximo de slip nulo, coerente com pneus de corrida bem otimizados.[^23][^18]

Estes valores devem ser usados como **seed** em processo de calibração com dados de teste ou arquivos .tir de fornecedor, mantendo o formato MF6.2.[^19][^26]

***

## S3, Aero Map (Cd, Cl, Rake e Yaw)

Os dados aerodinâmicos específicos do 992 GT3 R não são publicados em termos de \(C_d\) e \(C_l\); a Porsche divulga apenas descrições qualitativas de maior constância de performance aero e melhor equilíbrio em relação ao modelo anterior.[^27][^3][^5]

Para construir um mapa aero utilizável, é necessário combinar:

- Dados públicos de 992 GT3/GT3 RS de rua (Cd e downforce).[^28][^29][^30]
- Análises técnicas de aerodinâmica GT3 em geral.[^31][^32][^33]
- Escalonamento de modelos genéricos para a silhueta 911 GT3 R.

### Valores de referência (modelo estimado)

Valores abaixo referem‑se a um modelo de túnel de vento genérico de GT3 de motor traseiro, **escalado** para o 992; devem ser tratados como **estimativas** para inicializar o simulador.

- **Coeficiente de arrasto \(C_d\):**
  - Valor proposto: \(C_d \approx 0{,}38\) em configuração de *downforce* médio (sem equivaler diretamente ao Cd de rua, que inclui compromissos de NVH e consumo).[^29][^28]
  - Nota: análises do 992 GT3 RS mostram Cd efetivo maior em trim de alta carga (≈0,47-0,53), com possibilidade de redução via DRS; um valor 0,38 para o GT3 R implica suposição de pacote de corrida mais eficiente em arrasto relativo ao downforce.[^30][^29]

- **Coeficiente de sustentação total \(C_l\) (downforce):**
  - Valor proposto: \(C_l \approx -3{,}20\) a 200 km/h com *ride height* otimizado.
  - Esse valor é significativamente mais agressivo que o \(C_l\) típico de carros de rua (≈ −1,0 para o 992 GT3 RS em alta carga) e deve ser visto como *upper bound* de engenharia para simulações extremas.[^31][^29][^30]

- **Aero balance:**
  - Valor proposto: **≈ 42% frente / 58% traseira** em condição de referência, consistente com um carro de motor traseiro com grande asa e difusor.[^32][^31]
  - **Classificação:** estimativa; o balance real será ajustado via ângulo de asa, configurando o *range* de 38-45% frente.

### Sensibilidade a rake e altura

Literatura de GT3 indica que a variação de rake (diferença de altura traseira-dianteira) é um dos principais *tuning knobs* de downforce e balance:[^33][^32][^31]

- **Sensibilidade típica:**
  - Proposta: \(\partial C_l / \partial (\text{rake}) \approx -0{,}15\) por grau (isto é, aumentar o rake em 1° aumenta a magnitude do downforce total em ≈ 0,15, até a proximidade do estol do difusor).
  - Estol do difusor ocorre tipicamente na faixa de 1,5-2,0° de rake estático, dependendo da altura absoluta e do design do assoalho.[^33][^31]

Para implementação, recomenda‑se um mapa tabulado \(C_d, C_{l,f}, C_{l,r}\) em função de \(h_f, h_r\) e yaw, com estes valores servindo de âncoras centrais a serem refinadas via CFD ou correlação com dados de telemetria.[^32][^31]

***

## S4, Motor 4,2 L Flat‑6 (MDG.4)

O MDG.4 é um seis cilindros boxer aspirado, 4.194 cm³, com borboletas individuais e rotação máxima em torno de 9.250 rpm, projetado para aplicações GT3.[^2][^3][^5][^1]

### Mapa de torque parcial

Para fins de simulação veicular, assume‑se uma decomposição:

\(T(\omega, \alpha) = T_{max}(\omega)\, f(\alpha)\)

onde \(T_{max}(\omega)\) é a curva de torque plena carga (já medida/fornecida) e \(\alpha\) representa o comando de borboleta/pedal.

- **Função \(f(\alpha)\) proposta:**
  - Adota‑se uma forma não linear suave, por exemplo \(f(\alpha) \approx \sin(\alpha)\) em radianos para borboletas individuais *racing*, de modo que pequenos movimentos de pedal produzam resposta progressiva e ainda assim se atinja \(f(\alpha) \approx 1\) próximo de WOT.
  - Alternativamente, um mapeamento \(f(\alpha) = \alpha^{1{,}5}\) ou \(\alpha^2\) em \([0,1]\) pode ser usado para aproximar a calibração de torque desejado no pedal, conforme prática de calibração de motores de competição.[^34][^35]

Este formato é uma **hipótese de modelagem**; o ajuste fino deve ser feito com base em dados de dinamômetro e telemetria pedal→aceleração.[^35]

### FMEP (Friction Mean Effective Pressure), modelo Chen-Flynn

A modelagem de perdas mecânicas utiliza o conceito de **FMEP (Friction Mean Effective Pressure)**, amplamente documentado em literatura de motores. O modelo clássico de Chen-Flynn representa o FMEP como função da rotação:[^34][^35]

\(FMEP = A + B\,N + C\,N^2\)

onde \(N\) é a rotação (por exemplo, em mil rpm) e \(A, B, C\) são coeficientes calibrados em bancada de ensaios.[^36][^37][^35]

- **Parâmetros propostos (estimativa):**
  - \(A = 0{,}3\ \text{bar}\)
  - \(B = 0{,}0005\ \text{bar/rpm}\)
  - \(C = 1{,}0\times 10^{-7}\ \text{bar/rpm}^2\)

Esses valores estão na ordem de grandeza usual para motores NA de alta rotação, mas são estritamente **estimativas** até serem ajustados a dados reais de FMEP do MDG.4.[^35][^36][^34]

O torque de fricção equivalente em virabrequim é:

\(T_{fric}(N) = \dfrac{FMEP(N)\,V_d}{4\pi}\)

onde \(V_d\) é o deslocamento total do motor.[^35]

### Inércia rotacional do conjunto motor

Não há dados oficiais de inércia do MDG.4, mas a literatura sobre motores de competição fornece ordens de grandeza para motores similares.[^12][^34]

- **Valor proposto para simulação:** \(I_{engine} \approx 0{,}12\ \text{kg·m}^2\) para o conjunto virabrequim/volante leve.
- Este valor pretende representar uma inércia bastante ágil, típica de volante de corrida, e deve ser ajustado via ensaios de *spin‑down* (tempo de desaceleração de rotação em neutro) ou correlação com transientes 0-X km/h.[^34]

Na arquitetura do modelo 14‑DOF, a inércia adicional de cambota, embreagem e eixo primário refletida às rodas pode ser incorporada como inércia equivalente na transmissão, preservando \(I_{engine}\) como inércia efetiva do nó motor.[^12][^34]

***

## S5, Freios (AP Racing / Pagid RSL29)

O sistema de freios do 992 GT3 R combina hardware de corrida com controle ABS Bosch, utilizando discos ventilados e pastilhas endurance como Pagid RSL29.[^38][^3][^1][^2]

### Dimensões e massa dos discos

Segundo a ficha técnica Porsche:[^3][^1]

- **Dianteiros:** discos de aço ventilados, multi‑peça, **≈ 390 mm × 36 mm** (35,7 mm na especificação oficial).[^1][^3]
- **Traseiros:** discos de aço ventilados, multi‑peça, **≈ 370 mm × 32 mm** (32,1 mm na especificação oficial).[^3][^1]

Com base em catálogos AP Racing para discos de dimensões próximas, propõem‑se massas típicas:[^39][^40]

- **Massa dianteira por disco:** \(\approx 8{,}5\ \text{kg}\), estimativa dentro do intervalo usual de 8-10 kg para discos 380-390×35-36 mm.[^39]
- **Massa traseira por disco:** \(\approx 6{,}5\ \text{kg}\), estimativa dentro do intervalo de 6,5-8,5 kg para discos 355-370×32 mm.[^40][^39]

### Pastilhas Pagid RSL29, µ vs temperatura

A Pagid RSL29 (endurance) é amplamente usada em GT3 e possui documentação detalhada de atrito vs temperatura.[^41][^42][^43][^44]

- **Coeficiente de atrito operacional:**
  - µ ≈ 0,40 em baixa temperatura.
  - µ ≈ 0,43 a ~100 °C.
  - µ ≈ 0,47 a ~300 °C.
  - Pico em torno de µ ≈ 0,49 por volta de 500-550 °C.
- **Faixa térmica de trabalho:** 400-700 °C para operação contínua, com picos até ~750 °C por curtos períodos.[^43][^44]

Assim, um intervalo **µ ≈ 0,40-0,48** é adequado como faixa operacional típica no modelo, com µ(T) ajustado conforme as curvas Pagid.[^42][^44]

### Coeficiente de convecção e área de atrito

Estudos CFD de discos automotivos indicam coeficientes convectivos na faixa 80-200 W/m²K para discos ventilados de carros de passeio, aumentando com dutos direcionais e velocidades maiores.[^45][^46]

Para um GT3 com dutos de refrigeração forçada, propõe‑se:

- **Convecção efetiva (lumped):**
  - \(h \approx 120{-}150\ \text{W/m}^2\text{K}\) como valor conservador para o modelo térmico zero‑dimensional.
  - Esses valores substituem o default simplificado de ~60 W/m²K de modelos genéricos, mantendo coerência com ordens de grandeza CFD.[^46][^45]

- **Área de atrito efetiva:**
  - Valor proposto: **≈ 0,094 m²** (área nominal de contato da pastilha por eixo, combinando ambos os lados do disco), estimativa derivada de dimensões típicas de pastilhas GT3 usadas com discos 390/370 mm.[^40][^39]

### Questão de validação

Os parâmetros de freio e motor acima substituem valores genéricos como massa de disco 8 kg, área 0,12 m² e coeficiente de convecção 60 W/m²K, fornecendo um ponto de partida mais alinhado com hardware GT3.[^45][^46][^39][^40]

*Como você planeja validar a consistência destes parâmetros de freio e motor em relação ao seu modelo de inércia atual?*

---

## References

1. [Technical data Porsche 911 GT3 R (992) model year 2023](https://www.loveforporsche.com/technical-data-porsche-911-gt3-r-992-model-year-2023/) - Technical data Porsche 911 GT3 R (992) model year 2023

2. [Porsche 911 GT3 R (992.1) (2023 - 2025)](https://www.stuttcars.com/porsche-911-gt3-r-992-1/) - In the summer of 2022, Porsche unveiled the 992 generation of the 911 GT3 R. The car featured a bigg...

3. [Presse-Information](https://newsroom.porsche.com/dam/jcr:2bd9333a-438a-46c8-8cc2-9fa611bf876c/250808d_Technische%20Daten%20911%20GT3%20R26.pdf)

4. [[PDF] Balance of Performance for 2022-2027 FIA GT3 Specifications](https://api.fia.com/system/files/documents/2025-11-14_fia_bop_gt3_gtwc_v4_0.pdf)

5. [Debut for the newest generation of the Porsche 911 GT3 R](https://newsroom.porsche.com/en/2022/motorsports/porsche-911-gt3-r-generation-992-customer-racing-car-premiere-29201.html) - The new Porsche 911 GT3 R will be unveiled to the public at this year’s 24 Hours of Spa-Francorchamp...

6. [How close is the 992 to being 'mid engined'](https://www.reddit.com/r/Porsche/comments/17ba5ry/how_close_is_the_992_to_being_mid_engined/)

7. [Polar Moment of Inertia Calculation](https://speed-wiz.com/calculations/chassis/polar-moment-inertia.htm) - Speed-Wiz polar moment of inertia calculation

8. [How To Calculate Centre of Gravity Position](https://suspensionsecrets.co.uk/how-to-calculate-centre-of-gravity-position/) - Below is the technique used to calculate the static centre of gravity position of your car. Equipmen...

9. [Ferrari 296 GT3 Technical Insight - Racecar Engineering](https://www.racecar-engineering.com/articles/ferrari-296-gt3-technical-insight/) - Ferrari's 296 GT3 is the Prancing Horse's new GT weapon. Here's a precis of the main story in Raceca...

10. [Center of Gravity](http://forums.pelicanparts.com/porsche-911-technical-forum/213636-center-gravity.html) - Anybody know where on the z-axis the Center of Gravity is on a 911?

11. [911 CG height](http://forums.pelicanparts.com/porsche-autocross-track-racing/597864-911-cg-height.html) - Searched but did not find what I wanted. Anyone have some partially substantiated and somewhat educa...

12. [Moment of Inertia Summary](https://fr.scribd.com/document/273031275/Moment-of-Inertia-Summary) - The moment of inertia measures an object's resistance to changes in rotation. It is calculated as th...

13. [Michelin Motorsports Tires](https://trackdaytire.com/wp-content/uploads/2024/08/Michelin_Motorsports_Quick_Reference.pdf)

14. [Michelin Tires](https://sascosports.com/tires_search_results.asp?tire_manufacturer=Michelin) - Slick, Grooved. Michelin, Pilot Sport ... 30/68-18, 12.5, 12.5, 26.9, 13.1, 11.7. Michelin, DPI, LMP...

15. [30/68-18 TL PILOT SPORT CUP HARD RFID COMPETITION](https://chassis-simulation-datasets.michelin.com/Tires/18035-112873-30-68-18-tl-pilot-sport-cup-hard-rfid-competition-mf-tyre-52-hot.html) - 30/68-18 TL PILOT SPORT CUP HARD RFID COMPETITION - MF-Tyre 5.2. Slip ratio (%) 100 Frequency (Hz) 8...

16. [Tire - Michelin Engineering & Services](https://engineering-and-services.michelin.com/mesures-et-modeles/tire/) - MICHELIN Engineering & Services provides you with Michelin resources for testing, as well as special...

17. [Reifen - Michelin Engineering & Services](https://engineering-and-services.michelin.com/mesures-et-modeles/reifen/?lang=de) - Michelin Engineering & Services bietet Reifendaten für die Simulation des Fahrzugsverhaltens an.Dazu...

18. [MF-Tyre/MF-Swift 6.2 Equation Manual | PDF | Velocity](https://www.scribd.com/document/860740568/MF-Tyre-MF-Swift-6-2-Equation-Manual) - The document is the equation manual for MF-Tyre/MF-Swift 6.2, detailing the Magic Formula, which mod...

19. [Documentation](https://mfeval.wordpress.com/index/) - MFeval (Magic Formula evaluation) has been created to provide a robust way to evaluate Magic Formula...

20. [MF-Tyre/MF-Swift 6.2](https://functionbay.com/documentation/onlinehelp/Documents/Tire/MFTyre-MFSwift_Help.pdf) - “Estimated combined slip” can be turned on by setting the combined slip coefficients in the Tyre Pro...

21. [Simcenter Tire - MF-Tyre/MF-Swift](https://2022.help.altair.com/2022/hwdesktop/mv/topics/motionview/MFTyre-MFSwift_Help.pdf) - When using a reduced parameter file, detailed effects such as combined slip, tire relaxation effects...

22. [6.12.5. Tire Property File (*.tir) - Ansys Help](https://ansyshelp.ansys.com/public/views/secured/corp/v251/en/motion_pre/Tire_Property_File.html)

23. [Tire and Vehicle Dynamics, 3rd Edition](https://www.oreilly.com/library/view/tire-and-vehicle/9780080970165/xhtml/CHP004.html) - Chapter 4 Semi-Empirical Tire Models Chapter Outline 4.1. Introduction 4.2. The Similarity Method 4....

24. [Tyres and degradation models - Formula One Wiki](https://formula1.wiki/index.php?title=Tyres_and_degradation_models)

25. [Magic Formula Tire Model - an overview](https://www.sciencedirect.com/topics/engineering/magic-formula-tire-model)

26. [MFeval - File Exchange - MATLAB Central](https://www.mathworks.com/matlabcentral/fileexchange/63618-mfeval) - The toolbox contains the function with the same name (mfeval.m) used to evaluate tyre property files...

27. [Porsche 911 GT3R - Racecar Engineering](https://www.racecar-engineering.com/articles/gt/porsche-911-gt3r/) - Porsche's GT racing’s most famous car, the GT3 gets its 992 upgrade.

28. [911 GT3 RS](https://newsroom.porsche.com/dam/jcr:1d390f77-93c3-49c0-89c7-634f5f02b26a/S22_3515_en.pdf)

29. [Porsche 911 (992) GT3 RS - FIRST LOOK (Technical Analysis)](https://www.youtube.com/watch?v=6TmoIx7bia8) - Let's have a closer look at the new Porsche 992 GT3 RS.

How does the aerodynamics work?
How do the ...

30. [Here's how the aero works on the Porsche 911 GT3 RS | Top Gear](https://www.topgear.com/car-news/speed-week-2023/heres-how-aero-works-porsche-911-gt3-rs) - More than twice the downforce of the old RS, and three times as much as a 'regular' GT3. Here's how ...

31. [992 GT3 & GT3 RS Aero Tech | Issue 299 - Excellence Magazine](https://www.excellence-mag.com/issues/299/articles/992-gt3-gt3-rs-aero-tech) - A look at the aerodynamic advancements that make the current generation GT 911s so wickedly fast. on...

32. [GT3 Aerodynamics | Issue 257](https://www.excellence-mag.com/issues/257/articles/gt3-aerodynamics) - How has the GT3's bodywork evolved?. A look at how the bodywork for Porsche’s Cup car for the street...

33. [Ride Height & Aero - rwmgaming.ca](https://www.rwmgaming.ca/motorsport-academy/engineering-101/ride-height-aero) - In GT3 racing, air is as much a weapon as horsepower, and ride height is the trigger. Ride height is...

34. [[PDF] SIMULATION OF AN ENGINE FRICTION STRIP TEST](https://publications.lib.chalmers.se/records/fulltext/199604/199604.pdf)

35. [Mechanical efficiency and friction mean effective pressure ...](https://x-engineer.org/mechanical-efficiency-friction-mean-effective-pressure-fmep/) - Tutorial on the mechanical efficiency and the friction mean effective pressure (FMEP) of an internal...

36. [A Novel Friction Mean Effective Pressure Model for a Heavy ...](https://saemobilus.sae.org/articles/a-novel-friction-mean-effective-pressure-model-a-heavy-duty-diesel-engine-neural-network-applications-heat-release-rate-profile-optimization-03-18-01-0008) - The prediction of friction mean effective pressure (FMEP) is important when engine performance is es...

37. [Engine optimization model for accurate prediction of friction ...](https://pureportal.strath.ac.uk/en/publications/engine-optimization-model-for-accurate-prediction-of-friction-mod)

38. [RSL 29](https://www.pagidracing.com/racing-brake-pads-products/rsl-29) - DESCRIPTION. RSL 29 features very good modulation and release characteristics. It is a low metallic ...

39. [Brake Discs](https://apracing.com/drawings/2018%20Product%20Catalogue/Brake%20Discs.pdf) - This section on ventilated brake discs provides dimensional details, as well as information on face ...

40. [AP Racing - Catalogue 2015](https://www.scribd.com/doc/251937419/AP-Racing-Catalogue-2015) - AP Racing - Catalogue 2015

41. [1](https://www.epartrade.com/uploads/contents/c1df9f2e-6412-11e8-be4b-560001755c9c/2021/01/PAGID_Racing_Catalog_2021_EN.pdf)

42. [Friction Coefficients by Temperature | PDF - Scribd](https://www.scribd.com/document/975429109/Pagid-Product-Characteristics) - The document presents a comparison of the coefficient of friction for various racing compounds (Endu...

43. [racing brake products - pads](https://cdn.prod.website-files.com/6731cc91371547226bdaff03/679e21e75e4c36cf858413e1_PAGID_Racing_Highlights_2022.pdf) - It features a low heat conductivity and a flat friction curve up to high temperature levels. FRICTIO...

44. [Pagid RSL29 - E1295 - E46 M3/ CSL - Front (OEM Caliper)](https://www.apmotorsport.co.uk/product-page/pagid-rsl29-e1295-e46-m3-csl-front-oem-caliper) - Pagid RS19/29 Yellow Brake Pads (also now known as RSL29) Pagid RS29 is a recent development from th...

45. [Redalyc.CFD modeling and computation of convective heat coefficient transfer of automotive disc brake rotors](https://www.redalyc.org/pdf/5043/504373174002.pdf)

46. [Image Quality Enhancement Using ...](https://www.ije.ir/article_154253_86be69c4303b59c49807272a7494a24c.pdf) - Investigates the brake disc of outboard and inboard view of the disc brake, and computed the tempera...

