# Medição do formato Pi Toolbox `.pds`

Medição de 2026-09-14 para a issue #25 (`REF 992.pds` do 992.1 não abria). Complementa a medição de 2026-08-29 registrada na docstring de `src/saru_poc/readers/pi_pds.py`. Arquivos lidos do Drive (`Trabalho/` e `Estudo/`), 71 `.pds` únicos por tamanho e nome, 1.980,7 MB. Antes é o leitor em `main` (ccd5486); depois é o leitor deste PR.

## Resultado

| | Antes | Depois |
|---|---|---|
| Arquivos que abrem | 26 de 71 | 27 de 71 |
| `REF 992.pds` (992.1, 105,8 MB) | recusa | abre: 2484 canais, 581 s |
| Canais por arquivo F3 | 43 ou 44 | 44 ou 45 (um canal a mais, ver seção 4) |
| Canais com dados diferentes nos 26 comuns | | 0 |

## 1. O que estava errado no leitor

O leitor de 2026-08-29 foi medido em arquivos F3 com 46 ou 47 canais, um bloco de amostra por canal, amostra `float64` e tabela em ordem de índice. Nesses arquivos os campos 56 e 60 do registro da tabela valem `índice + 1`, e o leitor usava isso como checagem. O `REF 992.pds` quebra as premissas:

| Premissa de 2026-08-29 | Medido no `REF 992.pds` |
|---|---|
| um bloco por canal | 4311 blocos para 2937 canais do dicionário; 2023 canais com 1 bloco, 172 com 4, 139 com 8, um com 71 |
| tabela em ordem de índice, offsets crescentes | fora de ordem; offsets não monotônicos |
| campo 56 = índice + 1 | permutação de 0 a 4310, número de série do registro |
| campo 60 = índice + 1 | vale em 2393 de 4311 registros; nos outros, valor não interpretado |
| 8 bytes por amostra | 4 bytes em 1328 canais, 1 byte em 918, 2 bytes em 236 |

O primeiro registro da tabela tem campo 56 igual a 2122, a checagem falhava, a tabela voltava vazia e o leitor tentava os outros 1213 candidatos de ruído até desistir na linha 354.

## 2. O que mudou

1. Registro válido da tabela: intervalo e número de amostras positivos, índice dentro do dicionário, bloco terminando antes do dicionário. Os campos 56 e 60 não são mais usados. O primeiro registro inválido encerra a tabela (medido: no `REF 992.pds` o registro 4312 e no F3 o registro 48 têm intervalo zero).
2. Invariante de offset: blocos ordenados por offset; a distância até o próximo bloco dividida pelo número de amostras tem que dar 1, 2, 4 ou 8. Sobreposição derruba o arquivo. Buraco é tolerado até 10% dos pares.
3. Canal com vários blocos soma as amostras e exige o mesmo intervalo em todos (vale nos 2485 canais do `REF 992.pds`).
4. Candidatos a dicionário de mesmo tamanho são tentados do menor offset para o maior: um nome UTF-16 sem o primeiro caractere ainda repete em +88, então cada dicionário real gera cópias deslocadas em +2 e +4 B.

Nenhum campo isolado do dicionário ou da tabela determina o tamanho da amostra: varridos todos os offsets do registro de 552 B em 1, 2 e 4 bytes contra o tamanho medido por canal, nenhum separa 1, 2 e 4. Por isso o tamanho é deduzido da própria tabela, e o leitor continua sem ler amostra.

## 3. Invariante medida

| Arquivo | Pares consecutivos | Fecham exato | Buracos | Sobreposição |
|---|---|---|---|---|
| `REF 992.pds` | 4310 | 4308 (99,95%) | 2 | 0 |
| `P.Piquet000001-1.pds` (F3) | 46 | 46 (100%) | 0 | 0 |
| candidatos de ruído nos 44 arquivos recusados | | 0 blocos válidos em todos, exceto um candidato de 844 blocos no `REF 3.8 - 22ET3.pds`, rejeitado por sobreposição | | |

O teto de 90% fica entre o pior arquivo que abre (99,95%) e o melhor ruído (0%).

## 4. Canal a mais nos arquivos F3

O último registro da tabela dos F3 tem campos 56 e 60 diferentes de `índice + 1` (medido em `P.Piquet000001-1.pds`: 5 e 0). O leitor antigo parava antes dele. O bloco fecha exato: offset 5682368 + 487 × 8 = 5686264, e termina antes do dicionário. É o canal `Fuel Pressure` (`Fuel PressurePi` em um arquivo), 1 Hz, mesma duração do arquivo. Entra no inventário. A conferir por Vitor no Pi Toolbox: se o canal aparece com dado nesses arquivos.

## 5. O que continua de fora e por quê

| Lote | Arquivos | Motivo medido |
|---|---|---|
| `Estudo/Cursos/Bootcamp_FullTime` | 10 | dicionário com registro de 304 B, sem nome duplicado em +88; leitor só conhece o de 552 B |
| `Porsche_Cup/2025/Shakedown_2025-11` | 10 | 3 sem nenhum candidato na janela de 4 MB; 7 com candidatos de 8 a 40 canais e zero bloco de tabela: o dicionário real não está nos últimos 4 MB ou tem outro layout |
| `Porsche_Cup/2026/26ET07/telemetria/antigo` | 17 | 4 sem candidato; 13 com candidatos de 10 a 52 canais e zero bloco |
| `Porsche_Cup/2026/analise/Data Analysis` (CLASS, FREE PRACTICE, RACE) | 3 | candidatos de 24 a 43 canais, zero bloco; RACE tem 331 MB |
| `REF 25ET6 992.pds`, `REF38 - 26ET02.pds`, `REF 3.8 - 22ET3.pds`, `REF 991.2.pds` | 4 | idem; o `REF 3.8` tem um candidato com 844 blocos sobrepostos |

Esses 44 arquivos são a próxima medição: localizar o dicionário fora da janela ou decifrar o registro de 304 B. Fora do escopo da issue #25.

## 6. Tabela por arquivo

Colunas: tamanho em MB, resultado antes e depois, canais do dicionário, blocos da tabela, buracos, duração em segundos, tempo de leitura em segundos.


### `Estudo/Cursos/Bootcamp_FullTime/Analise de dados`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `FT1_School_Piloto_A.pds` | 7.6 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `FT1_School_Piloto_B.pds` | 6.8 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `FT1_School_Piloto_C.pds` | 6.4 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `FT1_School_Piloto_D.pds` | 6.4 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `PilotoA.pds` | 9.0 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `PilotoB.pds` | 8.6 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `PilotoC.pds` | 8.7 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `PilotoD.pds` | 9.3 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `PilotoE.pds` | 8.1 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `PilotoF.pds` | 6.6 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |

### `Outras_Categorias/Estudo_outras_series/Formula 3/C.Grande/G.Samaia`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `G.Samaia003073 (2022_12_18 20_23_00 UTC).pds` | 1.0 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 123 | 0.9 |

### `Porsche_Cup/2025/Shakedown_2025-11`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `992#096 - Shakedown - 21.11 - 06h47m00s - Arthur Leist.pds` | 86.2 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 8c/0b 8c/0b 8c/0b 8c/0b 8c/0b |
| `992#245 - Shakedown - 22.11 - 07h35m29s - Enzo Pedani.pds` | 118.1 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 13c/0b 13c/0b 13c/0b 13c/0b 13c/0b |
| `992#247 - Shakedown - 22.11 - 07h47m51s - Arthur Leist.pds` | 97.8 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 11c/0b 11c/0b 11c/0b 11c/0b 11c/0b |
| `992#255 - Shakedown - 21.11 - 06h50m36s - Beto gresser.pds` | 29.7 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 40c/0b 40c/0b 40c/0b 40c/0b 40c/0b |
| `992#259 - Shakedown - 22.11 - 07h55m02s - Andre Gaidzinski.pds` | 92.1 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `992#259 - Shakedown - 22.11 - 08h11m18s - André Gaidzinski.pds` | 101.0 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `992#263 - Shakedown - 22.11 - 07h34m13s - Dennis Dirani.pds` | 78.7 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 26c/0b 26c/0b 26c/0b 26c/0b 26c/0b |
| `992#284 - Shakedown - 22.11 - 07h50m17s - Enzo Bedani.pds` | 101.9 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 20c/0b 20c/0b 20c/0b 20c/0b 20c/0b |
| `992#285 - Shakedown - 22.11 - 07h36m10s - Arthur Leist.pds` | 95.6 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 10c/0b 10c/0b 10c/0b 10c/0b 10c/0b |
| `992#406 - Shakedown - 22.11 - 07h56m16s - Dennis Dirani.pds` | 81.4 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |

### `Porsche_Cup/2026/26ET07/telemetria/antigo/Engine Test`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `38#285 - TE1.1 - 01.01 - 00h00m15s - Joao Gonçalves.pds` | 2.1 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `38#285 - TE1.1 - 01.01 - 00h00m25s - Joao Gonçalves.pds` | 2.3 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `38#285 - TE1.1 - 01.01 - 00h00m46s - Joao Gonçalves.pds` | 3.0 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `38#285 - TE1.1 - 01.01 - 00h01m01s - Joao Gonçalves.pds` | 2.0 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |
| `IPS32 #3366 - TE1.1 - 04.04 - 16h30m10s - Unknown.pds` | 5.9 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 19c/0b 19c/0b 19c/0b 19c/0b 19c/0b |
| `IPS32 #3366 - TE1.1 - 04.04 - 17h30m14s - Unknown.pds` | 12.1 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 45c/0b 45c/0b 45c/0b 45c/0b 45c/0b |
| `IPS32 #3366 - TE1.1 - 04.04 - 18h30m27s - Unknown.pds` | 9.1 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 32c/0b 32c/0b 32c/0b 32c/0b 32c/0b |
| `IPS32 #3366 - TE1.1 - 05.04 - 02h29m17s - Unknown.pds` | 13.6 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 52c/0b 52c/0b 52c/0b 52c/0b 52c/0b |
| `IPS32 #3366 - TE1.1 - 25.08 - 10h11m15s - Unknown.pds` | 3.6 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 40c/0b 40c/0b 40c/0b 39c/0b 39c/0b |
| `IPS32 #3366 - TE1.1 - 26.08 - 02h20m43s - Unknown.pds` | 10.5 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 38c/0b 38c/0b 38c/0b 38c/0b 38c/0b |
| `IPS32 #3366 - TE1.1 - 26.08 - 03h12m25s - Unknown.pds` | 9.7 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 35c/0b 35c/0b 35c/0b 35c/0b 35c/0b |
| `IPS32 #3366 - TE1.1 - 26.08 - 03h33m55s - Unknown.pds` | 3.0 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 33c/0b 31c/0b 31c/0b 29c/0b 29c/0b |

### `Porsche_Cup/2026/26ET07/telemetria/antigo/Outing`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `38#285 - TE1.1 - 23.07 - 15h48m16s - Joao Golçalves.pds` | 9.0 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 22c/0b 22c/0b 22c/0b 22c/0b 22c/0b |
| `IPS32 #3366 - TE1.1 - 25.08 - 10h00m36s - Unknown.pds` | 5.6 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 17c/0b 17c/0b 17c/0b 17c/0b 17c/0b |
| `IPS32 #3366 - TE1.1 - 25.08 - 10h18m44s - Unknown.pds` | 6.2 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 20c/0b 20c/0b 20c/0b 20c/0b 20c/0b |
| `IPS32 #3366 - TE1.1 - 25.08 - 10h24m08s - Unknown.pds` | 2.9 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 10c/0b 10c/0b 10c/0b 10c/0b 10c/0b |
| `IPS32 #3366 - TE1.1 - 25.08 - 10h25m26s - Unknown.pds` | 9.4 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 34c/0b 34c/0b 34c/0b 34c/0b 34c/0b |

### `Porsche_Cup/2026/analise/Data Analysis/EXERCÍCIO ENGENHARIA EFICAZ`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `CLASS.pds` | 88.1 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 24c/0b 24c/0b 24c/0b 24c/0b 24c/0b |
| `FREE PRACTICE.pds` | 116.3 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 27c/0b 27c/0b 27c/0b 27c/0b 27c/0b |
| `RACE.pds` | 331.1 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 43c/0b 43c/0b 43c/0b 43c/0b 43c/0b |

### `Porsche_Cup/2026/analise/Telemetria_Real/Formula_3/Geral`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `P.Piquet000000.pds` | 7.5 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 641 | 3.9 |

### `Porsche_Cup/2026/telemetria/Geral`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `P.Piquet000992.pds` | 2.2 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 181 | 1.6 |
| `REF 25ET6 992.pds` | 102.4 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 28c/0b 27c/0b 27c/0b 27c/0b 27c/0b |
| `REF 992.pds` | 105.8 | recusa | abre (2484 canais) | 2937 | 4311 | 2 | 581 | 10.4 |

### `Porsche_Cup/Docs/Dados_SSD_Windows`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `REF38 - 26ET02.pds` | 8.2 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 12c/0b 10c/0b 10c/0b |

### `Porsche_Cup/Docs/Referencias/3.8 - 991.1`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `REF 3.8 - 22ET3.pds` | 9.2 | recusa | recusa: candidatos sem tabela válida |  |  |  |  | ruido: 328c/844b/sobrep 328c/0b 328c/0b 206c/0b 148c/0b |

### `Porsche_Cup/Docs/Referencias/4.0 - 991.2`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `REF 991.2.pds` | 25.3 | recusa | recusa: nenhum dicionário de 552 B na janela |  |  |  |  | ruido:  |

### `Telemetria/F3/Geral`

| Arquivo | MB | Antes | Depois | Dic. | Blocos | Buracos | s | Leitura s |
|---|---|---|---|---|---|---|---|---|
| `P.Piquet000001-1.pds` | 5.7 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 487 | 4.1 |
| `P.Piquet000001.pds` | 6.1 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 524 | 4.4 |
| `P.Piquet000974.pds` | 5.2 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 444 | 4.8 |
| `P.Piquet000975.pds` | 1.8 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 151 | 1.8 |
| `P.Piquet000976.pds` | 1.8 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 148 | 1.9 |
| `P.Piquet000977.pds` | 6.4 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 552 | 3.6 |
| `P.Piquet000978.pds` | 1.5 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 127 | 1.4 |
| `P.Piquet000979.pds` | 6.5 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 558 | 4.1 |
| `P.Piquet000980.pds` | 5.6 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 481 | 4.8 |
| `P.Piquet000981.pds` | 7.9 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 681 | 3.8 |
| `P.Piquet000982.pds` | 5.1 | abre (43) | abre (44 canais) | 46 | 46 | 0 | 433 | 4.3 |
| `P.Piquet000985.pds` | 4.2 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 356 | 3.8 |
| `P.Piquet000986.pds` | 3.0 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 252 | 1.7 |
| `P.Piquet000987.pds` | 15.3 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 1315 | 5.2 |
| `P.Piquet000988.pds` | 4.8 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 404 | 5.1 |
| `P.Piquet000989.pds` | 0.2 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 8 | 0.1 |
| `P.Piquet000990.pds` | 5.6 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 476 | 2.8 |
| `P.Piquet000991.pds` | 0.1 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 3 | 0.1 |
| `P.Piquet000993.pds` | 6.9 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 587 | 5.9 |
| `P.Piquet000994.pds` | 6.6 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 567 | 3.5 |
| `P.Piquet000995.pds` | 1.0 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 78 | 1.2 |
| `P.Piquet000996.pds` | 6.7 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 570 | 4.9 |
| `P.Piquet000997.pds` | 5.7 | abre (44) | abre (45 canais) | 47 | 47 | 0 | 483 | 8.0 |
