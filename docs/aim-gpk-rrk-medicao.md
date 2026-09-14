# Medicao dos leitores AiM RS2 `.gpk` e `.rrk` (2026-08-29, segunda tentativa)

Continuacao de `docs/aim-rs2-medicao.md` (primeira tentativa, mesmo dia).
Aquela medicao fechou com `.gpk`/`.rrk` como divida declarada (item 2):
"os dois parecem compartilhar um container de blocos com tag ASCII de 4
bytes + versao, mas o layout de cada bloco nao foi decodificado". Esta
tarefa reabriu o problema com uma pista nova: o Saru mandou o banco de
configuracao AiM RaceStudio 2 (`.mdb`, extraido com `mdbtools`). O
resultado: **o framing de container FOI decodificado e validado contra
100% do acervo. A semantica do payload (se carrega GPS ou outra coisa)
CONTINUA nao confirmada** mesmo com o banco de configuracao na mao.

## Procedencia

- Lote medido: `find "$HOME/Desktop/trabalho/clientes/saru/dados_telemetria"
  -name '*.gpk' -o -name '*.rrk'`, em 2026-08-29. `.gpk`: 68 arquivos
  (71 MB). `.rrk`: 67 arquivos (16 MB).
- Banco de configuracao AiM extraido em `DATABASE/`: `Configs_20800AIM.mdb`
  (sensores, unidades, conversoes), `Configs_20800CLI.mdb`
  (`CONF_CANALELOGGER`, config de canal por logger), `DrkTest_DB_20000.mdb`
  (banco de DEMONSTRACAO, `TAB_RUN` com 1 linha so, nao identifica os
  arquivos do acervo real).
- Gabarito geodesico: par `.xrk`/`.gpk`/`.rrk` de mesmo radical de nome
  (`davi_67_A.Senna Kart_a_0277`), pasta `telemetria/kart-guara/`. O `.xrk`
  irmao tem GPS ECEF em centimetros (campos 5/6/7 do chunk `GPS` de 14
  int32, 1-indexado, ou indices 4/5/6 0-indexado: a docstring de
  `xrk.py` erra o indice em 1 posicao, achado desta medicao), convertido
  aqui pra WGS84 com formula iterativa padrao: **lat -15.8257, lon
  -47.9711, altitude ~1081 m**. Bate com "Guara", bairro de Brasilia (nome
  da pasta do acervo), e com a altitude de Brasilia (~1100 m). Serve de
  gabarito confiavel pra validar qualquer decodificacao candidata de GPS
  no `.gpk`/`.rrk` do mesmo radical.
- Ferramentas: scripts Python ad hoc (`struct`, `math`, `collections`), so
  stdlib, rodados via Bash e descartados apos a medicao (nao versionados).
  Nenhum arquivo real do acervo foi copiado pra este repo.

## Item 1: framing de container, `.gpk`

Cada arquivo e uma sequencia de um ou mais SEGMENTOS concatenados. Cada
segmento:

1. Assinatura `PROV\x00\x01` em dois blocos de 16 bytes seguidos (bytes
   0-15 e 16-31; o segundo bloco e byte-a-byte identico ao primeiro,
   incluindo o padding de zeros ate 16 bytes).
2. 48 bytes de cabecalho (offset 32-79) que NAO foram decodificados: lidos
   como float64, saem valores de baixissima entropia / subnormais
   (`~1e-165`, `~-1.8e+307`), nada bate com nenhum campo verificavel do
   `.mdb` nem com data/hora/piloto em texto ASCII.
3. Um "pseudo-registro" de 16 bytes no offset 80: tag `PSOL` + contador
   u32 SEMPRE igual a 256 (validado nos 68/68 arquivos, incluindo em
   segmentos que nao sao o primeiro) + 8 bytes zero.
4. A partir do offset 96, a sequencia real de registros: tag `PSOL` (4
   bytes) + contador u32 (4 bytes) + payload (136 bytes) = **144 bytes por
   registro, tamanho fixo**.

O contador do registro sobe quase sempre de 20 em 20 entre registros
consecutivos (22321 de 22323 passos no arquivo de referencia sobem
exatamente 20, os outros 2 sobem 19: jitter de contagem, nao ruido
aleatorio). Se o contador for tempo em milissegundos (INFERENCIA, o
arquivo nao declara unidade em lugar nenhum), isso da ~50 Hz.

**Validacao**: em 68/68 arquivos `.gpk` do acervo, o numero de bytes
depois do offset 96 (ou do inicio do proximo segmento, quando ha mais de
um) divide EXATAMENTE por 144, e a tag+contador de CADA registro (nao
amostra: todos) bateu. Nenhum `.gpk` do acervo usou mais de 1 segmento,
mas o leitor trata o caso por simetria com o `.rrk` (item 2), que usa.

## Item 2: framing de container, `.rrk`

Mesma familia, container menor pela metade:

1. Assinatura `HEAD\x00\x01`, dois blocos de 16 bytes (offset 0-31).
2. 16 bytes de cabecalho nao decodificados (offset 32-47).
3. Pseudo-registro de 16 bytes no offset 48: tag `NSOL` + contador u32
   sempre 256 + 8 bytes zero.
4. Registros reais a partir do offset 64: tag `NSOL` (4) + contador u32
   (4) + payload (56) = **64 bytes por registro**.

O contador sobe quase sempre de 40 em 40 (o dobro do passo do `.gpk`: se a
mesma unidade valer pros dois, o `.rrk` amostraria a metade da taxa,
~25 Hz).

**Multiplos segmentos, confirmado em uso real** (o `.gpk` nunca usou):
12 dos 67 CAMINHOS de `.rrk` do acervo tem mais de uma ocorrencia da
assinatura dupla `HEAD` dentro do mesmo arquivo fisico. Sao so 3 SESSOES
distintas por conteudo, cada uma salva em ate 4 pastas diferentes do
acervo (ex. `telemetria/superbike/Goiânia/` e
`telemetria/porsche-cup/.../Goiânia/` tem o mesmo arquivo fisico
duplicado), entao 12 caminhos != 12 gravacoes diferentes. Exemplo medido:
`Fabio PittaBMW S1000RR18112022 (2022_12_18 20_23_00 UTC).rrk`, 205632
bytes, 3 segmentos (offset 0, 5696, 205568). O ULTIMO segmento em todos os
casos e so o cabecalho de 64 bytes ate o fim do arquivo, SEM nenhum
registro depois: 0 registros e resultado legitimo (nao e truncamento).

**Validacao**: 67/67 arquivos `.rrk`, framing completo (todo segmento,
toda tag de registro) confere.

## Item 3: tentativa de validacao geodesica do payload do `.gpk`

Usando o par `davi_67_A.Senna Kart_a_0277.gpk`/`.xrk` (gabarito: lat
-15.8257, lon -47.9711, ver Procedencia), tentei decodificar os 136 bytes
de payload de cada registro `PSOL` como GPS, testando (todas as
tentativas foram feitas contra o ARQUIVO INTEIRO, nao so o primeiro
registro, com tolerancia generosa o bastante pra cobrir qualquer ponto ao
longo da volta):

1. **17 float64 do payload como grau decimal de latitude/longitude, offset
   fixo entre registros**: nenhum par (lat, lon) consistente. Busca solta
   por QUALQUER float64 do arquivo perto de -15.8257 (tolerancia 0.01
   grau, ~1 km) achou 25 ocorrencias soltas, mas SEM contrapartida de
   longitude perto de -47.9711 no mesmo registro (a busca de longitude
   achou so 2 ocorrencias, em offsets que nao alinham com nenhuma das
   25 de latitude).
2. **ECEF em metros (float64), x/y/z esperados ~4.11e6 / -4.56e6 / -1.73e6
   m**: zero ocorrencias com tolerancia de 5 km.
3. **ECEF em centimetros (int32), mesma ordem**: 104 ocorrencias soltas de
   "x perto do esperado" com tolerancia de 5 km (~500000 cm), MAS y e z
   nos mesmos offsets nao batem com nada perto do esperado (valores
   arbitrarios tipo 1079981350, -213404224): consistente com coincidencia
   estatistica num espaco de ~800 mil offsets testados, nao com um campo
   ECEF real.
4. Os dois primeiros float64 do payload (offset 0x10/0x18 relativo ao
   registro) tem comportamento suave entre registros vizinhos (um decresce,
   o outro cresce a cada passo), o que os torna candidatos a
   velocidade/rumo (nao posicao absoluta), mas a faixa medida no arquivo
   inteiro (-46.9 a 133.7) e larga demais pra afirmar isso com confianca, e
   nao ha como validar contra o gabarito geodesico (que so cobre posicao,
   nao velocidade/rumo do `.xrk`, que este leitor nao decodifica).

**Nao tentei refazer a busca campo a campo pro `.rrk`**: arquivo pequeno
demais (media 240 KB) pra caber amostra de canal completa por volta, e a
mesma busca contra o `.gpk` (arquivo 10x maior, mais chance de achar
padrao real se existisse) ja deu negativo.

## Item 4: banco de configuracao AiM, a pista nova

A hipotese do enunciado desta tarefa era que a tabela de canal do `.rrk`
poderia morar no `.mdb` (`CONF_CANALELOGGER`), com o binario carregando so
indice numerico. **Nao consegui confirmar**: nenhum campo fixo do registro
`NSOL` (contador, ou qualquer byte de offset fixo testado no payload de
56 bytes) bateu com `ID_CANALELOGGER`, `CODICE_SENS` ou qualquer outra
chave numerica de `CONF_CANALELOGGER` nos poucos loggers que essa tabela
lista. O banco entregue e um `.mdb` de CONFIGURACAO (sensor, calibracao,
unidade por tipo de logger), nao um indice de SESSOES: `DrkTest_DB_20000.mdb`
(que teria `TAB_RUN` com uma linha por gravacao) e banco de DEMONSTRACAO
com 1 linha so, exatamente como o enunciado ja avisava. Sem uma tabela de
sessao real, nao ha como cruzar arquivo do acervo -> logger -> canal
configurado. Fica como divida (item abaixo), nao como leitor especulativo.

## Decisao

**Os dois leitores foram escritos, mas so pro framing de container
confirmado.** `src/saru_poc/readers/aim_gpk.py` (`LeitorAimGpk`,
`formato_id="aim_gpk"`) e `aim_rrk.py` (`LeitorAimRrk`,
`formato_id="aim_rrk"`). Os dois devolvem `Cabecalho.canais == ()`:
nenhum campo do payload tem semantica de canal validada contra o gabarito
geodesico real. E resultado legitimo (mesmo padrao do `.ldx` e do
`aim_drk` deste repo), nao falha de leitura: o arquivo abre, o framing
bate 100% contra o acervo inteiro (nao amostra), so nao ha canal pra
listar.

O que vai em `Cabecalho.bruto` (nao em canal, porque nao e semantica de
canal, e inventario estrutural cru): `n_segmentos`, `n_registros_total`,
`tamanho_registro_bytes`, `registros_por_segmento` (lista por segmento),
`offsets_segmento`, `contador_min`/`contador_max`/
`passo_contador_dominante` (contador cru, sem afirmar unidade).

## Resultado medido

- `.gpk`: **68 de 68 abrem** (100%), framing validado registro a registro
  contra o arquivo inteiro, nao amostra.
- `.rrk`: **67 de 67 abrem** (100%), mesma validacao completa. 12 caminhos
  (3 sessoes distintas, duplicadas em ate 4 pastas) usam mais de 1
  segmento; o ultimo segmento desses e sempre so cabecalho sem registro.
- Validacao geodesica `.xrk` x `.gpk`: **tentada, resultado negativo** (ver
  item 3). O payload nao decodifica como GPS em nenhuma das codificacoes
  testadas (grau float64, ECEF metro float64, ECEF centimetro int32).
- 22 testes automatizados em `tests/test_reader_aim_gpk_rrk.py`, incluindo
  2 que rodam contra o acervo real inteiro (`pytest.skip` se o acervo nao
  estiver montado).

## Divida declarada (nao resolvida nesta tarefa)

1. **Semantica do payload de 136 bytes (`.gpk`) e 56 bytes (`.rrk`)**: o
   framing de registro esta decodificado e validado, mas o CONTEUDO de
   cada registro nao. A hipotese mais forte que sobrou sem confirmar
   (item 3.4) e que os dois primeiros float64 do `.gpk` sejam
   velocidade/rumo, nao posicao. Quem quiser atacar de novo: comparar
   contra velocidade/rumo DERIVADOS do `.xrk` (diferenca de posicao ECEF
   entre chunks `GPS` consecutivos, dividida pelo intervalo de tempo), nao
   contra posicao absoluta, que ja foi descartada aqui.
2. **56 bytes de cabecalho por segmento (offset 32-79 no `.gpk`, 32-47 no
   `.rrk`) nao decodificados**: podem carregar identificador de logger,
   contagem total de registro (o campo em offset 32 do `.rrk` variava
   entre arquivos sem padrao que eu conseguisse fechar no tempo desta
   medicao) ou outra coisa. Nao bloqueia o contrato atual (`canais=()`
   nao depende disso), mas seria o proximo passo pra decodificar semantica
   de sessao (piloto, veiculo, data) se algum dia aparecer confirmavel.
3. **`readers/__init__.py` nao foi tocado** (fora do escopo desta
   tarefa, mesma nota do `aim_rs2.py` anterior): `LeitorAimGpk` e
   `LeitorAimRrk` existem mas nao estao registrados em
   `_registrar_embutidos`. Fica pra quem tiver permissao de editar esse
   arquivo.
4. **Banco `.mdb` nao rendeu cruzamento util** (item 4): a tabela de
   sessao real (`TAB_RUN` de producao, nao a de demonstracao) nao veio
   junto. Se o Saru conseguir exportar o `.mdb` de producao (nao o de
   demonstracao com 1 linha), vale reabrir esta investigacao: e o unico
   caminho que sobrou pra decodificar semantica de canal por indice.

# DECISAO PENDENTE (Lucas)

Nenhuma bifurcacao de arquitetura apareceu nesta tarefa (o contrato
`Cabecalho.canais=()` ja era o comportamento estabelecido pra formato sem
canal confirmado, seguindo `LeitorLdx` e `LeitorAimDrk`). Sem decisao
pendente pra levar a mesa desta vez.
