# Medição do limiar de início de frenagem por desaceleração longitudinal

Data da medição: 2026-09-13. Regra E-RN-02, caso de uso E-UC-02.
Alvo: o padrão `limiar_ms2 = -3.5`, `distancia_min_m = 10.0` de
`detectar_pontos_frenagem_g`, em
`saru-poc-trackday/src/saru_poc/pipeline/decomposicao.py:382`.

## 1. Resposta

O acervo sustenta -3,5 m/s² sustentado por 10 m. O número está confirmado.

Em 417 voltas de quatro fontes com canal de freio real, o limiar de -3,5 m/s²
acha entre 94,8% e 99,4% das frenagens verdadeiras e inventa entre 0,00 e 0,42
frenagem por volta em trecho sem pedal. Nenhuma outra linha da grade melhora as
duas coisas ao mesmo tempo.

O platô vai de -2,5 a -4,0 m/s². Dentro dele a sensibilidade fica acima de
0,94 nas quatro fontes. Abaixo de -2,5 o falso positivo real explode na fonte
de simulador, que passa de 0,42 para 1,64 por volta em -2,0. A partir de
-5,0 a sensibilidade começa a cair, e em -6,0 o `aim_xrk` já perde 12% das
frenagens. -3,5 é o centro desse platô e não o limite dele.

Sensibilidade e falso positivo sem pedal por volta, sustentação de 10 m:

| limiar (m/s²) | acc | aim_xrk | listhead_dat | vbox |
|---:|---:|---:|---:|---:|
| -2,0 | 0,979 / 1,64 | 0,979 / 0,42 | 1,000 / 0,15 | 0,959 / 0,53 |
| -2,5 | 0,956 / 0,58 | 0,979 / 0,20 | 1,000 / 0,12 | 0,969 / 0,19 |
| -3,0 | 0,956 / 0,53 | 0,976 / 0,10 | 0,997 / 0,12 | 0,979 / 0,03 |
| -3,5 | 0,948 / 0,42 | 0,966 / 0,02 | 0,994 / 0,03 | 0,979 / 0,00 |
| -4,0 | 0,948 / 0,35 | 0,955 / 0,03 | 0,994 / 0,04 | 0,985 / 0,00 |
| -5,0 | 0,932 / 0,38 | 0,915 / 0,01 | 0,974 / 0,01 | 0,974 / 0,00 |
| -6,0 | 0,920 / 0,27 | 0,877 / 0,00 | 0,963 / 0,00 | 0,907 / 0,00 |

A física explica por que a escolha é tão frouxa. Carro freando de verdade cai
de 12,8 a 16,3 m/s² na mediana. Qualquer valor entre -2,5 e -4,0 fica uma
ordem de grandeza abaixo disso. O trabalho do limiar é separar frenagem de
ruído de acelerômetro, e para isso qualquer ponto do platô serve.

Uma troca que vale considerar em versão futura: a sustentação de 8 m em vez de
10 m eleva a sensibilidade do `acc` de 0,948 para 0,995, ao custo de subir o
falso positivo sem pedal de 0,42 para 0,53 por volta. Nas outras três fontes a
diferença entre 8 m e 10 m fica dentro de um ponto percentual. Não é motivo
para mudar o código hoje.

## 2. Amostra

Quatro fontes entraram com canal de freio real. As duas primeiras colunas de
cada linha são o que o mapa de canais da PoC (`seeds/aliases.yaml`) entregou,
com a taxa que o arquivo realmente carrega.

| fonte | formato | freio | lon_acc | arquivos | voltas | onsets reais |
|---|---|---|---|---:|---:|---:|
| `acc` | MoTeC `.ld` de simulador | `BRAKE` 60 Hz | `G_LON` 20 Hz | 20 | 55 | 562 |
| `aim_xrk` | AiM `.xrk` de F3 | `BRAKE_F` 20 Hz | `GPS_InlineAcc` 4 Hz | 40 | 263 | 1491 |
| `listhead_dat` | Pi `.dat` LISTHEAD de F3 | `Brake Press F` 50 Hz | `Acc Long` 50 Hz | 16 | 67 | 349 |
| `vbox` | Racelogic `.vbo` de Porsche Cup | `VBOX_pbrk` 10 Hz | `VBOX_accx` 10 Hz | 6 | 32 | 194 |

O corte de voltas veio de quatro origens diferentes, nenhuma inventada. As 55
voltas de `acc` saíram dos beacons do `.ldx` irmão, porque o canal `LAP_BEACON`
dos 32 arquivos de simulador está inteiro em zero. As 263 voltas de `aim_xrk`
saíram dos chunks LAP do próprio `.xrk`. As 67 voltas de `listhead_dat` saíram
do contador `Lap Number` a 1 Hz. As 32 voltas de `vbox` saíram de
`VBOX_lapnumber` a 10 Hz.

O eixo de distância veio do canal `Distance` nas 67 voltas de `listhead_dat`.
Nas outras 350 voltas veio da integral da velocidade no tempo, porque nenhuma
dessas fontes grava distância.

### O que foi baixado

O clone parcial em `_arquivo/dados_telemetria` já tinha os 58 arquivos de
`telemetria/acc-autoanalise` (254,9 MB) no disco antes desta medição.

Pedido novo por `git sparse-checkout` mais `git checkout main`:

| pasta | seleção | arquivos | tamanho |
|---|---|---:|---:|
| `telemetria/f3` | `*.dat`, `*.pid`, `*.xrk` | 96 | 243,5 MB |
| `telemetria/porsche-cup` | `*.vbo`, `*.xrk`, `*.dat`, `*.pid`, `*.ld` | 21 | 85,8 MB |
| `telemetria/giaffone-vbox` | tudo | 4 | 21,4 MB |
| `telemetria/kart-guara` | `*.xrk` | 4 | 10,8 MB |

Conteúdo novo de fato: 121 blobs, 340,2 MB. Alguns arquivos aparecem em duas
pastas com o mesmo blob, então a soma da tabela acima conta o mesmo conteúdo
mais de uma vez.

O `.git` do repositório cresceu de 788 MB para 1.616 MB, ou seja, 828 MB
transferidos, 3,5% acima do teto de 800 MB combinado. A causa está medida: dos
dois pacotes escritos hoje, um tem 114 MB e traz os 121 blobs novos, e o outro
tem 714 MB e traz 163 blobs que o repositório já possuía antes da operação.
O servidor reenviou objeto presente durante a materialização do sparse-checkout.
Um `git gc` naquele repositório recupera os 714 MB duplicados. Não rodei, porque
reescreve o object store e a tarefa é de leitura.

A varredura viu 156 arquivos e descartou 5 por conteúdo idêntico a outro
arquivo já contado, identificados por hash e não por nome. Três são os `.vbo`
do Giaffone, que moram em `giaffone-vbox` e em `porsche-cup` ao mesmo tempo.

## 3. Tabela por limiar e por fonte

Todas as linhas saíram do script da seção 7, régua "rampa" da seção 5.
`det` é o total de detecções. `fp_sem_pedal` é detecção em trecho onde o freio
ficou abaixo de 5% do fundo de escala, o falso positivo verdadeiro.
`fp_pedal_ativo` é detecção onde havia freio, só não era onset limpo pela régua
estrita. `precisão_fp_real` conta só `tp` contra `tp + fp_sem_pedal`.
Erro mediano é a distância entre o onset detectado e o real, nos casados.

### `acc`, simulador GT3, 55 voltas, 562 onsets, sustentação 10 m

| limiar | det | tp | fn | fp_sem_pedal | fp_pedal_ativo | precisão | precisão_fp_real | sensibilidade | erro mediano |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| -2,0 | 787 | 550 | 12 | 90 | 147 | 0,699 | 0,859 | 0,979 | 1 m |
| -2,5 | 696 | 537 | 25 | 32 | 127 | 0,772 | 0,944 | 0,956 | 1 m |
| -3,0 | 686 | 537 | 25 | 29 | 120 | 0,783 | 0,949 | 0,956 | 1 m |
| -3,5 | 678 | 533 | 29 | 23 | 122 | 0,786 | 0,959 | 0,948 | 1 m |
| -4,0 | 675 | 533 | 29 | 19 | 123 | 0,790 | 0,966 | 0,948 | 1 m |
| -5,0 | 670 | 524 | 38 | 21 | 125 | 0,782 | 0,961 | 0,932 | 1 m |
| -6,0 | 677 | 517 | 45 | 15 | 145 | 0,764 | 0,972 | 0,920 | 1 m |
| -8,0 | 574 | 458 | 104 | 0 | 116 | 0,798 | 1,000 | 0,815 | 2 m |
| -10,0 | 549 | 407 | 155 | 0 | 142 | 0,741 | 1,000 | 0,724 | 2 m |
| -12,0 | 566 | 347 | 215 | 0 | 219 | 0,613 | 1,000 | 0,617 | 3 m |

### `aim_xrk`, F3, 263 voltas, 1.491 onsets, sustentação 10 m

| limiar | det | tp | fn | fp_sem_pedal | fp_pedal_ativo | precisão | precisão_fp_real | sensibilidade | erro mediano |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| -2,0 | 2000 | 1460 | 31 | 111 | 429 | 0,730 | 0,929 | 0,979 | 6 m |
| -2,5 | 1917 | 1459 | 32 | 53 | 405 | 0,761 | 0,965 | 0,979 | 8 m |
| -3,0 | 1811 | 1455 | 36 | 26 | 330 | 0,803 | 0,982 | 0,976 | 8 m |
| -3,5 | 1745 | 1441 | 50 | 6 | 298 | 0,826 | 0,996 | 0,966 | 9 m |
| -4,0 | 1648 | 1424 | 67 | 8 | 216 | 0,864 | 0,994 | 0,955 | 10 m |
| -5,0 | 1545 | 1364 | 127 | 2 | 179 | 0,883 | 0,999 | 0,915 | 12 m |
| -6,0 | 1475 | 1308 | 183 | 1 | 166 | 0,887 | 0,999 | 0,877 | 13 m |
| -8,0 | 1371 | 1180 | 311 | 1 | 190 | 0,861 | 0,999 | 0,791 | 16 m |
| -10,0 | 1212 | 1050 | 441 | 1 | 161 | 0,866 | 0,999 | 0,704 | 20 m |
| -12,0 | 1008 | 792 | 699 | 1 | 215 | 0,786 | 0,999 | 0,531 | 22 m |

### `listhead_dat`, F3, 67 voltas, 349 onsets, sustentação 10 m

| limiar | det | tp | fn | fp_sem_pedal | fp_pedal_ativo | precisão | precisão_fp_real | sensibilidade | erro mediano |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| -2,0 | 373 | 349 | 0 | 10 | 14 | 0,936 | 0,972 | 1,000 | 3 m |
| -2,5 | 374 | 349 | 0 | 8 | 17 | 0,933 | 0,978 | 1,000 | 3 m |
| -3,0 | 377 | 348 | 1 | 8 | 21 | 0,923 | 0,978 | 0,997 | 3 m |
| -3,5 | 368 | 347 | 2 | 2 | 19 | 0,943 | 0,994 | 0,994 | 4 m |
| -4,0 | 372 | 347 | 2 | 3 | 22 | 0,933 | 0,991 | 0,994 | 4 m |
| -5,0 | 369 | 340 | 9 | 1 | 28 | 0,921 | 0,997 | 0,974 | 4 m |
| -6,0 | 369 | 336 | 13 | 0 | 33 | 0,911 | 1,000 | 0,963 | 5 m |
| -8,0 | 339 | 318 | 31 | 0 | 21 | 0,938 | 1,000 | 0,911 | 5 m |
| -10,0 | 242 | 225 | 124 | 0 | 17 | 0,930 | 1,000 | 0,645 | 6 m |
| -12,0 | 201 | 193 | 156 | 0 | 8 | 0,960 | 1,000 | 0,553 | 7 m |

### `vbox`, Porsche Cup, 32 voltas, 194 onsets, sustentação 10 m

| limiar | det | tp | fn | fp_sem_pedal | fp_pedal_ativo | precisão | precisão_fp_real | sensibilidade | erro mediano |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| -2,0 | 296 | 186 | 8 | 17 | 93 | 0,628 | 0,916 | 0,959 | 5 m |
| -2,5 | 284 | 188 | 6 | 6 | 90 | 0,662 | 0,969 | 0,969 | 4 m |
| -3,0 | 279 | 190 | 4 | 1 | 88 | 0,681 | 0,995 | 0,979 | 3 m |
| -3,5 | 263 | 190 | 4 | 0 | 73 | 0,722 | 1,000 | 0,979 | 2 m |
| -4,0 | 245 | 191 | 3 | 0 | 54 | 0,780 | 1,000 | 0,985 | 2 m |
| -5,0 | 215 | 189 | 5 | 0 | 26 | 0,879 | 1,000 | 0,974 | 2 m |
| -6,0 | 194 | 176 | 18 | 0 | 18 | 0,907 | 1,000 | 0,907 | 3 m |
| -8,0 | 164 | 151 | 43 | 0 | 13 | 0,921 | 1,000 | 0,778 | 6 m |
| -10,0 | 148 | 127 | 67 | 0 | 21 | 0,858 | 1,000 | 0,655 | 10 m |
| -12,0 | 120 | 92 | 102 | 0 | 28 | 0,767 | 1,000 | 0,474 | 12 m |

### Cenário de sustentação 8 m

Mesma grade, mesmas voltas, `distancia_min_m` trocado de 10 para 8. Só as
linhas do platô, para comparar com a régua de agosto:

| fonte | limiar | sensibilidade 10 m | sensibilidade 8 m | fp_sem_pedal/volta 10 m | fp_sem_pedal/volta 8 m |
|---|---:|---:|---:|---:|---:|
| `acc` | -3,0 | 0,956 | 0,995 | 0,53 | 0,64 |
| `acc` | -3,5 | 0,948 | 0,995 | 0,42 | 0,53 |
| `acc` | -4,0 | 0,948 | 0,988 | 0,35 | 0,53 |
| `aim_xrk` | -3,0 | 0,976 | 0,979 | 0,10 | 0,13 |
| `aim_xrk` | -3,5 | 0,966 | 0,969 | 0,02 | 0,04 |
| `aim_xrk` | -4,0 | 0,955 | 0,962 | 0,03 | 0,03 |
| `listhead_dat` | -3,0 | 0,997 | 0,997 | 0,12 | 0,15 |
| `listhead_dat` | -3,5 | 0,994 | 0,994 | 0,03 | 0,09 |
| `listhead_dat` | -4,0 | 0,994 | 0,994 | 0,04 | 0,10 |
| `vbox` | -3,0 | 0,979 | 0,979 | 0,03 | 0,03 |
| `vbox` | -3,5 | 0,979 | 0,979 | 0,00 | 0,00 |
| `vbox` | -4,0 | 0,985 | 0,985 | 0,00 | 0,00 |

## 4. Queda mediana de `lon_acc` no onset

Queda é o mínimo de `lon_acc` nos 40 m seguintes ao onset real de freio.
p25 e p75 entre parênteses.

| fonte | agosto de 2026 | esta medição | diferença |
|---|---:|---:|---:|
| `acc` | -16,95 m/s² | -16,34 m/s² (-17,79 · -14,19) | +0,61 |
| `aim_xrk` | -14,45 m/s² | -13,65 m/s² (-15,95 · -9,90) | +0,80 |
| `listhead_dat` | -18,65 m/s² | -15,58 m/s² (-20,47 · -11,15) | +3,07 |
| `vbox` | -16,1 m/s², amostra insuficiente | -12,79 m/s² (-15,35 · -9,59) | +3,31 |

Duas fontes batem dentro de 1 m/s². As outras duas caem menos do que agosto
mediu. A explicação provável está na amostra, não no método: agosto usou 37
voltas de `listhead_dat` e 2 de `.vbo`, e esta medição usou 67 e 32. Com
amostra maior a mediana desceu para dentro da faixa p25 a p75 da medição de
agosto nos dois casos. Não investiguei além disso.

O que importa para a decisão continua igual. Frenagem real cai entre 12,8 e
16,3 m/s² na mediana, e o limiar em discussão vale 3,5 m/s².

## 5. Régua da medição

### Verdade

Um onset real de freio existe quando o freio cruza 15% do fundo de escala e
fica acima disso por pelo menos 8 m de pista, tendo ficado abaixo de 5% por
pelo menos 30 m antes. Pedal de simulador chega em porcentagem e vai direto.
Pressão de freio em bar não declara fundo de escala, então normalizo pelo
máximo da gravação inteira, descontando o zero do sensor. O zero é o percentil
1 da gravação. Sem esse desconto, o `.xrk` de F3 fica com 4,4 bar em repouso
contra 90 bar de máximo, ou seja, 4,9% do fundo de escala, colado no piso de
5% da régua.

Duas réguas de quieto, e as duas rodaram:

A régua `estrita` é a literal de 2026-08-22. Os 30 m de quieto são os 30 m
imediatamente anteriores ao cruzamento de 15%.

A régua `rampa` exige os mesmos 30 m de quieto, mas conta a partir do último
metro em que o freio ainda estava solto, não a partir do cruzamento de 15%.
Depois de aceitar um onset, ela pula até o freio voltar a ficar abaixo de 5%,
para uma aplicação valer um onset.

A régua `rampa` existe porque a `estrita` zera em três das quatro fontes. Canal
de freio lento transforma a aplicação em rampa longa no eixo de distância. No
`.vbo` a 10 Hz e 250 km/h cada amostra vale 7 m, e os 30 m antes do cruzamento
de 15% já estão dentro da própria aplicação, medidos entre 12% e 15% do fundo
de escala. Resultado da régua `estrita`: 0 onset em 32 voltas de `.vbo`, 0 onset
em 67 voltas de `listhead_dat`, 6 onsets em 265 voltas de `aim_xrk`. Só o `acc`,
com freio a 60 Hz, sobrevive a ela. As tabelas da seção 3 usam a régua `rampa`.
A régua `estrita` aparece na seção 6 e no JSON, para comparar com agosto.

### Candidato

Detecção só por `lon_acc` canônico em m/s², abaixo do limiar, sustentada por
`distancia_min_m` metros no eixo de distância. É a mesma conta de
`detectar_pontos_frenagem_g`. Grade de limiar: -2,0, -2,5, -3,0, -3,5, -4,0,
-5,0, -6,0, -8,0, -10,0, -12,0 m/s². Grade de sustentação: 10 m e 8 m.

### Casamento

Guloso, um para um, dentro de mais ou menos 30 m. Detecção sem par vira
`fp_sem_pedal` se o freio ficou abaixo de 5% na janela de 30 m ao redor dela, e
`fp_pedal_ativo` se havia freio.

### Frame

Cada volta vai para uma grade uniforme de distância com passo de 1 m.
O eixo de distância da volta sai da cascata da PoC: canal de distância do
arquivo primeiro, integral trapezoidal da velocidade depois. Cada canal é
levado para a grade interpolando primeiro o tempo em distância e depois o valor
em distância. A volta só entra se os dois canais cobrirem pelo menos 0,9 da
grade. Volta com menos de 500 m de eixo não é volta de pista e sai.

Agosto usou o eixo `s_common` do saru-app, que é uma grade de 2.000 pontos
esticada no comprimento da pista, o que dá 2,15 m por passo em Interlagos.
Aqui o passo é fixo em 1 m, porque esta medição não resolve pista e não tem o
comprimento do layout.

### Guardas

Arquivo cujo onset real tem queda mediana positiva sai da varredura como
suspeito de sinal invertido. Nenhum arquivo caiu nessa guarda.

Arquivo repetido em duas pastas entra uma vez só, identificado por hash do
conteúdo.

Corte de voltas pela cascata: contador canônico `lap_number`, depois contador
ou pulso por nome bruto da lista de `pipeline/corte_voltas.py`, depois beacons
do próprio `.xrk`, depois beacons do `.ldx` irmão. O `.ldx` só vale se o último
beacon couber na duração declarada pelo `.ld`, com 2% de folga. Passagem a menos
de 10 s da anterior não abre volta nova.

### Reproduzir

```
cd /home/vitor/Desktop/Motorsport/SARU/saru-poc-trackday
uv run python /tmp/claude-1000/-home-vitor-Desktop-Motorsport-SARU/78c16b84-f3b3-4ee5-b36c-29523ad3aeea/scratchpad/medicao-frenagem/medir_limiar_frenagem.py \
  --raiz /home/vitor/Desktop/Motorsport/SARU/_arquivo/dados_telemetria/telemetria \
  --out medicao.json
```

151 arquivos, 156 s. Nenhuma escrita em banco, nenhuma escrita nos
repositórios.

## 6. O que não foi possível medir

O `.pid` do Pi ficou fora. O leitor `pi_pid` da PoC declara `suporta_amostra`
mas entrega contagem crua, não unidade física. Medido nos 26 arquivos: `Speed`
vai de 0 a 12.462, `Acc Long` vai de 0 a 12.462 e `QmDistance` chega a
4.294.902.201, que é 2³² menos 65 mil. O próprio cabeçalho do leitor declara o
motivo: `_apply_scale` e `_as_signed_if_declared` foram descartados no porte do
saru-app. Além disso, o perfil `pi_pid` do `aliases.yaml` não mapeia `lon_acc`,
mesmo com a coluna `Acc Long` presente a 50 Hz no arquivo, e mapeia distância
para a coluna `Distance`, que no `.pid` se chama `QmDistance`. Derivar `lon_acc`
de `d(velocidade)/dt` não resolveria, porque a velocidade também está em
contagem crua. Este é o mesmo buraco que a calibração de agosto registrou como
achado colateral 1, com outra face.

Os 4 `.xrk` do kart Guará não têm canal de freio nenhum. Não servem de verdade.
Agosto contou kart dentro da fonte `aim_xrk`, o que aqui não aconteceu.

Os 7 `.xrk` de `porsche-cup` não têm canal de freio que o perfil `aim_xrk`
mapeie. Eles gravam `BrakeF`, `BrakeR`, `ECU_BRKP_F` e `ECU_BRKP_R`, e o alias
só conhece `BRAKE_F` e `Freio_Press`. Acrescentar esses nomes ao mapa é
decisão de ingestão, não desta medição, e por isso não foram usados.

Sete dos 31 `.ld` distintos de simulador não carregam o canal `BRAKE`. São gravações de
55 a 401 s, quase todas de Nürburgring, provavelmente exportação interrompida.

O único `.ld` de `porsche-cup` ficou sem perfil. A heurística de vocabulário
não desempatou entre `acc`, `gt7_ld` e `motec_ld`, que dividem o mesmo
container.

A `.pds` do Pi Toolbox, 124 MB em `f3` e 685 MB em `porsche-cup`, não tem
leitor de amostra na PoC. Não foi baixada.

O alvo real da PoC, logger amador sem pedal, continua sem representante no
acervo. O limiar chega lá por transferência das quatro fontes acima.

O erro mediano de posição de `aim_xrk` fica em 9 m em -3,5 m/s², contra 1 a 4 m
nas outras fontes. A causa está medida e é do arquivo, não do método: o
`GPS_InlineAcc` do `.xrk` de F3 vem a 4 Hz declarados e 3,46 Hz medidos, o que
dá cerca de 14 m entre amostras a 200 km/h. A posição do onset nessa fonte não
pode ser melhor que isso.

## 7. Script e saída

Script: `/tmp/claude-1000/-home-vitor-Desktop-Motorsport-SARU/78c16b84-f3b3-4ee5-b36c-29523ad3aeea/scratchpad/medicao-frenagem/medir_limiar_frenagem.py`

Saída bruta em JSON, com as quatro fontes nas duas réguas, a lista de arquivos
usados, os descartes contados por motivo e os parâmetros da régua:
`/tmp/claude-1000/-home-vitor-Desktop-Motorsport-SARU/78c16b84-f3b3-4ee5-b36c-29523ad3aeea/scratchpad/medicao-frenagem/medicao.json`

O scratchpad é de sessão. Para a medição virar teste de regressão de E-RN-02,
o script precisa mudar para `saru-poc-trackday/scripts/` e o JSON precisa de
um lugar versionado.
