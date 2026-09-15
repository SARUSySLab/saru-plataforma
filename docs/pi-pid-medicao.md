# Medição do formato Pi `.pid` (logger do F3)

Medição de 2026-09-14 para a issue #26 (leitor `.pid` entregava contagem crua). Vale para o logger Pi dos F3 do acervo (`Trabalho/Telemetria/F3/`, piloto P.Piquet, e um G.Samaia). A Porsche Cup grava `.pds`, outro formato, medido em `docs/pi-pds-medicao.md`. Antes é o leitor em `main` (ccd5486); depois é o leitor deste PR.

## Resultado

| | Antes | Depois |
|---|---|---|
| Arquivos `.pid` do acervo que abrem | 25 de 25 | 25 de 25 |
| `Speed` de `P.Piquet000996.pid`, p0,5 a p99,5 | 0 a 65535 (contagem embaralhada) | 0 a 253,8 kph, igual ao `.dat` |
| Canais que batem com o `.dat` da mesma sessão com r = 1,000 | 0 | 21 de 24 medidos |
| Canais no vocabulário canônico do perfil `pi_pid` | speed, rpm, distance_m (coluna errada), throttle (coluna errada), brake, lap_number | speed, rpm, distance_m, throttle, brake_press, lap_number |

## 1. O que estava errado

O `ler()` de 2026-08-29 decodificava o bloco de 1 s como se cada canal ocupasse `taxa × largura` bytes contíguos, na ordem do dicionário. O layout real, medido pelo leitor original do saru-app em 2026-08-04 e confirmado aqui, é intercalado por tick de 10 ms: o quadro do tick 0 leva todos os canais, o do tick 1 só os de 100 Hz, o do tick 2 os de 100 e 50 Hz, e assim por diante. A soma dos 100 quadros fecha no tamanho do bloco. Com o layout contíguo, `Speed`, `RPM`, `Acc Long` e todos os outros saíam com a mesma distribuição de contagem em cada arquivo (medido nos 25: p99,5 igual em todos os canais do mesmo arquivo), o sintoma que a issue descreve como "0 a 12.462".

Segundo achado: o quadro do tick 1 não traz amostra. Nos 24 arquivos F3 ele vale `00 00 00 00 <u16 variável> 03 e7 0b b8 00 01` (12 B, o tamanho exato do quadro dos seis canais de 100 Hz); no G.Samaia, com um canal de 100 Hz, vale `00 20` (2 B). É um marcador de bloco. Sem tratá-lo, `Steering` contra o `.dat` da mesma sessão dá r = 0,75; com o slot nulo, r = 1,000. O leitor emite nulo nesse slot para os canais de 100 Hz.

## 2. O que mudou

1. `ler()` decodifica o bloco por tick (`_layout_do_bloco`), porte do `_frame_layout` do saru-app.
2. O slot do tick 1 dos canais de 100 Hz sai nulo (`_TICK_MARCADOR`).
3. O leitor converte só o que o cabeçalho declara: `Speed` (escala 10, divisor), `RPM` e `Lap Number` (escala 1), `Steering` e `Damper *` (escala 0,0977517 e -0,0488759, multiplicador). Os demais saem em contagem.
4. O perfil `pi_pid` de `seeds/aliases.yaml` deixa de herdar o `pi_core` (nomes truncados do `.dat`) e ganha fator e offset medidos por canal (seção 3). O carregador do acervo passa a ler `offset` do YAML; a tabela `mapeamento_canal` já tinha a coluna.

## 3. Fator e offset medidos contra o `.dat` da mesma sessão

Método: 23 pares `.pid` e `_*.dat` de mesmo número de sessão (o `.dat` é a exportação do Pi Toolbox, em unidade física, `float32`). Ajuste linear `físico = fator × contagem + offset` por canal e por par, com o tick 1 dos canais de 100 Hz excluído. Um canal entra no perfil quando fator e offset são iguais em todos os pares e o resíduo máximo fica abaixo de 1e-3 na unidade de saída. Os 553 ajustes por par e canal estão em `docs/pi-pid-cruzamento.tsv`; a tabela abaixo resume por canal.

| Canal | Hz | Escala no cabeçalho | Pares | Fator (mín, mediana, máx) | Offset (mín, mediana, máx) | r mínimo | Resíduo máximo | Entra no perfil |
|---|---|---|---|---|---|---|---|---|
| `Speed` | 50 | 10 | 19 | 0.1, 0.1, 0.1 | -1.327e-07, -3.779e-08, 2.051e-06 | 1.00000 | 1.25e-05 | sim, via cabeçalho |
| `RPM` | 50 | 1 | 23 | 1, 1, 1 | -1.108e-12, -1.899e-13, 9.585e-13 | 1.00000 | 4.55e-12 | sim, via cabeçalho |
| `Throttle Position` | 25 | 0 | 23 | 0.1, 0.1, 0.1 | -7.933e-08, 4.433e-09, 4.146e-08 | 1.00000 | 3.2e-06 | sim, 0,001 para 0-1 |
| `QmDistance` | 50 | 0 | 19 | 0.01, 0.01, 0.01 | -6.849e-06, -1.285e-07, 2.997e-06 | 1.00000 | 0.000952 | sim, 0,01 m |
| `Acc Long` | 50 | 0 | 23 | -0.0263158, -0.0258569, -0.025641 | 12.85, 12.96, 13.18 | 0.99996 | 0.024 | não: offset varia por sessão |
| `Acc Lat` | 50 | 0 | 23 | -0.0263158, -0.0262074, -0.0261782 | 12.44, 12.45, 12.5 | 0.99998 | 0.0369 | não: offset varia por sessão |
| `Brake Press F` | 50 | 0 | 21 | 0.199645, 0.199645, 0.199645 | -41.33, -41.33, -41.33 | 1.00000 | 3.93e-06 | sim, 19,9645 kPa e -4132,7 kPa |
| `Brake Press R` | 50 | 0 | 23 | 0.199643, 0.199645, 0.199645 | -41.13, -41.13, -41.13 | 1.00000 | 0.998 | não: fora do vocabulário |
| `Steering` | 100 | 0.0977517 | 23 | 0.0977517, 0.0977517, 0.0977517 | -40.47, -40.47, -40.47 | 1.00000 | 2.09e-06 | não: offset -40,47 mm não declarado; fora do vocabulário |
| `Damper FL` | 100 | -0.0488759 | 23 | -0.0488759, -0.0488759, -0.0488758 | 5.132, 5.132, 5.132 | 1.00000 | 4.81e-07 | não: fora do vocabulário |
| `Damper FR` | 100 | -0.0488759 | 23 | -0.0488759, -0.0488759, -0.0488758 | 3.91, 3.91, 3.91 | 1.00000 | 4.8e-07 | não: fora do vocabulário |
| `Damper RL` | 100 | -0.0488759 | 23 | -0.0488759, -0.0488759, -0.0488758 | 9.531, 9.531, 9.531 | 1.00000 | 6.25e-07 | não: fora do vocabulário |
| `Damper RR` | 100 | -0.0488759 | 22 | -0.0488759, -0.0488759, -0.0488758 | 11.1, 11.1, 11.1 | 1.00000 | 9.05e-07 | não: fora do vocabulário |
| `Lap Number` | 1 | 1 | 15 | 1, 1, 1 | -1.093e-15, 5.096e-17, 7.238e-16 | 1.00000 | 9.77e-15 | sim, via cabeçalho |
| `Running Lap Time` | 1 | 0 | 21 | 0.001, 0.001, 0.001 | -4.746e-06, -4.367e-07, 4.381e-06 | 1.00000 | 4.9e-05 | não: fora do vocabulário (0,001 s) |
| `Beacon Code` | 50 | 1 | 17 | 1, 1, 1 | -1.731e-11, 2.988e-13, 3.268e-10 | 1.00000 | 6.84e-10 | não: fora do vocabulário |
| `Water Temp` | 10 | 0 | 22 | 0.0999996, 0.1, 0.1 | -5.32e-06, 4.479e-07, 0.0002864 | 1.00000 | 4.88e-06 | não: fora do vocabulário |
| `Oil Pressure` | 1 | 0 | 0 de 23 | constante no acervo | | | | não |
| `Battery Voltage` | 20 | 0.1 | 23 | 0.0999996, 0.1, 0.100001 | -0.009245, -6.932e-05, 0.004674 | 1.00000 | 7.75e-05 | não: fora do vocabulário |
| `Lambda` | 20 | 2048 | 23 | 2048, 2048, 2048 | -4.621e-09, -2.262e-10, 1.308e-09 | 1.00000 | 6.52e-09 | não: fora do vocabulário (1/2048) |
| `Fuel Pressure` | 50 | 0 | 0 de 23 | constante no acervo | | | | não |
| `Speed ECU` | 20 | 1 | 0 de 23 | constante no acervo | | | | não |
| `WS_FL` | 50 | 10 | 19 | 0.1, 0.1, 0.1 | -1.562e-07, -3.318e-08, 4.407e-06 | 1.00000 | 1.25e-05 | não: fora do vocabulário |
| `WS_FR` | 50 | 10 | 19 | 0.1, 0.1, 0.1 | -1.082e-07, -4.304e-08, 2.554e-06 | 1.00000 | 1.25e-05 | não: fora do vocabulário |

Leitura da tabela: fator e offset dos canais que entram são idênticos em todos os pares até a sexta casa; `Speed`, `WS_FL` e `WS_FR` têm 19 pares porque em 4 sessões o carro não andou. `Acc Long` e `Acc Lat` fecham com r = 1,000 em cada par, mas o offset muda de sessão para sessão (12,85 a 13,18 G no longitudinal), o que é o zero do sensor ajustado pelo Pi Toolbox por sessão; uma constante única erraria até 0,17 G (1,6 m/s²), acima do que o limiar de frenagem de -3,5 m/s² tolera. Os dois ficam fora do perfil até haver zero por sessão.

## 4. Antes e depois em uma sessão

`P.Piquet000996.pid` (570 s) contra `_P.Piquet000996.dat`, percentis 0,5 e 99,5 do que o leitor entrega. `Throttle`, `QmDistance`, `Acc Long` e `Brake` saem em contagem do leitor e viram unidade física pelo perfil (seção 3).

| Canal | Antes | Depois (leitor) | `.dat` (Pi Toolbox) |
|---|---|---|---|
| `Speed` | 0 a 65535 | 0.00 a 253.80 | 0.00 a 253.80 |
| `RPM` | 0 a 65535 | 0.00 a 6841.51 | 0.00 a 6841.51 |
| `Throttle Position` | -24801 a 23711 | 0.00 a 1000.00 | 0.00 a 100.00 |
| `QmDistance` | 0 a 4294901790 | 0.00 a 2609473.04 | 0.00 a 26094.73 |
| `Acc Long` | -24699 a 24391 | 467.00 a 572.00 | -1.82 a 0.89 |
| `Brake Press F` | -16448 a 16088 | 207.00 a 441.51 | 0.00 a 46.82 |
| `Steering` | -26302 a 26032 | 17.11 a 61.58 | -23.36 a 21.11 |

## 5. O que continua de fora

1. `Acc Long` e `Acc Lat`: zero por sessão (decisão de Vitor na issue #26).
2. `Steering` e `Damper *`: fator do cabeçalho aplicado, mas o `.dat` subtrai um offset por canal (-40,47 mm no `Steering`, 5,13 mm no `Damper FL`) que o `.pid` não declara. Fora do vocabulário canônico hoje.
3. `Gear Pot`: não é linear contra o `Gear` do `.dat` (r = 0,55).
4. `G.Samaia003073.pid`: abre, mas `Speed` fica em 0 na sessão inteira; sem `.dat` par.

## 6. Tabela por arquivo

`Speed` p99,5 do que o leitor entrega, antes e depois. 0,0 depois significa carro parado na gravação.

| Arquivo | kB | Speed p99,5 antes | Speed p99,5 depois (kph) |
|---|---|---|---|
| `G.Samaia003073 (2022_12_18 20_23_00 UTC).pid` | 250 | 65535 | 0.0 |
| `P.Piquet000000.pid` | 1960 | 65535 | 252.2 |
| `P.Piquet000992.pid` | 559 | 12336 | 0.0 |
| `P.Piquet000001.pid` | 1491 | 65535 | 252.5 |
| `P.Piquet000974.pid` | 1360 | 65535 | 0.0 |
| `P.Piquet000975.pid` | 468 | 65535 | 0.0 |
| `P.Piquet000976.pid` | 459 | 51743 | 184.2 |
| `P.Piquet000977.pid` | 1689 | 65535 | 251.9 |
| `P.Piquet000978.pid` | 395 | 53618 | 213.6 |
| `P.Piquet000979.pid` | 1707 | 65535 | 253.5 |
| `P.Piquet000980.pid` | 1473 | 65535 | 252.4 |
| `P.Piquet000981.pid` | 2081 | 65535 | 250.9 |
| `P.Piquet000982.pid` | 1327 | 65535 | 251.7 |
| `P.Piquet000985.pid` | 1092 | 65535 | 238.7 |
| `P.Piquet000986.pid` | 776 | 12455 | 0.0 |
| `P.Piquet000987.pid` | 4011 | 65535 | 249.5 |
| `P.Piquet000988.pid` | 1238 | 65535 | 251.6 |
| `P.Piquet000989.pid` | 33 | 12432 | 0.0 |
| `P.Piquet000990.pid` | 1457 | 65535 | 254.1 |
| `P.Piquet000991.pid` | 18 | 12041 | 74.1 |
| `P.Piquet000993.pid` | 1795 | 65535 | 251.1 |
| `P.Piquet000994.pid` | 1734 | 65535 | 254.0 |
| `P.Piquet000995.pid` | 246 | 18547 | 65.9 |
| `P.Piquet000996.pid` | 1744 | 65535 | 253.8 |
| `P.Piquet000997.pid` | 1479 | 65535 | 252.5 |

## 7. Desempenho

Medição de 2026-09-14, adiantando a issue #45 para os leitores Pi. O `ler()` do `.pid` ficou 39% mais rápido na mediana dos 25 arquivos do acervo, com a mesma saída célula a célula e o mesmo pico de memória. A mudança veio da análise do commit `66d9935` do Antigravity (branch `arquivo/antigravity-cosworth-66d9935`); a ideia que ele de fato propunha para memória, ler em pedaços de 64 KB, foi medida e deixou o leitor mais lento e mais pesado.

### 7.1 O que mudou

O `ler()` montava a contagem de cada canal com um laço por janela do layout por tick e, dentro dele, um laço por byte. Um canal de 100 Hz com 2 B por amostra fazia 100 janelas e 200 operações por bloco de arquivo. O perfil de CPU do `P.Piquet000987.pid` mostrava 31 ms de 119 ms só em conversão de tipo dentro desse laço.

Agora `_contagem_do_canal` junta de uma vez todos os bytes do canal em todos os blocos (`np.take` com a lista de posições do layout) e lê cada amostra como inteiro big-endian sem sinal. O resto do `ler()` não mudou: sinal, escala, slot nulo do tick 1, checagem de cursor e mensagens de erro com offset.

### 7.2 Método

1. Arquivos: os 25 `.pid` únicos do acervo, copiados do Drive para disco local.
2. Variantes: o leitor publicado no PR #35 (`1823e72`), o `CosworthPidReader` de `66d9935`, o leitor vetorizado e uma variante que lê o corpo em pedaços de 64 KB com a mesma decodificação vetorizada.
3. Tempo: mediana de 7 execuções de `inspecionar()` e de `ler()` consumindo todos os lotes, cada variante em processo Python novo.
4. Memória: pico do `tracemalloc` numa segunda chamada de `ler()` no mesmo processo. A primeira chamada paga cerca de 25 MB de import tardio que ficam retidos e não são custo do leitor. RSS máximo por `/usr/bin/time -v` numa passada de `inspecionar()` e `ler()`; o processo só com imports tem 59 MB.
5. Igualdade: cabeçalho igual e, em cada lote, mesma frequência, mesmos nomes na mesma ordem, mesmo tipo, mesma contagem de nulos e mesmos valores, com NaN igual a NaN. Máquina: Dell G15, 16 núcleos, Python 3.12.3, NumPy 2.5.2, PyArrow 25.0.1.

### 7.3 Resultado por arquivo

Tabela 7. Tempo de `ler()` em ms, pico de memória de `ler()` em MB (tracemalloc, segunda chamada) e RSS máximo do processo em MB, do maior para o menor arquivo. "Igual" compara as três outras variantes contra a publicada. `inspecionar()` ficou em até 1,0 ms em todos os arquivos e variantes.

| Arquivo | kB | ler ms publicado | ler ms Antigravity | ler ms vetorizado | ler ms 64 KB | pico MB publicado | pico MB vetorizado | pico MB 64 KB | RSS MB publicado | RSS MB vetorizado | Igual |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `P.Piquet000987.pid` | 4011 | 91,5 | 89,4 | 58,5 | 155,2 | 20,9 | 20,9 | 29,3 | 129,3 | 129,1 | sim |
| `P.Piquet000981.pid` | 2081 | 54,0 | 52,8 | 32,5 | 83,4 | 10,8 | 10,8 | 15,3 | 119,9 | 120,0 | sim |
| `P.Piquet000000.pid` | 1960 | 50,2 | 50,1 | 32,6 | 78,6 | 10,2 | 10,2 | 14,4 | 119,6 | 119,6 | sim |
| `P.Piquet000993.pid` | 1795 | 47,6 | 49,9 | 36,5 | 79,8 | 9,3 | 9,3 | 13,2 | 118,8 | 118,8 | sim |
| `P.Piquet000996.pid` | 1744 | 52,1 | 48,0 | 30,0 | 77,9 | 9,1 | 9,1 | 12,8 | 118,5 | 118,3 | sim |
| `P.Piquet000994.pid` | 1734 | 48,0 | 54,0 | 28,4 | 70,8 | 9,0 | 9,0 | 12,7 | 118,7 | 118,4 | sim |
| `P.Piquet000979.pid` | 1707 | 45,0 | 46,1 | 29,9 | 70,1 | 8,9 | 8,9 | 12,5 | 118,5 | 117,9 | sim |
| `P.Piquet000977.pid` | 1689 | 45,9 | 45,9 | 28,3 | 69,5 | 8,8 | 8,8 | 12,4 | 118,5 | 118,4 | sim |
| `P.Piquet000001.pid` | 1491 | 39,9 | 41,7 | 25,0 | 62,7 | 7,8 | 7,7 | 11,0 | 117,3 | 117,4 | sim |
| `P.Piquet000997.pid` | 1479 | 41,5 | 42,6 | 25,7 | 60,3 | 7,7 | 7,7 | 10,9 | 117,8 | 117,8 | sim |
| `P.Piquet000980.pid` | 1473 | 40,9 | 42,4 | 25,4 | 60,4 | 7,7 | 7,7 | 10,8 | 117,4 | 117,0 | sim |
| `P.Piquet000990.pid` | 1457 | 40,5 | 40,0 | 24,6 | 60,0 | 7,6 | 7,6 | 10,7 | 117,3 | 117,7 | sim |
| `P.Piquet000974.pid` | 1360 | 39,8 | 40,6 | 24,7 | 59,3 | 7,1 | 7,1 | 10,0 | 117,0 | 117,1 | sim |
| `P.Piquet000982.pid` | 1327 | 38,5 | 38,2 | 23,2 | 54,2 | 6,9 | 6,9 | 9,8 | 116,9 | 116,9 | sim |
| `P.Piquet000988.pid` | 1238 | 40,8 | 38,5 | 23,3 | 51,7 | 6,5 | 6,4 | 9,1 | 116,7 | 116,2 | sim |
| `P.Piquet000985.pid` | 1092 | 34,1 | 36,2 | 20,7 | 46,3 | 5,7 | 5,7 | 8,0 | 116,0 | 115,6 | sim |
| `P.Piquet000986.pid` | 776 | 30,3 | 32,3 | 18,5 | 37,9 | 4,2 | 4,2 | 5,7 | 113,9 | 114,1 | sim |
| `P.Piquet000992.pid` | 559 | 25,8 | 28,9 | 14,8 | 27,2 | 3,1 | 3,1 | 4,2 | 113,0 | 113,2 | sim |
| `P.Piquet000975.pid` | 468 | 23,9 | 25,1 | 13,0 | 23,2 | 2,6 | 2,6 | 3,5 | 112,9 | 112,3 | sim |
| `P.Piquet000976.pid` | 459 | 23,5 | 25,8 | 13,2 | 22,6 | 2,5 | 2,5 | 3,4 | 112,4 | 112,6 | sim |
| `P.Piquet000978.pid` | 395 | 21,8 | 22,1 | 12,0 | 20,8 | 2,2 | 2,2 | 3,0 | 112,1 | 112,1 | sim |
| `G.Samaia003073 (2022_12_18 20_23_00 UTC).pid` | 250 | 15,3 | 15,4 | 9,7 | 12,7 | 1,5 | 1,5 | 1,8 | 112,0 | 111,7 | sim |
| `P.Piquet000995.pid` | 246 | 25,0 | 19,4 | 10,4 | 15,0 | 1,4 | 1,4 | 1,9 | 112,0 | 111,8 | sim |
| `P.Piquet000989.pid` | 33 | 15,7 | 16,0 | 7,6 | 7,6 | 0,2 | 0,2 | 0,3 | 111,4 | 110,6 | sim |
| `P.Piquet000991.pid` | 18 | 15,2 | 15,2 | 7,4 | 7,1 | 0,1 | 0,1 | 0,2 | 109,1 | 109,2 | sim |

Soma de `ler()` nos 25 arquivos: 0,947 s publicado, 0,576 s vetorizado, 1,314 s em pedaços de 64 KB. Razão vetorizado sobre publicado: mediana 0,61, de 0,42 a 0,77. As 16.760.808 células conferidas são iguais nas três variantes.

### 7.4 O que foi e o que não foi portado do commit `66d9935`

| Ideia do commit | Portada | Motivo medido |
|---|---|---|
| Decodificação do `.pid` por tick | não havia o que portar | o `ler()` dele é cópia do publicado: mesma saída nos 25 arquivos e mesmo tempo (89 ms contra 92 ms no `P.Piquet000987.pid`), sem a checagem de cursor e sem os offsets nas mensagens de erro |
| Laço por janela e por byte trocado por leitura vetorizada | sim | é a leitura que o layout pré-calculado permite; 0,61 do tempo, memória igual |
| Corpo lido em pedaços de 64 KB | não | 2,7 vezes o tempo da leitura vetorizada inteira e pico 40% maior (29,3 MB contra 20,9 MB no `P.Piquet000987.pid`), porque a contagem de todos os canais fica alocada ao mesmo tempo; o corpo inteiro do maior `.pid` tem 4 MB |
| `TransformacaoLinear` e `calibracoes` | não | sem chamador; o fator medido vive no perfil `pi_pid` de `seeds/aliases.yaml` (seção 3), e o teste dele usa 0,125 sem fonte onde o medido é 0,1 |
| Pacote `src/telemetria/` ao lado de `src/saru_poc/readers/` | não | segunda pilha de leitores fora do registro, sem ADR e com importação circular |
| Leitura de amostra do `.pds` | não | tamanho de amostra escolhido por palpite quando a distância entre blocos não fecha; no `REF 992.pds` o `ler()` quebra com `ValueError: Arrays were not all the same length: 577 vs 581` depois de 3,9 s, com pico de 31,6 MB no tracemalloc; detalhe e caminho de medição na issue do `.pds` |
| `inspecionar()` do `.pds` sem o filtro `_nome_valido` | não | recusa o `P.Piquet000997.pds`, que o leitor do PR #34 abre com 45 canais: ruído da amostra forma candidatos de 274 registros que passam na frente do dicionário real de 47. Medido nos 27 `.pds` que o PR #34 abre: recusa 16. Nos 11 que abre, o cabeçalho é igual e o pico de memória é maior (12,2 MB contra 8,4 MB no `REF 992.pds`; 10,6 contra 3,9 MB no `P.Piquet000987.pds`) |

### 7.5 O que continua de fora

1. O restante do tempo do `ler()` vetorizado está no `np.percentile` de `_aplicar_escala` (24 ms de 66 ms no perfil do `P.Piquet000987.pid`), que calcula percentis da série dividida e da multiplicada. Não mudou aqui porque qualquer diferença de arredondamento pode trocar a direção da escala escolhida.
2. A meta de tempo e memória por MB e a medição dos outros formatos continuam na issue #45.
