# Casos de uso da empresa

Rascunho 2, 2026-09-12. Caso de uso é o roteiro de uma tarefa: o que acontece quando dá
certo, o que muda se a situação for outra, o que fazer quando dá errado. Só para tarefa
que tem desvio. No nível da empresa entram três: o caminho do arquivo até cada família, a
validação de física, e o compartilhamento entre famílias. Fontes em `01-problema-e-objetivos.md`.

## E-UC-01 Do arquivo ao uso por cada família

É o caminho principal da SARU e o que nunca fechou de ponta a ponta (Vitor, 2026-09-12).
Os 7 passos aprovados por Vitor em 2026-09-12.

- Requisitos: E-RF-01 a E-RF-05, E-RF-07, E-RNF-01, E-RNF-02
- Quem inicia: piloto, engenheiro, equipe ou organizador, ao enviar um arquivo
- Quem participa: o núcleo; a família que vai usar o resultado
- Antes de começar: o usuário está logado; o arquivo vem de um logger suportado
- Ao terminar: cada família tem o resultado no formato dela, e todo número tem origem

Quando dá certo:
1. O arquivo chega: upload, pasta compartilhada ou transmissão ao vivo.
2. O sistema reconhece o formato pela assinatura de bytes e segue.
3. Lê as amostras, sem inventar valor onde o logger não gravou.
4. Traduz cada canal para a língua única: um nome, uma unidade.
5. Descobre a pista e corta as voltas.
6. Analisa: setores, curvas, perdas por trecho, consistência, vitais do carro.
7. Entrega por família, cada uma na linguagem do seu público:
   - Piloto: onde perdeu tempo e o que treinar.
   - Engenheiro: comparação entre voltas e loggers, decisão de setup registrada.
   - Equipe: histórico do carro e do piloto por etapa.
   - Campeonato: comparativo do dia entre pilotos e torre de tempos.
   - Aluno: trilha de exercícios sobre a própria volta.

O que muda conforme a situação:
- 1a. Chegam vários arquivos da mesma captura (caso AiM com sidecars): viram uma gravação
  só, com papéis por arquivo.
- 1b. O arquivo já foi enviado antes (mesmo SHA-256): o sistema aponta a gravação existente e
  não cria outra.
- 2a. Formato desconhecido: recusa com motivo e abre o caminho raro do formato novo (E-UC-04).
  Pouquíssimos formatos novos vão entrar; o comum é o arquivo já ser compatível.
- 5a. O arquivo declara a pista: resolve por alias. Não declara mas tem GPS: resolve por
  posição. Nenhum dos dois: pergunta ao usuário uma vez e guarda a resposta.
- 5b. O logger já marca as voltas (canal ou beacon): usa. Não marca (log contínuo de ECU):
  corta por GPS na linha de chegada.
- 7a. A família de destino ainda não existe (hoje só Piloto tem tela): o resultado fica
  disponível pelo núcleo, com id e origem, para quando ela existir.

Quando dá errado (exceções conhecidas do acervo em 2026-09-12; cada uma vira tarefa a
fechar antes do lançamento da família que a sofre):
- 2e. Dois arquivos primários do mesmo formato no mesmo envio: falha alto, não funde voltas.
- 3e. O leitor lê só inventário e não decodifica canais (AiM `.gpk` e `.rrk`): a gravação entra
  sem amostra e o relatório diz por quê.
- 4e. Canal sem unidade provada: fica marcado como não mapeado, não vira número na tela.
- 5e. 100 gravações Pi com corte de volta dentro do arquivo que o leitor ainda não decodifica:
  hoje não cortam; tarefa aberta.
- 5f. Comprimento da pista no catálogo não bate com o percorrido (Curitiba, 67 voltas, razão
  1,164): decisão de domínio pendente, provavelmente catálogo errado ou outro layout.
- 5g. GPS do arquivo aponta outra pista (3 gravações GT7 com coordenada de Donington): corte
  por GPS e traçado recusam com o tamanho do erro.
- 5h. Canal de volta com valores que não são contagem (de 28 a 2572): guarda de densidade
  rejeita e o corte tenta o próximo método.
- 5i. Corte só por canal a 1 Hz: tempo de volta em segundos inteiros; refinar contra a série
  rápida é tarefa aberta.
- 6e. Setor sem dado: a volta é marcada como não setorizável; a volta ideal é suprimida se a
  soma dos melhores setores passar a melhor volta.
- 7e. Bloco sem dado (sem GPS, sem catálogo de curva, sem canal de combustível): o bloco
  aparece marcado com o motivo, nunca some nem mostra número inventado.

Critérios: E-CT-01 a E-CT-05 e, por família, os CT do relatório dela

## E-UC-02 Validar uma regra de física contra o acervo

Em uma frase: alguém propõe a regra com uma pergunta concreta, o agente mede no acervo e
traz uma tabela, Vitor olha a tabela e escolhe o valor, a regra ganha um id, e o código só
pode usar esse valor.

- Requisitos: E-RN-02, E-RF-08, E-RNF-03
- Quem decide: Vitor
- Quem participa: quem propõe (agente ou desenvolvedor); o acervo de dados
- Antes de começar: a regra escrita como "se condição, então consequência", a pergunta
  concreta ("10% de tolerância é bom?") e os arquivos do acervo em que ela será medida
- Ao terminar: regra aprovada com valor e id, ou recusada com motivo; registro em
  `06-validacao.md` e na matriz

Quando dá certo:
1. Quem propõe escreve a regra, a pergunta e a fonte (norma, manual, medição anterior).
2. O agente mede no acervo e traz a tabela: quantos arquivos, quantas voltas, o valor que
   separa o caso certo do errado, falsos positivos e falsos negativos. Exemplo real: a
   calibração de frenagem por G de 2026-08-22, 232 voltas com pedal, queda mediana de 11 a
   24 m/s².
3. Vitor e o agente analisam a tabela juntos; Vitor escolhe o valor.
4. A regra ganha id, versão e data de aprovação na matriz.
5. A regra vira código que cita o id, com um teste que reproduz a medição.

O que muda conforme a situação:
- 2a. O acervo não tem dado suficiente (ex.: FuelTech sem amostra): a regra fica "proposta,
  sem medição" e abre a tarefa de conseguir o dado.
- 3a. Vitor pede outra medição (outro conjunto, outro limiar): volta ao passo 2 com a nova
  pergunta registrada.
- 3b. A regra é de modelo (pneu, veículo) e não de limiar: a medição é a comparação do
  modelo com o dado real, com o erro por canal; Vitor aceita ou não a faixa de erro.

Quando dá errado:
- 1e. Regra sem fonte nem pergunta concreta: não entra em análise.
- 5e. O código usa um valor diferente do aprovado: o teste que reproduz a medição falha e o
  PR não entra.

Critérios: E-CT-09 e, por família, o CT que mede a regra

## E-UC-03 Compartilhar um resultado entre famílias

Em uma frase: a volta do piloto entra no histórico da equipe, a volta do campeonato vira
referência do piloto, e nos dois sentidos o número é o mesmo, com a mesma origem.

- Requisitos: E-RF-07, E-RF-06, E-RF-04, E-RNF-07, E-RNF-08
- Quem inicia: usuário de uma família (ex.: chefe de equipe)
- Quem participa: o dono do resultado (ex.: piloto); o núcleo
- Antes de começar: o resultado existe com id e origem; o usuário de destino tem permissão
- Ao terminar: o mesmo resultado, mesmo id, mesma origem, visível na família de destino

Quando dá certo:
1. O usuário de destino pede um resultado de outra família.
2. O núcleo confere se o dono autorizou, ou se o usuário de destino é o dono.
3. O núcleo entrega o resultado com id, versão e origem (arquivo, leitor, regras).
4. A família de destino mostra o resultado citando a origem. O inverso funciona igual.

O que muda conforme a situação (cenários propostos a partir dos documentos; a confirmar
com Vitor na modelagem):
- 1a. Resultado gerado com versão antiga do leitor ou das regras: entrega marcado "gerado
  com a versão X"; a família pode pedir reprocessamento; a cópia compartilhada nunca muda
  sozinha.
- 1b. Referência do campeonato usada por vários pilotos ao mesmo tempo: uma referência,
  muitos leitores; ninguém altera a referência.
- 1c. Gravação de referência do sistema (finalidade "referência", sem evento nem sessão):
  entra pela base de referência, não pelo evento do piloto (rodada 2 do Lucas, D3-B).
- 2a. Dono ainda não autorizou: a família de destino vê que existe e pede; não vê o conteúdo.
- 2b. Piloto sai da equipe: o histórico da equipe guarda o que foi compartilhado enquanto
  ele estava; o dado bruto continua do piloto. A confirmar com Vitor.
- 2c. Cliente pede exclusão ou exportação de tudo o que é dele: exporta completo e apaga o
  bruto; resultados já compartilhados ficam marcados "origem removida". A confirmar.

Quando dá errado:
- 2e. Usuário sem permissão: 404, sem revelar que o resultado existe.
- 3e. Resultado sem origem rastreável (dado antigo do `saru-app` ou importado): entra marcado
  "origem não rastreada" e não vira referência de comparação.

Critérios: E-CT-06, E-CT-07

## E-UC-04 Entrar um formato de logger novo no núcleo

Caminho raro, aberto pela exceção 2a do E-UC-01. Em uma frase: sem arquivo real não se
escreve leitor; com arquivo real, mede, cataloga a assinatura, escreve o leitor com teste,
mapeia os canais e passa o acervo inteiro do formato.

- Requisitos: E-RF-01, E-RF-02, E-RNF-09, E-RN-04
- Quem faz: desenvolvedor; Vitor aprova unidade de canal quando há dúvida
- Antes de começar: pelo menos um arquivo real, bruto, com taxa, pista e tipo de sessão
  conhecidos (pedido do plano de 2026-08-28)
- Ao terminar: assinatura no catálogo, leitor com teste e fixture, documento de medição em
  `docs/`, canais no mapa canônico

Quando dá certo:
1. Medir o arquivo (assinatura, cabeçalho, taxa, canais, unidades, codificação) e registrar
   em `docs/<formato>-medicao.md`.
2. Catalogar a assinatura.
3. Escrever o leitor contra o arquivo real e uma fixture pequena versionada.
4. Mapear cada canal com unidade; canal sem unidade provada fica não mapeado.
5. Passar o acervo inteiro do formato; recusas saem com motivo.

O que muda conforme a situação:
- 1a. Só há inventário e a semântica dos canais não foi confirmada: entra como "só
  inventário" e não é anunciado como suportado.
- 3a. O arquivo real é de cliente: a fixture é recortada e anonimizada; o original não entra
  no repositório.

Quando dá errado:
- Sem arquivo real (FuelTech e ProTune em 2026-09-12): não passa do DoR, item 8.
- 5e. Leitor lê mas com unidade errada (caso `lon_acc` em g contra m/s²): o teste de contrato
  de canal falha e o PR não entra.

Critérios: E-CT-01, E-CT-02
