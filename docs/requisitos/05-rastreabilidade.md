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
| E-RF-09 | estimar o carro a partir do dado | OBJ-02, OBJ-04 | E-RN-02 | a definir; peças em `_arquivo/saru-physics-py` (QSS, LTS), `saru-physics-jl` (14 DOF), `saru-KB/20_vehicle_dynamics`, `saru-docs/docs/fisica` | E-UC-02 | a abrir: varredura dos 53 documentos de física | E-CT-10 | proposto | 1 |
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
