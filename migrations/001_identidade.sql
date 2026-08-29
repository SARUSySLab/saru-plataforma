-- Modulo identidade (2/6 do catalogo): usuario, piloto.
-- Fora do recorte: equipe, campeonato, membro_equipe, equipe_campeonato.

create table usuario (
    id            uuid        primary key default gen_random_uuid(),
    email         varchar     not null,
    password_hash varchar     not null,
    name          varchar,
    role          text        not null,
    created_at    timestamptz not null default now(),
    constraint uq_usuario_email unique (email),
    constraint ck_usuario_role check (role in ('owner', 'membro', 'admin'))
);

comment on table usuario is 'A conta autenticada. E a raiz da propriedade: user_id desce denormalizado pela espinha operacional para o filtro de dono ser um where direto, sem join.';
comment on column usuario.role is 'Sem CHECK no catalogo original (nota: "entra como integridade de dominio no esquema fisico"). Valores inferidos (a confirmar): owner, membro, admin.';

create table piloto (
    id         uuid      primary key default gen_random_uuid(),
    user_id    uuid      not null references usuario (id),
    name       text      not null,
    role       text,
    status     text,
    updated_at timestamp not null default now(),
    constraint uq_piloto_user_name unique (user_id, name)
);

comment on table piloto is 'Piloto com chave propria (PK uuid), nao mais o number (int) do carro. user_id substitui o CRM sem tenant: piloto e unico por dono, nao globalmente.';
comment on column piloto.name is 'Chave natural e (user_id, name): dois "Joao Silva" de contas diferentes nao colidem.';
comment on column piloto.role is 'Sem CHECK no catalogo.';
comment on column piloto.status is 'Sem CHECK no catalogo.';
comment on column piloto.updated_at is 'Sem fuso, transcrito do catalogo literalmente (nota do catalogo: "o CRM inteiro usa timestamp, a espinha usa timestamptz", risco de erro silencioso ja registrado la).';
