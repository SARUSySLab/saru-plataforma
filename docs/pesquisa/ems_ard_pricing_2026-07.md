---
titulo: "Research, Item 3 do Pricing Pack §5: EMS e ARD (planos e preços públicos)"
data: "2026-07-16"
origem: "_arquivo/saru-KB/50_company/research/EMS_ARD_pricing_2026-07.md"
status: "vigente"
area: "negocio"
---

# Research, Item 3 do Pricing Pack §5: EMS e ARD (planos e preços públicos)

> Data: 2026-07-15 · Executor: sessão Claude (Vinicius) · Método: 5 ângulos de busca web +
> escavação do histórico git da KB + páginas oficiais renderizadas no browser (site do ARD é SPA).
> Regra do pack: ≥2 fontes por item. Confiança: ✅ página oficial · ⚠️ fonte única/terceiro.

---

## 1. ARD, Applied Racing Dynamics ✅ RESPONDIDO INTEIRO

**Identidade:** [appliedracingdynamics.com](https://appliedracingdynamics.com), plataforma
**cloud-native de dinâmica veicular** ("all in your browser"): QSS lap time, sweep paralelo de
milhares de sims, ride analysis (perfis de pista reais, velocidade de damper, resposta em
frequência), handling/kinematics (yaw-moment), **import de telemetria real + comparação sim×pista**,
histórico/versionamento automático. Fundada **2024**, **sem funding registrado**
([Tracxn ⚠️](https://tracxn.com/d/companies/applied-racing-dynamics/__lNAXOZtgrBU7ffByhy6gXeDtsgIiD53U39eijYvwZA4)).
Cliente-vitrine: **Hertz Team JOTA** (Hypercar/WEC); segmentos Formula/GT/Hypercar/Protótipo.
Cadência de release: **updates a cada ~2 semanas** (jul/2026: overhaul de performance do engine,
"Setup vs Running Conditions", expression editor de aero).

**Preços públicos (✅ [/pricing](https://appliedracingdynamics.com/pricing), lidos 2026-07-15;
mensal cobrado anualmente; −16/17% vs mensal puro; excl. VAT UK):**

| Tier | Preço (anual) | Mensal puro | Seats | Créditos/mês | Diferenciais |
|---|---|---|---|---|---|
| Consultant | **£250/mês** | £300 | 1 | 250 | QSS + kinematics/ride/handling; sweep 1 componente; 2.500 sims armazenadas |
| Team | **£420/mês** | £500 | 3 | 2.000 | sweep 5 componentes; 10k sims |
| **Team+ (most popular)** | **£670/mês** | £800 | 5 | 5.000 | **Dynamic lap time (BETA)**, sweeps ilimitados, **API**, Discord dedicado |
| Enterprise | custom |, | 50 | 10.000 | storage ilimitado, **integração HHDM** |

**Modelo de créditos:** sim padrão (QSS/ride/kin/handling) = **1 crédito** · **lap dinâmica = 10
créditos**; reset mensal sem rollover; top-up in-app. Free start **sem cartão**; programa especial
p/ **Formula Student**.

**Leituras estratégicas p/ SARU:**
1. ARD ocupa HOJE o "gap do meio" cloud que o módulo 09 §2 descreve, a tese da SARU tem
   concorrente direto, ativo e rápido (release quinzenal, JOTA como cliente). Timing importa.
2. **A dupla ARD (sim) + HHDM (team ops) já existe como INTEGRAÇÃO** no tier Enterprise, o
   mercado valida a demanda pelos dois eixos, mas serve em 2 produtos separados. O hub único
   (dual-axis num só lugar, módulo 06) segue sendo o white space da SARU.
3. Corredor de preço B2B real do gap do meio: **£250-670/mês ≈ R$ 1,8-4,9k/mês** (câmbio ~7,3).
   A faixa candidata do pack §4 p/ SARU Pro (R$ 1,5-2,5k/mês) fica **coerente e agressiva**, entrada abaixo do Consultant/Team do ARD, com o argumento Brasil (BRL, suporte local, ops).
4. Dynamic lap-time deles ainda é **BETA** e custa 10× em créditos, a janela de "alta fidelidade
   acessível" (14-DOF validado, Eixo A) continua aberta, MAS o guardrail vale: só vender quando
   validado por canais.

## 2. EMS, ✅ RESOLVIDO (2026-07-15, rev.2): **Effective Motorsport** (effectivemotorsport.com)

**Como foi identificado (sem perguntar ao operador):** o `deep_research_prompts.md` do **commit
inicial do saru-KB** (`323b9e0`, escrito pelo Vitor em 2026-06-26) nomeia por extenso:
*"concorrentes de mercado como ARD (Applied Racing Dynamics), Canopy Simulations e **EMS
(Effective Motorsport)**"*. Confirmado no site oficial (lido 2026-07-15 ✅).

**O que é ([effectivemotorsport.com](https://effectivemotorsport.com) ✅):** SaaS de gestão para
equipes de motorsport, **brasileiro** (site em PT-BR: "Tudo que sua equipe de motorsport precisa",
"Feito para engenheiros de corrida"):
- **Track-ops:** run planner, run sheets, setup sheets (comparação por sessão + export PDF),
  pneus/combustível/timing.
- **Inventário/"ERP":** gestão de pneus (conjuntos, lacre, aprovação) + **almoxarifado completo**
  (estoque, entradas/saídas de peças), bate literalmente com o "(ERP, inventário)" do módulo 06.
- **Telemetria (o "módulo incipiente"):** importa ECU/telemetria/estação meteorológica, gráficos
  em tempo real, KPIs automáticos (tempo/volta, consumo, temperaturas, pressões). **Sem simulação,
  sem referência simulada, sem correlação sim×real.**
- **Preço: NÃO publica**, só "**14 dias grátis, sem cartão**" (3× na home). Sem CNPJ/endereço/
  redes sociais/clientes no site = produto jovem, pré-tração pública.

**Nota de proveniência (2 confusões documentadas para não voltarem):** (a) o *Relatório de
Avaliação Estratégica* bruto (também no commit inicial) descreve "Effective Motorsport → Hevy
Coach / desempenho atlético", não corresponde ao site real; (b) o deep-research Gemini de
2026-07-15 ("Benchmark de Precificação" §3.1) identificou EMS como "Honda eMS SIM-01" (hardware
¥10M), **incorreto**. Este research (site oficial lido direto) é a fonte que vale.

**Leituras estratégicas:**
1. **EMS é o concorrente DIRETO brasileiro do Eixo B (team-ops)**, o alerta do módulo 06 ("não
   virar clone do EMS") é sobre um player nacional real e ativo. O Eixo A validado (simulação
   profunda) é o que a SARU tem e ele não.
2. O white space preciso (módulo 03 §3.1) fica mais nítido: EMS cobre **ops + telemetria-viewer**;
   ARD cobre **simulação + telemetria-import**; ninguém cobre **simulação ↔ telemetria ↔ ops
   correlacionados num hub**, a tese dual-axis segue única, mas com players fortes em cada eixo.
3. Pricing: mais um da categoria team-ops **sem tabela pública**, tabela pública simples
   (princípio §3.6 do pack) segue sendo diferencial de GTM. O trial 14d sem cartão é o mesmo
   padrão do ARD (free start), trial sem fricção é table stakes no nicho.

**Candidato descartado:** HH Data Management (hh-dev.com), perfil parecido (setups/pneus/tasks,
sem preço público, integra com ARD Enterprise), mas não é o "EMS" do módulo 06. Fica mapeado como
player adjacente da categoria.

## 3. Status do item 3 → pack §5

- **ARD: fechado** (identidade + posicionamento + pricing completo, 2 fontes: site oficial ✅ + Tracxn ⚠️).
- **EMS: fechado** (identidade = Effective Motorsport, via commit inicial da KB + site oficial ✅;
  features mapeadas; **sem preço público**, coletar via trial 14d se necessário p/ faixa exata).
- **Item 3 do pack §5: COMPLETO.**
