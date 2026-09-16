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

## `.xrk` e `.xrz` da mesma captura (2026-09-15, issue #53)

O `.xrz` guarda o mesmo stream do `.xrk` comprimido em zlib. Em nenhuma dupla
do acervo o conteúdo diverge. A diferença, quando existe, é um rodapé de
metadados que só o `.xrk` carrega, ou um `.xrz` truncado.

Tabela 1. Comparação byte a byte das duplas `.xrk`/`.xrz` com o mesmo radical
no catálogo local (406 radicais, 407 comparações).

| caso | mesma gravação | gravações separadas |
|---|---|---|
| `.xrz` descomprimido idêntico ao `.xrk` | 1 | 42 |
| `.xrz` descomprimido é prefixo do `.xrk`; o resto é rodapé de metadados | 356 | 2 |
| `.xrz` truncado (zlib incompleto), stream é prefixo do `.xrk` | 6 | 0 |
| conteúdo diferente | 0 | 0 |

O rodapé tem de 0 a 199 bytes e é feito só de blocos `<hXXX` de metadado
(`RCR` piloto, `VEH` veículo, `CMP` campeonato, `VTY` tipo de sessão, `TRK`
pista), sempre terminando em `NTE` (nota). A combinação mais comum é
`VTY-NTE`, em 157 duplas.

As 44 comparações em gravações separadas são cópias em pastas diferentes do
F3 e da AiM, por exemplo `F3/Geral/<radical>.xrk` contra
`F3/<piloto>/<carro>/<data>/<radical>.xrz`. O agrupamento de bundle é por
pasta e radical, então essas cópias viravam duas gravações com as mesmas
voltas, e a derivação de traçado parava em `uq_tracado_sha256`.

Método: para cada dupla listada em `arquivo_bruto`, o `.xrz` foi
descomprimido com `zlib.decompressobj()`, que devolve o stream até onde o
arquivo chega, e comparado com os bytes do `.xrk` por igualdade e por prefixo.

Regra adotada em `pipeline/recepcao.py` (`mesma_captura_aim`): duas cópias
são a mesma captura quando o stream menor é prefixo do maior e vale uma de
duas condições.

1. A diferença de tamanho é de até 1 KiB, o que cobre o rodapé medido de até
   199 bytes. Vale para qualquer tamanho, porque o menor `.xrk` do catálogo
   tem 28 KiB.
2. O stream menor tem pelo menos 64 KiB. É o caso do `.xrz` truncado; o piso
   impede que um truncado quase vazio case com outra captura do mesmo logger.

O nome igual só escolhe o candidato.
