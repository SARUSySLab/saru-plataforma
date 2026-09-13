# Catálogos da empresa

Rascunho 1, 2026-09-12. Só o que vale para todas as famílias. Requisito de uma família fica
no `02-catalogos.md` dela. Convenção de id, para não colidir entre famílias: prefixo `E`
para empresa e um prefixo por família (`PIL`, `ENG`, `EQP`, `CAM`, `ALU`), assim: `E-RF-01`,
`PIL-RF-01`. Issue no GitHub leva o mesmo prefixo no título (`[PIL] corte de volta por GPS`) e
no rótulo. Fontes F1 a F10 em `01-problema-e-objetivos.md`. Revisado por Vitor em 2026-09-12.

## Requisitos funcionais do núcleo (E-RF)

Capacidades que toda família usa. Nível de negócio: dizem o quê, não como.

| Id | Nome | Declaração | Origem | Prioridade | Critérios | Status |
|---|---|---|---|---|---|---|
| E-RF-01 | Ler dado de qualquer logger ou simulador suportado | O núcleo deve ler o arquivo de qualquer logger real ou simulador da lista de formatos suportados (iRacing, ACC, Assetto Corsa, GT7 entre os simuladores) e recusar, com motivo, o que não reconhece | F6; PRB-03; F1 Vitor 2026-09-13 | must | E-CT-01 | parcial: 12 leitores de logger real, 6 leem amostra completa; simuladores só via MoTeC .ld (ACC, GT7); os leitores de CSV de GT7, ACC, AMS2 e iRacing do `saru-app` não foram portados |
| E-RF-02 | Falar uma língua só | O núcleo deve traduzir todo canal para um nome e uma unidade únicos, para que dado de loggers diferentes seja comparável | F6; ADR-0049 do `saru-app` | must | E-CT-02 | parcial: só a camada bruta; canal sem mapa ainda passa com nome solto |
| E-RF-03 | Saber onde e quando | O núcleo deve resolver a pista e cortar as voltas de qualquer gravação suportada. Não conseguir é exceção a fechar antes de lançar, não resultado aceito (Vitor, 2026-09-12); enquanto existir, é declarada, nunca silenciosa | F7 etapas 4 e 5; E-RN-08 | must | E-CT-03, E-CT-11 | parcial: 100 gravações Pi sem corte, 67 voltas de Curitiba recusadas |
| E-RF-04 | Rastrear cada número | Para cada número que aparece na tela (tempo de volta, perda numa curva, nota), o núcleo deve guardar de onde ele veio: qual arquivo, qual versão do leitor, quais regras. Assim qualquer número pode ser refeito e conferido | F7 etapa 2; OBJ-03 | must | E-CT-04 | parcial: ingestão guarda versão; a tela ainda não mostra a origem |
| E-RF-05 | Traduzir para o nicho | O núcleo deve entregar cada resultado técnico com uma versão em linguagem do público da família (piloto, chefe, organizador) | F1; OBJ-04 | must | E-CT-05 | parcial: muito já existe no `saru-app` e precisa ser portado |
| E-RF-06 | Separar quem vê o quê | O núcleo deve autenticar pessoas e máquinas e mostrar a cada dono só o que é dele, inclusive entre famílias | F7 regra de escopo | must | E-CT-06 | parcial: escopo por dono existe, mas não está completo nem provado ponta a ponta |
| E-RF-07 | Compartilhar entre famílias | O núcleo deve permitir que um resultado de uma família seja consumido por outra (o relatório do piloto entra no histórico da equipe; a volta do campeonato vira referência do piloto) | F1 "acoplamentos", 2026-09-12 | must | E-CT-07 | proposto: necessário desde o início |
| E-RF-09 | Estimar o carro a partir do dado | A partir do arquivo de telemetria e do que se sabe do carro, o núcleo deve estimar os parâmetros do veículo (engenharia reversa: massa, pneu, aero, freio, motor) e rodar uma simulação parecida com a volta real, com um modelo de piloto, para encontrar os comandos e os comportamentos possíveis do carro. Requisito nunca escrito antes; existe em pedaços nos arquivados (QSS e LTS do `saru-physics-py`, 14 graus de liberdade do `saru-physics-jl`, calibração do 992 GT3 R em Interlagos, Pacejka na KB) | F1 Vitor 2026-09-13; inventário 03 (53 documentos de física) | must | E-CT-10 | parcial: modelos canônicos do 911 GT3 Cup (991.1, 991.2, 992.1) implementados em `saru-poc-trackday`, `src/saru_poc/fisica/parametros_gt3_cup.py`, com teste automatizado e auditoria de proveniência em `docs/fisica-parametros-gt3-cup.md` no mesmo repositório |
| E-RF-08 | Guardar conhecimento de engenharia | O núcleo deve manter catálogo de pista, veículo, pneu e modelo físico com versão e fonte, usado por todas as famílias | F2; ADR mestre do `saru-KB`; Vitor 2026-09-12 | must | E-CT-08 | parcial: pista e canal existem; veículo, pneu e modelo físico não |

## Requisitos não funcionais da empresa (E-RNF)

Valem para toda família, sem exceção.

| Id | Categoria | Declaração | Métrica e meta | Origem | Status |
|---|---|---|---|---|---|
| E-RNF-01 | Confiabilidade | Nenhuma etapa falha em silêncio nem escolhe default sem declarar; bloco sem dado diz o motivo | Zero default silencioso em teste; 100% das falhas com motivo | F7 bugs B1 e B2 | parcial |
| E-RNF-02 | Confiabilidade | Mesmo dado e mesma versão produzem o mesmo resultado; reprocessar nunca sobrescreve | Reingestão gera nova linha e resultado igual | F7 etapa 2 | parcial |
| E-RNF-03 | Honestidade | Todo resultado carrega o nível de validação (rascunho, suportado, validado) e a tela ou pitch só afirma o que esse nível permite | 100% dos claims públicos com status; revisão de Vitor antes de publicar | F2 decisão 2 de 2026-07-15 | processo existe, sem checagem automática |
| E-RNF-04 | Unidades | Dado interno em SI; exibição na unidade do paddock (km/h, g, grau, psi) | Fator de conversão único na borda; nenhum fator solto | ADR-0042 do `saru-app` | parcial: só velocidade |
| E-RNF-05 | Disponibilidade | A família que atua no autódromo funciona sem internet, com o dado no box, e sincroniza depois | Modo local-first especificado por família; meta de latência a definir | F5; OBJ-05 | proposto: vale para todas as famílias em princípio, confirmado família a família |
| E-RNF-06 | Usabilidade | Um leigo entende a tela principal em 5 segundos; nenhuma abreviação interna aparece sem expandir | Revisão de rótulos por família; teste com um usuário real do nicho | F4 itens B3 e F2; F7 N0 | parcial |
| E-RNF-07 | Segurança | Segredo nunca em repositório nem no Drive; dado de cliente isolado por dono e por família | gitleaks no CI; acesso cruzado devolve 404 | F8 D15; PoC | parcial (gitleaks a instalar) |
| E-RNF-08 | Portabilidade do dado | Dado bruto é imutável e o cliente consegue exportar tudo o que é dele | Exportação completa por dono | F7 etapa 1 | proposto |
| E-RNF-09 | Testabilidade | Leitor de formato ou regra física só entra com arquivo real, teste e documento de medição | 100% dos leitores com fixture e teste | F8 04 §3 | 12 de 12 com teste; 3 com medição |
| E-RNF-10 | Idioma | Código, dado, commit e documento em português; tradução para inglês só na camada de venda internacional | Revisão de PR | F1 decisão de 2026-09-12 | parcial: PoC sim, arquivados não |

## Regras de negócio da empresa (E-RN)

"Se condição, então consequência", independentes de tecnologia.

| Id | Regra | Fonte | Versão |
|---|---|---|---|
| E-RN-01 | Se uma afirmação sobre física, precisão ou cliente não tem código, fixture e validação que a sustentem, então ela não entra em pitch, landing, tela ou proposta | F2 decisão 2, 2026-07-15 | 1 |
| E-RN-02 | Se uma regra envolve física, calibração ou validação (modelo de pneu, de veículo, engenharia reversa de formato, análise de performance ou de vitais), então ela é validada junto com Vitor contra o acervo de dados antes de entrar, e só entra com a aprovação dele registrada, com a pergunta concreta e o valor medido. É um passo do backend a deixar refinado e funcional: a regra aprovada vira código com o id dela e teste | Regra do operador; F8; Vitor 2026-09-12 | 1 |
| E-RN-03 | Se um requisito não tem fonte (pessoa, documento, dado, observação), então não entra em catálogo nenhum | Skill `requisitos` | 1 |
| E-RN-04 | Se um dado bruto é de cliente, então nunca é alterado, nunca é copiado para repositório de código e sai do sistema só por exportação do dono | F7 etapa 1; README de `dados_telemetria` | 1 |
| E-RN-05 | Se um recurso é usado por duas ou mais famílias, então vive no núcleo com um dono; se é de uma só, vive na família | F1, 2026-09-12 | 1 |
| E-RN-06 | Se uma decisão muda produto, arquitetura ou processo, então é registrada em `docs/decisions.md` antes de virar código; ADR só para decisão de arquitetura que muda estrutura, poucos e curtos. Antes de codar qualquer família: uma semana de documentação e modelagem, e o modelo (dado, fluxo ou tela) da funcionalidade existe em `docs/modelos/` antes do código | F8 01 §3; Vitor 2026-09-12 | 1 |
| E-RN-08 | Se a gravação vem de simulador, então a pista é resolvida pelo que o jogo declara (nome do circuito e layout), nunca por GPS: a coordenada exportada por simulador é placeholder (caso GT7, que declara Interlagos com coordenadas de Donington, medido em 2026-08-13 no `saru-app`) | F1 Vitor 2026-09-13; ADR-0048 do `saru-app`; auditoria 04 dívidas | 1 |
| E-RN-07 | Se o time cresce, então quem entra lê, nesta ordem: perfil da organização, como contribuir, README do repositório, contrato do agente, decisões. Ordem ainda a confirmar; a necessidade de rastreabilidade para quem chega está confirmada | F8 06 §8; Vitor 2026-09-12 | 1 |

## Critérios da empresa (E-CT)

Verificados em toda família. Os de família ficam no catálogo dela.

| Id | Requisito | Dado | Quando | Então | Como verificar |
|---|---|---|---|---|---|
| E-CT-01 | E-RF-01 | um arquivo que nenhum leitor reconhece | é enviado | recusa com motivo, sem adivinhar | teste da família que ingere |
| E-CT-02 | E-RF-02 | qualquer arquivo de qualquer logger suportado | é normalizado | todo canal sai com nome e unidade canônicos, ou marcado como não mapeado; nunca nome bruto solto | teste de contrato de canal sobre o acervo inteiro |
| E-CT-03 | E-RF-03, E-RNF-01, E-RN-08 | uma gravação sem venue e sem GPS coerente, ou gravação de simulador com GPS sintético | é processada | em logger real recusa com pista não resolvida; em simulador preserva o circuito declarado pelo jogo e ignora GPS | teste da cascata de pista |
| E-CT-11 | E-RF-01, E-RF-03, E-RN-08 | um arquivo de simulador suportado (MoTeC .ld de ACC/GT7 ou exportação iRacing) | é enviado | ingere as amostras completas e resolve a pista pelo circuito declarado pelo jogo ignorando GPS placeholder | teste com fixture de simulador |
| E-CT-04 | E-RF-04, E-RNF-02 | um número mostrado ao usuário (ex.: melhor volta 1:34,586) | o arquivo bruto é reprocessado com a mesma versão do leitor e das regras | o mesmo número, e a tela mostra de qual arquivo e versão ele veio | teste de reingestão |
| E-CT-05 | E-RF-05, E-RNF-06 | a tela principal de uma família e uma pessoa do nicho recrutada antes | na validação de cada versão da tela, em sessão marcada | ela diz em uma frase o que viu, sem ajuda | demonstração registrada em `06-validacao.md` |
| E-CT-06 | E-RF-06, E-RNF-07 | recurso do dono A | o dono B acessa | 404 | teste |
| E-CT-07 | E-RF-07 | um resultado de uma família | outra família consulta, e o inverso | o mesmo id e a mesma origem aparecem dos dois lados | a escrever |
| E-CT-08 | E-RF-08 | uma pista, veículo ou pneu do catálogo | é consultado | tem versão e fonte | a escrever |
| E-CT-10 | E-RF-09, E-RN-02 | uma volta real de um carro com parâmetros conhecidos do acervo (ex.: 992 GT3 R em Interlagos) | o núcleo estima os parâmetros a partir do dado e simula a volta com o modelo de piloto | o tempo de volta e os canais simulados ficam dentro de uma faixa de erro que Vitor aprova contra o dado real (E-UC-02) | teste de regressão contra a fixture; faixa a definir |
| E-CT-09 | E-RNF-03, E-RN-01 | um texto público com afirmação técnica | é revisado antes de publicar | cada afirmação tem status suportado ou validado | revisão de Vitor; checagem automática a definir |

## Glossário

| Termo | Definição |
|---|---|
| Família | Linha de produto de um nicho, com requisitos, oferta e preço próprios |
| Núcleo | Conjunto de capacidades compartilhadas por duas ou mais famílias, com dono único |
| Nicho | Grupo de clientes com a mesma dor: piloto, engenheiro, equipe, campeonato, aluno |
| Persona | Retrato de um comprador típico do nicho (P1 a P4 na pesquisa de julho) |
| Local-first | Funciona no computador do box sem internet e sincroniza quando ela volta |
| Claim | Afirmação pública sobre o que o produto faz ou com que precisão |
| Fixture | Arquivo real, pequeno e versionado, usado para testar um leitor ou uma regra |
| Default silencioso | Escolha que o sistema faz sem avisar; proibida em toda família |
