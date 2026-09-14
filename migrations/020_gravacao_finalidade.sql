-- D3 (decisao do Lucas, 29/08, opcao B): dois acervos no MODELO, nao na
-- disciplina de quem escreve query. A gravacao declara a finalidade dela:
--   - 'piloto': trabalho do dono, alimenta agregados e o funil normal;
--   - 'referencia': arquivo importado so pra comparar (ex.: de outro
--     piloto), fora dos agregados e do caminho default da analise.
-- Junto com 018/019 fecha a rodada 2. A regra de escopo (29/08) ja cortou o
-- acervo sem dono das rotas; esta coluna e o lugar do arquivo alheio DENTRO
-- da conta, marcado, em vez de solto no sistema.

alter table gravacao add column finalidade text not null default 'piloto'
    check (finalidade in ('piloto', 'referencia'));
comment on column gravacao.finalidade is 'piloto = alimenta analise e agregados; referencia = so aparece no lado B da comparacao.';
