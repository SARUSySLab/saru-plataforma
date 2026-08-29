# Mapa de parsing: os dois motores do SARU

> Levantamento de 2026-08-29. Fonte: leitura integral do codigo dos dois repos.
> Motor A (legado): `saru-app/services/telemetry-api/saru_lapanalyzer/`
> Motor B (PoC, em producao em saru.lassoftware.com.br): `saru-poc-trackday/src/saru_poc/`
> Toda afirmacao aqui esta ancorada em `arquivo:linha`. Onde o codigo mede algo, o numero medido esta junto.

## 1. Resumo em uma tela

| | Motor A (legado) | Motor B (PoC) |
|---|---|---|
| pacote | `saru_lapanalyzer/infra/datasources/` | `src/saru_poc/readers/` |
| arquivos de parser | 19 + `vendor/ldparser` | 15 |
| linhas | ~3.541 | ~6.157 |
| formatos com leitor | 8 binarios + 10 de texto (7 mortos) | 12 registrados, 6 leem amostra |
| detecao | extensao (cascata `if/elif`) | assinatura/magic (tabela declarativa) |
| fallback quando nada casa | `CsvFileDataSource`, e depois perfil `"acc"` | `Deteccao(None, "nenhuma")`, sem default |
| dado tabular | `pandas.DataFrame` | `pyarrow.RecordBatch` em `Lote` |
| celula sem amostra | `np.interp` (interpola) | `NaN` (nunca interpola, nunca repete) |
| traducao de canal | dentro do parser + `aliases.yaml` | fora do leitor, etapa 3 do pipeline |
| persistencia do dado pesado | pickle no Redis (TTL 1h) + MinIO opcional | Parquet zstd enderecado por conteudo |
| corte de voltas | dentro do `IngestionService` | etapa 5 separada, cascata de 4 degraus |

A frase que resume a diferenca: **o motor A adivinha e conserta; o motor B mede e recusa.**

## 2. Cobertura de formato, lado a lado

| formato | fabricante | Motor A | Motor B |
|---|---|---|---|
| `.ld` | MoTeC | sim (via `vendor/ldparser`) | sim (`struct` puro, sem ldparser) |
| `.ldx` | MoTeC | sim (so oraculo de validacao) | sim (fonte de beacon, degrau 2 do corte) |
| `.xrk` / `.xrz` | AiM RS3 | sim, **exige `libxrk` (C++)** | sim, **Python puro** |
| `.dlf` | atribuicao divergente | sim (rotulado AiM) | sim (rotulado Pro Tune TDL, a confirmar) |
| `.vbo` | Racelogic VBOX | sim | sim |
| `.pid` | Pi / Cosworth | sim | sim |
| `.dat` LISTHEAD | Pi / Cosworth | sim | sim |
| `.xlsm` / `.xlsx` | generico | sim, **nao roteado** | nao |
| CSV de sim (ACC, AMS2, GT7, iRacing) | varios | sim, **7 dos 10 mortos** | nao |
| CSV TrackAddict | HP Tuners | sim, vivo | nao |
| `.pds` | Pi Toolbox | nao | inventario (sem amostra) |
| `.mf4` | ASAM (norma aberta) | nao | inventario (sem amostra) |
| `.drk` / `.bak` | AiM RS2 | nao | so metadado de texto |
| `.gpk` / `.rrk` | AiM RS2 | nao | so framing, zero canais |
| `.bmsbin` | Bosch WinDarab | nao | **catalogado, sem leitor** (920 MB de acervo) |

Os conjuntos so se cruzam em 7 formatos. Nao e reescrita um-pra-um.

## 3. Motor A: como o legado decide o formato

### 3.1 O dispatch real

`application/ingestion_service.py:272-296`, cascata `if/elif` por extensao:

```
.xrk/.xrz -> XrkFileDataSource          :274
.ld       -> LdFileDataSource           :277
.vbo      -> VboFileDataSource          :279
.dlf      -> AimDlfFileDataSource       :281
.dat      -> ListheadDatFileDataSource  :283
.pid      -> PidFileDataSource          :285
sniff     -> TrackAddictCsvDataSource   :286-294   (unico ramo por conteudo)
else      -> CsvFileDataSource          :296
```

Consequencias diretas:

- **Empate e impossivel** (curto-circuito, posicoes 1 a 6 disjuntas por extensao).
- **"Nenhum casar" tambem e impossivel.** Nao existe braco de erro. Um `.zip`, um `.xlsx` ou um PNG cai no `CsvFileDataSource` e falha depois como `ParserError` do pandas, sem mensagem util.
- Dentro do CSV, o dialeto sai de `ChannelMapper.detect_sim` (`channel_mapper.py:103-124`), voto por presenca de coluna, maior score vence. **Empate resolvido em silencio pelo `max()`**, ordem de insercao do dict decide.
- Fallback final em `ingestion_service.py:313`: `source = override or bundle.source_hint or "acc"`. Um CSV de dialeto desconhecido e mapeado com os aliases do **ACC**, e a falha aparece como `MissingChannelError: 'speed'` em vez de "formato desconhecido".

### 3.2 `__init__.py` nao e um registry

`datasources/__init__.py` e um barrel de re-export com `__all__` ordenado alfabeticamente. Nao ha lista de prioridade nem loop de `can_handle`. E **nao exporta** `TrackAddictCsvDataSource`, `ListheadDatFileDataSource` nem `PidFileDataSource`, tres dos que o dispatch realmente usa.

### 3.3 Sete parsers de texto estao mortos

Do dispatch acima, so `CsvFileDataSource` e `TrackAddictCsvDataSource` sao alcancados. Ficam instanciados-mas-nunca-chamados, ou nem instanciados:

| parser | estado | problema latente |
|---|---|---|
| `real_aim_csv.py` | morto | `can_handle` aceita qualquer arquivo com `"Format"` ou `"Vehicle"` nas 5 primeiras linhas (`:54-64`). `skiprows=14` fixo. Le metadado do cabecalho com as chaves cruas (`"Racer"`, `"Venue"`) e o `IngestionService` procura `driver`/`track`: **o metadado e lido e descartado**. |
| `real_windarab_csv.py` | morto | `sep=';'` **sem `decimal=','`** (`:25`). CSV europeu com essa combinacao le toda coluna numerica como string. `tests/validation/test_origin_detection.py:161` ja registra que o detector nao reconhece o proprio corpus. |
| `real_wintax_csv.py` | morto | **estritamente pior que o generico**: `can_handle` so dispara quando ha banner, e `load` nao passa `skiprows` (`:27-33`), entao sempre le o banner como header. O `CsvFileDataSource` ja trata WinTAX certo (`csv_file.py:22-24`). |
| `sim_acc_motec.py` | morto | assinatura `{VehSpd, G Long, T Tyre FL I}` (`:18`) e do **CSV do MoTeC i2**; o perfil `acc` do `aliases.yaml` espera `SPEED, RPMS, G_LAT, LAP_BEACON`, que e o dialeto do **`.ld`**. Se fosse ligado, todo arquivo aceito quebraria em `MissingChannelError`. |
| `sim_ams2_csv.py` | morto | consistente ponta a ponta. `steering` com lock fixo de +-90 graus e aproximacao declarada. |
| `sim_gt7_csv.py` | morto | tres constantes sao chute explicito no YAML: lock +-30 graus, raio de roda 0,318 m (erro de ate 12% por categoria), remapeamento de eixo do pacote UDP. |
| `sim_iracing_csv.py` | morto | o mais limpo em unidade (iRacing ja emite SI). `distance` tem `scale: null`, resolvido em runtime por `track_length_m`: unico canal do sistema com escala dinamica. |

### 3.4 Os dois que estao vivos

**`csv_file.py`** (o generico). `sep=None` + `engine="python"` = `csv.Sniffer` decide o separador. **Sem `decimal=`, sem `encoding=`.** `_detect_banner` (`:80-107`) varre **5 linhas** procurando token conhecido; nao achando, assume header na linha 0 (deslocamento silencioso). `metadata` sai vazio.

**`track_addict_csv.py`** (308 linhas, o unico parser de texto forense). Nao herda do generico por motivo medido: o preambulo do TrackAddict tem exatamente 5 linhas e o header esta na 6a, entao `_detect_banner` nunca acha e o generico levanta `ParserError`. Detecta por regex na primeira linha (`^#\s*RaceRender Data:\s*TrackAddict`). Trata `#` **no meio dos dados** (`# Lap N`, `# Pit Lane Entry/Exit`), o que `skiprows` seria incapaz de fazer. Converte km/h vs MPH **dentro do parser** porque a unidade depende da preferencia do usuario e a gramatica de alias so multiplica por constante fixa; unidade nao reconhecida levanta `ValueError` em vez de assumir ("assumir uma delas erraria a velocidade por 1,6x sem crashar nada a jusante"). Unico dos dez que preenche os cinco campos do `RawTelemetryBundle`.

Achado de operacao no TrackAddict: a coluna `Lap` e a marca `# Lap N: HH:MM:SS.mmm` **discordam em ate 0,949 s**, porque o app interpola o cruzamento entre dois fixes de GPS (0,934 Hz) e a coluna so vira na amostra seguinte (20 Hz). Quem exibir tempo de volta tem que usar `metadata["lap_markers"]`.

## 4. Motor A: os parsers binarios

Nenhum e stub. Nenhum `NotImplementedError` nos nove arquivos.

| formato | detecao | voltas | fator de escala |
|---|---|---|---|
| `.ld` | extensao (`ld_file.py:174`) | `.ldx` como oraculo + sintese por queda de `TIME` > 60 s | `(raw/scale * 10^-dec + shift) * mul` (`ldparser.py:399`) |
| `.ldx` | irmao do `.ld` (`ldx_reader.py:55`) | so contagem e fastest, **nao tem beacon por volta** | n/a |
| `.DLF` | ext + sniff `#V2` / `#SERIALNUMBER` | canal `Lap Number` | n/a |
| `.xrk` / `.xrz` | ext + magic zlib `78 01` | `log.laps`, ou corte por GPS (85 arquivos do acervo caem aqui) | n/a |
| `.vbo` | extensao | `VBOX_lapnumber` | lat/long em minuto de arco, convertido fora |
| `.pid` | **magic `01 20 03 23`** | `Beacon Code` a 50 Hz, debounce 5 s | divide **ou** multiplica, decidido pela faixa declarada |
| `.dat` | **magic `LISTHEAD`** | nos `EVNT_B0` | nenhum, `float32` ja em unidade |
| `.xlsm` | extensao | nenhuma | n/a |

Tres pecas merecem destaque porque sao engenharia reversa de verdade:

**`.pid`** (`pid_file.py`, 445 linhas). Bloco = 1 segundo, interleaved em 100 ticks de 10 ms, quadro de **tamanho variavel** (tick 0 leva todos os canais, 112 B; tick 1 leva so os de 100 Hz, 12 B). A invariante `sum(rate_hz * width) == block_size` fecha em 3044 B com 49 canais, e e checada: falhar levanta. O fator de escala **nao e sempre divisor**: `Speed` 2572 vira 257,2 km/h dividindo, `Steering` vira milimetro multiplicando por 0,0977517. A decisao e do arquivo, vale a operacao cujo resultado cai dentro de `[min, max]` declarado; ambigua, o valor sai cru ("contagem declarada como tal e honesta, contagem apresentada como km/h nao").

**`.dat` LISTHEAD** (`listhead_dat_file.py`). Container auto-descrito, nos de 32 B, o walk cobre **100,000% dos bytes em 25/25 arquivos**, sem regiao opaca. O tick de 100 us e **provado por dois caminhos que nao se falam**: o delta entre dois beacons da 1.475.649 ticks, e o canal `Running Lap Time` do mesmo arquivo declara maximo de 147,565 s. Refuta explicitamente a atribuicao anterior do KB: nao e WinDarab, nao existe a string `Darab` nem `Bosch` em byte nenhum.

**`.pid` validado contra o `.dat`** da mesma sessao, por dois leitores independentes: `Speed` correlaciona a +0,9998.

## 5. Motor A: a orquestracao

Quatro superficies de entrada, duas geracoes de contrato coexistindo.

| rota | limite | validacao de extensao |
|---|---|---|
| `POST /api/v1/sessions` (moderna) | 500 MB (`sessions.py:49`) | **nenhuma** |
| `POST /api/v1/sessions/preview` | 500 MB | so `_UNREADABLE_SUFFIXES` |
| `POST /lap-data` (legada) | nenhum | allowlist de 3: `.ld .csv .xrk` |
| `POST /upload-telemetry` (batch legado) | nenhum | mesma allowlist |

O limite efetivo e o **nginx em 200 MB**, menor que os 500 MB do engine. O BFF NestJS bufferiza em memoria com multer sem `limits.fileSize` e re-encapsula `Buffer` em `Blob` (`telemetry.controller.ts:81`), dobrando o pico: ~400 MB por upload concorrente.

**Tres listas de formato divergentes**: `main.py:104` diz 3 extensoes, `ingestion_service.py:274-296` roteia 9, `frontend/src/lib/telemetryFormats.ts:15-23` declara 7 mais `.ldx`. O arquivo do front diz por escrito que "a lista tem de espelhar o roteamento", e nada verifica isso. Efeito pratico: um `.vbo` ingere pela rota moderna e leva 400 da legada.

Pipeline pos-parse, na ordem (`ingestion_service.py:252-489`): fingerprint sha256 do byte cru **antes** de qualquer parse, roteamento, metadado do nome de arquivo preenchendo so o vazio, resolucao de pista, mapeamento de canal, resolucao de `lap_number` (beacon, queda de TIME, canal numerico ou inferencia por distancia), Savitzky-Golay em `brake`/`throttle` por volta, clip de aceleracao em +-30 m/s2, guarda de plausibilidade fisica, e **interpolacao de todo canal em `s_common = linspace(0, track.length_m, 2000)`**.

`saru-core` **nao e chamado na ingestao**. So aparece em `simulate.py`, `lts.py` e `lts_adapter.py`, que sao o caminho inverso (solver produz sessao sintetica).

Persistencia: **nada de telemetria vai pro Postgres**. O payload (2000 pts x N canais x N voltas) vira pickle no Redis com TTL de 1 h, mais MinIO opt-in por env. O Postgres recebe so metadado navegavel, gravado pelo BFF. O tempfile e apagado sempre; o byte original nao sobrevive, so o sha256.

Proveniencia de metadado, ordem de autoridade (documentada em `test_ingestion_metadata_provenance.py:16-20`):
1. O arquivo ganha do nome (`ingestion_service.py:298-307`, so preenche `if not bundle.metadata.get(key)`).
2. O nome do arquivo entrega **so o piloto**, e so da primeira posicao. O resto foi removido por bug medido: `vehicle = parts[1]` era o numero do carro ("8") virando `VehicleProfile(name="8")` e apagando massa/downforce/mu; `venue = parts[4]` era "a" e acendia `track_mismatch` em arquivo correto; a varredura de `file_path.parents` fazia todo upload de UI virar piloto `tmp` ou `var`.
3. A pista do arquivo ganha da pista do cliente. Motivo concreto: `demo_motec.ld` gravado em Barcelona analisado contra Interlagos narrava "Curva 1 (Senna)" numa volta que nao passa la.

Seguranca: `X-Internal-Key` entre BFF e engine, **fail-closed** (sem chave configurada responde 503, `api/security.py:31-32`). Ownership por `assertSessionAccess`, sem bypass de admin (ADR-0032). `test_no_arbitrary_file_reads.py` guarda duas coisas: que a rota `GET /video?path=` (que abria qualquer arquivo do container) foi removida, e um **guarda de padrao** que varre o OpenAPI e falha se qualquer rota declarar parametro `path`.

## 6. Motor B: como o PoC decide o formato

### 6.1 Tabela declarativa, nao cascata de codigo

`readers/formatos.py:55-211`. Treze formatos, cada um com assinatura literal, offset, marcador opcional, e **`amostras_medidas`**: quantos arquivos reais do acervo foram medidos pra fixar aquela assinatura. `detectar()` le so os primeiros **256 bytes**.

Ordem do algoritmo (`formatos.py:242-314`):
1. Arquivo vazio, sai com `confianca="nenhuma"`.
2. **Envelope zlib**: magic `78` + `{01,5e,9c,da}`, descomprime 64 bytes e testa o conteudo interno. So aceita se o interno for `aim_xrk`. Nunca aceita pelo envelope sozinho.
3. Varredura da tabela: assinatura no offset declarado, mais marcador obrigatorio quando existe.
4. **Regra de assinatura fraca**: `.ld` (`40 00 00 00`) e `.drk` (`RD`, 2 bytes) sao marcados FRACA e exigem que a extensao concorde; discordando, entram com `confianca="baixa"` e motivo escrito.
5. Familia conhecida sem formato, ou fallback final: `Deteccao(None, "nenhuma", "assinatura nao consta no catalogo")`.

**Nunca devolve default silencioso.** E a diferenca operacional mais importante contra o motor A.

O marcador existe por bug medido: `motec_ldx` exige `b"<LDXFile"` alem do prefixo XML porque sem ele um arquivo `.lic` virava `.ldx`.

### 6.2 Registry que se recusa a mentir

`readers/__init__.py:19-27`: `registrar()` levanta `ValueError` se o `formato_id` nao consta em `FORMATOS_POR_ID`, com a mensagem "Meca a assinatura de um arquivo real antes de registrar leitor". A coluna `formato_telemetria.leitor` do banco e **derivada** de `LEITORES` (`acervo.py:183`), nao declarada a mao. O comentario diz por que: a versao anterior declarava, e "o banco afirmou suporte nativo a tres formatos AiM que ninguem lia".

### 6.3 Contrato do leitor

`readers/base.py`, tres dataclasses frozen. `Lote.__post_init__` **levanta se a tabela nao tiver coluna `t_s`**: sem `t_s` nao ha corte de volta, entao a invariante e dura. Regra declarada em `base.py:17-20`: o leitor **nao interpreta semantica**, devolve nome bruto do fabricante e a unidade que o arquivo declara, mesmo errada. A traducao e a etapa 3.

`LeitorDeInventario` (`base.py:115-133`) e a base concreta dos leitores que catalogam canal mas nao leem amostra: `suporta_amostra = False`, `ler()` levanta com mensagem explicativa.

## 7. Motor B: os leitores, por profundidade

**Leem amostra (6):** `motec_ld`, `aim_xrk`, `protune_dlf`, `vbox_vbo`, `pi_pid`, `pi_listhead_dat`.
**Inventario de canal, sem amostra (2):** `pi_pds`, `asam_mf4`.
**Zero canais, so metadado/framing (4):** `motec_ldx`, `aim_drk`, `aim_gpk`, `aim_rrk`.
**Catalogado sem leitor (1):** `bosch_bmsbin`, 96 arquivos e 920 MB, o maior dataset do acervo.

### 7.1 `.xrk`: 1.411 linhas, Python puro, e uma divergencia provada contra a referencia

Decisao do Lucas: **sem `libxrk`**. Container de chunks ASCII simetricos, abertura de 12 B e fecho de 8 B com a tag repetida. Quatro tipos de registro de amostra (`S` escalar, `G` grupo com payload de tamanho somado, `M` rajada, `c` canal expandido em tres variantes).

O achado mais forte do repo inteiro esta aqui. Chunk `LAP` de 32 bytes: **a libxrk diz que o tempo cumulativo esta em +16; a medicao diz +28.** Nos 39 arquivos do acervo com dois ou mais `LAP` de 32 B em sequencia, a invariante `fim_n - fim_{n-1} == duracao_n` bate **39/39 com +28 e 0/39 com +16**. A causa foi rastreada: `_get_laps` da libxrk 0.13 nunca roda para corpo de 32 B, porque o handler anterior faz `struct.unpack('4xI8xI')`, que exige exatamente 20 B, levanta `struct.error` e cai na recuperacao "badbytes". E codigo morto na versao instalada.

Politica de anomalia: salto de numeracao de volta descarta **so aquele chunk** e conta em `bruto["lap_saltos_grandes"]`. A referencia abortaria o arquivo inteiro.

Limite honesto declarado: so canais de `bytes_amostra == 2` (int16) ou vistos em rajada `M` viram amostra. Canais de 4, 8, 12, 20, 32, 56 e 60 bytes **nao sao decodificados**, porque foi medido que um canal de 4 B gravava `float32` e nao `int32`, e nao ha como saber qual sem o chunk `CAL`. Marcado `DECISAO PENDENTE (Lucas)`.

### 7.2 `.pds`: 887 MB medidos do zero

Segundo maior volume do acervo, e **nunca existiu leitor no saru-app**. Unico formato com magic fora do offset 0 (offset 4; os 4 primeiros bytes sao um campo comprimento+conteudo com fragmento de caminho Windows da estacao que gravou).

O arquivo **grava do fim pro comeco** e nao ha ponteiro pro dicionario no cabecalho. O leitor le os ultimos 4 MB, varre de 2 em 2 bytes procurando registros de 552 B validados pelo **nome repetido em +88**, monta cadeias em passo aritmetico, e valida com a invariante `byte_offset[n] == byte_offset[n-1] + n_amostras[n-1] * 8`, que fechou em **100% dos registros consecutivos nos 25 arquivos decifraveis**. Guarda anti-ruido de 8 canais minimos porque um candidato de ruido com 1 ou 2 registros passa na invariante **por vacuidade**.

Divida declarada com numero: 10 arquivos usam registro de 304 B (layout diferente) e ao menos 9 tem varios dicionarios concatenados. Esses 19 levantam `ErroDeLeitura` em vez de devolver inventario errado.

### 7.3 `.mf4`: a taxa que a norma nao guarda

MDF4 nao guarda taxa de amostragem em lugar nenhum da arvore (`##HD`, `##DG`, `##CG`, `##CN`, todos medidos). Duas opcoes na mesa, marcadas `DECISAO PENDENTE (Lucas)`: (a) fazer duas leituras pontuais de 8 bytes no canal mestre, primeiro e ultimo registro, e derivar `(cycle_count - 1) / duracao`; (b) nunca tocar `##DT`, o que abriria **zero dos 5 arquivos**. Escolhida a (a).

**Divergencia doc x codigo encontrada aqui:** a docstring de `asam_mf4.py:44-68` descreve o comportamento de um metodo `ler()` que **nao existe** na classe. Documentacao adiantada ao codigo.

### 7.4 `.dlf`: a taxa que o arquivo tambem nao declara

Codificacao esparsa em texto: virgula e separador decimal, letra maiuscula e separador de campo **e** passo de avanco (`A`=1, `Z`=26, letra dupla soma 26 por letra). Primeira linha e keyframe, as seguintes so trazem canal que mudou.

A taxa nao esta declarada, entao e **derivada contando escritas reais por posicao** ao longo da varredura inteira, dividido pela duracao. Base global ~20 Hz, com canais de 0,13 Hz (`Engine Temperature`).

Vinte canais tem nome literal `"N/A"` mas sao 20 posicoes distintas com amostras proprias. O leitor sufixa com a posicao (`"N/A#7"`) so em quem repete. As alternativas (descartar, fundir) foram rejeitadas por escrito.

Atribuicao do fabricante **nao confirmada**: o saru-app rotula AiM, a ADR-0044 infere FuelTech, o Manual de Campo conclui Pro Tune TDL. E ha **1 unico arquivo** de amostra nesta maquina, contra os 81 que o Manual cita.

### 7.5 `.vbo`: o pareamento de unidade que o legado nunca acertou

`[channel units]` **nao e paralelo** a `[header]`: tem `1 + (n_colunas - idx_avisynctime - 1)` entradas, a primeira e do `sampleperiod`, e as demais casam com os canais **depois de `avisynctime`**. O leitor do saru-app tentava zip posicional, que nunca bate. Se a ancora faltar ou a contagem nao fechar, o motor B devolve `None` pra toda unidade e registra o motivo, em vez de atribuir unidade errada.

`t_s` deriva da coluna `time` (HHMMSS.sss) e **nao** acumula `Tsample`, porque somar 0,100 linha a linha acumula erro de ponto flutuante. Tem deteccao de virada de meia-noite pronta, embora nenhum arquivo do acervo cruze.

Encoding: os 9 arquivos decodificam em UTF-8 estrito. Latin-1 (o que o legado usava) produzia mojibake.

### 7.6 `.dat` e `.pid`: o porte que endureceu

Os dois foram portados do saru-app, e o porte trocou **degradacao silenciosa por erro duro** em varios pontos:

| situacao | motor A | motor B |
|---|---|---|
| `node_size` invalido no walk | `logger.warning` + `break` | `ErroDeLeitura` |
| `n_amostras` declarado > payload | warning + usa o menor | `ErroDeLeitura` |
| canais da mesma taxa com contagens diferentes | corte silencioso | `ErroDeLeitura` |
| `sum(rate * width) != block_size` no `.pid` | so logava | rejeita o arquivo |

E um ponto onde o motor B e mais **conservador** que o A: no `.dat`, os bytes em `CHANNEL_INFO+0x4A` que o motor A trata como faixa declarada sao na verdade a faixa **medida daquele arquivo** (`Steering` sai `(1.6618, 0.3910)` enquanto o `.pid` da mesma sessao declara `-100..100 mm`). O motor B deixa `valor_min`/`valor_max` como `None`, porque preencher "seria apresentar evidencia fabricada como faixa declarada".

## 8. Motor B: o pipeline

Sete etapas, cada uma com seu modulo. As que importam pro parsing:

**Etapa 1, recepcao** (`pipeline/recepcao.py`). Nao le amostra nenhuma, so hash sha256 em chunks de 1 MiB e rastreabilidade. Agrupa bundle por `(pasta, stem)`, que e como o AiM nomeia a captura. Escolhe o primario por `PRIORIDADE_PRIMARIO`, ordenada por riqueza de canal. Papel de cada arquivo: `primario`, `indice` (`.ldx`, `.drk`, `.rrk`), `gps` (`.gpk`), `backup` (`.bak` sempre). Dedupe pela chave natural sha256-do-primario, e reprocessar e caso normal, nao erro.

**Etapa 2, ingestao** (`pipeline/ingestao.py`). Formato sem leitor registrado **tambem vira linha** de `ingestao` com `status='falhou'` e a mensagem exata: "o silencio e que e o defeito". Metadado vai pro jsonb **prefixado pelo formato** (`motec_ld.venue_declarado`, `aim_xrk.lap_beacons_ms`), entao num bundle a divergencia entre irmaos fica visivel em vez de o ultimo vencer.

A resolucao de perfil (`ingestao.py:133-233`) e onde o motor B se separa mais claramente do `_SIM_HINTS` hardcoded do motor A: mede **sobreposicao de vocabulario** entre os nomes brutos do arquivo e as colunas do mapa no banco, exigindo cobertura minima de 25% **e** margem de 3 sobre o segundo colocado. Calibracao medida: `acc` sobre `.ld` da 39/55 com margem 38; ruido da 2/30 com margem 0. Sem essa guarda, 58 arquivos `.xrk` "venciam" para o perfil `protune`. **Nao resolver e resultado legitimo.**

O `on conflict` de `canal_gravado` usa `coalesce(excluded.canal_canonico_id, canal_gravado.canal_canonico_id)` porque reprocessar nao pode desaprender: sem isso, reingerir com perfil ambiguo sobrescrevia mapeamento correto por NULL, e "a temperatura de pneu de 2 gravacoes sumiu exatamente assim".

Status `"ok"` exige `suporta_amostra` **e** mapa resolvido; senao `"parcial"`. Inventario sem amostra e sucesso parcial por design.

**Storage** (`storage.py`). Um `ParquetWriter` aberto por taxa, zstd, sem acumular nada alem do lote corrente. Enderecamento por conteudo: `raiz/gravacao={id}/camada={bruta|canonica}/taxa={hz}/{sha256[:12]}.parquet`. Destino ja existente apaga o temporario, idempotencia de graca. Usa `shutil.move` e nao `Path.replace` porque em producao o temporario nasce no overlay do container e o destino esta em volume montado: `rename` falha com EXDEV, invisivel em dev.

**Etapa 5, corte de voltas** (`pipeline/corte_voltas.py`). Cascata literal de quatro degraus: canal contador/pulso, `.ldx`, `.xrk`, GPS. Ordena canais por **taxa decrescente**, porque foi medido que `Lap Number` do MoTeC mora em serie de 1 Hz em 51 gravacoes enquanto `LAP_BEACON` a 100 Hz descreve a mesma passagem. O degrau de GPS usa gate circular de 30 m **mais o sinal do rumo projetado**, entao passagem no contra-fluxo nao conta. N passagens dao N-1 voltas: out-lap e in-lap nao viram volta. Falhando os quatro, `corte.motivo` junta o que cada degrau tentou. **Nenhum caminho inventa volta.**

**Rota de upload** (`api.py:375-440`), `POST /api/gravacoes`, status **202**. Recepcao e sincrona (so hash e registro), o resto vai pra `BackgroundTasks`. Justificativa: o acervo tem `.ld` de 400 MB e `.bmsbin` de 920 MB, e ler mais normalizar mais escrever Parquet mais cortar estouraria qualquer timeout de proxy. Nao ha entidade de "job": o estado real mora na tabela `ingestao`, que e append-only. Ressalva declarada no proprio codigo: `BackgroundTasks` morre com o processo, e virar produto pede fila.

## 9. Sete diferencas de filosofia

1. **Detecao.** A: extensao, com um sniff. B: assinatura medida em N arquivos reais, com offset e marcador declarados numa tabela.
2. **Ausencia de match.** A: cai no CSV generico e depois no perfil `"acc"`, falhando como canal faltando. B: `confianca="nenhuma"` com motivo escrito, e a ingestao grava a falha.
3. **Buraco no dado.** A: `np.interp` ou zero-order hold, dependendo do canal. B: `NaN`, sempre, nunca repete o ultimo valor.
4. **Semantica.** A: o parser ja converte unidade e as vezes ja renomeia. B: o leitor entrega nome e unidade crus do fabricante, e a traducao e uma etapa separada com mapa versionado no banco.
5. **Escolha de perfil.** A: lista de hints hardcoded em Python, empate resolvido pelo `max()`. B: sobreposicao de vocabulario medida contra o banco, com piso de cobertura e margem, e "nao resolvi" como saida valida.
6. **Anomalia.** A: em geral degrada com WARNING e segue. B: em geral levanta, e onde degrada, registra o motivo em `bruto` pra ficar visivel no jsonb.
7. **Suporte declarado.** A: exportado em `__all__` (que nem esta sincronizado com o dispatch). B: derivado do registry, que por sua vez exige formato medido.

## 10. Achados que merecem acao

### Motor A

1. **`_discover_sidecars_and_media` nao tem `return`** (`ingestion_service.py:185-217`). Monta o dict e cai no fim da funcao, devolvendo `None`. O `if media_and_sidecars:` de `:310` e codigo morto. Sem cobertura de teste. Efeito pratico hoje e nulo (o path e sempre `/tmp`), mas o `iterdir()` roda em toda ingestao a toa.
2. **`NoLapBoundaryError` nao esta classificada em `sessions.py:146-170`.** E a excecao com a mensagem mais acionavel do sistema ("configure o beacon de volta no logger, ou envie um export ja cortado por volta") e cai no `except Exception` generico: o usuario le "Erro ao processar arquivo de telemetria."
3. **`ldparser.py:401-408`**: leitura truncada de canal e capturada e engolida (o `raise v` esta comentado). O DataFrame sai com dado parcial, sem sinal a jusante.
4. **`ld_file.py:246-249`**: o log diz "fallback 100 Hz" e o codigo usa `60.0`.
5. **`xlsm_file.py:87`**: `np.linspace(0, n*0.1, n)` da passo `0.1*n/(n-1)`, nao 0,1 s. O eixo sintetico sai esticado. E o parser nem esta roteado.
6. **`dlf_file.py:234-237`**: a docstring afirma que o formato esparso nao e decodificado; `_decode_sparse_body` decodifica desde a linha 107. Documentacao obsoleta.
7. **`pid_file.py` e `listhead_dat_file.py` leem `unit` por canal e nunca populam `raw_units`** no bundle. Informacao disponivel e descartada.
8. **Rotas legadas sem ownership**: `POST /telemetry/upload`, `POST /telemetry/lap-data` e `POST /gt7/laps/:id/analyze` passam pelo JWT mas nao registram dono nem historico. O `SaImportView` cai em `getLapData` como fallback, entao esse caminho e alcancado em producao.
9. **A suite de teste tem dois modos e nao avisa qual esta rodando.** So tres arquivos reais existem na arvore (`data/samples/gt7_*.ld`). MoTeC Porsche MPES, AiM Copa Truck, kart de Guara, os 81 `.DLF`: todos declarados e **ausentes**, com `pytest.skip` silencioso. Em CI, ~80% de `test_real_acervo_ingestion.py` e verde por skip. Nao ha teste que falhe quando o acervo esperado esta inteiramente ausente. O proprio cabecalho do arquivo articula o risco: "fixture inventada nao prova nada sobre o arquivo que o cliente tem, so que o autor do teste e o autor do parser combinaram a mesma suposicao".
10. **`test_dlf_de_export_continua_recusando_corpo_vazio`** usa `inspect.getsource` + `assert "UnsupportedDlfVariantError" in fonte`. E um grep vestido de teste.

### Motor B

1. **`asam_mf4.py:44-68` documenta um `ler()` que nao existe.** A classe nao sobrescreve `suporta_amostra`, entao herda `False`.
2. **`formatos.py:288` tem um `if True:` vestigial.**
3. **A regra de assinatura fraca e uma busca de substring em portugues**: `fraca = "FRACA" in fmt.nota` (`formatos.py:289`). Funciona, mas acopla comportamento a texto de comentario.
4. **Vocabulario por nome bruto no corte de voltas** (`corte_voltas.py:84-88`), reconhecido no proprio codigo como divida: o certo e o canal virar canonico e passar pelo mapa. Um `Lap Number` do acervo vai de 28 a 2572 com 136 transicoes em 640 s, mesmo nome e semantica completamente diferente.
5. **`BackgroundTasks` morre com o processo** (`api.py:395-397`), ja reconhecido, fila decidida (Redis) e nao implementada.

## 11. Oito `DECISAO PENDENTE (Lucas)` abertos no motor B

| local | assunto |
|---|---|
| `readers/xrk.py:152` | decodificar canais de 4, 8, 12, 20, 32, 56 e 60 bytes exige mapear tipo por largura ou abrir o chunk `CAL` |
| `readers/xrk.py:160` | o timestamp de cada amostra de rajada `M` e **inferido** (`ts_ms + i*periodo`), nenhum campo declara isso |
| `readers/dlf.py:125` | a notacao do sufixo de desambiguacao (`"N/A#7"`) e convencao desta PoC |
| `readers/dlf.py:331` | forma de expor a grade esparsa como `Lote`: (a) implementado, (b) e (c) na mesa |
| `readers/vbo.py:351` | fallback de `t_s` quando a coluna `time` falha numa linha |
| `readers/pi_pid.py:399` | `nome_bruto` duplicado no acervo F3 (dois "Oil Temp") produz duas colunas do mesmo nome no `Lote` |
| `readers/asam_mf4.py:22` | tocar ou nao o `##DT` pra provar a taxa; opcao (a) escolhida |
| `readers/asam_mf4.py:49` | 1.130 a 1.185 colunas por `Lote` (moot enquanto `ler()` nao existir) |

## 12. Onde estao os buracos de cobertura

| formato | arquivos no acervo | estado |
|---|---|---|
| `bosch_bmsbin` | 96 (920 MB) | catalogado, **sem leitor nenhum** |
| `pi_pds` | 47 (887 MB) | 25 lem inventario, **19 rejeitados** (10 de layout 304 B, 9+ com dicionarios concatenados) |
| `pi_listhead_dat` | 37 `.dat` | **25 lidos**, 12 sao familia distinta em `NAO_IDENTIFICADO` |
| `aim_drk` / `.bak` | 129 | 125 com metadado (97%), 4 da outra variante genuinamente vazios |
| `aim_gpk` + `aim_rrk` | 135 | so framing, **zero canais**, semantica do payload nao confirmada |
| `protune_dlf` | 1 nesta maquina (81 citados no Manual) | le, mas o fabricante e a confirmar |
| `asam_mf4` | 5 | inventario, `ler()` nao escrito |
