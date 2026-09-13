---
titulo: "Acervo Porsche Cup no HD externo, o modelo de coleta que a plataforma não tem"
data: "2026-08-16"
origem: "_arquivo/saru-app/docs/research/2026-08-16-acervo-porsche-cup-modelo-de-coleta.md"
status: "vigente"
area: "processo"
---

# Acervo Porsche Cup no HD externo, o modelo de coleta que a plataforma não tem

> Levantamento do HD `/media/hd_externo` (TOSHIBA, 1,8 T) a pedido do operador, 2026-08-16.
> **Documento de PESQUISA, não decide nem implementa nada.** O que ele faz é registrar o
> que existe de material real de campeonato e o que isso diz sobre o modelo de coleta.
> Decisões viram ADR.

## Por que isto existe

A plataforma tem uma pergunta aberta: **como o piloto se organiza num dia de evento**, e
quanto de coleta é obrigatório em cada modalidade (campeonato organizado · track day ·
simulador/kart). A sobreposição `RunSheet` × `OutingSheet` (dívida da Zona 3) é sintoma de
não existir esse modelo.

Em vez de especular, fomos ao material real: o HD tem o acervo de trabalho de um engenheiro
da **Porsche Carrera Cup Brasil**, incluindo etapa completa com cronograma, briefing,
regulamento e a planilha de um carro que correu.

## Onde está o material

Todos os caminhos relativos a `/media/hd_externo`.

| o quê | caminho |
|---|---|
| **Etapa completa** (cronograma, briefing, mapas, setups, referências, report final, template) | `04_Archive/04_Motorsport_Hub/PORSCHE CUP 2026/Data Analysis/DOCUMENTOS_ETAPA/` |
| **Planilha de trabalho de um carro** (18 abas, dados reais da 8ª etapa) | `02_Data_Lake_Motorsport/.../Porsche_Cup_2026/Geral/992#3 - Franco Giaffone (…).xlsm` |
| **Template oficial de Pi Toolbox** do campeonato, v18, cobrindo 992 / 991.2 / 991.1 | `.../DOCUMENTOS_ETAPA/Template/ENG220813_V18_RIM_Template Porsche Cup Brasil_992_991.2_991.1.pwb` |
| **Referências por modelo de carro** (`.pds`) | `.../DOCUMENTOS_ETAPA/Referências/{3.8 - 991.1, 4.0 - 991.2, 992.1}/` |
| **Dicionário de canais Porsche** | `.../Apostilas e Documentos/Manuais/Porsche Channels - Mj'E v2.pdf` |
| **Informativo de alarmes** para pilotos | `.../Manuais/ENG220308_V9_PEA_Informativo_de_Alarmes_e_Embragem_para_Pilotos.pdf` |
| Regulamentos | `.../Apostilas e Documentos/Regulamentos/Campeonatos/` |
| **Workbooks MoTeC por domínio** (`Base`, `Brakes`, `Driver`, `Engine`) | `03_RESOURCES/03_Data_Lake/Motorsport/MoTeC_Workbooks/` |
| Calculadora de pressão de pneu | `.../Logs/F. Giaffone Logs/Tire Pressure Calculator (…).xlsx` |
| Material OptimumG (transferência de carga, damper, K&C) | `.../PORSCHE CUP 2026/Information_for_OptimumG_SP_Adv_VDseminar/` |

> ⚠️ `02_AREAS_ASSETS/` do HD é marcado como sensível no `CLAUDE.md` da raiz do disco, > não foi acessado.

## 1. A cadeia real: Etapa → Sessão → Outing → Volta

Fonte: nomes das abas do workbook + a aba `DATABASE`.

As seis abas de trabalho do carro #255 são `CUP#255TE1Out1`, `TE1Out2`, `Q1Out1`, `Q2Out1`,
`R1Out1`, `R2Out1`. O nome **é** o modelo: campeonato · carro · tipo+número da sessão · qual
saída. O treino livre teve duas saídas; a corrida teve uma.

A aba `DATABASE` achata isso numa linha por volta, com **três numerações simultâneas**:

| coluna | significa |
|---|---|
| `LAPS_SEQ` | volta sequencial no evento inteiro |
| `OUTING` | a que saída pertence |
| `LAPS_OUT` | volta **dentro** daquela saída |

A plataforma hoje guarda `laps` como **contagem digitada** na `RunRecord`, não tem a tripla,
nem o grão de uma linha por volta no domínio de coleta.

## 2. O cronograma diz o que é uma "sessão"

Fonte: `Horários/PER230217_V6_VIQ_Cronograma Etapa 1 - Interlagos - PILOTOS.pdf`
(Etapa 1, Interlagos, 2 a 5 de março de 2023, **quatro dias**).

Cada linha do cronograma tem exatamente: **Início · Fim · Duração · Intervalo · Evento ·
Classe**. Três coisas que isso ensina:

**(a) Sessão é typed e tem janela.** Os tipos que aparecem: Pré-temporada (S1/S2/S3), Treino
opcional, Shake Down, Treino livre, Sessão/Practice, Classificação, Corrida. Mais os que não
são pista: Briefing, Briefing técnico, Almoço, Ação Porsche, Visitação de boxes, Montagens
técnicas e TV.

**(b) A classificação é dividida POR CATEGORIA.** Não é rótulo de resultado, é sessão
separada:

```
16:30-16:42  Classificação (Rookie)                    CARRERA CUP (992)
16:45-16:57  Classificação (Carrera + Carrera Sport)   CARRERA CUP (992)
17:02-17:12  Classificação, TOP 10                    CARRERA CUP (992)
```

Ou seja: **a categoria do piloto determina de qual sessão ele participa**, não só como ele é
classificado depois. (Categorias em `LISTAS` do workbook: ROOKIE · SPORT · CHALLENGE.)

**(c) Corrida é limitada por TEMPO, não por voltas.** `Corrida 1, 25 min + 1 volta`. A
plataforma modela volta como unidade e não tem o conceito de sessão cronometrada.

**(d) Um evento hospeda campeonatos diferentes ao mesmo tempo.** CARRERA CUP (992), SPRINT
CHALLENGE (991.2) e SPRINT TROPHY (991.1) correm no mesmo fim de semana, com sessões próprias
intercaladas.

## 3. Dois pesos de ficha no MESMO campeonato

Este é o achado que muda o desenho proposto de "seletor de modalidade global".

| ficha | onde | o que coleta |
|---|---|---|
| **pesada** | abas `TE`/`Q`/`R` + `Out` | 46 linhas: tempo por volta, velocidade por roda, `vitals_*` (pressão de óleo/água/combustível, temperatura de motor/óleo/câmbio), TPMS por canto com mín **e** máx, balanço de freio, offsets de acelerômetro, hodômetro |
| **leve** | aba `Folha de tempo`, *"Ficha de Clínicas e Treinos Opcionais"* | piloto · carona · tempo na pista · nº de voltas. Cabeçalho: chassis, carro, piloto, data, etapa |

**O peso da coleta é propriedade da SESSÃO, não do dia.** Um mesmo sábado de Porsche Cup tem
classificatório (pesado, obrigatório) e clínica opcional (leve). Um seletor global entre
`/login` e `/home` obrigaria a trocar de modo no meio do fim de semana, ou mentiria sobre
metade dele.

> **Decisão do operador 2026-08-16:** a clínica com carona é peculiaridade da Porsche Cup, > "sessão com passageiro" **não** entra no modelo como conceito de primeira classe.

## 4. Agregação é dado, não escolha de widget

Na ficha real, cada canal declara a própria agregação numa coluna dedicada (`max`, `min`,
`mean`, `end`, `diff`). `vitals_toil` aparece **duas vezes**, uma linha `max`, outra `min`.
`brake_bias_driver` aparece como `end` e como `diff`, porque o que interessa nele é o valor
final e **a mudança feita pelo piloto durante a saída**.

O engenheiro não escolhe no menu: a ficha já sabe que temperatura de óleo se lê pelo pico e
bias de freio se lê pela variação. Na plataforma, agregação é configuração de widget.

## 5. Out lap e in lap são papéis, não defeitos

A ficha escreve `0 (Out Lap)` e `17 (In Lap)` na linha de número da volta. A plataforma marca
`is_valid: false`, o que descarta a informação de **por que** a volta não vale, e é
justamente essa informação que o piloto precisa para entender o próprio stint.

## 6. A referência é externa e curada

`DOCUMENTOS_ETAPA/Referências/` guarda um arquivo por **modelo de carro**, nomeado pela etapa
de origem:

```
Referências/3.8 - 991.1/REF 3.8 - 22ET3.pds
Referências/4.0 - 991.2/REF 991.2.pds
Referências/992.1/
```

E o `Report SPRINT` do workbook declara o alvo: *"dados referentes à melhor volta do treino
classificatório **do piloto que somou mais pontos na etapa**"*. Não é a melhor volta do
próprio piloto, é um benchmark externo, curado, versionado por modelo e por etapa.

> **Correção de registro:** a plataforma **já tem o mecanismo**, `ActiveReference` suporta
> `stintLap` ("uma volta qualquer de qualquer log carregado, da bateria ou do acervo"). O que
> falta não é referenciar outro piloto, é a **semântica de benchmark**: marcar um arquivo como
> "a referência daquele modelo/etapa" em vez de depender de alguém escolher no seletor.
> `.pds` já está no contrato de formatos (`shared/proto/telemetry-formats.json`).

## 7. Jogo de pneu

O `Report SPRINT` rastreia, por canto (DE/DD/TD/TE), o **número do jogo** e as **voltas
naquele jogo**:

```
Pneus Slick
Set     23  22  23  22
Voltas  12  11  12  12
Set     27  27  27  27
Voltas   9   9   9   9
```

A `RunRecord` não tem onde guardar. Busca no BFF por `tyre_set` retorna zero arquivos.

> **Decisão do operador 2026-08-16:** jogo de pneu **é fundamental e já era para estar
> dentro**, serve tanto controle de estoque quanto performance/degradação.

## 8. Os workbooks MoTeC já são "lentes"

`MoTeC_Workbooks/` tem `Base.i2wkb`, `Brakes.i2wkb`, `Driver.i2wkb`, `Engine.i2wkb`, análise
separada por domínio, que é exatamente a ideia dos presets de lente do SA
(`race-engineer`, `vehicle-dynamics`, `driver-coach`, `tyre-engineer`). Convergência
independente: vale comparar o conteúdo dos `.i2wkb` com os presets antes de evoluí-los.

## Lacunas medidas contra o modelo atual

Comparação contra `RunRecord` (`services/frontend/src/lib/api.ts:188`) e varredura de
`services/api/src/events/`.

| conceito real | na plataforma | estado |
|---|---|---|
| Saída como unidade | `RunRecord` + `OutingSheet` | existe |
| Pressão fria e quente por canto | `tyre_press_cold` / `_hot` | existe |
| Condições congeladas na saída | `track_temp_c` · `air_temp_c` · `weather` | existe |
| Referenciar volta de outro arquivo | `ActiveReference.stintLap` | existe |
| **Tipo de sessão** (treino/quali/corrida/clínica) |, | **não existe** |
| **Sessão limitada por tempo** ("25 min + 1 volta") |, | **não existe** |
| **Jogo de pneu + voltas no jogo** |, | **não existe** |
| **Categoria do piloto** (Rookie/Sport/Challenge) |, | **não existe** |
| **Benchmark curado** (referência da etapa/modelo) | seletor manual | **falta a semântica** |
| Volta dentro da saída (`LAPS_OUT`) | `laps` (só a contagem) | parcial |
| Out lap / in lap como papel | `is_valid` booleano | parcial |
| Agregação declarada por canal | escolha de widget | parcial |

## Direção proposta (não decidida)

Dois níveis, em vez de um seletor global:

- **O evento declara a disciplina**, campeonato organizado · track day · simulador/kart.
  Define obrigatoriedade e defaults.
- **A sessão declara o tipo**, treino, classificatório, corrida, clínica, teste. É o tipo que
  decide o peso da ficha.

Consequência: `RunSheet` e `OutingSheet` deixam de ser telas concorrentes e viram **a ficha
leve e a ficha pesada**, cada uma ligada a um tipo de sessão. A dívida da Zona 3 se resolve
pela raiz, não por negociação de campo.

Sobre importação: no fluxo real o dado entra **por sessão**, não por "importação". Se a sessão
é a coisa que existe, o arquivo é anexo dela, e o Analyzer deixa de ser destino para virar o
que se faz *com* uma sessão que já existe.

## O que ainda não foi lido

> **Atualização 2026-08-16:** os três primeiros itens desta lista, mais o `Manual de Pista -
> Engenheiros` V19, do qual só o sumário tinha sido lido, foram lidos e registrados em
> [`2026-08-16-regulamento-e-manual-porsche-cup.md`](2026-08-16-regulamento-e-manual-porsche-cup.md).
> As pendências que restam estão listadas ao fim daquele documento; o `.pwb` e os `.i2wkb`
> continuam abertos por exigirem software proprietário.

- ~~Regulamentos (`Apostilas e Documentos/Regulamentos/Campeonatos/`)~~, **lido**; define
  formalmente `SESSÕES EXTRAS` × `SESSÕES OFICIAIS`, cota de pneu e as categorias.
- ~~`Porsche Channels - Mj'E v2.pdf`~~, **lido**; ~130 canais com unidade e taxa.
- ~~Informativo de alarmes~~, **lido**; prioridade, limiar e ação do piloto por modelo.
- Template `.pwb` do Pi Toolbox (v18), precisa do Pi Toolbox para abrir; conteúdo desconhecido.
- Conteúdo dos `.i2wkb` do MoTeC contra os presets de lente do SA.
