---
titulo: "Pesquisa, Aquisição de Dados (PI Toolbox · dataloggers · sims · GPS/OBD)"
data: "2026-08-19"
origem: "_arquivo/saru-app/docs/research/2026-07-aquisicao-de-dados.md"
status: "vigente"
area: "telemetria"
---

# Pesquisa, Aquisição de Dados (PI Toolbox · dataloggers · sims · GPS/OBD)

> **Data:** 2026-07-13 · **Método:** pesquisa web com URLs por afirmação; ⚠️ = não confirmado.
> Consumidores: roadmap de parsers do engine (`saru_lapanalyzer/infra/datasources/`),
> onboarding de ingestão por persona (ver `docs/product/personas-e-modularidade.md`).

## 1. Porsche Cup Brasil, Cosworth Pi (não Bosch) ⚠️ premissa corrigida

- O **992/991 GT3 Cup usa eletrônica de aquisição Cosworth** (logger *Badenia*, display CDU,
  ICD), analisada no **Pi Toolbox** (há versão "Porsche-approved" v13), [Cosworth/Porsche Motorsport](https://www.cosworth.com/motorsport/support/porsche-motorsport/),
  [suporte 991 Gen1](https://support.cosworth.com/porsche-991-gt3-cup-gen1-422867)/[Gen2](https://support.cosworth.com/porsche-991-gt3-cup-gen2-593034).
  A Bosch fornece ECU de motor; WinDarab é mais relevante p/ **Stock Car** e categorias com
  logger Bosch. ⚠️ "Bosch C 80 na Porsche Cup Brasil": não confirmado.
- **Pi Toolbox exporta ASCII, Excel, MATLAB e XML**, com *triggers* de exportação (outing,
  lap, evento), [Pi Toolbox 13 New Features](https://www.cosworth.com/media/kvae1rog/pi-toolbox-13-and-soft-keys-v1-3.pdf),
  [Product Information](https://www.cosworth.com/media/2erfisc1/pi-toolbox-product-information-v2.pdf).
  Formato nativo **.pds** é fechado (lido só por software Cosworth), [suporte: ASCII import/PDS](https://support.cosworth.com/post/pitool-box-ascii-file-import-or-conversion-into-pds-format-12290063).
  ⚠️ automação por CLI do export: não confirmada (docs mostram triggers na UI).
- **Não existe parser open-source de .pds.** O que existe: *writer* do dialeto "Pi Toolbox
  ASCII" no [BenergyRacing/racing-data-converter](https://github.com/BenergyRacing/racing-data-converter)
  (TS, GPL-2.0), serve como **spec de fato** do formato texto; e "Aim2PiToolbox" (AiM→Pi
  ASCII), [HiPo Driver](https://www.hipodriver.com/resources).
- **Bônus:** a Cosworth distribui **Pi Toolbox gratuito para iRacing**, [iracing.com/cosworth-pi-toolbox](https://www.iracing.com/cosworth-pi-toolbox/), um reader
  de Pi ASCII atende Cup real **e** sim racers de Pi.

## 2. Bosch WinDarab (Stock Car e afins)

- Log atual: **`.bmsbin`** (`.bin` legado). Sem parser open-source; o repo
  [boschmotorsport/WinDarab](https://github.com/boschmotorsport/WinDarab) é só doc/releases.
- **WinDarab Free exporta texto** (txt), [vídeo export](https://www.youtube.com/watch?v=GYOfZ6smDjs);
  o txt é importável até no MoTeC i2, [HP Academy](https://www.hpacademy.com/forum/professional-motorsport-data-analysis/show/can-someone-help-me-import-windarab-txt-file-in-i2-pro/).
  O engine já tem `real_windarab_csv.py`, validar contra exports reais.
- **API programática:** COM-API / **BMS2API** (lê datafile sem abrir WinDarab; licença anual
  atrelada ao Expert; Windows), [wiki Bosch](https://www.bosch-motorsport.com/content/downloads/WinDarab_Wiki/en-GB/239912075.html) (⚠️ página 403 no fetch, resumo via snippet),
  [XTRA Motorsport](https://xtramotorsport.com/product/bosch-motorsport-com-api-for-windarab-expert-yearly-license/).
- **Rota:** ingestão do export txt (curto prazo); worker Windows + BMS2API se houver demanda
  de automação (médio prazo). **Não** reverse-engineer `.bmsbin`/`.pds`.

## 3. MoTeC .ldx

- XML *sidecar* do `.ld` com **beacons/laps** e maths, [filext](https://filext.com/file-extension/LDX), [MoTeC Forum](https://forum.motec.com.au/viewtopic.php?f=26&t=4480).
- Estrutura confirmada no gerador do sim-to-motec
  ([`stm/motec/ldx.py`](https://github.com/GeekyDeaks/sim-to-motec/blob/main/stm/motec/ldx.py)):
  `LDXFile > Layers > Layer > MarkerBlock > MarkerGroup[Name="Beacons"] > Marker` com
  `Time` em **µs acumulados**; bloco `Details` (Total Laps, Fastest Time/Lap).
- [gotzl/ldparser](https://github.com/gotzl/ldparser) (o que usamos) **não lê .ldx**;
  referências cruzadas: [afonso360/motec-i2](https://github.com/afonso360/motec-i2) (Rust,
  lê/escreve ld+ldx). Parse via `xml.etree` = **esforço baixo, alto retorno** (laps corretos
  p/ ACC nativo, ACTI/AC, sim-to-motec GT7/AMS2, Mu/iRacing).

## 4. Outros formatos de logger (".dat" não é um formato)

| Ecossistema | Nativo | Rota | Fonte |
|---|---|---|---|
| Bosch WinDarab | `.bmsbin` | export txt / BMS2API | [lapsim.nl](https://lapsim.nl/load_oncar_data.html) |
| AEM/GEMS | proprietário (importam `.stf`) | não priorizar | [Autosport Labs forum](https://forum.autosportlabs.com/viewtopic.php?t=3731) |
| Haltech/ECUMaster/Link/MegaSquirt/rusEFI | logs próprios | spec via [UltraLog](https://github.com/ClassicMiniDIY/UltraLog) (OSS, multi-ECU) se houver demanda | [ultralog.co](https://ultralog.co/) |
| EFI Analytics | `.msl`/`.mlg` | writers no racing-data-converter | idem |
| RaceCapture | **CSV aberto** | trivial | [RaceRender](https://racerender.com/RR3/docs/Dataloggers.html) |

## 5. Simuladores (estado 2025-2026)

- **ACC:** exporta **MoTeC `.ld` + `.ldx` nativo** (Setup→Electronics; `Documents/ACC/MoTeC`), [Coach Dave](https://coachdaveacademy.com/tutorials/how-to-use-motec-data-in-assetto-corsa-competizione/). Já coberto pelo nosso `.ld`; falta `.ldx`.
- **AC (original):** sem export nativo → **ACTI** grava compatível com MoTeC i2, [OverTake](https://www.overtake.gg/downloads/acti-assetto-corsa-telemetry-interface.3948/).
- **GT7:** UDP criptografado (Salsa20), reverse-engineered, [Bornhall/gt7telemetry](https://github.com/Bornhall/gt7telemetry),
  [snipem/gt7dashboard](https://github.com/snipem/gt7dashboard);
  **[GeekyDeaks/sim-to-motec](https://github.com/GeekyDeaks/sim-to-motec)** captura a 60 Hz e
  escreve `.ld`/`.ldx` (também AMS2). Fork: [GT7toMoTeC](https://github.com/cybercic/GT7toMoTeC).
- **AMS2:** shared memory PCARS2/UDP, [CREST2-AMS2](https://github.com/viper4gh/CREST2-AMS2);
  export MoTeC via sim-to-motec.
- **iRacing:** `.ibt` + [pyirsdk](https://github.com/kutu/pyirsdk);
  conversor [patrickmoore/Mu](https://github.com/patrickmoore/Mu) (ibt→MoTeC); Pi Toolbox
  gratuito p/ iRacing (§1).
- **Padrão estratégico:** o ecossistema converge para **MoTeC `.ld`/`.ldx` como intercâmbio**, nosso parser `.ld` é o hub; `.ldx` destrava tudo de uma vez.

## 6. GPS/OBD, carros de rua em track day

- **RaceChrono Pro:** exporta CSV v2/v3, **VBO**, NMEA, [racechrono.com/support](https://racechrono.com/support).
- **Harry's LapTimer:** GPX/VBO; `.hlptrl` é XML, [fórum oficial](http://forum.gps-laptimer.de/viewtopic.php?t=6120).
- **TrackAddict:** CSV/`.tad`; [VBO Converter](https://vbo-converter.com/) converte
  AiM/RaceChrono/TrackAddict/Harry's → VBO/CSV.
- **RaceBox Mini (25 Hz):** exporta CSV/VBO/GPX, [racebox.pro](https://www.racebox.pro/info/session-export) (⚠️ fetch bloqueado, confirmado por snippet).
- **VBOX `.vbo`: formato TEXTO documentado oficialmente**, [Racelogic Support](https://en.racelogic.support/Knowledge_Base/.VBO_Files);
  parsers OSS: [quentinsf/vboxutils](https://github.com/quentinsf/vboxutils),
  [lbulej/vbo-tools](https://github.com/lbulej/vbo-tools).
- **OBD-II:** taxa compartilhada entre canais, ELM327 ~15-40 Hz totais; OBDLink MX+ ~50 Hz, [RaceChrono support](https://racechrono.com/support), [Miatafy](https://miatafy.com/nd-miata/lap-timing-apps/).
  → OBD é **enriquecimento de baixa taxa** (RPM/throttle/temps) sobre GPS 10-25 Hz; não é rota
  p/ dinâmica de alta frequência. Não construir logger próprio.

## 7. Recomendações priorizadas

| # | Item | Esforço | Risco | Retorno |
|---|---|---|---|---|
| 1 | **Parser `.ldx`** (beacons→laps) somado ao `.ld` | Baixo (1-2 d) | Baixo | ACC, AC/ACTI, GT7/AMS2 (sim-to-motec), iRacing (Mu) de uma vez |
| 2 | **Reader `.vbo`** (texto documentado) | Baixo | Baixo | RaceChrono, RaceBox, Harry's, TrackAddict, VBOX = todo o público track day |
| 3 | **Reader "Pi Toolbox ASCII"** | Médio | Baixo-méd. | Porsche Cup BR + usuários Pi/iRacing; validar com export real de um time |
| 4 | **Reader WinDarab txt** (validar o existente) | Baixo-méd. | Baixo | Bosch/Stock Car; fase 2 opcional BMS2API (licença, Windows) |
| 5 | **iRacing `.ibt` direto** (pyirsdk) | Médio | Baixo | elimina passo manual |
| 6 | Gravador GT7 UDP próprio | Médio | Médio (protocolo não oficial) | alternativa: instruir sim-to-motec + upload `.ld/.ldx` (custo zero c/ item 1) |
| 7 | OBD |, |, | ingerir CSV do RaceChrono com canais OBD; documentar limite de taxa |

**A validar com um time da Cup:** hardware exato de logging da série; automação de export do
Pi Toolbox; detalhes do BMS2API.
