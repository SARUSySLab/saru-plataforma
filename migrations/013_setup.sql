-- Ficha de setup (fase 4 do plano de integracao). Nao existia: 004_operacao
-- corta setup do recorte de proposito ("Fora do recorte: campeonato,
-- inscricao, veiculo, setup, tipo_evento").
--
-- DECISAO (Lucas delegou, 29/08): valores em JSONB versionado, nao entidade
-- normalizada. Motivo: a ficha ainda esta em descoberta. O contrato de leitura
-- de hoje carrega `contexto.setup` como Record<string, string|number>, um saco
-- sem schema, porque ninguem fechou ainda quais campos a ficha tem. Normalizar
-- agora congela um formato que vai mudar; JSONB versionado da historico e nao
-- impede normalizar depois (a migracao vira um INSERT ... SELECT jsonb_each).
--
-- O que NAO e negociado pelo JSONB: dono, versao e a que bateria pertence.
-- Isso e coluna, com FK e CHECK, porque e o que sustenta o filtro de dono.

create table setup (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references usuario (id),
    bateria_id uuid references bateria (id),
    gravacao_id uuid references gravacao (id),
    versao     int  not null default 1,
    valores    jsonb not null default '{}'::jsonb,
    notas      text,
    criado_em  timestamptz not null default now(),
    constraint ck_setup_um_dono check (num_nonnulls(bateria_id, gravacao_id) = 1),
    constraint uq_setup_bateria_versao unique (bateria_id, versao),
    constraint uq_setup_gravacao_versao unique (gravacao_id, versao)
);

comment on table setup is 'Ficha de setup do carro. Mesmo desenho de dono polimorfico de contexto (num_nonnulls = 1): pendura na bateria quando a espinha operacional existe, ou direto na gravacao quando o arquivo e solto (decisao D3).';
comment on column setup.valores is 'Campos da ficha. JSONB por decisao do Lucas em 29/08: o formato da ficha ainda nao fechou, e coluna normalizada congelaria o que ainda muda. Chave e nome do campo, valor e string ou numero, que e exatamente o Record<string, string|number> que o contract.ts ja declara.';
comment on column setup.versao is 'Versao da ficha na mesma bateria. Setup muda entre baterias e as vezes dentro dela; guardar historico e o que permite ler "mudou o que entre a bateria 2 e a 3".';

create index ix_setup_user on setup (user_id);
create index ix_setup_bateria on setup (bateria_id) where bateria_id is not null;
create index ix_setup_gravacao on setup (gravacao_id) where gravacao_id is not null;
