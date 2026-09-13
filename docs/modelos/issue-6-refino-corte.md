# Modelo: refinar o instante do corte contra a série de maior taxa

Issue #6, exceção 5i do E-UC-01. Critérios PIL-CT-58 e PIL-CT-41, requisitos
PIL-RF-08 e PIL-RNF-10. Modelo escrito antes do código, como pede E-RN-06.

## O problema em uma frase

O corte escolhe o canal de volta pela taxa (`corte_voltas.py::_canais_de_volta`).
Quando o único canal de volta da gravação é de 1 Hz, não existe degrau melhor a
escolher, e as 17 gravações do acervo nesse caso entregam tempo de volta em
segundos inteiros. O refino tem que vir de outra série do mesmo arquivo.

## Por que velocidade, e não um evento na posição

A linha de chegada quase sempre fica numa reta, no ponto de maior velocidade. O
sinal de velocidade não tem nenhuma feição local que marque a linha, então
procurar um evento na série rápida em torno do instante grosseiro não tem base.

O que a série rápida sabe é outra coisa: a volta é quase periódica. O mesmo
ponto da pista produz o mesmo trecho de sinal em toda volta. Alinhar a volta k
contra a volta de âncora pelo próprio sinal mede o quanto o instante grosseiro
está deslocado.

Isso também resolve o erro absoluto da âncora sem precisar conhecê-lo. O tempo
de volta é diferença entre instantes. Se o instante refinado da passagem k é o
momento em que o carro está no mesmo ponto de pista em que estava na âncora, a
diferença é o tempo de volta verdadeiro, qualquer que seja o ponto da pista em
que a âncora caiu.

## O método

Função pura, sem banco e sem arquivo:

```
refinar_passagens(instantes, periodo_grosso_s, t_rapido, v_rapido)
    -> (instantes_refinados, erro_instante_s, motivo | None)
```

1. A primeira passagem é a âncora e não se move. Deslocá-la mudaria todos os
   tempos pelo mesmo valor e não melhoraria nenhum.
2. Para cada passagem seguinte, o candidato de deslocamento varre
   `[-periodo_grosso_s, +periodo_grosso_s]` no passo da série rápida. A janela
   sai do período do canal grosseiro, como a issue exige, e não de constante
   escolhida à mão.
3. O critério é o menor erro quadrático entre o sinal rápido da volta k,
   deslocado do candidato, e o sinal rápido da volta âncora, comparados sobre uma
   janela curta ancorada na passagem (`JANELA_ALINHAMENTO_S`, 2 s, a medir no
   acervo).
4. Passagem cujo melhor encaixe deixa resíduo acima de
   `RESIDUO_MAXIMO_ALINHAMENTO` fica com o instante grosseiro e é contada como
   recusada. Deslocar por um encaixe que não encaixa trocaria erro conhecido por
   erro inventado.
5. Sem série rápida, com menos de duas passagens, com sinal constante na janela
   ou com janela que não cabe na série, a função devolve os instantes intactos e
   um motivo. Não refinar é resultado, como em todo o resto desta etapa.

### Por que a janela é curta, e não a volta inteira

A primeira versão comparava a volta inteira, e isso só vale quando todas as
voltas duram o mesmo, que era a hipótese escondida na fixture original. Volta
mais lenta percorre a mesma pista em mais tempo, então o sinal dela sai esticado:
comparar uma volta inteira contra outra de duração diferente alinha o erro de
ritmo em vez da posição na pista.

Medido no contraexemplo sintético, com a versão de volta inteira:

| Cenário | erro do 1 Hz | erro do refino |
|---|---|---|
| voltas idênticas | 0,700 s | 0,000 s |
| variação de 1 a 2 s entre voltas | 0,600 s | 1,350 s |
| volta com parada no meio | 0,400 s | 0,700 s |
| volta de saída mais lenta | 0,600 s | 1,000 s |

Três dos quatro cenários pioravam o que o 1 Hz já entregava. Com a janela curta
mais a guarda de resíduo, nenhum piora, e a tabela nova está no PR.

## Quando o refino entra, e por que ele não mexe em quem já corta bem

O critério 4 da issue é duro: gravação que já corta bem não pode ter o instante
alterado. A porta é a tolerância ratificada.

O refino só roda quando as três condições valem juntas:

1. o corte veio do degrau 1, o canal de volta dentro da amostra;
2. o período desse canal é pior que `TOLERANCIA_CORTE_S`, ou seja, o canal tem
   taxa abaixo de 20 Hz;
3. existe uma série de velocidade com taxa estritamente maior que a do canal.

Beacon de sidecar, beacon nativo do `.xrk` e GPS são outros degraus e não passam
por aqui. Canal de volta de taxa alta (50 Hz do `Beacon Code`, 100 Hz do
`LAP_BEACON`) reprova na condição 2 e sai intacto. É o que fecha o critério 4 por
construção, não por promessa.

## Os dois números, e o que falta neles

```python
TOLERANCIA_CORTE_S = 0.05
ALERTA_CORTE_S = 0.20
```

Ratificados por Vitor em 2026-09-13, item 7 de `docs/requisitos/06-validacao.md`.
Duas pendências, as duas registradas na docstring do módulo:

A ratificação não veio acompanhada de tabela de medição no acervo, que é o que
E-RN-02 pede. Enquanto a medição não existe, os dois ficam em constante nomeada
no topo do módulo, para que a pendência apareça no código e não só no documento.

O texto ratificado fala em "tolerância de sincronização para GPS de 1 Hz contra
série rápida". Esta issue trata do CANAL DE VOLTA a 1 Hz, que é outro degrau da
cascata. O número é o mesmo por analogia, e a analogia é suposição até Vitor
confirmar que a tolerância vale para os dois degraus.

Coerência que vale registrar: 0,05 s é o período de uma série de 20 Hz, que é a
taxa da maioria das séries de velocidade do acervo. A tolerância ratificada e o
teto físico do método coincidem, o que é bom sinal e não substitui a medição.

## O que muda no código

`src/saru_poc/pipeline/corte_voltas.py` ganha as duas constantes, o identificador
de método `METODO_REFINO`, a função pura `refinar_passagens` e um trecho em
`_por_canal` que chama o refino quando a porta abre. O dataclass `Corte` ganha
três campos com valor padrão, então nenhuma construção existente dele muda:
`refinado`, `erro_instante_s` e `motivo_refino`.

Quando o refino entra, `corte.metodo_versao` passa a `METODO_REFINO`. A coluna
`volta.metodo_versao` já existe, então o método do refino fica registrado na
volta sem migração nenhuma, que é o que o critério 1 pede.

## O que fica de fora, e por quê

Os critérios 2 e 3 da issue pedem que o relatório declare o erro de instante e
declare quando não deu para refinar. Isso é superfície de contrato inteira: campo
novo no `Relatorio`, leitura em `relatorio.py` e coluna nova em `volta` para
guardar o erro por gravação. Cai na mesma semana em que a issue #2 já mexe no
contrato, e vale issue própria.

Este modelo e o PR que sai dele fecham os critérios 1 e 4. Os critérios 2 e 3
ficam abertos e declarados, e a issue não é fechada por este PR.

O corte ao vivo (`pipeline/corte_incremental.py`) também fica de fora, e o motivo
é do método, não de prazo: o refino compara a volta k contra a volta âncora
inteira, e ao vivo a volta k ainda não terminou. Refinar ao vivo pede outro
critério, provavelmente refinar a volta k-1 no momento em que a k começa.

## Critérios e como o teste prova

| Critério da issue | Teste | Precisa de banco |
|---|---|---|
| 1, instante refinado e método registrado | `test_refino_recupera_o_instante_verdadeiro` | não |
| 2, erro declarado no relatório | fora deste PR | |
| 3, sem série rápida o corte fica como está e declara | `test_sem_serie_rapida_o_corte_nao_muda_e_diz_por_que` | não |
| 4, quem já corta bem não muda | `test_porta_do_refino_fecha_para_canal_de_taxa_alta` | não |

O teste principal é sintético e tem resposta conhecida por construção: série de
velocidade a 20 Hz com período de volta conhecido, canal de volta a 1 Hz cujas
transições são o instante verdadeiro empurrado para a próxima amostra de 1 Hz,
que é o que um contador de voltas faz. O refino tem que devolver os instantes a
menos de `TOLERANCIA_CORTE_S` do verdadeiro.
