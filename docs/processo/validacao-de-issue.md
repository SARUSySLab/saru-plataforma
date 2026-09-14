# Como uma issue é validada por Vitor

Decisão de 2026-09-14. Vale para toda issue da PoC e da plataforma. O PR que resolve a issue
só sai de rascunho quando os três itens abaixo estiverem no corpo dele.

1. Roteiro de conferência: 3 a 5 passos que Vitor executa, cada um com o comando ou a tela
   e o resultado esperado em uma linha. Sem passo que exija ler código.
2. Antes e depois: relatório ou tela gerados com uma gravação real do acervo, antes e depois
   da mudança, em HTML lado a lado, no mesmo arquivo `docs/html/<issue>.html`, atualizado a
   cada versão do PR e nunca duplicado.
3. Tabela de medição, quando a issue é de leitor ou de regra física: quantas gravações do
   acervo passaram a funcionar, com a lista por arquivo, e o que continua de fora e por quê.

Vitor aponta erro no PR. O erro vira item novo no roteiro e volta para o agente na mesma
issue; a issue só fecha quando Vitor marca o PR como aprovado.
