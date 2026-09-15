# Medição de cobertura do leitor Racelogic VBOX `.vbo` (2026-09-14)

## Resultado

| item | valor |
|---|---|
| arquivos únicos no acervo (hash) | 6 (todo o acervo catalogado, não é amostra) |
| abriram sem erro (`inspecionar`) | 6/6 |
| canais declarados por arquivo | média 34,7 (mín. 22, máx. 41) |
| canais mapeados em `seeds/aliases.yaml` (perfil `vbox`) | média 11,0 |
| cobertura agregada | 31,7% |
| velocidade de `inspecionar()` | média 93,1 MB/s (mín. 83,5, máx. 109,6) |

O acervo só tem 6 `.vbo` únicos no total (29 linhas no inventário, a maioria
duplicata), então esta medição cobre o universo inteiro, não uma amostra.

## O que foi medido

Os 6 arquivos `.vbo` únicos do acervo, copiados do Drive, passados por
`detectar()` e `LeitorVbo.inspecionar()` (`src/saru_poc/readers/vbo.py`).
Canais comparados contra o perfil `vbox` de `seeds/aliases.yaml`. `ler()`
também rodou em 2 dos 6 arquivos: sem erro, throughput 37-40 MB/s.

## Tabela por arquivo

| arquivo | tamanho MB | canais declarados | canais mapeados |
|---|---|---|---|
| 3 - 992#3 - F. Giaffone - 22ET08 - Q.1 (2022_12_18 20_23_00 UTC).vbo | 4,776 | 41 | 11 |
| 4 - 992#3 - F. Giaffone - 22ET08 - Q.2 (2022_12_18 20_23_00 UTC).vbo | 4,811 | 41 | 11 |
| 5 - 992#3 - F. Giaffone - 22ET08 - R1 (2022_12_18 20_23_00 UTC).vbo | 11,367 | 41 | 11 |
| Ref_40Rookie_23ET1_0001.vbo | 0,282 | 22 | 11 |
| Ref_40_23ET1.vbo | 0,281 | 22 | 11 |
| Ref_992_23ET1.vbo | 0,558 | 41 | 11 |

## O que fica de fora e por quê

Canais nunca mapeados nos 6 arquivos: `Tsample`, `VBOX_accz`,
`VBOX_laptime`, `VBOX_yaw`, `avifileindex`, `avitime`, `heading`, `height`,
`sats`, `time` (presentes nos 6); `rad_B_FCY`, `rad_B_SC`, `rad_B_SC_lap`,
`rad_B_bF` e outros `rad_B_*` (presentes nos 4 arquivos maiores, de 41
canais). `heading`, `height` e `VBOX_accz` são candidatos óbvios de
canônico (direção de deslocamento, altitude e aceleração vertical), hoje sem
alias no perfil `vbox`.

Prioridade baixa: o acervo tem só 6 arquivos únicos deste formato contra
centenas de `.xrk`/`.ld`/`.drk`. A lacuna é real mas afeta pouco volume.
Issue aberta com prioridade média-baixa: ver
`docs/cobertura-de-dados-resumo.md`.
