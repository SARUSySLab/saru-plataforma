-- Controle das proprias migrations. Append-only: aplicar de novo nao reescreve,
-- o runner pula o que ja tem linha aqui.
create table if not exists _migrations (
    versao      text        primary key,
    sha256      char(64)    not null,
    aplicada_em timestamptz not null default now()
);

-- gen_random_uuid() sem extensao: nativo desde o Postgres 13.
