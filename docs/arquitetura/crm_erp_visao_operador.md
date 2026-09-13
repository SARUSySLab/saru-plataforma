---
titulo: "CRM & ERP, Visão do Operador + Spec Técnica (DRAFT v0.1)"
data: "2026-07-15"
origem: "_arquivo/saru-KB/50_company/modules/13_crm_erp_visao_operador.md"
status: "stale"
area: "arquitetura_software"
---

# CRM & ERP, Visão do Operador + Spec Técnica (DRAFT v0.1)

> Data: 2026-07-15 · **Parte A** = visão bruta de produto do operador (Vitor), fonte da verdade de
> intenção, não mexer. **Parte B** = spec técnica DRAFT escrita p/ discussão, **@viniciusvieira00
> valida, corrige e bate o martelo nos pontos abertos (§B7)**.
> Stack já existente no `saru-os` (base da spec): hub Next.js 15 + FastAPI + PostgreSQL/TimescaleDB +
> Redis; auth funcional; telemetry-api real e testada; 5 módulos scaffolded (LTS/SA/SD/CRM/ERP).
> Regra do workspace: banco = PostgreSQL (SQLite nunca).

---

## PARTE A, Visão de produto do operador

### A1. Princípio (não negociável)

**Funcional e bem feito, não vitrine.** CRM e ERP precisam sair do scaffold e virar operação real,
com **tudo sincronizado para cada caso e tipo de uso**, o comportamento do sistema muda conforme
**assinatura, perfil e contexto** do usuário.

### A2. Casos de uso que CRM/ERP precisam cobrir

| Caso (persona) | CRM registra | ERP registra |
|---|---|---|
| **Cliente track day (P3, foco MVP)** | Evento participado → relatório entregue → follow-up → recorrência; histórico de voltas/relatórios; oficina que indicou (B2B2C) | Faturamento por evento/pacote; custo de atendimento; comissão de parceiro |
| **Equipe B2B** (Perez/Copa Truck agora; Car Racing/Stock Car futuro) | Contrato, contatos da equipe, entregas por etapa, telemetria vinculada ao cliente | Billing recorrente/por etapa, contratos, notas |
| **Aluno curso Hase (P4)** | Matrícula, progresso, conclusão/certificado | Receita do curso, turmas/cohorts |
| **Sim racer (P2)** | Assinatura, tier, **pontuação/badges/colecionáveis**, recompensas resgatadas | Estoque de brindes físicos de parceiros/sponsors; custo de recompensas |
| **Parceiro/patrocinador** | Cotas, ativações, leads gerados, contrapartidas | Brindes fornecidos, repasses, sponsorships |

### A3. Sincronização (requisito central do operador)

- **Perfil único cross-módulo:** mesmo usuário aparece em LTS/SA/CRM com estado consistente
  (evento no LTS/SA reflete no CRM sem ação manual).
- **Assinatura/tier controla o produto:** gating de features por plano (o que P2 free vê ≠ P2 pago ≠
  equipe Pro ≠ cliente consultoria).
- **Gamificação vive no perfil (CRM)** e fecha o loop com recompensas reais, resgate de consultoria,
  brinde de parceiro, item colecionável → baixa/registro no ERP.
- Nada duplicado, nada digitado 2×: uma fonte de verdade por entidade (usuário, contrato, evento).

---

## PARTE B, Spec técnica DRAFT v0.1 (p/ Vinicius validar)

### B1. Entidades núcleo (data model v0)

| Entidade | Papel | Campos-chave (mínimo) | Dono |
|---|---|---|---|
| `User` | Pessoa física (P2/P3/P4, membro de equipe) | id, email, perfil, gamification_profile_id | Auth/CRM |
| `Organization` | Equipe B2B, oficina, organizador, sponsor | id, tipo (`team`/`shop`/`organizer`/`sponsor`) | CRM |
| `Membership` | user ↔ org + papel | user_id, org_id, role | Auth |
| `Subscription` | Plano ativo de user OU org | owner (user\|org), tier, status, período | Billing |
| `Lead`/`Deal` | Pipeline comercial (lead → oportunidade → cliente) | origem (oficina/evento/IG), estágio, valor | CRM |
| `Event` | Track day / etapa de campeonato | data, pista, organizador_id | CRM |
| `Deliverable` | Relatório, análise, sessão de coaching | event_id, cliente, tipo, status, link p/ dado (SA/LTS) | CRM |
| `Enrollment`/`Progress` | Curso Hase (P4) e minicursos (P2) | user_id, curso, % progresso, certificado | CRM |
| `GamificationProfile` + `Badge`/`Collectible` | Pontuação P2 | pontos, badges[], itens[] | CRM |
| `Reward`/`Redemption` | Catálogo e resgate de recompensas reais | tipo (consultoria/brinde físico/digital), custo, estoque_ref | CRM→ERP |
| `Contract`/`Invoice` | Comercial/fiscal | org\|user, valores, moeda (BRL/USD), status | ERP |
| `InventoryItem` | Brindes físicos de parceiros | sku, qtd, sponsor_id, custo | ERP |
| `PartnerQuota` | Cotas/contrapartidas de sponsor | sponsor_id, cota, ativações, saldo | ERP |

### B2. Identidade, multi-tenancy e RBAC

- Tenancy por `org_id` em toda query de dado de equipe; indivíduo (P2/P3/P4) opera sem org (FK nula),
  **sem** org pessoal implícita (menos linhas, menos joins, validar).
- Roles mínimos: `saru_admin`, `saru_engineer` (atende clientes), `org_owner`, `org_member`,
  `customer` (individual), `partner` (visão restrita das próprias cotas/leads).
- Reusar o auth existente do hub; RBAC = claims no token + checagem por rota no FastAPI.

### B3. Gating por assinatura (liga com o pricing pack)

- Tiers = saída da [matriz de preço](12_pricing_decision_pack.md) §4, **uma** tabela `tier → features`
  no backend (fonte única), exposta ao hub via endpoint/claims; front nunca decide gating sozinho.
- Exemplos de feature flag: nº de análises/mês (P2 free), acesso a relatório interpretado (P3),
  multi-user + simulações (P1 Pro), minicursos × curso completo (P4).

### B4. Sincronização entre módulos (implementa A3)

- **Proposta V1:** monolito modular + **outbox pattern no PostgreSQL** (tabela `domain_events` + worker), LTS/SA emitem `analysis_completed`, CRM consome e atualiza `Deliverable`/pontuação. Simples, transacional,
  auditável; Redis já existe se precisar de fan-out depois.
- Alternativas (decisão Vinicius): Redis Streams (mais infra, menos acoplado) · webhooks internos (mais
  frágil). Anti-requisito: nada de fila externa gerenciada no V1.

### B5. Billing

- Necessidades: recorrente BRL (P1/P2), avulso por evento (P3), one-time/cohort (P4), invoice manual
  USD/EUR (consultoria intl, V1 manual).
- Gateway BR a decidir (Vinicius): Stripe BR × Mercado Pago × Pagar.me, critério: assinaturas + PIX +
  split p/ comissão de oficina (B2B2C) no roadmap.
- `Subscription.status` é a entrada do gating (B3); dunning simples no V1 (aviso + downgrade p/ free).

### B6. Corte V1 × V2 (proposta, simplicity first)

| | Entra | Fica fora |
|---|---|---|
| **V1** | User/Org/Membership/Subscription + gating por tier; pipeline Lead→Deal simples; Event+Deliverable (fluxo P3 completo: evento → relatório → follow-up); Enrollment básico; Invoice via gateway/link | Colecionáveis e loja de rewards; estoque de brindes (ERP); portal do parceiro; rev-share automático; NF-e automática |
| **V2** | Gamificação completa (badges/colecionáveis/resgate), `InventoryItem`+`Redemption`, `PartnerQuota`/portal sponsor, split/rev-share organizador, fiscal automatizado |, |

Racional: V1 destrava o **foco MVP (P3)** e o contrato B2B atual; gamificação P2 só monetiza depois
que a matriz de preço fechar a margem de rewards (pack §3.5).

### B7. Decisões do Vinicius (bater o martelo)

- [ ] Data model B1: aprovar/ajustar (esp. indivíduo sem org vs org pessoal).
- [ ] Mecanismo de sync B4: outbox Postgres (proposta) × Redis Streams × outro.
- [ ] Gateway de billing B5 (assinatura + PIX + split futuro).
- [ ] Onde vive o serviço: dentro do FastAPI existente (módulo) × serviço novo.
- [ ] Corte V1×V2 (B6): confirmar ou mover itens.
- [ ] Tabela `tier → features` inicial (depende da matriz de preço, pack §4).

### B8. Critério de pronto

- [ ] Vinicius devolve B7 respondido → spec vira issue/épico no `saru-app` (spec canônica migra p/
      `saru-docs`; este módulo permanece como registro de visão + rascunho).
- [ ] Fluxo P3 de ponta a ponta descrito e aceito: evento → dado (SA) → relatório (Deliverable) →
      cobrança (Invoice) → follow-up (CRM) sem redigitação.
