---
titulo: "SARU, Documento de Referência Competitiva"
data: "2026-08-19"
origem: "_arquivo/saru-app/docs/research/competitive-sim-telemetry-2026-07.md"
status: "vigente"
area: "produto"
---

# SARU, Documento de Referência Competitiva

*Sim racing hub · Análise de telemetria · Recomendações personalizadas · IA futura via OpenRouter*
*Síntese estratégica, 2026-07-18*

---

## 0. Resumo executivo (leia isto primeiro)

O mercado está partido em dois: (a) **ferramentas de análise crua** que não recomendam nada (MoTeC i2, Garage 61, Racelab, SimHub, Second Monitor, SRT) e (b) uma camada de **AI-coaching em rápida expansão** (Track Titan, Coach Dave Delta "Auto Insights", trophi.ai, RaceCrewAI, RACEngineer.ai, Full Grip Vision) que traduz telemetria em "seu maior erro e como corrigi-lo".

Todos os coaches de IA existentes dizem **o QUE** você fez e **o QUE** mudar, mas raciocinam por **correlação** (comparação com uma volta-referência ou heurísticas de módulos). **Ninguém explica o PORQUÊ em termos de dinâmica veicular.** Esse é o espaço aberto que o motor de física do SARU (14-DOF, load sensitivity, elipse de atrito, oráculo 86/99) pode ocupar. Somado a isso, o **console é greenfield**: quase tudo é PC-Windows-only; o SARU já tem a ponte GT7 e um padrão de ingestão UDP reutilizável.

Posicionamento recomendado (detalhado na seção 5): **"O coach que explica o porquê, validado contra física real, em Desktop e console."**

---

## 1. Matriz competitiva

| Produto | O que faz | Plataformas / Sims | Preço (fonte) | Coaching / IA |
|---|---|---|---|---|
| **Track Titan** ([tracktitan.io](https://www.tracktitan.io/memberships)) | Coach de IA + análise de telemetria; "Coaching Flows" guiam o maior erro da volta. "Strava do automobilismo". $5M seed (Porsche Ventures), 265K+ users | PC **+ console**; iRacing, ACC, AC, F1 26, AMS2, LMU, Forza. Web + iOS | Free; Plus **$7.99/mo**; Premium **$16.99/mo**; Ultra **$19.99/mo**; trial 7d | **Sim**, dicas de IA ilimitadas (pago), auto-detecta maior perda; + coaching humano 1:1 e conselho de instrutor certificado |
| **trophi.ai** ([trophi.ai](https://www.trophi.ai/pricing-sim-racing)) | Coach de **voz em tempo real** ("Mansell") fala enquanto você dirige + debrief corner-by-corner. Backed by Driver61 | PC; iRacing (road), ACC, F1 23/24/25, LMU. **Sem console** | **~$12.99-$15/mo** software-only, trial 7d; tier Professional adiciona 1:1 humano | **Sim, o mais "coach-like"**, voz conversacional ao vivo em 59+ idiomas; erros priorizados por perda de tempo |
| **Coach Dave Delta 6.0** ([coachdaveacademy.com/delta](https://coachdaveacademy.com/delta/)) | Setups pro (2.500+) + telemetria + "Auto Insights" IA (modelo 4 fases: Braking/Entry/Apex/Exit) + análise de vídeo. ~12.000 users/dia | PC; iRacing, ACC, LMU, AC Evo (full); **GT7** (parcial), AMS2, AC | **~$12.99/mo ou $109/yr**; bundle ACC+iRacing+LMU **$11.99/mo** | **Sim**, Auto Insights por fase de curva; ajuste de pressão condition-aware (ACC) |
| **Full Grip Vision** ([fullgripmotorsport.com](https://www.fullgripmotorsport.com/about/fullgripvision)) | Coach de voz **offline/local** + AI Setup Engineer; 62 módulos comparam à sua PB a 60Hz; anti-spam | PC; ACC, AC Evo, AC, iRacing, LMU, RaceRoom, F1, AMS2, Forza MS | Free / Supporter **€3.99** / Pro **€7.99** / Elite **€9.99** (Setup Engineer só no Elite) | **Sim**, voz gerada ao vivo (offline → NLG templada, não LLM cloud); 6 níveis de coaching |
| **RaceCrewAI** ([racecrewai.com](https://racecrewai.com/)) | **Multi-agente**: Boss (metas), Max (setup c/ explicação), Maia (coach ao vivo), Rocha (análise). Com Filipe Albuquerque | PC; iRacing, rFactor 2, AC, ACC, AMS2 | Trial 7d sem cartão; "AlphaPhase" early-access (valor não publicado) | **Sim**, design agêntico mais claro do mercado; ações > dados |
| **RACEngineer.ai** ([racengineer.ai](https://racengineer.ai/)) | **Engenheiro de corrida** (não só coach): spotter/tráfego/bandeiras, PTT radio Q&A, estratégia (combustível/pneu/pit), debrief curto | PC; iRacing (launch), ACC/LMU "coming soon". Beta | Não publicado (beta) | **Sim**, arquitetura 2 camadas: local (urgência) + cloud LLM ("natural-language radio") + memória cross-session |
| **Sim Coaches TrackPro (APEX)** ([simcoaches.com](https://simcoaches.com/)) | Coach de voz **multi-modal**: áudio + 12ch háptico + 5DOF motion | PC; iRacing, AC, BeamNG + Stream Deck | Free; Premium **~$20/mo** (auto-publicado) | **Sim**, diferencial é entrega multi-modal, não profundidade de raciocínio |
| **Simulator-Controller** (OSS, [GitHub](https://github.com/SeriousOldMan/Simulator-Controller)) | Pit crew open-source: Engineer/Strategist/Spotter (regras) + Driving Coach (**LLM, traga seu modelo**: GPT/Mistral/Llama local via Ollama) | PC; iRacing, ACC, rFactor 2, LMU | **Free / OSS** | **Sim, híbrido**, referência de arquitetura: regras p/ tempo-crítico, LLM p/ diálogo/explicação |
| **VRS (Virtual Racing School)** ([vrs.racing](https://vrs.racing/data-packs)) | Datapacks pro (setup+ghost+telemetria) + Academy; comparação vs coaches/amigos. Incumbente | iRacing (profundo). Web + desktop | Casual free; Dedicated **$4.99/mo** ou **$49.99/yr**; competitivo desde **$8.33/mo**; trial 14d | **Não-IA**, humano/reference-based; "otimizado para pilotos, não engenheiros" |
| **Garage 61** ([garage61.net](https://garage61.net/docs/faq/pricing)) | Telemetria iRacing + comparação comunitária; **700M+ voltas**; agente sincroniza ghosts; notas de equipe | iRacing. Desktop agent + web | Free; Pro desde **$7/mo** | **Não-IA**, data/community-driven; você interpreta |
| **MoTeC i2 (Std/Pro)** ([motec.com.au](https://www.motec.com.au/i2/i2overview/)) | Software pro de análise (pedigree real). O teto de referência da análise séria | iRacing (.ibt→.ld), ACC (export nativo). **Windows only** | i2 Standard **free**; Pro free p/ ACC não-comercial (efetivamente grátis) | **Nenhum**, dado cru puro; curva de aprendizado íngreme |
| **Racelab** ([racelab.app](https://www.racelab.app/)) | Suite de **overlays em tempo real** (delta, relative, track map, data blocks 80+) + layouts inteligentes | iRacing, AC, ACC, rF2, F1. Desktop overlay, VR | Free; Pro **~€4.90/mo** (também citado €3.90/mo ou €39.90/yr) | **Nenhum**, HUD ao vivo; interpretação é do piloto |
| **SimHub** ([simhubdash.com](https://www.simhubdash.com/)) | Dashboards custom, LED/RGB, motion/bass-shaker; Dash Studio. **80+ sims** | 80+ sims. Windows + displays | Free (donationware); licença perpétua **~€5 / £10-15** | **Nenhum**, engine de output/hardware |
| **Sim Racing Telemetry (SRT)** ([simracingtelemetry.com](https://www.simracingtelemetry.com/)) | Gravador/analisador **cross-platform incl. console**; charts + projeção na pista + TDiff | F1 20-25 (PC/PS/Xbox), ACC, PCars2. Steam/Android/iOS. **GT7 não suportado** | Trial grátis limitado; **IAP por jogo** (a la carte) | **Nenhum**, análise apenas; diferencial é alcançar console/F1 |
| **Second Monitor** (OSS, [GitHub](https://github.com/Winzarten/SecondMonitor)) | Live timing 2ª tela + telemetry viewer básico | iRacing, AC, rF2, Automobilista. Windows | **Free / OSS** | **Nenhum** |

**Bandas de preço:** o mercado converge em **freemium ~€4-20/mo**. Voz/tempo-real fica no topo ($13-20/mo); MoTeC e OSS são grátis; SimHub usa licença perpétua barata; SRT usa IAP por jogo. Coaching humano 1:1 é o upsell premium recorrente. *(Preços de trophi/Coach Dave/TrackPro vêm de fontes secundárias, verificar na página oficial antes de citar em material público.)*

---

## 2. Matriz de captura por sim/plataforma + as 2 fontes recomendadas

### 2.1 Matriz de captura

| Sim | Método de captura | Desktop (PC) | Console | Fidelidade / notas |
|---|---|---|---|---|
| **GT7** ✅ *(feito)* | **UDP LAN**, porta 33739 (heartbeat) / 33740 (extended), payload **cifrado Salsa20**, ~60Hz | Receptor roda em qualquer PC da rede (a ponte atual) | **PS4/PS5**, fonte console de referência | Reverse-engineered mas estável; já integrado no `saru-telemetry-gt7` |
| **iRacing** | **irSDK** memory-mapped (`Local\IRSDKMemMapFileName`): telemetria binária ~60Hz + sessionInfo YAML; arquivos `.ibt`→MoTeC | **Sim** (Windows mmap) | **Nenhum** (PC-exclusivo) | Canais riquíssimos + timing/competidores completos |
| **ACC** | **Shared memory** (SPageFilePhysics/Graphics/Static) + export MoTeC + Broadcasting UDP (só timing) | **Sim** (física completa) | **NENHUM**, build de console **não emite nada** (sem shmem, sem UDP) | ⚠️ **A armadilha**: "suporte ACC" = **só PC** |
| **F1 (EA/Codemasters 22-25)** | **UDP oficial documentado** (spec EA), porta 20777, menu-controlado, até 60Hz, múltiplos pacotes | **Sim** (loopback 127.0.0.1) | **PS4/PS5 E Xbox**, first-class | Spec mais bem documentada; per-tyre, ERS, dano, timing completo. **Zero risco de RE** |
| **Forza (MS 2023 / Horizon 4-5)** | **"Data Out" UDP** nativo, struct binário fixo (Sled/Dash), porta comum 5607 | **Sim** (idêntico ao Xbox) | **Xbox One/Series**, first-class | Único caminho p/ ecossistema **Xbox**. Sem pressões de pneu no struct base; timing mais grosseiro |
| **AMS2** | Shared memory (formato PCARS2) **e** UDP broadcast porta 5606 | **Sim** | **Não** (PC-only) | Parser PCARS2 cobre AMS2 + qualquer título Madness |
| **rFactor 2 / LMU** | Shared memory via plugin `rF2SharedMemoryMapPlugin` (.dll) + DAMPlugin→MoTeC | **Sim** (requer instalar plugin) | **Não** | LMU = mesmo plugin do rF2 |
| **RaceRoom (R3E)** | **Shared memory oficial** (`$R3E`), SDK mantido pelo dev | **Sim** | **Não** | Raro: SDK oficial |

**Dois arquétipos de ingestão** (o BFF-orquestrado do SARU serve ambos com um adapter por sim → schema comum):
1. **UDP-push LAN**, GT7, F1, Forza, AMS2. Reutiliza um único listener (a ponte GT7 é o template).
2. **Windows shared-memory / mmap**, iRacing, ACC, AMS2, rF2/LMU, RaceRoom. Requer um agente Windows que lê o mmap e encaminha.

### 2.2 As 2 fontes adicionais recomendadas (além de GT7/ACC/iRacing)

**#1, F1 (EA SPORTS / Codemasters).** A **melhor** próxima fonte para cobertura de console. É o único sim mainstream além do GT7 com **spec UDP oficial publicada** que emite **identicamente em PS4, PS5 E Xbox** (porta 20777, controlado por menu em todas as plataformas). Complementa o GT7 perfeitamente: o GT7 cobre o público Sony/GT prosumer; o F1 adiciona uma enorme audiência de esports/console cross-platform com o **pacote mais rico documentado** (per-tyre, ERS, dano, timing + todos os participantes). **Zero risco de reverse-engineering** (spec oficial, estável ano a ano) e o receptor **reutiliza a mesma arquitetura de listener UDP** já construída para o GT7. Justificativa de ranking #1: maximiza alcance NOVO de console com protocolo oficial e baixa manutenção.

**#2, Forza Motorsport (2023) / Forza Horizon 5.** A **segunda** fonte console-capable e o **único caminho para o ecossistema Xbox** (circuito + mundo aberto). "Data Out" UDP funciona nativamente em Xbox One/Series e PC com struct binário fixo documentado (orientação yaw/pitch/roll, suspensão/slip/rotação por roda, temps de pneu, g-forces, posição, dados de volta). Justificativa: **com F1 + Forza, a matriz cobre Desktop E as três famílias de console** (PlayStation via GT7/F1; Xbox via F1/Forza) usando apenas protocolos UDP oficiais, enquanto ACC e iRacing permanecem como fontes de física de alta fidelidade PC-only. Fica em #2 porque o dado é ligeiramente menos rico para engenharia de corrida (sem pressões de pneu no struct base, timing mais grosseiro), indispensável para Xbox, mas secundário ao F1.

**Estratégia de cobertura resultante:** trio PC de alta fidelidade (ACC + iRacing + um de rF2/AMS2/R3E via agente shmem) para o sim-racer sério de PC, **+ F1 + Forza** como as duas fontes UDP de console → toda família de console coberta, reutilizando exatamente **dois padrões de ingestão**.

---

## 3. O gap de mercado que o SARU ataca

### 3.1 O gap central: coaching CAUSAL, fundamentado em física ("o PORQUÊ")

| Nível de resposta | Quem faz | Como |
|---|---|---|
| **O QUE você fez** (freou tarde, perdeu o apex) | Todos os coaches de IA | Comparação com volta-referência / delta |
| **O QUE mudar** (freie mais cedo, mais throttle na saída) | Track Titan, trophi.ai, Coach Dave, Full Grip, RaceCrewAI | Heurística de módulos / correlação com referência |
| **POR QUE, em dinâmica veicular** ("você está 4 km/h lento no apex porque raspou grip dianteiro em trail-braking além do limite de transferência de carga, solte 15% do freio antes para manter a dianteira dentro do círculo de atrito") | **NINGUÉM convincentemente** |, |

**Quem já faz recomendações:** Track Titan (Flows), Coach Dave (Auto Insights 4-fases), trophi.ai (voz priorizada), Full Grip (62 módulos), RaceCrewAI (multi-agente), RACEngineer.ai, TrackPro, VRS (variance-based). **Quem NÃO faz:** MoTeC, Garage 61, Racelab, SimHub, SRT, Second Monitor (todos análise crua).

**Onde o SARU ganha:** o raciocínio de todos os incumbentes é **pattern/correlation-based**, compara sua volta a uma referência fixa ou aplica regras. O **motor de física do SARU** (14-DOF, load sensitivity, elipse de atrito, oráculo validado 86.18/99.36) é exatamente o ativo para transformar coaching-por-correlação em **coaching causal**. Isso ataca diretamente a **fraqueza documentada dos concorrentes**: eles dão conselho **genérico para pilotos avançados** (o coaching estagna quando você já está perto da referência), porque raciocinam sobre delta-a-uma-referência-fixa, não sobre o **estado específico do carro do piloto**. Um modelo de física que raciocina sobre o estado real do veículo resolve o "genérico para experts", e pode rodar **fora do hot path** (protegendo FPS, outra queixa documentada, ex. overhead de CPU do trophi).

### 3.2 Gaps adjacentes que o SARU também pode capturar

- **Setup recommendation físico.** Superfície grande e subatendida: só Full Grip (Elite), Coach Dave, Max do RaceCrewAI e airaceengineer tocam nisso, a maioria é **lookup de biblioteca ou auto-tune heurístico**. Um Setup Engineer **baseado em modelo de física** que *prevê o efeito no lap-time de uma mudança e explica o porquê* (condition-aware) bate os concorrentes de database-lookup. Alinha com o trabalho de load-sensitivity do SARU.
- **Console.** Quase tudo é Windows-PC-only. Voice coaching em tempo real para **PS5/Xbox é quase greenfield**, combina com a ponte GT7 já pronta.
- **Credibilidade por física, não por piloto.** Quase todo produto sério se ancora num piloto pro real (trophi←Driver61, RaceCrewAI←Albuquerque, Coach Dave). O SARU pode vender **fidelidade científica** ("validado contra oráculo de física real") onde os outros vendem pedigree de piloto, um diferencial defensável e distinto.

### 3.3 Nota de arquitetura de IA (relevante ao plano OpenRouter)

O mercado converge para um **híbrido**, e o SARU deve segui-lo: **NÃO** coloque um LLM no hot loop de 60Hz. Use **regras/física para tempo real** (spotter, bandeiras, cues por curva, como os 62 módulos do Full Grip, as 4 fases do Coach Dave, o rule engine do Simulator-Controller) e **reserve o LLM (via OpenRouter) para o "porquê" em linguagem natural, o debrief e o Q&A** (como a camada cloud "natural-language radio" do RACEngineer.ai e o coach GPT do Simulator-Controller). A **decomposição multi-agente** (RaceCrewAI: Boss/Max/Maia/Rocha; Simulator-Controller: Engineer/Strategist/Spotter/Coach) mapeia limpo sobre o BFF NestJS + serviços de física do SARU e a direção NMPC da Phase 3: um agente "engenheiro de corrida" (estratégia/combustível/pneu), um "coach" (técnica), um "setup engineer" (física).

---

## 4. Padrões de UX concretos a adotar/superar no front-end

**Adotar como table-stakes (para ter credibilidade):**

1. **Espectro NOVATO↔ENGENHEIRO explícito, com toggle.** VRS declara a persona ("otimizado para pilotos, não engenheiros"); Track Titan oferece **dois layouts**, simplificado vs "Advanced Layout" que imita o stack de traces do engenheiro (throttle/brake/speed/steering/gear alinhados verticalmente), atrás de **um toggle no topo**. O SARU deve declarar a persona E oferecer um modo avançado estilo MoTeC sem herdar a intimidação.

2. **Priorizar "onde melhorar" por SEGUNDOS PERDIDOS, nunca cronologicamente.** Padrão vencedor (trophi corner-by-corner, Track Titan "maior erro único"): **uma lista ranqueada de cards**, cada um = {curva, segundos perdidos, uma correção concreta}, mais custoso primeiro. Mostre **UM erro herói**, depois o resto ranqueado. Anti-spam / "smart priority system" é o que torna coaching usável vs irritante.

3. **Track map = índice espacial, não decoração.** Melhor padrão (Racelab + MoTeC i2): colorir o contorno da pista por tempo ganho/perdido por segmento, pontos-quentes clicáveis de perda, curvas nomeadas, e **ligação bidirecional map↔trace↔corner-card** (hover num card → destaca segmento no mapa + região no trace). É a visualização de coaching mais valiosa, **faça dela a peça central**.

4. **Dual-cursor de variância tempo/distância** (o primitivo canônico do MoTeC): solte dois cursores → auto-computa delta + min/max/avg + diferencial tempo-ou-distância. Toda view séria de análise precisa disso **+ toggle de eixo X entre distância e tempo**. Delta-vs-referência renderizado como **área preenchida** (verde = ganhando, vermelho = perdendo) sincronizada ao track map.

5. **Sistema de cores por canal, tokenizado e global** (MoTeC global channel properties): throttle=verde, brake=vermelho, steering/speed/gear com **uma cor cada, idêntica** em trace, mapa e cards. Consistência de cor por canal é o que faz a UI parecer profissional. Defina como **design tokens já no início**. Tema dark é table-stakes.

6. **LIVE loop vs REVIEW loop são superfícies separadas.** LIVE (Racelab/trophi in-sim): mínimo, glanceável a 200 km/h, transparência/font-size ajustáveis, voz para o complexo. REVIEW (MoTeC/VRS/Track Titan): denso, interativo, comparativo. **Projete-os como dois front-ends que compartilham telemetria, não um layout responsivo**, as restrições são incompatíveis.

7. **Ingestão de baixa fricção = campo de batalha de UX escondido.** VRS auto-upload cloud; Garage 61 usa **agente fino em background + análise no browser** (sem instalação pesada). A arquitetura **BFF-single-SPA-edge do SARU alinha naturalmente** com o modelo web-first do Garage61/VRS, "agente fino de captura + tudo analisado no browser".

**Superar (onde o SARU pode ir além):**

8. **Layouts auto-adaptativos por contexto.** Racelab "intelligent layouts" e SimHub "dashboard playlist" auto-trocam a view por carro/série/sessão. Presets context-aware (qualy vs corrida vs treino; classe do carro) que reorganizam quais painéis aparecem batem dashboards estáticos.

9. **Biblioteca de voltas-referência como feature (e moat).** "Comparar contra alguém mais rápido" motiva mais que a própria PB (Garage 61 voltas de equipe/comunidade; Track Titan/VRS datapacks pro). Planeje overlay de ghost da biblioteca com o piloto mais rápido destacado no mapa.

10. **Arquitetar a saída de coaching como eventos estruturados** `{corner, channel, delta, instruction}` desde o começo, assim uma camada TTS/voz (a fronteira premium: trophi $15/mo, 59 idiomas) pode ser adicionada depois sem retrabalho. Mesmo começando visual-only, o "porquê" causal do SARU brilha em voz.

---

## 5. Posicionamento recomendado do SARU

**Frase de posicionamento:**
> **"O coach de sim racing que explica o PORQUÊ, fundamentado em física real, do Desktop ao console."**

**Os quatro pilares defensáveis:**

1. **Coaching causal, não correlacional.** Todo concorrente diz *o quê* e *o quê mudar* via comparação-com-referência. O SARU usa seu motor de física (14-DOF, load sensitivity, elipse de atrito) para explicar *por que* em termos de dinâmica veicular sobre o estado real do carro do piloto. Resolve diretamente a queixa de "genérico para experts".

2. **Credibilidade científica em vez de pedigree de piloto.** Onde os rivais se ancoram num pro (Driver61, Albuquerque), o SARU vende **fidelidade validada contra oráculo de física** (86.18/99.36). Diferenciação distinta e ownable numa comunidade cansada de "mais um AI coach".

3. **Cobertura Desktop + console real.** Trio PC de alta fidelidade (ACC + iRacing + 1) **+** GT7 (feito) + **F1 + Forza** → todas as três famílias de console via protocolos UDP oficiais. Enquanto os concorrentes brigam num PC-iRacing lotado (Track Titan $5M seed, 265K users, categoria VC-validada e apinhada), o SARU pega o **console quase greenfield**.

4. **Setup engineer preditivo por física.** Não lookup de database, prevê o efeito no lap-time e explica, condition-aware. Superfície subatendida que alavanca o simulador do SARU.

**Arquitetura como produto (tiering natural):** decomposição multi-agente (engenheiro de corrida / coach / setup engineer) sobre o BFF NestJS + física + Phase-3 NMPC. **Regras/física no hot loop de 60Hz; LLM via OpenRouter para o "porquê", debrief e Q&A**, nunca o LLM no caminho tempo-crítico.

**Preço:** o mercado clusteriza em **€4-20/mo com free tier de aquisição** (não invente número, validar contra Full Grip €3.99-9.99, Track Titan free+pago, trophi/Coach Dave ~$13-15). Alavancas de upsell padrão: profundidade de coaching, acesso ao setup engine, e (topo de banda) voz em tempo real + 1:1 humano. Trial sem cartão (padrão RaceCrewAI 7d) para onboarding. **Free telemetry logging como funil de aquisição que alimenta o pool de dados**, os efeitos de rede são reais (Garage 61: 700M+ voltas; um AI coach precisa de corpus de voltas-referência rápidas).

**A evitar (fraquezas documentadas dos rivais):** overhead de CPU/FPS (rode a análise fora do hot path); conselho genérico que estagna perto da referência (o raciocínio de física ataca isso pela raiz).

---

*Fontes citadas inline. Preços de trophi.ai, Coach Dave Delta e TrackPro provêm de fontes secundárias, verificar nas páginas oficiais antes de uso em material público. GT7 já integrado no `saru-telemetry-gt7`; F1 e Forza reutilizam o mesmo padrão de listener UDP.*