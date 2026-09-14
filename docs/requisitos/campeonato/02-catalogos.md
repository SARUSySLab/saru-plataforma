# Catálogos da família Campeonato

Este arquivo é a lista completa do que a família Campeonato faz, como ela se comporta, que
regras obedece e como cada uma dessas coisas é provada. Quem compra é o organizador do
evento.

Rascunho 1, 2026-09-14. Um id por linha, id nunca reaproveitado. Versão sobe quando o verbo
ou o objeto muda. Origem cita o objetivo CAM-OBJ do `01-problema-e-objetivos.md`, as fontes CAM-F1 a
CAM-F13 do mesmo arquivo, um `E-` do catálogo da empresa ou um caminho de código. Status medido no código da PoC em
2026-09-14: implementado, parcial ou proposto. Onde um requisito depende de resposta de
Vitor, a linha diz "a confirmar com Vitor" e não inventa número.

## O que veio da família Piloto

Os quatro itens empurrados para cá (CAM-F10) foram redefinidos com id `CAM-`, porque nenhum
deles chegou a existir como `PIL-RF` no catálogo da família Piloto: eles saíram do rascunho
da PoC e vieram sem passar pela família Piloto. A coluna Origem de cada linha cita o id de
rascunho de onde veio.

| Rascunho da PoC | Virou aqui |
|---|---|
| RF-17 live timing | CAM-RF-01 a CAM-RF-09 |
| RF-18 telemetria ao vivo e pit wall | CAM-RF-10, CAM-RF-11, CAM-RF-12 |
| RF-19 clima | CAM-RF-14 |
| RF-22 comparativo do dia entre pilotos | CAM-RF-13 |

## Requisitos funcionais (CAM-RF)

| Id | Nome | Declaração | Nível | Núcleo | Origem | Prioridade | Critérios | Versão | Status |
|---|---|---|---|---|---|---|---|---|---|
| CAM-RF-01 | Ingerir o XML da cronometragem | O sistema deve receber o XML `resultspage` da cronometragem do autódromo, postado por um relay que roda na rede local do evento, e recusar com motivo o corpo que não for um `resultspage` com label `eventname` | produto | E-RF-01 | CAM-OBJ-01, CAM-OBJ-03; rascunho RF-17; CAM-F5; `livetiming.py`, `rotas/campeonato.py` | must | CAM-CT-01, CAM-CT-04 | 1 | implementado |
| CAM-RF-02 | Derivar o histórico volta a volta | O sistema deve derivar as passagens de cada carro por comparação entre snapshots consecutivos, porque o XML só carrega as 3 últimas voltas, e acumular o resultado sem sobrescrever o que já foi gravado | produto | E-RF-04 | CAM-OBJ-03; rascunho RF-17; CAM-PRB-03; CAM-F5 | should | CAM-CT-03, CAM-CT-19 | 1 | implementado; conferência contra o resultado oficial a escrever |
| CAM-RF-03 | Guardar o snapshot bruto do evento | O sistema deve guardar cada XML recebido como veio, identificado por SHA-256, e tratar o reenvio idêntico como não operação | produto | E-RF-04 | CAM-OBJ-03; rascunho RF-17; `livetiming.ingerir` | must | CAM-CT-02 | 1 | implementado |
| CAM-RF-04 | Montar a torre de tempos do evento | O sistema deve exibir, por carro, posição, número, piloto, carro, classe, voltas, gap para o carro da frente, diferença para o líder, última volta e melhor volta, mantendo gap e diferença como texto quando a cronometragem os entrega em voltas | usuário | E-RF-05 | CAM-OBJ-01; rascunho RF-17; CAM-F5; CAM-F8 | must | CAM-CT-04, CAM-CT-05, CAM-CT-13 | 1 | parcial: o dado sai completo do parse; a tela só existe como mock |
| CAM-RF-05 | Declarar a idade de cada linha | O sistema deve mostrar, por carro, quanto tempo passou desde a última passagem, comparando a hora da passagem com a hora do snapshot, e nunca apresentar número velho como se fosse agora | usuário | E-RNF-01 | rascunho RF-17 e RF-18; CAM-OBJ-02; CAM-F5, CAM-F6 | must | CAM-CT-06 | 1 | parcial: implementado no painel ao vivo; ausente na torre |
| CAM-RF-06 | Resolver a pista do evento | O sistema deve casar o nome de pista da cronometragem com um layout do catálogo, primeiro pelo apelido cadastrado, depois pelos tokens do nome, desempatando pelo comprimento declarado no XML, e declarar não resolvida quando nenhum casa | produto | E-RF-03 | CAM-OBJ-01; rascunho RF-17; `livetiming.resolver_layout` | should | CAM-CT-07 | 1 | implementado, sem critério verificado: CAM-CT-07 a escrever |
| CAM-RF-07 | Desenhar o mapa do evento | O sistema deve entregar o traçado medido do layout do evento para posicionar os carros, e declarar o que falta quando não há layout resolvido ou nenhuma volta com GPS daquele layout no acervo | usuário | E-RF-08 | CAM-OBJ-01; rascunho RF-17; `rotas/campeonato.py` | should | CAM-CT-07 | 1 | implementado em esqueleto, sem critério verificado: CAM-CT-07 a escrever |
| CAM-RF-08 | Empurrar o estado para a tela | O sistema deve enviar o estado do evento por stream ao navegador a cada snapshot novo, com batimento periódico para atravessar proxy, e a tela deve cair para consulta repetida se o stream morrer | produto | E-RF-05 | CAM-OBJ-01, CAM-OBJ-02; rascunho RF-17; `rotas/campeonato.py` | should | CAM-CT-13 | 1 | implementado |
| CAM-RF-09 | Registrar os avisos da direção de prova | O sistema deve ingerir o feed de avisos da cronometragem, guardar o texto cru de cada aviso, classificá-lo entre track limit, perda de volta, indefinido e texto, e contar por carro só o que foi anunciado como track limit | produto | E-RF-04 | CAM-OBJ-01; rascunho RF-17; pedido de Vitor em 2026-08-29; `022_lt_aviso.sql` | should | CAM-CT-08, CAM-CT-09 | 1 | implementado |
| CAM-RF-10 | Receber a telemetria do carro ao vivo | O sistema deve receber lotes curtos de amostras do gateway do carro, de cerca de 250 ms cada, autenticados por token do próprio carro, deduplicados por veículo, sessão e número de sequência | produto | E-RF-01 | CAM-OBJ-01; rascunho RF-18; CAM-F6; `vivo.py`, `023_veiculo_gateway.sql` | should | CAM-CT-10, CAM-CT-11, CAM-CT-14 | 1 | implementado |
| CAM-RF-11 | Manter o buffer quente do pit wall | O sistema deve guardar em memória os últimos 300 s de amostras de cada carro, que é o que o painel lê, sem gravar amostra em tabela do banco | produto | E-RF-04 | CAM-OBJ-01; rascunho RF-18; `vivo.JANELA_S` | should | CAM-CT-06 | 1 | implementado |
| CAM-RF-12 | Mostrar o pit wall do box | O sistema deve exibir, por carro do dono, os canais do buffer quente, a idade do último pacote e os avisos do evento, numa tela só | usuário | E-RF-05 | CAM-OBJ-01; rascunho RF-18; CAM-F8 | should | CAM-CT-06 | 1 | parcial: a rota do painel existe; a tela só existe como mock |
| CAM-RF-13 | Comparar os pilotos do dia | O sistema deve emitir o comparativo do dia entre pilotos do mesmo evento, com as perdas por trecho entre um piloto e uma referência, usando o mesmo motor de perdas do relatório do piloto e trocando volta por piloto como dimensão de comparação | usuário | E-RF-05, E-RF-07 | CAM-OBJ-01, CAM-OBJ-04; rascunho RF-22; CAM-F9; CAM-PRB-02 | must | CAM-CT-16 | 1 | proposto: sem classe de veículo confiável, o pódio por classe fica fora (`023_veiculo_gateway.sql`) |
| CAM-RF-14 | Entregar o clima da pista do evento | O sistema deve servir a previsão na coordenada do layout do evento por uma cascata de fontes, com cache de 15 minutos no banco, declarando qual fonte respondeu e se o dado está vencido | usuário | E-RF-05 | CAM-OBJ-01; rascunho RF-19; `clima.py`, `rotas/clima.py` | should | CAM-CT-15 | 1 | implementado; temperatura de pista continua estimativa declarada, nenhuma fonte mede asfalto |
| CAM-RF-15 | Emitir credencial de máquina | O sistema deve emitir credencial separada para o relay da cronometragem e para o gateway de cada carro, mostrar o token em claro uma única vez e permitir revogar uma credencial sem derrubar as outras nem as sessões humanas | produto | E-RF-06 | CAM-OBJ-01; rascunho RF-17 e RF-18; `021_livetiming.sql`, `023_veiculo_gateway.sql` | must | CAM-CT-12 | 1 | implementado |
| CAM-RF-16 | Exigir autorização para importar o evento | O sistema deve registrar quem autorizou o uso do XML da cronometragem de um evento antes de importá-lo, e recusar a ingestão de evento sem autorização registrada | negócio | E-RF-06 | CAM-OBJ-03, CAM-OBJ-04; CAM-PRB-03; a confirmar com Vitor: quem autoriza, o organizador ou o autódromo | must | CAM-CT-18 | 1 | proposto |

## Requisitos não funcionais (CAM-RNF)

Categorias pelo URPS+, como na família Piloto.

| Id | Categoria | Declaração | Métrica e meta | Núcleo | Origem | Prioridade | Critérios | Versão | Status |
|---|---|---|---|---|---|---|---|---|---|
| CAM-RNF-01 | Disponibilidade | A torre de tempos e o comparativo do dia funcionam com a rede externa desligada, rodando na rede local do box, e sincronizam quando a rede volta | Um evento operado ponta a ponta com a rede externa desligada. Meta de latência a definir, a confirmar com Vitor | E-RNF-05 | CAM-OBJ-01; CAM-F5, CAM-F6 | must | CAM-CT-17 | 1 | proposto: hoje a produção fica no Railway e não enxerga a rede local do autódromo |
| CAM-RNF-02 | Desempenho | O pit wall mostra o último dado recebido dentro de um limite fixado | Medir o tempo entre o POST do lote e a linha na tela. O que está medido hoje: o lote é de cerca de 250 ms de amostras e o stream consulta o banco 1 vez por segundo. Meta a confirmar com Vitor | própria da família | CAM-F6; `rotas/campeonato.py`, `rotas/vivo.py` | should | CAM-CT-06 | 1 | proposto, meta pendente |
| CAM-RNF-03 | Honestidade do dado | Toda linha da torre e do painel carrega a idade do dado, e acima do limiar de silêncio a linha deixa de ser tratada como ao vivo | Limiar medido no código: 15 s (`vivo.SILENCIO_S`). 100% das linhas com idade declarada | E-RNF-01 | CAM-OBJ-02; CAM-PRB-04 | must | CAM-CT-06 | 1 | implementado no painel, ausente na torre |
| CAM-RNF-04 | Usabilidade | Gap e diferença para o líder nunca se confundem: aparecem em colunas separadas e rotuladas, e os dois podem ser texto | Zero coluna que some as duas grandezas; o mock N1 já desenha as duas (CAM-F8) | E-RNF-06 | CAM-F5, CAM-F8 | must | CAM-CT-05 | 1 | parcial: separados no parse, sem tela |
| CAM-RNF-05 | Confiabilidade | Reenviar o mesmo XML, o mesmo feed de avisos ou o mesmo lote não duplica passagem, aviso nem amostra | Snapshot deduplicado por SHA-256, aviso por evento, data, hora e texto, lote por veículo, sessão e sequência | E-RNF-02 | `livetiming.py`, `022_lt_aviso.sql`, `vivo.py` | must | CAM-CT-02, CAM-CT-10 | 1 | implementado |
| CAM-RNF-06 | Segurança | A escrita é de máquina e a leitura é de humano logado; o token fica gravado só como SHA-256 e é revogável um a um | Ingestão com cookie de humano é recusada; leitura sem login é recusada; dump de banco não contém token em claro | E-RNF-07 | `021_livetiming.sql`, `rotas/campeonato.py`, `rotas/vivo.py` | must | CAM-CT-12, CAM-CT-13, CAM-CT-14 | 1 | implementado |
| CAM-RNF-07 | Usabilidade | A torre é lida no box em 5 segundos, sem clique, com rótulo por extenso | Revisão de rótulos com um organizador; zero abreviação não expandida | E-RNF-06 | CAM-OBJ-05; CAM-F8 | should | CAM-CT-17 | 1 | proposto: nenhum organizador foi ouvido (CAM-PRB-06) |
| CAM-RNF-08 | Suportabilidade | Trocar a fonte de clima não muda o resto do sistema | As fontes saem no mesmo formato e cada resposta declara qual respondeu | própria da família | `clima.py`; resposta ao 429 do Open-Meteo em 2026-08-29, o mesmo episódio de CAM-RN-10 | should | CAM-CT-15 | 1 | implementado |

## Regras de negócio (CAM-RN)

| Id | Regra | Física ou calibração | Fonte | Requisitos condicionados | Versão |
|---|---|---|---|---|---|
| CAM-RN-01 | Se a cronometragem oficial e a telemetria do carro divergem, então a oficial manda na classificação e a divergência é declarada na tela | não | CAM-F5; `rotas/campeonato.py`, que trata o live timing como placar do evento e não como acervo de conta | CAM-RF-04, CAM-RF-13 | 1 |
| CAM-RN-02 | Se não há autorização registrada para usar o XML da cronometragem de um evento, então o evento não é importado | não | CAM-PRB-03. Quem autoriza, organizador ou autódromo: a confirmar com Vitor | CAM-RF-01, CAM-RF-16 | 1 |
| CAM-RN-03 | Se o XML não traz o label `eventname`, então o corpo é recusado com motivo e nada é gravado | não | `livetiming.parse_resultspage` | CAM-RF-01 | 1 |
| CAM-RN-04 | Se o número do carro tem zero à esquerda, então ele é tratado como texto, porque converter para inteiro funde carros diferentes | não | Grid medido no 12º MBR Time Attack, com #08, #033, #001 e #2 ao mesmo tempo (`022_lt_aviso.sql`, `023_veiculo_gateway.sql`) | CAM-RF-04, CAM-RF-09 | 1 |
| CAM-RN-05 | Se um campo de setor vem vazio, então ele fica fora do snapshot e a coluna de setor da torre é declarada indisponível, nunca preenchida por estimativa | não | CAM-F5, medido no evento real; E-RNF-01 | CAM-RF-01, CAM-RF-04 | 1 |
| CAM-RN-06 | Se o aviso da direção de prova não traz o prefixo que o identifica como track limit, então ele entra como indefinido, aparece na lista e fica fora da contagem por carro | não | `livetiming._classificar_aviso`; a linha das 09:16 da amostra do MBR | CAM-RF-09 | 1 |
| CAM-RN-07 | Se o mesmo trecho chegou ao vivo e depois pelo cartão do gateway, então o arquivo vence o rádio e o trecho recebido ao vivo é marcado como provisório | não | `vivo.py`, decisão de Lucas em 2026-08-30; `023_veiculo_gateway.sql` | CAM-RF-10, CAM-RF-11 | 1 |
| CAM-RN-08 | Se um lote chega fora de ordem, então ele é contado e declarado, e as amostras entram assim mesmo | não | `vivo.BufferVivo.registrar`; em rede ruim o pacote atrasado ainda carrega amostra boa | CAM-RF-10 | 1 |
| CAM-RN-09 | Se o nome de pista da cronometragem não casa com nenhum layout do catálogo, ou casa com mais de um sem comprimento que desempate, então o evento fica sem layout e o mapa declara o que falta em vez de desenhar outra pista | sim | `livetiming.resolver_layout`. O limiar de 15% de diferença de comprimento está no código e nunca foi aprovado: é calibração e depende de E-RN-02, a confirmar com Vitor | CAM-RF-06, CAM-RF-07 | 1 |
| CAM-RN-10 | Se a fonte de clima falha e existe cache, então o sistema serve o dado velho com a idade declarada; se não há nada salvo, devolve erro em vez de número inventado | não | `clima.py`, resposta ao 429 do Open-Meteo em 2026-08-29 | CAM-RF-14 | 1 |
| CAM-RN-11 | Se a passagem derivada do diff entre snapshots discorda do resultado oficial do evento além da tolerância, então a passagem é marcada como não conferida | sim | CAM-OBJ-03. A tolerância volta a volta é calibração e depende de E-RN-02: a confirmar com Vitor, e ainda falta um resultado oficial para comparar | CAM-RF-02 | 1 |
| CAM-RN-12 | Se um evento hospeda mais de um campeonato ao mesmo tempo, então cada carro pertence ao campeonato que o evento declara e a disciplina vem do evento, nunca inferida do carro ou da classe | não | CAM-F12, latente registrado no 01; ainda sem campo no código da PoC | CAM-RF-01, CAM-RF-04, CAM-RF-13 | 1 |

## Critérios de aceitação (CAM-CT)

| Id | Requisitos | Dado | Quando | Então | Como verificar |
|---|---|---|---|---|---|
| CAM-CT-01 | CAM-RF-01, CAM-RN-03 | um corpo que não é um `resultspage` | é postado na ingestão | recusa com motivo e nada é gravado | `tests/test_livetiming.py::test_xml_que_nao_e_resultspage_e_recusado` |
| CAM-CT-02 | CAM-RF-03, CAM-RNF-05 | um XML já ingerido | o relay reenvia o mesmo XML | nenhum snapshot novo e nenhuma passagem duplicada | `tests/test_livetiming.py::test_ingest_grava_deduplica_e_deriva_passagens` |
| CAM-CT-03 | CAM-RF-02 | dois snapshots consecutivos do mesmo evento | o segundo é ingerido | as passagens que só existem na diferença entre os dois são gravadas | `tests/test_livetiming.py::test_ingest_grava_deduplica_e_deriva_passagens` |
| CAM-CT-04 | CAM-RF-01, CAM-RF-04 | o XML real do 12º MBR Time Attack, 84 carros e 9 classes | é parseado | posição, número, piloto, carro, classe, voltas, gap e diferença saem normalizados, com tempo em ponto e velocidade em vírgula lidos certo | `tests/test_livetiming.py::test_parse_do_xml_real_do_mbr`, `::test_segundos_cobre_os_tres_formatos_do_xml_real`, `::test_nome_e_carro_separa_no_pipe_do_fullname` |
| CAM-CT-05 | CAM-RF-04, CAM-RNF-04 | um carro cujo gap vem escrito como "4 Voltas" | a torre é montada | gap e diferença para o líder aparecem em colunas separadas, como texto, e nenhum dos dois vira número | a escrever; o parse já mantém os dois como texto |
| CAM-CT-06 | CAM-RF-05, CAM-RF-11, CAM-RF-12, CAM-RNF-03 | um carro sem pacote há mais de 15 s | o painel é aberto | a linha declara a idade do dado e não afirma que o carro está parado | `tests/test_vivo.py::test_painel_declara_idade_do_dado`, `::test_carro_sem_pacote_aparece_no_painel_sem_fingir_que_esta_parado` |
| CAM-CT-07 | CAM-RF-06, CAM-RF-07, CAM-RN-09 | um nome de pista que não casa com layout nenhum do catálogo | o evento é ingerido e o mapa é pedido | o evento fica sem layout e o mapa responde indisponível com o motivo | a escrever |
| CAM-CT-08 | CAM-RF-09, CAM-RN-06 | o feed de avisos real do MBR | é ingerido | track limit e perda de volta são classificados, o aviso sem prefixo fica indefinido e fora da contagem | `tests/test_livetiming.py::test_parse_avisos_le_o_feed_real_do_mbr`, `::test_aviso_sem_prefixo_fica_indefinido_e_nao_conta_como_track_limit`, `::test_penalidade_de_perda_de_volta_e_classificada`, `::test_contagem_de_track_limits_soma_so_o_que_foi_anunciado_como_tal` |
| CAM-CT-09 | CAM-RF-09, CAM-RN-04 | um grid com #08, #033, #001 e #2 | os avisos são extraídos | cada número continua texto, a reincidência entre parênteses vira contagem e nenhum carro é fundido | `tests/test_livetiming.py::test_numero_de_carro_e_string_com_zero_a_esquerda`, `::test_reincidencia_entre_parenteses_vira_contagem` |
| CAM-CT-10 | CAM-RF-10, CAM-RNF-05 | um lote do gateway já recebido | é reenviado com a mesma sequência | a resposta é aceita e nenhuma amostra é duplicada | `tests/test_vivo.py::test_lote_aceito_e_reenvio_e_idempotente`, `::test_lote_vazio_ou_sem_seq_e_recusado_com_motivo` |
| CAM-CT-11 | CAM-RF-10, CAM-RN-08 | um lote com sequência menor que a última recebida | chega ao servidor | é contado como fora de ordem e as amostras entram | `tests/test_vivo.py::test_sequencia_fora_de_ordem_e_contada_e_nao_descartada` |
| CAM-CT-12 | CAM-RF-15, CAM-RNF-06 | um token de máquina revogado e um cookie de humano | são usados na ingestão | os dois são recusados | `tests/test_livetiming.py::test_token_revogado_para_de_autenticar`, `::test_ingest_exige_token_de_maquina_e_cookie_nao_vale`, `tests/test_vivo.py::test_sem_token_recusa`, `::test_token_invalido_recusa` |
| CAM-CT-13 | CAM-RF-04, CAM-RF-08, CAM-RNF-06 | uma rota de leitura do campeonato | é chamada sem login | é recusada | `tests/test_livetiming.py::test_leitura_exige_login` |
| CAM-CT-14 | CAM-RF-10, CAM-RNF-06 | dois carros do mesmo dono mandando lote | os painéis são lidos | o dado de um carro não aparece no outro | `tests/test_vivo.py::test_dois_carros_do_mesmo_dono_nao_misturam_dado` |
| CAM-CT-15 | CAM-RF-14, CAM-RN-10, CAM-RNF-08 | a fonte de clima fora do ar e um cache vencido | a previsão é pedida | serve o dado velho marcado como velho, com a fonte declarada | `tests/test_clima.py::test_fonte_fora_do_ar_serve_cache_vencido_marcado_como_velho`, `::test_open_meteo_e_metno_falham_serve_cache_vencido`, `::test_open_meteo_e_metno_falham_sem_cache_propaga` |
| CAM-CT-16 | CAM-RF-13 | um evento com dois pilotos e voltas do mesmo layout | o comparativo do dia é gerado | as perdas por trecho entre os dois saem ordenadas da maior perda ao maior ganho | a escrever |
| CAM-CT-17 | CAM-RNF-01, CAM-RNF-07 | um evento real com a rede externa desligada | a torre e o comparativo do dia são operados no box | os dois funcionam e sincronizam quando a rede volta, e um organizador diz em uma frase o que viu | a escrever; quantos eventos fecham o objetivo é a confirmar com Vitor |
| CAM-CT-18 | CAM-RF-16, CAM-RN-02 | um XML de evento sem autorização registrada | é postado | a ingestão recusa com motivo | a escrever; quem autoriza é a confirmar com Vitor |
| CAM-CT-19 | CAM-RF-02, CAM-RN-11 | as passagens derivadas de um evento com resultado oficial publicado | são conferidas contra o oficial | a divergência fica dentro da tolerância aprovada | a escrever; a tolerância é a confirmar com Vitor (E-RN-02) |

## Glossário

| Termo | Definição | Unidade ou tipo | Origem |
|---|---|---|---|
| Gap | Diferença de tempo para o carro da frente. Campo `gap` do XML, que pode vir como texto quando a diferença é de voltas | s ou texto | `livetiming.py`, medido no MBR |
| Interval, ou diferença para o líder | Diferença de tempo para o primeiro colocado. Campo `difference` do XML, também pode vir como texto | s ou texto | `livetiming.py`, medido no MBR |
| Torre de tempos | Tabela ao vivo com uma linha por carro, ordenada por posição, que é o placar do evento | tela | CAM-F5, CAM-F8 |
| XML `resultspage` | Formato que o MyLaps e o Orbits publicam na rede local do evento, com os labels do evento e uma linha por carro. Carrega só as 3 últimas voltas de cada um | formato | CAM-F5 |
| Transponder | Etiqueta eletrônica no carro que o loop enterrado na pista lê a cada passagem, e que é a identidade do carro para a cronometragem | identificador | Campo `transponder` do XML |
| Outing | Trecho entre a saída e a entrada do box, com as voltas rodadas sem parar | contagem de voltas | Termo do paddock; ainda sem uso no código da PoC |
| Pit loss | Tempo perdido em uma parada, contado entre o ponto de entrada e o de saída do box comparado com o mesmo trecho em pista | s | Mock N1 (CAM-F8), com número ilustrativo |
| Drop zone | Faixa de posições em que o carro reentra na pista depois da parada | posição | Mock N1 (CAM-F8), com número ilustrativo |
| No-tow pace | Ritmo do carro sem o vácuo de outro carro à frente, usado para comparar pilotos sem o ganho emprestado da aerodinâmica | s por volta | CAM-F13, pesquisa cujos 26 links ainda não foram abertos; a validar antes de virar requisito |
