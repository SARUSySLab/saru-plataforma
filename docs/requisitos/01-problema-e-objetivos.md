# Problema e objetivos da família Piloto

Este arquivo diz por que a família Piloto existe, quem sofre o problema que ela resolve e
qual resultado mede se ela chegou lá.

Versão 1, 2026-09-13. Recorte da família Piloto a partir do rascunho da PoC inteira escrito
em 2026-09-12. Leitor: quem entra no projeto e precisa entender o porquê antes de abrir o
código. Fontes F1 a F12 na seção final; cada linha das tabelas cita uma.

## A família em uma frase

O piloto amador sobe o cartão do logger e recebe, em linguagem dele, onde perdeu tempo e o
que treinar. Mínimo viável aprovado por Vitor em 2026-09-12 (`saru/docs/requisitos/03-backlog.md`,
tabela "Ordem das famílias").

Personas: P2 (sim racer) e P3 (piloto amador de track day, "Dr. Fernando"), da pesquisa de
mercado de 2026-07-15 (F8). Nenhum dos dois foi entrevistado até 2026-09-13.

O piloto virtual conta como piloto, com o mesmo relatório da volta real (Vitor, 2026-09-13,
F14). A ordem dos simuladores é iRacing primeiro, depois ACC, Assetto Corsa e GT7. Quem
roda no simulador quer a mesma resposta de quem roda na pista: onde perdeu tempo e o que
treinar. O que muda é a procedência do arquivo, não o relatório.

## Cenário atual

Um piloto amador sai do track day com o cartão do logger (AiM, Garmin, FuelTech, ProTune,
MoTeC) e sem saber onde perde tempo. As ferramentas que leem esses arquivos (i2, RaceStudio,
Pi Toolbox) exigem um engenheiro para interpretar, custam licença de desktop e cada uma fala
um formato (F1, F5, F6). Loggers amadores raramente têm canal de pedal de freio ou
acelerador; têm giroscópio e acelerômetro, e o produto anterior assumia canais que a maior
parte do mercado não tem (F4, relato de 2026-08-20).

A SARU construiu o `saru-app` de junho a agosto de 2026 e mediu dois defeitos de confiança
na trilha de análise: volta ideal maior que a melhor volta (B1) e pista escolhida por
default sem avisar (B2). A PoC `saru-poc-trackday` nasceu em 2026-08-28 para provar o loop
mínimo do arquivo ao insight e matar os dois defeitos por construção (F1).

Estado medido no catálogo em 2026-08-29 (F2):

| Medida | Valor |
|---|---|
| Gravações ingeridas | 198 |
| Séries em Parquet | 686 |
| Voltas cortadas | 141 |
| Tempos de trecho | 369 |
| Formatos com assinatura catalogada | 13 |
| Formatos com leitor de amostra | 12 |
| Testes coletados em 2026-09-12 | 408 |

Dívidas medidas, não supostas (F2): 100 gravações Pi com corte de volta dentro do arquivo
que o leitor não decodifica; 17 gravações que cortam por canal a 1 Hz e dão tempo de volta
em segundos inteiros; 67 voltas de Curitiba recusadas porque o catálogo diz 3.220 m e o
carro anda 3.749 m; 3 gravações GT7 com GPS de outra pista; zero traçado gravado por
consequência; nenhum canal canônico de combustível.

## Problema

| Id | Problema | Quem sofre | Evidência (fonte, data) |
|---|---|---|---|
| PIL-PRB-01 | O piloto amador não sabe onde perde tempo na volta e não tem quem leia o arquivo para ele | Piloto de track day (P3), piloto virtual de simulador (P2) | F8 personas 2026-07-15; F4 relato de campo 2026-08-20; F14 |
| PIL-PRB-02 | Cada logger grava um formato próprio, muitos binários sem documentação; ler errado ou em silêncio esconde defeito | O piloto que recebe número errado | F5 mapa de parsing 2026-08-29; F2 tabela de 13 formatos |
| PIL-PRB-03 | O sistema anterior apresentava resultado errado como certo: volta ideal impossível e pista por default sem aviso | Piloto | F1 plano 2026-08-28, bugs B1 e B2 |
| PIL-PRB-04 | O produto assumia canais de pedal que loggers amadores não têm, e não usava o acelerômetro que todos têm | Piloto com Garmin, AiM sem pedal, ProTune | F4 relato de campo 2026-08-20, item F1 |
| PIL-PRB-06 | Jargão interno vaza para a tela ("delta OV") e o piloto não entende o que vê | Piloto e engenheiro | F4 relato de campo 2026-08-20, item B3 |
| PIL-PRB-07 | Os formatos mais prováveis dos pilotos do evento (FuelTech, ProTune CSV) não têm nenhuma amostra no acervo | Time da PoC, bloqueado para escrever o leitor | F1 plano, riscos 1 a 3 e pedido bloqueante |

O rascunho da PoC tem um sétimo problema, PRB-05 (o organizador não tem comparativo entre
os pilotos do dia). Ele sai desta família e vai para a família Campeonato. O sufixo dos ids
segue o do rascunho, então não existe `PIL-PRB-05`.

## Objetivos

Resultado mensurável, não funcionalidade. Os sufixos seguem os do rascunho; OBJ-04, que era
o comparativo do organizador, vai para a família Campeonato e não aparece aqui.

| Id | Objetivo | Indicador | Meta | Problema |
|---|---|---|---|---|
| PIL-OBJ-01 | Entregar ao piloto, sem engenheiro, onde ele perde tempo na volta | Fração das gravações com volta cortada que produzem relatório N0 a N2 | 100% das gravações com volta cortada e pista resolvida | PIL-PRB-01 |
| PIL-OBJ-02 | Nunca apresentar número errado como certo | Relatórios com volta ideal maior que a melhor volta; blocos sem dado sem motivo declarado | Zero em ambos, verificado por teste automatizado | PIL-PRB-03, PIL-PRB-06 |
| PIL-OBJ-03 | Ler os formatos que os pilotos do track day realmente usam | Formatos com leitor, fixture real e teste | 12 hoje; mais FuelTech CSV e ProTune CSV | PIL-PRB-02, PIL-PRB-07 |
| PIL-OBJ-05 | Servir logger sem canal de pedal | Gravações sem canal de freio com ponto de frenagem e viragem derivados do acelerômetro | 100% das gravações com acelerômetro válido, após limiar aprovado por Vitor | PIL-PRB-04 |
| PIL-OBJ-06 | Tornar cada resultado reproduzível e rastreável | Relatórios cujo caminho até o arquivo bruto, versão do leitor e mapa de canal pode ser refeito | 100%, por construção (ingestão append-only) | PIL-PRB-02, PIL-PRB-03 |

Ligação com os objetivos da empresa: PIL-OBJ-01 e PIL-OBJ-05 servem OBJ-04 da empresa
(traduzir para o nicho); PIL-OBJ-02 e PIL-OBJ-06 servem OBJ-03 (rastrear cada número);
PIL-OBJ-03 serve OBJ-02 (reaproveitar o que existe). Os objetivos da empresa estão em
`saru/docs/requisitos/01-problema-e-objetivos.md`.

## Stakeholders e fontes

| Stakeholder | Papel | Como foi ouvido | Data |
|---|---|---|---|
| Vitor Toledo | Fundador, dono da física e das regras de calibração; aprova toda regra de física (E-RN-02) | Decisões no plano e no chat; autor de 12 commits na branch `feat/pds-amostras` | 2026-08-28 a 2026-09-13 |
| Lucas Antunes | Desenvolvedor, dono do repositório; fechou as 4 decisões do plano e as decisões de arquitetura da rodada 2 | Plano canônico (F1) e corpo do commit 2b88627 (F7) | 2026-08-28 a 2026-08-30 |
| Giuliano | Engenheiro de pista sênior (kart, MG Cup, GT4), usou o `saru-app` em campo | Relato falado, transcrito por Vitor, com itens marcados como relatado ou medido (F4) | 2026-08-20 |
| Piloto de track day (P3, Dr. Fernando) | Comprador do resultado; quer saber por que perde tempo | Persona da pesquisa de mercado (F8); nenhum piloto entrevistado até 2026-09-13 | 2026-07-15 |
| Piloto virtual de simulador (P2) | Mesmo resultado, com arquivo de simulador. iRacing primeiro, depois ACC, Assetto Corsa e GT7 | Persona da pesquisa de mercado (F8); decisão de Vitor no chat (F14); no acervo, 34 arquivos de perfil `acc` e 3 de `gt7_ld` | 2026-07-15 e 2026-09-13 |
| Respondentes do questionário da barra de comparação | Deram a rodada 2 de feedback sobre a tela | Corpo do commit 2b88627 (F7); questionário em `SARU - barra de comparacao - perguntas.html` no Drive | 2026-08-29 |

Fontes:

| Id | Fonte | Onde |
|---|---|---|
| F1 | Plano canônico da PoC, 2026-08-28 | Drive `Trabalho/SARU/01_ Saru-KB/notas/plano-poc-core-trackday.md` |
| F2 | README do repositório, seções Estado, Rotas, Dívidas e Regras | `README.md` |
| F3 | Contrato de saída | `web/src/types/contract.ts` |
| F4 | Feedback de campo do engenheiro Giuliano, 2026-08-20 | `saru-app/docs/execution/2026-08-20-feedback-giuliano-engenheiro.md` |
| F5 | Mapa de parsing dos dois motores, 2026-08-29 | `docs/mapa-parsing-dois-motores.md` |
| F6 | Medições de formato | `docs/aim-rs2-medicao.md`, `docs/aim-gpk-rrk-medicao.md`, `docs/bosch-bmsbin-medicao.md` |
| F7 | Histórico git, em especial o commit 2b88627 de 2026-08-29 | `git log` |
| F8 | Personas e casos de uso do MVP anterior | `saru-docs/docs/produto/personas.md`, `use-cases.md`, `mvp.md` |
| F9 | Decisões de arquitetura do `saru-app` que a PoC herda | `saru-app/docs/adr/0033`, `0042`, `0047`, `0048`, `0049` |
| F10 | Calibração do limiar de frenagem por G, 2026-08-22 | `saru-app/docs/audit/2026-08-22-calibracao-frenagem-por-g.md` |
| F11 | Auditoria do repositório, 2026-09-12 | `SARU/_auditoria/04-poc-trackday.md` |
| F12 | Acervo de telemetria | repositório `SaruSysLab/dados_telemetria` |
| F13 | Catálogos, backlog e casos de uso da empresa, 2026-09-12 | `saru/docs/requisitos/02-catalogos.md`, `03-backlog.md`, `04-casos-de-uso.md` |
| F14 | Decisão de Vitor no chat, 2026-09-13: a família Piloto atende o piloto virtual de simulador, com o mesmo relatório da volta real. Virou E-RF-01 ampliado (logger real ou simulador) e E-RN-08 no núcleo | chat com Vitor |

## Desejos, necessidades e frustrações registradas

| Tipo | Registro (paráfrase) | Fonte | Virou |
|---|---|---|---|
| Necessidade | Detectar frenagem e viragem pela queda do G longitudinal e subida do G lateral, porque a maioria dos loggers amadores não tem pedal | F4, item F1 | PIL-OBJ-05, PIL-RF-23, PIL-RN-13 |
| Desejo | Velocidade GPS e traçado no topo da tela, porque é o que Garmin e i2 mostram primeiro | F4, item F2 | PIL-RNF-08 |
| Frustração | "delta OV" na tela sem explicação | F4, item B3 | PIL-RNF-08 |
| Frustração | Erro ao entrar de novo, espera indefinida para logar | F4, item B1 | Fora desta família (defeito do `saru-app`); PIL-RNF-07 evita a causa |
| Necessidade | Sem venue resolvido não pode haver setorização; default silencioso proibido | F1, etapa 4 | PIL-RN-01, PIL-RF-07 |
| Necessidade | Volta ideal nunca passa a melhor volta | F1, etapa 6 | PIL-RN-02, PIL-RN-03 |
| Necessidade | Reprocessar nunca sobrescreve; cada tentativa de leitura fica registrada com motivo | F1, etapa 2 | PIL-RN-04, PIL-RF-04 |
| Desejo | Análise por curva e por traçado já na primeira versão | F1, decisão 1 | PIL-RF-09 |
| Necessidade | Amostra nunca entra no Postgres; vai para Parquet com ponteiro | F1, decisão 2 | PIL-RNF-04, PIL-RF-06 |
| Latente | O piloto lê o N0 em 5 segundos no box, sem clicar em nada | F1, funil de zoom | PIL-RNF-08 |
| Necessidade | Degradação de bloco declarada na tela, com motivo | F1, fusão 2 | PIL-RF-13 |
| Necessidade | Exports reais de FuelTech e ProTune antes de escrever o leitor | F1, pedido bloqueante | PIL-PRB-07, PIL-RF-24 |
| Necessidade | Volta analisada e referência nunca são a mesma | F7 | PIL-RF-11, PIL-RN-14 |
| Necessidade | Acervo sem dono não vaza entre contas | F7 | PIL-RNF-07, PIL-RF-16 |
| Necessidade | Unidade interna SI, exibição em unidade de paddock | F9, ADR-0042 | PIL-RNF-09 |
| Necessidade | O piloto virtual recebe o mesmo relatório do piloto real; o que muda é a procedência do arquivo | F14 | PIL-RF-27, PIL-US-30 |
| Necessidade | Gravação de simulador resolve a pista pelo que o jogo declara, nunca por GPS, porque a coordenada exportada é placeholder | F14; caso GT7 medido em `readers/ld.py:29` | PIL-RN-17 |

## O que fica fora desta família

Nada disto é descartado. Cada item tem uma família de destino, registrada aqui para o
rascunho da PoC não perder o rastro.

| Item do rascunho | Destino | Motivo |
|---|---|---|
| PRB-05, OBJ-04, RF-22 comparativo do dia entre pilotos | família Campeonato | O comprador é o organizador, não o piloto |
| RF-17 live timing, RF-18 telemetria ao vivo e pit wall | família Campeonato | Acontece durante o evento, no box, não no cartão do piloto |
| RF-19 clima | família Campeonato | Serve a decisão de pista do evento |
| RF-14 contexto de bateria e ficha de setup, RF-15 espinha operacional | família Equipe (histórico) e família Engenheiro (setup) | O piloto consome como leitura; o registro é de quem opera o carro. A confirmar com Vitor se o piloto de track day precisa registrar pneu e clima da própria bateria |
| RF-20 assistente Sarue | fora das cinco famílias por enquanto | Decisão de Vitor em 2026-09-13; sem requisito nem teste |
| RF-21 ferramentas de box (pressão a frio, tempo previsto) | família Engenheiro | Ferramenta de quem prepara o carro |
| RF-25 Bosch bmsbin | família Engenheiro | Um único cliente (AMG GT4), 96 arquivos, formato de equipe |
