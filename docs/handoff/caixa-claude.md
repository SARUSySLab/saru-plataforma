# Caixa de mensagens: Antigravity para Claude Code (repositório saru-plataforma)

Responda aqui, R<n> para M<n>, a mais nova no fim.

## R1, 2026-09-14

Resposta às duas tarefas de leitura e medição do M1.

### 1. Tabela dos sete ADRs de docs/arquitetura/adr/

| id | título | decisão de docs/decisions.md que o motiva | vale após 2026-09-14? |
|---|---|---|---|
| ADR-001 | Adotar estilo Pipes and Filters com Repositório | nenhuma | Sim. O pipeline em filtros puros orquestrado por ingestao.py atende a ingestão de telemetria das cinco famílias da plataforma. |
| ADR-002 | Adotar persistência híbrida com PostgreSQL e DuckDB Parquet | nenhuma | Sim. PostgreSQL armazena dados relacionais (pilotos, sessões, metadados) e DuckDB com arquivos Parquet armazena séries temporais de alta frequência. |
| ADR-003 | Adotar normalização de canais em dois estágios | nenhuma | Sim. Extração inicial preservando nomes originais seguida de mapeamento para vocabulário canônico SARU e conversão para o Sistema Internacional permite suportar múltiplos fabricantes. |
| ADR-004 | Adotar decomposição espacial no eixo de distância por curvatura | nenhuma | Sim. Interpolação no domínio de distância normalizada com detecção geométrica de curvas é essencial para comparação de voltas e identificação de pontos de frenagem. |
| ADR-005 | Adotar processamento assíncrono com degradação graciosa | nenhuma | Sim. Resposta imediata com HTTP 202 Accepted e processamento em segundo plano evita travamento do cliente web e mobile, tratando ausência de sensores secundários. |
| ADR-006 | Adotar resolução de pista em três degraus com bypass para simuladores | 2026-09-13: Piloto virtual de simulador (iRacing, ACC, AC, GT7) é atendido na família Piloto; pista de simulador é resolvida pelo nome do circuito declarado pelo jogo, ignorando coordenadas GPS sintéticas (E-RN-08) | Sim. Mantém os três degraus para autódromos reais (proximidade geográfica, extensão de traçado e setores) e o desvio direto pelo nome de circuito para simuladores. |
| ADR-007 | Adotar classificação explícita de voltas anômalas | nenhuma | Sim. A máquina de estados com rótulos explícitos (NORMAL, IN_LAP, OUT_LAP, AQUECIMENTO, TRAFEGO) evita distorção de voltas ideais sem ocultar dados do piloto. |

Nota sobre as decisões de 2026-09-14: a decisão de 2026-09-14 referente a ADRs determinou a consolidação em ADR único em docs/adr/, portando os sete registros da PoC e vinculando requisitos e decisões formalmente.

### 2. Medição da estrutura do arquivo REF 992.pds (issue #24)

Medição realizada a partir de /tmp/REF_992.pds (descomprimido de ~/gdrive/Trabalho/Porsche_Cup/Docs/Referencias/992.1/REF 992.pds.zst, sem versionar), comparada com a gravação real que abre com sucesso no leitor (P.Piquet000001-1.pds) e com a referência citada no chamado (REF38 - 26ET02.pds).

| Parâmetro | REF 992.1 (REF 992.pds) | Referência F3 que abre (P.Piquet000001-1.pds) | Referência Cup citada (REF38 - 26ET02.pds) |
|---|---|---|---|
| Tamanho do arquivo | 105802306 B (100.90 MB; zst 21157841 B) | 5720056 B (5.45 MB) | 8190779 B (7.81 MB) |
| Offset do dicionário | 103905010 | 5690896 | não encontrado |
| Tamanho do dicionário | 1621224 B | 25944 B | não encontrado |
| Número de canais no dicionário | 2937 canais (de ACT101_Blockierung a warn_start_btn) | 47 canais | não encontrado |
| Offset da tabela de blocos | 105526234 | 5716840 | não encontrado |
| Tamanho da tabela de blocos | 275904 B | 2944 B | não encontrado |
| Número de registros na tabela | 4311 registros de 64 B | 46 registros de 64 B | não encontrado |
| Bytes por amostra medidos | 4 B (float32; 2968 pares consecutivos fecham exatos em 4 B por amostra; canais discretos com 1 B e 2 B) | 8 B (float64 constante) | não encontrado |
| Status no LeitorPiPds | Falha em pi_pds.py:354 | Abre com sucesso (44 canais com dados) | Falha em pi_pds.py:354 |

Diagnóstico detalhado da falha no arquivo REF 992.pds:

1. O leitor localiza o candidato correto de 2937 canais no offset 103905010 com passo de 552 B e nome duplicado em +88 B.
2. Em _ler_tabela (linha 262 de src/saru_poc/readers/pi_pds.py), o leitor exige check1 == check2 == idx + 1. No arquivo 992.1, check2 (offset 60) vale idx + 1 (1, 2, 3...), porém check1 (offset 56) contém o valor 2122. Como check1 difere de check2, _ler_tabela interrompe a leitura na primeira entrada e retorna zero registros.
3. Se a checagem de check1 for ajustada, a invariante de offset em _checar_invariante_offset (linha 286) falha porque o leitor calcula e_anterior.n_amostras * 8 (esperando float64). No 992.1, as amostras têm 4 bytes por ponto (float32), com alguns canais de 1 B e 2 B.
4. Na linha 354, após tentar os candidatos encontrados na janela de 4000000 B, o leitor lança ErroDeLeitura informando que nenhum candidato passou na validação.

Diagnóstico do arquivo REF38 - 26ET02.pds:
O leitor falha neste arquivo porque ele não utiliza o layout de 552 B com duplicata de nome a 88 B de distância (pertence ao lote com layout alternativo de 304 B ou cabeçalho sem duplicação).

## R4, 2026-09-14

Estado verificado em 2026-09-14 11:28 BRT: branch pil/26-pid-unidade-fisica, commit 63918f1 (docs(decisoes): pds table rule approved with PR 34). Entregas das tarefas 1, 2 e 5 do M4 em tabelas. Tarefas 3 e 4 aguardam as respostas de direcao de produto por Vitor.

### 1. Auditoria de docs/requisitos/ e docs/empresa/requisitos/

Analise dos 14 arquivos (7 da Piloto em docs/requisitos/, 7 da empresa em docs/empresa/requisitos/) contra o molde da skill requisitos e as decisoes de docs/empresa/decisions.md.

| arquivo | seção do molde que falta | id sem dono (citado e não definido) | contradição com outro arquivo ou com decisions.md | caminho de código citado que não existe neste repositório |
|---|---|---|---|---|
| docs/requisitos/00-guia-de-leitura.md | Nao previsto no molde oficial da skill (guia de apoio) | Nenhum | L32: ordem antiga das familias (Campeonato em segundo); L39: cita E-RF-01 e E-CT-01 no contexto da familia Piloto | Nenhum |
| docs/requisitos/01-problema-e-objetivos.md | Nenhuma | L146-155: RF-14, RF-15, RF-17, RF-18, RF-20, RF-21, RF-25 citados como itens fora da familia, sem definicao nos catalogos | L13, L87, L116: aponta saru/docs/requisitos/ como destino; L115: cita SaruSysLab/dados_telemetria | L13: saru/docs/requisitos/03-backlog.md; L87: saru/docs/requisitos/01-problema-e-objetivos.md; L93: feat/pds-amostras; L104: Trabalho/SARU/01_ Saru-KB/notas/plano-poc-core-trackday.md; L107: saru-app/docs/execution/2026-08-20-feedback-giuliano-engenheiro.md; L111: saru-docs/docs/produto/personas.md, use-cases.md, mvp.md; L112: saru-app/docs/adr/0033; L113: saru-app/docs/audit/2026-08-22-calibracao-frenagem-por-g.md; L114: SARU/_auditoria/04-poc-trackday.md; L115: SaruSysLab/dados_telemetria; L116: saru/docs/requisitos/02-catalogos.md, 03-backlog.md, 04-casos-de-uso.md |
| docs/requisitos/02-catalogos.md | Nenhuma | L41: PIL-CT-46 citado em PIL-RF-28 mas ausente da tabela de criterios; L127, L129: RN-09, RF-14, RF-15 citados em nota de migracao | L18: aponta saru/docs/requisitos/02-catalogos.md para E-RNF | L7, L14: 01-problema-e-objetivos.md; L18: saru/docs/requisitos/02-catalogos.md; L32: tracado.py (real: src/saru_poc/pipeline/tracado.py); L52, L54, L56, L64: sim_iracing_csv.py, sim_ams2_csv.py, sim_acc_motec.py, sim_gt7_csv.py (saru-app arquivado); L87, L107, L138-166, L185-194: 18 caminhos de teste citados sem prefixo de modulo ou inexistentes |
| docs/requisitos/03-backlog.md | Nenhuma | L7: US-09 citado como rascunho anterior da PoC | L21, L79: aponta saru/docs/requisitos/03-backlog.md; L87: DoR estipula caber em uma semana de sprint (contradiz flexibilizacao de prazo de 2026-09-14) | L6: 02-catalogos.md; L21, L79: saru/docs/requisitos/03-backlog.md; L62, L97: 06-validacao.md; L75: 01-problema-e-objetivos.md |
| docs/requisitos/04-casos-de-uso.md | Nenhuma | Nenhum | L9: aponta saru/docs/requisitos/04-casos-de-uso.md | L4: 03-backlog.md; L9: saru/docs/requisitos/04-casos-de-uso.md; L14: 02-catalogos.md; L108, L112: tracado.py, corte_voltas.py, resolucao_pista.py sem prefixo de pasta; L133: contract.ts (real: web/src/types/contract.ts) |
| docs/requisitos/05-rastreabilidade.md | Nenhuma | L17, L19, L21, L22, L23, L27, L32: issues #2, #3, #4, #5, #6, #7, #10 citadas pertencem a numeracao antiga da PoC, nao as issues #25 a #33 de saru-plataforma | Nenhuma direta; numeracao de issues desatualizada frente a decisao de 2026-09-14 | L22: corte_incremental.py sem prefixo (real: src/saru_poc/pipeline/corte_incremental.py); L23: tracado.py sem prefixo (real: src/saru_poc/pipeline/tracado.py); L24, L27, L62: contract.ts (real: web/src/types/contract.ts); L30: readers/fueltech_csv.py, readers/protune_csv.py (inexistentes); L37: docs/*-medicao.md (inexistente; ha docs/pi-pds-medicao.md); L58, L96: resolucao_pista.py, corte_voltas.py, tracado.py sem prefixo; L111-113: referencias a outros .md sem pasta |
| docs/requisitos/06-validacao.md | Nenhuma | Nenhum | Nenhuma | Nenhum |
| docs/empresa/requisitos/00-guia-de-leitura.md | Nao previsto no molde oficial da skill (guia de apoio) | Nenhum | L32: ordem antiga das familias (Campeonato em segundo); decisao de 2026-09-14 fixou Piloto, Equipe, Engenheiro, Campeonato, Aluno | Nenhum |
| docs/empresa/requisitos/01-problema-e-objetivos.md | Nenhuma | Nenhum | L3: aponta repositorio da empresa separado na fase 2 (superado por saru-plataforma como repositorio unico) | L72: _arquivo/saru-KB/50_company/SARU_MASTER_PRODUTO_NEGOCIOS.md; L73: _arquivo/saru-docs/docs/produto/personas.md; L74: _arquivo/saru-app/docs/execution/2026-08-20-feedback-giuliano-engenheiro.md; L76: saru-poc-trackday/docs/mapa-parsing-dois-motores.md; L77: Trabalho/SARU/01_ Saru-KB/notas/plano-poc-core-trackday.md; L78: _auditoria/00-plano-consolidado.md; L80: Trabalho/SARU/.../pesquisa_realdash_napko_dashauto_integracao_telemetria*.md; L111: dados_telemetria/PARES-VIDEO.md |
| docs/empresa/requisitos/02-catalogos.md | Criterios de aceitacao (secao nomeada como Criterios da empresa E-CT) | Nenhum | L53 (E-RN-06): estipula prazo fixo de uma semana de documentacao e modelagem, revogado na decisao de 2026-09-14 | L4: 02-catalogos.md; L7: 01-problema-e-objetivos.md; L22: docs/fisica/parameters_gt3_cup.py (inexistente; migrou para src/saru_poc/fisica/parametros_gt3_cup.py no PR #6 / branch pil/fisica-parametros-cup); L53: docs/decisions.md (real: docs/empresa/decisions.md); L53: docs/modelos/ (pasta inexistente); L68: 06-validacao.md |
| docs/empresa/requisitos/03-backlog.md | Historias de usuario (tabela de US ausente; so lista epicos E-EP-00 a E-EP-07); tabela detalhada de MVP ausente | Nenhum | L11 (E-EP-00): prazo de uma semana de documentacao e repositorio separado; L20-32: ordem das familias antiga (Campeonato em segundo); L36, L40, L54: sprint de uma semana e prazo fixo de modelagem; L38: um Projects por repositorio (superado pelo monorepo) | L5: 01-problema-e-objetivos.md; L61: 06-validacao.md |
| docs/empresa/requisitos/04-casos-de-uso.md | Nenhuma | Nenhum | Nenhuma | L6: 01-problema-e-objetivos.md; L80: 06-validacao.md |
| docs/empresa/requisitos/05-rastreabilidade.md | Nenhuma | L11, L22: RN-10 da PoC citado na coluna Regra sem registro no catalogo da empresa; L12: RN-01, RN-06, RN-07 da PoC citados sem registro no catalogo da empresa | Nenhuma direta; coluna Tarefa contem a abrir em vez das issues #25 a #33 | L10: saru-poc-trackday/src/saru_poc/readers/ (real: src/saru_poc/readers/); L12: corte_voltas.py (real: src/saru_poc/pipeline/corte_voltas.py); L17: aliases.yaml (real: seeds/aliases.yaml); L18: docs/fisica/parameters_gt3_cup.py (real: src/saru_poc/fisica/parametros_gt3_cup.py na branch PR #6); L22: format.ts (real: web/src/dados/formato.ts); L27: docs/*-medicao.md |
| docs/empresa/requisitos/06-validacao.md | Nenhuma | Nenhum | L13: registro historico de 2026-09-12 que menciona uma semana de documentacao antes de codar | Nenhum |

### 2. Matriz de rastreabilidade conferida

Conferencia de cada linha das matrizes de docs/requisitos/05-rastreabilidade.md e docs/empresa/requisitos/05-rastreabilidade.md.
Destino do codigo docs/fisica/parameters_gt3_cup.py: migrado e renomeado para portugues como src/saru_poc/fisica/parametros_gt3_cup.py (com teste tests/test_parametros_gt3_cup.py) no commit 60974e8 do saru e commit 23f5b0f da branch origin/pil/fisica-parametros-cup (PR #6 da PoC, portado para a issue #32 em saru-plataforma), pendente de merge para main.

| id | caminho citado | existe (sim/não) | caminho real se mudou | issues | ADRs |
|---|---|---|---|---|---|
| E-RF-01 | saru-poc-trackday/src/saru_poc/readers/ (12 leitores) | sim | src/saru_poc/readers/ | #25, #26, #31 | ADR-001 |
| E-RF-02 | pipeline/leitura.py, seeds/aliases.yaml | sim | src/saru_poc/pipeline/leitura.py, seeds/aliases.yaml | #26, #29 | ADR-003 |
| E-RF-03 | pipeline/resolucao_pista.py, corte_voltas.py | sim | src/saru_poc/pipeline/resolucao_pista.py, src/saru_poc/pipeline/corte_voltas.py | #28, #30 | ADR-006, ADR-007 |
| E-RF-04 | tabela ingestao, serie_amostral | sim | migrations/0001_inicial.sql, src/saru_poc/pipeline/ingestao.py, src/saru_poc/storage.py | nenhuma | ADR-001, ADR-002 |
| E-RF-05 | relatorio.py (N0) | sim | src/saru_poc/relatorio.py | nenhuma | ADR-007 |
| E-RF-06 | auth.py, regra de escopo por dono | sim | src/saru_poc/auth.py, src/saru_poc/rotas/auth.py | nenhuma | ADR-002 |
| E-RF-07 | a definir na modelagem | não | a definir | nenhuma | nenhuma |
| E-RF-08 | seeds/tracks.yaml, aliases.yaml | sim | seeds/tracks.yaml, seeds/aliases.yaml | nenhuma | ADR-006 |
| E-RF-09 | docs/fisica/parameters_gt3_cup.py | não | src/saru_poc/fisica/parametros_gt3_cup.py (branch origin/pil/fisica-parametros-cup, PR #6 / issue #32) | #32, #33 | nenhuma |
| E-RNF-01 | pipeline inteiro, MotivoDegradacao | sim | src/saru_poc/contrato.py, web/src/types/contract.ts | #27 | ADR-001, ADR-005 |
| E-RNF-02 | pipeline/ingestao.py, storage.py | sim | src/saru_poc/pipeline/ingestao.py, src/saru_poc/storage.py | nenhuma | ADR-001, ADR-002 |
| E-RNF-03 | processo de revisao | não | processo manual de revisao por Vitor | nenhuma | nenhuma |
| E-RNF-04 | pipeline/leitura.py, format.ts | sim | src/saru_poc/pipeline/leitura.py, web/src/dados/formato.ts | nenhuma | ADR-003 |
| E-RNF-05 | a definir por familia | não | a definir por familia | nenhuma | ADR-005 |
| E-RNF-06 | web/src/blocos/ | sim | web/src/blocos/ | nenhuma | ADR-007 |
| E-RNF-07 | auth.py, .gitignore | sim | src/saru_poc/auth.py, .gitignore | nenhuma | ADR-002 |
| E-RNF-08 | exportacao por dono (a definir) | não | a definir | nenhuma | nenhuma |
| E-RNF-09 | tests/fixtures/, docs/*-medicao.md | sim | tests/fixtures/, docs/pi-pds-medicao.md | #25 | ADR-001 |
| E-RNF-10 | repositorio inteiro | sim | repositorio inteiro | nenhuma | nenhuma |
| PIL-RF-01 | pipeline/recepcao.py, tabelas gravacao e arquivo_bruto | sim | src/saru_poc/pipeline/recepcao.py | nenhuma | ADR-001, ADR-005 |
| PIL-RF-02 | readers/formatos.py | sim | src/saru_poc/readers/formatos.py | nenhuma | ADR-001 |
| PIL-RF-03 | readers/ (12 leitores) | sim | src/saru_poc/readers/ | #25, #26, #31 | ADR-001 |
| PIL-RF-04 | pipeline/ingestao.py, tabela ingestao | sim | src/saru_poc/pipeline/ingestao.py | nenhuma | ADR-001 |
| PIL-RF-05 | pipeline/leitura.py, acervo.py, seeds/aliases.yaml | sim | src/saru_poc/pipeline/leitura.py, src/saru_poc/acervo.py, seeds/aliases.yaml | #29 | ADR-003 |
| PIL-RF-06 | storage.py, tabela serie_amostral | sim | src/saru_poc/storage.py | nenhuma | ADR-002 |
| PIL-RF-07 | pipeline/resolucao_pista.py, pista.py, seeds/tracks.yaml | sim | src/saru_poc/pipeline/resolucao_pista.py, src/saru_poc/pista.py, seeds/tracks.yaml | #30 | ADR-006 |
| PIL-RF-08 | pipeline/corte_voltas.py, corte_incremental.py, tabela volta | sim | src/saru_poc/pipeline/corte_voltas.py, src/saru_poc/pipeline/corte_incremental.py | #28, #32 | ADR-007 |
| PIL-RF-09 | pipeline/decomposicao.py, tracado.py, tabelas | sim | src/saru_poc/pipeline/decomposicao.py, src/saru_poc/pipeline/tracado.py | nenhuma | ADR-004 |
| PIL-RF-10 | relatorio.py, contract.ts | sim | src/saru_poc/relatorio.py, web/src/types/contract.ts | nenhuma | ADR-007 |
| PIL-RF-11 | relatorio.py, api.py rota relatorio | sim | src/saru_poc/relatorio.py, src/saru_poc/api.py | nenhuma | ADR-001 |
| PIL-RF-12 | api.py rota amostras, pipeline/leitura.py | sim | src/saru_poc/api.py, src/saru_poc/pipeline/leitura.py | nenhuma | ADR-002 |
| PIL-RF-13 | contract.ts MotivoDegradacao, relatorio.py | sim | web/src/types/contract.ts, src/saru_poc/relatorio.py, src/saru_poc/contrato.py | #27 | ADR-005 |
| PIL-RF-16 | auth.py, rotas/auth.py, tabela usuario | sim | src/saru_poc/auth.py, src/saru_poc/rotas/auth.py | nenhuma | ADR-002 |
| PIL-RF-23 | pipeline/decomposicao.py | sim | src/saru_poc/pipeline/decomposicao.py | nenhuma | ADR-004 |
| PIL-RF-24 | readers/fueltech_csv.py, readers/protune_csv.py | não | a definir (bloqueado por amostra) | nenhuma | ADR-001 |
| PIL-RF-26 | exportador de relatorio em HTML | não | a definir | nenhuma | nenhuma |
| PIL-RF-27 | readers/ld.py e perfis em acervo.py:85 | sim | src/saru_poc/readers/ld.py, src/saru_poc/acervo.py | #30 | ADR-006 |
| PIL-RNF-01 | pipeline inteiro | sim | src/saru_poc/pipeline/ | #27 | ADR-001, ADR-005 |
| PIL-RNF-02 | pipeline/ingestao.py, storage.py | sim | src/saru_poc/pipeline/ingestao.py, src/saru_poc/storage.py | nenhuma | ADR-001, ADR-002 |
| PIL-RNF-03 | api.py upload em segundo plano | sim | src/saru_poc/api.py | nenhuma | ADR-005 |
| PIL-RNF-04 | config.py SARU_DATA_ROOT, storage.py | sim | src/saru_poc/config.py, src/saru_poc/storage.py | nenhuma | ADR-002 |
| PIL-RNF-05 | tests/fixtures/, docs/*-medicao.md | sim | tests/fixtures/, docs/pi-pds-medicao.md | #25 | ADR-001 |
| PIL-RNF-06 | contrato.py | sim | src/saru_poc/contrato.py | nenhuma | ADR-005 |
| PIL-RNF-07 | auth.py, tabela usuario | sim | src/saru_poc/auth.py, src/saru_poc/rotas/auth.py | nenhuma | ADR-002 |
| PIL-RNF-08 | web/src/blocos/, web/src/gavetas/ | sim | web/src/blocos/, web/src/gavetas/ | nenhuma | ADR-007 |
| PIL-RNF-09 | pipeline/leitura.py, front format | sim | src/saru_poc/pipeline/leitura.py, web/src/dados/formato.ts | nenhuma | ADR-003 |
| PIL-RNF-10 | pipeline/corte_voltas.py | sim | src/saru_poc/pipeline/corte_voltas.py | #32 | ADR-007 |
| PIL-RNF-11 | Dockerfile, railway.json, docs/deploy-railway.md | sim | Dockerfile, railway.json, docs/deploy-railway.md | nenhuma | nenhuma |
| PIL-RNF-12 | repositorio inteiro | sim | repositorio inteiro | nenhuma | nenhuma |

### 5. Inventário do acervo de telemetria

Arquivo gerado: docs/handoff/agy/inventario-telemetria-2026-09-14.tsv (983 KB, 4.580 linhas de dados com caminho, tamanho em bytes, hash md5, logger, extensao, pista, carro, data, sessao e duplicata_de). Todas as hashes conferidas sem varredura no mount do Drive.

Resumo do acervo:
- Total de arquivos: 4.580
- Arquivos unicos: 2.981
- Arquivos duplicados: 1.599 (34,91% de duplicacao)
- Volume total: 15.382,91 MB (15,02 GB)

| Formato | Arquivos totais | Arquivos únicos | Duplicatas | Tamanho (MB) |
|---|---|---|---|---|
| pds | 184 | 71 | 113 | 5.225,59 |
| xrk | 882 | 687 | 195 | 2.606,39 |
| bmsbin | 192 | 96 | 96 | 1.755,41 |
| mf4 | 54 | 54 | 0 | 1.304,92 |
| ld | 236 | 104 | 132 | 1.304,64 |
| gpk | 534 | 340 | 194 | 1.127,76 |
| xrz | 551 | 451 | 100 | 655,67 |
| drk | 766 | 536 | 230 | 615,12 |
| rrk | 698 | 502 | 196 | 402,23 |
| vbo | 29 | 6 | 23 | 123,64 |
| pid | 103 | 25 | 78 | 120,00 |
| csv | 10 | 7 | 3 | 80,02 |
| pwb | 39 | 12 | 27 | 55,10 |
| i2wkb | 179 | 56 | 123 | 6,35 |
| ldx | 123 | 34 | 89 | 0,08 |
| Total | 4.580 | 2.981 | 1.599 | 15.382,91 |
