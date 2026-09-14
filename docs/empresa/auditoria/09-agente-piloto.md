# Agente da família Piloto, 2026-09-13

Relatório da sessão que converteu o rascunho de requisitos da PoC na família Piloto, abriu
as issues das exceções do `E-UC-01` e fechou dois testes que a matriz marcava como "a
escrever". Tudo aditivo, em duas branches e dois PRs em rascunho, sem tocar `main` e sem
mexer no clone principal `saru-poc-trackday`.

Worktree: `/home/vitor/Desktop/Motorsport/SARU/saru-poc-pil`.
Repositório: `SaruSysLab/saru-poc-trackday`, dono Lucas Antunes.

## O que foi feito

| Commit | Branch | O que entrou |
|---|---|---|
| `4b18f75` docs(requisitos): requisitos da familia Piloto v1 | `pil/requisitos` | os sete arquivos de `docs/requisitos/` |
| `73d0cb1` docs(requisitos): ligar matriz as issues | `pil/requisitos` | números das issues #2 a #7 na matriz `05` |
| `c0b2d19` test(pista): cobrir a cascata de resolucao de pista | `pil/testes-pista` | `tests/test_resolucao_pista.py`, 14 testes |
| `fc8d219` test(decomposicao): recusar o fechamento do eixo no caso Curitiba | `pil/testes-pista` | 2 testes em `tests/test_decomposicao.py` |

Arquivos criados, todos em `/home/vitor/Desktop/Motorsport/SARU/saru-poc-pil`:

- `docs/requisitos/00-guia-de-leitura.md`, cópia do repositório da empresa
- `docs/requisitos/01-problema-e-objetivos.md`
- `docs/requisitos/02-catalogos.md`
- `docs/requisitos/03-backlog.md`
- `docs/requisitos/04-casos-de-uso.md`
- `docs/requisitos/05-rastreabilidade.md`
- `docs/requisitos/06-validacao.md`
- `tests/test_resolucao_pista.py`

Nenhum arquivo existente foi renomeado, movido ou apagado. O único arquivo pré-existente
alterado é `tests/test_decomposicao.py`, que ganhou duas funções no fim da seção de
fechamento do eixo.

Tamanho do catálogo: 17 requisitos funcionais, 12 não funcionais, 14 regras de negócio,
43 critérios de aceitação e 10 critérios das exceções do `E-UC-01`, 21 histórias.

Convenção de id usada: o sufixo do rascunho da PoC foi preservado, então `RF-07` virou
`PIL-RF-07` e os sufixos dos itens que saíram para outra família ficaram vagos. É o que
deixa Lucas conferir a conversão linha a linha sem um de-para à parte.

## Links

Pull requests, os dois em rascunho:

- PR #8, documentação, `pil/requisitos` contra `main`:
  https://github.com/SaruSysLab/saru-poc-trackday/pull/8
- PR #9, testes, `pil/testes-pista` contra `pil/requisitos`:
  https://github.com/SaruSysLab/saru-poc-trackday/pull/9

Issues, uma por exceção do `E-UC-01` que ainda não tem código ou teste fechando:

| Issue | Exceção | Rótulos | Link |
|---|---|---|---|
| #2 declarar no relatório a gravação que entrou só com inventário | 3e | PIL, tipo:feature, prio:media | https://github.com/SaruSysLab/saru-poc-trackday/issues/2 |
| #3 mostrar ao piloto os canais que ficaram sem mapa | 4e | PIL, tipo:feature, prio:media | https://github.com/SaruSysLab/saru-poc-trackday/issues/3 |
| #4 decodificar o corte de volta do bloco EVNT_B0 do Pi | 5e | PIL, tipo:feature, prio:alta | https://github.com/SaruSysLab/saru-poc-trackday/issues/4 |
| #5 decidir o comprimento do layout de Curitiba | 5f | PIL, tipo:dado, prio:media | https://github.com/SaruSysLab/saru-poc-trackday/issues/5 |
| #6 refinar o instante do corte de volta contra a série de maior taxa | 5i | PIL, tipo:feature, prio:media | https://github.com/SaruSysLab/saru-poc-trackday/issues/6 |
| #7 provar que os sete motivos de bloco sem dado chegam à tela | 7e | PIL, tipo:bug, prio:alta | https://github.com/SaruSysLab/saru-poc-trackday/issues/7 |
| #10 rejeitar ambiguidade grosseira entre venue e GPS | 5g | PIL, tipo:feature, prio:alta | https://github.com/SaruSysLab/saru-poc-trackday/issues/10 |

Rótulos criados no repositório, que não existiam: `PIL`, `tipo:bug`, `tipo:feature`,
`tipo:dado`, `tipo:doc`, `tipo:pesquisa`, `prio:alta`, `prio:media`, `prio:baixa`.

## Medição das dez exceções do E-UC-01

Feita contra `src/` e `tests/` do worktree antes de abrir qualquer issue. Quatro exceções
já tinham teste fechando e não viraram issue.

| Exceção | Estado medido | Virou issue |
|---|---|---|
| 2e dois primários do mesmo formato | fechada por `test_duas_capturas_do_mesmo_formato_nao_fundem` | não |
| 3e leitor só de inventário | código existe (`ingestao.py:476` marca status parcial), relatório não avisa | #2 |
| 4e canal sem unidade provada | contagem `sem_mapa` só existe na tabela `ingestao` (`ingestao.py:254`) | #3 |
| 5e corte dentro do arquivo Pi | nenhum código; `pi_listhead_dat.py:18` declara `EVNT_B0` como descartado no porte | #4 |
| 5f comprimento do layout de Curitiba | guarda existe (`decomposicao.py:141`), teste escrito nesta sessão, decisão de domínio aberta | #5 |
| 5g GPS de outra pista | teste escrito nesta sessão (`test_resolucao_pista.py`), issue #10 aberta para implementar guarda entre venue e GPS | #10 |
| 5h canal de volta que não é contagem | fechada por `test_densidade_rejeita_canal_que_muda_demais` | não |
| 5i corte só por canal a 1 Hz | nenhum código, nenhum teste | #6 |
| 6e setor sem dado | fechada por `test_ideal_e_suprimida_com_setor_sem_dado` | não |
| 7e bloco sem dado | 1 dos 7 motivos do contrato tem teste | #7 |

## A confirmar com Vitor

Cada item é uma pergunta com resposta objetiva. Nenhum avança sem ela, porque responder no
lugar dele seria inventar número. Os oito primeiros também estão em `06-validacao.md` do
worktree; o nono está na issue #10.

1. Curitiba mede 3.220 m no catálogo de layouts e 3.749 m na telemetria, medidos em 67
   voltas. Qual dos dois está certo, ou o catálogo está descrevendo outro layout da mesma
   pista? Sem isso, essas 67 voltas continuam sem decomposição. Issue #5.
2. A faixa de 0,9 a 1,1 para o fator que fecha o eixo de distância no comprimento do layout
   está aprovada? Ela está no código desde 2026-08-29 e no CHECK da migration 012, sem
   aprovação registrada em lugar nenhum.
3. Qual o limiar de queda do G longitudinal que marca início de frenagem? A calibração de
   2026-08-22 achou queda mediana entre 11 e 24 m/s² em 232 voltas com pedal real. Sem o
   número, `PIL-RF-23` (dizer onde freou sem canal de pedal) fica bloqueado.
4. Uma volta é válida por cobertura da pista, sem piso de tempo absoluto? O ADR-0033 do
   `saru-app` propôs isso em 2026-07-27 e nunca foi ratificado.
5. Canal sem unidade provada fica fora do vocabulário canônico? O ADR-0049 propôs; falta
   ratificar para esta família.
6. Duas candidatas dentro do raio de 5,0 km mandam a resolução para o degrau seguinte, em vez
   de escolher a mais próxima? A regra é PIL-RN-16, herdada do ADR-0048, que continua
   proposto. O raio de 5,0 km, esse sim, você aprovou em 2026-08-20.
7. Quando o único canal de volta é de 1 Hz, qual erro de instante é aceitável depois do
   refino contra a série rápida? O rascunho da PoC propôs 0,05 s, sem medição que sustente.
   Issue #6.
8. O piloto de track day precisa registrar pneu e clima da própria bateria, ou isso é só da
   família Equipe? A resposta decide se `RF-14` do rascunho volta para a família Piloto.
9. A que distância entre o venue declarado e a posição GPS o sistema passa a declarar
   divergência? Sem o número dá para declarar; não dá para recusar. Issue #10.

## O que não coube, e por quê

O refino do instante do corte de volta contra a série de maior taxa, a exceção 5i, não foi
escrito. Três razões, na ordem:

1. Ele precisa de dois números que não existem aprovados: a tolerância de erro aceitável e a
   janela de busca em torno do instante grosseiro. A regra `E-RN-02` proíbe entrar com
   valor de física sem aprovação de Vitor e sem a medição que o sustenta.
2. O modelo do refino não existe em `docs/modelos/`, e `E-RN-06` pede o modelo antes do
   código.
3. Um dos critérios da tarefa é não mudar o comportamento das gravações que já cortam bem.
   Provar isso exige uma bateria de regressão contra o acervo real, que não está montado
   nesta máquina.

A tarefa ficou registrada na issue #6 com os critérios de aceitação escritos, incluindo o de
regressão, para quem pegar não ter que redescobrir.

A exceção 5e (decodificar `EVNT_B0` do Pi) estava fora do escopo desta sessão por instrução.
A issue #4 registra a estimativa medida: não cabe em uma semana, e a quebra proposta é medir
e documentar o nó em `docs/pi-evnt-medicao.md` antes de escrever o degrau de corte.

## Verificação

`uv run ruff check` nos dois arquivos tocados:

```
All checks passed!
```

`uv run ruff format --check` nos dois: formatados.

`uv run ruff check .` no repositório inteiro continua acusando os mesmos 66 avisos de antes
desta sessão, nenhum deles nos arquivos tocados. São dívida pré-existente, registrada na
auditoria de 2026-09-12, e não foram corrigidos porque não faziam parte do escopo.

`uv run pytest -q`, depois dos dois commits de teste:

```
280 passed, 144 skipped, 1 warning in 1.01s
```

Antes desta sessão eram 264 passando e os mesmos 144 pulando. Os 16 novos são os 14 de
`tests/test_resolucao_pista.py` e os 2 de `tests/test_decomposicao.py`.

O que não rodou, e por quê: os 144 testes pulados exigem o acervo real de telemetria
montado (`SARU_ACERVO_ROOT`, que aponta para o disco do Lucas) ou o Postgres na porta 5442.
A porta está fechada nesta máquina e subir o banco exige Docker, que estava fora do escopo.
Os testes novos foram escritos de propósito para não depender de nenhum dos dois: o dublê de
banco em memória e o `monkeypatch` da posição do GPS fazem os 14 rodarem em 0,13 s.

## Achados registrados, sem ação nesta sessão

1. `tests/test_pipeline.py` inteiro tem `pytestmark = pytest.mark.skipif` no acervo real. Os
   nove testes dele, entre eles o que fecha a exceção 2e do `E-UC-01`, nunca rodam sem o
   disco do Lucas montado. A garantia existe no papel e não roda em CI, que aliás também não
   existe no repositório.
2. O `fator` do código e a "razão 1,164" do README são inversos um do outro. O código calcula
   comprimento do layout dividido pela distância medida (3.220 / 3.749 = 0,859); o README cita
   3.749 / 3.220 = 1,164. Descrevem a mesma divergência, mas quem ler os dois sem perceber vai
   procurar um valor acima de 1,1 numa mensagem que mostra 0,86. Registrado no docstring do
   teste novo e na issue #5.
3. O repositório não tem `CLAUDE.md`, `.claude/`, CI, `CONTRIBUTING.md`, `CODEOWNERS` nem
   template de PR. A auditoria de 2026-09-12 já propôs os seis itens na seção 8; nenhum foi
   criado aqui, porque quatro deles precisam ser combinados com Lucas antes.

## Correções após revisão

A revisão da entrega achou quatro problemas. Todos corrigidos nas mesmas branches, um commit
por achado, sem force push e com `main` intocada em `59afd77`.

| Commit | Branch | Achado |
|---|---|---|
| `57ca85e` docs(requisitos): abrir a excecao 5g no degrau do alias | `pil/requisitos` | 1 |
| `b9cd8c8` docs(requisitos): separar o raio aprovado da regra de ambiguidade | `pil/requisitos` | 4 |
| `b8b9c8a` merge: trazer as correcoes de documentacao da revisao | `pil/testes-pista` | traz 1 e 4 para a branch de teste |
| `40b9233` test(pista): documentar a falta de guarda entre venue e GPS | `pil/testes-pista` | 1 |
| `7d41501` test(pista): ancorar as guardas de faixa e raio em numero absoluto | `pil/testes-pista` | 2 |
| `61d26e4` test(pista): corrigir a distancia ate Donington para 9.570 km | `pil/testes-pista` | 3 |

### 1. A exceção 5g não estava fechada, e eu disse que estava

Os 3 arquivos GT7 do acervo declaram `venue_declarado = "Autodromo de Interlagos"`
(`src/saru_poc/readers/ld.py:29`). Com venue declarado, `resolver` resolve pelo degrau do
alias e faz `continue`: o degrau GPS nunca roda. `src/saru_poc/pipeline/resolucao_pista.py`
não tem guarda de coerência entre o nome declarado e a posição, enquanto
`tracado.py:12` e `corte_voltas.py:285` têm a mesma guarda para o mesmo caso.

O teste que eu escrevi montava a gravação com metadata vazio e dizia no docstring que cobria
o caso GT7. Ele cobre outra coisa, legítima e necessária (arquivo sem venue, PIL-CT-11), mas
não a que o nome prometia.

Para esses 3 arquivos a pista escolhida está certa: a distância percorrida por volta dá
4.217 m contra 4.309 m de Interlagos, e Donington tem 4.020 m. O defeito não é a pista
escolhida, é a divergência de 9.570 km passar em silêncio na etapa que escolheu a pista,
contra E-RNF-01.

O que foi feito: issue #10 aberta com o modelo de requisito; teste novo
`test_venue_resolve_por_alias_mesmo_com_gps_em_outro_continente` com `xfail(strict=True)`
citando a issue; `05-rastreabilidade.md` trocou "fechada" por "aberta no degrau do alias";
`04-casos-de-uso.md` ganhou o fluxo 1f em PIL-UC-02 e corrigiu o 1e, que afirmava que o
degrau GPS recusa; `02-catalogos.md` corrigiu PIL-CT-56.

Achado colateral registrado na issue #10: o ADR-0048 decidiu que `gt7_ld` fica fora do
degrau GPS por ser placeholder fixo do exportador. A PoC não tem exclusão por formato em
lugar nenhum da etapa 4.

### 2. Duas guardas de borda não pegavam mutação

`test_um_por_cento_dentro_da_faixa_passa_e_um_por_cento_fora_recusa` e
`test_um_metro_dentro_do_raio_resolve_e_um_metro_fora_nao` construíam os pontos a partir das
próprias constantes (`FATOR_MAX * 0.99`, `RAIO_GPS_M - 1`). O docstring prometia pegar
alargamento da faixa e do raio, e o teste andava junto com a mutação.

Medido antes da correção, com a faixa em 0,7 a 1,3 e o raio em 8 km: os dois passavam.
Depois da correção, com a mesma mutação:

```
FAILED tests/test_resolucao_pista.py::test_4999_metros_resolve_e_5001_metros_nao
FAILED tests/test_decomposicao.py::test_fator_1_09_passa_e_1_11_recusa
```

As bordas passaram a ser literais: fator 1,09 aceito e 1,11 recusado, 0,91 aceito e 0,89
recusado, 4.999 m aceito e 5.001 m recusado. Os valores 0,9, 1,1 e 5,0 km são os do código
de hoje. `src/` foi restaurado ao original logo depois da medição, e os dois PRs continuam
sem nenhuma linha de `src/`.

### 3. A distância até Donington estava errada

Eu escrevi 9.400 km. `_distancia_m` sobre as constantes do teste dá 9.569,7 km. O texto
passou a "cerca de 9.570 km, medido com `_distancia_m` sobre as constantes deste módulo".

Três números convivem no repositório para a mesma medida, e nenhum foi alterado:

| Onde | Valor |
|---|---|
| `_distancia_m` sobre as constantes do teste | 9.569,7 km |
| `src/saru_poc/pipeline/tracado.py:16` e `corte_voltas.py:288` | 9.500 km |
| ADR-0048 do `saru-app`, seção Decisão | 9.600 km |

São arredondamentos da mesma medida, os dois primeiros para baixo e o terceiro para cima.
Não vale mudar o código por causa disso, mas vale saber que quem procurar "9.570" no
repositório não acha nada.

### 4. Rastreabilidade contraditória em PIL-RN-06

A matriz registrava PIL-RN-06 como aprovada por Vitor em 2026-08-20, sem pendência, e a
regra juntava numa frase só o raio de 5,0 km e a regra de ambiguidade. O ADR-0048 de origem
está com status "proposto, aguarda ratificação" desde a mesma data, e o que ele registra como
decisão do operador em 2026-08-20 é só o número do raio, com a medição na mesa (espalhamento
de 501 m em 29 arquivos, pista errada mais próxima a 318,8 km). A ambiguidade está na seção
"Regras que NÃO mudam" do ADR, que ninguém ratificou.

As duas foram separadas. PIL-RN-06 ficou com o raio, aprovado, sem pendência. PIL-RN-16 é id
novo, sem correspondente no rascunho da PoC, e carrega a ambiguidade com a pendência de
ratificação. A lição 4 de `06-validacao.md` deixou de dizer que as três regras de calibração
entraram sem aprovação, porque o raio tem aprovação registrada, e nasceu a lição 5: uma
regra aprovada pode carregar junto uma regra que ninguém aprovou. A lista de perguntas para
Vitor passou de sete para oito.

### Verificação depois das correções

`uv run ruff check tests/test_resolucao_pista.py tests/test_decomposicao.py`:

```
All checks passed!
```

`uv run pytest -q tests/test_resolucao_pista.py tests/test_decomposicao.py`:

```
29 passed, 1 xfailed in 0.13s
```

`uv run pytest -q`:

```
280 passed, 144 skipped, 1 xfailed, 1 warning in 1.01s
```

O `xfail` é estrito: se a guarda de coerência entrar sem alguém tirar o marcador, a suíte
passa a acusar `XPASS(strict)` e quebra. É o que obriga a issue #10 a ser fechada junto com
o código.

Os 144 pulados continuam sendo os que exigem o acervo real montado ou o Postgres na porta
5442, nenhum dos dois disponível nesta máquina.

Comentários com o detalhe de cada correção nos dois PRs:
https://github.com/SaruSysLab/saru-poc-trackday/pull/8#issuecomment-5654884108 e
https://github.com/SaruSysLab/saru-poc-trackday/pull/9#issuecomment-5654884199
