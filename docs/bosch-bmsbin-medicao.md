# Medicao do formato Bosch WinDarab .bmsbin

## Procedencia

- Lote medido: 96 arquivos `.bmsbin`, 920.338.432 bytes (878,0 MiB / 920,3 MB),
  em `dados_telemetria/telemetria/amg-gt4-26ET06-interlagos/` (12 subpastas
  numeradas por carro: 01, 04, 12, 28, 33, 40, 60, 62, 65, 70, 94...).
- 34 arquivos `Chassis`, 62 arquivos `Engine`. Menor arquivo: 655.360 bytes
  (Engine). Maior: 58.654.720 bytes (Chassis).
- Ferramentas: `xxd`, `strings`, `pdftotext`, scripts Python ad hoc (stdlib,
  nao versionados, rodados via Bash neste relatorio).
- Material de referencia consultado em
  `dados_telemetria/referencia/WinDarab/`: `WinDarab v7.4 Handbuch.pdf`
  (manual do usuario, 287 paginas) e `Bosch_Motorsport_Toolsupport_en.pdf`.
  Em `dados_telemetria/referencia/RaceCon/`: dois arquivos `.rlp`
  (`AMG_GT4_#XXXX_SU006_V127.rlp` e `..._Interlagos.rlp`), que sao o projeto
  RaceCon do carro (config de ECU/logger). Nenhum export ASCII/CSV pareado foi
  encontrado no acervo, so os `.bmsbin` binarios e os `.rlp` binarios.
- Nenhum arquivo real do acervo foi copiado para este repo. Os offsets e
  valores abaixo foram lidos direto dos arquivos originais no caminho acima.

## 0. Cabecalho fixo (offsets 0x00 a 0x23, validado em 96/96)

Hexdump de `01_Q1_Chassis_007_01-40-57_23#1263_2026.06.06_17.50.bmsbin`
(offsets 0x00 a 0x3F):

```
00000000: 4461 7261 6220 7637 2e31 302e 3038 3600  Darab v7.10.086.
00000010: 0000 0000 0000 0000 0000 0000 2300 c905  ............#...
00000020: 00d0 3401 0000 0000 b702 0000 ba04 0000  ..4.............
00000030: b701 0000 0001 0000 0000 0000 0000 0000  ................
```

Campos medidos e validados nos 96 arquivos (script Python lendo os
primeiros 64 bytes de cada um):

| offset | tamanho | conteudo | valor observado |
|---|---|---|---|
| 0x00-0x0F | 16 bytes | assinatura ASCII + NUL | `Darab v7.10.086\0`, **identica nos 96/96**, sem excecao |
| 0x10-0x1B | 12 bytes | zero-padding | `00` nos 96/96 |
| 0x1C | 1 byte | "flag de tipo de log" | `0x23` (35) em **todos** os 34 `Chassis`; `0x1F` (31) em **todos** os 62 `Engine`. Zero mistura. |
| 0x1E-0x1F | uint16 LE | campo constante por tipo | `1481` em todo `Chassis`; `1353` em todo `Engine` |
| 0x20-0x23 | uint32 LE | **tamanho total do arquivo em bytes** | igual a `os.path.getsize()` em **96/96 arquivos, sem excecao** (checado com `struct.unpack_from('<I', head, 32) == size` para cada um dos 96) |

Este e o unico ponto do arquivo que e comprovadamente auto-descritivo: o
cabecalho carrega o proprio tamanho do arquivo, e ele bate exato nos 96
casos. O par (byte 0x1C, uint16 0x1E) e uma constante por tipo de log
(Chassis vs Engine), nao por sessao: dentro de 34 arquivos Chassis de 12
carros diferentes e sessoes diferentes (Q1, TL1, TL2), o par nunca varia.
Isso e medido e reproduzivel, mas o que os numeros 35/1481 e 31/1353
*significam* (numero de canais? tamanho de registro? id de config de
ECU/logger?) eu **nao decodifiquei**: nenhuma tentativa de dividir o
tamanho do arquivo por 1481/1353 fechou em numero inteiro de forma
consistente entre arquivos, entao nao chamo isso de "numero de canais" nem
de "bytes por amostra". Fica como hipotese nao confirmada, nao como fato.

Da linha 0x24 em diante ate ~0x1A0 ha mais uint16/uint32 que se repetem
literalmente duas vezes dentro do mesmo arquivo (`b7 02 00 00`,
`ba 04 00 00`, `b7 01 00 00 00 01 00 00 00` aparecem em 0x28-0x33 e de novo
em 0x118-0x130 do mesmo arquivo). Padrao existe e e reproduzivel, mas eu
nao decodifiquei o que essa estrutura duplicada representa (poderia ser um
registro espelhado/checksum de verificacao, tipico de formatos Bosch que
tem redundancia de integridade). Nao chamo isso de tabela de canais: nao ha
nenhum campo nessa regiao que aponte, direta ou indiretamente, para uma
string de nome de canal.

## 1. O cabecalho e auto-descritivo? Ha tabela de canais, ponteiros, contagem?

Parcialmente. So o campo de tamanho total (offset 0x20) e comprovadamente
auto-descritivo (validado 96/96). Nao existe, em lugar nenhum do arquivo,
uma tabela com estrutura reconhecivel de "nome do canal + unidade + taxa +
offset/ponteiro para os dados daquele canal", que e o padrao que os outros
leitores deste repo (`.ld`, `.ldx`) conseguem explorar. Procurei por essa
tabela de duas formas:

- Varredura de todas as strings ASCII do arquivo (item 2 abaixo): nenhuma
  bate com nome de canal reconhecivel de telemetria (RPM, TPS, VCAR,
  pressao de freio etc.), so identificadores de ECU/projeto.
- Varredura de padroes de uint32 pequenos e repetidos que pudessem ser
  "contagem de canais" ou "ponteiro para tabela": os unicos candidatos
  claros sao os dois campos do item 0 (0x1C e 0x1E-0x1F), que sao
  constantes por tipo de log, nao uma lista.

Conclusao: nao ha tabela de canais legivel no cabecalho. Se existir, esta
codificada de um jeito que nao aparece como ASCII nem como um padrao
estrutural obvio nos primeiros ~8 KB do arquivo (unica regiao onde ainda
ha qualquer string legivel, ver item 2).

## 2. Strings ASCII legiveis: onde, e o que sao

Rodei `strings -a -n 4/5/6` no arquivo inteiro e tambem com offset
(`-t d`). Praticamente todas as strings legiveis (nomes com sentido, nao
lixo binario coincidindo com ASCII imprimivel) estao concentradas nos
primeiros ~2 KB do arquivo. Do arquivo `01_Q1_Chassis`:

```
offset(dec)  string
0            Darab v7.10.086
791          PAGE_01
831          PBX90_AMG_GT4_P525_1417__
863          MS6A_AMG_GT4_P525_1524__
895          DDU9_BASE_0611
1215         BOSCH MS6
1247         B07050d1.d01
1327         AMG_CUP_GT4_#2024_SU006_V127_Interlagos
1406         0sys_418.log
1487         LT AMG GT4
1567         ecu annotation goes here
1823         LPI_BASE_0517
1855         PAGE_03
1863         LAP_STK
1897         LAP_END
2076         PP UI
```

Do `01_Q1_Engine` (mesmo carro/sessao, kind Engine): strings quase
identicas na mesma faixa de offset, mais `M159 C190GT3` (codigo do motor
M159 da AMG e do chassi C190 GT3) e `GP 1`, alem de `A07050d1.d01` (no
Chassis era `B07050d1.d01`).

O que sao: identificadores de projeto/calibracao de ECU (nomes de arquivo
`.d01`, bases de calibracao `PBX90_...`, `MS6A_...`, `DDU9_BASE_...`,
`LPI_BASE_...`, o texto literal do nome do projeto RaceCon
`AMG_CUP_GT4_#2024_SU006_V127_Interlagos`, que bate com o nome dos
arquivos `.rlp` de referencia a menos do placeholder `#XXXX`), nome do
log de sistema da ECU (`0sys_418.log`), o marcador `ecu annotation goes
here` (que e um texto de template nao preenchido, evidencia de que essa
regiao vem de um template fixo do WinDarab), e tokens de volta
(`LAP_STK`/`LAP_END`, provavelmente "lap start"/"lap end"). **Nenhuma
dessas strings e nome de canal de telemetria, unidade, nome de piloto ou
nome de pista.** Sao metadados de configuracao do ECU/projeto, nao um
dicionario de canais.

Codificacao: ASCII de 8 bits (nao ha string em UTF-16 detectavel: rodei
`strings -e l` e `strings -e b` e nao apareceu nada alem do mesmo
conteudo ja visto em ASCII simples).

Depois de ~2 KB nao ha mais nenhuma string legivel ate o fim do arquivo
(confirmado varrendo os primeiros ~20 KB manualmente e o arquivo inteiro
com `strings -n 6 | sort -u`, que devolve 60 mil "strings" no
`01_Q1_Chassis`, todas ruido de 4 a 8 caracteres tipo `zZZZZZYYWVXYZ[\]^`
ou `_0C3_`, sem nenhum token com cara de nome de canal ou unidade).

## 3. Da pra determinar numero de canais e taxa por canal sem decodificar amostra?

Nao. Os unicos numeros candidatos a "numero de canais" sao o byte 0x1C
(35 para Chassis, 31 para Engine) e o uint16 0x1E (1481/1353), mas:

- Sao constantes por tipo de log em todos os 96 arquivos, entao nao
  carregam informacao por sessao (uma sessao Q1 vs uma TL1 do mesmo carro
  poderia, em teoria, logar um subconjunto diferente de canais, e esse
  campo nao mudaria pra refletir isso).
- Nao ha, associado a esses numeros, nenhuma lista de nomes/unidades pra
  cada um dos supostos 35 ou 31 canais.
- Nao consegui fechar uma conta simples (tamanho do arquivo dividido pelo
  campo, ou pelo campo vezes 4/8 bytes por amostra) que desse um numero
  inteiro de amostras de forma consistente entre os 96 arquivos.

Entao: **numero de canais e taxa por canal nao sao extraiveis do
cabecalho como esta**. So dá pra afirmar que existe uma distincao binaria
de tipo (Chassis/Engine) codificada em dois bytes fixos, nada mais.

## 4. O arquivo e comprimido? Entropia por bloco

Medi entropia de Shannon em blocos de 4 KB do inicio do arquivo, e depois
em blocos de 64 KB amostrados em varios pontos do arquivo (inicio, 10%,
25%, 50%, 75%, quase-fim), no arquivo `01_Q1_Chassis` (20.238.336 bytes):

| offset | entropia (bits/byte, max=8) |
|---|---|
| 0 | 7,85 |
| 2.023.833 (~10%) | 7,96 |
| 5.059.584 (~25%) | 7,97 |
| 10.119.168 (~50%) | 8,00 |
| 15.178.752 (~75%) | 7,99 |
| 20.172.800 (quase-fim) | 0,03 |

Em resolucao mais fina, do byte 0 ao byte 8192 (blocos de 256 bytes), a
entropia oscila entre ~0,7 (zero-padding) e ~7,2 (blobs binarios curtos ao
lado das strings do item 2) ate por volta do offset 4096, e da em diante
fica estavel entre 6,9 e 8,0 ate perto do fim do arquivo. O ultimo bloco
de 64 KB tem entropia quase zero: e uma regiao de zero-padding no final
do arquivo (ver item 6).

**Assinatura de compressao conhecida**: procurei magic bytes de gzip
(`1f 8b`), lz4 (`04 22 4d 18`), zstd (`28 b5 2f fd`), bzip2 (`BZh`), e
candidatos a header zlib (byte `0x78` seguido de segundo byte tal que
`(b0*256+b1) % 31 == 0`, que e a checagem de checksum do header zlib).
Nenhum stream real de gzip/lz4/zstd/bzip2 (a unica ocorrencia de `1f 8b`
achada no meio do blob de alta entropia e coincidencia estatistica, nao
inicio de um stream gzip valido: nao ha um stream deflate decodificavel
logo depois). Os "candidatos zlib" (7328 ocorrencias em 20 MB) sao
exatamente a taxa esperada por acaso em dados de alta entropia (1/31 dos
pares de bytes comecando com `0x78`), entao tambem nao e evidencia de
zlib real.

**Teste de aleatoriedade (qui-quadrado)** num bloco de 256 KB no meio do
payload (offset 1.000.000): qui-quadrado = 21.121 contra um limiar de
~293 pra 255 graus de liberdade a 5% de significancia. Ou seja, a
distribuicao de bytes **nao e estatisticamente uniforme**, apesar da
entropia estar perto do maximo teorico. Isso e consistente com dado
numerico real (floats IEEE-754 e inteiros de telemetria tem entropia alta
mas os bytes de sinal/expoente nao sao uniformes) ou com um output de
compressao/cifra malfeito; nao e conclusivo sozinho sobre compressao vs
nao-compressao.

**Achado mais forte, do manual do fabricante** (`WinDarab v7.4
Handbuch.pdf`, capitulo "File Password Protection" e secao "Reading Data
with non-FREE WinDarab version"): o formato binario interno do WinDarab
(que o manual chama de "Darab-Bin-File", claramente o `.bmsbin`) suporta
**protecao por senha e por "codigo de projeto" atrelado ao licenciamento
da ECU**. Citacao literal do manual (pagina ~270, secao "Reading Data"):

> "Any version of WinDarab (except FREE-Version) can import any protected
> data from FlashCard and save the data as a Darab-Bin-File. But if the
> file is protected by project code which is not allowed by licensing,
> the file still cannot be opened."

E, no capitulo de senha: "Removing the password will reactivate the
project protection of the ECU. There is no way to create a unprotected
WinDarab v6 compatible file!"

Ou seja: o proprio fabricante documenta que esse binario pode estar
protegido por um mecanismo de licenciamento/projeto que nem o WinDarab de
outros clientes consegue abrir sem a licenca certa. Isso muda a leitura
da entropia alta: nao e so "compressao proprietaria que ninguem
documentou", e possivelmente **criptografia/protecao intencional
amarrada a licenca da ECU**, o que e uma categoria de problema diferente
(nao e so engenharia reversa de formato, e contornar um gate de
licenciamento do fabricante).

## 5. Chassis e Engine do mesmo carro/sessao tem estrutura igual?

Sim, no que da pra medir. Comparei os 64 primeiros bytes de
`01_Q1_Chassis` e `01_Q1_Engine` (mesmo carro, mesma sessao):
assinatura identica, zero-padding identico, mesma posicao para os campos
de 0x1C/0x1E/0x20. A unica diferenca e o **valor** dos campos de tipo
(35/1481 no Chassis vs 31/1353 no Engine), nao a posicao ou o layout. O
mesmo vale, validado nos 96/96 arquivos via script (nao so nos pares do
carro 01): todo arquivo com `_Chassis_` no nome tem exatamente
`(0x23, 1481)` nesses dois campos, todo `_Engine_` tem exatamente
`(0x1F, 1353)`, sem excecao.

Container e identico entre os dois tipos de log; o que muda e um
discriminador de tipo em posicao fixa. E o mesmo padrao de design descrito
em `base.py` pra outros formatos deste repo (um container, canais
diferentes por variante), so que aqui eu nao consigo alcancar os canais.

## 6. Quanto do arquivo e cabecalho, quanto e payload?

- **Cabecalho comprovadamente estruturado e decodificado**: 0x00-0x23
  (36 bytes). So esses bytes tem significado que eu consegui validar.
- **Zona de metadados hibridos** (strings ASCII de projeto/ECU intercaladas
  com blobs binarios curtos de alta entropia, provavelmente hash/checksum
  de cada arquivo de calibracao referenciado): aproximadamente 0x24 ate
  algo entre 0x1000 e 0x2000 (medido: ultima string legivel do
  `01_Q1_Chassis` fica no offset decimal 2076; a entropia so estabiliza
  de vez por volta do offset 4096). Chamo essa fronteira de "algo entre 4
  e 8 KB" porque nao encontrei um marcador explicito de fim dessa zona,
  so a ausencia de mais strings legiveis dali pra frente.
- **Payload opaco**: do fim da zona de metadados ate praticamente o fim
  do arquivo. Entropia 6,9 a 8,0 o tempo todo, sem nenhuma string
  legivel, sem assinatura de compressao reconhecida. Pra um arquivo de
  20.238.336 bytes isso e mais de 99,9% do arquivo.
- **Rodape fixo**: no final do arquivo ha uma regiao de zero-padding
  (medido pelo menos 800 bytes de zeros antes do fim), seguida por um
  array de inteiros de 32 bits **sequenciais de 0 a 128** (129 valores,
  `00 00 00 00`, `01 00 00 00`, ..., `80 00 00 00`), e um pequeno trailer
  final: `03 00 00 00` / `80 00 00 00` (=128) / `7e 00 00 00` (=126) /
  `00 00 00 01`. Essa sequencia e estritamente crescente e identica em
  forma ao que se espera de uma tabela de indice generica (0..128), nao
  parece carregar informacao especifica da sessao. Nao decodifiquei o
  que ela indexa; nao chamo isso de "tabela de canais" porque nao ha
  nenhum ponteiro nem string associada a cada indice.

Resumo numerico pro maior arquivo do lote (20.238.336 bytes): cabecalho
decodificado = 36 bytes (0,0002%); zona de metadados = ~4-8 KB
(~0,02-0,04%); payload opaco = o resto, essencialmente 100% do arquivo.

## 7. Investigacao adicional (29/08/2026): .rlp, PDFs do manual e planilhas mileage

A investigacao original (secoes 0 a 6 acima) nao tinha usado o material de
referencia disponivel no acervo nem a pista da familia AiM (tabela de canal
pode morar fora do arquivo de dados, no banco de configuracao do software do
fabricante). Esta secao cobre o que cada fonte nova rendeu, medido, nao
suposto.

### 7.1 Projeto RaceCon (`.rlp`): caminho de decodificar via projeto, fechado

RaceCon e a ferramenta de configuracao da Bosch (ECU/logger). Os dois `.rlp`
de referencia (`AMG_GT4_#XXXX_SU006_V127.rlp`, 1.681.808 bytes, e
`..._V127_Interlagos.rlp`, 1.691.360 bytes) sao do mesmo carro e da mesma
pista dos 96 `.bmsbin` do lote.

Medido (script Python, entropia de Shannon em blocos de 64 KB, `strings -n 6`,
`file`, checagem de magic bytes de zip/gzip/zlib/lz4/zstd/bzip2/7z):

- **Entropia 7,988 a 7,997 bits/byte (max 8) desde o byte 0 ate o fim do
  arquivo**, nos dois arquivos. Ao contrario do `.bmsbin` (que tem cabecalho
  ASCII limpo `Darab v7.10.086\0` e ~2 KB de strings legiveis antes de virar
  opaco), o `.rlp` **nao tem nenhum trecho de baixa entropia nem string
  legivel em lugar nenhum**: `strings -n 6` devolve 2.932 tokens no arquivo
  Interlagos, todos ruido binario de 6 a 12 caracteres, nenhum com cara de
  nome de canal, projeto ou calibracao.
- `file` classifica os dois como `data` (sem assinatura reconhecida).
  Nenhuma ocorrencia de magic bytes de zip/gzip/zlib/lz4/zstd/bzip2/7z no
  inicio ou no fim de nenhum dos dois arquivos.
- Os dois arquivos (mesmo carro, pistas diferentes: generico vs Interlagos)
  tem tamanhos diferentes por ~9.552 bytes e **nenhum byte comum reconhecivel
  nos primeiros 128 bytes** (nem cabecalho, nem magic number). Isso e
  inconsistente com um container com cabecalho fixo tipo o do `.bmsbin`.

Conclusao medida: o `.rlp` esta protegido (criptografado ou comprimido com
um algoritmo que nao deixa cabecalho reconhecivel) **desde o primeiro byte**,
sem nenhuma zona de metadados em claro como a que existe no `.bmsbin`. Isso
fecha o **caminho 2 do briefing (decodificar o `.bmsbin` via tabela de canal
extraida do `.rlp`)**: nao ha tabela de canal para extrair, porque o proprio
arquivo de projeto e opaco por igual. A pista da familia AiM (tabela de canal
mora fora do arquivo de dados) **nao se confirma neste caso**: aqui os dois
lados (dado de sessao e projeto de configuracao) estao protegidos, nao so um
deles.

### 7.2 PDFs do WinDarab: sem spec de bytes, mas com o caminho de export documentado

- `Bosch_Motorsport_Toolsupport_en.pdf` e `_de.pdf` (7 paginas): sao
  procedimento de suporte tecnico (o que enviar por e-mail em caso de crash
  ou falha), nao documentacao de formato. Mencionam o `.bmsbin` uma vez
  ("The measurement data used during processing (bmsbin files)") como
  anexo a mandar em caso de bug, sem detalhar layout.
- `WinDarab v7.4 Handbuch.pdf` (287 paginas, ja citado na investigacao
  anterior pelo achado de protecao por senha/licenca): tem uma secao inteira
  de **ASCII Export/Extract** (paginas 265-266 e apendice, paginas 283-284)
  que **documenta o procedimento exato e o formato do arquivo de saida**.
  Isto e o caminho 4 do briefing (export documentado), alcancado agora com
  o procedimento literal abaixo.

### 7.3 Planilhas mileage (`.xlsm`): nao rendem vocabulario de canal

Os dois `.xlsm` (`Mercedes AMG GT4 Laufzeiten 00.xlsm`,
`Mercedes AMG GT4 Mileage 00.xlsm`) sao arquivos ZIP OOXML validos, abertos
com `unzip` e o `sharedStrings.xml` lido. As ~220 strings de cada planilha
sao vocabulario de **controle de quilometragem e substituicao de peca**
(`Laufzeit IST`, `BAUTEIL 1..20`, `WISHBONE`, `UPRIGHT`, `DAMPER`,
`Replaced part km (old)`, numero de peca Mercedes tipo `A2979890001`), nao
canais de telemetria. Nenhum nome reconhecivel de canal (RPM, TPS, pressao
de freio, velocidade) aparece nas strings. `VehicleDataABS 26.02.20 GT4.xml`
(em `Setup - Arquivo/`) tambem foi lido: e calibracao do modulo ABS
(circunferencia de pneu, bitola, massa do carro), 26 linhas, sem lista de
canais de log. **Nenhuma das duas fontes rende vocabulario aproveitavel**
para o `.bmsbin`.

### 7.4 Procedimento exato de export (ASCII Extract), para pedir ao Saru

Do manual (`WinDarab v7.4 Handbuch.pdf`, secoes "ASCII Extract (Logged
Data)" p.266 e "ASCII Extract File Format" apendice p.284), citacao
literal traduzida do passo a passo:

1. Ajustar no Oscilloscope (janela de visualizacao do WinDarab) o trecho da
   sessao que se quer extrair.
2. Menu: **WinDarab-Button / Import/Export / Export into text file**.
3. Informar o nome do arquivo ASCII de destino.
4. Selecionar o Logged Data File (o `.bmsbin`) de origem. So aparecem os
   arquivos que ja estao carregados no Oscilloscope atual.
5. Marcar as opcoes de tempo e/ou distancia, se quiser que o export inclua
   colunas `xTime`/`xDist`.
6. Informar o intervalo de amostragem do export (o passo se refere ao eixo X
   do Oscilloscope associado).
7. Selecionar a area a exportar.
8. Clicar OK. O arquivo ASCII e gravado no destino informado.

**Ponto critico, documentado no manual**: "quando voce usa a funcao ASCII
Extract para criar um arquivo, o arquivo so vai conter os canais que
estiverem exibidos no Oscilloscope" (seguindo o item 5). Ou seja, o pedido ao
Saru precisa especificar **todos os canais visiveis no Oscilloscope no
momento do export**, ou pedir explicitamente para exibir "todos os canais
disponiveis" antes de exportar, senao o CSV sai incompleto por escolha do
operador, nao por limitacao do formato.

Formato do arquivo resultante (mesma secao + "ASCII Import File Format",
apendice p.283), medido a partir da spec do manual, nao do binario:

- Texto plano, separador `;` (campo) e tambem TAB entre colunas de canal
  (o manual diz "channel columns are separated with a tab" no extract).
- Linhas de comentario comecam com `#`: o extract grava data de criacao,
  nome do Logged Data File de origem e area extraida como comentario.
- Uma linha de cabecalho por canal no formato `<Nome> [<Unidade>]` (nome
  ate 7 caracteres, unidade ate 4 caracteres, sem espaco nem colchete no
  nome).
- Valores gravados como float 32 bits, decimal com ponto no extract (o
  import aceita ponto ou virgula).
- Canais especiais `time`/`dist` viram `xtime`/`xdist` se `xdist`/`xtime`
  nao estiver disponivel.

Este e o caminho 4 do briefing, **alcancado com procedimento exato**: nao
decodifica o `.bmsbin` diretamente, mas da ao Lucas o texto pronto pra pedir
ao Saru (que ja mandou export CSV da AiM antes, precedente citado no
briefing), e o CSV resultante seria o gabarito que faltava pro item "Opcao B"
da bifurcacao original (engenharia reversa por correlacao).

## Decisao: nao escrever o leitor

**Nao escrevi `bosch_bmsbin.py`.** A barra da FASE 2 (extrair nome de
canal com taxa sem decodificar amostra) nao foi alcancada, e nem a barra
mais baixa (extrair so metadado tipo data/veiculo/sessao do PROPRIO
arquivo, tipo o `.ldx`) foi alcancada: os unicos metadados legiveis no
arquivo sao identificadores de calibracao de ECU (nomes de arquivo `.d01`,
bases de calibracao), nao data de captura, nome de piloto, nome de pista
ou numero do carro. Escrever um `Cabecalho` com `venue_declarado` ou
`capturado_em` a partir desses dados seria inventar semantica que o
arquivo nao declara, exatamente o erro que o contrato em `base.py` proibe
("o leitor NAO interpreta semantica" / "leitor que adivinha canal e a
mesma doenca do B2").

Onde travou, com offset: da fronteira da zona de metadados (~offset
0x1000-0x2000, nao determinada com precisao) ate o fim do arquivo (payload
opaco, >99,9% dos bytes), nao ha nenhuma estrutura decodificavel sem (a)
um gabarito externo ou (b) o segredo/algoritmo de protecao do fabricante.

O que seria necessario, em ordem de esforco crescente:

1. **Documentacao oficial do formato binario da Bosch Motorsport** (SDK,
   spec de bytes, ou ferramenta de linha de comando oficial de
   conversao). Nao existe em `dados_telemetria/referencia/WinDarab/`: o
   manual disponivel (287 paginas) documenta a interface do WinDarab e o
   formato *ASCII* de import/export, mas explicitamente nao documenta o
   layout binario do `.bmsbin`, e confirma que o binario pode estar
   protegido por licenca de projeto de ECU.
2. **Um export ASCII pareado** (CSV/TXT) do mesmo arquivo, gerado pelo
   proprio WinDarab por alguem com licenca e o codigo de projeto certo,
   pra servir de gabarito e permitir engenharia reversa por
   correlacao (abrir o `.bmsbin`, exportar ASCII, comparar valores
   decimais do CSV com sequencias de bytes do binario em offsets
   candidatos). Nao existe no acervo enviado.
3. **Engenharia reversa mais funda** (dissasembly do WinDarab.exe ou de
   alguma DLL do toolchain Bosch pra entender o algoritmo de
   protecao/decodificacao). Dado que o proprio manual do fabricante trata
   isso como um mecanismo de licenciamento, nao como so um formato
   proprietario obscuro, esse caminho tem um componente de "contornar
   protecao de licenca do fabricante" que e uma decisao de risco/escopo,
   nao so uma decisao tecnica.

## Bifurcacao pro Lucas

Como a medicao apontou que o obstaculo pode ser protecao de
licenciamento (nao so formato indocumentado), isso e decisao dele, nao
minha, sobre como seguir:

- **Opcao A: aceitar o buraco.** `.bmsbin` fica de fora do catalogo por
  enquanto, documentado como "formato reconhecido, sem leitor" (o
  cenario que este repo trata como divida legitima, nao mentira de
  suporte). Zero esforco adicional agora; reabre se aparecer gabarito ou
  doc oficial.
- **Opcao B: buscar gabarito.** Pedir pra equipe/dono do carro (ou pra
  quem tem licenca WinDarab) um export ASCII de pelo menos um par
  Chassis+Engine. **Procedimento exato ja levantado do manual (secao 7.4
  abaixo)**: menu "WinDarab-Button / Import/Export / Export into text
  file" (ASCII Extract), com o cuidado de pedir pra exibir todos os
  canais no Oscilloscope antes de exportar (o manual documenta que o
  extract so grava os canais que estiverem visiveis na hora, entao um
  pedido vago rende um CSV incompleto). Baixo custo de pedido, mas
  depende de terceiro ter a licenca certa (o manual sugere que nem toda
  licenca abre todo projeto).
  - Se o Lucas seguir por aqui, o leitor entra na fila de novo com
    gabarito real pra validar contra, e ai sim decide se o offset da
    "zona de metadados" e o layout do payload dao pra fechar.
- **Opcao C: contato comercial com a Bosch Motorsport** pra doc oficial
  do formato binario ou SDK. Mais lento, mais formal, resolve pra
  qualquer arquivo `.bmsbin` futuro do acervo (nao so este lote), mas
  tem custo de relacionamento/tempo que nao cabe eu estimar.

Minha recomendacao, sem decidir por ele: Opcao A agora (nao trava nada,
o resto do acervo segue andando) + Opcao B em paralelo se for facil pedir
pra equipe (baixo custo, pode desbloquear o maior lote do acervo).
Opcao C so se A+B nao renderem e o lote continuar sendo prioridade alta.

## Divida declarada

- `.bmsbin` (Bosch WinDarab, `Darab v7.10.086`) reconhecido por
  assinatura, **sem leitor**. 96 arquivos, 920,3 MB, maior lote do
  acervo, todos afetados.
- Nao ha `Cabecalho` (nem vazio) implementado pra este formato: nao
  cheguei nem no piso de "metadado sem canal" porque os unicos metadados
  legiveis sao de calibracao de ECU, nao de sessao/veiculo/pista.
- Bloqueio primario: payload de alta entropia (>99,9% do arquivo) sem
  assinatura de compressao reconhecida e com evidencia documental do
  fabricante de que o binario pode ter protecao por licenca de projeto
  de ECU. Nao investiguei se especificamente estes 96 arquivos estao
  protegidos (nao ha como confirmar sem a ferramenta oficial), so que o
  formato como categoria suporta esse mecanismo.
- Nenhum numero de canal, nome de canal, taxa de amostragem, ou qualquer
  outro conteudo semantico de telemetria foi extraido ou inferido deste
  formato.
- **Atualizado 29/08/2026 (secao 7)**: investigado o material de
  referencia do acervo que faltava (`.rlp` do RaceCon, PDFs completos do
  manual, planilhas mileage) e a hipotese de tabela de canal externa (pista
  da familia AiM). O `.rlp` **nao** guarda uma tabela de canal acessivel:
  esta protegido com a mesma opacidade do `.bmsbin`, so que desde o byte 0
  (sem cabecalho nem zona de strings). As planilhas mileage sao de
  manutencao de peca, sem vocabulario de canal de telemetria. O manual
  do WinDarab **documenta o procedimento e o formato exato de ASCII
  Export/Extract** (secao 7.4), que e o caminho 4 do briefing e fica
  pronto pra pedir ao Saru. Nenhuma das fontes novas decodificou o
  payload: caminhos 1, 2 e 3 continuam fechados como na medicao original;
  caminho 4 foi alcancado com procedimento concreto; caminho 5 nao se
  aplica porque ainda ha caminho 4 em aberto.
