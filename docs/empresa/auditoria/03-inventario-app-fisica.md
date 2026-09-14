# Inventário de documentação: saru-app e física

Auditoria só leitura de `saru-app/docs` (254 arquivos .md em 20 subpastas, mais 4 arquivos
na raiz de `docs/`), `saru-app` raiz (README, CLAUDE, AGENTS, SPM), `saru-physics-py`,
`saru-physics-jl`, `saru-telemetry-gt7` e `saru-desktop-app`. Nenhum clone foi alterado.
Total de 287 arquivos classificados em `03-inventario-app-fisica.tsv`. Data de referência
das datas de última mudança: 2026-09-12.

## Contagem por tipo

| Tipo | Arquivos |
|---|---:|
| adr | 49 |
| especificacao | 47 |
| auditoria | 38 |
| pesquisa | 28 |
| indice | 27 |
| sessao | 23 |
| prompt | 23 |
| relatorio | 19 |
| plano | 19 |
| runbook | 8 |
| calibracao | 3 |
| outro | 2 |
| brainstorm | 1 |

## Contagem por área

| Área | Arquivos |
|---|---:|
| arquitetura_software | 58 |
| produto | 56 |
| telemetria | 55 |
| processo | 37 |
| ui_marca | 27 |
| dinamica_veicular | 26 |
| dados | 11 |
| fisica (futuro repo) | 6 |
| pneu | 4 |
| outro | 4 |
| ia_agentes | 3 |

## Contagem por estado

| Estado | Arquivos |
|---|---:|
| vigente | 148 |
| obsoleto | 83 |
| stale | 28 |
| rascunho | 13 |
| superado_por_adr_X | 10 |
| duplicado | 5 |

Superado por ADR: 0010→24, 0024→35, 0026 (rotas propostas), 0030→34, 0032 (autorização),
0039 (workbook), 0046 (paleta), 0047 (voltas da bateria, duas vezes, execution e plans).

## Contagem por destino proposto

| Destino | Arquivos |
|---|---:|
| arquivo | 172 |
| poc-trackday/portar | 50 |
| fisica (futuro repo) | 25 |
| empresa/docs/pesquisa | 15 |
| poc-trackday/docs | 13 |
| descartar | 6 |
| empresa/docs/marca | 3 |
| empresa/docs/decisions | 2 |
| empresa/docs/processo | 1 |

172 dos 287 arquivos (60%) ficam só como referência histórica no arquivo do saru-app.
63 arquivos (22%) têm destino ativo na PoC ou na futura biblioteca de física. Nenhum
arquivo recebeu `empresa/docs/arquitetura`: o conteúdo de arquitetura do saru-app é
específico da stack Next.js/NestJS/FastAPI que fica arquivada, não da empresa.

## Os 49 ADRs

`docs/adr/README.md` numera 0001 a 0049 (49 decisões, não 48). O enunciado desta tarefa
citava 48; o índice master do próprio repositório, atualizado em 2026-08-22, lista 49.
Além dos ADRs numerados, a pasta tem três arquivos de apoio: `MASTER_ADR.md` (consolida
só os ADRs 0001-0014, os 15+ não estão resumidos), `RASTREABILIDADE.md` (matriz requisito
↔ ADR ↔ código ↔ endpoint ↔ teste) e o próprio `README.md` (índice).

| ADR | Título | Status declarado | Vale para a PoC | Motivo |
|---|---|---|---|---|
| 0001 | saru-os é um repositório multi-serviço | Aceito | não | PoC é serviço único Python/uv, não multi-serviço containerizado |
| 0002 | Borda NestJS + engine Python; Rust/Tauri deferidos | Aceito | não | arquitetura BFF/NestJS não existe no escopo da PoC |
| 0003 | Convenção de nomes de serviços e do repositório | Aceito, repo resolvido pelo 0022 | não | nomes de serviços do saru-app |
| 0004 | Cache em Redis, nunca SQLite commitado | Aceito, implementado | adaptar | princípio "nunca SQLite" já é regra global do operador; Redis não está definido para a PoC |
| 0005 | Dinâmica transiente SD, 3-DOF no core, dono do 14-DOF | Aceito | adaptar | relevante quando a física voltar como lib separada, não no estado atual da PoC |
| 0006 | Autenticação/identidade na borda NestJS | Aceito, A.1 implementada | não | auth JWT/NestJS é específica do saru-app |
| 0007 | BFF NestJS como camada de orquestração de cálculo | Aceito | não | não há BFF na arquitetura da PoC |
| 0008 | Refresh token com rotação e detecção de reuso | Aceito, A.2 implementada | não | sessão web NestJS específica |
| 0009 | CRM/ERP migram do engine para o BFF NestJS | Aceito, A.2 implementada | não | CRM/ERP fora do escopo da PoC |
| 0010 | Vehicle Setup SSoT e geração 2-tier | Aceito, §1/2 superados pelo 0024 | não | já superado; geração 2-tier é específica do saru-core-jl |
| 0011 | UI Global Context e módulo Trackside | Aceito | não | frontend Next.js/Zustand específico |
| 0012 | Organização GitHub, GitHub Flow e MVP | Aceito | não | topologia de repos antiga, substituída pela decisão de 2026-09-12 |
| 0013 | Contrato de setup é JSON-Schema-only | Aceito | sim | mesmo princípio que a PoC adota: contrato validado no servidor |
| 0014 | Dono único do DDL, migrations do BFF NestJS | Aceito, F1-F3 concluídas | não | não há BFF NestJS na PoC |
| 0015 | Captura GT7 como microserviço poliglota | Aceito | não | fora do escopo declarado da PoC |
| 0016 | Módulo de simuladores e ingestão multi-fonte | Aceito | não | fora do escopo declarado da PoC |
| 0017 | SARU Coach Engine, recomendações causais | Aceito | não | camada de coaching de IA, fora do escopo atual |
| 0018 | Camada de IA via OpenRouter na borda BFF | Aceito | não | depende de um BFF que não existe na PoC |
| 0019 | Frontend do módulo de simuladores, garage/LIVE/REVIEW | Aceito, Fase 1 implementada | não | frontend Next.js específico |
| 0020 | Compartilhamento de workbooks, arquivo JSON v1 | Aceito | não | feature de produto do saru-app |
| 0021 | Guarda de auth no servidor, proxy.ts otimista | Aceito | não | específico de Next.js/NestJS |
| 0022 | Nomenclatura comercial, SARU Hub e SFL | Aceito | não | marca do produto antigo |
| 0023 | Simulação em background via fila BullMQ | Aceito | não | infraestrutura de fila específica do saru-app |
| 0024 | SSoT de veículo interino no saru-physics-py | Aceito, §1/2 superados pelo 0035 | não | já superado; catálogo específico |
| 0025 | Gateway GT7 é headless | Aceito | não | fora do escopo atual da PoC |
| 0026 | IA por fase do loop, Preparar a Evoluir | Aceito | não | navegação de frontend específica |
| 0027 | Espinha do track day, Evento a Sessão a Run | Aceito | adaptar | modelo de domínio útil, mas schema é Postgres/NestJS específico |
| 0028 | Vida útil de componente por km de run | Aceito, execução adiada | não | ERP fora do escopo do analisador |
| 0029 | Pneu como ativo do ERP | Aceito, execução adiada | não | ERP fora do escopo do analisador |
| 0030 | Descongelamento de CRM/ERP | Superseded pelo 0034 | não | já revertido |
| 0031 | CFD fica fora do produto | Aceito | adaptar | decisão de escopo reaplicável, mas a re-tomar para a PoC |
| 0032 | Autorização, ownership por padrão, RBAC só global | Aceito, implementação concluída | adaptar | bom princípio geral, modelo de usuários da PoC ainda não descrito |
| 0033 | Validade de volta por distância e setores | Proposto | sim | validade de volta é central para qualquer analisador de track day |
| 0034 | CRM/ERP ficam pós-MVP | Aceito | não | CRM/ERP fora do escopo da PoC |
| 0035 | Catálogo de veículos servido pela API | Aceito | não | arquitetura de API/BFF específica |
| 0036 | IA do MVP track day, Run Sheet no centro | Aceito | adaptar | conceito de Run Sheet útil, implementação é frontend saru-app |
| 0037 | Motor gráfico de telemetria, uPlot e LTTB | Aceito | sim | performance de gráfico de alta frequência é necessidade direta da PoC |
| 0038 | IA por cadeia de entidades | Proposto | não | navegação de frontend, nunca ratificada |
| 0039 | Workbook como motor único de análise | Aceito pelo operador em 2026-08-04 | adaptar | dashboard configurável é referência útil, código acoplado ao frontend saru-app |
| 0040 | Persistência do LTS migra para o BFF | Proposto, não adotado | não | não adotado nem no saru-app; BFF não existe na PoC |
| 0041 | Túnel público, quick tunnel custo-zero | Proposto | adaptar | técnica genérica de exposição, reaplicável fora do stack |
| 0042 | Borda de exibição converte SI para paddock | Aceito | sim | princípio essencial: SI interno, conversão só na borda |
| 0043 | DuckDB motorsport_telemetry não é fonte de unidade | Proposto | sim | PoC usa DuckDB; bugs documentados são conhecimento direto |
| 0044 | .dlf, rotear pela forma do dado | Proposto | sim | PoC lista .dlf entre os formatos suportados |
| 0045 | Paleta da marca e tema Bento | Superseded pelo 0046 | não | já superado |
| 0046 | Paleta Vanguard e Solar neutro | Proposto | sim | tokens.css e paleta são candidatos diretos a portar, com contraste WCAG medido |
| 0047 | Voltas da bateria vêm do arquivo | Proposto | sim | contar voltas pelo parser em vez de input manual é central para telemetria de track day |
| 0048 | Pista por GPS, cascata de resolução | Proposto | sim | resolução de pista por GPS sem input manual confiável é essencial |
| 0049 | Contrato canônico de canais de telemetria | Proposto | sim | contrato de canal único é exatamente o problema central de um analisador multi-formato |

`docs/adr/0048-pista-por-gps-cascata-de-resolucao.md` tem um erro de metadado: o
front-matter YAML declara `adr: [47]`, deveria ser `[48]`. O corpo e o título do arquivo
usam 0048 corretamente.

Três cadeias de decisão não são duplicação, são revisão registrada em sequência: SSoT de
veículo (0010 a 0024 a 0035), paleta da marca (0045 a 0046) e o próprio ADR-0040, que
trocou de número duas vezes (0035 a 0037 a 0040) por colisão de numeração entre branches
paralelas, documentada nos próprios arquivos.

## Os 25 documentos mais valiosos hoje

Critério: informação medida contra dado real (não suposição), aplicável ao domínio de
telemetria de track day independente de stack, e não redundante com outro item da lista.

| Documento | Destino | Por que |
|---|---|---|
| docs/adr/0049-contrato-canonico-de-canais.md | poc-trackday/portar | contrato único de nome/unidade/sinal de canal, com tripwire sobre aliases.yaml |
| docs/adr/0048-pista-por-gps-cascata-de-resolucao.md | poc-trackday/portar | cascata de resolução de pista testada contra acervo real, raio de 5 km calibrado |
| docs/adr/0044-dlf-duas-variantes-um-leitor-por-forma.md | poc-trackday/portar | duas variantes de .dlf identificadas pela forma do dado, destrava 84 arquivos reais |
| docs/adr/0043-duckdb-motorsport-telemetry-nao-e-fonte-de-unidade.md | poc-trackday/portar | bugs medidos de uma extensão DuckDB que a PoC pode usar ou evitar |
| docs/adr/0042-borda-de-exibicao-unidades-paddock.md | poc-trackday/portar | princípio SI-interno / conversão-na-borda, evita bug recorrente de unidade |
| docs/adr/0047-voltas-da-bateria-vem-do-arquivo.md | poc-trackday/portar | contagem de voltas pelo parser em vez de digitação, com divergência real medida |
| docs/adr/0037-motor-grafico-telemetria-uplot.md | poc-trackday/portar | solução de performance, uPlot mais downsampling LTTB, para telemetria de alta frequência |
| docs/adr/0046-paleta-vanguard-e-solar-neutro.md | poc-trackday/portar | paleta e tokens de marca com contraste WCAG calculado |
| docs/audit/formatos-pi-cosworth-2026-08-04.md | poc-trackday/portar | engenharia reversa em nível de byte de .pid, .dat e .pds |
| docs/audit/2026-08-16-fronteira-de-volta-pid.md | poc-trackday/portar | algoritmo de corte de volta em .pid provado contra o oráculo do próprio logger |
| docs/audit/2026-08-22-calibracao-frenagem-por-g.md | poc-trackday/portar | limiar de frenagem por G calibrado contra 232 voltas com pedal real |
| docs/audit/2026-08-22-censo-canais-acervo.md | poc-trackday/portar | peculiaridades de eixo e sinal por formato, IMU do .dlf rotacionada e invertida |
| docs/architecture/formato-dlf-esparso.md | poc-trackday/portar | spec medida do .DLF esparso do logger AiM, keyframe e deltas |
| docs/architecture/MIGRACAO_TELEMETRIA_ACERVO.md | poc-trackday/portar | inventário do acervo real multi-formato, material de teste para os leitores |
| docs/testing/telemetry-data-inventory.md | poc-trackday/portar | cruza todo o acervo de dados dos repositórios SARU com o que cada formato entrega |
| docs/research/2026-08-22-parsers-canais-fontes-externas.md | poc-trackday/portar | mapa de parsers e licenças por formato, já ligado às ADR 0043 e 0044 |
| docs/research/2026-08-16-como-as-suites-constroem-mapa-de-pista.md | poc-trackday/portar | como MoTeC, Pi Toolbox e AiM RaceStudio geram e ancoram o mapa de pista |
| docs/research/resposta-coordenadas-pistas-2026-08-13.md | poc-trackday/portar | coordenadas WGS84 e comprimento de circuitos-alvo, fonte por linha |
| docs/research/2026-08-16-acervo-porsche-cup-modelo-de-coleta.md | empresa/docs/pesquisa | única evidência de campeonato real medindo a cadeia Etapa a Sessão a Outing a Volta |
| docs/research/relatorio_tecnico_racing_line_minima_curvatura.md | fisica (futuro repo) | fundamentação matemática validada do traçado de mínima curvatura, autoria corrigida |
| docs/analysis/2026-08-12-gap-analysis-hierarquia-motorsport.md | poc-trackday/portar | desenho de dados Etapa/Sessão/Outing/Volta, referência para o schema Postgres da PoC |
| docs/product/matriz-cobertura-vital-2026-08-13.md | poc-trackday/portar | cobertura real de canais vitais de motor por formato do acervo |
| docs/execution/2026-08-19-uiux-fluxo-coleta.md | poc-trackday/portar | laudo de 13 achados de UX de coleta, referência de comportamento a portar |
| docs/execution/2026-08-20-feedback-giuliano-engenheiro.md | poc-trackday/portar | único feedback de uso real de engenheiro de pista sênior |
| docs/execution/2026-08-16-matriz-widget-motor-render.md | poc-trackday/portar | decisão de qual motor de gráfico cada widget usa, referência de arquitetura de renderização |

## Peças portáveis do saru-app para a PoC

O código, não só a documentação, tem peças que a PoC deveria absorver ou usar como
referência direta. Caminhos relativos à raiz de `saru-app`.

Leitores de formato de telemetria, em
`services/telemetry-api/saru_lapanalyzer/infra/datasources/`: `xrk_file.py`, `vbo_file.py`,
`ld_file.py`, `ldx_reader.py`, `dlf_file.py`, `pid_file.py`, `drk_file.py`,
`listhead_dat_file.py`, mais os leitores de simulador (`sim_gt7_csv.py`, `sim_acc_motec.py`,
`sim_ams2_csv.py`, `sim_iracing_csv.py`) e de exportação real (`real_aim_csv.py`,
`real_windarab_csv.py`, `real_wintax_csv.py`, `track_addict_csv.py`, `xlsm_file.py`). Cobrem
boa parte da lista de formatos da PoC (xrk, vbo, ld, ldx, dlf, pid), faltando os leitores
de aim rs2/gpk/rrk, mf4 e bosch bmsbin, que a pesquisa em `docs/research/` já mapeou mas o
código não implementou.

Mapeamento de canal para nome canônico:
`services/telemetry-api/saru_lapanalyzer/infra/mapping/aliases.yaml` (1736 linhas, unidade
canônica documentada linha a linha, validada contra arquivo .ld bruto) e
`channel_mapper.py` no mesmo diretório.

Cascata de resolução de pista por GPS, ADR-0048:
`services/telemetry-api/saru_lapanalyzer/domain/track_map.py`,
`infra/mapping/track_config.py` e o teste `tests/test_track_resolution.py`.

Tokens de marca e paleta, ADR-0046: `services/frontend/src/app/tokens.css` (391 linhas,
com os dois temas Vanguard e Solar e os valores HSL calculados) e o espelho
`services/frontend/src/lib/channelColors.ts`.

Contrato canônico de canais, ADR-0049: `shared/proto/telemetry-channels.json` e
`shared/proto/telemetry-formats.json`. Contrato de setup de veículo, ADR-0013:
`services/frontend/src/features/sa/contract.ts` (174 linhas).

Seed de dados de desenvolvimento: `services/telemetry-api/tools/seed_dev_sessions.py`.

Migrations de schema, dono único do DDL pelo ADR-0014:
`services/api/src/migrations/` (26 arquivos TypeORM, cobrem auth, multitenancy, layouts
de usuário e tabelas de engine).

Testes de referência para portar junto com os leitores:
`services/telemetry-api/tests/` (inclui `test_track_resolution.py` e
`test_saru_gt7_csv.py`), `services/api/test/`, `services/frontend/tests/`.

## Duplicações internas

`docs/decisions/` e `docs/adr/` não duplicam conteúdo. O primeiro é o fluxo de pauta e
ratificação que antecede um ADR; o segundo é a decisão formal e imutável. A distinção está
documentada em `docs/decisions/README.md`.

`docs/plans/` e `docs/execution/` sobrepõem parcialmente. `docs/plans/gaps-trackday-espinha-2026-07.md`
origina `docs/plans/sessoes-reforma-frontend-2026-07.md` e reaparece em
`docs/execution/2026-08-14-plano-outing.md` e `docs/execution/2026-08-16-cerimonia-voltas-derivadas.md`.
`docs/plans/mvp-higiene-arquitetura-plano-acao.md` mais `mvp-higiene-arquitetura-seguimento.md`
é o plano-mãe que `docs/plans/fila-de-ataque-2026-07-29.md` executa item a item.

Dentro de `docs/architecture/`, `vehicle-setup-sot.md` virou o ADR-0010 e foi superado
pelo ADR-0024; `rotas-propostas-sa-sfl-2026-07-28.md` tem front-matter "superseded" pelos
ADR-0026 e ADR-0027; `telemetria-sot-e-ingestao-2026-07-28.md` se declara mera reorganização
de `MIGRACAO_TELEMETRIA_ACERVO.md`.

Dentro de `docs/audit/`, `frontend-analise-e-fluxo-2026-07-25.md` está marcado como
superado por `frontend-sweep-2026-08-02.md` e por `2026-08-16-passeio-hub-logado.md`;
`UIUX_AUDIT_2026-07-15.md` está marcado como superado pelo mesmo `2026-08-16-passeio-hub-logado.md`.
`2026-08-22-catalogo-canais-acervo.md` e `2026-08-22-censo-canais-acervo.md` medem o mesmo
lote de arquivos no mesmo dia, por ângulos diferentes (estatística completa contra
peculiaridade física); candidatos a fundir num único documento ao portar.

Dentro de `docs/research/`, três pares são duplicata direta, já marcados no TSV: `Otimização
de Traçado de Corrida.md` é a versão bruta de `relatorio_tecnico_racing_line_minima_curvatura.md`;
`pesquisa-formatos-pi-cosworth-windarab-ground-truth-2026-08-08.md` sobrepõe `Decodificação
de Telemetria Automotiva.md`; `pesquisa_ux_telemetria_bibliotecas_graficos.md` duplica
`Pesquisa UX Telemetria e Gráficos.md`; e `resposta-coordenadas-pistas-longa-2026-08-13.md`
é a versão discursiva de `resposta-coordenadas-pistas-2026-08-13.md`.

Dentro de `docs/product/`, quatro documentos são fotografias de gap ou estado do hub em
datas diferentes sem marcação de substituição entre si:
`matriz-gaps-release-hub.md`, `MVP-BETA-SPEC.md`, `programa-produto-mvp-2026-08-13.md` e
`gaps-frontend-2026-08-08.md`.

## Repositório fora do escopo desta auditoria

`saru-app/CLAUDE.md` e vinte outros arquivos de `saru-app/docs` citam `saru-docs` como
fonte de verdade de marca e pesquisa de mercado (paleta medida, identidade visual
consolidada, benchmark de dataloggers, análise competitiva). O repositório existe em
`/home/vitor/Desktop/Motorsport/SARU/_arquivo/saru-docs` (MkDocs, última mudança
2026-07-18), mas não estava no escopo desta tarefa. Boa parte do conteúdo que se qualifica
para `empresa/docs/marca` e `empresa/docs/pesquisa` provavelmente já mora lá, em vez de
precisar ser extraído do saru-app. Recomenda-se uma auditoria dedicada a `saru-docs` antes
de montar o repositório da empresa.

## Documentos que citam algo que não existe mais

`saru-KB` é o caso mais comum. Era o repositório de knowledge base cross-ecossistema,
descontinuado em 2026-08 e absorvido pelo `saru-docs` (registrado em
`saru-app/docs/adr/MASTER_ADR.md` e em `saru-app/CLAUDE.md`). Ainda é citado como fonte
ativa em `saru-app/docs/adr/0013-setup-contract-json-schema-only.md`,
`0022-nomenclatura-comercial-hub-sfl.md`, `0034-crm-erp-pos-mvp-recongelamento.md`,
`0043-duckdb-motorsport-telemetry-nao-e-fonte-de-unidade.md`,
`docs/decisions/ratificacao-do-dono-2026-07-29.md`,
`docs/architecture/system-overview.md` (que lista saru-KB como repo vivo do ecossistema) e
nos três `MASTER_ADR.md` de ponteiro em `saru-physics-py/docs/adr/` e
`saru-physics-jl/docs/adr/`, que apontam para `github.com/SARUSySLab/saru-KB` como fonte
única de ADRs cross-repo. Nenhum desses arquivos foi atualizado depois da descontinuação.

`saru-gateway` e `saru-unified-platform` aparecem só como nomes antigos rejeitados do que
hoje é `saru-app`, citados explicitamente como legado em `docs/adr/0003-convencao-de-nomes.md`
e `docs/adr/0022-nomenclatura-comercial-hub-sfl.md`. Não são referências quebradas, são
histórico marcado como tal.

`saru-os` (nome antigo de `saru-app`) aparece dezenas de vezes fora de contexto histórico
explicado, principalmente em `docs/plans/mvp-higiene-arquitetura-plano-acao.md`,
`mvp-higiene-arquitetura-seguimento.md`, `docs/audit/AUDIT-FINDINGS-2026-06-28.md` e
`docs/audit/UIUX_AUDIT_2026-07-15.md`, todos já classificados como obsoleto ou stale neste
inventário.

`saru-core` como diretório solto (fora do submódulo `services/telemetry-api/vendor/saru-core`)
aparece em `docs/audit/AUDIT-FINDINGS-2026-06-28.md:97`, que cita o checkout irmão
`platform/saru-core`, e o próprio arquivo já registra esse layout como extinto na
reorganização de 2026-07-15. Não achamos outra ocorrência de saru-core como projeto órfão.

Caminhos pessoais antigos (`~/Projects/SARU/...`, `/home/vitor/Projects/...`) aparecem em
pelo menos onze arquivos, entre eles `docs/execution/2026-08-14-trackday-mvp/PROMPT-continuacao-mvp.md`,
`docs/plans/sessoes-reforma-frontend-2026-07.md`, `docs/history/handoffs-jun-jul-2026.md`,
`docs/history/ORIGINAL_REQUEST.md`, `docs/adr/README.md:15` e
`saru-physics-jl/docs/REFERENCES-AND-RESEARCH.md` (que cita `~/Projects/01_UnB/FullVehicleSimulation/`
e `~/Projects/_shared/tire_data/` como fonte de dado MATLAB e .tir de pneu). O workspace
real hoje é `/home/vitor/Desktop/Motorsport/SARU`; nenhum desses caminhos existe mais.

`Obsidian` não aparece em nenhum arquivo de `saru-app`, `saru-physics-py`, `saru-physics-jl`,
`saru-telemetry-gt7` ou `saru-desktop-app`.

`docs/README.md` do saru-app está desatualizado desde 2026-08-11: diz 46 ADRs, 19
documentos em product, 9 em research, 7 em audit, 6 em decisions e 2 em sessions. Os
números reais hoje são 49, 27, 33, 22, 9 e 12.

## O que não deu para classificar com confiança

Todos os 287 arquivos receberam uma linha na TSV. Três pontos ficam com confiança menor,
listados aqui em vez de escondidos na tabela.

`docs/adr/RASTREABILIDADE.md`, linha R01, atribui o módulo `saru_lapanalyzer/infra/datasources/`
ao repositório `saru-physics-py`. Isso está errado: esse caminho existe dentro de
`saru-app/services/telemetry-api`, não no repositório de física. É um erro do próprio
documento, não uma reclassificação nossa; mantivemos a linha do documento como está e
registramos o erro aqui.

Os módulos de `saru-physics-py/src/saru_core/` e `saru-physics-jl/src/` foram inventariados
só por nome de arquivo e primeira linha de docstring, conforme pedido no escopo. Não avaliamos
se cada módulo está no caminho de execução real do solver; o próprio `saru-physics-jl/docs/AUDIT-FINDINGS.md`
já registra que só `Engine.jl` é chamado pelo solver e os demais componentes estão órfãos.

`saru-telemetry-gt7` (captura ao vivo de GT7 via UDP) e `saru-desktop-app` (frontend
Next.js abandonado) foram lidos só pelos documentos pedidos no escopo (README e docs/).
Não abrimos o código-fonte desses dois repositórios; a classificação de destino como
"arquivo" reflete que nenhum dos dois está na lista de formatos ou na stack declarada da
saru-poc-trackday, não uma leitura de código que confirme isso linha a linha.

Fontes: TSV desta auditoria (`03-inventario-app-fisica.tsv`), `git log` de cada repositório
em `/home/vitor/Desktop/Motorsport/SARU/_arquivo/`, leitura direta de `docs/adr/README.md`,
`docs/adr/RASTREABILIDADE.md` e dos ADRs 0001 a 0049 inteiros. Data: 2026-09-12.
