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

## 7. Calibração de zero por sessão de `Acc Long`/`Acc Lat` (issue #36, 2026-09-14)

A seção 3 mediu que `Acc Long`/`Acc Lat` fecham com r = 1,000 contra o `.dat`
em cada arquivo, com o MESMO fator (-0,02586 G por contagem), mas o offset
(zero do sensor) muda de sessão para sessão (12,85 a 13,18 G no longitudinal,
12,44 a 12,50 G no lateral): uma constante única erraria até 1,6 m/s².

**Decisão de arquitetura.** `mapeamento_canal` é por PERFIL: o mesmo
fator/offset vale pra toda gravação do `pi_pid`, não cabe um número que muda
arquivo a arquivo. A migration 025 cria `calibracao_canal_gravado`, uma linha
por (gravação, canal canônico), com o offset em CONTAGEM (não convertido). O
pipeline de ingestão (`pipeline/calibracao.py`) mede o próprio arquivo: a
média da contagem crua no maior trecho contíguo com `Speed` = 0 (mínimo 100
amostras, 2 s a 50 Hz), depois que o leitor já escreveu a série bruta em
Parquet. Sem trecho parado longo o bastante (`P.Piquet000991.pid`, sessão
curta de 18 kB sem carro parado identificável), nenhuma linha é escrita e
`lon_acc`/`lat_acc` ficam fora do inventário daquela gravação; o motivo fica
em `gravacao.metadata` (`pi_pid.calibracao_acc_motivo`). `seeds/aliases.yaml`
ganha `lon_acc`/`lat_acc` no perfil `pi_pid` com o fator fixo (-0,25360
m/s²/contagem = -0,02586 × 9,80665) e offset 0 (identidade): o offset de
verdade entra por `leitura.fator_do_canal`, que soma `-fator × offset_contagem`
ao offset do perfil quando há calibração pra aquela gravação.

**Validação: 21 dos 23 pares `.pid` × `.dat` do acervo F3, 2 canais cada (42
séries).** `P.Piquet000991.pid` fica fora por falta de trecho parado (acima).
Erro absoluto contra o `.dat` da mesma sessão, calibrado × referência, série
inteira:

| | valor |
|---|---|
| erro mínimo | 0,046 m/s² |
| erro mediano | 0,330 m/s² |
| erro médio | 0,349 m/s² |
| **erro máximo (dos 42)** | **0,707 m/s²** |
| séries com erro abaixo de 1 contagem (0,254 m/s²) | 11 de 42 |
| séries com erro abaixo de 0,5 m/s² | 36 de 42 |

**O critério de aceite da issue (erro máximo abaixo de 0,05 m/s²) NÃO foi
atingido.** Investigado em `P.Piquet000974.pid` (sessão 100% parada, 22.200
amostras, o caso mais favorável, sem nenhuma amostra em movimento pra
confundir a janela): a contagem crua de `Acc Long` oscila entre 500 e 503 ao
longo do arquivo inteiro (502 é o valor mais frequente, 72% das amostras), e
o `.dat` mapeia a contagem 501, não a média 501,73 nem a moda 502, pro zero
físico exato. Isso é medido, não suposição: filtrando o `.dat` pelas amostras
com contagem 501, o valor é 0,0 G em todas; com contagem 502, é sempre
-0,025641 G, o próprio passo de quantização. O offset que o Pi Toolbox usou
não é a média de nenhuma janela deste arquivo; nenhuma janela testada (1 s a
22.200 s) recupera exatamente 501.

A causa provável é a resolução do sensor, não o método de calibração: o
fator medido (-0,02586 G/contagem = -0,2536 m/s²/contagem) é o próprio passo
de quantização do conversor. Uma contagem de diferença entre o offset medido
e o offset "verdadeiro" do Pi Toolbox já vale 0,2536 m/s², cinco vezes o
critério de 0,05 m/s². A própria seção 3 mediu isso pelo lado da melhor
hipótese possível: o ajuste linear com fator e offset livres por arquivo
(usando todas as amostras do arquivo, não só um trecho parado) já fecha só
até 0,024 a 0,037 G de resíduo máximo (0,235 a 0,362 m/s²), acima de 0,05
m/s² mesmo no melhor caso teórico. Nenhum offset recuperável deste sensor,
calibrado por sessão ou não, bate abaixo do ruído de quantização dele.

**Resultado prático.** A calibração por sessão troca um erro de até 1,6 m/s²
(offset único fixo, o que a issue #26 mediu) por um erro de até 0,71 m/s²
(mediana 0,33 m/s², calibrado por gravação), quatro vezes menor no pior caso
e abaixo do limiar de frenagem de -3,5 m/s² com folga. O critério numérico de
0,05 m/s² da issue fica abaixo da resolução do próprio sensor e não fecha;
ver `docs/empresa/decisions.md` e o PR #36 para a decisão de seguir assim
mesmo, sem inventar precisão que o hardware não tem.
