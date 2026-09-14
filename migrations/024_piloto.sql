-- Piloto como degrau da espinha: evento > PILOTO > sessao > saida > telemetria.
--
-- A tabela `piloto` JA EXISTE desde a 001, com `name`, `role` e `status`, e a
-- `gravacao` ja tem `piloto_id`. Ela so nunca foi usada: estava com zero linha
-- quando o acervo do Nelson Piquet chegou. Esta migration nao cria nada do
-- zero, ela ADAPTA o que ja estava previsto.
--
-- Decisao do Lucas em 30/08: a navegacao ganha o degrau do piloto porque um
-- dia de pista no Nelson Piquet tem ate 8 pilotos diferentes (27/06 teve 8),
-- cada um com suas saidas. Sem esse degrau, "como foi o dia do Andre" nao tem
-- onde ser perguntado. Tudo numa conta so: piloto e identidade dentro do
-- acervo do dono, nao usuario com login.

-- Grafias vistas no acervo que apontam para esta pessoa. O acervo trouxe 24
-- grafias para 13 pessoas: acento perdido no encoding do logger ("AndrÃ©
-- Gomide"), apelido ("Edu" e "Eduardo Senra"), inicial trocada ("Vitor" e
-- "Victor Lira") e numero do carro colado no nome ("Miguel Pantazis 296").
-- Guardar o de-para permite reimportar sem refazer a curadoria, e auditar
-- depois de que grafia veio cada gravacao.
alter table piloto add column if not exists apelidos text[] not null default '{}';
alter table piloto add column if not exists notas text;

-- Par (id, user_id) unico: e ele que permite a chave estrangeira composta
-- abaixo garantir que sessao de um dono nunca aponte para piloto de outro. E
-- a mesma defesa que a 004 ja faz para evento e sessao.
do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'uq_piloto_id_user') then
    alter table piloto add constraint uq_piloto_id_user unique (id, user_id);
  end if;
end $$;

-- NULO permitido de proposito: o acervo antigo nao declara piloto, e exigir
-- agora quebraria o que ja esta no ar. Mesma regra da bateria opcional.
alter table sessao add column if not exists piloto_id uuid;

do $$
begin
  if not exists (select 1 from pg_constraint where conname = 'fk_sessao_piloto_user') then
    alter table sessao add constraint fk_sessao_piloto_user
      foreign key (piloto_id, user_id) references piloto (id, user_id);
  end if;
end $$;

create index if not exists sessao_piloto_idx on sessao (piloto_id);
