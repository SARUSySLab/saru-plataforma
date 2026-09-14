---
titulo: "Demo de 90 segundos, roteiro de gravação (shot-list)"
data: "2026-07-18"
origem: "_arquivo/saru-docs/docs/produto/demo-90s.md"
status: "vigente"
area: "marca"
---

# Demo de 90 segundos, roteiro de gravação (shot-list)

Vídeo curto para **slide 4 do deck, LinkedIn e mídia paga**. Distinto da
[demo guiada de 8 min](use-cases.md#7-demo-ao-vivo-do-mvp--roteiro-de-8-min) (essa é para call/presencial).
Foco na **persona P3 (track day)**, o comprador do MVP.

## Regras de produção

- **Sempre dado real** (do parceiro, se autorizado; senão o dataset GT7 do repo, `data/samples/*.ld`).
  Nunca a demo sintética (`demoData.ts`), e nunca abrir tela de feature futura (14-DOF, CRM/ERP).
- **Legendas sempre** (ads rodam sem som). A voz-off é opcional; a legenda carrega a mensagem.
- Screencast do app rodando local (1280×800), cursor visível, transições de 0,3 s. Sem stock, sem slop.
- Cada tela que mostra número **declara fonte/solver/confiança** (é o diferencial de honestidade, deixar visível).
- Terminar com CTA único e a régua de honestidade intacta.

## Shot-list (0:00 → 1:30)

| Tempo | Tela (o que aparece) | Legenda / VO | Objetivo |
|---|---|---|---|
| 0:00-0:08 | Fade-in no wordmark **SARU** → corte para um gráfico de telemetria bruto e confuso | "Você foi ao track day. Voltou com dados. E agora?" | Hook: a dor do P3 (dado cru, sem interpretação) |
| 0:08-0:22 | Arrastar um arquivo `.ld` real para a área de upload do **SA** → aparecem voltas detectadas, canais e **qualidade do dado** | "Sobe o arquivo do seu logger. O SARU detecta voltas, canais e qualidade." | Prova UC-01: ingestão real funciona, sem fricção |
| 0:22-0:42 | Selecionar melhor volta × volta-alvo → **delta por curva** (verde ganha / vermelho perde), speed/brake/throttle | "Compare duas voltas. O delta mostra, curva a curva, onde o tempo escapa." | Prova UC-02: comparação acionável (o "por que ele é mais rápido") |
| 0:42-1:02 | Ativar **referência simulada** → overlay real × simulado; destaque no rótulo "referência simulada · solver · confiança" | "Uma referência simulada rastreável, sempre marcada como referência, nunca cronômetro oficial." | Prova UC-03/04 + a régua de honestidade (diferencial) |
| 1:02-1:20 | Clicar **"Baixar relatório track day"** → abre o Markdown: "Sua volta", "Onde você perde tempo (Setor 2)", "O que treinar: 1, 2, 3" | "E leva embora um relatório interpretado: onde você perde tempo e o que treinar." | Prova UC-05 + o produto que o P3 compra (o relatório do E2) |
| 1:20-1:30 | Volta ao wordmark + one-liner + CTA | "SARU, telemetria real vira decisão de pista. **Entre na lista de espera.**" | Fechamento + conversão (mesma CTA da landing) |

## Variações de corte

- **6 s (story/ad):** 0:22-0:42 (delta por curva) + card de CTA. É o momento mais "aha".
- **30 s (LinkedIn B2B):** trocar o fechamento P3 por "por uma fração do custo de mais um engenheiro" e mirar a persona Equipes.
- **Still para slide 4:** frame do overlay real × simulado com o delta em destaque (o rótulo de confiança visível).

## Checklist antes de gravar

- [ ] Stack local no ar (`docker compose up -d`), usuário de demo logado, dataset real carregado.
- [ ] Autorização do parceiro se usar dado dele; senão, dataset do repo.
- [ ] Nenhuma aba de feature futura aberta (14-DOF/CRM/ERP fora do quadro).
- [ ] Legendas conferidas; áudio limpo (se houver VO).
- [ ] Take de backup do relatório já baixado (caso o download falhe no take).
