---
titulo: "Notas técnicas para fechamento de lacunas do simulador 14-DOF"
data: "2026-07-15"
origem: "_arquivo/saru-KB/20_vehicle_dynamics/research/relatorio_14dof_notas.md"
status: "vigente"
area: "dinamica_veicular"
---

# Notas técnicas para fechamento de lacunas do simulador 14-DOF

Este documento consolida as respostas discutidas sobre Pacejka combined slip, estimativa de momentos de inércia e formulação de envelope g-g-v, além de incorporar o material adicional fornecido pelo usuário. Sempre que uma afirmação vier de fonte externa recuperada nesta sessão, ela é marcada com citação inline. Sempre que vier do texto adicional solicitado pelo usuário sem verificação externa suficiente nesta sessão, ela é marcada como **Estimativa / texto a validar**.

## 1. Pacejka combined slip e domínio de validade

### 1.1 O que ficou sustentado por fonte

A formulação de combined slip em implementações MF derivadas de Pacejka usa funções de ponderação do tipo razão de cossenos com argumento baseado em `atan`, como no caso de `Gxa`, e é apresentada como modelo empírico ajustado a dados, não como lei física universal. [web:30]

A consequência prática é que o modelo deve ser usado dentro da faixa de calibração em slip ratio, slip angle, carga vertical e cambagem; fora dessa faixa, podem surgir comportamentos não físicos por extrapolação. [web:30][web:31][web:66]

Portanto, a leitura correta do domínio de validade no contexto do livro e de implementações correlatas é: os coeficientes `rBx1/rBx2/rCx1/rHx1` e `rBy1/rBy2/rCy1/rHy1` não possuem faixa universal garantida fora do conjunto de dados que os originou. [web:30][web:66]

### 1.2 Sobre o risco de `G < 0`

Se o fator de forma multiplicando o argumento do cosseno for suficientemente alto, a função de ponderação pode cruzar zero quando usada fora da região de ajuste; isso é um problema matemático de extrapolação, não um resultado físico desejado. [web:30]

Assim, a conclusão operacional é que `rC > 1` não é proibido por si só, mas requer controle rigoroso do domínio de entrada e, em muitas implementações, limitação numérica para impedir pesos negativos. [web:30][web:43]

### 1.3 Faixas e prática de implementação acrescentadas pelo usuário

**Estimativa / texto a validar:** não existem faixas universais “de fábrica”, pois são parâmetros de ajuste de curva para casar o modelo com dados de bancada.

**Estimativa / texto a validar:** para pneus de competição modernos, `rBx` geralmente reside entre 0.8 e 1.2, enquanto `rCx` deve permanecer próximo a 1.0.

**Estimativa / texto a validar:** uma prática robusta de implementação é usar saturação, por exemplo `G_eff = max(0, cos(...))`, ou substituir o clamp por função suave se o resolvedor exigir continuidade de derivadas.

## 2. Milliken RCVD e estimativa de `Iz`, `Ix`, `Iy`

### 2.1 O que ficou sustentado por fonte

A estimativa de momentos de inércia por distribuição de massa segue o procedimento clássico de corpo rígido: soma discreta `I = Σ m_i r_i^2` ou forma contínua equivalente, com uso do teorema do eixo paralelo quando necessário. [web:47][web:52]

Isso é compatível com a abordagem usual atribuída ao RCVD para construir `Ix`, `Iy` e `Iz` a partir da localização dos principais grupos de massa no veículo. [web:52][web:63]

### 2.2 Validação de ordem de grandeza para `Iz ≈ 2450 kg·m²`

Com apenas massa total `1345 kg` e entre-eixos `L = 2.507 m`, não existe validação única de `Iz`, porque o valor depende fortemente da distribuição longitudinal e lateral das massas e dos overhangs. [web:47][web:52]

Um modelo simplificado do tipo massa concentrada nos eixos pode servir como cheque de plausibilidade, mas não fecha o valor real para um GT3 de motor traseiro. [web:52][web:63]

Logo, `Iz ≈ 2450 kg·m²` é plausível como valor de trabalho, mas não pode ser confirmado nem rejeitado de forma definitiva apenas com `m` e `L`. [web:52][web:63]

### 2.3 Cálculos e heurísticas acrescentados pelo usuário

**Estimativa / texto a validar:** o cálculo simplificado `m_f a^2 + m_r b^2` tende a errar para GT3 de motor traseiro por causa da concentração de massa em overhang traseiro.

**Estimativa / texto a validar:** para `m = 1345 kg` e `L = 2.507 m`, usando distribuição 40/60, obtém-se `Iz ≈ 2028 kg·m²` pelo modelo de massas concentradas nos eixos.

**Estimativa / texto a validar:** uma heurística experimental para GT3 colocaria `Iz` entre `1.8 × m × (L/2)^2` e `2.2 × m × (L/2)^2`, levando a valor da ordem de `3990 kg·m²` com fator 1.9.

**Estimativa / texto a validar:** um `k_z = sqrt(Iz/m)` típico de GT3 estaria em torno de 1.3 m a 1.5 m.

### 2.4 Síntese prática para o simulador

Para fechamento de parâmetro em simulador 14-DOF, a melhor rota é usar o cálculo por distribuição real de componentes como valor inicial e depois correlacionar `Iz` por resposta transitória de yaw rate e lateral acceleration. Isso é coerente com a sensibilidade física do parâmetro e evita fixar um número excessivamente “geométrico”. [web:52][web:63]

## 3. Formulação canônica do envelope `g-g-v`

### 3.1 O que ficou sustentado por fonte

Não há uma fórmula universal fechada para o envelope `g-g-v` de um veículo com load sensitivity e combined slip; a prática canônica é obter a fronteira factível do modelo para cada velocidade. [web:53][web:54][web:66]

Em outras palavras, o envelope é construído como solução quase-estacionária do modelo completo, e não como simples círculo de atrito de ponto-massa. [web:53][web:54]

A dependência de velocidade entra naturalmente pela carga aerodinâmica e pelos efeitos de carga normal sobre a capacidade do pneu, o que altera o envelope em cada valor de `v`. [web:54][web:66]

### 3.2 Formulação operacional recomendada

Em cada velocidade, define-se um problema de equilíbrio em que as forças longitudinais, laterais e o momento de guinada devem fechar simultaneamente sob as restrições impostas pelo modelo de pneus e pela transferência de carga. [web:53][web:54]

Na prática, isso é resolvido por mapeamento QSS, busca em grade ou otimização numérica, produzindo diretamente o mapa `g-g(v)` nativo do modelo de alta fidelidade. [web:53][web:56]

### 3.3 Formulação matemática acrescentada pelo usuário

**Estimativa / texto a validar:** o estado de aderência máxima pode ser escrito como um problema `max a = sqrt(ax^2 + ay^2)` sujeito ao fechamento de `Fz`, `Fx`, `Fy` e `Mz` com `μ_i = Pacejka(Fz_i, κ_i, α_i, γ_i)`.

**Estimativa / texto a validar:** a dependência explícita de velocidade pode ser introduzida por `Fz_total(v) = Fz_static + 1/2 ρ v^2 S Cl`.

**Estimativa / texto a validar:** como `Cl` e aero balance mudam com rake, o envelope `g-g-v` torna-se dinamicamente acoplado com `ax` e `ay`.

**Estimativa / texto a validar:** para implementação, é preferível gerar o mapa por QSS mapping em malha de velocidade e acelerações do que buscar expressão analítica fechada.

## 4. Material adicional do usuário para incorporar no relatório principal

As notas abaixo foram mantidas porque podem ser úteis como hipóteses de trabalho, mas **não foram verificadas externamente nesta sessão**.

### 4.1 Aerodinâmica

**Estimativa / texto a validar:** para GT3 moderno, assumir `Cd ≈ 0.38-0.42` e `Cl ≈ 3.0-3.5` dependendo do rake.

**Estimativa / texto a validar:** gerar `Cl(h_f, h_r, yaw)` por matriz de sensibilidade e interpolação bilinear para evitar descontinuidades no resolvedor 14-DOF.

### 4.2 Motor

**Estimativa / texto a validar:** usar `FMEP = 0.05 + 0.0001N + 0.00000002N^2` como coeficientes médios de Chen-Flynn para motor de corrida aspirado.

**Estimativa / texto a validar:** adotar inércia rotacional do conjunto em torno de `0.035-0.045 kg·m²` e volante de `2.5-3.5 kg` como aproximação inicial.

### 4.3 Massa e CG

O documento FIA GT3 recuperado nesta sessão mostra `homologation weight 1250 kg` para o Porsche 911 GT3 R, o que é referência melhor para peso-base do que valores não homologados. [web:2]

O BoP LMGT3/WEC recuperado nesta sessão mostra o Porsche com `1336 kg` em decisão de 11/04/2025, valor coerente com a ordem de grandeza de massa de corrida/BoP e útil para reconciliar a dúvida `1330` versus `1265+80`. [web:1]

**Estimativa / texto a validar:** altura de CG de `420-450 mm` por tilt test estimado para o 992 GT3 R.

### 4.4 Freios

Há fonte pública encontrada nesta sessão para catálogo AP Racing, útil para fechar massa e geometria de disco por desenho de catálogo. [web:21]

Há também fonte pública com valores de atrito por temperatura associados à Pagid RSL29/RS29 em uso de mercado, útil como ponto de partida para digitalização, embora não substitua uma curva oficial do fabricante. [web:24][web:26]

**Estimativa / texto a validar:** usar `h_c ≈ 80-150 W/m²K` a `150 km/h` para dutos de freio de GT3 como aproximação inicial.

### 4.5 Target profile e driver model

**Estimativa / texto a validar:** varrer `v ∈ [40,260] km/h`, `a_x ∈ [-2.0,2.0] g` e `a_y ∈ [-2.5,2.5] g` em batch QSS.

**Estimativa / texto a validar:** usar controlador preview-follower PID ou LQR para seguir o alvo, de modo a evitar que a calibração agregada de `pDy2` imponha metas inalcançáveis ao driver.

### 4.6 Benchmark por canais

**Estimativa / texto a validar:** em Interlagos, GT3 de corrida operaria em ordem de grandeza de `1.8-2.0 g` lateral em curva rápida e cerca de `-1.8 g` em frenagem forte, com validação preferencial por canais `v`, `a_lat`, `a_long`, `yaw rate` e slip angle quando disponíveis.

## 5. Recomendação de uso no documento mestre

Para evitar misturar evidência com hipótese, o relatório principal deve marcar cada linha em uma destas duas classes:

- FONTE PRIMÁRIA / SECUNDÁRIA VERIFICADA: afirmações ancoradas em literatura ou documento recuperado nesta sessão. [web:1][web:2][web:21][web:30][web:53][web:66]
- ESTIMATIVA DE ENGENHARIA / TEXTO A VALIDAR: hipóteses numéricas, ranges práticos e estratégias de implementação fornecidas pelo usuário ou inferidas sem verificação primária suficiente nesta sessão.

Essa separação é a forma mais segura de transformar as notas acima em base defensável para o simulador 14-DOF sem endurecer números que ainda não foram fechados por homologação, catálogo ou paper. [web:1][web:2][web:30][web:53]
