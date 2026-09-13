# Guia de leitura dos requisitos

Para Vitor revisar os seis arquivos sem precisar do livro ao lado. Cada termo com uma
definição de uma linha e um exemplo real da SARU. Base: livro de Marsicano (UnB, 2026) e o
guia da disciplina, capítulos 5 a 9.

## Os seis arquivos, em ordem

| Arquivo | Pergunta que responde | Quem lê |
|---|---|---|
| 01 problema e objetivos | Por que a SARU existe e o que quer alcançar | qualquer pessoa |
| 02 catálogos | O que o sistema faz, como se comporta e que regras obedece | quem constrói |
| 03 backlog | Em que ordem fazer e quando algo pode começar ou está pronto | quem planeja |
| 04 casos de uso | Como é o passo a passo quando algo pode dar errado no meio | quem constrói e quem testa |
| 05 rastreabilidade | Quem depende de quem: objetivo, requisito, regra, código, teste | quem muda algo |
| 06 validação | Quem já viu isso, o que disse e o que mudou | todo mundo |

## Termos que aparecem nas tabelas

| Termo | Em uma linha | Exemplo na SARU |
|---|---|---|
| Problema (PRB) | Uma dor real de alguém, com prova | O piloto amador não sabe por que perde tempo |
| Objetivo (OBJ) | O resultado que queremos, com um número para saber se chegamos | Cinco famílias com requisitos aprovados antes de codar |
| Stakeholder | Quem sofre o problema, paga pela solução ou decide | Vitor, Lucas, Giuliano, o piloto de track day |
| Fonte (F) | De onde veio a afirmação; sem fonte, não entra | Plano da PoC de 28/08, feedback do Giuliano de 20/08 |
| Requisito funcional (RF) | O que o sistema faz, do ponto de vista de quem usa, sem dizer como | Ler o arquivo de qualquer logger suportado |
| Requisito não funcional (RNF) | Como o sistema se comporta, com número e condição de medição | Nada falha em silêncio; zero default silencioso em teste |
| Regra de negócio (RN) | "Se isso, então aquilo", vale mesmo trocando a tecnologia | Se uma regra é de física, só entra com aprovação de Vitor |
| Critério de aceitação (CT) | Como provar que o requisito foi atendido: Dado, Quando, Então | Dado um arquivo desconhecido, quando enviado, então recusa com motivo |
| História de usuário | O requisito contado como pedido: como alguém, quero algo, para um valor | Como piloto, quero saber onde perdi tempo, para treinar certo |
| Épico | Um pacote grande de histórias com um objetivo comum | Família Piloto |
| Família | Linha de produto de um nicho, com requisitos, oferta e preço próprios | Piloto, Campeonato, Engenheiro, Equipe, Aluno |
| Núcleo | O que duas ou mais famílias usam; tem dono único | Ler loggers, falar uma língua só, resolver pista |
| Nível (negócio, usuário, produto) | O quão perto do código o requisito está: por quê, o quê, como se comporta | Negócio: "reaproveitar o que existe"; produto: "corte de volta com erro de até 0,05 s" |
| MoSCoW | Prioridade em quatro caixas: must (obrigatório), should (importante), could (se der), won't (não agora) | Compartilhar entre famílias virou must em 12/09 |
| MVP | O mínimo que precisa funcionar para o produto valer a pena | O piloto sobe o cartão e recebe onde perdeu tempo |
| Definition of Ready (DoR) | A lista de coisas que uma tarefa precisa ter antes de alguém começar | Tem id, fonte, critério, estimativa, e a regra de física aprovada |
| Definition of Done (DoD) | A lista de coisas que precisam estar feitas para a tarefa contar como pronta | Teste verde, matriz atualizada, revisão de outra pessoa |
| Rastreabilidade | Saber, para cada requisito, de qual objetivo veio e qual código e teste o cumprem | OBJ-02, E-RF-01, `readers/`, E-CT-01 |
| Versão de requisito | Sobe quando o verbo ou o objeto muda; refinar condição não muda versão | "Cortar voltas" v1; se virar "cortar e validar voltas", v2 |
| Status | Onde o requisito está: proposto, aprovado, em andamento, implementado, validado | E-RF-04 está parcial |
| Caso de uso | O passo a passo com os desvios e os erros possíveis | Importar bundle: e se dois arquivos forem do mesmo formato? |
| Validação | Mostrar para quem usa e registrar o que disse | Giuliano em campo, 20/08 |
| Local-first | Funciona no computador do box sem internet e sincroniza depois | Pit wall no autódromo |
| Claim | Afirmação pública sobre o que o produto faz ou com que precisão | "solver validado contra referência" pode; "gêmeo digital" não pode |
| Fixture | Arquivo real, pequeno e versionado, usado para testar um leitor ou uma regra | Os quatro arquivos AiM do kart do Guará |

## Como revisar um arquivo em 5 minutos

1. Leia só a primeira coluna de cada tabela: os nomes contam a história.
2. Para cada linha, pergunte: isso é verdade hoje? A fonte existe? O número está certo?
3. Marque o que é confuso com "não entendi" e o que está errado com "errado porque".
4. Não tente completar o que falta; diga "falta X" e eu escrevo com fonte.
