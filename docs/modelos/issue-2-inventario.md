# Modelo: declarar a gravação que entrou só com inventário

Issue #2, exceção 3e do E-UC-01. Critério PIL-CT-52, regra PIL-RN-11,
requisitos PIL-RF-03 e PIL-RF-13. Modelo escrito antes do código, como pede
E-RN-06.

## O problema em uma frase

Os leitores `aim_gpk` e `aim_rrk` leem cabeçalho e contagem de registros e não
decodificam canal. A ingestão sabe disso e grava `status = 'parcial'`
(`src/saru_poc/pipeline/ingestao.py:476`). O piloto não recebe essa informação
em lugar nenhum: o relatório sai sem os blocos e o endpoint de estado atribui a
culpa à pista.

## O que muda

Três arquivos de contrato e dois de código. Tudo aditivo: nenhum campo existente
muda de nome, de tipo ou de significado.

### 1. Vocabulário de degradação

`web/src/types/contract.ts`, tipo `MotivoDegradacao`, hoje com sete literais.
Entra o oitavo:

```ts
| "somente_inventario"
```

O validador `src/saru_poc/contrato.py` lê o `.ts` como fonte e monta a união
sozinho, então acrescentar o literal já ensina o validador. Nenhuma linha de
`contrato.py` muda.

### 2. Bloco novo no relatório

Mesma fonte, interface nova e um campo novo em `Relatorio`:

```ts
export interface AmostraDaCaptura {
  arquivos_lidos: number;
  arquivos_com_amostra: number;
}

export interface Relatorio {
  // ... campos de hoje, intactos
  amostra_da_captura: Talvez<AmostraDaCaptura>;
}
```

Disponível quando pelo menos um arquivo da captura materializou série de
amostra. Degradado com motivo `somente_inventario` quando nenhum materializou.
O texto do bloco degradado nomeia os formatos que entraram e diz por quê.

O campo é obrigatório no shape, não opcional. O validador trata campo ausente
como erro, e um campo opcional deixaria passar exatamente o silêncio que este
bloco existe para matar.

### 3. Estado da gravação

`web/src/services/gravacoes.ts`, interface `EstadoDaGravacao`, ganha um campo:

```ts
ingestao: { status: "ok" | "parcial" | "falhou"; motivo: string | null } | null;
```

Nulo enquanto nenhum arquivo foi ingerido. O status sai da tabela `ingestao`,
que já é a fonte. O motivo repete em prosa o que o status resume.

### 4. Onde nasce, no Python

`src/saru_poc/relatorio.py` ganha duas funções e uma linha no dicionário final
de `montar`:

```
arquivos_da_captura(conn, gravacao_id) -> list[(formato_id, suporta_amostra, amostras_escritas)]
amostra_da_captura(arquivos)           -> dict do contrato, disponível ou degradado
```

`arquivos_da_captura` faz uma consulta por gravação, uma linha por arquivo do
bundle, com o maior `amostras_escritas` entre as ingestões daquele arquivo
(a tabela é append-only). O `suporta_amostra` sai do registro de leitores
(`readers.leitor_de`), não de contagem de amostra: um arquivo vazio de um
formato que suporta amostra escreveria zero e não é inventário.

`amostra_da_captura` é pura, recebe a lista e devolve o bloco. É ela que o teste
exercita, sem banco.

### 5. Como chega ao front

`src/saru_poc/api.py`, rota `GET /api/gravacoes/{id}/estado`, ganha a chave
`ingestao` em todas as saídas e um degrau novo na cascata de causa. O degrau
entra antes do degrau da pista, porque inventário é causa mais específica:
quando a captura não tem volta e nenhum arquivo entregou amostra, a resposta
para de culpar a pista e diz que o formato entrou só como inventário.

`GET /api/relatorio/{id}` não muda em nada. O campo novo viaja dentro do
relatório que `montar` já devolve, e `_validado` confere contra o `.ts`.

## Limite conhecido, e é o ponto que precisa de decisão

O critério 1 da issue pede que o relatório de um bundle só com `.gpk` declare o
bloco. Isso não é alcançável hoje e a issue não registra o motivo.

`montar` exige pelo menos uma volta cortada e levanta `ValueError` sem ela
(`relatorio.py:679`). Um `.gpk` sozinho não traz amostra, não traz beacon e não
traz venue, então não há volta, não há relatório e a rota devolve 404. O bloco
novo nunca seria alcançado nesse bundle.

Existe captura real que chega no bloco: um `.ldx` da MoTeC. O leitor dele também
é só de inventário, e mesmo assim os beacons do sidecar cortam volta
(`corte_voltas.py:465`). Essa é a gravação em que o bloco degradado aparece no
relatório.

A divisão fica assim, e é ela que o código implementa:

| Captura | Tem volta | Onde o piloto é avisado |
|---|---|---|
| `.ldx` sozinho, ou qualquer bundle sem amostra mas com beacon | sim | bloco `amostra_da_captura` do relatório |
| `.gpk` ou `.rrk` sozinho | não | campo `ingestao` e degrau novo da cascata em `/estado` |

Fazer `montar` emitir relatório sem volta cortada seria mudança de
comportamento, não campo novo, e não cabe nesta issue.

## Critérios e como o teste prova

| Critério da issue | Teste | Precisa de banco |
|---|---|---|
| 1, bloco degradado com motivo e texto | `test_captura_so_de_inventario_degrada_com_motivo` | não |
| 2, `/estado` traz status parcial e motivo | `test_estado_declara_inventario` em `tests/test_api.py` | sim |
| 3, bundle com amostra não mostra aviso | `test_captura_com_amostra_sai_disponivel` | não |
| 4, teste automatizado dos três | os três acima | parcial |

PIL-CT-52 é provado pelo primeiro e pelo terceiro: a mesma função decide os dois
lados, e o teste fixa o motivo `somente_inventario` e o texto.
