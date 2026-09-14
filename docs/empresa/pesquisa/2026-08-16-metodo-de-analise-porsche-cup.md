---
titulo: "O método de análise da Porsche Cup, como a categoria ensina a ler dado"
data: "2026-08-16"
origem: "_arquivo/saru-app/docs/research/2026-08-16-metodo-de-analise-porsche-cup.md"
status: "vigente"
area: "dinamica_veicular"
---

# O método de análise da Porsche Cup, como a categoria ensina a ler dado

> Terceiro documento da varredura do acervo Porsche Cup no HD externo, 2026-08-16.
> **Documento de PESQUISA, não decide nem implementa nada.** Decisões viram ADR.
>
> Os dois anteriores levantaram **o que existe** ([acervo e modelo de
> coleta](2026-08-16-acervo-porsche-cup-modelo-de-coleta.md)) e **o que é obrigatório
> registrar** ([regulamento e manual do
> engenheiro](2026-08-16-regulamento-e-manual-porsche-cup.md)). Este levanta **o método**:
> a apostila com que a categoria treina um engenheiro a ler telemetria, qual canal,
> em que ordem, respondendo a que pergunta.
>
> Nada aqui reescreve os anteriores. Onde há contradição, ela está **apontada**, não corrigida.

## Por que isto importa mais que os outros dois

Os documentos anteriores descrevem o **registro**. Este descreve o **raciocínio**. É a única
peça do acervo que responde diretamente à pergunta do produto: *o que um engenheiro de
categoria faz com o dado, passo a passo, que um piloto amador sozinho não sabe fazer?*

A apostila **D** é literalmente um treinamento interno: um engenheiro sênior da categoria
(Marcos Telles, *"Engenheiro especialista em análise de dados"*, D p.62) escrevendo o
procedimento para os outros engenheiros de pista. É o roteiro que a plataforma quer
automatizar.

## Convenção

- **MEDIDO**, está escrito no PDF citado, na página citada. Transcrito ou parafraseado.
- **SUPOSTO**, leitura minha ligando dois trechos, ou o documento ao produto. Falsificável.
- Onde o PDF não diz, está escrito **que ele não diz**. Nada foi completado por plausibilidade.
- Toda página citada é o **número de página do PDF** (conferido página a página).

## Corpus lido

Todos os caminhos relativos a
`/media/hd_externo/04_Archive/04_Motorsport_Hub/PORSCHE CUP 2026/Data Analysis/DOCUMENTOS_ETAPA/Apostilas e Documentos/Manuais/Lidos/`.
O HD foi acessado **somente para leitura**.

| # | documento | páginas | data | cobertura desta rodada |
|---|---|---|---|---|
| **D** | `ENG170914_V4_MAT_Análise de Dados.pdf` | 63 | V4, 31/10/2014 | **integral** (texto de todas as 63 páginas) |
| **TB** | `ENG160914_V3_MAT_Apostila Toolbox.pdf` | 32 | V3, 30/10/2014 | **integral** |
| **TS** | `ENG160914_V3_MAT_Apostila Toolset.pdf` | 35 | V3, 30/10/2014 | **integral** |
| **MEC** | `ENG210319_V15_DAG_Manual de Pista - Mecânicos.pdf` | 40 | V15, 19/03/2021 | **integral** (texto; ver ressalva) |
| **BOP** | `ENG220330_V2_PEA_Procedimento_para_instalação_de_lastro_e_BOP.pdf` | 1 | V2, 30/03/2022 | **integral** |

> ⚠️ **Ressalva de extração (MEDIDO).** Em **MEC p.9, p.12 e p.13**, os checklists do
> carrinho de ferramentas, de início de evento e diário, o corpo da tabela é **imagem**, não
> texto. Só saem as colunas `OK`/`N OK`; **os itens conferidos não são legíveis**. Não fiz OCR.
> O checklist de sessões (p.14) e o de final de evento (p.15) **são** texto e estão transcritos.
> O **BOP** é quase todo imagem: sobram as legendas e a lista de cuidados, transcritas na §14.

> ⚠️ **Descompasso de safra (MEDIDO).** D, TB e TS são de **2014** e dizem
> *"Porsche GT3 Cup Challenge Brasil"* na capa; MEC é de **2021** e diz *"Porsche Carrera Cup
> Brasil"*; BOP é de **2022**. A pasta se chama "PORSCHE CUP 2026". O software descrito (Pi
> Toolbox / Pi Toolset, Cosworth) é o de 2014, o acervo tem template `.pwb` **v18 de 2022**,
> o que sugere continuidade, mas isso não foi verificado. Nada aqui vale como procedimento
> vigente sem reconferência.

---

# Parte 1, O método (documento D)

## 1. A ordem é fixa e é a primeira coisa que o documento ensina

**MEDIDO, D p.18**, sobre dados vitais:

> "Eles não são de interesse do piloto, apenas do engenheiro.
> É a prioridade nº1, **não se avalia performance de um carro com problemas**."

E, na mesma página, a justificativa em termos de custo e de responsabilidade:

> "Um motor quebrado por falta de pressão de óleo, e que já estava com a pressão baixa desde o
> começo do fim de semana, é um erro do engenheiro. O mesmo vale para motores que tiveram o
> limite de giro excedido diversas vezes."

E o modo de falha que não é mecânico, é de corrida (D p.18):

> "se a bateria não está boa e sua tensão diminui durante todo o fim de semana, mas só acaba
> no grid."

**Sumário do conteúdo (MEDIDO, D p.2)**, que é a ordem em que a apostila trata os assuntos:

```
Dados vitais → Tempo → Aceleração → Frenagem → Coasting → Troca de marcha → Curvas
```

**SUPOSTO.** Esta é a hierarquia inteira do produto numa linha. Não é "escolha uma lente":
é **saúde do carro antes de performance**, e dentro de performance, **tempo antes de causa**.
Casa exatamente com a direção já registrada na memória do repo (*análise vital de motor é a
1ª análise*), e aqui ela está escrita pela categoria, não inferida.

## 2. Leitura × interpretação, a fronteira do que a máquina entrega

**MEDIDO, D p.17.** A apostila separa explicitamente as duas coisas. Reproduzo os pares
como estão (leitura → interpretação):

| leitura (o gráfico mostra) | interpretação (o analista conclui) |
|---|---|
| "O câmbio não troca de marcha" | "porque o compressor está sem pressão" |
| "O piloto aplica pouca pressão no freio" | "porque o balanço está errado" |
| "O piloto tirou o pé do acelerador" | "porque fica com medo, ou porque passou na sujeira?" |
| "O piloto não acelera no ponto certo na saída da curva" | "porque errou na entrada da curva anterior" |
| "O piloto toma 0,5 segundos do primeiro colocado" | "porque está de pneus velhos" |

> "Ler os gráficos é relativamente simples, são respostas de uma leitura […] Porém, o trabalho
> do analista de dados é **interpretar** o que ele está lendo" (D p.17).

**SUPOSTO, e é o achado central desta seção.** Toda linha da coluna esquerda é **detectável
por regra sobre canais**, são limiares, comparações e derivadas. Toda linha da direita exige
**contexto que não está no canal**: estado do pneu, pressão de um sistema auxiliar, o que
aconteceu na curva anterior, o que o piloto sentiu. Duas consequências para o produto:

1. A coluna esquerda é o escopo honesto de uma detecção automática. É bastante, é exatamente
   o que o amador não enxerga sozinho.
2. A coluna direita não é "IA melhor": é **dado que precisa existir no registro** (jogo e
   voltas do pneu, vitais do sistema, encadeamento entre curvas, relato do piloto). Os
   documentos anteriores já mostraram que a categoria registra tudo isso em ficha. A ponte
   entre as duas colunas é o modelo de dados, não o modelo estatístico.

## 3. As sete formas de ver, e a pergunta que cada uma responde

**MEDIDO, D p.4:** *"Um mesmo comportamento do carro pode ser identificado em canais
diferentes e de maneiras diferentes."* E: *"Independentemente de qual software de análise se
está usando, as funções básicas são sempre as mesmas, os gráficos tem sempre a mesma «cara»."*

| forma | página | para que serve (MEDIDO) |
|---|---|---|
| Gráfico tempo/distância | D p.5-7 | *"É o mais utilizado."* Canais em Y, tempo **ou** distância em X |
| Mapa da pista | D p.8-9 | localizar no traçado o ponto que está sendo analisado no gráfico |
| X-Y | D p.10 | *"Plota pontos ou linhas de qualquer canal em relação a qualquer outro canal."* |
| Histograma | D p.11 | *"representam um dados em várias frequências, de tempo ou percentuais"* |
| Tabela | D p.12 | *"Mostram valores máximos, mínimos, médios, diferença entre valores e destacam os valores de interesse."* |
| Bit field | D p.13 | *"Campos booleanos, mostram quando um canal ou botão está ligado/desligado."* |
| Instrumento | D p.14 | volante, brake bias, % de acelerador e freio, aceleração lateral/longitudinal |

**Canais que se sobrepõem ao mapa (MEDIDO, D p.9):** posição do acelerador, pressão de freio,
coasting, marcha, sobre-esterço/subesterço. As legendas das figuras da mesma página nomeiam
quatro usos: **marchas · travamento de rodas · sobre-esterço/subesterço · relação de marcha
total**. *"qualquer canal pode ser sobreposto"*.

> **SUPOSTO.** A tabela (D p.12) é a única forma que **já entrega agregação declarada**, máximo,
> mínimo, média, diferença. É o mesmo vocabulário (`max`/`min`/`mean`/`end`/`diff`) que o doc
> do acervo encontrou na ficha real. Duas fontes independentes dizendo que agregação é
> propriedade do canal, não escolha de widget.

## 4. A regra de eixo X, dura, e a plataforma tem como violar

**MEDIDO, D p.5**, textual:

> "Para se comparar dois pilotos deve-se **sempre** utilizar distância no eixo X, mas para
> analisar os dados vitais do carro deve-se **sempre** utilizar o gráfico por tempo."

O porquê, na mesma página e na p.6:

- **Por distância** o gráfico mostra *"onde e por qual distância um evento ocorreu"*, ponto de
  freada, ponto de tangência, velocidade num trecho.
- **Por tempo** mostra *"quando e por quanto tempo um evento ocorreu"*, quanto tempo a roda
  ficou travada, por quanto tempo a pressão de óleo esteve baixa, qual motor sobe de giro
  mais rápido.
- **MEDIDO, D p.6:** *"o gráfico por distância expande os trechos de velocidade alta e comprime
  os trechos de velocidade baixa. Por tempo, as curvas se deslocam cumulativamente."*
  Legendas das figuras: **"Distância, Onde?"** e **"Tempo, Quando?"**

**Tiled × Overlaid (MEDIDO, D p.7):** separados *"facilita a visualização de voltas
sobrepostas"*; juntos *"melhora a visualização de variações pequenas e de correlação entre
canais"*.

E a segunda regra dura, específica de vitais (**MEDIDO, D p.18**, bloco "Dicas"):

> "Sempre selecione **todas as voltas da saída de uma vez só**;
> Sempre utilize o eixo X do gráfico **em tempo**."

**SUPOSTO.** Isto é uma regra de UI, não uma preferência: o eixo X correto é **função do que
se está analisando**. Comparar pilotos em eixo de tempo é um erro de método, e a apostila
trata como erro. Uma plataforma que oferece o toggle livre em qualquer contexto está deixando
o amador cometer o erro sozinho.

## 5. Vitais, o que se olha e como o problema aparece

**MEDIDO, D p.18**, definição: *"dados de sensores que monitoram as funções vitais do carro
para diagnóstico"*, **pressão de água e óleo · temperatura de água, óleo e câmbio · tensões
e correntes**.

**Linhas de referência (MEDIDO, D p.19):**

> "Tanto no i2 quanto no Toolbox, os templates foram feitos com linhas de referência que
> indicam os limites normais máximos e mínimos de cada canal. Um problema pode estar ocorrendo,
> ou em eminência de acontecer, caso os valores estejam acima (por exemplo, mangueira de
> retorno de água interrompida) ou abaixo (por exemplo, falta de pressão de combustível) dos
> limites.
> **Atenção: Estes não são os mesmos limites dos alarmes!**"

> **Esta linha resolve, parcialmente, o conflito registrado no doc anterior.** O doc de
> regulamento (§9) registrou como conflito não resolvido a temperatura de óleo *normal até
> 140 °C* (manual do engenheiro V19/2023) contra o *alarme acima de 120 °C* (informativo de
> alarmes V9/2022). **MEDIDO, D p.19: são duas escalas diferentes por desenho.** A linha de
> referência do template marca a **faixa normal de diagnóstico**; o alarme do painel marca o
> **ponto de ação do piloto**. Não são o mesmo número e a apostila avisa explicitamente que não
> devem ser confundidos.
>
> **SUPOSTO.** Isso reclassifica o achado: não é erro de documento, é **duas grandezas
> distintas com o mesmo nome**. Mas continua **sem resposta** qual valor é qual em cada modelo
>, a apostila estabelece a distinção e **não dá nenhum número**. Não invento nenhum.

**Assinaturas de problema que a apostila usa como exemplo**, cada uma é uma página com
gráfico (imagem) mais um rótulo em texto. Os rótulos são MEDIDO; **os gráficos são imagem, os
valores não são legíveis**:

| p. | rótulo literal |
|---|---|
| 20 | "Pressão de água baixa" |
| 21 | "Temperaturas baixas" |
| 22 | "Pressão de combustível caindo" |
| 23 | "Correia do alternador quebrada" + "Pressão de combustível caindo" + "Mudança rápida nas temperaturas" + "Tensão de bateria caindo" |
| 24 | "Pressão de óleo caindo **durante as curvas**" |

> **SUPOSTO.** As páginas 23 e 24 são as duas mais interessantes para produto. A p.23 é uma
> **falha única com quatro sintomas simultâneos**, correia quebrada derruba combustível,
> temperatura e tensão ao mesmo tempo. A p.24 é uma falha **condicionada a evento de pista**:
> pressão de óleo só cai em curva (surge de cárter sob aceleração lateral). Nenhuma das duas é
> detectável por limiar por canal isolado: a primeira precisa de **correlação entre canais**, a
> segunda de **correlação com fase da volta**. A apostila trata isso como o trabalho normal do
> engenheiro. O doc anterior já registrou "cadeias de alarme" na mesma direção, aqui a mesma
> ideia aparece nos vitais, antes de qualquer alarme disparar.

## 6. Tempo, as duas maneiras, e a volta teórica que não vale

**MEDIDO, D p.25:** *"É a informação que mais importa para o piloto. Existem duas maneiras
principais para se comparar tempo."*

### Maneira 1, tabela de trechos/setores (D p.25)

*"Tabela com tempo volta e divisão de trechos (i2) ou setores (Toolbox)."* Dela saem **duas
voltas teóricas diferentes**, e a apostila julga uma delas:

| volta teórica | definição MEDIDA (D p.25) | veredito MEDIDO |
|---|---|---|
| **Eclectic** | *"Muda a posição da linha de chegada, mostrando um tempo de volta que soma setores/trechos consecutivos que somam o menor tempo entre todos."* | *"**É um tempo que o piloto realmente fez.**"* |
| **Rolling Minimum** | *"Soma de todos os melhores setores/trechos. Quanto maior o número de divisões, maior a diferença de tempo."* | *"**É um tempo pouco confiável.**"* |

**SUPOSTO, e é acionável.** A "volta teórica" que praticamente todo software de telemetria
mostra por padrão, inclusive o que a plataforma tende a implementar, é a **Rolling Minimum**,
e a categoria a chama de pouco confiável **por construção**: quanto mais setores, mais fantasia.
A alternativa que ela endossa (Eclectic, melhor janela de setores **consecutivos**, deslocando
a linha de chegada) é uma volta que existiu de fato. São duas métricas com pesos morais
opostos e a diferença cabe numa frase de tooltip.

### Maneira 2, delta cumulativo (D p.26)

*"O canal «Variance» (i2) ou «Compare Time» (Toolbox) mostra de maneira gráfica a diferença
cumulativa de tempo entre duas voltas que estiverem abertas.* **Deve-se estar atento à qual
volta é a referência utilizada.**"

Os três estados que a figura rotula (MEDIDO, aparecem duas vezes na página): **"Não ganhou nem
perdeu" · "Perdendo tempo" · "Ganhando tempo"**.

> **SUPOSTO.** *"Deve-se estar atento à qual volta é a referência"* é, em UI, o requisito de a
> referência estar **sempre visível e sempre nomeada** junto do delta, não escondida num
> seletor. É o mesmo aviso que a memória do repo já registrou para o caso de circuitos
> divergentes: o delta sem referência explícita é um número sem significado.

## 7. Aceleração, a curva anterior é a culpada

**MEDIDO, D p.27**, e é a tese mais forte da apostila:

> "As retas constituem em média **70 a 80% do comprimento total de uma pista**. Um carro de
> corrida passa muito mais tempo em reta e aceleração máxima do que em qualquer outra situação.
> Porém, todas as retas começam com a saída de uma curva […]
> **Na imensa maioria dos casos em que o piloto reclama de falta de rendimento na reta culpando
> o motor, o problema é um erro na saída da curva que a antecede.**"

**Pontos a analisar (MEDIDO, D p.27):**
- ponto em que começa a acelerar depois da frenagem;
- ponto de 100% de acelerador depois da frenagem;
- pontos em que alivia o acelerador, ou tira completamente o pé;
- **média da posição do acelerador por volta**.

**Rótulos das figuras (MEDIDO):**

| p. | assunto | rótulo |
|---|---|---|
| 28 | uso do acelerador | "Aliviou o acelerador onde é possível cravar" |
| 29 | uso do acelerador | "Demorou muito para acelerar 100%" / "Começou a acelerar no ponto certo" |
| 30 | arrasto aerodinâmico | "Aceleração longitudinal máxima caindo com o aumento da velocidade" |
| 31 | tração | "Indício de perda de tração no canal de **RPM**" |
| 32 | tração | "Indício de perda de tração no canal de **Slip Ratio**" + "Ocorrendo quando o piloto começa a acelerar" |

> **SUPOSTO.** O par p.31/p.32 é método puro: **o mesmo evento físico (perda de tração) tem duas
> assinaturas em canais diferentes**, e a apostila mostra as duas de propósito, RPM para quem
> não tem velocidade de roda por canto, Slip Ratio para quem tem. É o princípio declarado na
> p.4 ("mesmo comportamento em canais diferentes") aplicado. Para produto: a detecção deve
> **degradar por canal disponível**, não exigir o conjunto completo.
>
> E a p.30 é um teste de sanidade de aerodinâmica que sai só do acelerômetro longitudinal e da
> velocidade, sem sensor de arrasto.

## 8. Frenagem, e a única equação do documento

**Pontos a analisar (MEDIDO, D p.33):** ponto de início e fim da frenagem · intensidade ·
velocidade para atingir a máxima pressão de freio · travamento de rodas · balanço de freio e
Brake Bias.

**Rótulos das figuras (MEDIDO):**

| p. | rótulo |
|---|---|
| 34 | "Capacidade de frenagem aumentando com o aumento da velocidade" (pressão aerodinâmica) |
| 35-36 | "Desaceleração menor" + "Pouca pressão" |
| 37 | "Freou antes do ponto e por maior distância" / "Freou antes do ponto" / "Freou por mais tempo" |
| 38 | "Roda dianteira travando" (×2) + "**Piloto aumentou o Brake Bias!**" |
| 39 | "Roda dianteira travando" (×2) + "**Piloto não alterou o Brake Bias!**" |
| 41 | "Balanço muito dianteiro" / "Balanço muito traseiro" (via Slip Ratio) |

> **SUPOSTO.** As páginas 38 e 39 são o mesmo sintoma (dianteira travando) com **desfechos
> opostos**, e a diferença é uma ação do piloto entre as duas voltas. Isto é a justificativa
> concreta do achado do doc do acervo de que `brake_bias_driver` é registrado como `end` **e**
> como `diff`: o que interessa não é só o valor, é **a mudança feita durante a saída**. Sem o
> `diff`, as páginas 38 e 39 são indistinguíveis.

### Slip Ratio (MEDIDO, D p.40, integral)

> "A razão de escorregamento é a relação entre a velocidade da roda e a do carro. O pneu atinge
> a sua maior aderência, e consequentemente a maior força longitudinal, em uma dada porcentagem
> de escorregamento."

$$SR = \frac{V_{Roda} - V_{Carro}}{V_{Carro}}$$

E a adaptação prática para um carro de tração traseira (MEDIDO, D p.40):

> "Como o carro possui tração nas rodas traseiras, pode-se considerar a velocidade do eixo
> dianteiro igual a velocidade do carro durante a aceleração. Assim, para calcular o Slip Ratio
> das rodas traseiras, utilizamos a velocidade das rodas dianteiras."

$$SR_T = \frac{V_T - V_D}{V_D}$$

> "Durante a frenagem esta consideração não é correta. Porém, como buscamos a maior eficiência,
> sabemos que todos os pneus devem estar no seu ponto de aderência máxima e que, se o freio
> estiver equilibrado, as 4 rodas terão mesma velocidade nesta fase. Portanto, **durante a
> frenagem o Slip Ratio deve estar próximo de zero**."

> ⚠️ **A apostila NÃO diz qual é a porcentagem de escorregamento de aderência máxima.** Diz
> apenas que existe *"uma dada porcentagem"*. Não preencho.
>
> **SUPOSTO.** O canal é o mesmo, mas **o critério de leitura muda de fase**: em aceleração o
> SR traseiro mede tração; em frenagem o SR de qualquer canto mede **desequilíbrio de balanço**
> (p.41: "muito dianteiro" / "muito traseiro"), e o alvo é zero. Um detector que aplique um
> único limiar de SR à volta inteira mistura duas perguntas diferentes.

## 9. Coasting (D p.42)

**MEDIDO, integral:**

> "Quando o piloto não está acelerando e nem freando."
> Rótulos das figuras: *"**Antes do ponto de frenagem sempre faz perder tempo**"* ·
> *"**Após a freada pode ser benéfico em algumas situações**"*.

> **SUPOSTO.** Coasting não é um vício uniforme, é **contextual pela fase da curva**. Um
> indicador de "% de coasting por volta", que é o formato usual em app de telemetria amadora,
> soma um erro com uma técnica válida e produz um número sem significado. O corte útil é
> **coasting antes da frenagem**, e este a apostila condena sem ressalva.

## 10. Troca de marcha (D p.43-53)

**Pontos a analisar (MEDIDO, D p.43):** marchas utilizadas em cada trecho · **força feita na
alavanca de câmbio** · **pressão na embreagem** · **puntataco** · rotação ideal para troca ·
ocorrência de corte de giro.

| p. | rótulo literal (MEDIDO) |
|---|---|
| 44 | "Piloto puxa a alavanca de câmbio antes (**0,1 s**) de pressionar a embreagem totalmente" · "(**0,11 s**)" |
| 45 | "Piloto reduz de 6ª para 2ª sem soltar a embreagem" |
| 46 | "Rotação correta para a troca, não afeta a aceleração do carro" |
| 47 | "Troca de marcha antes do ponto, a aceleração longitudinal diminui" |
| 48 | "Corte de giro, causa perda de tempo significativa na reta" |
| 49 | "Apenas o puntataco da referência está aparecendo" |
| 50 | "A terceira marcha entra mas retorna" |
| 51 | "O câmbio não reduz com o acionamento do paddle down. A pequena variação no canal do potenciômetro do câmbio mostra que o atuador tenta engatar a marcha. EMSW ligado…" |
| 52 | "O câmbio não reduz. O piloto estava com o pé repousado na embreagem (acionada mesmo com acelerador em 100%)…" |
| 53 | "Carro no bico de pato, em 5ª marcha e sem acionamentos nos paddles. Piloto freou sem reduzir. Volante desconectado…" |

> **MEDIDO:** `0,1 s` e `0,11 s` são os **únicos valores numéricos de sincronismo** dados na
> apostila, e vêm como anotação de figura. A apostila **não** declara um limiar de "sincronismo
> aceitável", não infiro nenhum.
>
> **SUPOSTO, e vale mais que os números.** As páginas 50-53 são **quatro diagnósticos
> distintos do mesmo sintoma de piloto** ("o câmbio não reduziu"): marcha que engata e volta;
> falha do atuador com o potenciômetro tentando; **pé do piloto repousado na embreagem**; e
> volante fisicamente desconectado. Três das quatro causas são invisíveis sem os canais
> auxiliares que a p.43 lista, **força na alavanca, pressão de embreagem, potenciômetro do
> câmbio, estado dos paddles**. Isso mede a distância entre um dataset de simulador/GPS e um
> dataset de categoria: sem esses canais, "o câmbio não reduziu" é o fim da análise, não o
> começo. E o quarto caso (p.52) é o mais desconfortável, a causa é **o piloto**, e o dado
> prova.

## 11. Curvas, as três fases e a geometria do ápice

**MEDIDO, D p.54.** *"Contornar uma curva tem três fases:"*

```
1. Freada até o ponto de início do ponto de contorno;
2. Contorno até o ponto de tangência;
3. Saída da curva.
```

Além do já discutido, analisa-se: **velocidade mínima de contorno · ponto de tangência ·
subesterço ou sobre-esterço**. E as cinco perguntas de diagnóstico, textuais (D p.54):

> "Os pontos de frenagem e aceleração estão corretos?
> O carro sai de frente/traseira **durante a frenagem**?
> O carro sai de frente/traseira **durante o contorno**?
> O carro sai de frente/traseira **ao tentar acelerar**?
> Ele é neutro em alguma das fases?"

> **SUPOSTO, e é o achado de modelagem desta seção.** Subesterço/sobre-esterço **não é um
> atributo do carro nem da curva**, é um atributo do par **(curva, fase)**. Quatro respostas
> por curva, não uma. Qualquer indicador que devolva "o carro está subesterçando" sem dizer
> em qual das três fases descarta a informação que decide o acerto.

**Velocidade mínima (D p.55).** Rótulo: *"Parando demais o carro"*. As anotações numéricas da
figura são **`+ 0,09 s`, `+ 0,048 s`, `+ 0,069 s`**, MEDIDO como texto, mas **o gráfico é
imagem e o contexto (qual curva, quais voltas) não é legível**. Registro os números como
existentes na página; não os uso para nada.

**Ponto de tangência, o método é o raio de curva contra a distância (MEDIDO, D p.56-58).**
As três páginas são a mesma figura com três desfechos:

| p. | caso | geometria (MEDIDO) | consequência (MEDIDO) |
|---|---|---|---|
| 56 | **correto** | *"Raio mínimo coincide com o centro da curva"*; *"Gráfico do raio de curva é simétrico"*; *"Patamar no G-LAT"* | *"Mantém a velocidade o maior tempo possível sem sacrificar a velocidade de saída."* |
| 57 | **tardio** | *"Raio mínimo **antes** do centro da curva"*; *"G-LAT caindo"* | *"Sobra pista na saída, carro aceita acelerador mais cedo, mas **sacrifica a velocidade de entrada** na curva"* |
| 58 | **antecipado** | *"Raio mínimo **depois** do centro da curva"* | *"Precisa virar mais o volante na saída da curva, **acelera tarde e perde velocidade de saída**"* |

> **SUPOSTO, e é o item mais diretamente implementável do documento.** O critério de ápice é
> **puramente geométrico e derivável de canais básicos**: raio de curva instantâneo contra
> distância, comparado ao centro geométrico da curva; simetria da curva de raio; patamar (ou
> queda) no G-LAT. Não precisa de sensor especial, de setup, nem de referência de outro piloto
>, precisa de **velocidade, aceleração lateral e um mapa com as curvas delimitadas**. O
> Toolbox delimita curvas no mapa (TB p.27, §13 abaixo), então a delimitação é dado curado,
> não detecção.

**Subesterço e sobre-esterço (D p.59-60), método MEDIDO:**

| p. | rótulo |
|---|---|
| 59 | "**Carro neutro, curva de G-LAT acompanha a do volante**" |
| 60 | "Sobre-esterço: **correções bruscas no volante para o lado contrário da curva**" |
| 60 | "Subesterço: **piloto aumenta o ângulo do volante gradativamente, mas o G-LAT cai**" |

> **SUPOSTO.** O método é **correlação entre ângulo de volante e G-LAT**, não um canal
> dedicado. Neutro = as duas curvas andam juntas; subesterço = volante sobe e G-LAT não
> acompanha; sobre-esterço = **inversão de sinal** no volante. É detectável com dois canais que
> qualquer aquisição decente tem. O doc do acervo registrou "sobre-esterço/subesterço" como
> canal sobreposto ao mapa (D p.9), aqui está como ele se constrói.

**Erro comum encadeado (MEDIDO, D p.61):**

> "Piloto freia muito cedo" → "Por estar lento, começa a acelerar muito cedo" → "Carro fica mau
> posicionado e o piloto não consegue acelerar 100%"

> **SUPOSTO.** É a mesma tese da p.27 fechando o ciclo: **o erro é upstream do sintoma**. Um
> sistema que aponta "você não acelerou 100% na saída da curva 4" está apontando o efeito. A
> causa está na frenagem da mesma curva, ou na curva anterior.

## 12. A bibliografia (MEDIDO, D p.63)

> SEGERS, J. *Analysis Techniques For Racecar Data Acquisition*, 2nd Ed, SAE International, 2014.

**Única referência citada em todo o documento.** É a base declarada do método da categoria.

---

# Parte 2, O vocabulário Cosworth (TB e TS)

## 13. Hierarquia de objetos, o que é outing, lap, setor, template

**MEDIDO, TB.** A cadeia de objetos do Pi Toolbox, com o nome exato que a categoria usa:

| objeto | onde | definição MEDIDA |
|---|---|---|
| **Outing** | TB p.12, atalho `Ctrl+L` "Add Outing" | é a **unidade de arquivo aberta**, *"Para abrir um arquivo de dados, clique em «Data» e em seguida em «Add Outing…»"* |
| **Lap** | TB p.13 | *"As voltas e os respectivos tempos são mostrados na barra superior «Navigator»."* *"Selecionar duas ou mais voltas irá sobrepor os gráficos delas."* |
| **Setor / trecho** | TB p.26 | *"As parciais são mostradas de acordo com a divisão feita no mapa da pista."* |
| **Workbook** | TB p.15, D p.15 | o template; **máx. 6 worksheets** (TB p.20) |
| **Worksheet** | TB p.20 | aba; **máx. 16 displays** por aba (TB p.21) |
| **Display** | TB p.21 | um gráfico ou tabela dentro da aba |

**Equivalência entre softwares (MEDIDO, D p.15):** `Template` = **Pi → Workbook** ·
**MoTeC → Project**.

> **Correção de registro apontada, não aplicada.** O doc do acervo lê `Outing` a partir do nome
> das abas do workbook (`CUP#255TE1Out1`). **TB p.12 mostra que `Outing` é o nome que o próprio
> software dá ao arquivo de dados**, a ficha herdou o vocabulário da ferramenta, não o
> inventou. Reforça a conclusão daquele doc; não a contradiz.

**Abas do template oficial de 2014 (MEDIDO, TB p.6-11).** São seis, e a divisão é por domínio:

| aba | conteúdo declarado |
|---|---|
| `Driver` | *"informações principais para se comparar uma volta"* |
| `Brakes` | canais do sistema de freio |
| `Gear shift` | dados para análise da troca de marchas |
| `Vitals & Alarms` | canais dos dados vitais do veículo |
| `IPS32` | informações da unidade de controle do sistema elétrico |
| `Free Worksheet` | *"mais alguns gráficos úteis e é livre para ser editada"* |

> **SUPOSTO, e é convergência forte.** Esta é a **terceira** fonte independente do acervo
> apontando a mesma decomposição por domínio: os workbooks MoTeC (`Base`, `Brakes`, `Driver`,
> `Engine`), o template Pi de 2014 acima, e os presets de lente do SA
> (`race-engineer`, `vehicle-dynamics`, `driver-coach`, `tyre-engineer`). `Driver`, `Brakes` e
> uma lente de motor/vitais aparecem nas três. A que **não** aparece nas fontes da categoria é
> uma lente de pneu isolada, no acervo, pneu é ficha e planilha (jogo, voltas, pressão), não
> aba de gráfico.

**Política de template (MEDIDO, D p.15):**

> "Templates são pessoais, cada um tem a sua maneira preferida de organizar as coisas. Além
> disso, criam-se templates diferentes de acordo com o tipo de treino, teste, corrida e
> **principalmente carro** que irá se trabalhar. […] Criar um template é trabalhoso e custa
> tempo. Para que cada um não tenha que criar o seu próprio template, e **para manter um padrão
> entre todos os analistas de dados**, temos os nossos templates padrões instalados nos
> computadores de pista."

E a regra de uso (MEDIDO, TB p.5):

> "Caso você altere o template, **não salve em cima do template original**. Crie um novo
> template com o seu nome e mantenha o original sem alterações. De preferência, altere apenas
> a primeira e última abas."

> **SUPOSTO.** É exatamente a relação **template ↔ workbook** que o SA já modela: um preset
> curado, imutável, do qual se deriva uma cópia pessoal. A categoria chegou nisso por dor
> operacional (padrão entre analistas + custo de montar). E o critério de "que template usar"
> é **tipo de sessão + modelo de carro**, os dois eixos que os docs anteriores já apontaram
> como ausentes no modelo da plataforma.

**Split Report (MEDIDO, TB p.26).** É o display de tempos:

> "A visualização dos tempos de volta, parciais de cada setor e voltas teóricas são mostradas
> no campo «Split Report». […] Para que este display mostre os tempos, é necessário que o canal
> **«Elapsed Lap Time»** seja adicionado a ele. São mostrados os tempos apenas de **um único
> arquivo de dados por display**, para abrir mais de um arquivo de dados é necessário adicionar
> outro display."

**Edição do mapa (MEDIDO, TB p.27):** *"O mapa pode ser editado, para adicionar o **nome das
curvas** e separar os **setores**."* Um limite de trecho pode ser arrastado; clique duplo edita
o nome; há botão para inserir a divisão de um setor.

**Canais matemáticos e constantes (MEDIDO, TB p.28-30):**

> "Estes canais são equações, que utilizam como variável os canais que são logados. As
> expressões podem conter operações matemáticas básicas, funções, **derivadas, integrais e
> condicionais**." O editor tem **frequência do canal** própria por canal criado.
> Constantes: *"facilita a edição dos canais matemáticos criados, diminui a chance de cometer
> erros de digitação ou de unidades e deixa as expressões mais organizadas."*

**Propriedades de canal que o template guarda (MEDIDO, TB p.24-25):** cor da linha e escala de
cor · autoescala · limites de escala manual · posição do canal no gráfico · **limites das linhas
de alarme** · e uma flag de *"permite ou não posicionar e dimensionar o gráfico de um canal
quando o display estiver no modo «Overlay»"*.

**Formato de tempo (MEDIDO, TB p.19):**

> "Em «Formats» se altera as unidades e casas decimais do tempo e da velocidade. **Por default,
> o programa vem configurado para mostrar os tempos em segundos.**" Opções: segundos ·
> minutos:segundos · horas:min:segundos.

> **SUPOSTO.** A ferramenta nasce com o formato errado para o usuário e exige configuração
> manual. É o mesmo problema que a memória do repo já registra como regra de produto
> (tempo de volta sempre `m:ss,mmm`, nunca segundo cru), aqui está a origem histórica do vício.

**Atalhos que revelam o fluxo de trabalho (MEDIDO, TB p.15-16).** A lista completa é longa;
os que dizem algo sobre método:

| atalho | função |
|---|---|
| `Ctrl+E` | **Select all laps**, *"Seleciona todas as voltas da saída"* |
| `Ctrl+Q` | **Select fastest lap**, *"Seleciona a volta mais rápida da saída"* |
| `T` | Tile/Overlay, junta/separa todos os canais de um gráfico |
| `Ctrl+Shift+PgUp` / `PgDn` | próxima / volta anterior |
| `M` / `N` | mostra o maior / menor valor |
| `H` / `Ctrl+H` | oculta o canal selecionado / oculta um arquivo aberto |
| `Z` / `Backspace` / `Ctrl+Backspace` | zoom in / out / desfaz todos os zooms |

> **SUPOSTO.** `Ctrl+E` e `Ctrl+Q` existirem como atalhos de uma tecla é a evidência de que
> **"todas as voltas da saída"** e **"a mais rápida da saída"** são as duas seleções que o
> engenheiro faz o tempo todo, e a apostila D p.18 confirma: vitais se lê com **todas** as
> voltas da saída de uma vez. São dois presets de seleção, não uma funcionalidade avançada.

## 14. Toolset, aquisição, referência e integridade

TS é o software de **comunicação carro ↔ computador** (TS p.5), não de análise. Três coisas dele
importam aqui.

**(a) Sistema travado (MEDIDO, TS p.3):**

> "Ao contrário do MoTeC, **todas as configurações do ICD são travadas**. O sistema da Cosworth
> instalado nos carros foi personalizado com exclusividade para a Porsche Motorsport […] as
> configurações das páginas, alarmes, canais de aquisição e suas frequências **não são
> alteráveis**, pois ficam gravadas em arquivo de Setup que, além de não permitir que estas
> configurações sejam acessíveis, não permite nem que elas sejam visíveis."

Só duas coisas são editáveis (TS p.3 e p.24): **Shift Light** e **diâmetro da roda**.

**(b) Diâmetro da roda é integridade de dado (MEDIDO, TS p.29):**

> "Estes valores são utilizados para calcular a velocidade das rodas, e por consequência, a
> velocidade do carro. **Valores de diâmetro do pneu errados levarão a incoerências nos dados
> gravados.**"

E os cuidados ao mexer (MEDIDO, TS p.3): verificar sempre qual configuração está sendo
modificada · **deixar o piloto e o engenheiro responsável cientes** · conferir mais de uma vez ·
**reverter as alterações no final do fim de semana**.

> **SUPOSTO.** Um parâmetro de configuração do carro que corrompe silenciosamente **velocidade,
> distância e, por consequência, Slip Ratio e todos os canais derivados**. É metadado de
> aquisição que precisa viajar com o arquivo, e é a prova concreta de por que "importar o
> arquivo" não é suficiente: o mesmo `.pds` pode estar certo ou errado dependendo de um número
> que não está no gráfico.

**(c) Volta de referência, três modos (MEDIDO, TS p.13-15):**

| modo | comportamento MEDIDO |
|---|---|
| `Distance Based, Auto Learn` | *"o carro irá utilizar as primeiras voltas no circuito para aprender o traçado. Na primeira volta completa, o sistema aprende o comprimento da pista. Na segunda volta, este comprimento é conferido, e caso esteja com **mais de 5% de diferença**, ele irá medir a distância novamente."* |
| `Learn Fastest Lap` | *"sempre que uma nova volta mais rápida for completada, ela será a volta utilizada como referência"* |
| `Distance Based, PDS File Reference` | envia uma volta salva no computador; *"**A volta mais rápida do arquivo será selecionada automaticamente.**"* |

**Segmentos (MEDIDO, TS p.13):** *"O número «Segments» pode ir de **1 a 128**, e representa a
quantidade de vezes que o «Time Diff» será atualizado durante a volta."*

**E o alerta operacional (MEDIDO, TS p.14):**

> "Clicar neste botão **zera a volta de referência**. Portanto, confira estas configurações e
> clique neste botão **sempre no início do fim de semana**, para não utilizar voltas de
> referência gravadas anteriormente **em outros circuitos e/ou por outros pilotos**."

> **SUPOSTO.** *"Referência de outro circuito"* é exatamente o modo de falha que a plataforma já
> tratou (aviso de circuito divergente no delta). A categoria resolve por **procedimento
> humano no início do fim de semana**, o que significa que o erro acontecia. Um sistema que
> carrega a chave de circuito junto da referência resolve por construção o que ali é
> disciplina.
>
> E os três modos são três **políticas de referência** distintas: adaptativa (melhor volta
> corrente), fixa curada (arquivo externo, a mesma semântica de benchmark que o doc do acervo
> pediu), e aprendizado de traçado. Não é um seletor de volta; é um modo de operação.

**Arquivos do ecossistema Pi (MEDIDO, TS p.23):**

| extensão | função |
|---|---|
| `*.pds` | arquivo de dados baixado do carro |
| `*.toolset` | arquivo de Setup do ICD |
| `*.bmp` | imagem do mapa enviada ao ICD (**800×480**, TS p.21) |
| `*.pwb` | Workbook do Toolbox |
| `*.pxt` | Mapa para o Toolbox |

> **Fecha uma lacuna dos docs anteriores.** O template do acervo é `.pwb` e o mapa de pista do
> Toolbox é `.pxt`, dois formatos proprietários distintos. O doc do acervo lista o `.pwb` como
> pendência por exigir software; **`.pxt` não estava mapeado em lugar nenhum** e é o que carrega
> a delimitação de curvas e setores usada no método da §11.

**Abreviações de sessão do Toolset (MEDIDO, TS p.11), tabela integral:**

| sessão | abreviação |
|---|---|
| Treino Opcional 1 / 2 | `TO1` / `TO2` |
| Treino Livre 1 / 2 | `TL1` / `TL2` |
| Treino Class. Parte 1 / 2 | `Q1` / `Q2` |
| Testes | `ShakeDown` |
| Volta de aquecimento 1 / 2 | `WarmUp1` / `WarmUp2` |
| Corrida 1 / 2 | **`P1`** / **`P2`** |

**Padrão de identificação (MEDIDO, TS p.18)**, campos declarados: **posição da barra
estabilizadora dianteira, traseira e asa · chassis do veículo · (um campo em branco)**.
E TS p.10: *"O comando `<type>` é importante, pois separa os arquivos de «outing» e «engine
test» em pastas diferentes."*

---

# Parte 3, Mecânico × engenheiro (MEC)

## 15. Onde os dois registros se encontram

**MEDIDO, MEC p.26**, e é a linha mais importante do manual do mecânico para este documento:

> "OBS: A ordem dos pneus doados é definida pelo engenheiro. A mesma será utilizada nos
> **checklists**, **arquivos de volta**, **report eletrônico** e deve estar anotada nos pneus do
> respectivo SET."

**Padrão de anotação no pneu físico (MEDIDO, MEC p.26):**

```
#CHASSIS · SET DE PNEUS · RODA (DD; DE; TD; TE) · Nº DE VOLTAS
```

com marcações distintas para **SET DE PNEU CORINGA**, **SET DE PNEU DOADO** e a sequência
Michelin. E MEC p.27: pneu a ser guardado leva **o nº do chassis na banda de rodagem**.

**O handshake explícito (MEDIDO, MEC p.23):**

> "Peça ao seu engenheiro para que lhe informe **o número de voltas que o carro deu no último
> treino**, a fim de fazer a marcação correta nos pneus."

> **SUPOSTO, e fecha um circuito.** O jogo de pneu é o **único identificador que existe
> simultaneamente em quatro lugares**: escrito a mão no pneu, no checklist do mecânico, no nome
> do arquivo de telemetria (`SET 15` no Short Comment, MEDIDO no doc anterior a partir de
> M p.41) e no report eletrônico. E a **contagem de voltas do jogo vem do dado**, do engenheiro
> para o mecânico, por rádio ou verbalmente.
>
> Ou seja: `tyre_set` não é um campo de conveniência, é **a chave estrangeira física** que liga
> o mundo do box ao mundo do dado. O doc do acervo já registrou a decisão do operador de que
> jogo de pneu *"é fundamental e já era para estar dentro"*; esta página mostra **por que**: sem
> ele, a plataforma não consegue nem responder "quantas voltas tem este jogo", que é a pergunta
> que o mecânico faz ao engenheiro a cada sessão.

## 16. O que o mecânico registra, e o que ele não registra

**Quatro checklists distintos (MEDIDO, MEC p.11):** *"Existem listas de conferências para
diferentes momentos do evento. Checklist de **início de evento**, **diário**, **sessões de
pista** e de **final de evento**."* E: *"Existem **diferenças entre os checklists dos carros 3.8
e 4.0** devido a particularidades de cada um."*

**Checklist de sessões, MEDIDO integral, MEC p.14.** Cabeçalho: *"Estes itens devem ser
checados **quando o carro voltar para o box**"*. Códigos de sessão declarados:

```
CP - Clínica de Pilotagem    TE - Treino Extra
TO - Treino Opcional          Q  - Classificatório
TL - Treino Livre             R  - Corrida
```

Colunas do exemplo: `TO1  CP2  TL1  Q1  R1  R2`. Itens, `OK`/`NOK`, **preenchimento
obrigatório**:

```
1  Realizou o treino? (Se sim - OK, Se não - NOK)
2  Houve algum incidente com o carro? (Se não - OK, Se sim - NOK)
3  Desligar o extintor
4  Alinhar o carro na vaga do box e deixar suspenso pelo Air-Jack com calço
5  Limpeza do disco de freio
6  Conferir vazamentos em geral
7  Inspeção visual criteriosa geral do carro
8  Limpeza externa do carro
9  Limpeza de ferramentas e carrinho Beta
```

> **MEDIDO, item 1 e 2.** *"Realizou o treino?"* e *"Houve algum incidente?"* são **por sessão**,
> booleanos, obrigatórios, preenchidos **por carro**.
>
> **SUPOSTO.** Item 1 é a prova de que **sessão existe antes do dado**, a ficha da sessão é
> criada e depois marcada como realizada ou não. A plataforma modela a sessão como consequência
> de um arquivo importado; aqui a sessão é a linha do cronograma, e o arquivo (ou a ausência
> dele) é o que preenche.
>
> Item 2 é o **gatilho** do fluxo de incidente que o doc anterior mapeou no lado do engenheiro
> (formulário com sessão, volta, arquivo de Pi, OS). Quem levanta a bandeira é o mecânico, no
> box, na volta da sessão. E MEC p.22 fecha: *"Descreva para seu engenheiro, qualquer tipo de
> problema e/ou incidente que ocorra com o carro, **de forma que ele possa anotar em seu
> checklist**."*

**Checklist de final de evento, MEDIDO integral, MEC p.15.** Quatro blocos: **Pertences**
(10 itens, incluindo *"Lastros e B.O.P **lacrados**?"*), **Rodas e pneus** (5 itens, incluindo
*"Checar se as rodas do carro conferem com a **numeração do chassi**"* e *"Checar **marcação de
voltas** do pneu, se necessário reforçar"*), **Sistema de rádio** (4 itens, incluindo
*"módulo da câmera VBOX"*) e **Ferramentas** (2 itens). A planilha tem coluna
**"Se NOK foi resolvido?"**.

**Cadeia de custódia (MEDIDO):** o carrinho de ferramentas é assinado na entrega **e** na
devolução por *"Nome do mecânico 1 · Nome do mecânico 2 · **Nome do Analista de Dados 1**"*
(MEC p.8), o analista de dados é parte da equipe do carro, não um serviço externo. Fecha o
ciclo em MEC p.29: *"entregar o mesmo na **sala de engenharia**"*.

**Devolução de pneu (MEDIDO, MEC p.30):** *"engenheiro e mecânico devem ir **juntos**
identificar os pneus a serem guardados e descartados […] devem também assinar a ficha de
recolhimento."*

**O que o mecânico NÃO registra (MEDIDO por ausência).** Varri as 40 páginas: o manual do
mecânico **não contém nenhum canal de telemetria, nenhum valor de vital, nenhum limiar de
alarme e nenhuma referência a arquivo de dados**. A única grandeza numérica de carro que ele
manipula é pressão de pneu, e nem essa é dele: **MEC p.17**, *"Chame um técnico da Michelin
para calibrar os pneus antes do carro entrar no pit lane."*

> **SUPOSTO.** A fronteira é limpa e vale como modelo de permissão: **o mecânico registra
> estado físico e eventos; o engenheiro registra grandeza e interpretação; a Michelin registra
> pressão.** Três papéis, três domínios de escrita, um único objeto (a sessão do carro).

**Procedimento de chuva (MEDIDO, MEC p.21).** É a única página do manual do mecânico com
mudança de **setup** condicionada a condição de pista:

```
Barras estabilizadoras dianteira e traseira na posição 1 (mais mole)
Balanço de freio: a partir do ajuste de pista seca, passar 1 a 2 voltas para a traseira
991 Fase 2, Mudar o modo de ABS para "RAIN"
+ anti-embaçante nos vidros, ventilador em "SCREEN", luzes de neblina, pneus de chuva
```

> **MEDIDO:** *"Lembre seu engenheiro de ajustar o balanço de freio."* O ajuste é do engenheiro;
> o lembrete é do mecânico.
>
> **SUPOSTO.** `weather` na plataforma é um campo de contexto congelado na saída. Aqui, chuva é
> um **estado que muda barras, balanço de freio, modo de ABS e composto de pneu**, ou seja,
> muda o próprio setup contra o qual o dado será lido. Registrar "choveu" sem registrar a
> mudança de setup que a chuva provocou produz duas sessões incomparáveis marcadas como
> comparáveis.

**Números operacionais MEDIDOS no manual do mecânico** (registro por completude; não são de
análise): torque de roda 991 = **500 Nm** (p.24) · **uma** martelada de brita, *"a partir da
segunda martelada o torque será excedido"* (p.24-25) · cilindros de nitrogênio **70 bar no
mínimo** ao final do dia (p.28).

**Comunicação por rádio (MEDIDO, MEC p.18).** Os dois exemplos literais de mensagem ao piloto:

```
"Tom, faltam 5 minutos, 5 minutos"
"Tom, P3 a 2 décimos do P1"
```

> **SUPOSTO.** As duas únicas informações que a categoria considera dignas de interromper um
> piloto em pista são **tempo restante de sessão** e **posição + gap para a referência**.
> Nenhum canal, nenhum vital, nenhuma sugestão de técnica. É um filtro de prioridade brutal e
> gratuito para qualquer HUD ao vivo.

---

# Parte 4, BoP e lastro (BOP)

## 17. O documento é de procedimento físico e não contém nenhum número

**MEDIDO, BOP, página única, integral.** O documento distingue **duas** placas, nomeadas
separadamente no diagrama: **`Lastro`** e **`B.O.P.`**, ambas instaladas nos mesmos furos, com
orientação **Frente / Trás** indicada. Instruções transcritas:

> "Utilizar esses furos para instalar os parafusos de lastro e BOP
> Encostar os parafusos com a mão. Para isso, é importante verificar se a rosca entrou de
> maneira correta.
> Apertar os parafusos com a chave e verificar se a montagem está correta.
> Depois de posicionar as placas de chumbo, colocar a chapa de fechamento, arruela e porcas"

> "Montar as placas de chumbo **com o maior peso em baixo e menor peso em cima**;
> Do lado **esquerdo (piloto)**, colocar **duas** porcas em cima das placas de chumbo;
> Do lado **direito (porta)**, colocar **apenas uma** porca em cima das placas de chumbo;
> A utilização de brita ou parafusadeira é **proibida**;
> Tomar cuidado com os cabos que estiverem próximos à chapa de lastro."

⚠️ **O documento NÃO contém:** massa de lastro, massa de BoP, tabela por carro ou por etapa,
critério de atribuição, peso mínimo do conjunto, nem qualquer referência a etapa ou
temporada. É **um procedimento de montagem, uma página, majoritariamente imagem**. Não
completo nada.

**O que se sabe de BoP vem dos outros documentos, não deste:**

- **MEDIDO, MEC p.15**, checklist de final de evento: *"Lastros e B.O.P **lacrados**?"*, item
  obrigatório. O conjunto é **lacrado** e conferido a cada final de etapa.
- O doc anterior registrou o **rating B.O.P. do piloto** como escala que define categoria no
  Endurance (§3c daquele doc), grandeza **diferente** desta.

> **SUPOSTO, e é a resposta à pergunta que originou a leitura deste PDF.** BoP na Porsche Cup
> são **duas coisas homônimas**:
>
> 1. **Lastro físico de BoP**, placas de chumbo, lacradas, montadas no carro, distintas do
>    lastro comum. Atributo do **carro**, verificado por etapa.
> 2. **Rating B.O.P. do piloto**, escala de classificação de piloto, que no Endurance define
>    categoria de equipe e tempo mínimo/máximo de stint.
>
> A plataforma não tem nenhum dos dois. O primeiro é o que muda o carro entre etapas, e
> **este documento não diz de quanto**. Sem uma tabela de BoP por etapa (não encontrada no
> corpus), o conceito pode ser modelado como **massa declarada + lacre + etapa de vigência**,
> mas os valores teriam que vir do RPP, que o doc anterior já registrou como não encontrado.

---

# O que isto muda no modelo da plataforma

Nada aqui é decisão. É o delta entre o método medido e o que a plataforma faz hoje.

## 1. A ordem da análise é dado, não navegação

Vitais → tempo → aceleração → frenagem → coasting → marcha → curva (D p.2) é uma **sequência
com precondição**: *"não se avalia performance de um carro com problemas"* (D p.18). Hoje o SA
oferece lentes como opções paralelas de menu. A sequência da categoria é um **fluxo com portão**:
se os vitais reprovam, a análise de performance não deveria nem ser oferecida, deveria ser
**bloqueada com o motivo**. É a mesma direção já registrada na memória do repo, agora com fonte.

## 2. Eixo X é regra, não preferência

*"Sempre distância para comparar pilotos; sempre tempo para vitais"* (D p.5, p.18). O eixo
correto é **derivável do que está sendo analisado**. Deixar o toggle livre em todo contexto é
transferir para o amador um erro de método que a categoria trata como erro. Mínimo viável: o
eixo **default por lente**, e um aviso quando se sai dele.

## 3. Volta teórica: existem duas, e uma é ruim

`Eclectic` (*"tempo que o piloto realmente fez"*) × `Rolling Minimum` (*"pouco confiável"*),
D p.25. Se a plataforma mostra "volta teórica", ela precisa dizer **qual das duas**, e o
julgamento da categoria sugere qual delas merece o destaque.

## 4. Agregação por canal, terceira confirmação

`max/min/mean/diff` é o vocabulário da tabela do Pi (D p.12) e da ficha real (doc do acervo).
Duas fontes independentes; hoje é configuração de widget.

## 5. `brake_bias` precisa de `diff`, e agora se sabe por quê

D p.38 × p.39: mesmo sintoma, desfecho oposto, diferença = **mudança feita pelo piloto**. Sem
o delta do canal ao longo da saída, os dois casos são o mesmo gráfico.

## 6. Ápice por raio de curva é implementável hoje

D p.56-58 dá um critério geométrico fechado (raio mínimo × centro da curva, simetria, patamar
de G-LAT) que precisa apenas de **velocidade, G-LAT e curvas delimitadas no mapa**. A
delimitação existe como dado curado no ecossistema Pi (`.pxt`, TS p.23; edição em TB p.27), não precisa ser detectada.

## 7. Subesterço/sobre-esterço é correlação de dois canais, por fase

Volante × G-LAT (D p.59-60), avaliado **separadamente na frenagem, no contorno e na saída**
(D p.54). Não é um número por curva; são até quatro respostas por curva.

## 8. Coasting só vale segmentado

Antes da frenagem = erro; depois = pode ser técnica (D p.42). Um "% de coasting por volta"
mistura os dois.

## 9. Detecção precisa degradar por canal disponível

O mesmo evento tem assinatura em canais diferentes (D p.4, p.31 × p.32). E as falhas de câmbio
(D p.50-53) só se separam com canais auxiliares que dataset de sim/GPS não tem. Isto define
honestamente **o que a plataforma pode prometer por perfil de fonte**, e é o argumento contra
uma detecção que exige o conjunto completo ou não roda.

## 10. Metadado de aquisição corrompe dado silenciosamente

Diâmetro de roda errado ⇒ velocidade, distância e Slip Ratio errados (TS p.29), sem nenhum
sintoma no gráfico. Precisa viajar com o arquivo e ser conferível.

## 11. Referência é um modo, não uma escolha de volta

Três políticas medidas (TS p.13-15): melhor volta corrente · arquivo externo curado ·
aprendizado de traçado. Mais o alerta de referência de outro circuito/piloto (TS p.14), que a
categoria resolve por procedimento e uma plataforma resolve por chave.

## 12. `tyre_set` é chave estrangeira física, não campo

MEC p.23 e p.26: o mesmo identificador vive no pneu, no checklist, no nome do arquivo e no
report; e a **contagem de voltas do jogo flui do engenheiro para o mecânico**. Confirma a
decisão já registrada do operador, e mostra o custo de não ter.

## 13. Sessão existe antes do arquivo

*"Realizou o treino? (Se sim - OK, Se não - NOK)"* (MEC p.14) só faz sentido se a sessão foi
criada antes. Reforça, de outra fonte, a direção do doc do acervo: **o dado entra por sessão,
não por importação**.

## 14. Chuva muda setup, não só o rótulo

MEC p.21: barras para a posição 1, balanço 1-2 voltas para a traseira, ABS em `RAIN`, pneu de
chuva. `weather` como string de contexto marca como comparáveis duas sessões que não são.

## 15. Template é por (tipo de sessão × modelo de carro)

D p.15 e TB p.5-11: template padrão curado, cópia pessoal, e a escolha depende de tipo de
sessão e **principalmente de carro**. Os dois eixos que os docs anteriores apontaram como
ausentes reaparecem aqui, agora determinando qual **lente** se usa.

## 16. Rádio: só duas informações valem interromper o piloto

Tempo restante e posição+gap (MEC p.18). Filtro de prioridade pronto para qualquer HUD ao vivo.

---

# Contradições e descompassos apontados

Nenhum foi resolvido; nenhum documento anterior foi editado.

1. **`TE`, "Treino Extra" ou treino livre?** **MEDIDO, MEC p.14:** `TE = Treino Extra`,
   `TL = Treino Livre`. O doc do acervo lê as abas `CUP#255TE1Out1` / `TE1Out2` como *"o treino
   livre teve duas saídas"*. Pelo código do manual do mecânico, `TE` é **Treino Extra**, sessão
   distinta de `TL`. Aponto; não corrijo o doc anterior.

2. **Corrida: `R` ou `P`?** **MEDIDO, TS p.11 (2014):** Corrida 1 / 2 = **`P1` / `P2`**.
   **MEDIDO, MEC p.14 (2021):** `R = Corrida`, com colunas `R1 R2`. Códigos diferentes para a
   mesma sessão, sete anos de distância. Qual vale em 2026 não se sabe.

3. **Duas taxonomias de sessão, nenhuma idêntica.** TS p.11 tem `ShakeDown`, `WarmUp1/2`,
   `TO1/TO2`, `TL1/TL2`, `Q1/Q2`, `P1/P2`, e **não** tem clínica. MEC p.14 tem `CP`, `TO`,
   `TL`, `TE`, `Q`, `R`, e **não** tem warm-up nem shakedown. O doc do regulamento traz ainda
   uma terceira lista, do cronograma. Três fontes, três conjuntos parcialmente sobrepostos.

4. **Linha de referência ≠ limiar de alarme.** **MEDIDO, D p.19**, explícito. Isto **reclassifica**
   (não resolve) o conflito "óleo 120 °C × 140 °C" registrado no doc anterior (§9): são duas
   grandezas por desenho, não um erro de documento. Continua sem resposta qual valor é qual por
   modelo, D não dá **nenhum** número.

5. **Nomenclatura de arquivo: TS p.10/p.18 (2014) × M p.42-43 (2023).** O doc anterior registrou
   o padrão `CP1.2.1` e o Short Comment `BD 2 BT 6 ASA 3 +G SET 15` do manual do engenheiro V19.
   TS p.18 (2014) declara o padrão de identificação como **posição das barras dianteira/traseira
   e asa + chassis + um campo em branco**, mesma ideia, sem o SET de pneus e sem Gurney. O
   campo de pneu parece ter sido acrescentado entre 2014 e 2023; **não verificado**.

6. **Safra.** D, TB e TS são de 2014 e dizem "GT3 Cup Challenge"; MEC é de 2021 e diz "Carrera
   Cup"; BOP é de 2022. Nada aqui vale como procedimento vigente sem reconferência.

---

# Não lido nesta rodada

**Por decisão de escopo** (pasta `Manuais/Lidos/`, disponíveis, não abertos):

- `ENG210909_V1_RIM_Manual de Utilização dos Rádios.pdf`, rádios.
- `ENG220324_V1_PEA_Verificação do cartão SDHC.pdf`, cartão de mídia.
- `ENG220813_RAC_V1_Procedimento de Digitalização de Checklists.pdf`, **provável ponte entre o
  checklist de papel do mecânico e o report eletrônico**; o mais relevante dos três.
- `ENG220809_V1_RAC_Padrão de Nomenclatura dos Relatórios Eletrônicos.pdf`, já era pendência
  do doc anterior (item 8), continua aberta.
- `ENG230529_V19_HEG_Manual de Pista - Engenheiros.pdf`, **já lido** no doc anterior; não
  reprocessado aqui.

**Por limitação técnica:**

- **Checklists de MEC p.9, p.12 e p.13** (carrinho de ferramentas · início de evento · diário):
  corpo da tabela é **imagem**. Só as colunas `OK`/`N OK` saem como texto. **Não fiz OCR.** São
  três listas de conferência cujos itens permanecem desconhecidos.
- **Todos os gráficos de D** são imagem. Os rótulos de anotação saem como texto (e estão todos
  transcritos acima), mas **nenhum valor de eixo, nenhuma escala e nenhum canal plotado é
  legível**. Onde a apostila só mostra e não escreve, este documento diz que não sabe.
- **BOP** é quase todo imagem; sobraram as legendas, transcritas integralmente na §17.

**Pendências herdadas, ainda abertas:**

- Template `.pwb` do Pi Toolbox v18 e conteúdo dos `.i2wkb` do MoTeC, exigem software
  proprietário.
- **Novo:** o formato `.pxt` (mapa do Toolbox, TS p.23), é o que carrega a delimitação de
  curvas e setores de que o método da §11 depende. Nenhum `.pxt` foi procurado no acervo nesta
  rodada.
- Regulamento Particular da Prova (RPP), onde moram os valores variáveis por etapa, incluindo,
  presumivelmente, o BoP. Não encontrado em nenhuma rodada.

**Vale abrir depois (fora de escopo, uma linha cada):**

- SEGERS, J., *Analysis Techniques For Racecar Data Acquisition*, 2nd Ed, SAE 2014, **a
  bibliografia declarada do método da categoria** (D p.63). Não está no acervo do HD.
- `Information_for_OptimumG_SP_Adv_VDseminar/` (transferência de carga, damper, K&C), citado
  no doc do acervo, nunca aberto.
