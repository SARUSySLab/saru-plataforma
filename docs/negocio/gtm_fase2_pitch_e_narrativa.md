---
titulo: "GTM Fase 2, Pitch, Narrativa e Tradução Técnica → Comercial"
data: "2026-07-16"
origem: "_arquivo/saru-KB/50_company/modules/10_gtm_fase2_pitch_e_narrativa.md"
status: "stale"
area: "negocio"
---

# GTM Fase 2, Pitch, Narrativa e Tradução Técnica → Comercial

> Data: 2026-07-15 · Base: auditoria MVP (saru-os hub 5 módulos + telemetry-api real + QSS GREEN 93,03 s
> + 3-DOF validado Khalil 2018 + 14-DOF em roadmap) + Fase 1 (módulo 09) + Brand DNA (`SARU_BRAND_DNA.md`).
> Regra-mestra: **o pitch só afirma o que o código sustenta hoje.** Roadmap se vende como roadmap.

---

## 1. Matriz de tradução: ativo técnico → benefício comercial

Regra de ouro da tradução: **ninguém compra DOF, compra décimos de segundo e dinheiro economizado.**
A matemática entra como *prova*, nunca como *manchete*.

| Ativo técnico (real) | O que significa | Frase de pitch (leigo/investidor) | Prova disponível |
|---|---|---|---|
| Solver QSS validado vs oráculo (Porsche 992 GT3 R @ Interlagos, 94 s ± 1 s) | Prever tempo de volta e efeito de setup sem ir à pista | "Testamos 200 configurações do seu carro no computador antes de você gastar um jogo de pneus." | Baseline de regressão GREEN 93,03 s |
| Telemetria assíncrona 1000 Hz (TimescaleDB/Redis, testada) | Dados do carro em tempo real, acessíveis de qualquer lugar | "Cada sensor do carro, ao vivo, na tela do engenheiro, no box ou do outro lado do mundo." | telemetry-api em produção de dev, com testes |
| Modelo transiente 3-DOF validado vs benchmark publicado (Khalil 2018, roll gradient −5%) | A física bate com literatura científica revisada | "Nossa física é validada contra pesquisa publicada, não é achismo de garagem." | `tests/unit/test_khalil2018_roll.py` + `validation/` |
| Arquitetura web/cloud multi-serviço (vs desktop legado) | Colaboração, sem licença travada em 1 máquina | "Os concorrentes vendem um software de 2005 preso num PC. Nós vendemos uma sala de engenharia na nuvem." | Hub Next.js + FastAPI + filas, demo ao vivo |
| Solver C++ de suspensão (pybind11) | Velocidade de cálculo de cinemática | "Cálculo de suspensão em milissegundos, não minutos." | `ext/suspension_cpp` |
| 14-DOF acausal Julia (ModelingToolkit), **ROADMAP Fase 2 eng.** | Fidelidade de simulador de fábrica | "Estamos construindo o motor de próxima geração: a física que só equipes de F1 têm hoje." | ROADMAP.md + harness TDD vs oráculo |
| Pacejka térmico + aero 4D + surrogates ML, **ROADMAP (moat, módulo 06)** | Diferencial defensável de longo prazo | "Nosso fosso: pneu que esquenta, aerodinâmica que respira, IA que aprende o carro." | Só como visão; zero claim de 'pronto' |

## 2. Guardrails de honestidade (o que PODE e NÃO PODE ser dito)

| ✅ PODE afirmar | ❌ NÃO PODE afirmar | Por quê |
|---|---|---|
| "Solver de lap-time validado contra referência (±1 s em Interlagos)" | "Simulador 14-DOF operacional" | 14-DOF é Fase 2 de engenharia; hoje é QSS |
| "Física validada contra benchmark publicado" | "Precisão de gêmeo digital" | Validação é pontual (roll gradient), não global |
| "Plataforma de telemetria funcional e testada" | "Produto completo em produção com clientes" | `/simulate` ainda mock; zero cliente pagante |
| "Parcerias ativas com Copa Truck e projeto Hase" | Nomes de clientes/resultados não autorizados | Parcerias ≠ contratos fechados até assinar |
| "Roadmap para fidelidade de fábrica (14-DOF, pneu térmico)" | Datas duras de entrega p/ investidor | Solo dev; risco de execução real |

> Investidor técnico **vai** fazer due diligence. Uma inconsistência entre pitch e repo mata a credibilidade
> de todas as outras claims. A honestidade sobre o estágio ("QSS validado hoje, 14-DOF em construção com
> harness TDD") é em si um sinal de maturidade de engenharia, usar a favor.

## 3. Elevator pitches (30 s, formato problema → solução → prova → gancho)

### 3a. Investidor
> "Equipes de corrida fora da F1 decidem setup de carro no feeling, porque software de simulação de verdade
> custa 6 dígitos e roda preso num desktop. A SARU entrega simulação e telemetria validadas cientificamente,
> na nuvem, por assinatura, preço de equipe nacional, física de fábrica. O mercado de telemetria motorsport
> dobra até 2033 (US$ 2,4 bi), e a Porsche Ventures acabou de financiar a camada rasa desse funil. Nós somos
> a camada profunda. Nosso solver já bate a referência com erro menor que 1 segundo em Interlagos."

### 3b. B2B (chefe de equipe nacional)
> "Quantos treinos você gasta pra achar o acerto do carro? A gente simula centenas de combinações de setup
> antes do caminhão sair da oficina, e na pista sua telemetria vira análise em tempo real, engenheiro no box
> e consultor remoto na mesma tela. Física validada, sem licença travada, sem comprar servidor. Posso rodar
> uma simulação do seu carro na pista da próxima etapa e te mostrar o resultado?"

### 3c. B2C (entusiasta track day / sim racer)
> "Você faz track day e não sabe por que seu amigo é 2 segundos mais rápido. A gente pega seus dados e te
> devolve em português claro: onde você perde tempo, o que treinar, o que ajustar no carro. A mesma engenharia
> que equipe de corrida usa, no seu carro de rua, no autódromo de Brasília."

## 4. Estrutura do Deck completo (12 slides, arco narrativo)

| # | Slide | Objetivo | Conteúdo-chave | Nota visual (anti-slop) |
|---|---|---|---|---|
| 1 | Capa | Impacto | Logo + tagline + 1 imagem de dado real (traçado de telemetria) | Stealth Dark + Apex Gold; zero stock photo |
| 2 | Problema | Dor | "Setup no feeling": custo de treino, ferramenta legada cara/travada | 1 número grande (custo de 1 dia de pista) |
| 3 | Solução | Clareza | Plataforma: simular antes + medir durante + entender depois | Diagrama 3 passos, não screenshot denso |
| 4 | Demo/Produto | Prova visual | Hub ao vivo: LTS (sim de setup) + SA (telemetria) | Produto real > mockup; teal/orange dos módulos |
| 5 | Por que agora | Urgência | Autódromo BSB reaberto + mercado 9% CAGR + VC entrando no setor | Dados do módulo 09 com fontes |
| 6 | Mercado | Tamanho | TAM US$ 2,4 bi (2033) / SAM equipes nacionais+GT / SOM BSB+parcerias | Funil TAM-SAM-SOM honesto |
| 7 | Modelo de negócio | Receita | 3 tiers: Hase (B2C freemium) / SARU Pro (equipe, assinatura) / Consultoria (internacional, USD) | Tabela de tiers |
| 8 | Diferencial/Moat | Defesa | Física validada + cloud colaborativo vs desktop legado; roadmap 14-DOF/térmico | Matriz 2×2: fidelidade × acessibilidade |
| 9 | Validação/Tração | Confiança | Oracle ±1 s, benchmark Khalil, parcerias Copa Truck/Hase, 8k audiência | Só fatos auditáveis (guardrails §2) |
| 10 | Concorrência | Contexto | Canopy (caro) / ChassisSim (legado) / OptimumLap (raso) / Track Titan (gamer) | Mapa posicionamento, SARU no gap do meio |
| 11 | Roadmap | Visão | Eng.: 14-DOF → correlação HiL · Negócio: BSB → nacional → export | Timeline 3 horizontes, sem data dura |
| 12 | Time + Ask | Fechamento | Fundador eng. automotiva UnB + o que se busca (contrato piloto / capital) | Ask específico e numérico |

**Arco:** dor cara (2) → alívio simples (3-4) → janela de tempo (5-6) → como vira dinheiro (7) → por que ninguém copia fácil (8-10) → onde chega (11) → quem executa (12).

## 5. Identidade de marca → comunicação (elegante + agressivo)

> **Atualização 2026-07-15:** mascote oficial = **saruê** (ver `SARU_BRAND_DNA.md` §1). O princípio
> anterior "felino = comportamento, não mascote" foi **SUPERSEDED**, a SARU tem mascote. O que
> permanece: **discrição visual, agressividade factual** (números, deltas de tempo, provas) e
> linguagem sóbria em proposta comercial B2B formal (mascote vive na marca/comunidade, não no contrato).

- **Verbal (mantido):** frases curtas, afirmativas, zero hedging. Vocabulário de precisão ("medido",
  "validado", "±1 s") em vez de superlativo vazio ("revolucionário", "disruptivo", banidos).
- **Visual:** Brand DNA (Stealth Dark + Apex Gold); no deck 90% dark neutro, dourado apenas no número
  que importa por slide. Mascote saruê: logo em iteração, paleta #HEX em definição pelo operador.
- **Storytelling de naming, A REVISAR:** narrativa antiga "SARU (predador) × Hase (lebre/presa)" não
  sobrevive à troca p/ saruê + Hase virando **curso** (persona própria, módulo 09 §5 P4). Construir nova
  narrativa a partir do saruê (marsupial brasileiro: resiliente, adaptável, noturno) quando logo fechar.
- **Taglines candidatas, revisar na mesma rodada:** *"Precision is predatory"* era felina; seguem na
  mesa "Engenharia que caça décimos" e "See the apex first" / "Enxergue o apex primeiro".
- **NUNCA:** mascote cartoon em UI de dados ou contexto B2B técnico formal, dourado em excesso (vira
  slop), metáfora animal em proposta comercial (linguagem sóbria; o saruê vive na marca, não no contrato).

## 6. Entradas para a Fase 3 (GTM e aquisição)
- [ ] Decisão de arquitetura de marca Turbotec ↔ SARU (rebrand vs braço de mídia), bloqueia tagline e bio.
- [ ] Montar deck físico (Canva/Figma) a partir do §4, depende de logo/assets atuais do operador.
- [ ] Gravar demo de 90 s do hub (LTS+SA), insumo p/ slide 4, LinkedIn e ads.
- [ ] Definir os 3 tiers de preço (gap do módulo 09 §6) antes do slide 7 virar público.

## 7. Demo ao vivo do MVP, roteiro de 8 min (reunião B2B/investidor)

> Complementa a demo de 90 s (§6, vídeo p/ slide/ads): este é o roteiro **guiado** para call/presencial.
> Integrado do plano de execução 2026-07-15. Regras: **sempre dado real** (do parceiro, se autorizado);
> nunca abrir tela de feature futura; screencast de backup gravado caso algo falhe.

1. Login → workspace: "isto é o que sua equipe vê" (30 s)
2. Importar sessão real (`.ld`/`.xrk`) → detecção de voltas/canais/qualidade (90 s)
3. Comparar melhor volta × volta alvo: delta, speed, brake/throttle, G-G (2 min)
4. "Onde está o tempo?", insight por curva (90 s)
5. Referência LTS para a pista/carro → overlay real × simulado, com fonte/solver/confiança visíveis (90 s)
6. Export do resumo técnico: "isto vai para a reunião pós-sessão" (60 s)
7. Fechamento: roadmap Now/Next/Later em 1 tela (módulo 04 §4.1) (30 s)

**Deck comercial por segmento (esqueleto, deriva do §3/§4):** dor do segmento na linguagem dele →
o que a SARU entrega (só os módulos relevantes) → demo/prints com dado do segmento → como começa
(onboarding em 1 sessão) → plano/preço (aguarda matriz, módulo 12) → roadmap curto → próximo passo
concreto (agendar importação da primeira sessão do cliente).

## 8. Demo 90s, roteiro de gravação (shot-list p/ o Vitor)

> Screencast do hub p/ slide 4, LinkedIn e ads (§6). Regras: dado REAL (fixture Copa Truck),
> 1920×1080, dark theme, sem narração falada, legendas curtas (funciona mudo no feed); música
> neutra. Cada take: gravar 5s a mais de cada lado p/ corte.

| # | t | Cena (o que gravar) | Legenda (PT-BR) |
|---|---|---------------------|------------------|
| 1 | 0-8s | Login → Hub abre (dashboard escuro, módulos visíveis) | "Seus dados de pista. Um só lugar." |
| 2 | 8-20s | Arrastar `.xrk` real → detecção de voltas/canais/qualidade aparecendo | "Importe a telemetria. Qualquer logger." |
| 3 | 20-38s | SA: comparar melhor volta × alvo, delta subindo/descendo, brake/throttle | "Onde estão os décimos? Aqui." |
| 4 | 38-52s | Zoom num trecho: leitura por curva (SaDriver), G-G | "Curva a curva. Sem achismo." |
| 5 | 52-70s | LTS: rodar referência simulada → overlay real × sim c/ badge de fonte/solver | "Compare com a física. Rastreável." |
| 6 | 70-82s | Export do resumo técnico (botão → arquivo) | "Da pista pra reunião em minutos." |
| 7 | 82-90s | Logo SARU + tagline (aguarda decisão §5) + CTA | "SARU, engenharia que caça décimos." *(placeholder até tagline oficial)* |

**Checklist pré-gravação:** stack limpa (`docker compose up`), usuário demo, fixture `.xrk` Perez
carregada, zoom do browser 100%, cursor highlight ON, notificações OFF. **Pós:** cortar em 90s
exatos; versão 30s (takes 2-3-5) p/ ads; thumbnail = frame do take 5 (overlay).
