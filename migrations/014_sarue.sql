-- Sarue, o assistente de IA do sistema (fase 9 e 12 do plano de integracao).
-- Nome definido pelo Lucas em 29/08 pra nao colidir com SARU, que e o sistema.
--
-- Duas coisas moram aqui, e sao diferentes:
--
--   `sarue_aviso`  o que o assistente EMITIU sozinho, no ciclo de 30 min. E
--                  produto de um job do servidor, nao de uma pergunta.
--   `sarue_turno`  a conversa: o que o usuario perguntou e o que voltou.
--
-- Separadas porque tem ciclo de vida diferente: aviso e gerado sem ninguem
-- pedir e precisa saber se ja foi visto; turno so existe se alguem perguntou.
-- Uma tabela so com `origem: 'aviso' | 'pergunta'` misturaria as duas e
-- obrigaria metade das colunas a ser anulavel.

create table sarue_aviso (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references usuario (id),
    bateria_id  uuid references bateria (id),
    gravacao_id uuid references gravacao (id),
    texto       text not null,
    -- o que o modelo leu pra dizer isso. Sem isto o aviso e inauditavel, e
    -- aviso inauditavel e a mesma doenca do numero sintetico: some a regua.
    base        jsonb not null default '{}'::jsonb,
    modelo      text not null,
    visto_em    timestamptz,
    criado_em   timestamptz not null default now(),
    constraint ck_sarue_aviso_um_dono check (num_nonnulls(bateria_id, gravacao_id) = 1)
);

comment on table sarue_aviso is 'Aviso emitido pelo Sarue no ciclo periodico. O timer mora no servidor (fase 9 do plano): o front so consulta, nunca dispara geracao.';
comment on column sarue_aviso.base is 'Os fatos que entraram no prompt (contexto atual, contexto anterior, recorte da telemetria). Guardado pra o aviso ser auditavel depois, nao pra reprocessar.';
comment on column sarue_aviso.visto_em is 'Nulo enquanto o usuario nao viu. E o que distingue aviso novo de historico, sem o front guardar isso no browser.';

create table sarue_turno (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references usuario (id),
    gravacao_id uuid references gravacao (id),
    pergunta    text not null,
    resposta    text,
    base        jsonb not null default '{}'::jsonb,
    modelo      text,
    erro        text,
    criado_em   timestamptz not null default now()
);

comment on table sarue_turno is 'Um turno de conversa com o Sarue. `resposta` e `modelo` nulos com `erro` preenchido significa que a chamada falhou: o turno fica gravado assim de proposito, porque falha apagada vira "o Sarue nunca respondeu isso" na proxima leitura.';

create index ix_sarue_aviso_user on sarue_aviso (user_id, criado_em desc);
create index ix_sarue_turno_user on sarue_turno (user_id, criado_em desc);
