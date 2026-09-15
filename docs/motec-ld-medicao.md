# Medição de cobertura dos leitores MoTeC `.ld` e `.ldx` (2026-09-14)

## Resultado

| item | `.ld` | `.ldx` |
|---|---|---|
| arquivos únicos no acervo (hash) | 116 | 34 |
| amostra medida | 10 | 10 |
| abriram sem erro (`inspecionar`) | 10/10 | 10/10 |
| canais declarados por arquivo | média 18,9 (5 arquivos com 0: exportações de simulador quase vazias, ver abaixo) | 0 sempre (sidecar de voltas, sem canal, por desenho) |
| canais mapeados em `aliases.yaml` (perfil `motec_ld`) | média 1,2 | não se aplica |
| cobertura agregada (só arquivos com canal) | 6,3% | não se aplica |
| velocidade de `inspecionar()` | ver tabela; arquivos grandes < 1 ms, não é medida útil de throughput | idem |

`.ldx` não carrega canal de telemetria (é sidecar com total de voltas e
melhor tempo, conforme `formatos.py`); os 0 canais são o comportamento
correto do leitor, não uma falha.

## O que foi medido

Amostra de 10 `.ld` e 10 `.ldx` únicos (por hash), sorteados do inventário
do acervo e copiados do Drive. Cada arquivo passou por `detectar()` e por
`LeitorLd.inspecionar()` / `LeitorLdx.inspecionar()`
(`src/saru_poc/readers/ld.py`, `ldx.py`). Canais comparados contra o perfil
`motec_ld` de `seeds/aliases.yaml` (não há perfil `motec_ldx` porque não há
canal a mapear).

Também rodei `ler()` em 2 dos 10 `.ld` (fora do escopo de tempo da medição
de cobertura, mas achado relevante, ver abaixo).

## Tabela por arquivo, `.ld`

| arquivo | tamanho MB | canais declarados | canais mapeados |
|---|---|---|---|
| nurburgring-porsche_991ii_gt3_r-0-2023.03.05-14.52.09.ld | 8,702 | 49 | 0 |
| 20200930-0364202_2.ld | 3,046 | 43 | 7 |
| M1.ld | 1,353 | 42 | 5 |
| nurburgring-porsche_991ii_gt3_r-0-2024.07.28-00.54.44.ld | 0,106 | 55 | 0 |
| 2024-01-20_Barcelona_ACC_MCLAREN720SGT3EVO_Run20.ld | 0,001 | 0 | 0 |
| 2024-05-04_Imola_ACC_MCLAREN720SGT3EVO_Run0.ld | 0,001 | 0 | 0 |
| 2024-05-10_Monza_ACC_FERRARI296GT3_Run1.ld | 0,001 | 0 | 0 |
| 2024-08-23_Nurburgring_24h_ACC_FERRARI296GT3_Run1.ld | 0,001 | 0 | 0 |
| 2024-08-23_Zandvoort_ACC_MCLAREN720SGT3EVO_Run1.ld | 0,001 | 0 | 0 |
| 2024-08-17_Zolder_ACC_JAGUARG3_Run0.ld | 0,001 | 0 | 0 |

5 dos 10 arquivos são exportações do simulador Assetto Corsa Competizione com
1.001 bytes: arquivo aberto sem erro, mas praticamente vazio (0 canal). Não é
falha do leitor: são stubs genuínos do exportador do simulador. Fica fora do
denominador de cobertura por não terem canal a mapear.

## O que fica de fora e por quê

Nos 4 arquivos reais com canal (49, 43, 42 e 55 canais declarados), os canais
nunca mapeados em nenhum dos 4 incluem toda a família de suspensão e freio:

`ABS`, `BRAKE`, `BRAKE_TEMP_LF/LR/RF/RR`, `BUMPSTOPDN_RIDE_LF/LR/RF/RR`,
`BUMPSTOPUP_RIDE_LF/LR/RF/RR`, `BUMPSTOP_FORCE_LF/LR/RF/RR` (lista truncada
na medição, ver `resultados.json` do run para a lista completa por arquivo).

O perfil `motec_ld` de `seeds/aliases.yaml` (linha 892) mapeia só os canais
básicos de piloto (`speed`, `rpm`, `throttle`, `brake` via pressão,
`lon_acc`/`lat_acc`, `steering`), a mesma amplitude que o alias `aim_xrk`
cobre. Ele não tem alias nenhum para temperatura de freio, curso de damper ou
força de bump-stop, que são exatamente os canais que os `.ld` reais do
acervo trazem em quantidade (12 dos ~43-49 canais de cada arquivo são dessa
família).

**Achado adicional em `ler()`**: `20200930-0364202_2.ld` (43 canais, o
segundo maior da amostra) levanta `ErroDeLeitura` ao chamar `ler()`:

```
ErroDeLeitura: .../20200930-0364202_2.ld: canal 'GPS Heading' com combinacao
de tipo (dtype_a=8, dtype=8) nao suportada (mapa cobre so o medido no acervo)
```

`inspecionar()` funciona normalmente nesse arquivo (declara o canal
`GPS Heading` sem erro); é `ler()` que não decodifica a combinação de tipo.
Arquivo real do acervo, erro reproduzível, não amostra sintética.

Issues abertas para as duas lacunas (mapa de canal e falha de `ler()`): ver
`docs/cobertura-de-dados-resumo.md`.
