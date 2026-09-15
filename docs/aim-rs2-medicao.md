# Medicao do formato AiM RaceStudio 2 (.drk, .gpk, .rrk)

## Procedencia

- Lote medido: `find "$HOME/Desktop/trabalho/clientes/saru/dados_telemetria"
  -name '*.drk' -o -name '*.gpk' -o -name '*.rrk' -o -name '*.bak'`, em
  2026-08-29.
- `.drk`: 76 arquivos, `.bak`: 53 arquivos (129 no total, todos tratados
  juntos porque o item 5 abaixo mostra que sao o mesmo container por
  radical de nome, so que NAO byte-identicos). `.gpk`: 68 arquivos.
  `.rrk`: 67 arquivos.
- Ferramentas: scripts Python ad hoc (so stdlib: `struct`, `re`, `hashlib`),
  rodados via Bash e descartados apos a medicao (nao versionados, viviam em
  `/tmp`). Nenhum arquivo real do acervo foi copiado pra este repo: os
  offsets abaixo foram lidos direto dos arquivos originais no caminho
  acima.
- Ponto de partida: o leitor de referencia `drk_file.py`
  (`saru-app/services/telemetry-api/saru_lapanalyzer/infra/datasources/`,
  so leitura), que assume uma tabela de descritores de 288 bytes a partir
  do offset `0x800` pra canal, e uma varredura de forca bruta por
  coordenada GPS de 32 bits no `.gpk`.

## Item 1: quantos .drk/.bak tem tabela de descritores decodificavel em 0x800

**Reproduzi a funcao `_parse_channels_table` + `_drop_noise_channels` do
`drk_file.py` byte a byte** (mesmo offset `0x800`, mesmo passo de 288
bytes, mesma regex de nome `^[a-zA-Z0-9_\s#%°\-/]+$`, mesmo filtro de
ponteiro `0 < data_offset < tamanho` e `0 < n_amostras < 500_000`, mesmo
filtro `len(nome) >= 2`).

**Resultado medido: 0 de 129 arquivos `.drk`/`.bak` produzem qualquer canal
decodificavel.** Rodei tambem contra os 67 `.rrk` (o mesmo parser se aplica
a eles no `drk_file.py`, ja que `.rrk` cai no mesmo `_load_drk`): tambem 0
de 67. Total: **0 de 196**.

Isso e mais estrito que a doc do saru-app ("160 dos 167 nao tem tabela
decodificavel", ou seja 7 decodificaveis), mas nao contradiz: o proprio
`drk_file.py` documenta que esses 7 eram nomes de canal tipo `'°'`, `'y'`,
que sao ruido binario lido como texto e sao descartados pelo filtro
`len(nome) >= 2`. Rodando os DOIS filtros juntos (que e o comportamento
real de producao: `_load_drk` chama os dois em sequencia), o numero de
arquivos que sobrevivem com pelo menos um canal e **zero**, nao sete. A
doc do saru-app ja aponta pra isso implicitamente (`if not channels: raise
UndecodableChannelsError`), so nao tinha o numero final explicito. Meu
numero fecha essa lacuna: com o acervo atual (129+67=196 arquivos, maior
que os 167 do snapshot de 2026-08-15), a taxa de sucesso do metodo
"288 bytes em 0x800" e 0%.

Achado a parte, fora do escopo do que o saru-app assume: abri o maior
arquivo do acervo (`Matt Romanowski_Watkins Glen_June182020Webinar.drk`,
9,5 MB, magic `RDX\x02`) e achei, por busca de string ASCII, um bloco real
de nomes de canal (`Logger Temperature`, `FRWheelSpeed`, `BrakePressure`,
`GPS_Speed`, etc., ~50 canais) comecando perto de `0x900`, com passo
**variavel** entre `0x420` (1056 bytes) e multiplos disso, NAO os 288 bytes
fixos que o `drk_file.py` assume. Cada registro tem nome nos primeiros 20
bytes e a unidade textual (`mph`, `psi`) exatamente no offset `+0x14` (20)
do registro, confirmado em 4 canais (`FRWheelSpeed`, `FLWheelSpeed`,
`BrakePressure` com unidade certa; `Logger Temperature` e `External
Voltage` sem unidade, campo vazio no mesmo offset). Isso e evidencia de que
EXISTE uma tabela de canal real em pelo menos parte do acervo, so que numa
familia de layout diferente da que o `drk_file.py` (e eu, na primeira
tentativa) assumimos. Nao virou leitor: ver Fase 2, decisao.

## Item 2: os descritores de 288 B trazem taxa, nome, unidade, contagem?

**Os descritores de 288 bytes em `0x800` (a hipotese do `drk_file.py`) nao
aparecem em NENHUM arquivo real** (item 1: 0/196 tem sequer um descritor
que passe no filtro de nome+ponteiro). Entao a pergunta "o que esses
descritores trazem" nao tem resposta no acervo medido: a estrutura que o
`drk_file.py` documenta e uma hipotese que nao bate com os bytes reais em
`0x800` de nenhum arquivo.

Hexdump anotado de um dos 32 slots de 288 bytes em `0x800`, arquivo
`Matt Romanowski_Watkins Glen_June182020Webinar.drk`, offset `0x800`:

```
000800  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
000810  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
000820  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
000830  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
000840  49 49 58 02 7f 02 00 00 00 00 00 00 00 00 00 00  IIX.............
```

Zero puro nos primeiros 64 bytes, depois um marcador `IIX\x02` que nao e
nome de canal nenhum. O real bloco de canal deste arquivo comeca em
`0x900`, nao `0x800`.

**Achado do descritor real** (familia diferente, nao registrada em
leitor): tomando o registro `FRWheelSpeed` em `0x1560` como exemplo (ver
item 1), os primeiros 0x40 bytes sao:

```
001560  46 52 57 68 65 65 6c 53 70 65 65 64 00 00 00 00  FRWheelSpeed....
001570  00 00 00 00 6d 70 68 00 00 00 00 00 00 00 01 00  ....mph.........
001580  00 00 00 00 00 00 03 00 00 00 00 00 00 00 00 00  ................
001590  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
0015a0  e7 03 00 00 03 00 04 00 62 a7 00 00 3c 64 28 41  ........b...<d(A
0015b0  40 41 02 43 00 00 00 00 00 00 00 00 3c 64 28 41  @A.C........<d(A
```

- `+0x00` (20 bytes): nome, `"FRWheelSpeed\0..."`.
- `+0x14` (confirmado com 3 canais de unidade diferente): unidade,
  `"mph\0"`.
- `+0x40`: `u32 = 999`. **Candidato a contagem de amostra, nao
  confirmado**: nenhum arquivo teve o numero de amostras validado contra
  duracao de sessao conhecida.
- `+0x4c` / `+0x50`: `float32 = 10.52` / `130.25`. **Candidato a
  min/max do canal** (faz sentido pra velocidade de roda em mph),
  nao confirmado.
- **Taxa de amostragem: nao achei campo candidato confiavel.** Nenhum u16/u32
  nos primeiros 0x60 bytes bate com um valor plausivel de Hz (1, 5, 10,
  20, 50, 100) de forma consistente entre os 4 canais testados.
- O passo entre registros **nao e constante**: `0x420` entre 2 dos
  registros testados, `0x840` (2x) entre outros dois. Isso sugere bloco de
  tamanho variavel por canal (ex.: tabela de calibracao de tamanho
  variavel dentro do registro), que eu nao consegui fechar com confianca
  suficiente pra virar leitor sem reverse-engineering bem mais extenso.

**Veredito do item 2: nao, os 288 bytes assumidos pelo saru-app nao trazem
nada, porque essa estrutura nao existe nos arquivos reais.** Existe uma
estrutura de descritor DIFERENTE, com nome e unidade confirmados, contagem
e min/max candidatos nao confirmados, e taxa de amostragem NAO
localizada, com passo de registro variavel. Nao virou leitor (ver Fase 2).

## Item 3: o .gpk tem estrutura legivel, ou e blob de forca bruta?

**Nao tem estrutura legivel que eu tenha conseguido decodificar; a
varredura de forca bruta do saru-app produz principalmente ruido.**

O `.gpk` (68 arquivos) comeca com um cabecalho de blocos com tag ASCII de
4 bytes + versao, repetido:

```
000000  50 52 4f 56 00 01 00 00 00 00 00 00 00 00 00 00  PROV............
000010  50 52 4f 56 00 01 00 00 00 00 02 15 00 00 0f c8  PROV............
000020  67 15 1d fb 50 41 13 3d ad 74 3a 12 25 41 5d 42  g...PA.=.t:.%A]B
000030  ae cc f0 2a 51 41 00 00 00 00 00 00 00 00 00 00  ...*QA..........
000040  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
000050  50 53 4f 4c 00 01 00 00 00 00 00 00 00 00 00 00  PSOL............
```

Ha tags repetidos (`PROV`, `PSOL`) em posicoes fixas pequenas (`0x00`,
`0x10`, `0x50`), o suficiente pra ver que e um formato de blocos com
cabecalho, mas eu **nao decodifiquei** o que separa um bloco do outro (o
segundo `PROV` em `0x10` tem um payload de floats que parece coordenada
mas eu nao confirmei contra nenhuma referencia), nem o tamanho de cada
bloco, nem onde comeca a proxima tag. Reverse engineering incompleto:
reportado, nao inventado.

Rodei a varredura de forca bruta do `drk_file.py`
(`_extract_gpk_coords`: todo offset multiplo de 4, interpreta como par de
`int32` em micrograus, aceita se cair em -85..85 lat / -175..175 lon) no
menor `.gpk` do acervo (`0702176... ` na verdade usei o primeiro do
`glob`, 774.528 bytes): **55.466 "coordenadas" aceitas em 0,22s**. A
primeira dezena inclui pontos claramente absurdos pra um kartodromo
(`lat=-8.20, lon=102.47` = meio do oceano perto da Indonesia;
`lat=72.04, lon=0.0017` = Ártico), o que confirma que o metodo aceita
ruido em volume: nao ha como, so olhando o numero de "coordenadas"
aceitas, saber quantas sao dado real e quantas sao coincidencia
aritmetica. **Nao existe verificacao independente no proprio arquivo (ex.:
um contador de pontos declarado no cabecalho) pra validar a contagem.**

**Se tem GPS, a que taxa, da pra saber sem varrer o arquivo inteiro?**
Nao. Nao achei nenhum campo no cabecalho de blocos que declare contagem de
pontos ou taxa; a unica forma que o saru-app (e eu, tentando reproduzir)
consegue estimar "quantos pontos" e varrendo o arquivo inteiro byte a
byte, e o resultado dessa varredura e majoritariamente ruido, como acima.

## Item 4: o .rrk contem o que?

**Nao decodifiquei o conteudo.** Fatos medidos:

- 67 arquivos, 16.036.352 bytes totais, media de 239.349 bytes (min 5.888,
  max 1.062.848).
- Comeca com o mesmo padrao de blocos do `.gpk`, mas com tags diferentes:
  `HEAD` (nao `PROV`) e depois `NSOL` (nao `PSOL`):

```
000000  48 45 41 44 00 01 00 00 00 00 00 00 00 00 00 00  HEAD............
000010  48 45 41 44 00 01 00 00 00 00 00 00 00 00 de 40  HEAD...........@
000020  00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
000030  4e 53 4f 4c 00 01 00 00 00 00 00 00 00 00 00 00  NSOL............
000040  4e 53 4f 4c 3e 00 00 00 c8 eb d9 21 00 00 00 00  NSOL>......!....
```

- **Nao e amostra de canal completa**: uma sessao de kart tipica (dezenas
  de canais, 1 kHz+, minutos de duracao) exigiria dezenas de MB, e a media
  aqui e 240 KB. Consistente com **indice/resumo de sessao**, mas isso e
  `(inferido)`: nao achei nenhum campo de contagem ou string que confirme.
- **Sem metadado de texto**: testei os mesmos offsets de piloto/veiculo/
  venue/data que funcionam pro `.drk` (item 6) contra os 67 `.rrk`; 0
  tinham os 4 campos simultaneamente legiveis como ASCII puro, e os 10
  "positivos" de uma primeira passada (filtro fraco: qualquer string nao
  vazia) eram lixo binario (fragmentos de `"NSOL"`, 1-2 caracteres soltos),
  nao texto real. Corrigido: 0/67.
- Dado o mesmo padrao de blocos `TAG+versao` repetido do `.gpk`, e
  provavel (`inferido`) que `.gpk` e `.rrk` compartilhem o mesmo container
  de baixo nivel (formato de blocos generico da AiM), com `.gpk` guardando
  trajeto/posicao e `.rrk` guardando outra coisa (indice de corrida,
  configuracao, resultado). Nao confirmado.

## Item 5: .drk e .bak de mesmo radical sao byte-identicos?

**Nao.** SHA-256 de 50 pares com o mesmo radical de nome (ex.:
`Gabriel Bortoleto_...c_1154.drk` e `Gabriel Bortoleto_...c_1154.bak`):

- **1 par identico** (mesmo hash).
- **49 pares diferentes**, e em TODOS os 49 o `.bak` e MENOR que o `.drk`
  correspondente (nunca o contrario), com a razao de tamanho variando
  bastante (de ~72% a ~84% do tamanho do `.drk`, com um caso extremo: os 4
  arquivos `davi_67_...` tem `.bak` com so ~27-36% do tamanho do `.drk`
  irmao).
- 18 `.drk` nao tem `.bak` correspondente por radical; 3 `.bak` nao tem
  `.drk` correspondente.

Isso **contradiz a premissa de "mesmo container"** que motivou tratar
`.bak` como alias de extensao no catalogo (`aliases_ext=(".bak",)` em
`formatos.py`): os bytes magicos batem (ambos comecam com `RD`), a
estrutura de blocos provavelmente e a mesma familia, mas o conteudo NAO e
uma copia identica. Hipotese mais provavel (`inferido`, nao confirmado):
`.bak` e um snapshot anterior da mesma gravacao (RaceStudio 2 salva
incrementalmente e o `.bak` fica pra tras), nao um backup byte-a-byte do
`.drk` final. Isso nao muda o formato_id (a assinatura e a mesma, o
alias de extensao continua correto pra deteccao), mas muda a expectativa:
nao dá pra tratar um par `.drk`/`.bak` como duplicata a descartar sem
olhar o conteudo.

## Item 6: existe metadado em TEXTO, com offset?

**Sim, em `.drk`/`.bak`, e e o achado mais solido desta medicao.** Quatro
campos de texto ASCII puro em offset FIXO e ABSOLUTO (nao relativo a
nenhum ponteiro), confirmados contra os 129 arquivos completos (nao so
amostra):

| offset | tamanho | conteudo | exemplo real |
|---|---|---|---|
| `0x4c` (76) | 24 bytes | data/hora, `DD-MM-AA HH:MM:SS` | `"02-02-21 16:13:06"` |
| `0x440` (1088) | 40 bytes | veiculo | `"F309-016"` |
| `0x468` (1128) | 40 bytes | pista/venue | `"Interlagos"` |
| `0x490` (1168) | 40 bytes | piloto | `"Gabriel Bortoleto"` |

Os tres ultimos campos sao **contiguos**: `0x440 + 40 = 0x468`,
`0x468 + 40 = 0x490`. E um array de 3 campos de 40 bytes, confirmado em
amostra aleatoria de 20 arquivos (nomes de piloto, pista e veiculo batendo
exatamente com o que o nome do arquivo ja indicava, ex.: arquivo
`Pedro Aizza_F309-016_..._Goiania_...` -> campos `driver="Pedro Aizza"`,
`veh="F309-016"`, `venue="Goiania"`) e depois contra o acervo completo.

**Taxa de sucesso medida, com criterio estrito (campo tem que ser 100%
bytes no intervalo ASCII imprimivel `0x20-0x7e`, senao conta como
ausente, nunca decodificado como lixo; ao menos 1 dos 4 campos legivel
conta como sucesso):**

- `.drk`: 72 de 76 (95%).
- `.bak`: 53 de 53 (100%).
- Total `.drk`+`.bak`: **125 de 129 (97%)**.

Os 4 arquivos sem nenhum dos 4 campos (`Test.drk`, `Test #1.drk`,
`WarmUp.drk`, `81214006.drk`, todos `.drk`) nao sao falha: tem magic
diferente (`RD\x90\x01` ou `RD\xf4\x01`, contra `RDX\x02` dos outros
125/129) e os 4 campos existem no arquivo mas **genuinamente vazios**
(bytes nulos, nao lixo binario nem texto truncado). Cabecalho pobre e
resultado legitimo, nao erro de leitura.

**`.gpk` e `.rrk` nao tem esse metadado** nos mesmos offsets (testei):
`.gpk` tem os tags `PROV`/`PSOL` que sao literalmente texto mas sao
marcadores de bloco, nao metadado de sessao; `.rrk` nao tem nada legivel
nos offsets do `.drk` (item 4).

## Fase 2: decisao

**Escrevi o leitor, mas SO para a parte que a medicao confirmou: metadado
de sessao do `.drk`/`.bak` (item 6).** `src/saru_poc/readers/aim_rs2.py`,
classe `LeitorAimDrk`, `formato_id="aim_drk"` (o mesmo do catalogo, `.bak`
e alias de extensao do mesmo formato_id, entao um leitor so cobre os
dois). `Cabecalho.canais` sai sempre como tupla vazia: **nenhum canal
com amostra e taxa foi decodificado, e nao escrevi nada que finja o
contrario.** Isso e o mesmo padrao que `LeitorLdx` (`motec_ldx`) ja usa
pra sidecar sem canal.

Justificativa por item:

- **Canal com taxa (item 1+2): NAO escrevi leitor.** 0/196 decodificavel
  pelo criterio do saru-app; o achado alternativo (registro de ~0x420+
  bytes com nome+unidade em pelo menos um arquivo grande) tem campo de
  nome e unidade confirmados, mas **taxa de amostragem nao localizada** e
  **passo de registro variavel nao entendido**. Escrever um leitor de
  canal em cima disso seria arriscar exatamente o que o repo existe pra
  evitar: declarar `Cabecalho.canais` com uma `frequencia_hz` chutada.
- **GPS do `.gpk` (item 3): NAO escrevi leitor.** A forca bruta do
  saru-app produz majoritariamente ruido (55 mil "coordenadas" num
  arquivo de 774 KB, com exemplos absurdos nos primeiros 5), e nao ha como
  separar sinal de ruido sem decodificar a estrutura de blocos real, que
  eu nao consegui fechar no tempo desta medicao. Concordo com a recusa que
  o `drk_file.py` ja tem pra `.gpk` avulso, so que por um motivo mais
  forte: nao e so "gpk nao e sessao", e "gpk nem decodifica GPS de forma
  confiavel do jeito que esta sendo tentado hoje".
- **`.rrk` (item 4): NAO escrevi leitor.** Sem metadado de texto, sem
  hipotese de conteudo confirmada, arquivo pequeno demais pra ser amostra
  de canal completa. Fica como divida declarada.
- **Metadado do `.drk`/`.bak` (item 6): escrevi leitor.** 125/129 (97%)
  com pelo menos piloto+veiculo+venue+data legiveis por offset fixo,
  validado contra o acervo inteiro (nao so amostra), com os 4 arquivos
  restantes sendo cabecalho pobre legitimo (variante de magic diferente),
  nao erro.

## Divida declarada (nao resolvida nesta tarefa)

1. **Canal com taxa em `.drk`/`.bak`**: existe uma familia de registro
   real (nome + unidade confirmados em pelo menos 1 arquivo de 9,5 MB, bem
   diferente dos 288 bytes que o saru-app assume), mas taxa de amostragem
   e tamanho de registro variavel nao foram decodificados. Precisa de
   reverse-engineering dedicado (varios arquivos, comparando contagem de
   amostra candidata contra duracao de sessao conhecida) antes de virar
   leitor. **Bifurcacao pro Lucas**: vale investir nisso, dado que so
   achei essa estrutura em 1 dos 129 arquivos ate agora (nao sei se e
   comum ou raro no acervo)?
2. **Estrutura de blocos `PROV`/`PSOL` (`.gpk`) e `HEAD`/`NSOL` (`.rrk`)**:
   os dois parecem compartilhar um container de blocos com tag ASCII de 4
   bytes + versao, mas o layout de cada bloco (tamanho, campos) nao foi
   decodificado. Se alguem decodificar isso, os dois formatos provavelmente
   caem juntos.
3. **`.bak` nao e copia do `.drk`**: contradiz a premissa do catalogo
   atual (`aliases_ext=(".bak",)` implicando "mesmo container" no
   comentario de `formatos.py`). O alias de extensao continua correto pra
   deteccao (mesma assinatura), mas o conteudo real difere; quem for medir
   volume de dado do acervo por sessao nao pode somar `.drk` + `.bak` do
   mesmo radical como se fossem coisas diferentes, nem descartar um dos
   dois como duplicata sem checar.
4. **`readers/__init__.py` nao foi tocado** (fora do escopo desta tarefa):
   `LeitorAimDrk` existe mas nao esta registrado em `_registrar_embutidos`.
   Fica pra quem tiver permissao de editar esse arquivo.

## Complemento (2026-09-14): reconfirmação com amostra nova, escopo de cobertura de dados

Reconfirmação, no âmbito de `docs/cobertura-de-dados-resumo.md`, com 10
`.drk` únicos novos (sorteio diferente do original), via
`LeitorAimDrk.inspecionar()`:

- 10/10 abriram sem erro.
- `Cabecalho.canais` vazio nos 10/10, confirmando de novo a conclusão de
  que a tabela de descritores em `0x800` não decodifica canal.
- Correção da nota "4": `LeitorAimDrk` **já está** registrado em
  `readers/__init__.py::_registrar_embutidos` (conferido nesta data); a
  nota anterior ficou desatualizada.
- `inspecionar()` na amostra nova: 23,8 a 956,6 MB/s (arquivo inteiro cabe
  em memória, maior `.drk` do acervo é 1,8 MB por medição anterior; não há
  indício de leitor lento ou de materialização desnecessária dado o
  tamanho típico do formato).

Sem issue nova de cobertura de canal para `.drk` pelo mesmo motivo do
`.gpk`/`.rrk`: `canais=()` é resultado correto, não falha.
