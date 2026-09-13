---
titulo: "Mercado e Posicionamento"
data: "2026-07-15"
origem: "_arquivo/saru-docs/docs/produto/mercado.md"
status: "vigente"
area: "negocio"
---

# Mercado e Posicionamento

Destilado da pesquisa GTM de 2026-07-15 na SARU Knowledge Base (fontes
cross-checked, >= 2 por claim). Taticas de aquisicao, precificacao e pitch sao
material interno e ficam somente na KB (`50_company/`).

## Numeros-ancora

- Telemetria motorsport global: **US$ 1,0-1,15 bi (2025/26) -> US$ 2,3-2,4 bi
  (2033-35)**, CAGR 8-9%
  ([market.us](https://market.us/report/telemetry-intelligence-for-motorsport-market/),
  [Coherent MI](https://www.coherentmarketinsights.com/industry-reports/telemetry-intelligence-for-motorsport-market)).
- Cerca de metade do mercado e hardware (MoTeC, AiM, Bosch, Cosworth). O SARU
  **nao compete ai**, compete na camada de software/analise/simulacao, que e
  onde o share cresce.
- Europa concentra ~45% do mercado: sustenta a tese de exportacao (consultoria
  remota cobrada em USD/EUR com custo em BRL).
- VC esta financiando o setor: Track Titan levantou seed de US$ 5M com
  participacao da Porsche Ventures.

## Cenario competitivo por camada de preco

| Camada | Player | Limitacao exploravel |
|---|---|---|
| F1-grade cloud | [Canopy Simulations](https://simulation.michelin.com/canopy) | Caro, foco formula/prototipo; inacessivel para equipe nacional |
| Pro desktop | ChassisSim, VI-grade, AVL | Monolitico, licenca travada, sem colaboracao web |
| Entrada gratis | [OptimumLap](https://optimumg.com/product/optimumlap/) | Ponto-massa +/-10%, sem transiente, telemetria ou nuvem |
| B2C sim racing SaaS | Track Titan, Trophi, VRS, Garage 61 | Fisica rasa; zero ponte com pista real |
| B2C track day | Garmin Catalyst (US$ 1.199), RaceChrono | Hardware fechado ou dado raso sem interpretacao |

**Posicao SARU: o gap do meio.** Fisica com validacao seria (roadmap 14-DOF,
pneu termico, aero) entregue como web/SaaS colaborativo a preco de equipe
nacional/GT. Canopy prova que assinatura + creditos de computo funciona no
topo; Track Titan prova que freemium funciona na base.

## Janela Brasilia

Autodromo Internacional Nelson Piquet reativado em nov/2025 apos ~12 anos, com
5.384 m, maior tracado ativo do pais. Calendario 2026 com >= 6 grandes
eventos (GT Series, Endurance Brasil, Stock Car Corrida do Milhao, Formula
Truck, NASCAR Brasil)
([Agencia CEUB](https://agenciadenoticias.uniceub.br/esportes/autodromo-internacional-nelson-piquet-em-brasilia-tera-ao-menos-6-grandes-eventos-em-2026/)).

O ecossistema local esta sendo refundado agora: janela estimada de 12 a 24
meses para se estabelecer como parceiro tecnico local antes da concorrencia
migrar de SP.

## Sequencia de receita

1. **Consultoria** (caixa imediato): simulacao e analise por evento; valida a
   fisica com dado real e gera case studies.
2. **SaaS** (escala): plataforma para equipes; derivado de entrada B2C
   ("Hase") com fisica simplificada.
3. **Exportacao**: consultoria remota para GT3/GT4/TCR, modelo ja praticado
   por RH Race Engineering e IER Simulations.

Regra herdada dos gates de produto: cada claim comercial deve respeitar
[Landing e narrativa](landing.md); nada acima do nivel de validacao.

## Onde aprofundar (interno, KB)

- [GTM Fase 1, mercado, oportunidades e personas](https://github.com/SARUSySLab/saru-KB/blob/develop/50_company/modules/09_gtm_fase1_mercado_e_personas.md)
- [Documento Master de Produto e Negocios](https://github.com/SARUSySLab/saru-KB/blob/develop/50_company/SARU_MASTER_PRODUTO_NEGOCIOS.md)
