# Como a cronometragem entrega dados a terceiros

Pesquisa de 2026-09-14, feita por agente na web, com cada link aberto. Motivo: Vitor informou
que a ingestão por XML `resultspage` em rede local é caso de Brasília; fora, as empresas de
cronometragem têm API ou feed com lógica parecida com a da HH Timing, e o organizador autoriza
o uso sem bloqueio. Isso muda CAM-RF-01, CAM-RF-16, CAM-RN-02 e CAM-CT-18 da família
Campeonato.

## O que foi confirmado

| Fornecedor | Produto | Entrega | Acesso | Fonte |
|---|---|---|---|---|
| MyLaps | Orbits, protocolo RMonitor | TCP porta 50000, texto ASCII linha a linha (mensagens `$A`, `$F`, `$G`) | protocolo público; a porta é habilitada pelo operador da pista | timingguys.com/topic/live-timing-with-mylaps-orbits-5-software |
| MyLaps | Orbits, Local App Feed | TCP porta 60000, configurado localmente | operador da pista | mesma página |
| MyLaps | Orbits, exportação XML | plugin restrito a Orbits Pro e Advanced | licença do operador | mesma página |
| MyLaps | Speedhive, API de resultados | REST, sem documentação oficial pública | integração não oficial de terceiros | github.com/ncrosty58/speedhive-tools |
| Al Kamel | protocolo Alkamel V2 | JSON; transporte não explícito na página | usuário e senha da Al Kamel, filtragem por credencial desde 2026 | help.hhtiming.com/timekeeper-specific-info/alkamel-v2 |
| HH Timing | DMI (Data Management Integration) | modo local (mesma máquina) ou API da HH Data Management | recebe RIS (IndyCar), Natsoft, IMSA Timing e Alkamel; lista não exaustiva | help.hh-dm.com/dmi/using-the-dmi |
| TSL Timing | feed TSL | feed pela internet, host e porta dados pelo cronometrista; algumas séries exigem chave de API | credencial | help.hhtiming.com/timekeeper-specific-info/tsl-timing |
| Race Result | REST API | REST com chave de API e id de cliente; 1 requisição por segundo por URL e IP | cliente autorizado | raceresult.com/en/support/kb?id=22003-REST-API-Interface |
| Race Monitor | API | endpoints de corrida, série e resultado; protocolo não especificado | cadastro prévio; a corrida pode restringir terceiros | race-monitor.com/Home/API |
| FastCrono (Brasil) | cronometragem de pista | não informado no site | não informado | fastcrono.com.br/resultados/resultados-automobilismo: atende Interlagos, Goiânia, Curitiba, Velocitta, Cascavel e Tarumã |
| Audace Tech, Chronon (Brasil) | cronometragem de categorias nacionais | não informado no site | não informado | crono.audacetech.com.br: Cascavel, Interlagos, Goiânia, Velocitta, Santa Cruz do Sul, Brasília na temporada 2026 |

## O que isso muda no produto

1. A entrada da família Campeonato é "fonte de cronometragem", com pelo menos três adaptadores:
   XML `resultspage` em rede local (Brasília), feed RMonitor por TCP (qualquer pista com Orbits
   e porta liberada) e API do cronometrista (Alkamel V2, TSL, Race Result, Race Monitor), cada um
   com credencial própria.
2. A autorização do organizador é registro de contrato, não bloqueio de ingestão: CAM-RF-16 e
   CAM-RN-02 mudam de "recusar sem autorização" para "registrar quem autorizou e qual fonte".
3. Quem cronometra fora de Brasília (FastCrono, Audace Tech) não publica o sistema que usa. A
   pergunta "que feed vocês liberam para o organizador?" vai para a entrevista com organizador
   (CAM-OBJ-05).

## Não confirmado

Transporte do Alkamel V2; API do Apex Timing (nome colide com outros produtos); existência de
Cronoservice; protocolo do Race Monitor; sistema usado pela FastCrono e pela Audace Tech;
se racingcrono.com.br usa MyLaps (afirmação de resumo de busca, página não aberta).
