-- Um container pode carregar mais de um vocabulario, entao `formato -> perfil`
-- deixou de ser 1 pra 1. Medido em 29/08: o `.ld` do acervo carrega tres
-- (acc em 34 arquivos, motec_ld em 5, gt7_ld em 3), e o perfil passa a ser
-- resolvido em runtime por sobreposicao de nome de canal.
--
-- Resolucao por heuristica precisa dizer COMO resolveu, senao vira o mesmo
-- default silencioso do B2. `erro` nao serve: ela e pra falha, e nao resolver
-- o perfil nao e falha, e um resultado.
alter table ingestao add column perfil_motivo text;

comment on column ingestao.perfil_motivo is
    'Como o perfil foi decidido: perfil unico do formato, sobreposicao de '
    'vocabulario com os numeros, ou o motivo de nao ter resolvido. Nulo so em '
    'linha anterior a 29/08.';
