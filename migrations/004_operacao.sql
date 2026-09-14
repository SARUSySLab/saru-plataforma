-- Modulo operacao (espinha operacional, decisao 16 do plano): evento, sessao,
-- bateria. Mais contexto (decisao D2 do Lucas, 28/08), que nao existe no
-- catalogo: casa unica do contexto de sessao (pneu, temperaturas, vento,
-- horario, notas de piloto/engenheiro).
--
-- Fora do recorte: campeonato, inscricao, veiculo, setup, tipo_evento.
-- A espinha e opcional, nunca pre-requisito (decisao D3): gravacao.bateria_id
-- (em 005_telemetria.sql) e anulavel, arquivo solto ingere sem evento nenhum.

create table evento (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null references usuario (id),
    track_id   text not null references layout (id),
    name       text not null,
    starts_at  timestamptz not null,
    ends_at    timestamptz,
    local_date date,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_evento_id_user unique (id, user_id)
);

comment on table evento is 'A etapa: um dia de pista, num layout. Denormaliza user_id (ADR-0027 do catalogo) para o filtro de dono ser um where direto sem join; UNIQUE (id, user_id) sustenta a FK composta de sessao.';
comment on column evento.track_id is 'FK direta pra layout (era texto solto no schema antigo).';
comment on column evento.local_date is 'Data no fuso da pista (pista.timezone), para agrupar o dia sem depender do fuso do servidor.';

-- DECISAO PENDENTE (Lucas): o catalogo tem evento.tipo_evento_id -> tipo_evento
-- (trackday, corrida, teste...), mas tipo_evento nao esta nas 26 entidades do
-- recorte. Implementado aqui o mais conservador: coluna omitida, evento nao
-- guarda tipo estruturado nesta PoC. Opcoes se isso incomodar:
--   (1) trazer tipo_evento como entidade extra so pra sustentar a FK;
--   (2) coluna texto livre nao normalizada (ex.: evento.tipo text) sem tabela;
--   (3) manter omitido (o que esta implementado).
-- Campeonato (evento.championship_id no catalogo) fica fora sem essa mesma
-- ressalva: o plano ja lista campeonato como fora do recorte de identidade.

create table sessao (
    id           uuid primary key default gen_random_uuid(),
    user_id      uuid not null references usuario (id),
    event_id     uuid not null references evento (id),
    type         text not null,
    label        text,
    planned_laps int,
    starts_at    timestamptz,
    created_at   timestamptz not null default now(),
    updated_at   timestamptz not null default now(),
    constraint fk_sessao_evento_user foreign key (event_id, user_id) references evento (id, user_id),
    constraint uq_sessao_id_user unique (id, user_id),
    constraint uq_sessao_id_evento unique (id, event_id),
    constraint ck_sessao_type check (type in ('practice', 'qualifying', 'race', 'trackday_battery', 'test'))
);

comment on table sessao is 'Pratica, classificatoria, corrida, bateria de track day, teste. FK composta (event_id, user_id) contra evento garante que a divergencia de dono entre sessao e evento e impossivel de gravar.';

create table bateria (
    id          uuid primary key default gen_random_uuid(),
    user_id     uuid not null references usuario (id),
    session_id  uuid not null references sessao (id),
    evento_id   uuid not null,
    laps        int,
    fuel_in_l   real,
    fuel_out_l  real,
    started_at  timestamptz,
    went_out_at timestamptz,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now(),
    constraint fk_bateria_sessao_user foreign key (session_id, user_id) references sessao (id, user_id),
    constraint fk_bateria_sessao_evento foreign key (session_id, evento_id) references sessao (id, event_id),
    constraint uq_bateria_session_saida unique (session_id, went_out_at)
);

comment on table bateria is 'A ida a pista. Recorte de 28/08: inscricao_id, driver, crm_driver_number, vehicle_id, versao_setup_id e tyre_temps saem porque inscricao/veiculo/setup ficam fora desta PoC (ja saiam por 3FN no catalogo original tambem). Por decisao D2, track_temp_c, air_temp_c, weather e notes tambem saem daqui: essa informacao mora inteira em contexto.';
comment on column bateria.evento_id is 'Denormalizado da sessao (mesmo raciocinio do user_id): FK composta (session_id, evento_id) -> sessao torna impossivel a bateria apontar pra sessao de um evento e achar que esta em outro. No catalogo original tambem valida contra inscricao_id; aqui nao ha inscricao, entao so o lado da sessao existe.';
comment on column bateria.laps is 'Derivado (soma do lap_count das gravacoes vinculadas). Guardado como coluna por decisao ja tomada no catalogo original (ADR-0047); o pipeline e quem mantem coerente, nao ha trigger de recalculo nesta PoC.';
comment on constraint uq_bateria_session_saida on bateria is 'Substitui a chave natural do catalogo (session_id, inscricao_id, went_out_at): sem inscricao no recorte, a chave cai para (session_id, went_out_at). Marcada a confirmar la no catalogo original; aqui e consequencia direta do corte de inscricao, nao decisao nova.';

create table contexto (
    id                  uuid primary key default gen_random_uuid(),
    bateria_id          uuid references bateria (id),
    gravacao_id         uuid, -- FK adicionada em 005_telemetria.sql (add_fk_contexto_gravacao), gravacao ainda nao existe aqui
    pneu_estado         text,
    pneu_voltas_rodadas int,
    pneu_composto       text,
    temp_ar_c           real,
    temp_pista_c        real,
    vento_kmh           real,
    horario             timestamptz,
    notas_piloto        text,
    notas_engenheiro    text,
    criado_em           timestamptz not null default now(),
    constraint ck_contexto_um_dono check (num_nonnulls(bateria_id, gravacao_id) = 1),
    constraint ck_contexto_pneu_estado check (pneu_estado is null or pneu_estado in ('novo', 'usado'))
);

comment on table contexto is 'Decisao D2 (Lucas, 28/08): casa unica do contexto de sessao. bateria_id e gravacao_id sao ambos anulaveis com CHECK exigindo exatamente um preenchido (num_nonnulls = 1) - contexto pendura na bateria quando ela existe, ou direto na gravacao quando o arquivo e solto (decisao D3). Nao existe no catalogo original: entidade nova, pedida pelo engenheiro de pista no feedback de 28/08 (estado do pneu decide se o insight vale).';
comment on column contexto.pneu_estado is 'novo/usado, decisao D2. Tipo e enum inferidos: o plano nao especifica o dominio exato.';
comment on column contexto.vento_kmh is 'Unidade inferida (km/h). O plano pede "vento" sem especificar unidade nem se e velocidade ou so descricao textual; km/h escolhido por ser o padrao de boletim meteorologico no Brasil.';
comment on column contexto.notas_piloto is 'Nota livre do piloto. Coluna separada de notas_engenheiro por pedido explicito do engenheiro no feedback ("escreva algumas observacoes gerais do piloto e observacoes gerais do engenheiro").';
