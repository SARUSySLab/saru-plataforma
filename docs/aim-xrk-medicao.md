# Medição de cobertura do leitor AiM RaceStudio 3 `.xrk` (2026-09-14)

## Resultado

| item | valor |
|---|---|
| arquivos únicos no acervo (hash) | 687 |
| amostra medida | 10 arquivos únicos, sorteio aleatório (seed 42) sobre o inventário `docs/handoff/agy/inventario-telemetria-2026-09-14.tsv`, commit `b0548b5` |
| abriram sem erro (`inspecionar`) | 10/10 |
| canais declarados por arquivo | média 32,3 (mín. 20, máx. 61) |
| canais mapeados em `seeds/aliases.yaml` (perfil `aim_xrk`) | média 7,1 |
| cobertura agregada | 22,0% dos canais declarados |
| velocidade de `inspecionar()` | média 34,8 MB/s (mín. 24,5, máx. 43,1) |

## O que foi medido

Amostra de 10 arquivos `.xrk` únicos (por hash MD5) sorteados do inventário do
acervo, copiados do Drive via `rclone copy gdrive-rw: ... --files-from`.
Cada arquivo passou por `readers.formatos.detectar()` e depois por
`LeitorXrk.inspecionar()` (`src/saru_poc/readers/xrk.py`), com o tempo de
parede cronometrado por `time.perf_counter()`. Os nomes brutos de canal
(`CanalBruto.nome_bruto`) de cada arquivo foram comparados contra a união de
todas as colunas (`col`, string ou lista) do perfil `aim_xrk` em
`seeds/aliases.yaml`.

## Tabela por arquivo

| arquivo | tamanho MB | tempo `inspecionar` (s) | MB/s | canais declarados | canais mapeados |
|---|---|---|---|---|---|
| 1st Race_20211125_151714.xrk | 0,831 | 0,034 | 24,5 | 20 | 6 |
| Bruno Novillo_Superpole_20221022_132625.xrk | 0,062 | 0,0023 | 26,9 | 29 | 7 |
| Caua Rodrigues_Practice 3_20221022_094238.xrk | 2,071 | 0,0586 | 35,3 | 29 | 7 |
| Caua Rodrigues_Superpole_20221022_123606.xrk | 0,164 | 0,0046 | 35,8 | 29 | 7 |
| FELIPE PAN_54_POTENZA_Generic testing_a_0068.xrk | 4,069 | 0,1157 | 35,2 | 61 | 9 |
| Gabriel Carioca_22 R6_Interlago SP_Generic testing_a_0338.xrk | 3,619 | 0,1029 | 35,2 | 30 | 7 |
| Gonzalo Augusto_Practice 1_20221125_114149.xrk | 2,079 | 0,0483 | 43,1 | 28 | 7 |
| Igor Cruz_Chery TIGGO5X_Rua_Generic testing_a_0552.xrk | 1,482 | 0,0433 | 34,2 | 39 | 7 |
| Jeronimo Gonzles_Practice 1_20221021_113648.xrk | 1,766 | 0,049 | 36,1 | 29 | 7 |
| Joao Almeida_911 turbo s_NelsonPiquet_Testes genéricos_a_0072.xrk | 4,931 | 0,1185 | 41,6 | 29 | 7 |

## O que fica de fora e por quê

Canais não mapeados presentes em **todos os 10 arquivos** da amostra (não é
ruído de um arquivo isolado):

`Best Run Diff`, `Best Today Diff`, `External Voltage`, `GPS Altitude`,
`GPS_Fix`, `GPS_Position_Accuracy`, `GPS_Satellites`, `GPS_Velocity_Accuracy`,
`GPS_Yaw_Rate`, `GPS_pDOP`, `Internal Battery`, `Master Clk`,
`Predictive Time`. `iGPS` e `Distance Lap` aparecem em 9 dos 10.

Nenhum desses é ruído de instalação (como os aliases já documentados de
`throttle`/`brake` que variam por carro): são metadados de qualidade de GPS
e telemetria de estado do logger, presentes de forma sistemática em todo
arquivo AiM RaceStudio 3 do acervo, e hoje nenhum tem canônico. `GPS Altitude`
em particular é usado por outros formatos (MoTeC declara `gps_lat`/`gps_lon`
mas nenhum `.xrk` do acervo tem `gps_altitude` mapeado) e seria coerente
mapear junto de `gps_lat`/`gps_lon`.

`ler()` roda sem erro nos 2 arquivos testados (amostra menor, fora do escopo
de tempo desta medição), mas o número de linhas por lote não é comparável
1:1 com a soma de `n_amostras` por canal declarado em `inspecionar()`: canais
de taxas diferentes viram lotes (`Lote.frequencia_hz`) separados, então a
soma de amostras por canal conta cada linha várias vezes (uma vez por canal
daquela taxa). Não há evidência, nesta medição, de perda de amostra em
`ler()`; confirmar isso exigiria o mesmo tipo de teste de invariante que
`.pds`/`.pid` já têm, fora do escopo desta auditoria.

Issue aberta para a lacuna de cobertura: ver `docs/cobertura-de-dados-resumo.md`.
