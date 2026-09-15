# Matriz de rastreabilidade da família Piloto

Este arquivo liga cada requisito ao objetivo que ele serve, à capacidade do núcleo que ele
usa, ao código que o implementa, à issue que o move e ao teste que o prova. É o que se
consulta antes de mudar qualquer linha do sistema.

Versão 1.1, 2026-09-13. Atualizada com a documentação de arquitetura e decisões
registradas em `docs/arquitetura/adr/`.
Status: proposto, aprovado, em andamento, implementado, validado, descartado.

## Requisitos

| Requisito | Tipo | Objetivo | Núcleo | Regra | Componente | Decisão | Issue | Teste | Status |
|---|---|---|---|---|---|---|---|---|---|
| PIL-RF-01 | funcional | PIL-OBJ-06 | E-RF-01 | PIL-RN-05 | `pipeline/recepcao.py`, tabelas gravacao e arquivo_bruto | ADR-001, ADR-005 | | PIL-CT-01, PIL-CT-02, PIL-CT-51 | implementado |
| PIL-RF-02 | funcional | PIL-OBJ-03 | E-RF-01 | PIL-RN-11 | `readers/formatos.py` | ADR-001 | | PIL-CT-03 | implementado |
| PIL-RF-03 | funcional | PIL-OBJ-03 | E-RF-01 | PIL-RN-11 | `readers/` (12 leitores), `relatorio.py::amostra_da_captura` | ADR-001 | #2 | PIL-CT-04, PIL-CT-52 | implementado, exceção 3e declarada no relatório e no `/estado` |
| PIL-RF-04 | funcional | PIL-OBJ-06 | E-RF-04 | PIL-RN-04 | `pipeline/ingestao.py`, tabela ingestao | ADR-001 | | PIL-CT-05, PIL-CT-06 | implementado |
| PIL-RF-05 | funcional | PIL-OBJ-06 | E-RF-02 | PIL-RN-10 | `pipeline/leitura.py`, `acervo.py`, `seeds/aliases.yaml` | ADR-003 | #3 | PIL-CT-07, PIL-CT-53 | implementado, exceção 4e aberta |
| PIL-RF-06 | funcional | PIL-OBJ-06 | E-RF-04 | PIL-RN-04 | `storage.py`, tabela serie_amostral | ADR-002 | | PIL-CT-08 | implementado |
| PIL-RF-07 | funcional | PIL-OBJ-01, PIL-OBJ-02 | E-RF-03 | PIL-RN-01, PIL-RN-06, PIL-RN-16, PIL-RN-17 | `pipeline/resolucao_pista.py`, `pista.py`, `seeds/tracks.yaml` | ADR-006 | #10 | PIL-CT-09, PIL-CT-10, PIL-CT-11, PIL-CT-56 | implementado, com teste próprio desde 2026-09-13 |
| PIL-RF-08 | funcional | PIL-OBJ-01 | E-RF-03 | PIL-RN-08, PIL-RN-15 | `pipeline/corte_voltas.py` (com `refinar_passagens`), `corte_incremental.py`, tabela volta | ADR-007 | #4, #6 | PIL-CT-12, PIL-CT-54, PIL-CT-57, PIL-CT-58 | implementado, exceção 5e aberta e 5i parcial |
| PIL-RF-09 | funcional | PIL-OBJ-01 | E-RF-03 | PIL-RN-03, PIL-RN-07 | `pipeline/decomposicao.py`, `tracado.py`, tabelas tempo_trecho, tracado, subtracado | ADR-004 | #5 | PIL-CT-13, PIL-CT-14, PIL-CT-55 | implementado |
| PIL-RF-10 | funcional | PIL-OBJ-01, PIL-OBJ-02 | E-RF-05 | PIL-RN-02, PIL-RN-03, PIL-RN-12 | `relatorio.py`, `contract.ts` | ADR-007 | | PIL-CT-15, PIL-CT-16, PIL-CT-59 | implementado |
| PIL-RF-11 | funcional | PIL-OBJ-01 | E-RF-05, E-RF-07 | PIL-RN-14 | `relatorio.py`, `api.py` rota relatorio | ADR-001 | | PIL-CT-17 | implementado |
| PIL-RF-12 | funcional | PIL-OBJ-01 | E-RF-05 | | `api.py` rota amostras, `pipeline/leitura.py` | ADR-002 | | PIL-CT-18 | implementado |
| PIL-RF-13 | funcional | PIL-OBJ-02 | E-RF-05 | PIL-RN-01, PIL-RN-11 | `contract.ts` `MotivoDegradacao` (8 motivos), `relatorio.py` | ADR-005 | #2, #7 | PIL-CT-19, PIL-CT-52, PIL-CT-60 | implementado |
| PIL-RF-16 | funcional | PIL-OBJ-06 | E-RF-06 | | `auth.py`, `rotas/auth.py`, tabela usuario | ADR-002 | | PIL-CT-22, PIL-CT-23 | implementado |
| PIL-RF-23 | funcional | PIL-OBJ-05 | E-RF-05 | PIL-RN-13 | `pipeline/decomposicao.py` | ADR-004 | | PIL-CT-30 | em andamento |
| PIL-RF-29 | funcional | PIL-OBJ-06 | E-RF-09, E-RF-08 | | `fisica/parametros_gt3_cup.py`, presets 991.1, 991.2 e 992.1 do 911 GT3 Cup | | #19 | PIL-CT-47, `tests/test_parametros_gt3_cup.py` | parcial: os presets entraram sem validação contra manual e sem proveniência por valor, ver `docs/fisica-parametros-gt3-cup.md` |
| PIL-RF-24 | funcional | PIL-OBJ-03 | E-RF-01 | PIL-RN-11 | a definir: `readers/fueltech_csv.py`, `readers/protune_csv.py` | ADR-001 | a abrir após amostra | PIL-CT-31 | proposto, bloqueado |
| PIL-RF-26 | funcional | PIL-OBJ-01 | E-RF-05 | | a definir | | a abrir | PIL-CT-33 | proposto |
| PIL-RF-27 | funcional | PIL-OBJ-01, PIL-OBJ-03 | E-RF-01 | PIL-RN-17 | `readers/ld.py` e perfis `acc` e `gt7_ld` em `acervo.py:85`; iRacing e Assetto Corsa a definir | ADR-006 | #10 | PIL-CT-44, PIL-CT-45 | parcial: ACC e GT7 leem, iRacing e Assetto Corsa sem leitor |
| PIL-RNF-01 | confiabilidade | PIL-OBJ-02 | E-RNF-01 | PIL-RN-01, PIL-RN-04 | pipeline inteiro | ADR-001, ADR-005 | | PIL-CT-05, PIL-CT-11, PIL-CT-19 | implementado |
| PIL-RNF-02 | confiabilidade | PIL-OBJ-06 | E-RNF-02 | PIL-RN-04 | `pipeline/ingestao.py`, `storage.py` | ADR-001, ADR-002 | | PIL-CT-06, PIL-CT-08 | implementado |
| PIL-RNF-03 | desempenho | PIL-OBJ-01 | própria | | `api.py` upload em segundo plano | ADR-005 | a abrir: medir tempo por gravação | PIL-CT-34 | implementado, meta pendente |
| PIL-RNF-04 | suportabilidade | PIL-OBJ-06 | própria | | `config.py` `SARU_DATA_ROOT`, `storage.py` | ADR-002 | | PIL-CT-35 | a verificar |
| PIL-RNF-05 | suportabilidade | PIL-OBJ-03 | E-RNF-09 | PIL-RN-11 | `tests/fixtures/`, `docs/*-medicao.md` | ADR-001 | a abrir: medição dos 9 leitores sem doc | PIL-CT-36 | parcial |
| PIL-RNF-06 | confiabilidade | PIL-OBJ-02 | E-RNF-01 | | `contrato.py` | ADR-005 | | PIL-CT-37 | implementado |
| PIL-RNF-07 | segurança | PIL-OBJ-06 | E-RNF-07 | | `auth.py`, tabela usuario | ADR-002 | | PIL-CT-22, PIL-CT-23, PIL-CT-38 | implementado |
| PIL-RNF-08 | usabilidade | PIL-OBJ-01 | E-RNF-06 | | `web/src/blocos/`, `web/src/gavetas/` | ADR-007 | a abrir: revisão de rótulos e ordem | PIL-CT-39 | parcial |
| PIL-RNF-09 | restrição de design | PIL-OBJ-02 | E-RNF-04 | PIL-RN-10 | `pipeline/leitura.py`, front `format` | ADR-003 | a abrir: pressão em psi | PIL-CT-07, PIL-CT-40 | implementado para velocidade |
| PIL-RNF-10 | confiabilidade | PIL-OBJ-01 | própria | | `pipeline/corte_voltas.py::refinar_passagens`, constantes `TOLERANCIA_CORTE_S`, `ALERTA_CORTE_S`, `JANELA_ALINHAMENTO_S` e `RESIDUO_MAXIMO_ALINHAMENTO` | ADR-007 | #6 | PIL-CT-41, PIL-CT-58 | parcial: o refino melhora o corte e nunca o piora, e o erro de instante continua sem medição (só resolução) |
| PIL-RNF-11 | restrição de implantação | | própria | | `Dockerfile`, `railway.json`, `docs/deploy-railway.md` | | | PIL-CT-42 | implementado |
| PIL-RNF-12 | restrição de implementação | | E-RNF-10 | | repositório inteiro | | | PIL-CT-43 | implementado |

## Exceções do E-UC-01

Uma linha por exceção do caso de uso da empresa, com o estado medido em 2026-09-13 contra
`src/` e `tests/` deste repositório.

| Exceção | Critério | Requisito | Código que já existe | Teste | Issue | Estado |
|---|---|---|---|---|---|---|
| 2e dois primários do mesmo formato | PIL-CT-51 | PIL-RF-01 | `pipeline/recepcao.py` | `test_duas_capturas_do_mesmo_formato_nao_fundem` | | fechada, com a ressalva de o teste exigir acervo real e Postgres |
| 3e leitor só de inventário | PIL-CT-52 | PIL-RF-03 | `readers/aim_gpk.py`, `readers/aim_rrk.py`, status parcial em `pipeline/ingestao.py:476`, bloco `amostra_da_captura` em `relatorio.py` e degrau novo em `api.py::estado_da_gravacao` | decisão coberta sem banco em `tests/test_relatorio.py`; ponta a ponta em `tests/test_api.py`, que pula sem Postgres | #2 | parcial: relatório e `/estado` implementados, verificação em banco pendente e o critério 1 da issue segue inalcançável (ver `docs/modelos/issue-2-inventario.md`) |
| 4e canal sem unidade provada | PIL-CT-53 | PIL-RF-05 | `pipeline/ingestao.py:254` conta `sem_mapa` | não | #3 | aberta |
| 5e corte dentro do arquivo Pi | PIL-CT-54 | PIL-RF-08 | nenhum | não | #4 | aberta |
| 5f comprimento do layout que não bate | PIL-CT-55 | PIL-RF-09 | `pipeline/decomposicao.py:141` | sim, desde 2026-09-13 | #5 | fechada: Curitiba nominal 3.695 m ratificado por Vitor |
| 5g GPS de outra pista | PIL-CT-56 | PIL-RF-07, PIL-RF-09 | guarda de lugar em `tracado.py:12` e `corte_voltas.py:285`; `resolucao_pista.py` não tem guarda de coerência | corte e traçado sim; resolução de pista em `xfail` estrito desde 2026-09-13 | #10 | aberta no degrau do alias |
| 5h canal de volta que não é contagem | PIL-CT-57 | PIL-RF-08 | `corte_voltas.py::_densidade_plausivel` | `test_densidade_rejeita_canal_que_muda_demais` | | fechada |
| 5i corte só por canal a 1 Hz | PIL-CT-58 | PIL-RF-08 | `corte_voltas.py::refinar_passagens` e `_refinar_corte` | sim, fixture sintética em `tests/test_corte_voltas.py` | #6 | parcial: critérios 1 e 4 fechados, 2 e 3 abertos (ver `docs/modelos/issue-6-refino-corte.md`) |
| 6e setor sem dado | PIL-CT-59 | PIL-RF-10 | `relatorio.py` | `test_ideal_e_suprimida_com_setor_sem_dado` | | fechada |
| 7e bloco sem dado | PIL-CT-60 | PIL-RF-13 | `relatorio.py`, `contract.ts` | 1 dos 7 motivos | #7 | parcial |

## Issues abertas em 2026-09-13

Uma issue por exceção do E-UC-01 que ainda não tem código ou teste fechando. As exceções 2e,
5g, 5h e 6e não entraram porque já têm teste que as fecha. A tabela também carrega issue que
nasce de requisito e não de exceção, como a #19.

| Issue | Título | Exceção | Rótulos |
|---|---|---|---|
| #2 | declarar no relatório a gravação que entrou só com inventário | 3e | PIL, tipo:feature, prio:media |
| #3 | mostrar ao piloto os canais que ficaram sem mapa | 4e | PIL, tipo:feature, prio:media |
| #4 | decodificar o corte de volta do bloco EVNT_B0 do Pi | 5e | PIL, tipo:feature, prio:alta |
| #5 | decidir o comprimento do layout de Curitiba | 5f | PIL, tipo:dado, prio:media |
| #6 | refinar o instante do corte de volta contra a série de maior taxa | 5i | PIL, tipo:feature, prio:media |
| #7 | provar que os sete motivos de bloco sem dado chegam à tela | 7e | PIL, tipo:bug, prio:alta |
| #10 | declarar a divergência entre venue declarado e posição GPS | 5g, no degrau do alias | PIL, tipo:bug, prio:media |
| #19 | usar `ParameterValue` com proveniência por valor ou remover | nenhuma; vem de PIL-RF-29 e PIL-CT-47 | PIL, tipo:doc, prio:media |

A issue #10 ganhou em 2026-09-13 o escopo da regra PIL-RN-17: para gravação de perfil
simulado, a guarda não é declarar a divergência, é não entrar no degrau GPS. É o mesmo caso
GT7, agora com regra aprovada por Vitor.

As issues #5 e #6 dependem de decisão de Vitor e por isso recebem `prio:media` em vez de
`prio:alta`: até a decisão existir, ninguém pode começar sem inventar número.

## Regras e sua aprovação

Regra de física só vale com aprovação de Vitor registrada, com a pergunta concreta e o valor
medido (E-RN-02).

| Regra | Aprovada por | Data | Pendência |
|---|---|---|---|
| PIL-RN-01 a PIL-RN-05 | Lucas e Vitor, no plano | 2026-08-28 | nenhuma |
| PIL-RN-06 raio de 5,0 km | Vitor, com a medição na mesa (espalhamento de 501 m, pista errada mais próxima a 318,8 km) | 2026-08-20 | nenhuma |
| PIL-RN-16 ambiguidade não decide | Vitor, no chat (ADR-0048 ratificado) | 2026-09-13 | nenhuma na regra: ambiguidade repassa ao degrau de extensão |
| PIL-RN-17 simulador resolve pista pelo que o jogo declara | Vitor, no chat, como E-RN-08 do núcleo | 2026-09-13 | nenhuma na regra; guarda de perfil simulado a integrar em `resolucao_pista.py` (issue #10) |
| PIL-RN-07 faixa 0,9 a 1,1 | Vitor, no chat (Curitiba nominal 3.695 m aprovado) | 2026-09-13 | nenhuma: faixa ratificada, Curitiba corrigido, in/out/trânsito classificados |
| PIL-RN-08 volta válida por cobertura | Vitor, no chat (ADR-0033 ratificado) | 2026-09-13 | nenhuma: validade por cobertura espacial e setores, velocidade mínima 20 km/h |
| PIL-RN-10 unidade única por canal canônico | Vitor, no chat (ADR-0049 ratificado) | 2026-09-13 | nenhuma: teste de fatores plausíveis; exclusão se ambíguo |
| PIL-RN-11, PIL-RN-12, PIL-RN-14, PIL-RN-15 | práticas já no código e ratificadas por Vitor | 2026-08-28 a 2026-09-13 | nenhuma |
| PIL-RN-13 limiar de frenagem por G | Vitor, no chat (calibração F10 ratificada) | 2026-09-13 | nenhuma: limiar -3,5 m/s² por 10 m com trail-braking combinado |

## Impacto de mudança

Ao mudar uma linha, listar aqui o que precisa ser revisto.

| Data | Requisito | Mudança | Itens afetados | Quem aprovou |
|---|---|---|---|---|
| 2026-09-13 | todos | criação da versão 1 da família Piloto, a partir do rascunho da PoC de 2026-09-12, dos catálogos da empresa e do código em `main` (59afd77) | nenhum código muda; PIL-CT-30, PIL-CT-31, PIL-CT-33, PIL-CT-40, PIL-CT-41, PIL-CT-52, PIL-CT-53, PIL-CT-54, PIL-CT-58 e seis dos sete motivos de PIL-CT-60 ficam a escrever | pendente: Vitor |
| 2026-09-13 | PIL-RF-07, PIL-RF-09 | PIL-CT-09, PIL-CT-10, PIL-CT-11, PIL-CT-14 e PIL-CT-56 saem de "a escrever" para teste automatizado | `tests/test_resolucao_pista.py` novo; `tests/test_decomposicao.py` acrescido | pendente: Lucas, na revisão do PR |
| 2026-09-13 | PIL-CT-56 | revisão achou que o caso GT7 resolve por alias antes de o degrau GPS rodar, e que a etapa 4 não tem guarda de coerência entre venue e posição. A exceção 5g deixa de constar como fechada | `04-casos-de-uso.md` fluxo 1f de PIL-UC-02; issue #10; teste em `xfail` estrito | pendente: Vitor decidir o limiar da divergência |
| 2026-09-13 | PIL-RF-27, PIL-RN-17 | mudança de núcleo: Vitor ampliou E-RF-01 para logger real ou simulador e criou E-RN-08. A família Piloto passa a atender o piloto virtual, com o mesmo relatório | `01-problema-e-objetivos.md` público e fonte F14; `02-catalogos.md` PIL-RF-27, PIL-RN-17, PIL-CT-44, PIL-CT-45; `03-backlog.md` PIL-US-30 no MVP; issue #10 | Vitor, 2026-09-13 |
| 2026-09-13 | PIL-RN-06 | amadurecimento: a regra de ambiguidade sai de PIL-RN-06 e vira PIL-RN-16, porque o raio de 5,0 km tem aprovação de Vitor e a ambiguidade só tem um ADR proposto | `02-catalogos.md`, tabela de regras; tabela de aprovação desta matriz; `06-validacao.md` pergunta 6 e lição 5 | pendente: Vitor ratificar PIL-RN-16 |
| 2026-09-13 | PIL-RF-05, PIL-RF-07, PIL-RF-08, PIL-RF-09, PIL-RNF-08 | criação dos mocks Desktop PC N0 (piloto trackday) e N1 (pitwall e engenharia) em `docs/mocks/` e especificação de UI em `docs/arquitetura/visao-mocks-ui.md` | `docs/mocks/`, `docs/arquitetura/visao-mocks-ui.md` | Vitor, 2026-09-13 |
| 2026-09-13 | PIL-RF-29 | o módulo de parâmetros do 911 GT3 Cup sai de `saru/docs/fisica/` e entra na PoC como `src/saru_poc/fisica/`, ligando a família Piloto ao E-RF-09. Nenhum valor mudou na migração | `src/saru_poc/fisica/`, `tests/test_parametros_gt3_cup.py`, `docs/fisica-parametros-gt3-cup.md`; a auditoria de proveniência abriu sete perguntas para Vitor | Vitor, 2026-09-13, no chat |
| 2026-09-13 | PIL-RF-03, PIL-RF-13, PIL-CT-52 | o vocabulário `MotivoDegradacao` ganha o oitavo motivo, `somente_inventario`, e o relatório ganha o bloco `amostra_da_captura`. A exceção 3e passa a ser declarada ao piloto, e fica parcial até a verificação em banco | `web/src/types/contract.ts`, `src/saru_poc/relatorio.py`, `src/saru_poc/api.py`, `docs/modelos/issue-2-inventario.md`; issue #2 | pendente: Vitor, na revisão do PR |
| 2026-09-13 | PIL-RF-08, PIL-RNF-10, PIL-CT-41, PIL-CT-58 | o corte por canal de volta de taxa baixa passa a ser realinhado contra a série de velocidade. Tolerância de 0,05 s e alerta de 0,20 s entram como constante nomeada, com a pendência de medição declarada na docstring | `src/saru_poc/pipeline/corte_voltas.py`, `docs/modelos/issue-6-refino-corte.md`; issue #6 | pendente: Vitor, medição no acervo (E-RN-02) e se a tolerância de GPS vale para o canal de volta |
| 2026-09-15 | PIL-RF-05 | a calibração por sessão de `lat_acc`/`lon_acc` passa a valer só para `pi_pid`; os outros formatos voltam a mapear G lateral e longitudinal pelo perfil | `src/saru_poc/pipeline/calibracao.py`, `src/saru_poc/pipeline/ingestao.py`, `tests/test_calibracao_pi_pid.py`; issue #51 | Vitor, 2026-09-15, no chat |
| 2026-09-15 | PIL-RF-03 | leitor `.ld` passa a ler as combinações de tipo `(4, 2)` e `(8, 8)` medidas no acervo; teste de acervo ignora `.ldx` com extensão `.ld` | `src/saru_poc/readers/ld.py`, `tests/test_reader_ld.py`, `docs/motec-ld-medicao.md`; issue #38 | Vitor, 2026-09-15, no chat |
| 2026-09-15 | PIL-RF-03 | inventário do `.pds` passa a nomear bloco pela ligação medida por assinatura; `REF 992.pds` e outra assinatura sem medição passam a ser recusados | `src/saru_poc/readers/pi_pds.py`, `src/saru_poc/readers/pi_pds_ligacao.py`, `tests/test_reader_pi_pds.py`, `docs/pi-pds-medicao.md`; issue #54 | Vitor, 2026-09-15, no chat |
