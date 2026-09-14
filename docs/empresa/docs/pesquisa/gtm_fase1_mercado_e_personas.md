---
titulo: "GTM Fase 1, Pesquisa de Mercado, Oportunidades e Personas"
data: "2026-07-15"
origem: "_arquivo/saru-KB/50_company/modules/09_gtm_fase1_mercado_e_personas.md"
status: "stale"
area: "negocio"
---

# GTM Fase 1, Pesquisa de Mercado, Oportunidades e Personas

> Data: 2026-07-15 · Fonte: pesquisa web cross-checked (≥2 fontes por claim) + auditoria dos módulos 01-08.
> Escopo: base factual para o Documento Master de Produto e Negócios (Fases 2 e 3 constroem em cima).

---

## 1. Tamanho e dinâmica do mercado (TAM/SAM)

| Segmento | Tamanho 2025/26 | Projeção | CAGR | Fonte |
|---|---|---|---|---|
| Telemetria motorsport (global) | US$ 1,0-1,15 bi | US$ 2,3-2,4 bi (2033-35) | 8-8,9% | [market.us](https://market.us/report/telemetry-intelligence-for-motorsport-market/), [Coherent MI](https://www.coherentmarketinsights.com/industry-reports/telemetry-intelligence-for-motorsport-market) |
| Racing telemetry (subsegmento) | US$ 579,5 mi (2025) | US$ 1,49 bi (2035) | 9,9% | [market.us](https://market.us/report/racing-telemetry-market/) |
| Hardware vs software | Hardware = 49,5% do share | Software/análise = espaço em expansão |, | market.us |
| Geografia | Europa ≈ 45% do mercado 2026 |, |, | Coherent MI |

**Leituras estratégicas:**
- Metade do mercado é hardware (MoTeC, AiM, Bosch, Cosworth). A SARU **não compete aí**, compete na camada de **software/análise/simulação**, que é onde o share está crescendo e onde os incumbentes são desktop-legados.
- Europa concentra ~45% do mercado → confirma tese de **exportação** (LinkedIn/Ads internacionais na Fase 3).
- "Team performance optimization" ≈ 41% do mercado de telemetry intelligence em 2026 → exatamente o Eixo A+B da SARU (módulo 06).

**Âncoras Brasil, bottom-up (pesquisa 2026-07-15, fontes CBA oficiais ✅):**
- Teto de gastos **Stock Series: R$ 750 mil/temporada por equipe** (CBA, 2023), declarado "o menor
  entre categorias de Turismo BR" ⇒ as demais custam MAIS. Premissa de software: 0,5-1% do orçamento
  ≈ R$ 3,75-7,5 mil/ano (validar em conversa).
- **Brasileiro de Kart 2025: 600+ inscrições (recorde**; 545 em 2021), 22 categorias; **40+ kartódromos**
  homologados CBA (⚠️ mídia). Base ampla p/ P2/P3/P4 fora do asfalto.
- Método p/ o gap "nº de equipes por categoria" (§6): a CBA publica **listas oficiais de pilotos por
  campeonato**, contar grid a grid (Stock Pro/Series, Truck, F4, GT) dá o SAM sem estimativa de mídia.

## 2. Cenário competitivo por camada de preço (o "gap do meio")

| Camada | Player | Modelo/Preço | Limitação explorável |
|---|---|---|---|
| F1-grade cloud | [Canopy Simulations](https://simulation.michelin.com/canopy) (ex-McLaren, hoje Michelin) | Assinatura + compute credits, nodes em nuvem | Caro, foco fórmula/protótipo; inacessível p/ equipes nacionais |
| Pro desktop | [ChassisSim](https://www.chassissim.com/), VI-grade, AVL | Licença desktop pesada | Monolítico, licença travada, sem colaboração web |
| Entrada grátis | [OptimumLap](https://optimumg.com/product/optimumlap/) (OptimumG) | Grátis, ponto-massa, ±10% | Sem transiente, sem telemetria, sem nuvem |
| B2C sim racing SaaS | Track Titan (~US$ 8/mês, seed US$ 5M c/ [Porsche Ventures](https://techfundingnews.com/track-titan-raises-5m-seed-ai-sim-racing-coach/)), [Trophi.ai](https://www.trophi.ai/pricing-sim-racing) (US$ 15/mês), VRS, Garage 61 (free) | Freemium volume alto | Só sim racing; física rasa; zero ponte com pista real |
| B2C track day hardware | [Garmin Catalyst](https://www.garmin.com/en-US/p/690726/) (US$ 1.199), Apex Pro, RaceChrono (US$ 20 + GPS US$ 80) | Hardware fechado ou app raso | Gap enorme entre RaceChrono (raso) e MoTeC i2 (hostil a leigo) |

**Posição SARU:** o *gap do meio*, física validada nível Canopy (14-DOF, Pacejka térmico, aero 4D) entregue como **web/SaaS colaborativo** a preço de equipe nacional/GT, é o oceano menos disputado. Confirma o moat do módulo 06; agora com evidência de mercado.
**Validação de modelo de negócio:** Canopy prova que *cloud credits + assinatura* funciona no topo; Track Titan prova que freemium funciona na base (e que VC, inclusive Porsche, está financiando o setor).

## 3. Oportunidades locais (Brasília / DF)

**Fato-âncora:** Autódromo Internacional Nelson Piquet reativado em nov/2025 após ~12 anos, com 5.384 m, **maior traçado ativo do país** (supera Interlagos). Calendário 2026 com ≥6 grandes eventos ([Agência CEUB](https://agenciadenoticias.uniceub.br/esportes/autodromo-internacional-nelson-piquet-em-brasilia-tera-ao-menos-6-grandes-eventos-em-2026/)):

| Evento 2026 | Data | Relevância p/ SARU |
|---|---|---|
| GT Series Cup + Paulista de Marcas | 20-22/mar | GT = ICP direto do LTS/SA |
| Endurance Brasil (abertura) | abr | Estratégia de corrida + telemetria = Eixo B |
| SuperBike Brasil | 21-23/ago | Adjacente (2 rodas), baixa prioridade |
| Stock Car, Corrida do Milhão | 27/set | Vitrine máxima nacional |
| Fórmula Truck | 9-11/out | Sinergia parceria `lts-copatruck` |
| NASCAR Brasil | 28-29/nov | Categoria em expansão, equipes menos servidas |

**Implicações:**
- Nenhum player de simulação/engenharia de dados está "instalado" em BSB, pista ficou 12 anos parada, o ecossistema local está sendo **refundado agora**. Janela de 12-24 meses p/ virar *o* parceiro técnico local antes de concorrência migrar de SP.
- Track days no Brasil: inscrição R$ 200-900, cultura em expansão (Festival Interlagos, Club TrackDay, PKM). Público local de BSB com carro esportivo + evento na porta = funil B2C 2.
- Ativos existentes: parcerias `lts-copatruck` e `lts-hase` (derivado prosumer) + rede de consultoria/vendas com empresas de automobilismo do DF + oficinas de performance (canal B2B2C: oficina indica SARU no pacote de preparação).

## 4. Oportunidades globais (exportação)

- **Consultoria de simulação remota** p/ equipes GT3/GT4/TCR, modelo já validado por [RH Race Engineering](https://www.rh-raceengineering.com/) e [IER Simulations](https://www.iersimulations.com/); McLaren Customer Racing terceiriza análise pré/pós-evento. Custo em BRL, preço em USD/EUR = margem cambial estrutural.
- **SaaS de simulação mid-market:** equipes-cliente GT3/GT4, F4, categorias nacionais fora do eixo F1, grandes demais p/ OptimumLap, pequenas demais p/ Canopy.
- **Sequência recomendada:** consultoria (cash flow imediato, valida física com dados reais) → produto SaaS (escala). Consultoria também gera os *case studies* que o SaaS precisa p/ vender.

## 5. Personas

### P1, B2B: "Ricardo, o Chefe de Equipe" (prioridade de receita)
- **Perfil:** 38-55, dono/chefe de equipe em Stock Car/Stock Light, Copa Truck, GT Series, F4 ou endurance nacional. Orçamento apertado vs categorias europeias; 1 engenheiro de pista generalista, sem engenheiro de simulação dedicado.
- **Dores:** ferramenta pro = licença desktop cara + curva de aprendizado; setup decidido "no feeling" + histórico; perde posições p/ equipes com engenharia de dados melhor.
- **Ganho SARU:** simulação de setup pré-evento + análise de telemetria colaborativa (nuvem, multi-user) por fração do custo de contratar +1 engenheiro.
- **Gatilho de compra:** case comprovado (delta de tempo de volta em categoria que ele respeita). Compra por **confiança + indicação**, não por anúncio. Canal: LinkedIn + presença física em BSB/eventos + parcerias existentes.

### P2, B2C: "Lucas, o Sim Racer Competitivo"
- **Perfil:** 18-30, iRacing/ACC ranqueado, já paga assinatura (iRacing ~US$ 13/mês; benchmark de tools: US$ 8-15/mês). Consome conteúdo técnico no Instagram/YouTube/Discord.
- **Dores:** platôs de performance; MoTeC i2 gratuito porém hostil; coaching humano caro (US$ 50-150/h).
- **Ganho SARU** *(corrigido 2026-07-15)*: produto de **análise + LTS** com física real (não heurística de gamer) + **sistema de pontuação** com minicursos embutidos e trilha de evolução do amador → piloto competitivo (ou → engenheiro). Gamificação estilo CS/LoL/Valorant/WoW: badges, itens colecionáveis/personalizáveis e **recompensas reais**, consultorias, brindes de parcerias/sponsorships.
- **Papel estratégico:** volume + comunidade + funil Turbotec (8k). Financia pouco, mas gera prova social, dados e audiência que o B2B enxerga. **Nota:** o derivado Hase **não** é a entrada do Lucas, Hase é **curso**, persona própria (P4 abaixo).

### P3, B2C: "Dr. Fernando, o Entusiasta de Track Day" 🎯 FOCO DO MVP
- **Perfil:** 35-60, profissional liberal/empresário, Porsche/BMW M/preparado; gasta R$ 200-900 por evento + pneus/manutenção sem piscar. Status + evolução pessoal como motivação. Beachhead em BSB, mas a persona existe no país inteiro.
- **Dores:** não sabe *por que* o amigo é 2 s mais rápido; Garmin Catalyst custa US$ 1.199 + importação; dado do RaceChrono é raso e ninguém interpreta pra ele.
- **Ganho SARU:** relatório pós-track-day interpretado ("onde você perde tempo e o que treinar") + coaching data-driven no autódromo. Ticket alto unitário, LTV via recorrência de eventos.
- **Canal:** oficinas de performance parceiras (B2B2C), grupos de track day, Instagram, organizadores e patrocinadores de evento.
- 🎯 **Decisão do operador (2026-07-15): persona mais importante agora, o MVP é para ele.** Escopo = **Brasil inteiro**, não só BSB (Brasília ≠ Brasil; carência de tecnologia/investimento nessa área em todas as regiões, Sul, SP, Nordeste, CO). Frentes a aprofundar: integrações e ferramentas, pacotes comerciais (evento único / temporada / premium c/ coaching presencial), oportunidades e suporte junto a organizadores, **patrocinadores de evento** e parceiros. Deep research nacional **feita** (2026-07-15): resultados em `50_company/research/`, absorvidos no [pricing pack §2](12_pricing_decision_pack.md).

### P4, "Aluno Hase" (curso, persona nova, a detalhar)
- **O que é:** o derivado **Hase é um curso**, não SaaS de entrada (correção do operador, 2026-07-15). Outro tipo de persona vs Lucas (P2).
- **Hipótese de perfil:** amador/entusiasta que quer **formação estruturada**, virar piloto competitivo ou seguir trilha de engenharia de dados de pista. Os minicursos embutidos no sistema de pontuação (P2) funcionam como degrau de entrada p/ o curso completo.
- **Status:** persona a detalhar pelo operador (público exato, formato, preço, certificação).

## 6. Gaps a validar (entrada da Fase 2)
- [ ] Auditar MVP real (saru-os) vs promessas comerciais, o pitch só pode vender o que o GREEN 93,03s sustenta (dívida técnica do 14-DOF documentada em `saru-core-jl/docs/AUDIT-FINDINGS.md`).
- [ ] Precificação: **matriz multi-segmento** (ampliada 2026-07-15; substitui "3 tiers"): track day P3 (MVP) · curso Hase (P4) · equipe Perez/Copa Truck (agora) · Car Racing/Stock Car e outras categorias (futuro) · pilotos e equipes virtuais e reais · consultoria internacional USD. Benchmark Canopy/ChassisSim real segue pendente (não público; obter via trial/contato).
- [ ] Nome/relação Turbotec ↔ SARU Dynamics (decisão de arquitetura de marca, Fase 3).
- [ ] Dimensionar nº de equipes ativas por categoria nacional (Stock/Truck/F4/GT) p/ SAM local em contratos.
