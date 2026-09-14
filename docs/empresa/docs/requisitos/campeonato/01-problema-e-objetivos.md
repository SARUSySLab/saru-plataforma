# Problema e objetivos da família Campeonato

Rascunho 1, 2026-09-13. Família Campeonato, a segunda da fila (CAM-F1). Quem compra é o
organizador do evento: a pessoa que aluga a pista, monta as baterias e precisa dizer, no
fim do dia, quem andou quanto. Cada linha cita uma fonte da tabela do fim do arquivo.

## Cenário atual

Track day no Brasil não tem cronometragem oficial. A norma da CBA trata o track day como
atividade não competitiva, o Time Attack quando existe é recreativo, e na prática o piloto
se cronometra sozinho com celular, RaceChrono, Harry's LapTimer ou RaceBox (CAM-F2, seção 4).
O organizador opera baterias de 20 a 30 minutos separadas por nível ou por potência, com
briefing, vistoria e calibragem de pneu, e não tem placar do dia para entregar (CAM-F2).

Campeonato regional é outro caso. Ali existe cronometragem profissional: o autódromo roda
MyLaps ou Orbits e publica um XML `resultspage` na rede local do evento. A SARU mediu esse
XML no 12º MBR Time Attack de 2026, no Autódromo de Brasília, com 84 carros e 9 classes
(CAM-F5). Três limites do formato foram medidos ali: o XML carrega só as últimas 3 voltas de
cada carro, os campos de setor vieram vazios, e a hora da última passagem pode ser de horas
antes, porque o time attack roda em levas e carro parado não passa no loop (CAM-F5).

A PoC de track day já lê esse XML e já tem o esqueleto do pit wall. São 631 linhas de leitura
e ingestão de cronometragem com 14 testes, 251 linhas de rotas de campeonato, 214 linhas de
ingestão ao vivo com 8 testes e 607 linhas de clima com 8 testes (CAM-F7). O transporte ao
vivo é lote HTTP curto, de cerca de 250 ms de amostras por envio, escolhido porque o 4G de
autódromo cai o tempo todo e reenviar um lote é repetir o POST (CAM-F6).

Quanto o organizador brasileiro paga hoje por cronometragem, quantos track days acontecem por
ano e de quem é o dado que o autódromo gera: a levantar com Vitor. Nenhuma fonte lida sustenta
esses números.

## Problema

| Id | Problema | Quem sofre | Evidência (fonte, data) |
|---|---|---|---|
| CAM-PRB-01 | O track day não tem cronometragem oficial, então o organizador não tem placar do dia para entregar e o piloto se mede sozinho pelo celular | Organizador, piloto inscrito | CAM-F2 seção 4, 2026-07 |
| CAM-PRB-02 | O organizador não tem comparativo do dia entre pilotos nem torre de tempos acessível; telemetria ao vivo é privilégio de categoria de ponta | Organizador, campeonato regional, equipe pequena | CAM-F1 PRB-04, 2026-09-12; CAM-F13, 2026-09-12 |
| CAM-PRB-03 | O dado da cronometragem fica preso na rede local do evento e só entrega as 3 últimas voltas de cada carro; o histórico volta a volta precisa ser derivado por comparação entre snapshots | Organizador, equipe, quem monta o resultado | CAM-F5, 2026-08-29 |
| CAM-PRB-04 | O dado chega incompleto e com idade: no evento medido os campos de setor vieram vazios, e a hora da última passagem pode ser de horas antes | Quem lê a torre no box | CAM-F5, 2026-08-29 |
| CAM-PRB-05 | A conexão do autódromo cai, e produção na nuvem não enxerga a rede local da cronometragem | Organizador, telemetrista | CAM-F6, 2026-08-30; CAM-F5 |
| CAM-PRB-06 | Nenhum organizador foi entrevistado: todo requisito desta família vem de documento, código e mock | A própria SARU | CAM-F1, 2026-09-12 |

## Objetivos

Resultado mensurável, não funcionalidade. Meta sem número fica marcada.

| Id | Objetivo | Indicador | Meta | Problema |
|---|---|---|---|---|
| CAM-OBJ-01 | O organizador vê o comparativo do dia e a torre de tempos do evento sem internet no box | Evento real operado ponta a ponta com a rede externa desligada | 1 evento antes de fechar a família; a confirmar com Vitor | CAM-PRB-01, CAM-PRB-02, CAM-PRB-05 |
| CAM-OBJ-02 | Nenhum número velho aparece como se fosse agora | Linhas da torre com a idade do dado declarada na tela | 100% | CAM-PRB-04 |
| CAM-OBJ-03 | Reconstituir o histórico volta a volta do evento inteiro a partir de uma fonte que só entrega 3 voltas | Passagens derivadas conferidas contra o resultado oficial do evento | a definir; precisa de um resultado oficial para comparar, a confirmar com Vitor | CAM-PRB-03 |
| CAM-OBJ-04 | O evento vira receita por contrato de organizador, não por assinatura de piloto | Contratos de organizador fechados por temporada | a definir; a estrutura de taxa fixa mais valor por carro é sugestão do research, nunca foi vendida (CAM-F4) | CAM-PRB-01 |
| CAM-OBJ-05 | Ouvir um organizador de verdade antes de fechar o catálogo desta família | Entrevistas registradas em `06-validacao.md` | pelo menos 1 antes de qualquer CAM-RF entrar em desenvolvimento; a confirmar com Vitor | CAM-PRB-06 |

## Escopo herdado da família Piloto

A família Piloto empurrou quatro requisitos para cá, com o motivo registrado (CAM-F10). Eles
entram no catálogo desta família como CAM-RF no arquivo 02.

| Veio como | O quê | Motivo registrado |
|---|---|---|
| RF-17 | Live timing | Acontece durante o evento, no box, não no cartão do piloto |
| RF-18 | Telemetria ao vivo e pit wall | Mesmo motivo |
| RF-19 | Clima | Serve a decisão de pista do evento |
| RF-22 | Comparativo do dia entre pilotos | O comprador é o organizador, não o piloto |

O comparativo do dia não é mais um nível de zoom do relatório do piloto: é uma segunda tela,
com piloto no lugar de volta como dimensão de comparação, e reaproveita o mesmo motor de
perdas por trecho (CAM-F9).

## Stakeholders e fontes

| Stakeholder | Papel | Como foi ouvido | Data |
|---|---|---|---|
| Organizador de evento e campeonato | Compra o comparativo do dia e o pit wall | Nunca entrevistado. Só documento de pesquisa e plano de produto | 2026-08-28 |
| Cronometrista do autódromo | Opera o MyLaps ou Orbits e é dono da rede do evento | Nunca ouvido. O que se sabe veio do XML medido e do script de relay | 2026-08-29 |
| Piloto inscrito no evento | Aparece na torre e recebe o comparativo | Nunca entrevistado nesta família | a levantar |
| Vitor Toledo | Fundador, aprova requisito e regra de física | Chat de 2026-09-12 e 2026-09-13 | 2026-09-13 |
| Lucas Antunes | Escreveu o live timing e a ingestão ao vivo da PoC | Docstring dos módulos e decisões datadas no código | 2026-08-29 a 2026-08-30 |

| Id | Fonte | Onde |
|---|---|---|
| CAM-F1 | Problema, objetivos e backlog da empresa | `docs/requisitos/01-problema-e-objetivos.md`, `03-backlog.md` |
| CAM-F2 | Pesquisa de pistas e track days, seção 4 | `docs/pesquisa/2026-07-pistas-e-track-days.md` |
| CAM-F3 | Oportunidades de produto no track day, item O6 | `docs/pesquisa/oportunidades-track-day.md` |
| CAM-F4 | Pacote de decisão de preço, linha do contrato de organizador | `docs/negocio/pricing_decision_pack.md` |
| CAM-F5 | Leitura e ingestão do XML de cronometragem, com os fatos medidos no evento real | `saru-poc-trackday/src/saru_poc/livetiming.py` |
| CAM-F6 | Ingestão ao vivo e pit wall | `saru-poc-trackday/src/saru_poc/vivo.py`, `rotas/vivo.py` |
| CAM-F7 | Auditoria da PoC, tabela de módulos e testes | `docs/auditoria/04-poc-trackday.md` |
| CAM-F8 | Especificação do mock N1 e o mock entregue | `saru-poc-trackday/docs/arquitetura/visao-mocks-ui.md`, `docs/mocks/mock-pitwall-desktop.html` |
| CAM-F9 | Plano canônico da PoC, seção do comparativo do evento | Drive `Trabalho/SARU/01_ Saru-KB/notas/plano-poc-core-trackday.md` |
| CAM-F10 | O que a família Piloto empurrou para cá | `saru-poc-trackday/docs/requisitos/01-problema-e-objetivos.md` |
| CAM-F11 | Concorrente para feature, linhas do HH Timing e do HH Data Management | `_arquivo/saru-app/docs/product/programa-produto-mvp-2026-08-13.md` |
| CAM-F12 | Modelo de coleta de um campeonato real | `docs/pesquisa/2026-08-16-acervo-porsche-cup-modelo-de-coleta.md` |
| CAM-F13 | Pesquisa do pit wall, 26 links | Google Doc de Vitor, 2026-09-12. Nenhum link aberto ainda |

## Desejos, necessidades e frustrações registradas

| Tipo | Registro (paráfrase) | Fonte | Virou |
|---|---|---|---|
| Necessidade | Pit wall sem vídeo, dado por distância, local-first, gap e interval separados | CAM-F13 | CAM-OBJ-01 |
| Necessidade | Funcionar no box com a rede do autódromo caindo, e sincronizar depois | CAM-F6 | CAM-OBJ-01 |
| Necessidade | A tela declara a idade do dado em vez de mostrar número velho | CAM-F6, silêncio a partir de 15 s | CAM-OBJ-02 |
| Necessidade | O histórico volta a volta é derivado, porque a fonte não o entrega | CAM-F5 | CAM-OBJ-03 |
| Desejo | Vender ranking recreativo por classe e dashboard do evento white-label ao organizador | CAM-F3 item O6 | CAM-OBJ-04 |
| Frustração | Track day não tem cronometragem oficial, então o dado existe e não tem onde virar análise | CAM-F3 leitura de mercado | CAM-PRB-01 |
| Latente | Um evento hospeda campeonatos diferentes ao mesmo tempo, e o evento é quem declara a disciplina | CAM-F12 | a virar regra de negócio no arquivo 02 |

## Referência de mercado

Régua desta família. A coluna da SARU sai do código e dos mocks medidos em 2026-09-13.

| Capacidade | Quem faz | SARU hoje |
|---|---|---|
| Torre de tempos com posição, gap para a frente e diferença para o líder | MyLaps e Orbits, no XML `resultspage` | Existe: o parse lê posição, gap e diferença, e trata os dois como texto porque podem vir como "4 Voltas" (CAM-F5) |
| Parciais de setor S1, S2 e S3 na torre | HH Timing | Não existe com dado real. O schema tem os campos de setor e eles vieram vazios no evento medido (CAM-F5). O mock N1 já desenha a coluna (CAM-F8) |
| Tempo de volta projetado em três modos (melhores setores, diferença percentual, melhor volta) | HH Timing | Parcial: a volta ideal por melhores setores existe no núcleo; os outros dois modos não (CAM-F11) |
| Leitura de vários formatos de logger num banco só | HH Data Management | Existe: 12 leitores registrados na PoC (CAM-F7) |
| Run sheet como entidade do evento | HH Timing | Parcial: a espinha operacional de evento, sessão e bateria existe na PoC com 935 linhas (CAM-F7) |
| Telemetria ao vivo do carro no box | HH Timing e equivalentes de categoria de ponta | Parcial: ingestão em lote, deduplicação e buffer quente de 300 s existem; a tela do pit wall só existe como mock (CAM-F6, CAM-F8) |
| Mapa do evento ao vivo e envio por stream para o navegador | HH Timing | Existe em esqueleto: rota de traçado e stream por SSE na PoC (CAM-F7) |

O mock N1 já desenhou, além da torre: telemetria transiente multicanal, matriz de degradação
térmica e de desgaste de pneu por eixo e lado, traçado de pedais e ângulo de esterço com delta
contínuo, e elipse de atrito a 50 Hz (CAM-F8). Os números que aparecem no arquivo do mock são
ilustrativos e não vêm de medição.
