---
titulo: "SARU, Documento Master de Produto e Negócios"
data: "2026-07-16"
origem: "_arquivo/saru-KB/50_company/SARU_MASTER_PRODUTO_NEGOCIOS.md"
status: "vigente"
area: "negocio"
---

# SARU, Documento Master de Produto e Negócios

> **Síntese executiva única** (pedido original do operador, consolidando os módulos GTM 09-11 de 2026-07-15
> + base 01-08). Profundidade e fontes: [Fase 1, mercado/personas](modules/09_gtm_fase1_mercado_e_personas.md) ·
> [Fase 2, pitch/narrativa](modules/10_gtm_fase2_pitch_e_narrativa.md) ·
> [Fase 3, aquisição/canais](modules/11_gtm_fase3_aquisicao_e_canais.md) · [Brand DNA](SARU_BRAND_DNA.md).
> Regra-mestra herdada da Fase 2: **o pitch só afirma o que o código sustenta hoje.**

## 1. Posicionamento, o "gap do meio"

Física validada nível topo de mercado (roadmap 14-DOF, Pacejka térmico, aero 4D) entregue como
**web/SaaS colaborativo a preço de equipe nacional/GT**. As camadas existentes deixam o meio vazio:

| Camada | Player típico | Limitação explorável |
|---|---|---|
| F1-grade cloud | Canopy (Michelin) | Caro, foco fórmula; inacessível p/ equipe nacional |
| Pro desktop | ChassisSim, VI-grade, AVL | Monolítico, licença travada, zero colaboração web |
| Entrada grátis | OptimumLap | Ponto-massa ±10%, sem telemetria/nuvem |
| B2C sim racing | Track Titan, Trophi, VRS | Física rasa, zero ponte com pista real |
| B2C track day | Garmin Catalyst, RaceChrono | Hardware fechado ou dado raso sem interpretação |

Moat real (módulo 06): **pneus térmicos + aero 4D + 14-DOF multibody + surrogates ML**, provados
ANTES de escalar Team-Ops, senão vira "clone de EMS". Rival de deep simulation = ARD, não EMS.
*(Identidades verificadas 2026-07-15: **EMS = Effective Motorsport**, SaaS 🇧🇷 de team-ops sem
simulação nem preço público; **ARD** publica £250-670/mês, cliente Hertz Team JOTA, módulo 03 §3.1
e [research](modules/../research/EMS_ARD_pricing_2026-07.md).)*

## 2. Mercado (números-âncora, fontes nos módulos)

- Telemetria motorsport global: **US$ 1,0-1,15 bi (2025/26) → US$ 2,3-2,4 bi (2033-35)**, CAGR 8-9%.
- Metade do mercado é hardware (MoTeC/AiM/Bosch), SARU compete na camada **software/análise**, a que cresce.
- Europa ≈ 45% do mercado → tese de **exportação** (consultoria remota em USD/EUR, custo em BRL).
- VC entrando na base do funil (Track Titan seed US$ 5M c/ Porsche Ventures) valida o setor.
- **Janela Brasília:** Autódromo Nelson Piquet reaberto (nov/2025, 5.384 m, maior traçado ativo do país),
  ≥6 grandes eventos 2026 (GT Series, Endurance, Stock Milhão, F-Truck, NASCAR). Ecossistema local em
  refundação → 12-24 meses p/ virar *o* parceiro técnico antes da concorrência migrar de SP.

## 3. Personas (detalhe no módulo 09 §5)

| Persona | Quem é | Dor central | Ganho SARU | Canal |
|---|---|---|---|---|
| **P1 Ricardo**, chefe de equipe nacional (B2B, prioridade de receita) | Stock/Truck/GT/F4, sem eng. de simulação dedicado | Setup no feeling; ferramenta pro cara/travada | Simulação de setup + telemetria colaborativa por fração de +1 engenheiro | Confiança/indicação: LinkedIn, presença BSB, parcerias |
| **P2 Lucas**, sim racer competitivo (B2C volume) | 18-30, iRacing/ACC, já paga US$ 8-15/mês em tools | Platô; MoTeC i2 hostil; coaching caro | Análise + LTS c/ física real, **pontuação + minicursos + badges/colecionáveis** e recompensas reais (consultorias, brindes de sponsors) | Turbotec (8k), Discord/YouTube |
| **P3 Dr. Fernando**, entusiasta track day (B2C ticket alto) 🎯 **FOCO DO MVP** | 35-60, Porsche/BMW M, **Brasil inteiro**, beachhead BSB | Não sabe por que perde 2 s; Catalyst US$ 1.199 | Relatório pós-track-day interpretado + coaching data-driven; pacotes c/ organizadores/patrocinadores de evento | Oficinas parceiras (B2B2C), grupos de track day, IG |
| **P4 Aluno Hase**, curso (novo 2026-07-15, a detalhar) | Amador buscando formação (piloto competitivo ou trilha de engenharia) | Sem caminho estruturado de evolução | **Curso Hase**; minicursos da pontuação (P2) como degrau | Comunidade P2/P3, Turbotec |

## 4. Oferta e sequência de receita

1. **Consultoria** (imediato): simulação/análise por evento, cash flow + validação da física com dado
   real + case studies. Caminho mais curto = parcerias quentes (lts-copatruck, rede DF, oficinas).
2. **SaaS** (escala): SARU Pro para equipes; análise+LTS B2C (P2/P3). **Hase = curso** (P4; corrigido
   2026-07-15, não é o SaaS de entrada).
3. Exportação: consultoria remota GT3/GT4/TCR (modelo validado por RH Race Engineering, IER).

> ⚠️ **PENDÊNCIA BLOQUEANTE, matriz de preço multi-segmento** (P3 track day = foco; P1 equipe; P2 SaaS;
> P4 curso Hase; organizador B2B2C; consultoria intl USD). Bloqueia landing, slide 7 do deck e campanhas.
> **Decisor: @viniciusvieira00** (delegado 2026-07-15). Insumo completo, benchmarks (incl. research
> track day BR), sinais de WTP, faixas candidatas por segmento e prompt de deep-research p/ dados
> faltantes: [Pricing Decision Pack (módulo 12)](modules/12_pricing_decision_pack.md).

## 5. Narrativa e guardrails

- Tradução técnica→comercial: **ninguém compra DOF, compra décimos e dinheiro economizado**, matriz
  completa no módulo 10 §1; elevator pitches (investidor/B2B/B2C) no módulo 10 §3; deck 12 slides no §4.
- PODE: "solver validado contra referência (±1 s Interlagos)", "física validada vs benchmark publicado
  (Khalil 2018)", "plataforma de telemetria funcional e testada", "roadmap p/ fidelidade de fábrica".
- NÃO PODE: "14-DOF operacional", "precisão de gêmeo digital", "produto em produção com clientes",
  nomes de parceiros como clientes fechados, data dura p/ investidor.
- Identidade *(atualizada 2026-07-15)*: mascote oficial = **saruê** (logo em iteração, #HEX em definição, Brand DNA §1). Mantém-se: discrição visual, agressividade factual; proposta comercial B2B formal
  sóbria (mascote vive na marca/comunidade, não no contrato). Narrativa SARU×Hase → revisar (mód. 10 §5).

## 6. Canais e aquisição (plano completo no módulo 11)

- **Turbotec (8k) mantém o nome** = braço de mídia/comunidade B2C; **@sarudynamics** nasce separado
  (corporativo). Registrar handles (IG/LinkedIn/X/YouTube/domínio) ANTES de qualquer divulgação.
- Instagram: 4 pilares (40% engenharia traduzida, 25% bastidores BSB, 20% produto, 15% comunidade),
  3 Reels/semana; **lead magnet "análise gratuita da sua volta"**.
- LinkedIn B2B: perfil do fundador > página; build in public de engenharia (EN); outbound valor-primeiro
  ("rodei uma simulação do seu carro na pista da próxima etapa"), 20 conexões qualificadas/semana.
- Mídia paga: 1º orçamento em Google Search (intenção) + Meta (remarketing/local); **LinkedIn Ads só
  ≥US$ 2-3k/mês dedicados**. Pré-requisito: landing por persona + pixels + demo 90 s. Split no módulo 11 §4.

## 7. Execução 90 dias e KPIs (detalhe módulo 11 §5-6)

Sem. 1-2 handles+landings+pixels → 2-4 demo 90 s + lead magnet no ar → 3-6 LinkedIn founder + outbound
→ 6-8 ligar Google/Meta → 8-12 revisão CPL + evento BSB. **Alvos 90 dias:** ≥2 calls B2B qualificadas,
≥100 leads B2C, CPL B2C ≤ R$ 15, engajamento Turbotec sem queda pós co-branding.

## 8. Decisões ratificadas (2026-07-15, não reabrir sem motivo novo)

1. Turbotec mantém o nome (braço de mídia); @sarudynamics separado.
2. Pitch só afirma o que o código sustenta; 14-DOF/térmico vendem-se como roadmap.
3. Sequência de receita: consultoria → SaaS.
4. 1º orçamento de mídia: Google Search + Meta; LinkedIn orgânico até US$ 2-3k/mês.
5. Mascote oficial = **saruê albino** (2026-07-15; supersede "felino = comportamento"). Proposta
   comercial B2B formal segue sóbria; logo/#HEX em iteração (SPM backlog).

## 9. Pendências abertas

- [ ] **Matriz de preço multi-segmento** (§4), **decisão do Vinicius**; insumo pronto no
  [Pricing Decision Pack](modules/12_pricing_decision_pack.md) (benchmarks + faixas por segmento + deep-research prompt).
- [ ] **Logo saruê:** iterar variações → decidir #HEX → SVG master + PNG em `brand_assets/` (Brand DNA §1).
- [ ] **Deck visual** (módulo 10 §4) via **Canva MCP**, desbloqueia após logo/#HEX.
- [ ] **CRM/ERP:** [módulo 13](modules/13_crm_erp_visao_operador.md) → spec técnica c/ @viniciusvieira00
  (tiers da matriz de preço = gating).
- [ ] Deep-research complementar de pricing (pack §5), operador/Vinicius roda no Gemini/Perplexity.
- [ ] Dimensionar nº de equipes ativas por categoria nacional (SAM local em contratos), método:
  listas oficiais de pilotos da CBA, contáveis grid a grid (módulo 09 §1, âncoras Brasil).
- [ ] 🔴 **DEADLINE 03/08/2026, Start BSB (Edital FAPDF 11/2026) ABERTO, aceita pessoa física**
  (Eixo II ~R$ 110k, CNPJ só se aprovado): cadastro SIGFAP + submissão com o draft pronto, [kit completo no módulo 15](modules/15_kit_juridico_e_formalizacao.md). (Centelha DF 3 encerrou;
  Centelha 4 provável só 2027.)
- [ ] **Formalização jurídica** ([kit módulo 15](modules/15_kit_juridico_e_formalizacao.md)):
  **cessão de IP entre fundadores JÁ (vale antes do CNPJ, crítico p/ due diligence)** · CNPJ LTDA
  DF (Simples V→III via Fator R) · acordo de sócios (vesting 4+1, deadlock 50/50) · **marca SARU
  INPI 9+42 (~R$ 880 c/ desconto)** + busca pePI manual · registro de software (GRU 730).
- [ ] **Captação:** escada fomento não-dilutivo → aceleradora → anjo/sports-tech mapeada no
  [módulo 14](modules/14_captacao_fomento_e_investimento.md); FINEP = degrau 2027 (exige CNPJ+receita).
- [ ] Revisão Turbotec em 6 meses: se >30% do engajamento vier de conteúdo SARU → avaliar "Turbotec by SARU".
- [ ] Manter `saru-docs` sincronizado (1ª leva feita 2026-07-15, `c4cae3a`), atualizar pós-decisão de pricing.
