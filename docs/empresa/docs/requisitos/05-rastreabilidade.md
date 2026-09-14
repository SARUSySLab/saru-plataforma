# Matriz de rastreabilidade da empresa

Rascunho 1, 2026-09-12. Para cada requisito: de qual objetivo veio, que regra o condiciona,
onde vive hoje (ou vai viver), qual caso de uso o exercita, qual critério o prova, e o
status. Atualizada a cada mudança, nunca só no fim. Status: proposto, aprovado, parcial,
implementado, validado. Coluna Tarefa fica "a abrir" até as issues existirem.

| Requisito | Tipo | Objetivo | Regra (RN) | Onde vive hoje ou vai viver | Caso de uso | Tarefa | Critério | Status | Versão |
|---|---|---|---|---|---|---|---|---|---|
| E-RF-01 | ler qualquer logger ou simulador | OBJ-02, OBJ-03 | E-RN-04, E-RN-08 | `saru-poc-trackday/src/saru_poc/readers/` (12 leitores) | E-UC-01, E-UC-04 | a abrir | E-CT-01, E-CT-11 | parcial | 1 |
| E-RF-02 | falar uma língua só | OBJ-02 | RN-10 da PoC | `pipeline/leitura.py`, `seeds/aliases.yaml`; contrato de canal do `saru-app` a portar | E-UC-01 | a abrir | E-CT-02 | parcial | 1 |
| E-RF-03 | saber onde e quando | OBJ-04 | RN-01, RN-06, RN-07 da PoC, E-RN-08 | `pipeline/resolucao_pista.py`, `corte_voltas.py` | E-UC-01 | a abrir: 9 exceções listadas no E-UC-01 | E-CT-03, E-CT-11 | parcial | 1 |
| E-RF-04 | rastrear cada número | OBJ-03 | E-RN-04 | tabela `ingestao`, `serie_amostral`; origem na tela a criar | E-UC-01, E-UC-03 | a abrir | E-CT-04 | parcial | 1 |
| E-RF-05 | traduzir para o nicho | OBJ-04 | E-RN-01 | `relatorio.py` (N0); textos do `saru-app` a portar | E-UC-01 passo 7 | a abrir | E-CT-05 | parcial | 1 |
| E-RF-06 | separar quem vê o quê | OBJ-03 | E-RN-04 | `auth.py`, regra de escopo por dono | E-UC-03 | a abrir | E-CT-06 | parcial | 1 |
| E-RF-07 | compartilhar entre famílias | OBJ-01 | E-RN-05 | a definir na modelagem | E-UC-03 | a abrir | E-CT-07 | proposto | 1 |
| E-RF-08 | guardar conhecimento de engenharia | OBJ-02 | E-RN-02 | `seeds/tracks.yaml`, `aliases.yaml`; veículo, pneu e modelo físico a criar (docs de física dos arquivados) | E-UC-02 | a abrir | E-CT-08 | parcial | 1 |
| E-RF-09 | estimar o carro a partir do dado | OBJ-02, OBJ-04 | E-RN-02 | `docs/fisica/parameters_gt3_cup.py`; modelos canônicos 991.1, 991.2, 992.1 Cup validados | E-UC-02 | a abrir | E-CT-10 | parcial | 1 |
| E-RNF-01 | nada falha em silêncio | OBJ-03 | | pipeline inteiro; `MotivoDegradacao` no contrato | E-UC-01 | a abrir | E-CT-03 | parcial | 1 |
| E-RNF-02 | mesmo dado, mesmo resultado | OBJ-03 | E-RN-04 | `pipeline/ingestao.py`, `storage.py` | E-UC-01, E-UC-03 | a abrir | E-CT-04 | parcial | 1 |
| E-RNF-03 | honestidade de claim | OBJ-03 | E-RN-01 | processo de revisão; checagem automática a definir | E-UC-02 | a abrir | E-CT-09 | proposto | 1 |
| E-RNF-04 | unidades SI e paddock | OBJ-04 | RN-10 da PoC | `pipeline/leitura.py`; `format.ts` do `saru-app` a portar | E-UC-01 | a abrir | E-CT-02 | parcial | 1 |
| E-RNF-05 | local-first | OBJ-05 | | a definir por família na arquitetura | E-UC-01 passo 1 | a abrir | a definir | proposto | 1 |
| E-RNF-06 | leigo entende em 5 s | OBJ-04 | | `web/src/blocos/` da PoC | E-UC-01 passo 7 | a abrir | E-CT-05 | parcial | 1 |
| E-RNF-07 | segredo e isolamento | OBJ-03 | E-RN-04 | `auth.py`, `.gitignore`; gitleaks a instalar no CI | E-UC-03 | a abrir | E-CT-06 | parcial | 1 |
| E-RNF-08 | dado exportável | OBJ-03 | E-RN-04 | a definir | E-UC-03 cenário 2c | a abrir | a definir | proposto | 1 |
| E-RNF-09 | leitor só com arquivo real | OBJ-02 | E-RN-03 | `tests/fixtures/`, `docs/*-medicao.md` | E-UC-04 | a abrir | E-CT-01 | parcial | 1 |
| E-RNF-10 | português | OBJ-04 | | repositório inteiro | | | revisão de PR | parcial | 1 |

Regras da empresa e quem as aprovou:

| Regra | Origem | Aprovada por | Data |
|---|---|---|---|
| E-RN-01 claim só com lastro | decisão ratificada 2 | Vitor | 2026-07-15 |
| E-RN-02 física validada junto contra o acervo | regra do operador | Vitor | 2026-09-12 |
| E-RN-03 requisito só com fonte | skill `requisitos` | Vitor, ao aprovar o 02 | 2026-09-12 |
| E-RN-04 dado bruto do cliente intocável | plano da PoC etapa 1 | Vitor, ao aprovar o 02 | 2026-09-12 |
| E-RN-05 núcleo com dono único | chat | Vitor | 2026-09-12 |
| E-RN-06 decisão antes de código; semana de modelagem; poucos ADR | chat | Vitor | 2026-09-12 |
| E-RN-07 ordem de leitura de quem entra | pesquisa de padrão GitHub | ordem a confirmar | |
| E-RN-08 simulador resolve pista pelo jogo, nunca por GPS | chat; caso GT7 medido | Vitor | 2026-09-13 |

## Família Campeonato

Rascunho 1, 2026-09-14, junto com o arquivo `campeonato/02-catalogos.md`. Onde vive: código da
PoC `saru-poc-trackday/src/saru_poc/`. Caso de uso: `campeonato/04-casos-de-uso.md`, a escrever.

| Requisito | Tipo | Objetivo | Regra (RN) | Onde vive hoje ou vai viver | Caso de uso | Tarefa | Critério | Status | Versão |
|---|---|---|---|---|---|---|---|---|---|
| CAM-RF-01 | ingerir o XML da cronometragem | CAM-OBJ-01, CAM-OBJ-03 | CAM-RN-02, CAM-RN-03, CAM-RN-05, CAM-RN-12 | `livetiming.py`, `rotas/campeonato.py` | a escrever | a abrir | CAM-CT-01, CAM-CT-04 | implementado | 1 |
| CAM-RF-02 | derivar o histórico volta a volta | CAM-OBJ-03 | CAM-RN-11 | `livetiming.py` | a escrever | a abrir | CAM-CT-03, CAM-CT-19 | implementado; conferência a escrever | 1 |
| CAM-RF-03 | guardar o snapshot bruto | CAM-OBJ-03 | | `livetiming.ingerir` | a escrever | a abrir | CAM-CT-02 | implementado | 1 |
| CAM-RF-04 | montar a torre de tempos | CAM-OBJ-01 | CAM-RN-01, CAM-RN-04, CAM-RN-05, CAM-RN-12 | parse pronto; tela só em mock | a escrever | a abrir | CAM-CT-04, CAM-CT-05, CAM-CT-13 | parcial | 1 |
| CAM-RF-05 | declarar a idade de cada linha | CAM-OBJ-02 | | painel ao vivo; torre a fazer | a escrever | a abrir | CAM-CT-06 | parcial | 1 |
| CAM-RF-06 | resolver a pista do evento | CAM-OBJ-01 | CAM-RN-09 | `livetiming.resolver_layout` | a escrever | a abrir | CAM-CT-07 | implementado, sem critério verificado | 1 |
| CAM-RF-07 | desenhar o mapa do evento | CAM-OBJ-01 | CAM-RN-09 | `rotas/campeonato.py` | a escrever | a abrir | CAM-CT-07 | implementado em esqueleto, sem critério verificado | 1 |
| CAM-RF-08 | empurrar o estado para a tela | CAM-OBJ-01, CAM-OBJ-02 | | `rotas/campeonato.py` | a escrever | a abrir | CAM-CT-13 | implementado | 1 |
| CAM-RF-09 | registrar os avisos da direção de prova | CAM-OBJ-01 | CAM-RN-04, CAM-RN-06 | `livetiming.py`, `022_lt_aviso.sql` | a escrever | a abrir | CAM-CT-08, CAM-CT-09 | implementado | 1 |
| CAM-RF-10 | receber a telemetria do carro ao vivo | CAM-OBJ-01 | CAM-RN-07, CAM-RN-08 | `vivo.py`, `023_veiculo_gateway.sql` | a escrever | a abrir | CAM-CT-10, CAM-CT-11, CAM-CT-14 | implementado | 1 |
| CAM-RF-11 | manter o buffer quente do pit wall | CAM-OBJ-01 | CAM-RN-07 | `vivo.py` | a escrever | a abrir | CAM-CT-06 | implementado | 1 |
| CAM-RF-12 | mostrar o pit wall do box | CAM-OBJ-01 | | rota pronta; tela só em mock | a escrever | a abrir | CAM-CT-06 | parcial | 1 |
| CAM-RF-13 | comparar os pilotos do dia | CAM-OBJ-01, CAM-OBJ-04 | CAM-RN-01, CAM-RN-12 | motor de perdas do relatório do piloto, a reaproveitar | a escrever | a abrir | CAM-CT-16 | proposto | 1 |
| CAM-RF-14 | entregar o clima da pista do evento | CAM-OBJ-01 | CAM-RN-10 | `clima.py`, `rotas/clima.py` | a escrever | a abrir | CAM-CT-15 | implementado | 1 |
| CAM-RF-15 | emitir credencial de máquina | CAM-OBJ-01 | | `021_livetiming.sql`, `023_veiculo_gateway.sql` | a escrever | a abrir | CAM-CT-12 | implementado | 1 |
| CAM-RF-16 | exigir autorização para importar o evento | CAM-OBJ-03, CAM-OBJ-04 | CAM-RN-02 | a definir | a escrever | a abrir | CAM-CT-18 | proposto | 1 |
| CAM-RNF-01 | local-first no box | CAM-OBJ-01 | | a definir na arquitetura; produção hoje no Railway | a escrever | a abrir | CAM-CT-17 | proposto | 1 |
| CAM-RNF-02 | latência do pit wall | CAM-OBJ-01 | | `rotas/campeonato.py`, `rotas/vivo.py` | a escrever | a abrir | CAM-CT-06 | proposto, meta pendente | 1 |
| CAM-RNF-03 | idade do dado em toda linha | CAM-OBJ-02 | | `vivo.py` | a escrever | a abrir | CAM-CT-06 | parcial | 1 |
| CAM-RNF-04 | gap e diferença separados | CAM-OBJ-01 | CAM-RN-05 | parse pronto; sem tela | a escrever | a abrir | CAM-CT-05 | parcial | 1 |
| CAM-RNF-05 | reenvio não duplica | CAM-OBJ-03 | CAM-RN-08 | `livetiming.py`, `vivo.py` | a escrever | a abrir | CAM-CT-02, CAM-CT-10 | implementado | 1 |
| CAM-RNF-06 | escrita de máquina, leitura de humano | CAM-OBJ-01 | | `021_livetiming.sql`, rotas | a escrever | a abrir | CAM-CT-12, CAM-CT-13, CAM-CT-14 | implementado | 1 |
| CAM-RNF-07 | torre lida em 5 s | CAM-OBJ-05 | | mocks | a escrever | a abrir | CAM-CT-17 | proposto | 1 |
| CAM-RNF-08 | trocar fonte de clima sem tocar o resto | CAM-OBJ-01 | CAM-RN-10 | `clima.py` | a escrever | a abrir | CAM-CT-15 | implementado | 1 |

Regras da família e quem as aprovou:

| Regra | Origem | Aprovada por | Data |
|---|---|---|---|
| CAM-RN-01 a CAM-RN-12 | `campeonato/02-catalogos.md`, rascunho 1 | a aprovar por Vitor ao ler o 02 | |

## Impacto de mudança

| Data | Item | Mudança | Itens afetados | Quem aprovou |
|---|---|---|---|---|
| 2026-09-12 | todos | versão 1 dos seis arquivos da empresa, escritos um por vez com revisão de Vitor | nenhum código; as issues ainda não existem | Vitor, arquivo a arquivo |
| 2026-09-12 | E-RF-07, E-RF-08 | de should para must | E-UC-03, ordem das famílias | Vitor |
| 2026-09-12 | E-RF-03 | falha deixa de ser resultado aceito e vira exceção a fechar | E-UC-01 exceções 5e a 5i viram tarefas | Vitor |
| 2026-09-12 | E-RN-02 | validação passa a ser conjunta contra o acervo | E-UC-02, DoR item 8 | Vitor |
| 2026-09-12 | E-RN-06 | "modelo antes do código" sai do DoR e entra na regra | 03 DoR | Vitor |
| 2026-09-12 | todos os status | "implementado" rebaixado a "parcial" | 02, 05 | Vitor |
| 2026-09-13 | E-RF-01, E-RN-08 | família Piloto passa a atender piloto virtual de simulador; simulador resolve pista pelo jogo, nunca por GPS | 02, 01, 05; requisitos PIL (agente Piloto avisado) | Vitor |
| 2026-09-13 | E-RF-09 | requisito novo: estimar parâmetros do carro e simular volta parecida com modelo de piloto; nunca tinha sido escrito | 02, 05, 01; tarefa de varrer os documentos de física | Vitor |
| 2026-09-13 | E-RF-09 | status atualizado de proposto para parcial com modelos canônicos 991.1, 991.2, 992.1 Cup em parameters_gt3_cup.py | 02, 05; PR #6 | Vitor |
| 2026-09-14 | CAM-* | bloco da família Campeonato aberto na matriz; CAM-RN-12 criada a partir do latente CAM-F12 do 01 | campeonato/01, campeonato/02, 05 | a aprovar por Vitor (PR 15) |
