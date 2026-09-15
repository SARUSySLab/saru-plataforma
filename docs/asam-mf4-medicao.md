# Medição de cobertura do leitor ASAM MDF4 `.mf4` (2026-09-14)

## Resultado

| item | valor |
|---|---|
| arquivos únicos no acervo (hash) | 54 |
| amostra medida | 10 arquivos únicos sorteados (1 falhou na cópia do Drive, 9 chegaram) |
| abriram sem erro (`inspecionar`) | 4/9 (44%) |
| falharam com `##DL ... dl_count=2` | 5/9 (56%) |
| canais declarados (arquivos que abriram) | 1185 a 1236 por arquivo |
| canais mapeados em `aliases.yaml` | 0 (não existe perfil `asam_mf4` nem `mf4` em `seeds/aliases.yaml`) |
| velocidade de `inspecionar()` (arquivos que abriram) | 1230 a 2104 MB/s |

A velocidade alta não é throughput de leitura de amostra: `inspecionar()`
só decodifica o cabeçalho de canais (`##CN`/`##CG`/`##DG`), não os blocos de
dado, por isso o tempo de parede fica na casa de 0,03 s mesmo em arquivos de
66 MB. Não há medição de `ler()` para `.mf4` nesta auditoria porque nenhum
arquivo da amostra com dados grandes conseguiu passar de `inspecionar()`.

## O que foi medido

Amostra de 10 arquivos `.mf4` únicos, sorteados do inventário do acervo.
9 dos 10 foram copiados com sucesso do Drive (1 falhou no `rclone copy`,
provavelmente por caractere no caminho; não investigado, fora do escopo).
Cada arquivo passou por `detectar()` e `LeitorAsamMf4.inspecionar()`
(`src/saru_poc/readers/asam_mf4.py`).

## Tabela por arquivo

| arquivo | tamanho MB | tempo (s) | resultado |
|---|---|---|---|
| SportCar_bra.mf4 | 3,362 | 0,006 | erro: `##DL` com `dl_count=2` |
| SportCar_bra_2.mf4 | 3,694 | 0,006 | erro: `##DL` com `dl_count=2` |
| RaceCar_vdd.mf4 | 63,402 | 0,030 | ok, 1185 canais |
| SportCar_FullElectric_vdd_copy_copy.mf4 | 66,131 | 0,035 | ok, 1236 canais |
| SportCar_FullElectric_vdd_vdf.mf4 | 66,131 | 0,031 | ok, 1236 canais |
| RaceCar_bit.mf4 | 9,906 | 0,008 | ok, 1185 canais |
| FFHOOK.mf4 | 6,569 | 0,006 | erro: `##DL` com `dl_count=2` |
| SUV_fshk.mf4 | 5,694 | 0,006 | erro: `##DL` com `dl_count=2` |
| SedanCar_fshk_copy.mf4 | 6,332 | 0,006 | erro: `##DL` com `dl_count=2` |

## O que fica de fora e por quê

`_localizar_bloco_de_dado()` em `asam_mf4.py` (linha ~300) só decodifica
`##DL` com `dl_count == 1`; qualquer outro valor levanta `ErroDeLeitura` com
a mensagem "nao ocorre no acervo medido". Essa premissa, medida em 29/08
contra uma amostra menor, não se sustenta: 5 dos 9 arquivos únicos desta
nova amostra de 10 (56%) têm `dl_count=2`. Todos os 5 são simulações do PIBIC
(`SportCar_bra*`, `FFHOOK`, `SUV_fshk`, `SedanCar_fshk_copy`), o mesmo tipo
de arquivo que os 4 que abriram. Não é um perfil de exportador diferente:
é o mesmo gerador produzindo às vezes 1 e às vezes 2 blocos `##DL` filhos.

Também não existe perfil `asam_mf4` (nem `mf4`) em `seeds/aliases.yaml`:
nenhum dos ~1200 canais que cada arquivo declara tem alias canônico. Os
nomes de canal seguem convenção hierárquica com ponto
(`Brake.ABS_Activity.L1`, `Animator_Widget.engine_rpm`), compatível com o
padrão de `col` como lista que os outros perfis já usam.

Issues abertas para as duas lacunas (`dl_count` e ausência de perfil): ver
`docs/cobertura-de-dados-resumo.md`.
