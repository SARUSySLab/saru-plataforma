# Problema e objetivos da SARU

Rascunho 1, 2026-09-12. Nível: empresa. Vai para o repositório da empresa na fase 2 do plano.
Leitor: Vitor, Lucas e quem entrar no time. Cada linha cita a fonte.

## Cenário atual

A SARU é uma empresa de software para automobilismo fundada por Vitor Toledo em 2026. Em três
meses construiu duas gerações de produto (o `saru-app` de junho a agosto e a PoC de track day
desde 28 de agosto), 222 documentos ainda válidos e leitores de 12 formatos de logger (F6).
Nada disso nasceu de requisitos escritos. O que existe atende piloto, engenheiro, equipe e
campeonato ao mesmo tempo, o que dificulta vender e manter (F1).

O posicionamento decidido em julho é o "gap do meio": física de nível profissional entregue
como software web colaborativo a preço de equipe nacional, entre o software de F1 que a
equipe brasileira não paga e o app de celular que não interpreta nada (F2). A pesquisa de
setembro sobre pit wall mostra o degrau seguinte: engenharia de pista ao vivo, local-first,
que hoje só categoria de ponta tem (F5).

## Problema

| Id | Problema | Quem sofre | Evidência (fonte, data) |
|---|---|---|---|
| PRB-01 | O piloto amador não sabe por que perde tempo e ninguém interpreta o dado do logger dele | Piloto de track day e sim racer | F3 personas P2 e P3, 2026-07-15; F4 relato de campo, 2026-08-20 |
| PRB-02 | A equipe nacional decide setup no feeling porque a ferramenta profissional é cara, travada em desktop e sem colaboração | Chefe de equipe e engenheiro de pista | F2 seção 1 e F3 persona P1, 2026-07-15 |
| PRB-03 | Cada logger grava um formato próprio e cada software fala só com o seu; o engenheiro junta tudo na mão | Engenheiro de pista, consultor | F6 mapa de 13 formatos, 2026-08-29; F4 item F1 |
| PRB-04 | O organizador de evento e o campeonato não têm comparativo do dia nem pit wall acessível; telemetria ao vivo é privilégio de categoria de ponta | Organizador, campeonato, equipe pequena | F7 plano etapa 7, 2026-08-28; F5 pesquisa, 2026-09-12 |
| PRB-05 | O conhecimento de engenharia (dinâmica veicular, pneu, simulação) fica com poucos e não é traduzido para quem dirige ou decide | Piloto, chefe de equipe, aluno | F1 Vitor, 2026-09-12; F3 persona P4 |
| PRB-06 | A própria SARU construiu muito sem requisitos, sem segmentação por cliente e sem processo escrito para quem entra no time | Vitor, Lucas, próximos membros | F1 Vitor, 2026-09-12; F8 auditoria, 2026-09-12 |

## Objetivos

Resultado mensurável, não funcionalidade. Meta "a definir" fica marcada até Vitor fixar.

| Id | Objetivo | Indicador | Meta | Problema |
|---|---|---|---|---|
| OBJ-01 | Uma família de produto por nicho, cada uma com requisitos, oferta e preço próprios | Famílias com `01` e `02` de requisitos aprovados | 5 (piloto, engenheiro, equipe, campeonato, aluno) antes de qualquer código novo | PRB-06 |
| OBJ-02 | Reaproveitar o que já existe em vez de reescrever | Documentos vigentes e módulos da PoC com destino numa família | 100% dos 222 documentos e dos 44 módulos classificados | PRB-06 |
| OBJ-03 | Nunca vender o que o código não sustenta | Afirmações públicas com status validado | 100% (decisão ratificada 2 de 2026-07-15) | PRB-05 |
| OBJ-04 | Todo resultado tem uma versão que um leigo entende e usa | Telas e relatórios com texto em linguagem de piloto, sem jargão | 100% | PRB-01, PRB-05 |
| OBJ-05 | Apoio de pista presencial e remoto, com ou sem internet no autódromo | Famílias com modo local-first especificado | a definir; presencial é a prioridade, remoto sem data (Vitor, 2026-09-12) | PRB-04 |
| OBJ-06 | Elevar o nível de dado e organização do automobilismo brasileiro | Eventos e equipes usando a SARU em pista por ano | a definir; é o objetivo final da empresa (Vitor, 2026-09-12) | PRB-02, PRB-04 |

## Famílias de produto

Uma família por nicho. Recurso usado por mais de uma família vive no núcleo compartilhado.
Cada família terá os seus próprios `docs/requisitos/`. Decisão de Vitor em 2026-09-12 (F1).

| Família | Nicho | Quem compra | Exemplo do que entrega |
|---|---|---|---|
| Piloto | Piloto amador de track day e sim racer | P2, P3 | Relatório interpretado: onde perdi tempo, o que treinar |
| Engenheiro | Engenheiro de pista e consultor | Engenheiro de performance | Análise multi-formato, comparação, simulação, ferramentas de box |
| Equipe | Chefe de equipe nacional | P1 | Setup, operação do evento, histórico de carro e piloto |
| Campeonato | Organizador de evento e campeonato | Organizador | Comparativo do dia, cronometragem, pit wall ao vivo |
| Aluno | Quem aprende fazendo | P4 e comunidade | Produto que ensina com o dado do próprio aluno; pontuação e trilha |
| Hase (parceiro) | Curso de formação | P4 | Infoproduto do parceiro; a SARU ajuda a expandir; não é família de software |
| Hardware (futuro) | Aquisição de dado no carro, transversal às famílias | Piloto e equipe | Logger próprio da SARU; só depois da consolidação do software e da conversa com a DashAuto (F1, F10) |

## Stakeholders e fontes

| Stakeholder | Papel | Como foi ouvido | Data |
|---|---|---|---|
| Vitor Toledo | Fundador, dono da física, aprova requisitos e regras | Chat desta sessão; decisões de 2026-07-15 | 2026-09-12 |
| Lucas Antunes | Desenvolvedor, dono da PoC | Plano canônico e commits | 2026-08-28 a 2026-08-30 |
| Giuliano | Engenheiro de pista sênior, usou o produto em campo | Relato transcrito por Vitor | 2026-08-20 |
| Piloto de track day (P3), sim racer (P2), chefe de equipe (P1), aluno (P4) | Compradores por nicho | Pesquisa de mercado; nenhum entrevistado diretamente | 2026-07-15 |
| Organizador de evento e campeonato | Comprador do comparativo do dia e do pit wall | Só por documento; não entrevistado | 2026-08-28 |

| Id | Fonte | Onde | Validação |
|---|---|---|---|
| F1 | Respostas de Vitor no chat | esta sessão | direta |
| F2 | Documento mestre de produto e negócios | `_arquivo/saru-KB/50_company/SARU_MASTER_PRODUTO_NEGOCIOS.md` | links de mercado não abertos |
| F3 | Personas de mercado | `_arquivo/saru-docs/docs/produto/personas.md` | idem |
| F4 | Feedback de campo de Giuliano | `_arquivo/saru-app/docs/execution/2026-08-20-feedback-giuliano-engenheiro.md` | relato, marcado pelo autor |
| F5 | Pesquisa "Dashboard de Engenharia de Performance e Estratégia, MF Ghost e HH Timing" | Google Doc no Drive, 26 links | nenhum link aberto ainda |
| F6 | Mapa de parsing e catálogo de formatos | `saru-poc-trackday/docs/mapa-parsing-dois-motores.md` | medido no código |
| F7 | Plano canônico da PoC | Drive `Trabalho/SARU/01_ Saru-KB/notas/plano-poc-core-trackday.md` | decisões de Lucas e Vitor |
| F8 | Auditoria da guarda-chuva | `_auditoria/00-plano-consolidado.md` | medido |
| F9 | Anúncio do Garmin Catalyst 2 na loja Race Cars For You, enviado por Vitor | imagem em `~/.claude/uploads/.../0d03776e-image.jpg` | lista de funções do fabricante; preço e detalhe não conferidos |
| F10 | Pesquisa RealDash, Napko e DashAuto para integração de telemetria, 2026-08-29 | Drive `Trabalho/SARU/01_ Saru-KB/notas/pesquisa_realdash_napko_dashauto_integracao_telemetria*.md` | não lida nesta sessão; links não abertos |

## Desejos, necessidades e frustrações registradas

| Tipo | Registro (paráfrase) | Fonte | Virou |
|---|---|---|---|
| Necessidade | Segmentar por nicho (piloto, engenheiro, equipe, campeonato) porque é mais fácil de fazer e de vender | F1 | OBJ-01 |
| Necessidade | Reaproveitar o muito que já foi feito, refazendo só os passos pulados (requisitos, arquitetura) | F1 | OBJ-02 |
| Desejo | Organizar o automobilismo brasileiro e mundial, elevar performance, dado e organização ao máximo | F1 | OBJ-06 |
| Necessidade | Acoplar produtos novos de apoio de pista presencial e remoto | F1 | OBJ-05 |
| Necessidade | Insights, KPIs, visualização, decisão, engenharia, simulação e tradução para qualquer um entender | F1 | OBJ-04, famílias |
| Frustração | O produto atual atende todos ao mesmo tempo e está muito incompleto | F1 | PRB-06 |
| Necessidade | O pitch só afirma o que o código sustenta | F2 decisão 2 | OBJ-03 |
| Necessidade | Loggers amadores não têm pedal; todos têm acelerômetro | F4 | família piloto |
| Necessidade | Pit wall sem vídeo, dado por distância, local-first, gap e interval separados | F5 | família campeonato |
| Necessidade | Manter os modelos de simulação com engenharia reversa de parâmetros: analisar o arquivo e o carro, simular uma volta parecida com modelo de piloto e achar comandos e comportamentos possíveis. Nunca tinha sido escrito como requisito | F1, 2026-09-13 | E-RF-09 |
| Desejo | Cobrir tudo o que o Garmin Catalyst 2 faz, no software primeiro | F1, F9 | tabela de referência abaixo |
| Desejo | Ter hardware próprio de aquisição; pré-condição: software consolidado e parceria com a DashAuto | F1, F10 | linha Hardware (futuro) |

## Referência de mercado: Garmin Catalyst 2 (F9)

Régua para a família Piloto. Coluna "SARU hoje" medida na PoC em 2026-09-12 (F6, F7, F8).

| Função anunciada | SARU hoje | Vai para |
|---|---|---|
| True Optimal Lap (volta ideal) | Existe, com a guarda "ideal nunca passa a melhor volta" | Núcleo, E-RF-03 e E-RF-04 |
| Coaching por áudio em tempo real na pista | Não existe. A PoC tem pit wall ao vivo por dado, sem voz e sem estar no carro | Piloto; depende de app no carro ou de hardware próprio |
| Insights personalizados depois de cada sessão | Existe: relatório em quatro níveis, onde perdi tempo por curva | Piloto |
| Análise de circuito e de arrancada (drag strip) | Só circuito. Arrancada não existe | Piloto; fora do escopo até haver pedido |
| Ranking e comparação entre sessões | Comparação entre voltas e entre gravações existe; ranking entre pilotos não | Piloto (comparação) e Campeonato (ranking) |
| Vídeo HD com dado sobreposto | Não existe. O acervo tem vídeo pareado com telemetria (`dados_telemetria/PARES-VIDEO.md`) | Piloto; depende de câmera ou hardware próprio |
| Hardware dedicado no carro | Não existe. A SARU lê 12 formatos de loggers de terceiros | Hardware (futuro), após DashAuto |

Leitura: das sete funções, a SARU cobre duas por inteiro e uma pela metade só com software.
As outras quatro dependem de estar no carro, o que hoje é o logger de terceiro.
