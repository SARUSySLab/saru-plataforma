---
titulo: "3. Análise Competitiva"
data: "2026-07-16"
origem: "_arquivo/saru-KB/50_company/modules/03_3_an_lise_competitiva.md"
status: "vigente"
area: "negocio"
---

## 3. Análise Competitiva
*Síntese extraída da avaliação estratégica EMS vs SARU:*
- O diferencial competitivo central da SARU é a **arquitetura orientada a serviços e APIs**.
- Enquanto softwares de mercado rodam estritamente em desktops pesados com licenças travadas, a SARU oferece *Edge Computing* e processamento em nuvem, permitindo colaboração remota entre engenheiros na fábrica e nos boxes.

---

## 3.1 Matriz competitiva com preços verificados (pesquisa 2026-07-15)

> Complementa o "gap do meio" por camada de preço (módulo 09 §2) com o **eixo de integração**.
> Confiança: ✅ página oficial lida diretamente · ⚠️ fonte única/mídia · 🕰 preço histórico.
> Re-checar itens ⚠️ antes de material impresso de investidor.

**Telemetria (análise):** AiM Race Studio 3 **grátis** c/ hardware, só Windows (✅) · MoTeC i2
Standard grátis / **i2 Pro ~€1.053** licença perpétua travada no logger (✅ dealer) · VBOX Circuit
Tools **grátis** c/ hardware Racelogic (✅) · Control/cntrl.io = telemetria celular pro endurance,
preço enterprise oculto (✅). *Leitura:* análise básica custa **zero** no mercado, o valor da SARU
está em nuvem multi-fonte + referência simulada + ponte para operação, não em "dashboard melhor".

**Simulação de volta / dinâmica:** **ARD (Applied Racing Dynamics), o rival direto cloud** ✅:
browser, QSS→dinâmico (BETA), sweeps paralelos, telemetria×sim, **£250/420/670/mês** (1/3/5 seats,
créditos: padrão=1, dinâmica=10; Enterprise integra HHDM), cliente Hertz Team JOTA, [research
dedicado](../research/EMS_ARD_pricing_2026-07.md) · ChassisSim Online **US$ 5/sim** (registro
US$ 100 c/ 150 sims ✅; Lite 🕰 ~US$ 2.000+modelagem em 2011) · OptimumG Dynamics/Kinematics/Tire →
assinatura **~US$ 295/ano** (⚠️; OptimumLap grátis) · Canopy (Michelin) créditos cloud sem preço
público (⚠️). *Corredor acessível: US$ 5/uso a ~US$ 300/ano; corredor cloud pro (ARD): £250-670/mês.*

**Sim racing / coaching B2C:** Garage 61 grátis (300M+ voltas), Pro **€5/mês** (✅) · VRS free /
**US$ 4,99 / 9,99/mês** (✅) · Trophi.ai **US$ 89,99/ano**, +Setups 199,99, **Team 3 assentos
249,99/ano**, Professional 699,99 c/ coach humano (✅) · **Track Titan cobra em BRL no Brasil:
Plus R$ 29,99 · Ultra R$ 69,99 · Premium R$ 89,99/mês, anual −20%** (✅, melhor âncora de WTP
B2C nacional; 13 títulos incl. Automobilista 2) · Coach Dave Delta US$ 11,99-12,99/mês (⚠️ blog
do próprio) · Grid & Go US$ 5/10/15/mês (⚠️).

**Operação de equipe (lifing/estoque/"race ops"), o eixo que o módulo 09 não cobre:**

| Player | O que faz | O que NÃO faz | Fonte |
|---|---|---|---|
| **EMS, Effective Motorsport** (🇧🇷; o "EMS" do módulo 06) | Run/setup sheets, pneus c/ lacre, **almoxarifado**, telemetria-viewer (ECU/clima, KPIs), trial 14d s/ cartão | **Não simula**, sem referência simulada nem correlação sim×real; sem preço público | ✅ |
| **Out Lap** (EUA, early access) | Lifing, estoque (oficina/trailer/carro), setup por sessão, análise por **resultados oficiais** IMSA/SRO | **Não ingere telemetria**, não simula | ✅ |
| Trenchant LifeCheck (UK, 1995) | "Padrão da indústria" de lifing, F1/INDYCAR/WRC | Silo puro; sem telemetria/sim; foco elite | ✅ |
| RaceLedger | Lifing SMB (rally): BOM, serial, Vehicle Passport | Single-purpose declarado | ✅ |
| Racing Connected | Supply chain/compras motorsport | Só suprimentos | ✅ |
| RFK Racing (NASCAR) + SYSPRO | Equipe de elite usando **ERP genérico** + integrações sob medida | Não existe ERP nativo dominante nem na elite | ⚠️ |
| **MOVEdot** (movedot.ai) | AI agents p/ eng. veicular (parceiro VI-grade), concorrente do módulo LLM futuro | Sem ops/ERP; watching (90_tools) | ⚠️ |

**White space (tese confirmada, precisão 2026-07-15):** hoje **nenhum player cobre simulação ↔
telemetria ↔ operação correlacionadas num só hub**. Os mais próximos, cada um num eixo: **EMS/
Effective Motorsport (🇧🇷)** = ops + telemetria-viewer, **sem simulação**; **ARD** = simulação +
telemetria-import, **sem ops**; a dupla ARD+HHDM existe só como *integração* Enterprise (2 produtos).
Out Lap analisa por timing oficial sem dado embarcado; Control faz telemetria sem ops; LifeCheck/
RaceLedger são silos. Categoria nascente e price-opaque = validação de timing **e** aviso: o white
space não fica aberto p/ sempre, **e o player de ops mais próximo é brasileiro**.
Riscos da tese: baseline grátis dos incumbentes; EMS adicionar simulação (ou ARD adicionar ops)
antes de nós; executar 3 categorias ao mesmo tempo (mitigação: MVP faz só análise+LTS).
