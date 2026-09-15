# Catálogos da família Piloto

Este arquivo é a lista completa do que a família Piloto faz, como ela se comporta, que
regras obedece e como cada uma dessas coisas é provada.

Versão 1, 2026-09-13. Um id por linha, id nunca reaproveitado. Versão sobe quando o verbo ou
o objeto muda. Origem cita as fontes F1 a F13 de `01-problema-e-objetivos.md` ou um caminho
do repositório. Status: proposto, aprovado, implementado, validado.

## Como ler os ids

O sufixo de cada id é o mesmo do rascunho da PoC de 2026-09-12 (`RF-07` virou `PIL-RF-07`).
Onde o rascunho tinha um item que não é da família Piloto, o sufixo fica vago e o item
aparece na tabela "O que fica fora desta família" de `01-problema-e-objetivos.md`, com o
destino. Assim Lucas confere a conversão linha a linha sem precisar de um de-para à parte.

A coluna "Núcleo" diz qual capacidade da empresa cada requisito da família usa. Os `E-RF` e
`E-RNF` estão em `saru/docs/requisitos/02-catalogos.md`.

## Requisitos funcionais (PIL-RF)

| Id | Nome | Declaração | Nível | Núcleo | Origem | Prioridade | Critérios | Versão | Status |
|---|---|---|---|---|---|---|---|---|---|
| PIL-RF-01 | Receber o cartão do logger inteiro | O sistema deve receber um ou mais arquivos de uma captura e criar uma gravação com N arquivos brutos, identificando cada arquivo pelo SHA-256 | usuário | E-RF-01 | F1 etapa 1; `pipeline/recepcao.py` | must | PIL-CT-01, PIL-CT-02, PIL-CT-51 | 1 | implementado |
| PIL-RF-02 | Identificar o formato pela assinatura | O sistema deve identificar o formato de cada arquivo pelos bytes de assinatura, entre os 13 catalogados, e recusar com motivo o arquivo que não casa com nenhum | produto | E-RF-01 | F5; `readers/formatos.py` | must | PIL-CT-03 | 1 | implementado |
| PIL-RF-03 | Ler as amostras dos formatos suportados | O sistema deve extrair canais e amostras dos formatos com leitor registrado (vbox_vbo, motec_ld, motec_ldx, aim_xrk, protune_dlf, pi_pid, pi_listhead_dat, pi_pds, aim_drk, asam_mf4, aim_gpk, aim_rrk), sem interpolar célula vazia | produto | E-RF-01 | F5; `readers/` | must | PIL-CT-04, PIL-CT-52 | 1 | implementado |
| PIL-RF-04 | Registrar cada tentativa de leitura | O sistema deve gravar uma linha de ingestão por tentativa de leitura, com versão do leitor, versão do mapa de canal, status e motivo em caso de falha, sem sobrescrever tentativas anteriores | produto | E-RF-04 | F1 etapa 2; `pipeline/ingestao.py` | must | PIL-CT-05, PIL-CT-06 | 1 | implementado |
| PIL-RF-05 | Normalizar canal para o vocabulário canônico | O sistema deve traduzir cada canal gravado para o canal canônico e converter a unidade nativa para SI usando o mapa de canal do perfil de origem | produto | E-RF-02 | F1 etapa 3; F9 ADR-0049; `pipeline/leitura.py`, `seeds/aliases.yaml` | must | PIL-CT-07, PIL-CT-53 | 1 | implementado |
| PIL-RF-06 | Guardar as séries fora do banco relacional | O sistema deve gravar as amostras em objeto colunar imutável, particionado por gravação e taxa nativa, e guardar no catálogo só o ponteiro (URI, contagem, taxa) | produto | E-RF-04 | F1 decisão 2; `storage.py` | must | PIL-CT-08 | 1 | implementado |
| PIL-RF-07 | Resolver a pista em cascata | O sistema deve resolver o layout da pista pelo alias declarado no arquivo, depois pela posição GPS contra a coordenada de referência do catálogo, depois perguntando ao piloto, e registrar qual degrau resolveu | usuário | E-RF-03 | F1 etapa 4; F9 ADR-0048; `pipeline/resolucao_pista.py`, `POST /api/gravacoes/{id}/pista` | must | PIL-CT-09, PIL-CT-10, PIL-CT-11, PIL-CT-56 | 1 | implementado |
| PIL-RF-08 | Cortar as voltas | O sistema deve cortar a gravação em voltas usando, em ordem, o canal de volta da amostra, os tempos de beacon do sidecar e o cruzamento da linha de chegada por GPS | produto | E-RF-03 | F1 etapa 5; `pipeline/corte_voltas.py` | must | PIL-CT-12, PIL-CT-54, PIL-CT-57, PIL-CT-58 | 1 | implementado |
| PIL-RF-09 | Decompor a volta em trechos e traçado | O sistema deve calcular o tempo por setor e por curva do layout resolvido, os micro-setores por distância, e o traçado medido a partir do GPS | produto | E-RF-03 | F1 decisão 1 e etapa 6; `pipeline/decomposicao.py`, `tracado.py` | must | PIL-CT-13, PIL-CT-14, PIL-CT-55 | 1 | implementado |
| PIL-RF-10 | Entregar o relatório em quatro níveis | O sistema deve emitir, para uma gravação, o relatório com N0 (melhor volta, três maiores perdas), N1 (voltas), N2 (perdas por curva e por micro-setor, mapa), N3 (canais) e contexto, no shape do contrato | usuário | E-RF-05 | F1 funil; F3 `Relatorio`; `relatorio.py` | must | PIL-CT-15, PIL-CT-16, PIL-CT-59 | 1 | implementado |
| PIL-RF-11 | Comparar a volta com uma referência | O sistema deve permitir escolher a volta analisada e uma referência (outra volta da mesma gravação ou de outra gravação, inclusive da base de referência do sistema) e emitir as perdas por trecho entre as duas, nunca aceitando a mesma volta dos dois lados | usuário | E-RF-05, E-RF-07 | F7; `GET /api/relatorio/{id}?volta=&referencia=` | should | PIL-CT-17 | 1 | implementado |
| PIL-RF-12 | Servir as séries na grade comum | O sistema deve entregar as séries de amostras de uma volta reamostradas numa grade comum de 900 pontos para os blocos do N3 | produto | E-RF-05 | F2 rotas; `GET /api/gravacoes/{id}/amostras` | should | PIL-CT-18 | 1 | implementado |
| PIL-RF-13 | Declarar bloco sem dado | O sistema deve marcar cada bloco sem dado como indisponível com um motivo do vocabulário (sem_gps, sem_venue, sem_catalogo_de_curva, sem_setor, sem_contexto_pneu, sem_contexto_sessao, sem_canal_combustivel, somente_inventario) e um texto legível | usuário | E-RF-05, E-RNF-01 | F1 fusão 2; F3 `MotivoDegradacao` | must | PIL-CT-19, PIL-CT-60 | 1 | implementado |
| PIL-RF-16 | Autenticar o piloto e isolar o dado por dono | O sistema deve autenticar por cadastro e login e mostrar a cada piloto só o que ele possui, respondendo 404 ao acesso a recurso de outro dono | produto | E-RF-06 | F7 regra de escopo; `auth.py`, `rotas/auth.py` | must | PIL-CT-22, PIL-CT-23 | 1 | implementado |
| PIL-RF-23 | Dizer onde freou e virou sem canal de pedal | O sistema deve derivar o ponto de frenagem da queda do G longitudinal (-3,5 m/s² por 10 m) e a viragem pela subida do G lateral, combinando velocidade, ângulo de volante, aceleração lateral e delta instantâneo para calcular o índice de trail-braking | usuário | E-RF-05 | F4 item F1; F10; ratificado por Vitor em 2026-09-13 | should | PIL-CT-30 | 1.1 | pronto para implementar |
| PIL-RF-24 | Ler FuelTech CSV e ProTune CSV | O sistema deve ler os exports CSV de FTManager e de ProTune, com envelope (separador, decimal, codificação, cabeçalho, taxa) medido em arquivo real | produto | E-RF-01 | F1 formatos 1 e 2 e riscos 1 a 3 | should | PIL-CT-31 | 1 | proposto, bloqueado por falta de amostra |
| PIL-RF-27 | Ler telemetria de simuladores e e-sports | O sistema deve ler telemetria de simulação para sim drivers e equipes de e-sports: nativa MoTeC (.ld) de ACC e ACTI do Assetto Corsa, binário .ibt do iRacing e .ld de GT7 | usuário | E-RF-01 | Vitor 2026-09-13 (F14) | must | PIL-CT-44, PIL-CT-45 | 1.1 | parcial: ACC e GT7 leem; ACTI/AC via .ld compatível; .ibt em especificação |
| PIL-RF-28 | Conscientizar o piloto sobre pneus e clima | O sistema deve permitir ao piloto registrar composto, pressão a frio e quente e voltas no jogo de pneus, exibindo resumo climático processado da pista (seco/molhado, temperatura estimada) | usuário | E-RF-05 | Vitor 2026-09-13 | should | PIL-CT-46 | 1 | pronto para implementar |
| PIL-RF-26 | Exportar o relatório em HTML | O sistema deve gerar um HTML autossuficiente do relatório com N0 e N1 completos e N2 resumido, imprimível em PDF, sem interação | usuário | E-RF-05 | F1 decisão 3 e opção C | could | PIL-CT-33 | 1 | proposto |
| PIL-RF-29 | Manter preset de veículo por geração | O sistema deve manter os parâmetros de veículo de cada geração do 911 GT3 Cup com proveniência por valor, para alimentar simulação e estimação | produto | E-RF-09, E-RF-08 | Vitor 2026-09-13, no chat; migração do `saru` | must | PIL-CT-47 | 1.1 | parcial: os três presets existem em `fisica/parametros_gt3_cup.py`, a proveniência por valor não |
| PIL-RF-30 | Calibrar parâmetros do veículo contra telemetria real e simular a volta | O sistema deve ajustar os `ParameterValue` de `fisica/parametros_gt3_cup.py` (massa, geometria, pneu) contra os canais medidos de uma volta ingerida, e usar o resultado para simular a volta em dois motores: QSS em Python e transiente 14-DOF em Julia, seguindo as fórmulas de `saru/docs/referencias/engenharia-de-pista.md` | usuário | E-RF-09 | Vitor 2026-09-15, no chat; issue #49 | should | a escrever | 1 | proposto |

### O que existe hoje por simulador

Medido no código em 2026-09-13. Nenhuma linha é estimativa.

| Simulador | Estado | Onde |
|---|---|---|
| ACC | perfil `acc` do container MoTeC `.ld`, lido pelo leitor `motec_ld` da PoC. No acervo, 34 arquivos, mediana de 39 dos 55 canais casando com o mapa | `src/saru_poc/acervo.py:85` e o comentário acima dele |
| GT7 | perfil `gt7_ld` do mesmo container, mesmo leitor. No acervo, 3 arquivos, mediana de 23 dos 37 canais | `src/saru_poc/acervo.py:86` |
| iRacing | sem leitor na PoC. O `saru-app` tem `sim_iracing_csv.py`, adaptador do CSV exportado, reconhecido por assinatura de coluna (`LongAccel`, `LatAccel`, `TireTempFLI`), marcado como código morto | `_arquivo/saru-app/.../datasources/sim_iracing_csv.py`; `docs/mapa-parsing-dois-motores.md:88` |
| Assetto Corsa, o original | sem leitor em nenhum dos dois repositórios | medido por busca em `src/` e nos datasources do `saru-app` |
| AMS2 | fora da ordem pedida por Vitor. O `saru-app` tem `sim_ams2_csv.py`, também morto | `_arquivo/saru-app/.../datasources/sim_ams2_csv.py` |

O `saru-app` também tem `sim_acc_motec.py` e `sim_gt7_csv.py`, os dois mortos, e os dois com
defeito documentado: o de ACC tem assinatura do CSV do MoTeC i2 enquanto o perfil `acc`
espera o dialeto do `.ld`, e o de GT7 depende de três constantes que são chute explícito no
YAML, entre elas raio de roda de 0,318 m com erro de até 12% por categoria
(`docs/mapa-parsing-dois-motores.md:87` e `:88`). Portar qualquer um deles é reescrever, não
copiar.

O iRacing grava telemetria nativa em `.ibt` binário. Não existe leitor de `.ibt` em nenhum
dos dois repositórios, e `sim_iracing_csv.py` lê o CSV exportado, não o `.ibt`. Sem leitor,
a pesquisar: sem arquivo real não se escreve leitor (DoR item 8).

Os leitores da PoC identificam formato por assinatura de bytes (`readers/formatos.py`),
enquanto os quatro adaptadores de simulador do `saru-app` identificam por conjunto de
colunas do CSV. Os dois mecanismos não são o mesmo, e reconciliar isso faz parte de
PIL-RF-27.

## Requisitos não funcionais (PIL-RNF)

Categorias pelo URPS+ (usabilidade, confiabilidade, desempenho, suportabilidade, mais
restrições).

| Id | Categoria | Declaração | Métrica e meta | Núcleo | Origem | Prioridade | Critérios | Versão | Status |
|---|---|---|---|---|---|---|---|---|---|
| PIL-RNF-01 | Confiabilidade | Nenhuma etapa do pipeline pode falhar em silêncio nem escolher um default sem declarar | 100% das tentativas de ingestão com status e motivo; 100% dos relatórios com `resolucao_pista` declarada; zero default silencioso em teste | E-RNF-01 | F1 etapas 2 e 4; F2 regras | must | PIL-CT-05, PIL-CT-11, PIL-CT-19 | 1 | implementado |
| PIL-RNF-02 | Confiabilidade | O mesmo arquivo, com a mesma versão de leitor e de mapa de canal, produz o mesmo relatório; reprocessar não sobrescreve | Reingestão gera nova linha e mesmo resultado; objeto Parquet identificado por SHA-256 nunca é alterado | E-RNF-02 | F2 regras; `tests/test_reingestao.py` | must | PIL-CT-06, PIL-CT-08 | 1 | implementado |
| PIL-RNF-03 | Desempenho | O upload responde antes de processar e o processamento das etapas 2 a 6 roda em segundo plano | `POST /api/gravacoes` responde 202; tempo total por gravação a medir no acervo | própria da família | F2 rotas | must | PIL-CT-34 | 1 | implementado, meta pendente |
| PIL-RNF-04 | Suportabilidade | A migração do armazenamento de amostras para objeto remoto (S3 ou MinIO) troca só o caminho do ponteiro | Nenhum código além de `SARU_DATA_ROOT` e do prefixo de URI muda | própria da família | F1 decisão 2; `.env.example` linha 9 | should | PIL-CT-35 | 1 | implementado, a verificar |
| PIL-RNF-05 | Suportabilidade | Todo leitor de formato entra com fixture versionada, teste automatizado e documento de medição | 12 de 12 leitores com teste; 3 de 12 com documento de medição em 2026-09-12 | E-RNF-09 | F11 seção 3 | must | PIL-CT-36 | 1 | parcial |
| PIL-RNF-06 | Confiabilidade | Toda resposta de leitura da API é validada contra o contrato TypeScript antes de sair; divergência vira erro no servidor, nunca tela quebrada | 100% das rotas de leitura passam por `contrato.py`; divergência de shape retorna 500 | E-RNF-01 | F2 rotas; `contrato.py` | must | PIL-CT-37 | 1 | implementado |
| PIL-RNF-07 | Segurança | Sessão em cookie httpOnly com JWT, senha com argon2, dado isolado por dono | Acesso a recurso de outro piloto retorna 404; segredo de produção nunca no repositório | E-RNF-07 | `auth.py`; F7 regra de escopo; `.env.example` | must | PIL-CT-22, PIL-CT-23, PIL-CT-38 | 1 | implementado |
| PIL-RNF-08 | Usabilidade | O N0 é lido em 5 segundos no box sem clique; rótulos por extenso, sem abreviação interna; velocidade e traçado acima do relatório | N0 com três números e três frases e nenhum controle; zero abreviação não expandida na tela em revisão de rótulos | E-RNF-06 | F1 funil; F4 itens B3 e F2 | should | PIL-CT-39 | 1 | parcial |
| PIL-RNF-09 | Restrição de design | Dado interno em SI; conversão para unidade de paddock (km/h, g, grau, %, °C, psi) só na borda de exibição | Séries em m/s no armazenamento; velocidade em km/h no contrato de saída | E-RNF-04 | F9 ADR-0042; `tests/test_relatorio.py::test_velocidade_sai_em_km_por_hora` | must | PIL-CT-07, PIL-CT-40 | 1 | implementado para velocidade |
| PIL-RNF-10 | Confiabilidade | O instante do corte de volta tem erro menor ou igual ao período da série de maior taxa da gravação | Em 2026-09-12, 17 gravações cortam a 1 Hz com erro de até 1 s. Refino contra a série rápida em `corte_voltas.py::refinar_passagens`; tolerância de 0,05 s e alerta de 0,20 s ratificados por Vitor em 2026-09-13, medição no acervo pendente (E-RN-02) | própria da família | F2 dívidas | should | PIL-CT-41, PIL-CT-58 | 1 | parcial: motor e corte prontos, declaração no relatório aberta |
| PIL-RNF-11 | Restrição de implantação | Um container serve API e front na mesma origem; amostras em volume persistente; banco gerenciado separado | Deploy descrito em `docs/deploy-railway.md` reproduzível do zero | própria da família | `docs/deploy-railway.md` | should | PIL-CT-42 | 1 | implementado |
| PIL-RNF-12 | Restrição de implementação | Código, tabela, rota, mensagem de commit e documentação em português, sem travessão | Revisão de PR; commit be4ebcb removeu travessão de nome de pista como regra da casa | E-RNF-10 | Decisão de Vitor 2026-09-12; F7 | must | PIL-CT-43 | 1 | implementado |

E-RNF-05 da empresa (funcionar sem internet no box e sincronizar depois) não foi escrito
para esta família. O piloto de track day envia o cartão depois da bateria, com internet. A
confirmar com Vitor se a família Piloto precisa de modo local-first na versão 1.

## Regras de negócio (PIL-RN)

Regra de física ou calibração só entra com aprovação de Vitor (E-RN-02). A coluna Fonte diz
quem aprovou e quando, ou "aprovação pendente".

| Id | Regra | Física (E-RN-02) | Fonte | Requisitos condicionados | Versão |
|---|---|---|---|---|---|
| PIL-RN-01 | Se o venue não foi resolvido, então não existe setorização e o relatório declara `resolucao_pista = nao_resolvida`; default silencioso é proibido | não | F1 etapa 4 (Lucas e Vitor, 2026-08-28) | PIL-RF-07, PIL-RF-09, PIL-RF-13 | 1 |
| PIL-RN-02 | Se a soma dos melhores setores for menor que a melhor volta, então ela é a volta ideal; senão a volta ideal é suprimida e o relatório marca `ideal_suprimida` | não | F1 etapa 6; F3 `MelhorVolta` | PIL-RF-10 | 1 |
| PIL-RN-03 | Se um setor da volta não tem dado, então a volta é marcada como não setorizável e não entra no cálculo da ideal | não | F1 etapa 6 | PIL-RF-09, PIL-RF-10 | 1 |
| PIL-RN-04 | Se um arquivo é reprocessado, então nasce uma nova linha de ingestão e o estado atual passa a ser o último sucesso; nenhuma linha ou objeto anterior é alterado | não | F1 etapa 2; F2 regras | PIL-RF-04, PIL-RF-06 | 1 |
| PIL-RN-05 | Se o SHA-256 do arquivo primário já existe, então o envio não cria segunda gravação | não | `tests/test_pipeline.py::test_reenviar_o_mesmo_arquivo_nao_cria_segunda_gravacao` | PIL-RF-01 | 1 |
| PIL-RN-06 | Se o arquivo tem GPS e existe um layout do catálogo a até 5,0 km da posição mediana, então esse layout é candidato do degrau GPS | sim | Raio de 5,0 km aprovado por Vitor em 2026-08-20, com espalhamento medido de 501 m em 29 arquivos de Interlagos e pista errada mais próxima a 318,8 km (F9 ADR-0048, seção Contexto) | PIL-RF-07 | 1 |
| PIL-RN-16 | Se duas ou mais candidatas caem dentro do raio, então o degrau GPS não decide e a resolução segue para o degrau seguinte | não | F9 ADR-0048; ratificada por Vitor em 2026-09-13: proximidade euclidiana não decide ambiguidade espacial | PIL-RF-07 | 1.1 |
| PIL-RN-07 | Se o fator que fecha o eixo de distância no comprimento do layout ficar fora da faixa 0,9 a 1,1, então a decomposição recusa a volta com o tamanho do erro na mensagem; in-laps, out-laps, voltas de aquecimento e trânsito são categorizadas | sim | `pipeline/decomposicao.py:141`; ratificada por Vitor em 2026-09-13; Curitiba nominal fixado em 3.695 m | PIL-RF-09 | 1.1 |
| PIL-RN-08 | Se uma volta cobre a pista (cobertura de distância e setores com velocidade média mínima de 20 km/h), então é válida; piso de tempo absoluto não é critério de validade | sim | F9 ADR-0033; ratificada por Vitor em 2026-09-13 | PIL-RF-08, PIL-RF-10 | 1.1 |
| PIL-RN-10 | Se um canal tem nome canônico, então tem uma única unidade de saída; canal sem unidade provada é testado contra fatores físicos plausíveis e, se permanecer ambíguo, fica fora do canônico | sim | F9 ADR-0049; ratificada por Vitor em 2026-09-13 | PIL-RF-05 | 1.1 |
| PIL-RN-11 | Se um formato tem só inventário (cabeçalho, contagem) sem semântica de canal confirmada, então não é apresentado como suportado para amostra | não | F6 `docs/aim-gpk-rrk-medicao.md`; F11 seção 3 | PIL-RF-02, PIL-RF-03 | 1 |
| PIL-RN-12 | Se a volta é in-lap ou out-lap, então fica fora do cálculo de consistência | não | F1 etapa 7; ratificada por Vitor em 2026-09-13 com classificação explícita | PIL-RF-10 | 1.1 |
| PIL-RN-13 | Se a gravação não tem canal de pedal e tem acelerômetro válido, então o ponto de frenagem é onde o G longitudinal cai abaixo de -3,5 m/s² sustentado por 10 m; trail-braking combina velocidade, volante, acc lateral, frenagem e delta | sim | F4 item F1; F10 calibração 232 voltas; ratificada por Vitor em 2026-09-13 | PIL-RF-23 | 1.1 |
| PIL-RN-14 | Se a análise e a referência apontam para a mesma volta, então a comparação é recusada | não | F7 item 1.12 | PIL-RF-11 | 1 |
| PIL-RN-17 | Se a gravação vem de um perfil de origem marcado como simulado, então a pista é resolvida pelo que o jogo declara (nome do circuito e layout) e a gravação não entra no degrau GPS, nem grava alias novo a partir de posição, porque a coordenada exportada por simulador é placeholder do exportador | não | E-RN-08, decidida por Vitor em 2026-09-13 (F14). Caso medido: os 3 arquivos GT7 declaram Interlagos e trazem coordenada de Donington (`src/saru_poc/readers/ld.py:29`). O gancho já existe: `acervo.SIMULADOS` em `acervo.py:104` alimenta a coluna `perfil_origem.simulado` em `acervo.py:243` | PIL-RF-07, PIL-RF-27 | 1 |
| PIL-RN-15 | Se um canal de volta bruto tem densidade incompatível com contagem de voltas (por exemplo, valores de 28 a 2572), então é rejeitado pela guarda de densidade e o corte segue para o próximo degrau | não | F2 dívidas, último item | PIL-RF-08 | 1 |

PIL-RF-27, PIL-RN-17, PIL-CT-44 e PIL-CT-45 são ids novos, sem correspondente no rascunho
da PoC: vieram da decisão de Vitor de 2026-09-13.

PIL-RN-16 é id novo, sem correspondente no rascunho da PoC: ela saiu de PIL-RN-06, que
misturava o raio aprovado por Vitor com a regra de ambiguidade herdada de um ADR ainda não
ratificado. Separar as duas foi o que permitiu registrar a pendência de cada uma.

A regra RN-09 do rascunho (contagem de voltas vem do parser, o número digitado vira
anotação) condiciona a espinha operacional, que sai desta família. Ela vai para a família
Equipe junto com RF-14 e RF-15.

## Critérios de aceitação (PIL-CT)

Dado, Quando, Então. A coluna "Como verificar" cita o teste automatizado que já existe, ou
diz "demonstração" ou "a escrever".

| Id | Requisito | Dado | Quando | Então | Como verificar |
|---|---|---|---|---|---|
| PIL-CT-01 | PIL-RF-01 | um bundle AiM com .xrk, .gpk e .rrk do mesmo radical | o piloto envia os três | nasce 1 gravação com 3 arquivos brutos e papéis distintos | `tests/test_pipeline.py::test_bundle_vira_uma_gravacao_com_papeis` (exige acervo real e Postgres) |
| PIL-CT-02 | PIL-RF-01, PIL-RN-05 | um arquivo já ingerido | o mesmo arquivo é reenviado | nenhuma segunda gravação é criada e a resposta aponta a existente | `tests/test_pipeline.py::test_reenviar_o_mesmo_arquivo_nao_cria_segunda_gravacao` |
| PIL-CT-03 | PIL-RF-02 | um arquivo cujos bytes não casam com nenhuma assinatura | é enviado | é recusado com motivo, sem adivinhar formato, e o resto do bundle segue | `tests/test_pipeline.py::test_arquivo_sem_formato_e_recusado_nao_adivinhado`, `::test_recusado_aparece_no_relatorio_sem_derrubar_o_bundle` |
| PIL-CT-04 | PIL-RF-03 | um .vbo real com célula vazia | é lido | a célula sai como NaN, nunca interpolada nem repetida | `tests/test_reader_vbo.py`; F5 tabela |
| PIL-CT-05 | PIL-RF-04, PIL-RNF-01 | um arquivo de formato catalogado sem leitor | é ingerido | nasce linha de ingestão com status falhou e o motivo | `tests/test_pipeline.py::test_sem_leitor_vira_linha_de_ingestao_com_motivo` |
| PIL-CT-06 | PIL-RF-04, PIL-RNF-02, PIL-RN-04 | uma gravação já ingerida | é reprocessada | a linha anterior permanece e uma nova é acrescentada | `tests/test_pipeline.py::test_ingestao_e_append_only`, `tests/test_reingestao.py` |
| PIL-CT-07 | PIL-RF-05, PIL-RNF-09 | um canal de velocidade gravado em km/h | é normalizado e depois servido | armazenado em m/s e exibido em km/h | `tests/test_relatorio.py::test_velocidade_sai_em_km_por_hora`, `::test_de_para_cobre_os_canais_que_o_front_le` |
| PIL-CT-08 | PIL-RF-06, PIL-RNF-02 | uma série gravada em Parquet | a mesma série é gravada de novo | o objeto tem o mesmo SHA-256 e não é reescrito | `tests/test_storage.py` |
| PIL-CT-09 | PIL-RF-07 | um arquivo que declara venue com alias no catálogo | é resolvido | `resolucao_pista = alias` | `tests/test_resolucao_pista.py::test_venue_com_alias_unico_resolve_por_alias` |
| PIL-CT-10 | PIL-RF-07, PIL-RN-06, PIL-RN-16 | um arquivo sem venue e com GPS a menos de 5 km de um único layout | é resolvido | `resolucao_pista = gps` com o layout certo | `tests/test_resolucao_pista.py::test_gps_dentro_do_raio_e_layout_unico_resolve_por_gps` |
| PIL-CT-11 | PIL-RF-07, PIL-RN-01 | um arquivo sem venue e sem GPS coerente (caso GT7 com coordenada de Donington) | é resolvido | `resolucao_pista = nao_resolvida`, nenhum setor, e o piloto pode informar a pista por `POST /pista` | `tests/test_resolucao_pista.py::test_sem_venue_e_gps_longe_do_catalogo_fica_nao_resolvida`; o degrau da pergunta, por demonstração |
| PIL-CT-12 | PIL-RF-08 | uma gravação com canal de volta, beacon e GPS | é cortada | o canal de volta vence; sem ele, o beacon; sem ambos, o GPS | `tests/test_corte_voltas.py` (20 testes) |
| PIL-CT-13 | PIL-RF-09 | uma volta válida num layout com setores | é decomposta | os micro-setores particionam a volta inteira e a soma das perdas dá o delta da volta | `tests/test_decomposicao.py::test_micro_setores_particionam_a_volta_inteira`, `::test_soma_das_perdas_por_micro_setor_da_o_delta_da_volta` |
| PIL-CT-14 | PIL-RF-09, PIL-RN-07 | uma volta de Curitiba cujo eixo de distância mede 3.749 m contra 3.220 m do layout | é decomposta | a volta é recusada e a mensagem traz o medido, o do layout e o fator | `tests/test_decomposicao.py::test_curitiba_recusa_e_a_mensagem_traz_o_tamanho_do_erro` |
| PIL-CT-15 | PIL-RF-10, PIL-RN-02 | uma sessão em que a soma dos melhores setores passa a melhor volta | o N0 é gerado | a ideal é suprimida e `ideal_suprimida = true` | `tests/test_relatorio.py::test_ideal_e_suprimida_quando_passaria_a_melhor_volta` |
| PIL-CT-16 | PIL-RF-10, PIL-RN-03 | uma sessão em que um setor não tem dado | o N0 é gerado | a ideal é suprimida e a volta não entra como setorizável | `tests/test_relatorio.py::test_ideal_e_suprimida_com_setor_sem_dado` |
| PIL-CT-17 | PIL-RF-11, PIL-RN-14 | duas gravações da mesma pista | o piloto compara a volta A com a volta B | as perdas por trecho saem ordenadas da maior perda ao maior ganho, e ganho aparece como perda negativa | `tests/test_relatorio_entre_gravacoes.py`; `tests/test_relatorio.py::test_perdas_saem_ordenadas_da_maior_perda_pro_maior_ganho` |
| PIL-CT-18 | PIL-RF-12 | uma volta com séries em taxas diferentes | o front pede as amostras | todas saem na grade de 900 pontos que o front espera | `tests/test_relatorio.py::test_grade_bate_com_a_que_o_front_espera` |
| PIL-CT-19 | PIL-RF-13, PIL-RNF-01 | uma gravação sem catálogo de fase | o relatório é gerado | `tempo_por_fase` sai como indisponível com motivo, nunca omitido | `tests/test_relatorio.py::test_fase_sai_declarada_como_indisponivel` |
| PIL-CT-22 | PIL-RF-16, PIL-RNF-07 | um recurso do piloto A | o piloto B lista ou edita | não aparece na listagem e a edição devolve 404 | `tests/test_operacao.py::test_usuario_b_nao_ve_evento_de_a_na_listagem`, `::test_usuario_b_recebe_404_ao_editar_evento_de_a` |
| PIL-CT-23 | PIL-RF-16, PIL-RNF-07 | uma rota de leitura | é chamada sem login | é recusada | `tests/test_auth.py`, `tests/test_livetiming.py::test_leitura_exige_login` |
| PIL-CT-30 | PIL-RF-23, PIL-RN-13 | uma gravação com acelerômetro e sem canal de freio | o relatório é gerado | o ponto de frenagem e o de viragem aparecem em metros contra a referência, e zebra ou buraco não viram frenagem | a escrever, após aprovação do limiar por Vitor |
| PIL-CT-31 | PIL-RF-24 | um export real de FTManager | é enviado | o formato é identificado, as amostras lidas, e envelope divergente é recusado com motivo | a escrever, após receber amostra real |
| PIL-CT-33 | PIL-RF-26 | um relatório gerado | o piloto exporta | um único arquivo HTML abre offline com N0 e N1 completos e N2 resumido | a escrever |
| PIL-CT-34 | PIL-RNF-03 | um bundle do tamanho dos do acervo | é enviado | a resposta é 202 e `GET /estado` mostra o progresso das etapas 2 a 6 | `tests/test_api.py`; tempo total a medir |
| PIL-CT-35 | PIL-RNF-04 | `SARU_DATA_ROOT` apontando para outro caminho | o pipeline roda | nenhum outro código muda | demonstração |
| PIL-CT-36 | PIL-RNF-05 | um leitor novo | é proposto em PR | o PR traz fixture em `tests/fixtures/`, teste e documento de medição | revisão de PR |
| PIL-CT-37 | PIL-RNF-06 | uma resposta com campo fora do contrato | é servida | o servidor devolve 500 e registra a divergência | `tests/test_contrato.py` (6 testes) |
| PIL-CT-38 | PIL-RNF-07 | um cookie de sessão ausente, inválido ou adulterado | uma rota protegida é chamada | devolve 401 | `tests/test_auth.py::test_rota_protegida_sem_cookie_devolve_401`, `::test_token_adulterado_devolve_401` |
| PIL-CT-39 | PIL-RNF-08 | a tela N0 de uma gravação | é aberta | há três números, três frases e nenhum controle; nenhum rótulo abreviado | demonstração e revisão de rótulos |
| PIL-CT-40 | PIL-RNF-09 | um canal de pressão em bar | é exibido | aparece em psi com o fator único da borda | a escrever nesta família (implementado no `saru-app`, F9 ADR-0042) |
| PIL-CT-41 | PIL-RNF-10 | uma gravação com canal de volta a 1 Hz e série de velocidade a 20 Hz | é cortada | o instante do corte tem erro menor ou igual ao período da série rápida | a escrever: o refino entrega resolução de 0,05 s, e resolução não é erro de instante. `tests/test_corte_voltas.py::test_resolucao_nao_e_o_erro_do_instante` mostra que o erro real varia de 0,000 a 0,300 s na mesma resolução |
| PIL-CT-42 | PIL-RNF-11 | um projeto Railway vazio | o runbook é seguido | API, front e volume sobem e uma amostra sobrevive a um redeploy | demonstração |
| PIL-CT-43 | PIL-RNF-12 | um PR | é revisado | nenhum identificador, mensagem ou documento em inglês ou com travessão | revisão de PR |

| PIL-CT-44 | PIL-RF-27 | uma gravação exportada por simulador da lista suportada | é enviada | o formato é identificado, as amostras lidas, e o relatório sai com os mesmos blocos do relatório de uma volta real | ACC e GT7 pelo `.ld`, sem teste dedicado de procedência; iRacing e Assetto Corsa a escrever, depois de haver arquivo real |
| PIL-CT-45 | PIL-RF-07, PIL-RF-27, PIL-RN-17 | uma gravação de perfil simulado, que declara o circuito e traz coordenada de placeholder | a pista é resolvida | resolve pelo que o jogo declara, o degrau GPS não roda, e nenhum alias novo nasce de posição | a escrever; hoje em `xfail` estrito em `tests/test_resolucao_pista.py`, issue #10 |
| PIL-CT-47 | PIL-RF-29 | o preset de uma das três gerações do 911 GT3 Cup | é consultado | cada valor traz a proveniência dele e os valores pendentes de manual estão marcados | a escrever; hoje a proveniência vive só em `docs/fisica-parametros-gt3-cup.md`, e `ParameterValue` não é usado (issue #19) |

## Critérios das exceções do E-UC-01

O caso de uso da empresa `E-UC-01` (do arquivo ao uso por cada família) lista dez exceções
conhecidas no acervo em 2026-09-12. Cada uma vira um critério desta família, porque é nesta
família que elas acontecem primeiro. A coluna "Como verificar" foi medida contra `tests/` e
`src/` do repositório em 2026-09-13.

| Id | Exceção | Requisito | Dado | Quando | Então | Como verificar |
|---|---|---|---|---|---|---|
| PIL-CT-51 | 2e | PIL-RF-01 | dois arquivos primários do mesmo formato, radicais diferentes, no mesmo envio | são enviados juntos | o sistema falha alto para os dois, sem fundir voltas | `tests/test_pipeline.py::test_duas_capturas_do_mesmo_formato_nao_fundem` (exige acervo real e Postgres) |
| PIL-CT-52 | 3e | PIL-RF-03, PIL-RN-11 | um `.gpk` ou `.rrk`, que o leitor lê só como inventário | é ingerido | a gravação entra sem amostra, a ingestão fica com status parcial e o relatório diz por quê | parcial: a decisão está coberta sem banco em `tests/test_relatorio.py::test_captura_so_de_inventario_degrada_com_motivo` e `::test_captura_com_amostra_nao_mostra_aviso_de_inventario`; o ponta a ponta em `tests/test_api.py::test_estado_declara_inventario` pula sem Postgres, então a verificação em banco continua pendente |
| PIL-CT-53 | 4e | PIL-RF-05, PIL-RN-10 | um canal sem unidade provada no mapa | a gravação é ingerida | o canal fica sem `canal_canonico_id`, não vira número na tela, e o piloto vê quantos canais ficaram sem mapa | a escrever; hoje a contagem `sem_mapa` só existe na tabela `ingestao` |
| PIL-CT-54 | 5e | PIL-RF-08 | uma das 100 gravações Pi com corte de volta dentro do arquivo | é cortada | o corte usa o marcador do próprio arquivo, em vez de cair para o degrau seguinte | a escrever; o leitor ainda não decodifica o bloco `EVNT_B0` |
| PIL-CT-55 | 5f | PIL-RF-09, PIL-RN-07 | uma volta de Curitiba, layout de 3.220 m no catálogo e 3.749 m percorridos | é decomposta | a volta é recusada com o tamanho do erro, até Vitor decidir qual dos dois comprimentos vale | `tests/test_decomposicao.py::test_curitiba_recusa_e_a_mensagem_traz_o_tamanho_do_erro`; a decisão de domínio segue aberta |
| PIL-CT-56 | 5g | PIL-RF-07, PIL-RF-09 | uma das 3 gravações GT7, que declara venue de Interlagos e traz coordenada de Donington | é resolvida, cortada e traçada | o corte por GPS e o traçado recusam com o tamanho do erro, e a resolução de pista declara que o venue e a posição discordam | corte e traçado fechados (`tests/test_corte_voltas.py::test_gps_longe_do_layout_nao_corta_e_diz_o_motivo`, `tests/test_tracado.py::test_contorno_certo_no_lugar_errado_e_recusado`); a declaração na resolução de pista é a escrever, hoje em `xfail` estrito em `tests/test_resolucao_pista.py`. A guarda que falta é PIL-RN-17 |
| PIL-CT-57 | 5h | PIL-RF-08, PIL-RN-15 | um canal de volta com valores de 28 a 2572 | é usado para cortar | a guarda de densidade rejeita e o corte tenta o próximo degrau | `tests/test_corte_voltas.py::test_densidade_rejeita_canal_que_muda_demais` |
| PIL-CT-58 | 5i | PIL-RF-08, PIL-RNF-10 | uma gravação cujo único canal de volta é de 1 Hz, com série de maior taxa disponível | é cortada | o instante do corte é refinado contra a série rápida e o tempo de volta deixa de sair em segundos inteiros | parcial: `tests/test_corte_voltas.py::test_refino_recupera_o_instante_verdadeiro` e `::test_porta_do_refino_fecha_para_canal_de_taxa_alta` cobrem o corte; a declaração do erro no relatório continua a escrever |
| PIL-CT-59 | 6e | PIL-RF-10, PIL-RN-03 | uma volta com setor sem dado | o N0 é gerado | a volta é marcada como não setorizável e a ideal é suprimida | `tests/test_relatorio.py::test_ideal_e_suprimida_com_setor_sem_dado` |
| PIL-CT-60 | 7e | PIL-RF-13 | cada um dos oito motivos de degradação do contrato | o relatório é gerado | o bloco aparece marcado com o motivo e um texto legível, nunca some nem mostra número inventado | parcial: `sem_catalogo_de_curva` (`tests/test_relatorio.py::test_fase_sai_declarada_como_indisponivel`) e `somente_inventario` (`::test_captura_so_de_inventario_degrada_com_motivo`) têm teste; os outros seis são a escrever |

## Glossário

| Termo | Definição | Tipo ou unidade | Observação |
|---|---|---|---|
| Gravação | Uma captura do logger, com um ou mais arquivos brutos | entidade | Pode existir sem evento |
| Bundle | Conjunto de arquivos do mesmo radical enviados juntos (por exemplo, .xrk com sidecars .gpk e .rrk) | entrada | Duas capturas do mesmo formato nunca fundem |
| Arquivo bruto | Arquivo original, identificado por SHA-256, nunca alterado | entidade | |
| Perfil de origem | Regras de leitura e mapa de canal de um logger ou software | catálogo | Vem de `seeds/aliases.yaml` |
| Canal canônico | Nome único de uma grandeza no vocabulário da SARU, com uma unidade de saída | catálogo | PIL-RN-10 |
| Série amostral | Amostras de um canal numa taxa nativa, guardadas em Parquet; o banco guarda só o ponteiro | entidade | |
| Layout | Configuração de uma pista (comprimento, coordenada de referência, setores, curvas) | entidade | Uma pista pode ter vários layouts |
| Venue | Nome de pista declarado no arquivo pelo logger | texto | Pode estar ausente ou errado |
| Volta | Trecho da gravação entre dois cruzamentos da linha de chegada | entidade | Válida quando cobre a pista (PIL-RN-08) |
| Volta ideal | Soma dos melhores tempos de setor do piloto na sessão | s | Nunca maior que a melhor volta (PIL-RN-02) |
| In-lap, out-lap | Volta de entrada e de saída do box | classificação | Fora da consistência (PIL-RN-12) |
| Trecho | Setor, curva ou micro-setor de um layout | entidade | |
| Micro-setor | Trecho de distância fixa, sem catálogo de curva | m | Modo de degradação do "onde ganhar tempo" |
| Traçado | Linha que o carro fez, derivada do GPS de uma volta | coordenadas | Vazio quando o GPS é incoerente |
| Degradação | Bloco do relatório sem dado, com motivo do vocabulário | estado | PIL-RF-13 |
| Fator de fechamento | Razão entre o comprimento do layout e a distância medida na volta, usada para escalar o eixo de distância | adimensional | Aceito entre 0,9 e 1,1 (PIL-RN-07) |
| Perfil simulado | Perfil de origem cuja gravação veio de simulador, e não de logger em pista | catálogo | Marcado na coluna `perfil_origem.simulado`, a partir de `acervo.SIMULADOS` |
| Placeholder de coordenada | Posição fixa que o exportador do simulador escreve no lugar da coordenada real do circuito | defeito de origem | Razão de PIL-RN-17 |
| Default silencioso | Escolha que o sistema faz sem avisar | defeito | Proibido em toda família (E-RNF-01) |
