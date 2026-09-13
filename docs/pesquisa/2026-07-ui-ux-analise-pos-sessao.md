---
titulo: "Pesquisa UI/UX, Análise de telemetria pós-sessão (MoTeC, AiM, Pi Toolbox, ferramentas web)"
data: "2026-08-19"
origem: "_arquivo/saru-app/docs/research/2026-07-ui-ux-analise-pos-sessao.md"
status: "vigente"
area: "ui_marca"
---

# Pesquisa UI/UX, Análise de telemetria pós-sessão (MoTeC, AiM, Pi Toolbox, ferramentas web)

> Bloco 5b do mapeamento de arquitetura/customização do Saru Analyzer (2026-07-19).
> Pergunta-guia: como ferramentas de engenheiro (MoTeC i2, Race Studio 3, WinTAX4, Pi Toolbox)
> e ferramentas modernas para amadores (Garage 61, Track Titan, VRS, Delta, Popometer) organizam
> muitos canais, e como um híbrido resolve para cliente não-técnico.
> Companheiros: `2026-07-ui-ux-telemetria-ao-vivo.md` · `2026-07-ui-ux-video-sincronizado.md`.

---

## 1. Como as ferramentas de engenheiro organizam MUITOS canais

### 1.1 Hierarquia Workspace → Workbook → Worksheet (MoTeC i2)

O i2 é o padrão-ouro do modelo "páginas salvas". A hierarquia é explícita:

- **Workspace** = projeto completo (carro/campeonato) contendo um conjunto de **Workbooks** (abas temáticas: análise de pilotagem, motor, pneus, suspensão);
- **Workbook** = conjunto de **Worksheets** (páginas de tela);
- **Worksheet** = layout livre de componentes: gráfico tempo/distância, outing graph, histograma, histograma de suspensão, scatter plot, mixture map, FFT, vídeo, track report, mapa "rainbow" (pista colorida por valor de canal), time report, channel report e gauges.

Propriedades de canal (cor, unidade, escalas mín/máx) são definidas **globalmente**, o canal "Throttle" é sempre verde em todas as páginas, o que reduz drasticamente a carga cognitiva. Templates de worksheet padronizam páginas novas. O i2 Standard limita componentes/workbooks; o i2 Pro libera matemática avançada, múltiplas voltas em overlay e componentes ilimitados.
Fontes: [MoTeC i2 (produto)](https://software.motec.com.au/products/i2), [MoTeC i2 Overview](https://www.motec.com.au/i2/i2overview/), [Guia MoTeC p/ iRacing, Coach Dave](https://coachdaveacademy.com/tutorials/how-to-use-motec-data-in-iracing/), [BoxThisLap, configurar MoTeC](https://boxthislap.org/iracing-how-to-configure-motec/).

### 1.2 Troca rápida de página e teclas de função

- No i2, a navegação entre worksheets é pensada para ser instantânea (abas + atalhos). **F4** alterna o modo overlay; **F3** liga o gráfico de **Variance** (delta-time); zoom e cursor respondem a teclado.
- No Pi Toolbox, a versão 13 introduziu **soft keys** configuráveis para trocar de display/worksheet rapidamente ([PDF Pi Toolbox 13 & Soft Keys](https://www.cosworth.com/media/kvae1rog/pi-toolbox-13-and-soft-keys-v1-3.pdf)).
- No Race Studio 3, a **barra de espaço** esconde/mostra painéis da view, e há controles rápidos para escolher canais exibidos e cores.
Fontes: [MoTeC i2 highlights](https://www.motec.com.au/i2/i2highlights/), [Fórum MoTeC, Time slip plot](https://forum.motec.com.au/viewtopic.php?f=26&t=86), [Manual RS3 Analysis](https://www.aim-sportline.com/docs/racestudio3/manual/html/analysis.html).

### 1.3 Perfis e layouts no AiM Race Studio 3

O RS3 chama seu "workbook" de **Profile**: um conjunto de propriedades de visualização + conjunto de janelas, salvo e **aplicável a qualquer sessão**. Layouts default prontos: *Time/Distance* (lista de canais + mapa da pista + gráfico + storyboard), *Histogram*, *Channels Report* (mín/máx/média por volta e split) e *Video* (painel de filme sincronizado). Ou seja: o novato recebe páginas pré-montadas e o avançado customiza e salva as suas.
Fontes: [RS3 Analysis docs](https://www.aim-sportline.com/docs/racestudio3/manual/html/analysis.html), [Manual RS3 (PDF)](https://www.aim-sportline.com/docs/racestudio3/manual/latex/racestudio3-manual-en-latest.pdf), [AiM Data Analysis, James Colborn](https://www.jamescolborn.com/aim-data-analysis).

### 1.4 Pi Toolbox e WinTAX4

- Pi Toolbox: workbooks com até 16 worksheets, cada área de display com até 8 displays. Tipos: time/distance, channel display, mapa, dials, barras, bit indicator, outing report tabular, split report, relatório Excel, event display, histograma, navigator, summary, X/Y. Vídeo totalmente sincronizado com dados. ([Pi Toolbox, Cosworth](https://www.cosworth.com/motorsport/products/pi-toolbox/), [Pi Toolbox, RaceDataSystems](https://www.racedatasystems.com/pages/analysis-software-cosworth-pi-research-toolbox-html), [User Guide PDF](https://download.cosworth.com/documents/Reference/29P-071406.pdf))
- WinTAX4 (Marelli, usado em F1/WEC/MotoGP): janelas de análise, time/distance, scatter 2D/3D, bar graph, frequência, histograma, trends, report por volta e por setor, events, alarms, gauges, notas, e overlay que combina vídeo onboard com trilha no Google Earth. Até 100 kHz de aquisição. ([WinTAX4](https://store.racing-tech.net/wintax4/), [PDF WinTAX4](https://store.racing-tech.net/content/WinTAX4.pdf))

### 1.5 Overlay de voltas, delta-time e math channels

- Overlay: a volta de referência é desenhada "fantasma" sobre a volta principal, alinhada por **distância** (não tempo), convenção universal em todas as ferramentas.
- Delta-time / Variance: gráfico de ganho/perda acumulada entre voltas; no i2 é o "Variance" (F3) e existe também como *rainbow track map* de ganho/perda pintado sobre o traçado. É unanimemente descrito como o canal mais importante para achar onde está o tempo. ([Fórum MoTeC, Variance Channel](https://www.motec.com.au/forum/viewtopic.php?f=26&t=1231), [Rainbow track map](https://www.motec.com.au/forum/viewtopic.php?f=26&t=3697))
- Math channels: canais calculados pelo usuário; no i2 Pro há funções como `variance_dist(x)` e o prefixo `ref:` para referenciar o canal da volta overlay dentro de expressões, ou seja, a comparação entre voltas é *programável*. ([Fórum MoTeC, math](https://forum.motec.com.au/viewtopic.php?f=26&t=133), [i2 Training Seminar PDF](http://www.precisionautoresearch.com/DOWNLOADS/Motec%20Interpreter/i2%20Training%20Seminar%202008.pdf))
- Cursor vinculado: no i2, zoom e posição de cursor de um gráfico podem ser **linkados** a histogramas, scatters, outros gráficos, vídeo e mapa, mover o cursor atualiza todos os componentes de forma consistente. ([MoTeC i2 Overview](https://www.motec.com.au/i2/i2overview/))
- Workspaces compartilháveis: a comunidade troca workspaces prontos (ex.: [SDMotecWorkspace no GitHub](https://github.com/stevendaniluk/SDMotecWorkspace), workspaces do Coach Dave para ACC/iRacing), evidência de que o "template de análise" é um artefato de valor por si.

---

## 2. Como as ferramentas web modernas simplificam para amadores

### 2.1 Garage 61 (web, iRacing), "comparação sem fricção"

Agente leve roda em background e faz upload automático; **toda a análise acontece no browser**. UX centrada em: comparar sua volta contra leaderboards comunitários (milhões de voltas), colegas de equipe e voltas de referência; overlays, gráficos e track maps; notas de análise colaborativas; sync automático de *ghost laps* de volta para o iRacing. Núcleo gratuito, Pro ~US$ 6,50-7/mês. A simplificação-chave: **zero configuração de canais**, a ferramenta já decide o que mostrar (velocidade, pedais, delta, linha).
Fontes: [Garage61 docs](https://garage61.net/docs/usage), [Guia FUSION Racing](https://www.fusion-racing.org/iracing/iracing-apps/iracing-apps-garage61.php), [Delta vs Garage 61, Coach Dave](https://coachdaveacademy.com/tutorials/coach-dave-delta-vs-garage-61-which-is-best-for-you/).

### 2.2 Track Titan, "Coaching Flows": do dado ao diagnóstico

Captura automática em 20+ sims. O **Coaching Flow** quebra a volta em setores e zonas de frenagem, roda um motor de simulação proprietário (milhares de cenários) para custear cada erro em milésimos, e apresenta **um único maior ofensor** por vez, em linguagem natural: *"você freia 20 m tarde demais na Curva 4 e perde 3 décimos"*, com o trace lado a lado contra a referência. Em vez de entregar gráficos crus, ele responde a pergunta causal ("foi o throttle na saída ou você errou a entrada?"). Alegam ~0,5 s de ganho médio na primeira sessão analisada.
Fontes: [Coaching Flows, Track Titan blog](https://www.tracktitan.io/post/november-2025-update-coaching-flows), [Update dez/2025](https://www.tracktitan.io/post/december-2025-track-titan-update-faster-coaching-flows-social-leaderboards-bigger-team), [Review iRacerHUB](https://iracerhub.com/track-titan-iracing-review/), [Como analisar telemetria, Track Titan](https://www.tracktitan.io/post/how-to-analyse-telemetry-for-sim-racing).

### 2.3 VRS, referência profissional embutida + "biggest opportunity"

Modelo de **datapacks**: pacote por carro/série com setup, replay de hotlap, telemetria do coach e às vezes vídeo-tutorial por curva. O **Driving Analyzer** destaca automaticamente o trecho da pista com a **maior oportunidade de ganho** (oportunidades ordenadas da maior para a menor) e evidencia diferenças de linha, velocidade e inputs; permite estudar posição/orientação do carro nos pontos-chave da curva (brake point, turn-in, throttle point) e comparar padrões/hábitos, não só voltas isoladas. A própria VRS declara otimizar a UI "para pilotos, não para engenheiros".
Fontes: [VRS, usando datapacks](https://virtualracingschool.com/academy/iracing-career-guide/season-one/using-datapacks/), [VRS, practising efficiently](https://virtualracingschool.com/academy/iracing-career-guide/second-season/practising-efficiently-analysing/), [VRS FAQ](https://virtualracingschool.com/faq/), [Data Packs, vrs.racing](https://vrs.racing/data-packs).

### 2.4 Coach Dave Delta, o híbrido mais completo

Delta 6.0 combina: telemetria ao vivo + análise completa nos boxes; **Auto Insights** (IA que divide cada curva em 4 fases, frenagem, entrada, ápice, saída, e diz qual fase custou tempo e como corrigir); comparação contra voltas de pros, leaderboard global ou amigos; e **Video Analysis** frame a frame sincronizado com os traces (você vê o insight da IA ao lado do onboard do pro naquela curva). Parceria com **Popometer** para quem quer profundidade extra.
Fontes: [Delta 6.0](https://coachdaveacademy.com/delta/), [Auto Insights, doc](https://coachdaveacademy.com/documentation/how-to-use-auto-insights-ai-coaching-in-delta/), [Video Analysis](https://coachdaveacademy.com/announcements/video-analysis-levels-up/), [Traxion](https://traxion.gg/native-telemetry-tracking-and-analysis-added-to-coach-daves-delta-service/).

### 2.5 Popometer e Racelab

- **Popometer** (~5€/mês): plota seus dados contra um profissional em charts e track maps "expondo cada pequena diferença"; assinante tem análise avançada e customização de charts; foco em diferenças de estilo de pilotagem, wheel slip, temperaturas. Fluxo simples: rodar → menu "Laps" → filtrar/ordenar → comparar. ([Popometer](https://popometer.io/), [Guia](https://popometer.io/p/popoguide), [Parceria CDA](https://coachdaveacademy.com/announcements/coach-dave-academy-teams-up-with-popometer/))
- Racelab: primariamente overlays ao vivo (input telemetry comparando contra sua melhor volta ou amigos, laptime graph com filtros, laptime log), análise "leve" contínua em vez de sessão de análise profunda; biblioteca comunitária de layouts. ([Racelab](https://www.racelab.app/), [iRacing overlays](https://racelab.app/iracing/))

### 2.6 O caso Cosworth × iRacing: ferramenta pro "empacotada" para amador

A parceria Cosworth/iRacing entrega o Pi Toolbox de graça lendo `.ibt` nativamente, **com workbooks pré-montados por categoria**, a resposta da ferramenta de engenheiro ao problema do amador não foi simplificar o motor, foi **entregar templates prontos + tutoriais em vídeo**. ([iRacing × Cosworth](https://www.iracing.com/cosworth-and-iracing-unite-to-redefine-data-analysis-in-sim-racing/), [iRacing 101: Pi Toolbox](https://www.iracing.com/iracing-101-cosworth-pi-toolbox/), [Guia iRacerHUB](https://iracerhub.com/iracing-cosworth-pi-toolbox-guide/))

---

## 3. O espectro "engenheiro configurável" ↔ "coach automático"

| | Ferramenta de engenheiro (i2, Pi, WinTAX, RS3) | Coach automático (Track Titan, Auto Insights, VRS) |
|---|---|---|
| **Pergunta que responde** | "O que aconteceu?" (qualquer pergunta, se você souber montar a página) | "O que eu faço diferente na próxima volta?" |
| **Prós** | Profundidade ilimitada; math channels; qualquer canal/qualquer cruzamento; padrão da indústria; páginas reutilizáveis viram conhecimento institucional | Zero curva de aprendizado; tempo-até-insight em segundos; prioriza (um erro por vez); linguagem natural; funciona para quem "ignora telemetria por complexidade" |
| **Contras** | Curva de aprendizado brutal, descrito como "intimidante até para engenheiros experientes"; consenso de que "não vale para iniciantes"; o usuário precisa saber **qual pergunta fazer** | Opinião enlatada pode errar o diagnóstico causal; teto baixo para usuário avançado; opacidade ("por que a IA disse isso?"); depende de referência boa |

Fontes do consenso sobre complexidade: [Beginner's Guide to MoTeC, Trinacria](https://trinacriasimracing.wordpress.com/beginners-guide-to-telemetry-analysis-motec/), [MySimRig, telemetria p/ iniciantes](https://mysimrig.nl/en/blog/simracing/sim-racing-telemetry-for-beginners/), [Melhores apps 2026, Coach Dave](https://coachdaveacademy.com/tutorials/the-best-sim-racing-apps/).

**Como os híbridos resolvem**, três estratégias observadas:

1. **Camadas progressivas (Delta/VRS):** entrada pela opinião pronta (Auto Insights / biggest opportunity), com os traces completos um clique abaixo. O insight é *âncora de navegação* para o gráfico cru, a IA diz "Curva 4, fase de frenagem" e o gráfico já abre com zoom ali.
2. **Templates prontos sobre motor completo (Cosworth/AiM):** o poder total continua lá, mas o usuário abre em uma página curada (perfil/workbook default por categoria). Curadoria substitui simplificação.
3. **Referência automática (Garage 61/Popometer/VRS):** o maior custo cognitivo do amador não é ler gráfico, é **obter uma volta de referência confiável**. Resolver isso via comunidade/leaderboard/coach embutido já entrega 80% do valor mesmo com gráficos simples.

---

## 4. Padrões extraíveis (catálogo)

1. **Hierarquia de páginas salvas** (Workspace→Workbook→Worksheet / Profile): análise = conjunto nomeado e persistente de layouts, não estado efêmero de tela.
2. **Templates compartilháveis**: workspaces/perfis trocados entre usuários (GitHub, downloads de coaches), o layout é artefato distribuível e aplicável a qualquer sessão.
3. **Identidade global de canal**: cor/unidade/escala definidas uma vez, consistentes em todas as páginas.
4. **Modularidade de componentes**: página = grade de componentes plugáveis (trace, histograma, scatter, mapa, gauge, relatório tabular, vídeo) individualmente configuráveis.
5. **Presets por tipo de análise**: página "pilotagem" (speed/pedais/delta), "consistência" (laptime graph), "relatório" (mín/máx/média por volta/split), "vídeo".
6. **Overlay por distância + delta-time como canal rei**: comparação sempre alinhada por distância; variance/delta acumulado com acesso de 1 tecla (F3/F4 no i2).
7. **Cursor vinculado e zoom sincronizado**: um cursor global (posição na volta) move simultaneamente todos os gráficos, o marcador no mapa da pista e o frame do vídeo; zoom propagado entre componentes.
8. **Mapa "rainbow"**: pista pintada pelo valor de um canal (ou por ganho/perda vs referência), a visualização que mais rápido comunica "onde".
9. **Math channels**: canais derivados definíveis pelo usuário, inclusive referenciando a volta overlay (`ref:`).
10. **Troca de página por tecla / soft keys**: navegação sem mouse entre presets.
11. **Análise guiada priorizada**: motor que ordena oportunidades de ganho (maior primeiro) e explica causa em linguagem natural, uma por vez.
12. **Referência automática**: leaderboard comunitário, datapack de coach ou "sua melhor volta" como baseline default sem o usuário escolher nada.
13. **Ingestão zero-clique**: agente/upload automático; a sessão "aparece" na web.
14. **Vídeo sincronizado ao dado**: onboard frame-a-frame preso ao cursor.

---

## 5. Recomendações práticas para o Saru Analyzer (cliente não-técnico)

1. **Comece pelo veredito, não pelo gráfico.** Landing da sessão = 3-5 "cartões de insight" ordenados por impacto ("maior perda: trecho X, −0,3 s, frenagem tardia"), no padrão Track Titan/Auto Insights. Cada cartão é um **link que abre o gráfico já com zoom no trecho**, o insight vira navegação.
2. **Presets nomeados em vez de builder livre.** Ofereça 3-4 páginas prontas ("Visão geral", "Comparação de voltas", "Consistência", "Relatório") como os layouts default do RS3. Um builder de página modular (grid de componentes) pode existir, mas como recurso "avançado", nunca como caminho obrigatório.
3. **Delta-time sempre visível.** Na página de comparação, o gráfico de variance acumulada é fixo (não opcional), acima dos traces; a referência é escolhida automaticamente (melhor volta da sessão ou referência global) com opção de trocar.
4. **Um cursor global por sessão.** Estado único de posição-na-volta (por distância) sincronizando trace ↔ mapa da pista ↔ (futuro) vídeo, com zoom propagado. É o padrão técnico mais barato de implementar cedo e mais caro de retrofitar depois, modelar desde já como estado compartilhado (no caso do SARU: Zustand para cursor/zoom).
5. **Identidade global de canal como design token.** Cor/unidade/escala por canal definidas centralmente (mapa canal→token), nunca por gráfico, garante o mesmo verde de throttle em toda página e casa com o SSoT de tokens do frontend (`tokens.css`).
6. **Mapa colorido ("rainbow") como resumo espacial.** Para não-técnico, o traçado pintado por ganho/perda comunica mais que qualquer trace; usar como componente do cartão de insight e da visão geral.
7. **Templates como artefatos compartilháveis.** Se/quando houver builder, o layout salvo deve ser serializável (JSON) e compartilhável entre usuários/organizações, comportamento comprovado da comunidade MoTeC e da biblioteca de layouts do Racelab.
8. **Ingestão sem fricção.** Upload automático/arrastar-e-soltar e a sessão pronta ao abrir o browser (modelo Garage 61); nunca exigir configuração de canais antes do primeiro insight.
9. **Escada de profundidade em 3 degraus:** (a) insight em linguagem natural → (b) comparação visual pré-montada → (c) traces completos/canais livres. O usuário não-técnico fica no degrau a-b; o power user chega ao c sem trocar de produto, exatamente o posicionamento que Delta 6 e Pi Toolbox+templates ocupam hoje.
10. **Explique a opinião.** Todo insight automático deve mostrar "como cheguei aqui" (o trecho do trace que o justifica), mitigando o principal contra do coach automático (opacidade/diagnóstico causal errado).

### Fontes principais
- MoTeC: [i2 produto](https://software.motec.com.au/products/i2) · [i2 overview](https://www.motec.com.au/i2/i2overview/) · [i2 highlights](https://www.motec.com.au/i2/i2highlights/) · [Fórum variance](https://www.motec.com.au/forum/viewtopic.php?f=26&t=1231) · [Rainbow map](https://www.motec.com.au/forum/viewtopic.php?f=26&t=3697) · [Training seminar PDF](http://www.precisionautoresearch.com/DOWNLOADS/Motec%20Interpreter/i2%20Training%20Seminar%202008.pdf) · [SDMotecWorkspace](https://github.com/stevendaniluk/SDMotecWorkspace)
- AiM: [RS3 Analysis docs](https://www.aim-sportline.com/docs/racestudio3/manual/html/analysis.html) · [Manual PDF](https://www.aim-sportline.com/docs/racestudio3/manual/latex/racestudio3-manual-en-latest.pdf) · [James Colborn](https://www.jamescolborn.com/aim-data-analysis)
- Cosworth: [Pi Toolbox](https://www.cosworth.com/motorsport/products/pi-toolbox/) · [Soft keys PDF](https://www.cosworth.com/media/kvae1rog/pi-toolbox-13-and-soft-keys-v1-3.pdf) · [iRacing × Cosworth](https://www.iracing.com/cosworth-and-iracing-unite-to-redefine-data-analysis-in-sim-racing/) · [iRacing 101](https://www.iracing.com/iracing-101-cosworth-pi-toolbox/)
- WinTAX: [WinTAX4](https://store.racing-tech.net/wintax4/) · [PDF](https://store.racing-tech.net/content/WinTAX4.pdf) · [Laptime Club intro](https://www.laptimeclub.com/an-introduction-to-telemetry-systems-and-wintax/)
- Modernas: [Track Titan Coaching Flows](https://www.tracktitan.io/post/november-2025-update-coaching-flows) · [Review iRacerHUB](https://iracerhub.com/track-titan-iracing-review/) · [Garage61 docs](https://garage61.net/docs/usage) · [FUSION Racing G61](https://www.fusion-racing.org/iracing/iracing-apps/iracing-apps-garage61.php) · [VRS datapacks](https://virtualracingschool.com/academy/iracing-career-guide/season-one/using-datapacks/) · [VRS FAQ](https://virtualracingschool.com/faq/) · [Delta 6.0](https://coachdaveacademy.com/delta/) · [Auto Insights](https://coachdaveacademy.com/documentation/how-to-use-auto-insights-ai-coaching-in-delta/) · [Delta vs Garage 61](https://coachdaveacademy.com/tutorials/coach-dave-delta-vs-garage-61-which-is-best-for-you/) · [Popometer](https://popometer.io/) · [Racelab](https://www.racelab.app/) · [MySimRig beginners](https://mysimrig.nl/en/blog/simracing/sim-racing-telemetry-for-beginners/) · [Best apps 2026](https://coachdaveacademy.com/tutorials/the-best-sim-racing-apps/)

> Nota de método: vários sites-fonte recusaram fetch direto pelo proxy da sessão; o conteúdo vem
> dos resultados de busca detalhados sobre essas páginas, com as URLs originais citadas.
