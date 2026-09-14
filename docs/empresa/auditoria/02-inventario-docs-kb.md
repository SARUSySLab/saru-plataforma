# Inventário de documentação arquivada da SARU

Auditoria só leitura de quatro repositórios arquivados: saru-docs (33 arquivos), saru-KB
(95 arquivos), saru-research (11 arquivos) e o par de README de dados de pneu em SARU/_shared
(1 arquivo). Total de 140 arquivos classificados, listados em 02-inventario-docs-kb.tsv.
Data de corte da auditoria: 2026-09-12.

A pasta /home/vitor/Desktop/Motorsport/SARU/_arquivo/SARU/saru-knowledge-base existe mas
está vazia, sem submódulo configurado em .gitmodules. Nenhum arquivo para classificar ali.

## Contagem por tipo

| tipo | arquivos |
|---|---|
| especificacao | 54 |
| pesquisa | 24 |
| relatorio | 14 |
| indice | 12 |
| runbook | 12 |
| referencia_externa | 5 |
| template | 6 |
| brainstorm | 4 |
| ata | 3 |
| script | 3 |
| adr | 2 |
| outro | 1 |

## Contagem por área

| area | arquivos |
|---|---|
| negocio | 30 |
| arquitetura_software | 29 |
| dinamica_veicular | 14 |
| processo | 18 |
| telemetria | 13 |
| produto | 10 |
| fisica | 9 |
| ia_agentes | 5 |
| marca | 5 |
| pneu | 5 |
| empresa | 1 |
| outro | 1 |

## Contagem por estado

| estado | arquivos |
|---|---|
| vigente | 74 |
| stale | 39 |
| obsoleto | 15 |
| duplicado | 9 |
| rascunho | 3 |

74 arquivos, 53% do total, seguem vigentes hoje. 39 arquivos citam um repositório ou
caminho que não existe mais. Nenhum arquivo teve estado indefinido.

## Os 25 documentos mais valiosos para a empresa hoje

Critério de seleção: decisão de negócio ou marca já ratificada, especificação de produto
ou física ainda coerente com o produto atual (poc-trackday), ou pesquisa de mercado já
verificada de forma adversarial contra fonte primária.

| caminho | por que vale | destino proposto |
|---|---|---|
| saru-KB/50_company/SARU_MASTER_PRODUTO_NEGOCIOS.md | Síntese de posicionamento, personas, oferta e cinco decisões de negócio ratificadas em 2026-07-15 | empresa/docs/decisions |
| saru-KB/40_software_arch/adr/MASTER_ADR.md | Único ADR cross-ecossistema hoje: topologia multi-repo, ISO 8855, storage em 4 camadas, convenções de código | empresa/docs/decisions |
| saru-KB/50_company/SARU_BRAND_DNA.md | Fixa o mascote saruê, tipografia e paleta por módulo, decisão de marca vigente | empresa/docs/marca |
| saru-docs/docs/arquitetura/contracts.md | Contratos de dados (CanonicalTelemetrySession, VehicleSetup) usados pelo produto atual | poc-trackday/docs |
| saru-docs/docs/arquitetura/escala-v2.md | ADR de diferir NATS, Keycloak, Envoy e Debezium, com gatilho de reativação | poc-trackday/docs |
| saru-docs/docs/arquitetura/mvp-flows.md | Diagramas C4 e sequência dos fluxos do MVP em uso | poc-trackday/docs |
| saru-docs/docs/produto/use-cases.md | Seis casos de uso do MVP com rastreabilidade até status real verificado em julho de 2026 | poc-trackday/docs |
| saru-docs/docs/produto/mvp.md | Escopo dentro e fora do MVP e definição de pronto | poc-trackday/docs |
| saru-docs/docs/produto/personas.md | Três personas de compra do GTM ainda usadas para priorizar feature | empresa/docs/negocio |
| saru-docs/docs/produto/landing.md | Tabela de claim permitido e bloqueado para a narrativa comercial | empresa/docs/marca |
| saru-docs/docs/fisica/validation-pack.md | Define nível de claim físico e estrutura mínima de fixture de validação | fisica |
| saru-docs/docs/fisica/modelos.md | Estado da arquitetura 2-tier de física (QSS/3-DOF e 14-DOF) | fisica |
| saru-docs/docs/onboarding/index.md | Guia de onboarding com comandos essenciais por repo, ainda útil como modelo | poc-trackday/docs |
| saru-KB/20_vehicle_dynamics/modules/02_2_modelos_de_pneu_pacejka_mf.md | Especificação completa do modelo de pneu Pacejka MF 5.2 e 6.2 | fisica |
| saru-KB/20_vehicle_dynamics/modules/07_5_din_mica_veicular_e_refinamentos_cr_ticos_14_dof.md | Correções físicas do modelo 14-DOF (transferência de carga, ARB, TCS/ABS) com fórmulas | fisica |
| saru-KB/20_vehicle_dynamics/modules/10_8_par_metros_can_nicos_veiculares_e_pista.md | Parâmetros canônicos de veículo GT3 de referência e geometria de pista | fisica |
| saru-KB/20_vehicle_dynamics/research/gt3_factcheck_report.md | Fact-check de parâmetros do Porsche 911 GT3 R contra fonte primária | fisica |
| saru-KB/50_company/research/EMS_ARD_pricing_2026-07.md | Preço e modelo de negócio verificados dos dois concorrentes diretos | empresa/docs/pesquisa |
| saru-KB/50_company/research/pack_itens_5-10_2026-07.md | Verificação adversarial que corrige claims de pricing anteriores | empresa/docs/pesquisa |
| saru-KB/50_company/modules/03_3_an_lise_competitiva.md | Matriz de preço verificada por camada de concorrente | empresa/docs/negocio |
| saru-KB/50_company/modules/12_pricing_decision_pack.md | Consolida benchmark de preço como insumo direto da decisão de pricing | empresa/docs/negocio |
| saru-KB/50_company/modules/14_captacao_fomento_e_investimento.md | Mapa da escada de captação brasileira para o estágio atual da empresa | empresa/docs/negocio |
| saru-KB/50_company/research/Kit_Juridico_Start_BSB_2026-07.md | Pesquisa de formalização jurídica com fonte oficial | empresa/docs/processo |
| saru-KB/40_software_arch/modules/22_21_auditoria_ownership_sessoes_historico_saru_app.md | Auditoria de código real de ownership e sessão, ainda aplicável ao produto | poc-trackday/docs |
| saru-research/.claude/rules/calibration-guardrails.md | Baseline de calibração (992 GT3 R em Interlagos, 94.0 s) com regra de aprovação para mudança | fisica |

## Duplicatas encontradas

| arquivo A | arquivo B | observação |
|---|---|---|
| saru-research/_shared/tire_data/README.md | SARU/_shared/tire_data/README.md | Idênticos, confirmado byte a byte. Manter uma cópia em fisica e descartar a outra |
| saru-KB/20_vehicle_dynamics/research/Load sensitivity de pneus slick GT3....md | saru-KB/20_vehicle_dynamics/research/Sensibilidade Carga Pneu Slick GT3.md | Mesmo coeficiente k, mesmas fontes (Milliken, Pacejka, TTC/FSAE), dois relatórios de pesquisa paralelos sobre o mesmo tema |
| saru-KB/50_company/research/Mercado de Track Day Brasil.md | saru-KB/50_company/research/Track Day no Brasil 2026 Mapeamento de Mercado....md | Dois mapeamentos independentes dos mesmos autódromos e organizadores de track day |
| saru-docs/docs/fisica/gates.md | saru-docs/docs/fisica/validation-pack.md | As regras de gates.md são um subconjunto quase literal da seção central de validation-pack.md |
| saru-docs/docs/research/bibliografia.md | saru-docs/docs/research/benchmarking.md | Mesma lista de referências de mercado e standards, bibliografia.md é a versão sem comentário |
| saru-docs/docs/runbooks/release.md | saru-docs/docs/runbooks/alpha-release.md | Esquema de tags e checklist genérico repetem o runbook mais detalhado de alpha release |
| saru-KB/50_company/HANDOFF_GTM_2026-07-15.md | saru-KB/50_company/SARU_MASTER_PRODUTO_NEGOCIOS.md | O handoff duplica quase toda decisão e pendência já consolidada no documento síntese |
| saru-research/.claude/rules/git-workflow.md | ~/.claude/CLAUDE.md do operador | Repete regra de branch, commit e merge já centralizada na regra global atual |

Não encontrei par de duplicação entre saru-KB e uma pasta references de saru-docs, porque
saru-docs não tem pasta com esse nome. A relação real entre os dois repositórios é outra:
saru-docs/docs/research/index.md afirma que o conteúdo de pesquisa foi destilado a partir da
saru-KB, e saru-docs/docs/fisica/modelos.md é descrito como destilação direta dos módulos de
física da saru-KB (20_vehicle_dynamics/modules/01, 02, 04, 07). Ou seja, saru-docs contém
versões resumidas de conteúdo que existe em forma mais longa na saru-KB, não uma cópia
literal. O mesmo padrão aparece em saru-docs/docs/produto/mercado.md e personas.md frente a
saru-KB/50_company/modules/09_gtm_fase1_mercado_e_personas.md.

## Documentos que citam caminho ou repositório que não existe mais

Termos considerados stale: saru-os, saru-core, saru-core-jl, saru-gateway, saru-knowledge-base
fora do caminho atual, Obsidian, ~/Projects. O repositório saru-app existe e está arquivado,
mas vários módulos o tratam como projeto ativo em desenvolvimento, o que também não é mais
verdade.

| caminho | termo stale citado |
|---|---|
| saru-KB/SPM.md | saru-core, saru-core-jl |
| saru-KB/00_meta/session-prompts-sa-real-data-2026-07-18.md | saru-os, ~/Projects |
| saru-KB/20_vehicle_dynamics/modules/01_1_paradigmas_de_simula_o_f_sica.md | saru-core, saru-core-jl |
| saru-KB/20_vehicle_dynamics/modules/12_10_m_tricas_de_an_lise_telemetria_tra_ado.md | saru-os |
| saru-KB/20_vehicle_dynamics/modules/13_11_auditoria_de_reposit_rios_e_estado_atual_atualiza_o_2026_07.md | saru-core, saru-core-jl, lts-copatruck |
| saru-KB/40_software_arch/adr/MASTER_ADR.md | saru-core, saru-core-jl, saru-os |
| saru-KB/40_software_arch/Arquitetura SDV para Dinâmica Veicular, Motorsport e EVs.md | saru-os |
| saru-KB/40_software_arch/auditoria_alinhamento_2026-07-14.md | saru-core, saru-os, saru-core-jl |
| saru-KB/40_software_arch/auditoria_alinhamento_2026-07-15.md | saru-core, saru-os, saru-core-jl |
| saru-KB/40_software_arch/modules/01 a 20 (12 arquivos: 01, 02, 04, 05, 07, 12, 13, 14, 18, 19, 20, 21) | saru-core, saru-core-jl ou saru-os, conforme o módulo |
| saru-KB/40_software_arch/Relatorio Pesquisa SDV Modelagem Acausal.md | saru-core-jl, saru-os |
| saru-KB/40_software_arch/saru_analyzer_code_bundle_parsers.md | saru-os |
| saru-KB/40_software_arch/validation_architecture_roadmap.md | saru-core, saru-os |
| saru-KB/50_company/HANDOFF_GTM_2026-07-15.md | saru-os |
| saru-KB/50_company/modules/09_gtm_fase1_mercado_e_personas.md | saru-os |
| saru-KB/50_company/modules/10_gtm_fase2_pitch_e_narrativa.md | saru-os |
| saru-KB/50_company/modules/13_crm_erp_visao_operador.md | saru-os |
| saru-KB/50_company/modules/16_benchmark_simsense_skill_score_academy.md | saru-os |
| saru-docs/docs/arquitetura/index.md | descreve polyrepo saru-app, saru-physics-py/jl como vigente |
| saru-docs/docs/arquitetura/repos.md | saru-os, saru-core, saru-core-jl, saru-docs-extensive |
| saru-docs/docs/research/index.md | afirma que a saru-KB é o P&D vivo, o que não é mais verdade |
| saru-docs/docs/runbooks/mvp-board.md | issues de saru-app, saru-physics-py, saru-physics-jl como backlog ativo |
| saru-research/AGENTS.md | saru-os, saru-knowledge-base, ~/Projects/SARU, Obsidian |
| saru-research/.agents/skills/docs-auditor/SKILL.md | /home/vitor/Projects/SARU/saru-knowledge-base |
| saru-research/.github/copilot-instructions.md | saru-core, saru-core-jl, saru-os, saru-desktop-app, lts-copatruck |
| saru-research/implementation_plan.md | saru-core, saru-os |
| saru-research/README.md | saru-gateway, saru-core, saru-core-jl, lts-copatruck |
| saru-research/SGM.md | saru-os, saru-core, saru-core-jl, saru-knowledge-base |

## O que não consegui classificar com confiança

saru-docs/docs/arquitetura/contracts.md tem uma decisão em aberto sobre o schema de setup
(JSON Schema puro versus Protobuf), citada também no MASTER_ADR da saru-KB. Classifiquei como
especificacao, mas metade do conteúdo é uma decisão ainda pendente. Confirmar com Vitor se
essa decisão já foi tomada em outro lugar antes de migrar.

saru-KB/50_company/research/Benchmark de Precificação em Motorsport....md foi lido só até a
linha 50 pelo agente responsável, por ter mais de 300 linhas. O pack_itens_5-10_2026-07.md
indica que há claims errados adicionais além dos já corrigidos, possivelmente neste
documento. Recomendo reler o arquivo inteiro contra o pack de verificação antes de marcá-lo
como fonte citável em empresa/docs/pesquisa.

Não foi possível confirmar se os repositórios saru-app, saru-physics-py e saru-physics-jl,
citados em saru-docs como arquitetura polyrepo vigente à época, chegaram a ser implementados
nessa forma ou se o polyrepo nunca saiu do papel antes de o produto convergir para o
saru-poc-trackday atual. Sem essa confirmação, mantive vários documentos de
docs/arquitetura/ como vigente em vez de stale, por descreverem uma arquitetura de produto
que pode ou não ter existido de fato.

10_motorsport/transcrever_prints.py na saru-KB é um utilitário de OCR sem ligação direta a
uma área de negócio. Classifiquei como área processo, mas poderia caber em outro.

O prazo citado em saru-KB/50_company/modules/15_kit_juridico_e_formalizacao.md, edital Start
BSB fechando em 03 de agosto de 2026, já passou na data desta auditoria. O conteúdo jurídico
geral do documento segue vigente, mas o gatilho de urgência está vencido.

Fontes externas citadas em saru-docs/docs/produto/mercado.md, docs/research/benchmarking.md
e docs/research/bibliografia.md, e nos relatórios de pesquisa de mercado da saru-KB, não
foram abertas para confirmar se o link diz o que o texto afirma. Nenhum desses documentos
deve virar fonte citável em empresa/docs/pesquisa sem essa validação.
