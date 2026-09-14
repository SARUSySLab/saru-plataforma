---
titulo: "Pesquisa UI/UX, Sincronia entre vídeo onboard e telemetria (pista real + simulador)"
data: "2026-08-19"
origem: "_arquivo/saru-app/docs/research/2026-07-ui-ux-video-sincronizado.md"
status: "vigente"
area: "ui_marca"
---

# Pesquisa UI/UX, Sincronia entre vídeo onboard e telemetria (pista real + simulador)

> Bloco 5c do mapeamento de arquitetura/customização do Saru Analyzer (2026-07-19).
> Pergunta-guia: como as ferramentas sincronizam vídeo (GoPro, VBOX, replay de sim) com dados
> sobrepostos, e que padrões de UX valem para um analisador web voltado a cliente não-técnico.
> Companheiros: `2026-07-ui-ux-telemetria-ao-vivo.md` · `2026-07-ui-ux-analise-pos-sessao.md`.

---

## 1. Como cada ferramenta sincroniza vídeo↔dados (e como expõe isso na UI)

### Ecossistemas fechados: sync "de fábrica" (o padrão-ouro de UX)

**Racelogic VBOX Video HD2 + Circuit Tools**, o logger grava vídeo `.avi` e dados `.vbo` (GPS/CAN a 10 Hz+) **no mesmo hardware**, codificando a posição de pista no vídeo. Resultado: o usuário nunca vê uma etapa de "sincronizar", abre a sessão e o cursor do gráfico já move o vídeo frame a frame. Só existe um ajuste manual de *Video Synchronisation Offset* (em ms) escondido em menu, para casos de falha. Fontes: [VBOX Circuit Tools](https://www.vboxmotorsport.co.uk/us/circuit-tools), [Racelogic, Unsynchronised Video and Data](https://en.racelogic.support/VBOX_Motorsport/Software_Info/VBOX_Sim/Troubleshooting/Unsynchronised_Video_and_Data), [Manual Circuit Tools (PDF)](https://www.racelogic.co.uk/_downloads/vbox/Manuals/Software/CircuitTools_Software_Manual-EN.pdf).

**AiM SmartyCam + RaceStudio 3 Analysis**, a câmera recebe dados do logger/ECU (CAN/RS232/K-line) e grava um *data stream* embutido no `.MOV`. Na importação, o RS3A **reconhece automaticamente quais arquivos de dados e vídeo são vinculáveis e já propõe o link**; cursores ficam automaticamente sincronizados com o vídeo. Requisito: firmware recente + SmartyCam conectada ao logger durante a sessão. Fontes: [RaceStudio 3 Analysis docs](https://www.aim-sportline.com/docs/racestudio3/manual/html/analysis.html), [AiM SmartyCam 4](https://www.aimtechnologies.com/smartycam-4-corsa/).

**Garmin Catalyst / Catalyst 2**, câmera 1440p integrada ao próprio dispositivo com GPS 10 Hz: sync é invisível ao usuário por construção. Fontes: [Garmin Catalyst 2](https://www.garmin.com/en-US/newsroom/press-release/automotive/optimize-time-on-the-track-with-the-cutting-edge-garmin-catalyst-2/), [Manual Catalyst (PDF)](https://www8.garmin.com/manuals/webhelp/GUID-16C78876-E016-40FD-8A0A-049BA52B462B/EN-US/Catalyst_OM_and_Help_EN-US.pdf).

**MoTeC i2 Pro**, dois modos: (a) **VSM Video Sync Module**, que grava pulsos de sync na trilha de **áudio** de qualquer câmera → sync automático no i2; (b) manual, alinhando um mesmo ponto (site) no vídeo e nos dados. Exige às vezes conversão para AVI mjpeg e pasta de vídeos configurada em Tools > Options. Fontes: [MoTeC i2](https://www.motec.com.au/products/I2?catId=4), [MoTeC, i2 Pro video sync news](https://www.motec.com.au/latestnews/newsi2provideosync/), [VSM](https://www.fischermotorsports.com/fm-store/electrical-systems/motec-products/accessories/video-sync-module/).

### Ecossistemas abertos: sync automático por metadados + fallback manual

**RaceChrono Pro** (o melhor modelo de UX manual): ao importar vídeo, tenta **sync automático via GPS embutido no vídeo** (GoPro GPMF); falha se o GPS da câmera estava desligado ou os timestamps não caem na janela da sessão → thumbnail marca "**Not synchronised**" em vermelho. O sync manual é um modo dedicado: botão de corrente (link) abre estado "destravado" onde vídeo e gráfico se movem **independentemente**; botões **−50 ms / +50 ms** para nudge fino; botão de **cadeado** trava o vínculo (a partir daí movem-se juntos). Dica oficial: escolher um momento nítido e identificável (ex.: início do movimento). *Chapters* de GoPro são vinculados automaticamente após o primeiro arquivo. Fontes: [Tutorial linking video](https://racechrono.com/article/480), [Tutorial adjusting sync](https://racechrono.com/article/3293), [Overview de importação](https://racechrono.com/article/3128).

**Telemetry Overlay** (goprotelemetryextractor), se vídeo e dados têm bom *timing data* (GPS time no GPMF da GoPro, timestamps no FIT/GPX/CSV), **sync é automático**; senão, UI manual com: **offset** em s/ms, **Data Speed** (Real Time / Match Video / In-to-Out), **Stretch** (% de velocidade dos dados, para drift/time-lapse), **Starts/Ends Now** (ancorar início/fim dos dados no tempo atual do vídeo) e **copiar sync de outra fonte** já sincronizada. Fontes: [Telemetry Overlay](https://goprotelemetryextractor.com/telemetry-overlay-gps-video-sensors), [FAQ](https://goprotelemetryextractor.com/gopro-insta-dji-garmin-gpx), [Manual (PDF)](https://goprotelemetryextractor.com/docs/telemetry-overlay-manual.pdf), [tutorial de sync (YouTube)](https://www.youtube.com/watch?v=GZrn0BXFSqE).

**RaceRender (HP Tuners)**, *Sync Tool* abaixo da lista de inputs: popup ajusta a posição inicial do vídeo ou do arquivo de dados; o usuário confere no preview comparando a posição no *track map* (GPS) com o que vê no vídeo. Reconhecidamente "tedioso de acertar". Fontes: [RaceRender Sync Tool docs](https://racerender.com/RR3/docs/InputFileSync.html), [How-To Data Overlay](https://racerender.com/RR3/docs/HowTo-Datalogger.html). **TrackAddict** (mesmo fornecedor) grava vídeo + dados **no mesmo celular**, então o overlay interno já sai sincronizado; câmera externa → sync no RaceRender. Fontes: [TrackAddict](https://www.hptuners.com/products/trackaddict-racerender/), [Features](https://racerender.com/TrackAddict/Features.html).

**DashWare** (descontinuado, mas referência histórica de UX): dois sliders, um percorre o tempo do vídeo, outro o tempo dos dados; usuário acha o mesmo evento nos dois (ex.: "carro começa a andar" ↔ "velocidade começa a subir") e marca checkbox "Sync with video". Truque analógico clássico: filmar a tela do GPS mostrando hora/posição para criar ponto de referência. Fontes: [DashWare Sync Tutorial](http://www.dashware.net/videos/synchronization-tutorial-sample-file-download/), [FAQ](http://www.dashware.net/faq/).

**Base técnica GoPro (GPMF)**: gyro ~400 Hz, acelerômetro ~200 Hz, GPS ~18 Hz, timestamps GPS a 1 Hz; streams trazem timestamps próprios (STMP) e *PTS* na linha de tempo do vídeo para alinhar amostra↔frame. Atenção: relógio da câmera **deriva** (offset perceptível após 60-90 min). Fontes: [gpmf-parser](https://github.com/gopro/gpmf-parser), [GoPro Labs, GPS timing accuracy](https://github.com/gopro/labs/discussions/592), [Intro GPMF](https://www.trekview.org/blog/metadata-exif-xmp-360-video-files-gopro-gpmd/).

## 2. Padrões de overlay (widgets, anti-poluição, presets)

**Widgets canônicos** (interseção de todas as ferramentas): velocímetro (dial ou numérico), RPM + marcha, **barras de throttle/freio** (verde/vermelho), ângulo de volante, **mapa da pista com posição**, lap timer + **delta** vs. melhor volta, força G (g-ball / círculo de tração), e secundários (temperaturas, pressões, combustível, lean angle p/ moto). Fontes: [Telemetry Overlay, motorsports](https://goprotelemetryextractor.com/karting-motorbike-rally-trackday-overlay), [VBOX HD2 Setup](https://www.vboxmotorsport.co.uk/us/vbox-video-hd2-setup).

**Presets/templates**: VBOX usa "Scenes" (`.VVHSN`), cena default com speed gauge, g-ball, lap timing e track map, + **Online Scene Wizard** com templates por veículo e logo do usuário, até 8 cenas no aparelho; AiM RaceStudio 3 oferece *sets* gráficos pré-determinados com layout consistente (misturáveis) + logo + track map. Fontes: [HD2 scene files](https://www.vboxmotorsport.co.uk/index.php/en/support/hd2-scene-files), [SmartyCam 4](https://www.aimtechnologies.com/smartycam-4-corsa/).

**Anti-poluição (regras práticas encontradas)**: poucos widgets com propósito ("2 widgets limpos superam 6 amontoados"); posicionar onde o olho já vai (topo-centro, cantos inferiores); margem de 3-5% das bordas; ajustar tamanho/cor para legibilidade sem cobrir o apex; e cuidado com percepção de atraso, dado que "chega depois" da ação na tela mata a imersão. Fontes: [SimXPro, clean layouts](https://simxpro.com/en-us/blogs/guides/simhub-overlays-for-streaming-clean-layouts-for-obs-without-distractions), [BeInMotion, overlay tricks](https://motion-studio.io/en/blog/five-video-overlay-tricks-pro-youtubers), [vetkuro, telemetry overlays](https://vetkuro.com/blog/enhancing-insights-with-telemetry-overlays-a-new-perspective-on-racing-data).

## 3. Análise lado a lado com cursor vinculado

- Circuit Tools: clicar no gráfico → **os vídeos pulam para a posição correspondente na pista**; ALT+setas avança **uma amostra GPS por vez** (scrub frame-a-frame orientado a dados). Comparação de voltas exibe **dois vídeos 1080p lado a lado em câmera lenta**, com borda **verde na volta mais rápida e vermelha na mais lenta**, e canal **Delta-T** plotado por default junto com velocidade. Fontes: [Circuit Tools](https://www.vboxmotorsport.co.uk/us/circuit-tools), [User Guide "The Art of Going Faster"](https://en.racelogic.support/VBOX_Motorsport/Software_Info/Circuit_Tools/01_Circuit_Tools_-_Windows/Circuit_Tools_User_Guide/01_-_Circuit_Tools_The_Art_of_Going_Faster), [View Layout CT3](https://en.racelogic.support/VBOX_Motorsport/Software_Info/Circuit_Tools/Circuit_Tools_3/User_Guide/03_View_Layout).
- RaceStudio 3 Analysis: vídeo centrado na página com gráficos ao redor, cursores auto-sincronizados, **até 4 vídeos lado a lado sincronizados**. Fonte: [RS3A docs](https://www.aim-sportline.com/docs/racestudio3/manual/html/analysis.html).
- MoTeC i2 Pro: múltiplos streams de vídeo tocando em sincronia com qualquer componente de análise (gráficos, track map). Fonte: [MoTeC i2](https://www.motec.com.au/products/I2?catId=4).
- Garmin Catalyst: inverte o paradigma, em vez de gráficos, entrega **"Opportunities"** (top 3 momentos onde melhorar), vídeo com overlays (mapa, velocidade, delta, G-G) e o **True Optimal Lap** (vídeo emendado das melhores seções reais). Comparação de 2 voltas da mesma sessão na página Laps. Crítica de UX recorrente: o **scrub do cursor de vídeo é impreciso/frustrante** em review fino de curva. Fontes: [Hagerty review](https://www.hagerty.com/media/motorsports/review-garmin-catalyst/), [Winding Road review](https://windingroad.com/articles/reviews/gear-review-the-garmin-catalyst-driving-performance-optimizer-the-best-lap-timer/), [YourDataDriven](https://www.yourdatadriven.com/garmin-catalyst-review-optimal-lap-any-good/).

O padrão de interação comum: **um cursor mestre por tempo-na-volta (ou distância)**; qualquer superfície (gráfico, mapa, vídeo) é tanto controle quanto display; na comparação, cada volta mantém seu próprio vídeo e o alinhamento é **por distância percorrida**, não por tempo absoluto (por isso Delta-T funciona).

## 4. Especificidades do simulador

- **Replays de sim não carregam telemetria completa** (AC/ACC/iRacing): o fluxo dominante é (a) gravar overlay **ao vivo** por cima do jogo via OBS (SimHub/Racelab expõem overlays como URL de browser source), ou (b) gravar o replay em vídeo (OBS/ShadowPlay) + exportar telemetria (`.ibt` do iRacing → MoTeC via conversor **Mu**; ACC → MoTeC/CSV) e sincronizar depois. Fontes: [Racelab](https://www.racelab.app/), [SimHub OBS Connector](https://www.overtake.gg/threads/simhub-obs-connector.209721/), [Mu exporter](https://github.com/patrickmoore/Mu), [Coach Dave, MoTeC no iRacing](https://coachdaveacademy.com/tutorials/how-to-use-motec-data-in-iracing/).
- SimHub Replay: grava o feed de telemetria para replay posterior (tuning de dash/overlay), mas **não é time-synced por padrão**, replays de AC saem fora de sincronia porque a velocidade do replay não bate com a da gravação. Fontes: [SimHub forum, AC replay out of sync](https://www.simhubdash.com/community-2/simhub-support/telemetry-record-for-replays-in-assetto-corsa-out-of-sync/), [SimHub forum, rF2 replays](https://www.simhubdash.com/community-2/simhub-support/rfactor-2-recorded-telemetry-replays-are-not-playing-in-real-time/).
- **StintBox** (web/desktop, mira não-técnico): arrasta vídeo do replay + CSV; colunas auto-detectadas; **sync automático por timestamp**. [ACCReplay](https://www.accreplay.com/) extrai telemetria direto do arquivo de replay do ACC. Fontes: [StintBox](https://stintbox.app/), [StintBox × Assetto Corsa](https://stintbox.app/works-with/assetto-corsa).
- **Garage 61** (iRacing): plataforma web de telemetria com comparação de traces, ghost laps e track maps, **análise sem vídeo do usuário**; mostra que no sim o "vídeo" muitas vezes é substituído por replay 3D/ghost. Fontes: [Garage 61](https://garage61.net/docs/usage), [what's new](https://garage61.net/whatsnew).
- Diferenças vs. pista real: no sim (1) não há GPS time, o relógio comum é o timestamp do SO ou o tempo-de-sessão do jogo; (2) a telemetria é perfeita e densa (60 Hz+), sem drift de sensor, mas o *vídeo* é que é gerado depois (replay ≠ gravação ao vivo, câmeras podem mudar); (3) sync ao vivo via OBS elimina o problema, ao custo de "queimar" o overlay no vídeo, sem análise posterior interativa.

## 5. Padrões extraíveis e recomendação prática (analisador web, cliente não-técnico)

**Padrões que se repetem em todas as ferramentas boas:**

1. **Sync automático primeiro, manual como fallback visível.** Tente GPS time (GPMF/FIT) e timestamps de arquivo; se falhar, marque claramente ("Not synchronised", padrão RaceChrono) e ofereça o modo manual, nunca deixe dessincronia silenciosa.
2. **Modelo mental do sync manual = destravar → alinhar → travar.** Dois transportes independentes (vídeo e dados), botões de nudge (±50 ms / ±1 s), e um evento-âncora sugerido ao usuário ("pause no momento em que o carro começa a se mover; nós detectamos onde a velocidade sobe nos dados"). Auto-sugestão por correlação (início de movimento, pico de frenagem) reduz o trabalho a "confirmar".
3. **Um cursor mestre bidirecional.** Clicou no gráfico → vídeo busca o frame; scrub no vídeo → cursor anda no gráfico e no mapa. Guarde o mapeamento como `t_video = t_dados + offset` (+ *stretch* opcional para drift de relógio, necessário para vídeos >30 min, cf. drift GoPro).
4. **Comparação por distância, não por tempo.** Duas voltas = dois vídeos lado a lado avançando pela mesma posição de pista, com Delta-T no gráfico e código de cor rápida/lenta (verde/vermelho, padrão Circuit Tools).
5. **Overlay com presets, não editor livre de cara.** 3-4 layouts prontos (mínimo: velocidade+delta; padrão: +pedais+mapa; completo: +G+volante), margem de 3-5%, cantos inferiores/topo-centro, e widgets renderizados **como camada HTML/Canvas sobre o `<video>`** (não queimados), permite trocar layout sem re-render.
6. **Para o não-técnico, esconda a telemetria bruta atrás de conclusões** (lição do Catalyst): "você perdeu 0,3 s na curva 4 freando cedo, veja o vídeo" com deep-link do insight para o instante do vídeo vale mais que 12 canais plotados. E capriche no scrub fino (a maior reclamação de UX do Catalyst).
7. **Web tech concreta**: `requestVideoFrameCallback` para acoplar cursor↔frame com precisão; extração GPMF client-side é viável (ex.: [gopro-telemetry (npm)](https://www.npmjs.com/package/gopro-telemetry), [gpmf-parser](https://github.com/gopro/gpmf-parser)); para sim, aceitar CSV/`.ibt` convertido + vídeo de replay com sync por timestamp (modelo StintBox).

> Nota de método: fetch direto de várias páginas primárias foi bloqueado pelo proxy do ambiente; o relatório foi construído a partir de resultados de busca detalhados, com todas as URLs citadas para verificação.
