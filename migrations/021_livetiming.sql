-- Modulo live timing (visao de campeonato, decisoes do Lucas em 29/08):
-- usuario maquina + cronometragem externa no formato "resultspage"
-- (padrao MyLaps/Orbits), a mesma que alimenta o painel do autodromo pela
-- rede local. Um relay autenticado como usuario maquina posta os XMLs; o
-- sistema guarda snapshot bruto (auditoria/replay) e deriva historico de
-- passagem volta a volta (decisao: snapshot + historico, nunca so o ultimo).

-- 'maquina': conta nao-humana (o relay de cronometragem e o primeiro caso).
-- Autentica por token de API dedicado (tabela abaixo), nunca por cookie de
-- sessao: credencial de maquina nao expira no meio de um evento e e revogavel
-- uma a uma, sem derrubar as sessoes humanas.
alter table usuario drop constraint ck_usuario_role;
alter table usuario add constraint ck_usuario_role
    check (role in ('owner', 'membro', 'admin', 'maquina'));

create table maquina_token (
    id            uuid        primary key default gen_random_uuid(),
    user_id       uuid        not null references usuario (id),
    token_sha256  char(64)    not null,
    nome          text        not null,
    criado_por    uuid        not null references usuario (id),
    criado_em     timestamptz not null default now(),
    revogado_em   timestamptz,
    ultimo_uso_em timestamptz,
    constraint uq_maquina_token_sha unique (token_sha256)
);

comment on table maquina_token is 'Credencial de usuario maquina. So o sha256 do token fica gravado: o token em claro aparece UMA vez, na criacao, e nunca mais e recuperavel.';
comment on column maquina_token.criado_por is 'O humano (owner/admin) que emitiu. Auditoria de quem deu acesso de maquina.';
comment on column maquina_token.revogado_em is 'Revogacao e soft: a linha fica pra auditoria, o token para de autenticar.';

create table lt_evento (
    id             uuid        primary key default gen_random_uuid(),
    maquina_id     uuid        not null references usuario (id),
    nome           text        not null,
    grupo          text,
    run_nome       text        not null default '',
    run_tipo       text,
    pista_nome     text,
    track_length_m real,
    layout_id      text        references layout (id),
    criado_em      timestamptz not null default now(),
    constraint uq_lt_evento_nome_run unique (nome, run_nome)
);

comment on table lt_evento is 'Um evento de cronometragem externa (eventname + runname do XML). NAO e o evento da espinha operacional: aquele e do piloto dono da conta, este e do autodromo inteiro.';
comment on column lt_evento.layout_id is 'Resolvido por heuristica sobre trackname + tracklength, ou cravado depois. Nulo quando nao resolveu: o mapa declara que falta, nao desenha a pista errada (mesma regra do B2).';
comment on column lt_evento.pista_nome is 'trackname literal do XML, guardado mesmo com layout resolvido: e a evidencia da resolucao.';

create table lt_snapshot (
    id          uuid        primary key default gen_random_uuid(),
    evento_id   uuid        not null references lt_evento (id),
    timeofday   text,
    racetime    text,
    flag        text,
    labels      jsonb       not null,
    resultados  jsonb       not null,
    raw_sha256  char(64)    not null,
    raw_xml     text        not null,
    recebido_em timestamptz not null default now(),
    constraint uq_lt_snapshot_dedupe unique (evento_id, raw_sha256)
);

comment on table lt_snapshot is 'O XML como chegou + o parse dele. O dedupe por sha256 faz o relay poder postar sem medo: snapshot repetido (o Orbits congela entre passagens) vira no-op, nao linha nova.';
comment on column lt_snapshot.raw_xml is 'Bruto integral. E o que permite reprocessar com parser melhor sem pedir o evento de volta (mesma licao do acervo de telemetria).';

create index ix_lt_snapshot_evento_recebido on lt_snapshot (evento_id, recebido_em desc);

create table lt_competidor (
    id          uuid primary key default gen_random_uuid(),
    evento_id   uuid not null references lt_evento (id),
    numero      text not null,
    transponder text,
    nome        text not null,
    carro       text,
    classe      text,
    constraint uq_lt_competidor_numero unique (evento_id, numero)
);

comment on table lt_competidor is 'Competidor do evento externo. numero e text, nao int: cronometragem usa "199A" e afins. Sem FK pra piloto da conta: o vinculo competidor -> piloto do SARU e decisao futura, nao um join chutado por nome.';
comment on column lt_competidor.carro is 'A cronometragem do MBR embute o carro no fullname ("Piloto | Carro"); quando o separador existe, o carro fica aqui e o nome fica limpo.';

create table lt_passagem (
    id             uuid primary key default gen_random_uuid(),
    competidor_id  uuid not null references lt_competidor (id),
    volta          int  not null,
    tempo_s        real,
    velocidade_kmh real,
    timeofday      text,
    snapshot_id    uuid references lt_snapshot (id),
    criado_em      timestamptz not null default now(),
    constraint uq_lt_passagem_volta unique (competidor_id, volta),
    constraint ck_lt_passagem_volta check (volta >= 1)
);

comment on table lt_passagem is 'Historico volta a volta, derivado por diff entre snapshots. O XML so carrega as ultimas 3 voltas de cada carro; quem transforma isso em serie completa e a ingestao acumulando aqui. Snapshot perdido = ate 3 voltas ainda recuperaveis, alem disso ha buraco (e o buraco fica visivel, nao interpolado).';
comment on column lt_passagem.tempo_s is 'Nulo quando o XML trouxe a passagem sem tempo (primeira volta em treino cronometrado, por exemplo).';
