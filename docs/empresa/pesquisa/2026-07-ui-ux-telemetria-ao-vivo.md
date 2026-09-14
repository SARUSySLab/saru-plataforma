---
titulo: "Pesquisa UI/UX, Telemetria ao vivo (GT7, Assetto Corsa e ecossistema)"
data: "2026-08-19"
origem: "_arquivo/saru-app/docs/research/2026-07-ui-ux-telemetria-ao-vivo.md"
status: "vigente"
area: "ui_marca"
---

# Pesquisa UI/UX, Telemetria ao vivo (GT7, Assetto Corsa e ecossistema)

> Bloco 5a do mapeamento de arquitetura/customização do Saru Analyzer (2026-07-19).
> Pergunta-guia: como jogos e overlays apresentam dezenas de canais **sem sobrecarregar o usuário**,
> e o que disso se aplica a um analisador web para clientes não-técnicos.
> Companheiros: `2026-07-ui-ux-analise-pos-sessao.md` · `2026-07-ui-ux-video-sincronizado.md`.

---

## 1. Gran Turismo 7: minimalismo imposto + ecossistema em camadas

### HUD in-game: pouquíssimo, e condicional
- O HUD nativo do GT7 é deliberadamente enxuto: mapa da pista, standings, contagem de voltas, combustível/pneus, e a opção "Race Info Only" reduz a tela a standings + voltas + traçado nos cantos superiores. Não há customização granular (nem opacidade, nem seleção item a item), a filosofia é "um bom default, não um construtor de HUD".
- **Elementos condicionais:** TCS, Fuel Map, brake balance e distribuição de torque **só aparecem se o carro tem o recurso e a prova permite usá-lo**. Isso é simplificação por contexto: o canal não existe na tela quando não é acionável.
- **Delta ao vivo só em Time Trial**, o dado aparece apenas no modo em que é a métrica central. Temperatura de pneu existe na simulação desde o GT Sport, mas **não é mostrada ao jogador**, foi julgada dado de engenheiro, não de piloto.

### A API UDP e a divisão de trabalho jogo ↔ apps
- A telemetria completa sai por UDP (portas 33739/33740, pacotes estendidos "B"/"~" desde o update 1.42, com sway/heave/surge, surface type por pneu etc.). O jogo mantém o HUD simples e **delega a densidade a apps externos**: EzioDash (dash simples em iOS), RS Dash, SimHub, gt7dashboard.
- O **gt7dashboard** (open source, referência de análise pós-volta) organiza tudo em **duas abas com nomes de tarefa, não de dado**: "Get Faster" (delta vs. volta de referência, velocidade×distância, throttle/brake/coast) e "Race Line" (traçado colorido: verde = acelerando, vermelho = freando, azul = coasting, com picos/vales de velocidade). A âncora de tudo é **uma volta de referência** (default = melhor volta): "tudo abaixo da barra em 0 é mais lento que a referência; acima, mais rápido". Uma única pergunta ("onde perdi tempo?") estrutura a tela inteira.

**Lição GT7:** default minimalista + canais condicionais ao contexto + densidade movida para uma camada de análise separada, sempre ancorada em comparação contra referência.

## 2. AC/ACC, iRacing e overlays: como os densos se organizam

### ACC, MFD: paginação de 4 páginas, uma por vez
- O MFD do ACC tem **4 páginas + off** (posições em tempo real, standings, eletrônica, pitstop), cicladas com um botão, cada página com atalho dedicado. Nunca há mais de uma página visível: é *progressive disclosure* por paginação, operável sem tirar a mão do volante.
- A página de pitstop suporta **até 30 estratégias pré-criadas** (pressões, pneus wet/dry, combustível, pastilhas) selecionáveis ao vivo, decisão complexa reduzida a "escolher um preset" no calor da corrida. "Fuel to End" é calculado e atualizado em tempo real, **o jogo entrega a conclusão, não os operandos**.

### iRacing, black boxes: um painel por tarefa, sob demanda
- Informação de carro vive em "black boxes" cicláveis por F1-F10 (timing, standings, relative, fuel, pneus, ajustes in-car, rádio...), exibidas **uma de cada vez** num canto fixo. Relative e Standings têm estados **minimizado e expandido**; Alt+K permite mover/ativar elementos.
- Guias de comunidade (Coach Dave, Traxion) convergem: manter na tela só relative + delta, e chamar fuel/tires apenas quando a decisão se aproxima.

### SimHub, o construtor, e as regras de bom senso da comunidade
- SimHub é o canivete suíço (dashboards, overlays, layouts por jogo), com um limite técnico revelador: **overlays são limitados a 480.000 px² (800×600)**, restrição de performance que força concisão.
- Boas práticas destiladas dos guias (SimXPro, iRacerHUB, EveZone):
  - Legibilidade a 250 km/h: alto contraste, fontes grandes, design simples; o que é bonito em screenshot pode ser ilegível em corrida.
  - Trio inicial padrão: relative + fuel calculator + input trace, cobre as lacunas do HUD nativo antes de qualquer coisa; adicionar depois, um a um.
  - "Prefira estado a dado": *"'Pitting in 2 laps' beats 8 fuel numbers"*, mostrar a conclusão, não os insumos.
  - Rotular todo delta (delta contra o quê?); evitar animações desnecessárias; posicionar fora da linha de visão do traçado.

### RaceLab, presets automáticos e blocos modulares
- Overlays com **auto-switching de layout por tipo de sessão e por carro** ("set it once and race forever"), o preset corrida/quali/prática troca sozinho.
- Data Blocks: HUD montável com **80+ widgets** e temas; cada overlay permite controlar transparência, fonte e **adicionar/remover seções de informação**. Modularidade com defaults prontos: o usuário casual usa o padrão, o avançado compõe.

### CrewChief, o canal auditivo como válvula de escape
- CrewChief (engenheiro/spotter por voz) tira dados da tela e entrega **eventos por exceção** no áudio (carro ao lado, dano, janela de pit). É altamente configurável: dá para desligar avisos redundantes e **limitar "complaints" por sessão (de 60 para 5)**, até o canal de exceções tem orçamento de interrupções. Alternativa ainda mais enxuta: beeps em vez de voz.

### Coach Dave Delta, telemetria para não-técnicos (o benchmark direto)
- Delta é o produto que mais se aproxima do problema "telemetria para leigos": interface onde "cada elemento tem um propósito claro e o layout guia naturalmente à informação, **sem exigir experiência com software de telemetria**".
- Mecânicas-chave: **drag & drop de uma volta do leaderboard** para comparar com a sua; gráfico de delta com tempo ganho/perdido em cada ponto + resumos por canal (speed, throttle, brake, steering, gear); **AI coach que diz em texto o que você fez diferente da referência**. Suporta iRacing, ACC, LMU, ACEvo, GT7, AMS2, AC.

## 3. Padrões extraíveis (catálogo)

| # | Padrão | Onde aparece |
|---|--------|--------------|
| P1 | **Default minimalista, densidade opcional** | GT7 "Race Info Only"; trio inicial SimHub |
| P2 | **Canais condicionais ao contexto** (dado só existe se acionável) | GT7 (TCS/fuel map só se o carro tem); ACC MFD |
| P3 | **Paginação/um painel por tarefa** em vez de tudo simultâneo | ACC MFD (4 páginas), iRacing black boxes (F1-F10) |
| P4 | **Estado > dado** (conclusão calculada, não operandos) | "Fuel to End" do ACC; "pitting in 2 laps" |
| P5 | **Tudo relativo a uma referência** (delta como métrica mestra) | gt7dashboard, Delta, GT7 time trial |
| P6 | **Alerta por exceção + orçamento de interrupções** | CrewChief (limite de complaints) |
| P7 | **Presets por contexto com auto-switch** (corrida/quali/prática, por carro) | RaceLab; estratégias de pit do ACC |
| P8 | **Widgets modulares com defaults curados** | RaceLab Data Blocks (80+), SimHub |
| P9 | **Codificação de cor semântica fixa** (verde=aceleração, vermelho=freio, azul=coasting) | gt7dashboard race line |
| P10 | **Orçamento de tela** (limite físico de área por widget) | SimHub 480k px² |
| P11 | **Estados minimizado/expandido por widget** | iRacing Relative/Standings |
| P12 | **Camada de coach em linguagem natural sobre os dados** | Delta AI coach; CrewChief |

Estes padrões são instâncias de *progressive disclosure* (Nielsen, 1995) e das práticas de dashboard UX: sumário primeiro, detalhe sob demanda; hierarquia visual primário/secundário; drill-down em vez de tela única com tudo (Pencil & Paper, UXPin).

## 4. Recomendações para o Saru Analyzer (cliente não-técnico)

1. **Home = 3 respostas, não 30 canais (P1, P4, P5).** A primeira tela responde: "quão rápido fui?", "onde perdi tempo?" (delta vs. volta de referência com barra em zero), "o que fazer diferente?" (1-3 insights em texto). Canais brutos ficam atrás de um "ver detalhes".
2. **Volta de referência como espinha dorsal (P5).** Todo gráfico é comparação contra referência (melhor volta própria por default; trocável). Nunca mostrar um canal absoluto sem contexto de comparação, o leigo não sabe se "82% de freio" é bom.
3. **Abas por pergunta, não por sensor (P3).** Seguir o gt7dashboard: "Onde ganhar tempo" / "Traçado" / "Consistência", em vez de "RPM", "Suspensão", "Pneus".
4. **Mostrar estado calculado, não dado cru (P4).** "Freou 8 m tarde na curva 3" em vez do trace de pressão de freio; o trace fica um clique abaixo, como evidência.
5. **Exceções ganham destaque; o normal fica quieto (P6).** Cinza/neutro quando dentro da faixa; cor só quando há algo a agir (travamento de roda, pneu fora de temperatura). Limitar o número de alertas simultâneos (orçamento à la CrewChief).
6. **Presets por contexto (P7):** perfis "Corrida", "Quali/Hotlap", "Prática/Setup" que mudam quais widgets e alertas existem, com auto-seleção pelo tipo de sessão do arquivo, e "modo simples/avançado" por usuário.
7. **Widgets modulares com curadoria (P8, P10, P11):** layout default fechado e bom; edição (adicionar/remover/arrastar, minimizar/expandir) como recurso avançado, com limite de widgets por tela para impedir o usuário de construir a própria sobrecarga.
8. **Cor semântica fixa e acessível (P9):** um vocabulário único (aceleração/freio/coasting; ganho/perda de tempo) usado identicamente em todos os gráficos; fundo escuro de alto contraste (norma do gênero, e alinhado ao design flat near-black do produto).
9. **Progressive disclosure literal:** hover/clique para detalhe, drill-down por curva (visão da volta → visão da curva → canais crus), accordions para canais secundários.
10. **Camada de linguagem natural (P12):** o diferencial do Delta para leigos é o coach que traduz dado em frase acionável, para clientes não-técnicos, um resumo textual automático por volta/sessão provavelmente vale mais que qualquer gráfico adicional.

## Fontes

- GT7: [gt7dashboard (GitHub)](https://github.com/snipem/gt7dashboard) · [GTPlanet, GT7 telemetry via open-source](https://www.gtplanet.net/gran-turismo-7-telemetry-data-now-available-via-open-source-software/) · [GTPlanet, GT7 HUD Options](https://www.gtplanet.net/forum/threads/gt7-hud-options.430454/) · [Gamepur, display settings](https://www.gamepur.com/guides/how-to-change-display-settings-in-gran-turismo-7) · [Manual oficial GT7, Race Screen](https://www.gran-turismo.com/gb/gt7/manual/race/02) · [GTPlanet, tyre temperature](https://www.gtplanet.net/forum/threads/tyre-temperature.406736/) · [SimHub issue #2254, pacotes estendidos GT7](https://github.com/SHWotever/SimHub/issues/2254) · [HackerNoon, SimHub + GT7](https://hackernoon.com/how-to-set-up-simhub-with-gran-turismo-7) · [EzioDash](https://granturismosport.se/eziodash/) · [RS Dash GT7](https://www.rsdash.com/rs-dash-gt7) · [Traxion, GT7 time trial telemetry app](https://traxion.gg/the-app-that-can-monitor-gran-turismo-7-time-trial-telemetry-tyre-pressures-and-racing-lines/)
- SimHub/overlays: [SimHub Wiki, Dash Studio Overlays](https://github.com/SHWotever/SimHub/wiki/Dash-Studio-Overlays) · [SimXPro, SimHub guide](https://simxpro.com/en-us/blogs/guides/simhub-for-sim-racing-dashboards-overlays-and-the-why-behind-it) · [SimXPro, overlays para OBS](https://simxpro.com/en-us/blogs/guides/simhub-overlays-for-streaming-clean-layouts-for-obs-without-distractions) · [iRacerHUB, SimHub setup](https://iracerhub.com/simhub-iracing-setup-guide/) · [EveZone, second-screen dashboards](https://evezone.evetech.co.za/build-lab/simhub-dashboard-second-screen-guide/)
- RaceLab: [racelab.app/iracing](https://racelab.app/iracing/) · [Simracing-PC, Racelab guide](https://simracing-pc.de/en/racelab-overlay-2/) · [simracingcockpit.gg, RaceLab](https://simracingcockpit.gg/iracing-overlay-racelabapps/)
- ACC/iRacing: [Steam, ACC MFD pages](https://steamcommunity.com/app/805550/discussions/0/2983033649172760952/) · [Traxion, pit stops no ACC](https://traxion.gg/the-dark-art-of-mastering-pit-stops-in-assetto-corsa-competizione/) · [iRacing Support, Black Box controls](https://support.iracing.com/support/solutions/articles/31000167257-black-box-screen-information-and-controls) · [Coach Dave, iRacing HUD](https://coachdaveacademy.com/tutorials/how-to-set-up-your-hud-in-iracing/) · [Traxion, iRacing UI guide](https://traxion.gg/iracing-ui-guide-how-to-customize-and-move-the-hud/) · [OverTake, Live Telemetry Evo (ACC)](https://www.overtake.gg/downloads/live-telemetry-evo.84121/)
- CrewChief: [simracingsetup.com, Crew Chief para iRacing](https://simracingsetup.com/iracing/how-to-set-up-crew-chief-for-iracing/) · [OverTake, Electronic Beeping Spotter](https://www.overtake.gg/downloads/electronic-beeping-spotter-crewchief.59774/)
- Coach Dave Delta: [Delta](https://coachdaveacademy.com/delta/) · [Guia de telemetria com Delta](https://coachdaveacademy.com/tutorials/a-delta-guide-the-power-of-data-in-sim-racing/) · [Comparar voltas no Delta](https://coachdaveacademy.com/documentation/how-to-compare-laps-in-delta/) · [Traxion, telemetria nativa no Delta](https://traxion.gg/native-telemetry-tracking-and-analysis-added-to-coach-daves-delta-service/)
- UX geral: [Pencil & Paper, Dashboard UX patterns](https://www.pencilandpaper.io/articles/ux-pattern-analysis-data-dashboards) · [UXPin, Progressive Disclosure](https://www.uxpin.com/studio/blog/what-is-progressive-disclosure/) · [LogRocket, Progressive disclosure](https://blog.logrocket.com/ux-design/progressive-disclosure-ux-types-use-cases/)

> Nota de método: algumas páginas primárias (racelab.app, coachdaveacademy.com, gran-turismo.com, simxpro.com) bloquearam fetch direto; o conteúdo delas foi obtido via resultados de busca indexados e fontes secundárias, e as afirmações acima refletem apenas o que apareceu nesses excertos.
