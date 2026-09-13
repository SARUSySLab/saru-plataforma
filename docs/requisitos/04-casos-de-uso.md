# Casos de uso da família Piloto

Este arquivo é o passo a passo de cada tarefa do piloto que tem desvio ou erro possível no
meio. Tarefa sem desvio fica na história, em `03-backlog.md`.

Versão 1, 2026-09-13. Fonte de cada fluxo: o rascunho da PoC de 2026-09-12, a docstring do
módulo citado e os testes de `tests/`. Os quatro casos de uso são o recorte da família
dentro do caminho principal da empresa, `E-UC-01` (do arquivo ao uso por cada família), em
`saru/docs/requisitos/04-casos-de-uso.md`.

## Onde cada exceção do E-UC-01 aparece aqui

O `E-UC-01` lista dez exceções medidas no acervo. A tabela diz em qual caso de uso desta
família cada uma acontece e qual critério a prova. Os critérios estão em `02-catalogos.md`.

| Exceção do E-UC-01 | Caso de uso | Critério |
|---|---|---|
| 2e dois primários do mesmo formato | PIL-UC-01 | PIL-CT-51 |
| 3e leitor só de inventário | PIL-UC-01 | PIL-CT-52 |
| 4e canal sem unidade provada | PIL-UC-01 | PIL-CT-53 |
| 5e corte de volta dentro do arquivo Pi | PIL-UC-03 | PIL-CT-54 |
| 5f comprimento do layout que não bate | PIL-UC-03 | PIL-CT-55 |
| 5g GPS de outra pista | PIL-UC-02 e PIL-UC-03 | PIL-CT-56, aberta no degrau do alias |
| 5h canal de volta que não é contagem | PIL-UC-03 | PIL-CT-57 |
| 5i corte só por canal a 1 Hz | PIL-UC-03 | PIL-CT-58 |
| 6e setor sem dado | PIL-UC-03 | PIL-CT-59 |
| 7e bloco sem dado | PIL-UC-03 | PIL-CT-60 |

## PIL-UC-01 Importar o cartão do logger

- Requisitos: PIL-RF-01 a PIL-RF-06
- Ator principal: piloto autenticado
- Atores secundários: pipeline em segundo plano
- Antes de começar: piloto logado; arquivos disponíveis no dispositivo
- Ao terminar: uma gravação por captura, com arquivos brutos, linhas de ingestão e séries em
  Parquet; placar nomeando cada arquivo

Quando dá certo:
1. O piloto envia um ou mais arquivos em `POST /api/gravacoes`.
2. O sistema agrupa por pasta e radical: cada captura vira uma gravação; sidecars do mesmo
   radical ficam juntos.
3. O sistema calcula o SHA-256 de cada arquivo e identifica o formato pela assinatura.
4. O sistema responde 202 com o placar e dispara as etapas 2 a 6 em segundo plano.
5. Para cada arquivo, o leitor do formato extrai canais e amostras.
6. O sistema traduz canais para o vocabulário canônico e grava as séries em Parquet.
7. O sistema registra uma linha de ingestão com status, versão do leitor e versão do mapa.
8. `GET /api/gravacoes/{id}/estado` mostra a etapa alcançada.

O que muda conforme a situação:
- 3a. O SHA-256 do arquivo primário já existe: o sistema não cria segunda gravação e aponta
  a existente (PIL-RN-05).
- 3b. O arquivo é cópia comprimida de captura já presente: vira arquivo de backup da mesma
  gravação (`test_copia_comprimida_da_mesma_captura_vira_backup`).
- 5a. O formato tem só leitor de inventário (aim_gpk, aim_rrk): o sistema registra cabeçalho
  e contagem, marca a ingestão como parcial e declara que não há amostra (PIL-RN-11).

Quando dá errado:
- 2e. Dois arquivos primários do mesmo formato com radicais diferentes no mesmo envio: o
  sistema falha alto para os dois em vez de fundir voltas
  (`test_duas_capturas_do_mesmo_formato_nao_fundem`).
- 3e. Nenhuma assinatura casa: o arquivo é recusado com motivo e o resto do bundle segue
  (`test_arquivo_sem_formato_e_recusado_nao_adivinhado`).
- 5e. Formato catalogado sem leitor (bosch_bmsbin): nasce linha de ingestão com status falhou
  e motivo (`test_sem_leitor_vira_linha_de_ingestao_com_motivo`).
- 5f. O leitor lança erro no meio do arquivo: linha de ingestão com status falhou e a
  mensagem; nada do que foi gravado antes é apagado (PIL-RN-04).
- 5g. Canal sem unidade provada no mapa: fica sem `canal_canonico_id` e não vira número na
  tela. O piloto ainda não vê quantos canais ficaram assim (PIL-CT-53).

Critérios: PIL-CT-01 a PIL-CT-08, PIL-CT-51, PIL-CT-52, PIL-CT-53

## PIL-UC-02 Resolver a pista da gravação

- Requisitos: PIL-RF-07, PIL-RF-13, PIL-RF-27
- Ator principal: sistema, na etapa 4
- Atores secundários: piloto, quando perguntado
- Antes de começar: gravação ingerida com séries; catálogo de layouts com coordenada de
  referência
- Ao terminar: `resolucao_pista` com um dos valores alias, gps, perguntado ou
  nao_resolvida; setorização só nos três primeiros

Quando dá certo:
1. O sistema lê o venue declarado no arquivo e procura alias no catálogo.
2. Casamento único: a pista é resolvida por alias.
3. O sistema grava a origem da resolução e libera as etapas 5 e 6.

O que muda conforme a situação:
- 1a. Sem venue ou sem alias: o sistema calcula a posição mediana das amostras com fix de
  GPS e procura layouts a até 5,0 km (PIL-RN-06).
- 1a.1. Exatamente um layout no raio: resolvida por GPS.
- 1a.2. Nenhum layout no raio: a mensagem distingue "o arquivo tem GPS mas nenhuma pista do
  catálogo tem coordenada perto", para alguém cadastrar a coordenada.
- 1a.3. Dois ou mais layouts no raio: ambiguidade não decide; segue para o degrau da
  pergunta.
- 1b. O piloto informa a pista em `POST /api/gravacoes/{id}/pista`: resolvida como
  perguntado, e as etapas 5 e 6 rodam de novo.
- 1c. O venue declarado diverge da escolha do piloto: o arquivo vence (precedente do
  ADR-0048).

Quando dá errado:
- 1e. Sem venue declarado, e com GPS coerente consigo mesmo mas longe de toda referência do
  catálogo: o degrau GPS recusa e diz o motivo; o traçado fica vazio.
- 1f. Com venue declarado que resolve por alias, e GPS longe da referência daquele layout
  (caso das 3 gravações GT7, que declaram "Autodromo de Interlagos" e trazem coordenada de
  Donington, a cerca de 9.570 km): a pista resolve por alias e o degrau GPS nunca roda. Para
  esses 3 arquivos a pista escolhida está certa, porque a distância percorrida por volta dá
  4.217 m contra 4.309 m de Interlagos e Donington tem 4.020 m. O que falta é a divergência
  ser declarada: `tracado.py` e `corte_voltas.py` recusam mais adiante, `resolucao_pista.py`
  não tem guarda de coerência entre venue e posição. Issue #10.
- 1g. A gravação vem de perfil de simulador: a pista sai do que o jogo declara, o degrau GPS
  não roda e nenhum alias novo nasce de posição (PIL-RN-17). É a regra que fecha o 1f para o
  caso GT7, decidida por Vitor em 2026-09-13 e ainda não implementada: `resolucao_pista.py`
  não lê a coluna `perfil_origem.simulado`.
- 3e. Nenhum degrau resolveu: `resolucao_pista = nao_resolvida`, nenhum setor, e o bloco
  "onde ganhar tempo" degrada com motivo sem_venue (PIL-RN-01). Default silencioso é
  proibido.

Critérios: PIL-CT-09, PIL-CT-10, PIL-CT-11, PIL-CT-19, PIL-CT-45, PIL-CT-56

## PIL-UC-03 Gerar o relatório da gravação

- Requisitos: PIL-RF-08, PIL-RF-09, PIL-RF-10, PIL-RF-13
- Ator principal: sistema, nas etapas 5 a 7
- Antes de começar: pista resolvida ou declarada não resolvida
- Ao terminar: `Relatorio` válido contra o contrato, com blocos disponíveis ou degradados

Quando dá certo:
1. O sistema corta as voltas pelo canal de volta, senão pelo beacon, senão pelo GPS.
2. O sistema marca in-lap e out-lap e valida cada volta pela cobertura da pista.
3. O sistema fecha o eixo de distância no comprimento do layout e decompõe cada volta em
   setores, curvas e micro-setores.
4. O sistema calcula melhor volta, volta ideal, perdas por trecho e consistência.
5. O sistema monta N0 a N3 e contexto e valida o shape contra `contract.ts`.
6. A API serve o relatório.

O que muda conforme a situação:
- 1a. Canal de volta com densidade incompatível (valores de 28 a 2572): rejeitado pela guarda
  e o corte usa o próximo degrau (PIL-RN-15).
- 1b. Corte só por canal a 1 Hz: o tempo de volta sai em segundos inteiros e o relatório
  declara a taxa do corte. Refinar contra a série rápida é tarefa aberta (PIL-RNF-10).
- 1c. O arquivo é de logger Pi e traz o corte de volta dentro do arquivo: hoje o leitor não
  decodifica esse bloco e o corte cai para o degrau seguinte. 100 gravações do acervo estão
  sem corte por causa disso.
- 3a. Layout sem catálogo de curva: `por_curva` degrada com sem_catalogo_de_curva e
  `por_micro_setor` serve o N2.
- 3b. Sem GPS: `tracado` e mapa degradam com sem_gps; N0, N1 e N3 seguem completos.
- 4a. Soma dos melhores setores maior que a melhor volta: ideal suprimida e
  `ideal_suprimida = true` (PIL-RN-02).
- 4b. Setor sem dado numa volta: volta não setorizável, fora da ideal (PIL-RN-03).
- 4c. Sem canal canônico de combustível: bloco de consumo degrada com sem_canal_combustivel.

Quando dá errado:
- 3e. Fator de fechamento do eixo de distância fora de 0,9 a 1,1: volta recusada com o
  tamanho do erro (PIL-RN-07). É o caso de Curitiba: 3.749 m medidos contra 3.220 m do
  catálogo, 67 voltas recusadas. Qual dos dois comprimentos está certo é decisão de Vitor.
- 4e. Nenhuma volta válida: o relatório não inventa melhor volta
  (`test_sessao_sem_volta_valida_nao_inventa_melhor`).
- 5e. Shape divergente do contrato: a API devolve 500 e registra a divergência (PIL-RNF-06).
- 7e. Bloco sem dado: aparece marcado com um dos sete motivos e um texto legível, nunca some
  nem mostra número inventado. Seis dos sete motivos ainda não têm teste (PIL-CT-60).

Critérios: PIL-CT-12 a PIL-CT-16, PIL-CT-19, PIL-CT-37, PIL-CT-54 a PIL-CT-60

## PIL-UC-04 Comparar a volta com uma referência

- Requisitos: PIL-RF-11, PIL-RF-12
- Ator principal: piloto
- Antes de começar: gravação analisada com pelo menos uma volta válida
- Ao terminar: perdas por trecho entre a volta analisada e a referência

Quando dá certo:
1. O piloto escolhe a volta analisada na barra de comparação.
2. O piloto escolhe a referência: outra volta da mesma gravação, de outra gravação sua, ou da
   base de referência do sistema.
3. O sistema alinha as duas voltas por distância e calcula as perdas por trecho.
4. O N2 mostra as perdas ordenadas da maior perda ao maior ganho; ganho aparece como perda
   negativa, nunca escondido.
5. O piloto escolhe um trecho no mapa e o N3 abre nele para os dois lados.

O que muda conforme a situação:
- 2a. Referência de outra pista: a comparação por trecho não é oferecida; só N1 lado a lado.
- 3a. Um dos lados sem tempo num trecho: o trecho não vira item
  (`test_trecho_sem_tempo_nos_dois_lados_nao_vira_item`).

Quando dá errado:
- 2e. Analisada e referência são a mesma volta: recusado (PIL-RN-14).
- 2f. Referência sem volta válida: o sistema informa e não compara.

Critérios: PIL-CT-17, PIL-CT-18
