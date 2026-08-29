-- D2 (decisao do Lucas, 29/08, opcao B): tipo de evento como COLUNA de texto
-- com conjunto fechado, e os modelos de sessao como DADO SEMEADO, nao como
-- entidade nova. Resolve a "DECISAO PENDENTE" registrada em 004_operacao.sql
-- pela saida (2) turbinada: a coluna e restrita e os modelos moram numa
-- tabela propria, entao viram entidade depois sem perder dado.

alter table evento add column tipo text
    check (tipo in ('track_day', 'corrida', 'teste'));
comment on column evento.tipo is 'Formato do evento. Decide que sessoes vem pre-montadas na criacao (modelo_sessao). NULL em evento anterior a esta migration.';

create table modelo_sessao (
    tipo_evento text not null,
    ordem       int  not null,
    type        text not null,
    label       text not null,
    primary key (tipo_evento, ordem),
    constraint ck_modelo_tipo check (type in ('practice', 'qualifying', 'race', 'trackday_battery', 'test'))
);
comment on table modelo_sessao is 'Sessoes que nascem junto com o evento, por tipo (resposta 1.3 do Vitor: "a run sheet importa esse dado"). Dado semeado, editavel por SQL sem migration de schema.';

insert into modelo_sessao (tipo_evento, ordem, type, label) values
    ('track_day', 1, 'trackday_battery', 'Manhã'),
    ('track_day', 2, 'trackday_battery', 'Tarde'),
    ('corrida',   1, 'practice',         'Treino Livre'),
    ('corrida',   2, 'qualifying',       'Classificação'),
    ('corrida',   3, 'race',             'Corrida'),
    ('teste',     1, 'test',             'Teste');
