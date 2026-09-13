---
titulo: "Regulamento e manual da Porsche Cup, o que é obrigatório registrar"
data: "2026-08-16"
origem: "_arquivo/saru-app/docs/research/2026-08-16-regulamento-e-manual-porsche-cup.md"
status: "vigente"
area: "processo"
---

# Regulamento e manual da Porsche Cup, o que é obrigatório registrar

> Fecha a seção *"O que ainda não foi lido"* de
> [`2026-08-16-acervo-porsche-cup-modelo-de-coleta.md`](2026-08-16-acervo-porsche-cup-modelo-de-coleta.md).
> **Documento de PESQUISA, não decide nem implementa nada.** Registra o que os documentos
> oficiais dizem, com origem por bloco. Decisões viram ADR.

## Por que isto existe

O levantamento anterior inferiu o modelo de coleta a partir de **artefatos de trabalho**
(planilha de um carro, cronograma de uma etapa, pastas de referência). Inferência de
artefato é sujeita a viés: o que se vê é o que aquele engenheiro fez, não o que a categoria
exige. Este documento vai à **fonte normativa**, regulamento e manual, para separar
*"assim se faz"* de *"assim é obrigatório"*.

O resultado principal: quase tudo que o doc anterior inferiu do workbook está **escrito no
regulamento**, às vezes com mais rigor do que a inferência sugeria. Um achado inverte a
leitura anterior (§3) e um conflito entre dois documentos oficiais ficou em aberto (§9).

## Convenção

- **MEDIDO**, está escrito no PDF citado, na página citada. Transcrito ou parafraseado.
- **SUPOSTO**, leitura minha ligando dois trechos ou o documento ao produto. Falsificável.
- Onde o PDF não diz, está escrito **que ele não diz**. Nada foi completado por plausibilidade.

## Corpus lido

Todos os caminhos relativos a
`/media/hd_externo/04_Archive/04_Motorsport_Hub/PORSCHE CUP 2026/Data Analysis/DOCUMENTOS_ETAPA/Apostilas e Documentos/`.
O HD foi acessado **somente para leitura**.

| # | documento | páginas | data do documento |
|---|---|---|---|
| **R1** | `Regulamentos/Campeonatos/SPRINT/porsche_carrera_cup_brasil_regulamento_tecnico_e_desportivo_2022.pdf` | 44 | Rio, 30/03/2022 (p.35 e p.44) |
| **R1a** | `.../SPRINT/porsche-carrera-cup-brasil-regulamento-tecnico-e-desportivo-2022-adendo-1-.pdf` | 2 | Rio, 06/06/2022 (p.2) |
| **R2** | `.../SPRINT/porsche_sprint_challenge_brasil_regulamento_tecnico_e_desportivo.pdf` | 44 | Rio, 25/03/2022 (p.35 e p.44) |
| **R2a** | `.../SPRINT/porsche-sprint-challenge-brasil-regulamento-tecnico-e-desportivo-2022-adendo-1-.pdf` | 2 | Rio, 06/06/2022 (p.2) |
| **R3** | `.../ENDURANCE/porsche-c6-bank-endurance-challenge-2022-regulamento-desportivo-e-tecnico-.pdf` | 56 | Rio, 22/07/2022 (p.49 e p.55) |
| **R3a** | `.../ENDURANCE/porsche-c6-bank-endurance-challenge-2022-adendo-1-ao-regulamento-desportivo-.pdf` | 4 | Rio, 09/08/2022 (p.4) |
| **M** | `Manuais/Lidos/ENG230529_V19_HEG_Manual de Pista - Engenheiros.pdf` | 67 | V19, 29/05/2023 |
| **C** | `Manuais/Porsche Channels - Mj'E v2.pdf` | 5 | Cosworth, rev. 23/08/2013 |
| **A** | `Manuais/ENG220308_V9_PEA_Informativo_de_Alarmes_e_Embragem_para_Pilotos.pdf` | 21 | V9, fev/2022 |

> ⚠️ **Descompasso de safra (MEDIDO).** Os regulamentos são da **temporada 2022**; o manual do
> engenheiro é **V19, de 2023**; o dicionário de canais é de **2013**. A pasta se chama
> "PORSCHE CUP 2026". Todo número deste documento é da safra citada, não vale como
> regulamento vigente sem reconferir. Onde 2022 e 2023 se cruzam, o cruzamento está marcado.

---

## 1. A sessão é *typed* pelo próprio regulamento

**MEDIDO, R1 p.17, Artigo 58** (texto idêntico em R2 p.17):

> i. SESSÕES EXTRAS são: Clínica de Pilotagem, Treinos Opcionais e Treinos Pré Temporada.
> ii. SESSÕES OFICIAIS são: Treinos Livres, Treino de Classificação e Corridas.

Este é o achado mais forte do corpus. O doc anterior **inferiu** de duas planilhas que existem
"duas fichas de peso diferente". O regulamento **define formalmente as duas classes de sessão**,
por nome, num artigo numerado, e as usa como sujeito de dezenas de outros artigos ("Nas
SESSÕES EXTRAS e nas SESSÕES OFICIAIS…", R1 Art. 59, 63, 67).

**SUPOSTO.** Peso da coleta não é convenção de engenheiro: é consequência da classe regulatória
da sessão. Um modelo de dados que não tenha o tipo de sessão como campo de primeira classe não
consegue expressar nem a regra de pneu (§4), que é escrita *em cima* dessa distinção.

Complemento **MEDIDO, M p.42**: o manual define os códigos usados no nome de arquivo de volta:

```
CP, Clínica de Pilotagem      TO, Treino Opcional
TL, Treino Livre              TE, Treino Extra
Q, Treino Classificatório    W, Warmup
Grid, Formação de Grid        R, Corrida
Shakedown
```

São **nove** códigos, contra os dois tipos regulatórios do Art. 58 e contra os seis prefixos de
aba vistos no workbook (`TE`, `Q1`, `Q2`, `R1`, `R2`). **SUPOSTO:** o vocabulário operacional é
mais rico que o regulatório; o modelo precisa dos dois níveis (classe regulatória + tipo
operacional), não de um enum único.

## 2. Formato de sessão, as durações

**MEDIDO, R1 p.25, Artigo 101** (idêntico em R2 p.25):

| sessão | duração |
|---|---|
| Treinos opcionais | "determinado no regulamento particular de cada Etapa" |
| Treino oficial (treino livre) | 1 (um) de **45 minutos** |
| Classificação C1 | **15 minutos**, todos os carros juntos |
| Classificação C2 | **10 minutos**, somente os dez primeiros do C1 |
| Corridas | **2 corridas de 25 minutos + 1 volta**, cada |

**MEDIDO, R1 p.25, Art. 101, Único:** bandeira vermelha no classificatório permite ao Diretor
de Provas acrescentar **até 5 minutos** ao tempo total. R1 p.27 Art. 108 repete o mesmo teto de
5 minutos para interrupção de qualquer sessão do classificatório.

**Cruzamento MEDIDO.** O doc anterior leu "Corrida 1, 25 min + 1 volta" no cronograma da
**Etapa 1 de 2023**. O regulamento de **2022** já dizia o mesmo (R1 p.25). Duas fontes
independentes, duas temporadas, a sessão limitada por tempo é estrutural, não peculiaridade de
uma etapa.

**MEDIDO, R1 p.26-27, Artigo 105:** existem **três formatos de classificação** numa mesma
temporada, e o regulamento diz qual etapa usa qual (Art. 105.4: Etapas 1-4 convencional, Etapa 5
etapas finais, Etapa 6 finais ou Preliminar do GP Brasil de F1):

- **105.1 convencional**, C1 (15 min, todos) + C2 (10 min, top-10). C1+C2 formam o grid da
  Corrida 1. A Corrida 2 larga pelo resultado da Corrida 1 **com inversão dos 6, 7 ou 8
  primeiros, definida em sorteio ao término da Corrida 1**.
- **105.2 etapas finais**, C1 e C2 sem ligação; C1 forma o grid da Corrida 1, C2 o da Corrida 2.
  Sem inversão.
- **105.3 Preliminar do GP Brasil de F1**, um único classificatório de **30 minutos**, onde a
  **1ª melhor volta** de cada competidor forma o grid da Corrida 2 e a **2ª melhor volta** forma
  o grid da Corrida 1.

**SUPOSTO.** O formato 105.3 é o caso que quebra qualquer modelo que trate "melhor volta" como
escalar único por sessão: aqui a **segunda** melhor volta tem valor desportivo próprio. Ranking
de voltas dentro de uma sessão precisa ser ordenável e endereçável por posição, não só por
máximo.

## 3. Categoria, três mecanismos diferentes, mesmo nome

Aqui a leitura anterior precisa de correção. O doc anterior registrou "Categorias em `LISTAS`
do workbook: ROOKIE · SPORT · CHALLENGE" e concluiu que "a categoria do piloto determina de
qual sessão ele participa". A parte da sessão continua de pé. Mas **"categoria" não é um
conceito só**, são três mecanismos distintos, e só um deles é atributo do piloto.

### (a) Sprint, atributo do piloto, por **histórico de carreira**, definido por exclusão

**MEDIDO, R1 p.7-9, Artigo 21.** Dentro do Campeonato Porsche Carrera Cup Brasil existem dois
sub-campeonatos: **SPORT** e **ROOKIE**. Ambos são definidos por **critérios de veto**, não de
admissão:

- **SPORT**, *não* pode ser disputado por quem: competiu na Carrera Cup (4.0 e 3.8) em 2021,
  2020, 2019 ou 2018; é piloto profissional "em atividade" em Stock Car, Stock Car Light, F3, F4
  ou categorias internacionais reconhecidas pela FIA (exceto classificado "Bronze" no ranking
  FIA); está "em atividade" em outras Porsche Carrera Cup pelo mundo; tem **menos de 24 anos**,
  vem do kart sem histórico de automóvel e tem 3+ anos de kartismo nacional/internacional; ou
  por critério do promotor, se apresentar nível de performance diferente dos demais.
- **ROOKIE**, reservado a quem vem da Porsche GT3 Cup **ou tem 50 anos ou mais**; vetado por
  qualquer critério do SPORT e por ter competido na Carrera Cup "SPORT" em 2020/2019 sem ter 50+.

**MEDIDO, R1 p.7-8, Art. 21.II.b.i-ii**, duas definições operacionais que valem citar porque são
computáveis:

> "Fora de atividade" são COMPETIDORES que participaram de no máximo 2 provas por ano, nos
> últimos dois anos.

> Considera-se "uma temporada" caso o COMPETIDOR se inscreveu em 50% ou mais das Etapas do
> Campeonato em questão. […] Duas "meias temporadas" são iguais a "uma temporada".

**MEDIDO, R1 p.8-9, Art. 21.1:** ROOKIE **não** participa do campeonato SPORT, mesmo terminando
entre competidores SPORT, não sobe ao pódio SPORT nem pontua nele. E **Art. 21.2:** todos são
PCCB; só alguns são também SPORT e/ou ROOKIE. **Art. 109 (p.27):** para sorteio de grid não
existe distinção entre PCCB, SPORT e ROOKIE.

**MEDIDO, R2 p.7-8, Artigo 21 (Sprint Challenge):** mesma estrutura, três diferenças de valor, o sub-campeonato ROOKIE é *"ou somente «TROPHY»"* (o próprio artigo usa os dois nomes); o corte
etário é **60 anos ou mais** (não 50); e *"A PSCB, TROPHY participará das Etapas 1, 2, 3 e 4 com
potência diminuída"*.

### (b) Endurance, atributo da **EQUIPE**, derivado do rating B.O.P. de um piloto

**MEDIDO, R3 p.19-20, Artigo 50.** Duas Classes: **CARRERA** (carros 992) e **CHALLENGE**
(carros 991.2). Cada uma com duas subclasses:

| subclasse | definição literal |
|---|---|
| CARRERA SPORT | EQUIPES com carro 992 que possuam **um piloto de classificação BOP "BRONZE"** |
| CARRERA ROOKIE | EQUIPES com carro 992 que possuam **um piloto de classificação BOP "COBRE"** |
| CHALLENGE SPORT | EQUIPES com carro 991/2 com **ao menos um piloto BOP "BRONZE"** |
| CHALLENGE ROOKIE | EQUIPES com carro 991/2 com **um piloto BOP "COBRE"** |

Ou seja: no Sprint a categoria é do **piloto** e vem do currículo; no Endurance é da **equipe** e
vem do rating do piloto mais fraco que ela carrega. Mesmos rótulos, semânticas incompatíveis.

**MEDIDO, R3 p.20, Art. 50.1 e 50.2:** as regras de herança entre classe e subclasse **diferem
entre CARRERA e CHALLENGE**, na CARRERA, ROOKIE não participa de SPORT; na CHALLENGE, ROOKIE
*também* participa de SPORT.

### (c) O rating B.O.P. do piloto, a escala que liga os dois

**MEDIDO, R3 p.44-45, Artigo 159.10, "Tabela de classificação B.O.P":**

| classif. B.O.P. | CARRERA | CHALLENGE | quem entra (resumo do texto) |
|---|---|---|---|
| **Platina** | 60 kg | 60 kg | profissionais de Stock Car Pro/Series ou internacionais de nível profissional (lista literal: F1, FIA WEC, F-E, F2/GP2, F3, F3 EURO, V8 Supercars, Porsche Supercup, DTM, Blancpain GT, IMSA SCC, IRL, Road to Indy); "Titânio" na GT3 Cup Endurance 2018/2019 |
| **Ouro** | 35 kg | 35 kg | Platina fora de atividade; Platina com 55+; pilotos de Porsche Carrera Cup (Sprint) em 2020/2021/2022; "PRO" de outros campeonatos |
| **Prata** | 10 kg | 10 kg | Porsche GT3 Cup (Sprint) 2020/2021 ou "Challenge" 2021 competindo na CHALLENGE; Carrera Cup "Sport"/"Rookie" competindo na CHALLENGE; Platina com 60+; Ouro com 55+ ou fora de atividade |
| **Bronze** | −10 kg | −10 kg | **Carrera Cup Sport e Sprint Challenge Sport, temporada 2022**; Ouro com 60+; Prata fora de atividade ou com 55+; "gentleman drivers"/"AM" de outros campeonatos |
| **Cobre** | −20 kg | −20 kg | **Carrera Cup Rookie e Sprint Challenge Rookie, temporada 2022**; pilotos iniciantes sem experiência |

**MEDIDO, e é o ponto:** as linhas Bronze e Cobre citam **nominalmente as categorias do Sprint**.
A categoria do piloto no Sprint é a entrada que produz o rating dele no Endurance, que por sua
vez produz a subclasse da equipe. É uma cadeia formal, cross-campeonato, versionada por
temporada.

**MEDIDO, R3 p.40, Art. 157:** o rating tem consequência de elegibilidade: não se admite equipe
cujo B.O.P. somado passe de **48 kg** (CARRERA) ou **35 kg** (CHALLENGE); e não se admite trio com
dois Platina no mesmo carro na CARRERA, mesmo que a soma feche.

**MEDIDO, R3 p.30, Art. 112-113:** no Endurance a categoria decide **quem pilota qual sessão**,
com a mesma força que o doc anterior observou no cronograma: a **primeira** classificação é
feita pelo competidor de **menor** B.O.P. da equipe e a **segunda** pelo de **maior**. O grid sai
da **média** das melhores voltas dos dois:

> Melhor tempo piloto A: 1:41,500 · Melhor tempo piloto B: 1:40,200
> Tempo consolidado da Equipe: 1:40,850 = ((1:41,500 + 1:40,200) /2)

## 4. Jogo de pneu, Sprint

O doc anterior registrou que o `Report SPRINT` rastreia número do jogo e voltas no jogo por
canto, e o operador decidiu que jogo de pneu "é fundamental e já era para estar dentro". O
regulamento mostra **por que**: o jogo de pneu é uma conta corrente com saldo, herança entre
etapas e punição em posição de grid.

**MEDIDO, R1 p.18, Artigos 60-62** (idêntico em R2 p.18):

| regra | valor |
|---|---|
| Jogos de slick **novos** por etapa | **3** (Art. 60) |
| Jogos de slick carregados para a etapa seguinte | **3** (Art. 61) |
| Condição para carregar | "Somente poderão ser carregados pneus **comprovadamente usados (com mais de uma volta de uso)**" (Art. 61) |
| Pneus não utilizados | **não podem ser carregados** para etapas futuras, sejam jogos inteiros ou avulsos (Art. 61) |
| Pneus "coringa" por campeonato | **4**, solicitáveis em qualquer etapa, a qualquer momento, **sem gerar punição** (Art. 62) |
| Coringas precisam formar um jogo? | Não, "pode solicitar 3 dianteiros e 1 traseiro por exemplo" (Art. 62.1) |
| Coringa para prova única | **1 por etapa**; após 3 etapas, 4 menos os já usados (Art. 62.2) |
| Jogos de pneu de chuva **montados** | **1**, no jogo de "rodas de chuva"; **desmontar é proibido** (Art. 75, p.21) |

**MEDIDO, R1 p.18-19, Art. 63-66:** pressão é **livre** e pode ser ajustada por mecânico,
engenheiro ou terceiro indicado pelo competidor, com calibrador do promotor ou próprio. Mas
**"a aferição de temperatura dos pneus é proibida, em qualquer lugar e momento"** (Art. 64), e
pré-aquecimento / tratamento químico ou mecânico é proibido (Art. 66).

**Quando pode trocar, MEDIDO, R1 p.19, Art. 67-68:** livre nas sessões extras e oficiais, exceto
que **não é permitida troca durante uma sessão de classificação**, salvo autorização no RPP de
etapa com cronograma diferente ou pneu comprovadamente danificado (com autorização do diretor
técnico, Art. 68.1).

**Punição por estourar a cota, MEDIDO, R1 p.19-20, Art. 69.3**, e o detalhe importa porque a
punição é **por canto**:

| canto substituído | perda no grid |
|---|---|
| dianteiro **externo** (lado de apoio) | 3 posições |
| dianteiro **interno** | 2 posições |
| traseiro **externo** (lado de apoio) | 5 posições |
| traseiro **interno** | 4 posições |

**MEDIDO, Art. 69.4:** as punições são **acumulativas** (exemplo do próprio regulamento: 2
dianteiros na classificação + 1 dianteiro externo depois = perda de 8 posições). **Art. 69.5:**
troca no treino livre e/ou classificação → punição aplicada no grid da Corrida 1.

**SUPOSTO.** "Lado de apoio" é o lado externo da curva predominante do circuito, logo a punição
depende do traçado, e o modelo de dados não pode tratar os quatro cantos como simétricos nem
inferir o mapeamento sem saber a pista.

## 5. Sprint × Endurance, o que realmente muda

### Formato da prova

**MEDIDO, R3 p.7, Artigo 22:** três provas. Etapas 1 e 2 = **300 km ou 2h45**; Etapa 3 =
**500 km ou 4h30**. Limite **duplo**: distância *ou* tempo, o que vier primeiro.

**MEDIDO, R3 p.7, Artigo 23:** Etapas de 300 km só admitem **duplas**; a Etapa 3 de 500 km
admite **mínimo 2 e máximo 3** competidores por carro.

**MEDIDO, R3 p.7, Artigo 27:** a corrida é dividida em **"segmento inicial"** e **"segmento
final"**, com corte por volta declarado por etapa:

| | Etapa 1 (Termas) | Etapa 2 (Goiânia) | Etapa 3 (Interlagos) |
|---|---|---|---|
| Segmento inicial | 32 voltas | 40 voltas | 59 voltas |
| Distância total | 63 voltas | 79 voltas | 117 voltas |

**MEDIDO, Art. 27.1/27.2:** pontuação é atribuída **ao fim do segmento inicial**, desde que a
equipe complete ao menos 75% das voltas do segmento, cumpra **ao menos um pit stop obrigatório
antes do fim do segmento inicial** e **todos os competidores da equipe tenham completado ao
menos uma volta válida no segmento inicial**.

### Troca de piloto e stint mínimo

**MEDIDO, R3 p.10, Artigo 30:** *"Nos PIT STOP OBRIGATÓRIOS é obrigatória a troca dos
COMPETIDORES"*, exceto se a equipe unificou pit stops. Não cumprir → **DRIVE THRU**; impossível
aplicar → **+60 s** no tempo final (Art. 30.2).

**MEDIDO, R3 p.11, Artigo 32:** mínimo de **3 pit stops obrigatórios** nas Etapas 1 e 2 e **5**
na Etapa 3, com **duração mínima de 6 minutos cada**.

**MEDIDO, R3 p.11, Art. 32.1, "PIT TIME HANDICAP"**, o tempo mínimo cai conforme o rating do
melhor piloto da equipe (mesmo valor para CARRERA e CHALLENGE):

| pit time mínimo | equipe cujo competidor de maior B.O.P. seja |
|---|---|
| 05:57,500 | OURO |
| 05:55,000 | PRATA |
| 05:52,500 | BRONZE |
| 05:50,000 | todos COBRE |

(Equipes com Platina ficam nos 6 minutos cheios do Art. 32.)

**MEDIDO, R3 p.12, Artigo 37, existem três tipos de pit stop:**

| tipo | tempo mínimo | para quê |
|---|---|---|
| **PIT STOP OBRIGATÓRIO** | 6 min | os 3 ou 5 do Art. 32 |
| **PIT STOP EXTRA** | 60 s | reparo, abastecimento, troca extra de pilotos, troca de pneus do **mesmo tipo** |
| **PIT STOP DE TROCA DE TIPO DE PNEUS** | 3 min | seco↔chuva |

**MEDIDO, R3 p.11-12, Art. 33:** pit stops podem ser **unificados** com autorização, somando
**45 s por unificação**, 2 unificados = 12 min 45 s; 3 = 19 min 30 s; 4 = 26 min 15 s;
5 = 33 min 00 s.

**MEDIDO, R3 p.12-13, Art. 39:** a punição por pit stop curto é escalonada em faixas de
milésimo, entre 5:59,000 e 5:59,999 → +6 s a pagar num pit stop faltante (ou +12 s no tempo
final); entre 5:58,000 e 5:58,999 → +12 s (ou +24 s); entre 5:50,000 e 5:57,999 → **drive thru**
em até 3 voltas; **abaixo de 5:50,000 o pit stop não conta** na contagem mínima.

**MEDIDO, R3 p.15, Art. 40:** os boxes ficam **fechados para pit stop obrigatório do início da
corrida até o minuto 12**, independentemente de safety car.

**Voltas mínimas e máximas por piloto, MEDIDO, R3 p.9 (Art. 29) e R3a p.1-2 (Adendo 1, que
inverte a regra):**

| | Etapa 1 | Etapa 2 | Etapa 3 (2 pilotos) | Etapa 3 (3 pilotos) |
|---|---|---|---|---|
| Original R3, **mínimo** para o piloto de **menor** B.O.P. | 32 voltas | 40 voltas | 59 voltas | 40 voltas |
| Adendo R3a, **máximo** para o piloto de **maior** B.O.P. | 31 voltas | 39 voltas | 58 voltas | 39 voltas |
| Adendo R3a, mínimo para o de menor B.O.P. (trios) | N/A | N/A | N/A | 39 voltas |

**MEDIDO, R3a p.1-2:** se a prova terminar por tempo, o teto vira percentual: **52%** das voltas
do carro (Etapas 1, 2 e 3 com 2 pilotos) e **32%** (Etapa 3 com trio); no caso de trios
*"nenhum COMPETIDOR da EQUIPE poderá ter menos de 25% das voltas do carro"* (Art. 29.3
modificado). **Art. 29.5 modificado:** cada volta além do máximo → **+5 s** no tempo final.

> ⚠️ **Conflito interno MEDIDO, não resolvido aqui.** O regulamento base (R3 Art. 29, p.9) impõe
> **mínimo ao piloto de menor B.O.P.**; o Adendo 1 (R3a, p.1) reescreve o mesmo artigo como
> **máximo ao piloto de maior B.O.P.** e mantém tabelas com valores diferentes. Além disso R3
> Art. 29.5 e R3a Art. 29.6 citam uma **"Etapa 9"** num campeonato que o Art. 22 define com
> **três** etapas. Erro aparente de redação, não corrigido por mim.

### Stint é conceito nomeado no regulamento

**MEDIDO, R3 p.8-9, Art. 28.2**, sobre uso do carro reserva após quebra:

> […] o outro COMPETIDOR deve sair com um sensor fornecido pela PROMOTORA, selecionando
> corretamente seu DRIVER ID e, quando ele realizar a saída do pit lane, encerrasse o stint da
> quebra e iniciasse um novo stint.

**MEDIDO, R3 p.27, Art. 95.i:** é responsabilidade **única e exclusiva do competidor** a
*"Seleção correta do Piloto no «Driver ID» (seleção do Piloto no sistema de cronometragem)"*, primeiro item da lista, antes de banco, espelhos, cintos e rádio.

**SUPOSTO.** O `Driver ID` é o que permite atribuir volta a piloto num carro compartilhado, e o
`stint` é a unidade que fecha e reabre nessa troca. Isso é um grão **entre** sessão e volta que
o modelo atual não tem: a cadeia real do Endurance é Etapa → Sessão → **Stint (por piloto)** →
Volta, e não Etapa → Sessão → Outing → Volta.

### Pneu no Endurance é outro regime

**MEDIDO, R3 p.22-23, Artigos 65-68:**

| regra | Etapas 1 e 2 (300 km) | Etapa 3 (500 km) |
|---|---|---|
| Jogos **lacrados** para a corrida | 3 | 4 |
| Jogos **novos** para treino/quali | 5 | 6 |
| Jogos **usados** para treino/quali | 3 (de etapas passadas) | 3 |
| Coringas para prova única | 1 | 2 |

**MEDIDO, Art. 65:** a **lacração** é feita pelo promotor **após o término das classificações**,
conforme indicação de cada equipe; iniciada a corrida, só se corre com os lacrados.
**Art. 66.i:** equipes estreantes sem pneus de etapas passadas recebem 3 jogos usados **com no
mínimo 20 voltas cada**. **Art. 67:** ao fim da prova cada equipe elege **3 jogos** para
transportar à próxima etapa, *"(Sprint ou Endurance)"*. **Art. 68:** coringas não podem ser
solicitados **após a lacração**.

**SUPOSTO, e é consequência de produto:** o estoque de pneu é **um só, compartilhado entre dois
campeonatos**. Rastrear jogo de pneu por sessão não basta; a entidade "jogo" tem ciclo de vida
próprio que atravessa etapas e campeonatos.

**MEDIDO, R3 p.24, Artigo 73:** *"A utilização de qualquer software que não os fornecidos pela
MICHELIN ou pelo PROMOTOR, é PROIBIDA."* O artigo está no capítulo de pneus, entre regras de
aquecimento e armazenagem. **SUPOSTO:** a leitura restritiva é "software de pneu"; a leitura
literal é mais ampla. Vale confirmar com a categoria antes de qualquer claim comercial sobre uso
de ferramenta de terceiros em box de Endurance.

## 6. Telemetria no regulamento, o que é obrigatório

Esta seção responde à pergunta "o que é OBRIGATÓRIO registrar/entregar" e a resposta tem uma
parte incômoda.

**MEDIDO, R1 p.43 e R3 p.54:** ambos os regulamentos **técnicos** têm um capítulo intitulado
*"CAPÍTULO IX: AQUISIÇÃO DE DADOS, DO SISTEMA DE RÁDIO E DO SISTEMA DE GRAVAÇÃO DE DADOS E
OUTRAS FORMAS DE COMUNICAÇÃO"*, cujo corpo inteiro é uma linha:

> Refere-se ao respectivo artigo do Regulamento Desportivo da Série.

**MEDIDO:** varredura dos regulamentos **desportivos** (Parte A) por "aquisição de dados",
"Cosworth", "telemetria", "gravação de dados" **não encontra o artigo correspondente**. O
capítulo de comunicação da Parte A (R1 Cap. XXI, Art. 84, p.23) trata só de rádio. **A
referência cruzada não resolve**, os regulamentos de 2022 não contêm regra explícita de
aquisição/entrega de dados.

O que **existe** de obrigação com dado, medido:

| obrigação | fonte | teor |
|---|---|---|
| Câmera onboard obrigatória | R1 p.43 Art. 27 · R3 p.54 Art. 27 | cada competidor **deve fornecer** uma filmadora **V-BOX ou GOPRO** ao promotor, que a instala no cockpit para análise de incidentes, vídeo, TV e publicidade |
| Filmagem privativa do promotor | R1 p.43 Art. 27.1 | direito exclusivo, sem pagamento de direito de imagem |
| Dispositivo de filmagem não autorizado | R1 p.43-44 Art. 29 | competidor **não pode participar** com qualquer dispositivo de filmagem sem consentimento prévio do promotor |
| Transmissão on-board | R3 p.54 Art. 27.2 | promotor pode instalar a seu critério; o peso é descontado do carro |
| Telemetria como instrumento de fiscalização | R1a p.2 Art. 145 (novo) · R2a p.2 | ao fim das corridas a equipe técnica *"utilizando-se do sistema de aquisição e armazenamento de dados dos carros «PI Cosworth»"* verifica os dados de **todos** os competidores quanto à largada em 3ª marcha; infração = atitude antidesportiva, **+20 s** |
| Velocidade de pit lane por dado | R3 p.28 Art. 101 | 50 km/h no Endurance, verificado por cronometragem, radar móvel **e/ou sistema de aquisição de dados dos carros** (no Sprint o limite é **60 km/h**, R1 p.24 Art. 95, controlado "pelas autoridades") |
| Aquisição de dados durante pit stop | R3 p.18 Art. 45 | permitida durante todo o processo de pit stop, junto com ajuste de asa, ajuste de barras e troca de competidores, **desde que executada por membros da equipe da PROMOTORA**, *"coaches e convidados não podem participar"* |
| Propriedade dos arquivos de volta | **M p.41** | *"Os arquivos de volta dos carros são propriedade da Porsche Cup Brasil e só poderão ser disponibilizados ou utilizados para outras atividades […] com autorização e assinatura do piloto."* |

**SUPOSTO.** A obrigatoriedade de registro **não está no regulamento**, está no **manual
interno** (§7). O regulamento define quem é dono do dado e usa o dado para punir; o manual define
o que se registra. Para o produto isso separa duas coisas que pareciam uma: *compliance* (o que a
categoria exige) e *método* (o que o engenheiro faz).

---

## 7. Manual do engenheiro, o ciclo completo

**Fonte: M, 67 páginas, V19 de 29/05/2023.** Objetivo declarado (p.4): *"Ser um guia de trabalho
para os engenheiros da categoria, instruindo e padronizando o trabalho de todos"*.

### Preparação (p.5-10)

**MEDIDO.** Material obrigatório (p.5): caneta (*"Não dependa das canetas da organização"*),
pendrive, computador de pista, checklists, rádio do carro.

**Briefings (p.6)**, dois níveis: briefing **da equipe** no primeiro e último dia, antes das
atividades; briefing **dos engenheiros** **todos os dias**, após o da equipe. É no briefing dos
engenheiros que se entregam **todos os checklists e o computador de pista**.

**Checklists (p.7-8)**, quatro, físicos:

| checklist | conteúdo |
|---|---|
| **do Engenheiro** | conferências no início da etapa, durante as sessões e ao final; **ficha de controle de tempos e voltas de treinos opcionais e clínicas**; ficha de assinaturas do piloto da última etapa que ele participou **e uma em branco** para a atual |
| **do Mecânico** | entregue fisicamente pelo engenheiro ao seu mecânico no início da etapa |
| **do Carrinho de Ferramentas** | conferência de entrega e devolução, responsabilidade do mecânico |
| **do Computador de Pista** | computador + cabo de Pi, leitor de SD card, fonte, capa e mochila; assinado **na entrega e na devolução** |

**Arquivos da etapa (p.10)**, distribuídos via rede, pasta `DOCUMENTOS_ETAPA` no Dropbox de cada
computador de pista: documentos oficiais, manuais, briefing, cronograma, **template para análise
de dados, mapas da pista, voltas referência e relatório eletrônico**. Instrução em maiúscula:
*"ATENÇÃO: Copiar os arquivos para o computador. Não alterar o mesmo na pasta do Dropbox!"*

**Cruzamento MEDIDO.** Isto identifica a origem do acervo do HD: a pasta `DOCUMENTOS_ETAPA` que o
doc anterior mapeou **é o pacote oficial distribuído pela categoria**, não uma organização
pessoal do engenheiro. As "voltas referência" curadas por modelo (§6 do doc anterior) são
entregues pela organização.

### Início da etapa (p.11-15)

**MEDIDO.** Solicitar o computador na sala de engenharia conforme número na grade da etapa;
conectar à rede "PISTA CUP" e sincronizar Dropbox; **testar o rádio o quanto antes e com o
capacete do próprio piloto** (p.11). Verificar histórico de pneus da última etapa nos PDFs de
ficha de pneus do Dropbox do carro, *"O responsável da Michelin também pode informar o
histórico de pneus de cada piloto"* (p.12).

**Cartão SDHC (p.14)**, procedimento próprio: cartão antigo pode não ser reconhecido pela VBOX,
fazendo **saídas inteiras não serem gravadas**. Verificação: inserir no slot "SD CARD" e conferir
LED "ok" **verde sólido, sem piscar**, com a VBOX já completamente iniciada. A verificação é no
início do evento **e antes de cada saída**, *"muitas vezes o cartão é reconhecido, mas, ao
retirar e colocar de novo, para de funcionar"*. Fecha com: *"Todos os módulos VBOX são testados
antes de ir para a pista, por isso a responsabilidade pela gravação é do engenheiro."*

**Posicionamento da VBOX (p.15)**, *"deixar a indicação «TOP» para cima"*.

### Durante a etapa (p.16-33)

**Gerais (p.16-17), MEDIDO:** combinar o setup com o piloto (barras, asa, balanço de freio)
**antes** de executar e nunca deixar de avisar mudança; no primeiro treino usar como base o setup
habitual dele **ou o de melhor tempo na última etapa naquela pista**; informar condição dos pneus
e combinar estratégia de troca; avisar tempo restante **quando faltar 10 minutos, 5 e quando
encerrado**; ao final de cada treino **importar os arquivos de volta no Report eletrônico e
salvar**.

**Análise de dados (p.19-20), MEDIDO:** durante os treinos, atualizar o setup no **"Short
Comment"** dos arquivos de volta (barras, asa, gurney, set de pneus); monitorar temperaturas de
trabalho contra os parâmetros da p.34; **levar o computador de pista para o alinhamento no grid,
baixar os dados e verificar os dados vitais**; alterar a sessão no nome do arquivo a cada saída.

**Ficha de Clínicas e Treinos Opcionais (p.21-23), MEDIDO**, o "peso leve" do doc anterior, com
as regras que faltavam:

- O **próprio piloto** escreve o nome por extenso e assina.
- Todas as informações por extenso, **sem abreviações**.
- O campo **"Incidentes?"** (Sim/Não) *"só deverá ser preenchido quando houver algum tipo de
  incidente ocasionado por uma **falha técnica da categoria**"*, exemplo dado: falha de bomba de
  combustível que interrompeu a saída no início.
- Havendo incidente, a ficha **deve ser assinada por um responsável da categoria**.
- *"ATENÇÃO: A ficha de tempos de treinos opcionais e clínicas é de extrema importância para a
  organização, pois **a partir deste documento são geradas cobranças**."*

**MEDIDO, p.23**, o exemplo preenchido mostra as colunas reais: sessão · piloto · carona · hora
de início · hora de fim · duas colunas numéricas · Incidentes? · assinatura. No exemplo, três
linhas: `Enzo / Max Wilson / 9:10 / 9:18 / 3 / 2 / Sim`; `Max Wilson / Enzo / 9:25 / 9:35 / 3 / 5
/ Não`; `Max Wilson /, / 9:38 / 9:50 / 4 / 6 / Não`, com nota de rodapé *"1. Falha na bomba de
combustível."*

> **SUPOSTO.** A ficha leve tem **hora de início e fim absolutas**, não duração, o que a
> ancora no cronograma do dia. A ficha existe para faturar, e isso explica por que é leve: ela
> não serve à performance.

**Durante as sessões, o que se faz sempre que o carro para (p.24), MEDIDO literal:**

1. Baixe o arquivo de dados da saída;
2. Atualize o report eletrônico no Dropbox adicionando a saída;
3. **Cheque os alarmes nos dados**;
4. **Checar dados vitais conforme manual de pista**;
5. Verifique dados de frenagens;
6. Se prepare para conversar com o piloto;
7. **Registre os incidentes com maior nível de detalhes possível**.

**Boas práticas (p.25), MEDIDO:** antes do carro entrar no pit lane, **chamar um técnico da
Michelin** para verificar calibragem; perguntar como o carro está se comportando e dar a opção de
alterar setup e/ou trocar set de pneus; avisar o mecânico com antecedência; mostrar tempos de
volta e setores; **monitorar o consumo de combustível toda a saída**.

**Análise rápida (p.26), MEDIDO:** balanço de freio (observando se **alguma roda está travando**);
marchas corretas nas curvas; **em qual ponto da pista está a maior diferença de tempo** (os
tempos de setor agilizam a identificação). Depois de reportar ao piloto, análise detalhada de
balanço de freio, pressão de óleo, temperatura do motor e **pressão de trabalho do compressor do
câmbio**, *"dessa forma será possível prevenir e reparar problemas no carro"*.

**Análise após a sessão (p.31-33), MEDIDO.** Contra a **volta referência fornecida**, cinco
perguntas literais:

> No canal variância, onde estão as maiores diferenças de tempo? · No canal de velocidade, onde
> estão as maiores diferenças? · No canal de marchas, o piloto utiliza as marchas corretas nas
> curvas? · No canal de freio, o piloto freia com intensidade correta? · O piloto deixa o carro
> cortar giros?

E o **mapa de pista** (p.32) é usado para anotar: pontos a melhorar, **diferença em distância nos
pontos de frenagem**, pontos de tangência, **diferenças de velocidade mínima no contorno de
curvas** e perda em tempo.

Duas instruções de método (p.33) que contrariam o default de qualquer ferramenta:

> Nunca analise apenas a volta mais rápida, e sim **todas as voltas da saída**.

> ATENÇÃO: É função do analista **prevenir e detectar problemas que possam levar à quebra do
> carro**.

## 8. Procedimento de chuva

**MEDIDO, M p.27**, literal e completo:

1. Trocar para pneus de chuva;
2. Passar antiembaçante ou detergente na superfície interna dos vidros;
3. Colocar o ventilador interno na posição "Screen" (para-brisas);
4. Ligar as luzes de neblina traseiras;
5. **Barras estabilizadoras dianteiras e traseiras na posição 1 (mais mole)**;
6. **Ajustar balanço de freio: a partir do ajuste de pista seca, de 1 a 2 voltas de balanço de
   freio para a traseira**;
7. No 991 Fase 2, mudar modo de **ABS** para chuva, caso esteja de pneus de chuva;
8. No 992, mudar **ABS e TC e chave de pneu** para modo chuva, caso esteja com pneu de chuva;
9. **Após a mudança de tipo de pneu, realizar um power cycle.**

**SUPOSTO.** É uma **receita de setup determinística disparada por condição de pista**, não uma
recomendação. Cada passo mapeia num campo que a ficha pesada já tem (barras, balanço de freio,
tipo de pneu) mais dois que ela não tem (modo de ABS/TC, power cycle executado).

**MEDIDO, R1 p.21, Art. 72-74:** a direção de prova pode **determinar uso obrigatório** de pneu
de chuva em classificatório e/ou corrida; nos treinos opcionais e oficiais o uso é **livre
decisão do competidor**; em condições de chuva o competidor escolhe entre jogo de chuva novo ou
usado.

## 9. Dados vitais, os limites numéricos

**MEDIDO, M p.34.** Instrução: *"Verifique detalhadamente o comportamento das curvas de
pressões, temperaturas, tensão de bateria e funcionamento do compressor de câmbio **de todas as
saídas**"*. Valores normais:

| grandeza | 991 Fase 1 (3.8) | 991 Fase 2 (4.0) | 992 (p.35) |
|---|---|---|---|
| RPM | máx **9000** | máx **9000** | máx **9000** |
| Temp. óleo | 100, **140** °C | 100, **140** °C | 100, **130** °C |
| Temp. água | 80, 110 °C | 80, 110 °C | 80, 110 °C |
| Pressão óleo | 5,5, 8,5 bar | 5,5, 8,5 bar | **4**, 8,5 bar |
| Pressão água | 0,5, 1,5 bar | 0,5, 1,5 bar | **0,6, 2** bar |
| Pressão combustível | **4,5**, 5,5 bar | **2,5**, 5,5 bar | **3**, 5,5 bar |
| Tensão de bateria | 13, 14 V | 13, 14 V | 13, 14 V |
| Pressão compressor do paddle shift | 5,0, 7,0 bar | 5,0, 7,0 bar | **não consta na tabela do 992** |

Estes são os limites que fecham o ciclo com o bloco `vitals_*` da ficha pesada e com a
prioridade declarada do operador (análise vital de motor). São **faixas por modelo de carro**,
não constantes globais.

> ⚠️ **Conflito entre documentos oficiais, MEDIDO, não resolvido aqui.** O manual (M p.34, V19
> de 2023) dá **temperatura de óleo normal até 140 °C** no 991; o informativo de alarmes
> (A p.11 e p.12, V9 de fev/2022) dispara **alarme de Oil Temperature acima de 120 °C** no mesmo
> 991, Fase 1 e Fase 2. Ou seja: pelo alarme o carro está em falha a 121 °C; pelo manual está
> dentro do normal até 140 °C. Temperatura de água **não** tem esse problema (normal até 110 °C,
> alarme acima de 110 °C, coerentes). Documentos de anos diferentes; qual prevalece é pergunta
> para a categoria, não inferência minha.

## 10. Registro de incidentes

**MEDIDO, M p.36:** *"Após cada sessão registre de forma clara qualquer incidente tenha ocorrido
com o carro. Fale com seu mecânico para averiguar detalhes […] É responsabilidade do engenheiro
indicar todos os incidentes ocorridos com o carro."* O registro é feito por **botão dedicado no
report eletrônico**. M p.21 reforça: *"Todos os incidentes do final de semana devem ser relatados
no relatório eletrônico"*.

**MEDIDO, M p.37**, campos do formulário de incidente, conforme as legendas da tela:

| campo | teor |
|---|---|
| Quando ocorreu | informações de data/hora do incidente |
| Chassis | *"As demais informações serão preenchidas automaticamente"* |
| Descrição | **detalhada**, informando **em qual sessão** aconteceu, **qual a volta** (caso seja possível determinar), **quem foi acionado** e **se foi resolvido** |
| Resolução | se resolvido: **quando** e **qual a solução**; se não resolvido: **o motivo** |
| Arquivo de Pi | *"Copie o nome do arquivo de PI e cole neste campo"* |
| Ordem de Serviço | OS relacionada ao incidente |

**SUPOSTO, e é o achado desta seção.** O campo "cole o nome do arquivo de Pi" é um **link
manual entre o registro de incidente e o arquivo de telemetria**, feito por copiar-e-colar de
string. É exatamente a junção que uma plataforma faz por chave estrangeira. E a granularidade
declarada do incidente, **sessão + volta**, é a mesma tripla que o doc anterior encontrou na
aba `DATABASE`.

**MEDIDO, R1 p.29, Art. 120**, a definição desportiva de incidente, que é outra coisa:

> "Incidente" significa qualquer acontecimento, ou série de acontecimentos […]

(decidido pelos Comissários Desportivos, Art. 121-124). São **dois conceitos homônimos**:
incidente **técnico** (manual, do engenheiro, ligado ao arquivo de Pi) e incidente **desportivo**
(regulamento, dos comissários, ligado a penalidade).

## 11. Report de piloto

**MEDIDO, M p.46:** a pasta com arquivos de volta e report é nomeada
`"Modelo#Nº do carro, Nome do Piloto"`, ex. `992#65, Max Wilson` ou `40#65-Max Wilson`. E:

> Os reports são ferramentas muito uteis para identificar problemas que possam ter passado
> despercebidos, por esse motivo é de extrema importância eles serem preenchidos **dia a dia com
> todas as sessões e não apenas no final do evento**.

> Revise o report eletrônico antes de entrega-lo. Eles são entregues com **uma quantidade enorme
> de erros**, que geram retrabalho no oficina […]

**Fluxo de montagem (M p.47-52), MEDIDO:**

1. Abrir **um "out" do piloto por vez** no Pi, *"de forma a garantir que as informações copiadas
   estejam corretas"* (p.47);
2. Selecionar a aba **"Vitals & Alarms"**, *"Nela consta a tabela necessária para exportar os
   dados do Pi para o Excel"* (p.47);
3. Botão direito na janela **"Tabular Outing Report"** → **"Copy As Text"** (p.47);
4. **IMPORTAR** na planilha (p.48). Campos preenchidos por saída: nº de chassis (*"Caso não seja
   automático, preencher manualmente"*), **sessão**, **nº do out daquela sessão** (botão atualiza
   automaticamente), **setup de asa**, **SET de pneu utilizado**, posição do piloto no geral e
   posição final na categoria, as duas posições *"Apenas para classificatório e corridas.
   \*Não é obrigatório!"*;
5. Após adicionar cada out, **verificar os dados**: *"Procurar identificar se alguma informação
   está incoerente ou faltando, por exemplo, tempo de volta em branco, velocidades e acelerações
   absurdas"* (p.49);
6. **Verificar os alarmes de todos os "outs"**, *"Eles são de grande ajuda para identificar
   algum problema com o carro"* (p.49);
7. Gerar o **report final**, escolhendo entre **report de etapa SPRINT ou ENDURANCE**, e
   preencher nome(s) do(s) piloto(s) e a etapa (p.49);
8. Antes de gerar, **indicar quais pneus serão guardados**, *"As informações preenchidas neste
   relatório devem coincidir com as informações do checklist"*; identificar **sempre** os pneus
   de chuva disponíveis, **usados ou não** (p.50);
9. Conferir capa (nº do carro, piloto, etapa, data), posições de classificatório e corridas, e
   que **os dados do relatório são referentes à volta mais rápida do treino classificatório**
   (p.51-52).

**Cruzamento MEDIDO.** O doc anterior leu no `Report SPRINT` que o alvo é *"a melhor volta do
treino classificatório do piloto que somou mais pontos na etapa"*. O manual (p.52) manda conferir
que os dados são *"referentes à volta mais rápida do treino classificatório"*. As duas frases
descrevem lados diferentes do mesmo relatório: a coluna do próprio piloto e a coluna de
benchmark. **SUPOSTO:** o report tem as duas colunas, e é por isso que a referência precisa ser
curada, ela não sai do arquivo do piloto.

**MEDIDO, M p.53-54, pneus no fechamento:** ao final da etapa cada piloto guarda um número de
pneus **definido pelo regulamento** (§4); os pneus são devolvidos no box da Michelin com
**assinatura de engenheiro e mecânico na ficha de recolhimento**; *"Todos os pneus que o piloto
utilizou devem estar registrados na ficha de pneus daquela etapa e no report eletrônico,
incluindo os de chuva"*, com o objetivo declarado de *"manter o histórico de pneus do piloto
sempre atualizado, facilitando a consulta e rastreio"*; **"Somente o número final de voltas de
cada pneu será registrado na ficha de assinaturas"**; e *"Um dos SET's que serão guardados para
próxima etapa deverá estar montado no carro ao final da etapa"*.

**MEDIDO, M p.28:** durante o evento, *"Registrar no checklist do engenheiro o número de voltas
que determinado pneu deu **naquela sessão**"*; indicar o SET no "Short Comment" do arquivo de
volta; e informar o número de voltas ao mecânico **para anotação no próprio pneu**.

**SUPOSTO.** O jogo de pneu tem **duas contagens**: voltas por sessão (checklist, durante) e
voltas acumuladas (ficha de assinaturas, final). A ficha de assinaturas do doc anterior mostrava
pares como `1 13 / 2 17` e `W2 12`, **MEDIDO M p.57-59:** são pares `SET → nº de voltas`, com
`W*` para chuva, e existe um bloco separado *"Ficha de Assinaturas, Alterações"* onde
*"Preencher novamente todos os campos. Mesmo dos pneus que não foram alterados"* (p.59).

## 12. Nomenclatura, o padrão de arquivo

**MEDIDO, M p.42-43.** O nome do arquivo de volta carrega sessão e saída:

```
CP1.2      →  CP = Clínica de Pilotagem · 1 = 1ª clínica · 2 = 2ª saída ("Outing") daquela sessão
CP1.2.1    →  mesmo, 1º arquivo da saída  (usado quando a saída gerou dois arquivos, ex. rodou)
CP1.2.2    →  mesmo, 2º arquivo da saída
```

Modelo do carro no nome: **`40` = 991 Fase 2 · `38` = 991 Fase 1 · chassis `911` · `992#chassis`**.

**Short Comment, obrigatório (M p.41, p.43):**

```
BD 2 BT 6 ASA 3 +G SET 15
```

| token | significado |
|---|---|
| `BD` | Barra Dianteira |
| `BT` | Barra Traseira |
| `ASA` | Posição da Asa |
| `+G` / `-G` | com / sem Gurney |
| `SET` | SET de pneus, na mesma nomenclatura da ficha |

**MEDIDO, M p.41:** *"informações obrigatórias no «Short Comment» (Barras, asa, SET de pneus)"*.

**Nomenclatura de pneu (M p.29), MEDIDO:**

| código | significado |
|---|---|
| `SET 1, 2, 3…` | slicks, sequência **definida pela Michelin** e indicada no próprio pneu |
| `W1, W2, W3` | chuva, sequência definida pela Michelin |
| `C` | pneu **coringa**, permitido a compra de acordo com regulamento |
| `CUP` | pneu **doado pela organização** ao piloto (sequência definida pela Michelin) |

E o padrão de anotação no pneu físico (M p.30):
`#CHASSIS · SET DE PNEUS · RODA (DD; DE; TD; TE) · Nº DE VOLTAS`.

**MEDIDO, M p.44:** vídeo tem padrão próprio, `X-992#número do carro, nome do piloto, anoETnúmero da etapa, sessão`, exemplo literal
`1, 992#77, piloto A, 22ET01, Q1`. Arquivos de vídeo da VBOX **só podem ser renomeados pelo
software Circuit Tools**, *"para que haja paridade com os arquivos de dados"* (p.44-45).

**SUPOSTO.** `22ET01` é o mesmo padrão do nome de arquivo de referência que o doc anterior
encontrou (`REF 3.8 - 22ET3.pds`). É a chave de etapa da categoria: `AA` + `ET` + `NN`.

## 13. Dicionário de canais Porsche

**Fonte: C**, `Porsche Channels - Mj'E`, Cosworth Electronics, autor `alastair.fordham@cosworth.com`,
rev. 23/08/2013, *"IPS outputs changed for mjE"*. Escopo declarado (p.1): *"This is the channels
the Cosworth data logger will generate. As of August 2013 with 29/30 IPS output swap."*

O documento tem quatro colunas: **Channel Name · Unit · Rate (Hz) · Description**. Cerca de 130
canais. Famílias:

### Alarmes (14 canais lógicos + 2 bitfield), p.1 e p.2

`Alarm Alternator Stopped` · `Alarm Battery Voltage` · `Alarm Fuel Press` · `Alarm Gbox emsw` ·
`Alarm Lights Flash` · `Alarm Low Fuel` · `Alarm Oil Press` · `Alarm Oil Temp` ·
`Alarm Pit Speed` · `Alarm Speed FL Lock` · `Alarm Speed FR Lock` · `Alarm Water Level` ·
`Alarm Water Press` · `Alarm Water Temp`, todos **logic, 10 Hz**, *"shows 1 when alarm is active"*.

Mais: `Alarm Lights Pattern` (bitfield, **50 Hz**, *"lower 8 bits show which alarm LED's are lit"*)
e `Global Alarm` (logic, 10 Hz, *"shows 1 if any dash alarm is active"*).

**SUPOSTO.** Alarme **não é evento derivado de threshold em pós-processamento**, é um canal
gravado, com taxa própria, que o carro decidiu em tempo real. `Global Alarm` dá o índice barato:
um canal a 10 Hz responde "houve alarme nesta saída?" sem varrer os outros catorze.

### Dinâmica e controles, p.1, p.4, p.5

| canal | unidade | Hz | descrição literal (resumida) |
|---|---|---|---|
| `Speed` | kph | 100 | *"Calculated channel. Maximum of axle average"* |
| `Speed FL` / `FR` / `RL` / `RR` | kph | 50 | velocidade por roda |
| `Speed FL Locked` / `FR Locked` | Secs | 50 | *"Time in seconds FL is locked"* |
| `Brake Balance` | % | 100 | *"Percentage of Front Pressure out of the Total Brake Pressure"* |
| `Brake Bias` | decimal | 10 | *"Sensor shows number of steps F or R brake bias"* |
| `Brake Press Front` / `Rear` | bar | 100 | sensor de pressão |
| `Brake Press Front/Rear Offset` | bar | 1 | *"offset being used, made with zeroing"* |
| `Steering Angle` | degrees | 100 | sensor na coluna |
| `Steering Angle Offset` | degrees | 1 | offset do zeramento |
| `X` / `Y` / `Z Acceleration` | G | 100 | no ICD, *"not possible to zero"*; **Z lê 1 G estático** |
| `DRS X Accel` / `DRS Y Accel` | G | 100 | sensores Porsche no **túnel do câmbio** |
| `DRS Yaw` | deg/sec | 100 | sensor de ângulo de guinada Porsche |
| `Gear` | decimal | 50 | *"-1=R, 0=N, 1=1st etc"* |

**SUPOSTO.** Existem **dois** conjuntos de acelerômetro, o do ICD (não zerável) e o Porsche do
túnel do câmbio (`DRS *`). Um `ChannelMapper` que colapse "aceleração lateral" num alias único
escolhe por acaso entre duas medidas de origem física diferente. E `Brake Balance` (%, calculado
da pressão) ≠ `Brake Bias` (passos do potenciômetro), o doc anterior viu `brake_bias_driver`
registrado como `end` **e** `diff` na ficha; o `diff` só faz sentido sobre o canal de passos.

### Volta e modo de classificação, p.3, p.4

| canal | unidade | Hz | descrição |
|---|---|---|---|
| `Lap Distance` | metres | 100 | *"Calculated channel from Distance, **resets at the beacon**"* |
| `Lap Number` | decimal | 1 | *"Incrementing number, reset this number from Toolset Actions"* |
| `Lap Time` | seconds | 1 | *"Lap time in Seconds of the **previous** lap"* |
| `Distance` | m | 100 | *"Distance travelled calculated from Speed channel"* |
| `QM Reference Lap Time` | seconds | 10 | *"Qualifying mode reference lap, **learnt or loaded via Toolset**"* |
| `QM Predicted Lap Time` | seconds | 10 | *"prediction of lap time compared to reference lap"* |
| `QM Cumulative Segment Time Diff` | seconds | 10 | *"time difference to reference lap"* |
| `Logging Time Remaining` | seconds | 1 | tempo restante do logger |

**SUPOSTO, e é relevante para o produto.** O carro **já faz delta contra volta de referência, a
bordo, a 10 Hz**, com a referência *carregável de fora* (`loaded via Toolset`). O conceito de
`ActiveReference` do SA tem equivalente em hardware desde 2013, e o vocabulário do carro é
"segmento" (`Cumulative Segment Time Diff`), não "setor".

### Motor e ECU (`MS4 *`), p.3, p.4

`MS4 poil` (bar, 10 Hz) · `MS4 pwat` (bar, 10) · `MS4 pfuel` (bar, 10) · `MS4 pclutch` (bar, 10) ·
`MS4 paccumulator` (bar, 10, *"ECU air system pressure"*) · `MS4 pamb` (bar, 10) ·
`MS4 ugearp` (bar, **50**, *"gear oil pressure"*) · `MS4 tmot` (°C, 5, coolant) ·
`MS4 toil` (°C, 5) · `MS4 tgear` (°C, 5) · `MS4 ub` (volts, 10) · `MS4 nmot` (rpm, 50) ·
`RPM` (rpm, **100**, *"faster version of MS4 nmot"*) · `MS4 aps` (%, 100, pedal) ·
`MS4 ath` (%, 100, borboleta) · `MS4 speed` (kph, 5) · `MS4 gear dash` (decimal, 50).

Combustível: `Fuel Level` (Litre, 10, sensor no tanque) · `MS4 fuelcons` (Litres, 5, *"zero with
long press of Mark button"*) · `MS4 fuellap old` (Litres per lap, 1) · `MS4 fueltotal` (Litres, 5,
*"reset with Race CON"*).

Lógicos da ECU: `MS4 B padup` / `B paddn` (logic, 50, requisição de paddle) · `MS4 B blipper` ·
`MS4 B brev` · `MS4 B cmpron` (compressor ligado) · `MS4 B emsw` (marcha de emergência) ·
`MS4 B mildiag` (lâmpada de malfunção da ECU) · `MS4 B oillamp` · `MS4 B pitspeed`.

**Cruzamento MEDIDO.** Estes são exatamente os canais por trás do bloco `vitals_*` da ficha
(`vitals_toil` ↔ `MS4 toil`, etc.) e dos limites do manual (§9). A cadeia fecha:
**canal do logger → agregação declarada na ficha → limite normal no manual → alarme no dash**.

### Elétrica e diagnóstico, p.2, p.3, p.4, p.5

`IPS01`…`IPS32`, corrente (amps, 5 Hz) **por circuito nomeado**: dash, luzes de ID, faróis,
LEDs diurnos, pisca esquerdo/direito, luz de freio, ABS KL15/KL30, farol de neblina, ventoinha
do cofre, lanternas, direção elétrica (`IPS13 EPS Amps`), flaps de HVAC, lambda, limpador,
válvula Shiftec, bombas de combustível intanque 1+2 e 3+4, rádio, compressor de ar,
para-brisa aquecido, faróis baixo/alto por lado, solenoide de partida, ventilador do piloto,
bomba principal, ECU Bosch.

Mais `IPS Error Alarm` / `Latched` / `Combined` (bitfield de 32 saídas) ·
`IPS Temp Alarm` (*"1 if any of the 5 IPS box temperatures are more than 60 deg C"*) ·
`IPS Voltage Alarm` (*"if the IPS sees less than 8V for 1 second or more than 20V for 1 second"*) ·
`IPS Output Amps Total` · `IPS Switch Status`.

`Sensor Power 1`…`7` (volts, 1 Hz) declaram **qual trilho alimenta o quê**, 1: 12 V do beacon;
2: 5 V do GPS; 3: 5 V do sensor de volante e curso traseiro; 4: 5 V dos sensores de pressão de
freio e do poti de brake bias; 5: 5 V do curso dianteiro, temperatura ambiente e de combustível;
6: 5 V do sensor de posição do mapa e do botão de pit speed; 7: 12 V da caixa de direção,
**4 sensores de velocidade de roda**, nível de combustível.

**SUPOSTO.** Os `Sensor Power N` transformam "canal morto" em diagnóstico endereçável: se o
trilho 7 cai, as quatro velocidades de roda **e** o nível de combustível caem juntos, e a causa
é elétrica, não de sensor. Isso é uma verificação de integridade barata que só é possível porque
o dicionário declara o agrupamento.

`Battery Voltage` (volts, 5, *"measured at the ICD"*) · `Box Temperature` (°C, 1) ·
`Serial Number` · `Odometer` (km, 1) · `Odometer Trip` (km, 5, *"reset with long press Mark
button"*) · `Shift Lights Pattern` (bitfield, 50) · `SW_Page` (*"1=Race, 2=Prac etc"*) ·
`SW01 Mark Button` … `SW10` (bitfield, 10).

**MEDIDO, nota de escopo:** o documento é de 2013 e nomeia o `Mj'E`. **SUPOSTO:** cobre a
geração 991; nada nele menciona o 992. Vale como dicionário do acervo histórico, não como
contrato do carro atual.

## 14. Alarmes, limiar, prioridade e o que o piloto faz

**Fonte: A**, "Informativo Técnico para Pilotos", Departamento de Engenharia, fev/2022, V9.
Escopo declarado (p.2): embreagem, layout do dash, alarmes, exemplos, termo de recebimento.

### Tabela de alarmes, 991 Fase 1 (3.8), MEDIDO A p.11

| prioridade | alarme | condição | dash |
|---|---|---|---|
| 1 | Water Temperature | **> 110 °C** | aviso sobreposto + barra + L1+L2+R1+R2 **vermelho piscando** |
| 2 | Oil Pressure | pressão de óleo baixa (**limiar não informado**) | aviso sobreposto + barra + L1+L2+R1+R2 vermelho piscando |
| 4 | Oil Temperature | **> 120 °C** | barra + L3+L4+R3+R4 vermelho aceso |
| 5 | Water Pressure | **< 0,35 bar** | barra + L3+L4+R3+R4 vermelho aceso |
| 6 | Battery Voltage | **< 11,5 V** | barra + L3+L4+R3+R4 vermelho aceso |
| 7 | Water Level | nível baixo (**limiar não informado**) | barra + L3+L4+R3+R4 vermelho aceso |
| 9 | Gearbox Emergency | botão "Emergency Gearbox" acionado | barra `WARN GBOX EMSW` + L1 vermelho aceso |

### Tabela de alarmes, 991 Fase 2 (4.0), MEDIDO A p.12

| prioridade | alarme | condição | dash |
|---|---|---|---|
| 1 | Oil Pressure | pressão de óleo baixa (**limiar não informado**) | aviso sobreposto + barra + L4+R4 vermelho piscando |
| 2 | Oil Temperature | **> 120 °C** | barra + L4+R4 vermelho aceso |
| 3 | Water Temperature | **> 110 °C** | aviso sobreposto + barra + L4+R4 vermelho piscando |
| 11 | Emergency Gearbox | botão acionado (sistema de segurança do câmbio **desligado**) | barra + L3 **amarelo** aceso |
| 15 | Water Pressure | **< 0,15 bar** | barra + L4+R4 vermelho aceso |
| 18 | Water Level | nível baixo (**limiar não informado**) | barra + L4+R4 vermelho aceso |
| 20 | Check Belt | **alternador parou de funcionar** | barra + L3 vermelho aceso |

**MEDIDO, observações que importam:**

- As duas tabelas **têm prioridades faltando** (3 e 8 no 3.8; 4-10, 12-14, 16-17, 19 no 4.0).
  O documento não explica as lacunas. **SUPOSTO:** há alarmes não expostos ao piloto neste
  informativo, não que os números não existam.
- **A ordem de prioridade inverte entre os modelos.** No 3.8, temperatura de água é prioridade 1
  e pressão de óleo é 2; no 4.0, pressão de óleo é 1 e temperatura de água é 3.
- `Water Pressure` dispara a **0,35 bar** no 3.8 e a **0,15 bar** no 4.0, mais que o dobro de
  diferença no mesmo campeonato.
- Nota literal em ambas: *"Apenas o alarme de maior prioridade será mostrado no dash, mesmo
  havendo mais de um alarme acionado."*
- `Check Belt` e `Water Level` **não existem no 3.8** (A p.15 e p.18 declaram explicitamente
  "Não ocorre no 991 fase 1 - 3.8").

### O que o piloto deve fazer, MEDIDO A p.13

1. **1ª ação: resetar o alarme no botão "Alarm" do volante.** *"Se o erro for esporádico ele não
   reaparecerá no painel. Caso reapareça, o piloto deve estar apto a interpretar o aviso."*
2. **Alarme de alta prioridade (pressão de óleo, temperatura de água) → ir para o box de apoio**,
   *"de forma a evitar qualquer dano e/ou quebra do carro"*.
3. Ressalva sobre pressão de óleo: *"em alguns casos o sensor pode acusar baixa pressão em curvas
   específicas (baixo nível de óleo)"*, o piloto precisa distinguir **esporádico (uma vez na
   volta)** de **diversas vezes na volta (problema mais grave)**.
4. Ressalva sobre temperatura de água: pode subir *"em circunstância em que o carro fica muito
   tempo atrás de outro ou em baixa velocidade em momentos de «safety car»"*.

**SUPOSTO, e é o achado central desta seção.** A regra de decisão do piloto é **frequência do
alarme por volta**, não valor de pico. "Uma vez na volta" e "diversas vezes na volta" separam
artefato de sensor de falha real. Uma análise vital que reporte só mín/máx da saída **destrói
exatamente a informação que decide**.

### Assinaturas de falha, cadeias de alarme, MEDIDO

**Vazamento de radiador (A p.15, exemplificado com dado real em p.16-17):**

```
1º WATER PRESS → 2º WATER LEVEL (não ocorre no 3.8) → 3º OIL TEMP → 4º OIL PRESS → 5º WATER TEMP
```

Outro sintoma listado: *"Falta de aderência, devido a fluido de arrefecimento nas rodas"*.
O caso da p.17 registra: *"Piloto continuou na pista por mais duas volta completas, mesmo
constando alarme de pressão de óleo no painel, causando danos no motor."*

**Falha da correia secundária (A p.18, exemplificado em p.19):**

```
1º CHECK BELT (não ocorre no 3.8) → 2º LOW BATT → 3º WATER TEMP → 4º OIL TEMP → 5º OIL PRESS
```

Outro sintoma: *"Maior resistência na direção do carro, devido à queda de tensão da bateria,
comprometendo funcionamento da bomba de direção hidráulica."*

**SUPOSTO.** São **assinaturas ordenadas**, o diagnóstico está na **sequência**, não no alarme
isolado. `WATER PRESS` primeiro aponta radiador; `CHECK BELT` primeiro aponta correia. Ambas
terminam em `OIL PRESS`, que é o alarme que mata o motor. Detecção por sequência é um problema
diferente de detecção por limiar.

### Consequência contratual, MEDIDO A p.21

O documento termina com **termo de recebimento assinado pelo piloto**, declarando ciência de que

> a negligencia ao sistema de alarmes do carro ou o mau uso da embreagem […] podem gerar danos ao
> equipamento, incluindo a quebra do motor, quebra do câmbio, dano permanente ao sistema de
> embreagem […] e que, nestes casos, **não há cobertura do pacote de manutenção (running)
> tampouco do "pacote de cobertura de acidentes" (seguro)**.

**MEDIDO A p.4-6, sobre embreagem** (o outro tema do informativo): o 991 Fase 2 (4.0) tem
acelerador eletrônico que corrige a rotação conforme o pedal de embreagem é liberado na saída,
**mesmo em aclive**, *"não existe necessidade de o piloto acionar o acelerador para sair"*.
Acionar o acelerador sem liberar completamente a embreagem *"promove o desgaste prematuro,
podendo ocasionar a falha do componente"*, e o gráfico da p.5 mostra o motor atingindo o
**limite máximo de rotação controlada eletronicamente**.

**SUPOSTO.** Existe uma detecção objetiva de mau uso de embreagem, sobreposição de
`MS4 aps` > 0 com `MS4 pclutch` fora do estado liberado, na saída, com RPM no limitador. Todos os
três canais existem no dicionário (§13). Isso é análise de **preservação de componente com
consequência financeira direta**, que é exatamente a moldura do termo de recebimento.

---

## O que isto muda no modelo da plataforma

Sem propor implementação. Cada linha liga um achado a um conceito concreto do produto.

### Tipo de sessão

- **A distinção de peso é regulatória, não convencional.** `SESSÕES EXTRAS` × `SESSÕES OFICIAIS`
  é artigo numerado (R1 Art. 58) e é o sujeito das regras de pneu. A "ficha leve × ficha pesada"
  proposta no doc anterior tem respaldo normativo, mas o enum precisa de **dois níveis**:
  classe regulatória (2 valores) e tipo operacional (9 códigos do manual, §1).
- **Sessão tem janela e teto de extensão.** 45 / 15 / 10 / "25 min + 1 volta", com **até +5 min**
  discricionários por bandeira vermelha (§2). Duração não é constante do tipo, é do agendamento,
  e é mutável durante o evento.
- **Melhor volta não é escalar.** O formato Preliminar do GP (R1 Art. 105.3) dá valor desportivo
  à **2ª melhor volta**. Ranking de voltas na sessão precisa ser ordenável e endereçável por
  posição (§2).
- **"Sessão" no Endurance não é o grão de atribuição.** O grão é **stint por piloto**, delimitado
  por `Driver ID` no sistema de cronometragem (R3 Art. 28.2 e 95.i). Um carro tem 2-3 pilotos e a
  volta pertence a um deles (§5).

### Categoria

- **São três conceitos com o mesmo nome** (§3): (a) divisão do piloto no Sprint, derivada de
  **histórico de carreira** por critérios de veto; (b) subclasse da **equipe** no Endurance,
  derivada do rating do piloto que ela carrega; (c) **rating B.O.P. do piloto**, escala de cinco
  níveis com peso em kg. Modelar como um enum único no perfil do piloto perde (b) e (c).
- **A categoria é atributo persistente e versionado por temporada**, não rótulo de resultado:
  a tabela B.O.P. do Endurance (R3 Art. 159.10) cita nominalmente "Carrera Cup Sport […]
  temporada 2022" como entrada. É um histórico, com data.
- **A categoria decide de qual sessão o piloto participa**, confirmado em duas formas
  independentes: classificação segmentada por categoria no cronograma do Sprint (doc anterior) e
  ordem obrigatória de classificação por B.O.P. no Endurance (R3 Art. 112).
- **O resultado pode ser agregado de dois pilotos.** O grid do Endurance sai da **média** das
  melhores voltas dos dois competidores (R3 Art. 113). "Melhor volta da sessão" precisa saber
  de quem.

### Jogo de pneu

- **É conta corrente com saldo, não campo de texto** (§4): 3 novos por etapa, 3 carregados, 4
  coringas por temporada com saldo decrescente, e a condição de herança é **"mais de uma volta de
  uso"**, ou seja, o saldo depende do próprio contador de voltas.
- **O jogo atravessa etapas e campeonatos.** No Endurance a eleição de 3 jogos é *"para a próxima
  Etapa (Sprint ou Endurance)"* (R3 Art. 67). A entidade tem ciclo de vida acima do evento.
- Tem duas contagens de volta: por sessão (checklist, durante o evento) e acumulada (ficha de
  assinaturas, no fechamento), M p.28 e p.54.
- **A punição é por canto, com pesos diferentes** (3/2/5/4 posições, R1 Art. 69.3) e
  **acumulativa**. Os quatro cantos não são simétricos.
- Estado extra que hoje não existe em lugar nenhum: `lacrado` (Endurance, após a
  classificação), `coringa`, `doado (CUP)`, `guardado`, `descartado`. E a regra de que **um dos
  sets guardados deve estar montado no carro ao final da etapa** (M p.54) é uma restrição de
  estado físico, não de registro.

### Alarme de vital

- **Alarme é canal gravado, não derivação de threshold.** Catorze canais lógicos a 10 Hz mais
  `Global Alarm` (§13). A plataforma pode *ler* o alarme do carro em vez de recalculá-lo, e
  quando recalcula, precisa saber que o carro usou outro limiar.
- **O limite é por modelo de carro, não global** (§9): temperatura de óleo normal até 140 °C no
  991 e 130 °C no 992; pressão de óleo mínima 5,5 bar no 991 e 4 bar no 992. Uma constante única
  reprova metade do acervo.
- **Existe conflito documentado entre manual e informativo de alarmes** (óleo: normal até 140 °C
  × alarme acima de 120 °C, §9). Qualquer verificação automática precisa declarar **qual fonte
  está usando**, e o conflito precisa de resposta da categoria antes de virar regra.
- **A regra de decisão é frequência por volta, não pico** (§14): "uma vez na volta" = artefato de
  sensor; "diversas vezes na volta" = falha. Uma agregação `max`/`min` por saída, que é
  exatamente o que a ficha pesada faz, **não responde essa pergunta**. É um caso onde o método
  do papel é insuficiente e o software pode fazer melhor.
- **Falha tem assinatura sequencial** (§14): vazamento de radiador e falha de correia são
  **ordens** distintas de alarmes que convergem para `OIL PRESS`. Detecção por sequência é o
  problema real; detecção por limiar é o caso fácil.
- **A conta é financeira.** Negligenciar alarme retira a cobertura do pacote de manutenção e do
  seguro (A p.21). O caso da p.17 é um motor perdido por duas voltas de teimosia.

### Report de piloto e registro de incidente

- **O report é preenchido dia a dia, out por out** (M p.46), é um documento incremental durante
  o evento, não um export final. O que o produto chama de "relatório" é, no fluxo real, o
  **estado corrente da sessão**.
- Os campos por out são exatamente os da ficha pesada: chassis, sessão, nº do out, setup de
  asa, SET de pneu, posições (M p.48), com posições marcadas *"Não é obrigatório!"*. Há
  obrigatoriedade diferenciada **por campo dentro da mesma ficha**.
- **Existe validação declarada, hoje feita a olho** (M p.49): *"tempo de volta em branco,
  velocidades e acelerações absurdas"*. É uma regra de qualidade de dado escrita no manual e
  executada manualmente, e o manual mesmo admite que os reports chegam *"com uma quantidade
  enorme de erros"* (p.46).
- **Incidente técnico ≠ incidente desportivo** (§10). O primeiro é do engenheiro, ligado ao
  arquivo de Pi por **cópia manual do nome do arquivo**, com granularidade **sessão + volta**. O
  segundo é dos comissários (R1 Art. 120). São duas entidades.
- **O vínculo incidente ↔ arquivo é a junção mais barata que existe para automatizar**, hoje é
  copiar-e-colar de string (M p.37).

### Referência e delta

- **O carro já faz delta contra referência a bordo, a 10 Hz, desde 2013** (`QM Predicted Lap
  Time`, `QM Cumulative Segment Time Diff`, `QM Reference Lap Time`, §13), com a referência
  **carregável de fora**. O `ActiveReference` do SA reimplementa em software algo que o dado
  bruto já contém como canal.
- **A "volta referência" é entregue pela organização** no pacote `DOCUMENTOS_ETAPA` (M p.10) e o
  método de análise pós-sessão é escrito **contra ela** (M p.31). Confirma o achado do doc
  anterior: benchmark curado é insumo distribuído, não escolha de seletor.
- **O vocabulário do carro é "segmento"**, não "setor" (`Cumulative Segment Time Diff`).

### Condição de pista

- **Chuva é receita determinística de 9 passos** (§8), não um enum de clima. Dois passos não têm
  onde ser registrados hoje: modo de ABS/TC e **power cycle executado**.
- Pneu de chuva tem regime próprio: 1 jogo montado, desmontar proibido, troca vedada durante
  classificação e corrida salvo dano (R1 Art. 75-76).

### Integridade de aquisição

- **A falha de gravação é conhecida, recorrente e tem procedimento** (M p.14): cartão SDHC que
  funciona no PC e não na VBOX, que passa a falhar após remover e recolocar, com verificação
  **antes de cada saída** e LED verde sólido como critério. *"A responsabilidade pela gravação é
  do engenheiro."*
- **`Sensor Power 1..7` permite diagnosticar canal morto por trilho elétrico** (§13), falha
  correlacionada tem causa comum declarada no dicionário.
- **`Logging Time Remaining`** é canal (§13): o logger sabe quanto tempo de gravação resta.

### Propriedade e compliance

- **Arquivo de volta é propriedade da Porsche Cup Brasil** e só pode ser usado para outras
  atividades **com autorização e assinatura do piloto** (M p.41). Qualquer funcionalidade de
  compartilhamento, exportação ou benchmark cruzado esbarra nisso.
- **Câmera onboard é obrigatória e do promotor** (R1 Art. 27); dispositivo de filmagem não
  autorizado **impede a participação** (R1 Art. 29).
- **Telemetria é instrumento de fiscalização**, o promotor varre os dados de todos os carros no
  fim da corrida (R1a Art. 145). Dado de corrida não é privado do piloto.
- **R3 Art. 73 proíbe software que não seja da Michelin ou do promotor** no capítulo de pneus
  (§5). Precisa de leitura da categoria antes de qualquer claim comercial.

---

## O que continua sem resposta

1. **Regra de aquisição de dados nos regulamentos.** Ambos os regulamentos técnicos remetem a um
   artigo do regulamento desportivo que **não foi localizado** na varredura (§6). Ou a referência
   é órfã, ou o artigo está sob outro título. Só a categoria resolve.
2. **Limiares que o informativo de alarmes não dá** (§14): "pressão de óleo baixa" e "nível de
   água baixo" aparecem **sem valor numérico** nas duas tabelas. Não inventei.
3. **Prioridades faltantes nas tabelas de alarme** (§14): 3 e 8 no 3.8; 4-10, 12-14, 16-17 e 19
   no 4.0. O documento não explica.
4. **Conflito óleo 120 °C × 140 °C** (§9) entre manual V19/2023 e informativo V9/2022. Não
   resolvido, precisa de decisão da categoria.
5. **Conflito Art. 29 × Adendo no Endurance** (§5): mínimo do piloto de menor B.O.P. versus
   máximo do de maior, com tabelas diferentes; e a menção a uma "Etapa 9" num campeonato de três
   etapas.
6. **Alarmes do 992.** O informativo (fev/2022) cobre só 991 Fase 1 e Fase 2. Não há tabela de
   alarmes do 992 no corpus lido, embora o manual traga os **vitais** do 992 (M p.35).
7. **Dicionário de canais do 992.** O `Porsche Channels - Mj'E` é de 2013 e não menciona o 992.
   Existe `ENG220308_V8_LUB_Apresentação 992.pdf` e `ENG210319_V4_DAG_Manual 991.1 E 991.2.pdf`
   na mesma pasta, **não lidos**.
8. **`ENG220809_V1_RAC_Padrão de Nomenclatura dos Relatórios Eletrônicos.pdf`**, o manual cita
   um padrão de nomenclatura em várias páginas; este arquivo provavelmente o formaliza. **Não
   lido.**
9. **`ENG220330_V2_PEA_Procedimento_para_instalação_de_lastro_e_BOP.pdf`**, fecha o BOP, que
   aqui aparece só pela tabela de rating. **Não lido.**
10. **Regulamento Particular da Prova (RPP).** Citado dezenas de vezes como o lugar onde moram os
    valores variáveis por etapa (quantidade de jogos de chuva, intervalo de velocidade de largada,
    formato alterado de classificação). **Nenhum RPP foi encontrado no corpus lido.**
11. **Template `.pwb` do Pi Toolbox (v18)** e conteúdo dos `.i2wkb` do MoTeC, pendências herdadas
    do doc anterior, ainda abertas (precisam do software proprietário).
12. **Safra vigente.** Todo o regulamento lido é de **2022**. A pasta é "PORSCHE CUP 2026". Nenhum
    número deste documento deve ser tratado como regra atual sem reconferência.
