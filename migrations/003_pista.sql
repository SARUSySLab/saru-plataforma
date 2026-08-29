-- Modulo pista (8/10 do catalogo + fase, decisao D1 do Lucas):
-- pista, layout, alias_layout, segmento, setor, curva, fase.
-- tracado e subtracado (tambem modulo pista no catalogo) moram em
-- 005_telemetria.sql: dependem de volta, que depende de layout, e a ordem dos
-- arquivos tem que respeitar dependencia de FK antes de agrupamento tematico.
-- Fora do recorte: reta, reta_setor (v1). O valor 'reta' continua permitido no
-- CHECK de segmento.tipo porque o catalogo especifica o enum completo, mas sem
-- tabela reta nenhum segmento tipo='reta' passa no trigger de subtipo obrigatorio
-- (006_invariantes.sql) - e o comportamento correto para uma entidade fora de escopo.

create table pista (
    id       uuid primary key default gen_random_uuid(),
    nome     text not null,
    pais     text,
    cidade   text,
    timezone text not null,
    constraint uq_pista_nome unique (nome)
);

comment on table pista is 'O lugar fisico. Interlagos e uma pista; o GP e o circuito curto sao layouts dela.';
comment on column pista.timezone is 'IANA, ex.: America/Sao_Paulo. E o fuso que evento.local_date pressupoe.';

create table layout (
    id             text primary key,
    pista_id       uuid not null references pista (id),
    nome           text not null,
    comprimento_m  real not null,
    sentido        text,
    ref_lat        real,
    ref_lon        real,
    constraint uq_layout_pista_nome unique (pista_id, nome),
    constraint uq_layout_id_pista unique (id, pista_id),
    constraint ck_layout_sentido check (sentido is null or sentido in ('horario', 'anti_horario'))
);

comment on table layout is 'Era Tracado no catalogo antigo; renomeado porque "tracado" agora significa a linha que o carro fez. E o layout que todo o resto cita, nunca a pista direto: dele vem comprimento, coordenada de referencia e segmentacao.';
comment on column layout.id is 'track_id snake_case: interlagos_gp.';
comment on column layout.ref_lat is 'Medida de arquivo real do acervo, nunca de memoria (regra dura do catalogo: coordenada errada casa a pista errada em silencio).';

create table alias_layout (
    alias     text not null,
    layout_id text not null references layout (id),
    fonte     text not null,
    primary key (alias, fonte)
);

comment on table alias_layout is 'Apelido pelo qual uma fonte chama o layout. Chave e (alias, fonte), nao (layout, alias): dentro de uma fonte a ambiguidade e zero, entre fontes cada uma tem seu de-para proprio.';

create table segmento (
    id          uuid primary key default gen_random_uuid(),
    layout_id   text not null references layout (id),
    tipo        text not null,
    ordem       int  not null,
    s_inicio_m  real not null,
    s_fim_m     real not null,
    constraint uq_segmento_layout_tipo_ordem unique (layout_id, tipo, ordem),
    constraint uq_segmento_id_layout unique (id, layout_id),
    constraint uq_segmento_id_tipo unique (id, tipo),
    constraint ck_segmento_tipo check (tipo in ('setor', 'curva', 'reta', 'fase')),
    constraint ck_segmento_ordem_s check (s_fim_m > s_inicio_m)
);

comment on table segmento is 'Supertipo de setor, curva, reta (fora do recorte) e fase (decisao D1, 28/08): qualquer pedaco do layout medido em distancia percorrida. s_fim_m contra layout.comprimento_m e checado por trigger em 006_invariantes.sql, porque CHECK nao atravessa tabela.';
comment on column segmento.tipo is 'Trava de subtipo: UNIQUE (id, tipo) aqui + coluna tipo constante por CHECK em cada subtipo + FK composta (segmento_id, tipo) -> segmento. Impede segmento tipo=setor ganhar linha em curva, ou ficar sem subtipo (trigger em 006).';

create table setor (
    segmento_id uuid primary key references segmento (id),
    tipo        text not null default 'setor',
    layout_id   text not null,
    rotulo      text,
    constraint ck_setor_tipo check (tipo = 'setor'),
    constraint fk_setor_segmento_tipo foreign key (segmento_id, tipo) references segmento (id, tipo),
    constraint fk_setor_segmento_layout foreign key (segmento_id, layout_id) references segmento (id, layout_id),
    constraint uq_setor_segmento_layout unique (segmento_id, layout_id)
);

comment on table setor is 'Subtipo de segmento. Nasceu da 1FN: era a lista sector_distances dentro do YAML.';

create table curva (
    segmento_id uuid primary key references segmento (id),
    tipo        text not null default 'curva',
    setor_id    uuid not null references setor (segmento_id),
    layout_id   text not null,
    corner_id   text not null,
    label       text,
    s_apex_m    real,
    raio_min_m  real,
    constraint ck_curva_tipo check (tipo = 'curva'),
    constraint fk_curva_segmento_tipo foreign key (segmento_id, tipo) references segmento (id, tipo),
    constraint fk_curva_segmento_layout foreign key (segmento_id, layout_id) references segmento (id, layout_id),
    constraint fk_curva_setor_layout foreign key (setor_id, layout_id) references setor (segmento_id, layout_id),
    constraint uq_curva_layout_corner unique (layout_id, corner_id),
    constraint uq_curva_segmento_layout unique (segmento_id, layout_id)
);

comment on table curva is 'Pertence a exatamente um setor, por decisao de dominio: curva nao se divide entre setores. A contencao (curva dentro dos limites do setor) e checada por trigger em 006_invariantes.sql (decisao do Lucas 28/08, achou 13 de 148 curvas do tracks.yaml cruzando fronteira de setor).';
comment on column curva.s_apex_m is 'Distancia do apex. O unico dos tres pontos que e da curva e nao do segmento (inicio/fim vem de segmento.s_inicio_m/s_fim_m).';

create table fase (
    segmento_id uuid primary key references segmento (id),
    tipo        text not null default 'fase',
    layout_id   text not null,
    curva_id    uuid not null references curva (segmento_id),
    ordem       smallint not null,
    constraint ck_fase_tipo check (tipo = 'fase'),
    constraint ck_fase_ordem check (ordem between 1 and 3),
    constraint fk_fase_segmento_tipo foreign key (segmento_id, tipo) references segmento (id, tipo),
    constraint fk_fase_segmento_layout foreign key (segmento_id, layout_id) references segmento (id, layout_id),
    constraint fk_fase_curva_layout foreign key (curva_id, layout_id) references curva (segmento_id, layout_id),
    constraint uq_fase_curva_ordem unique (curva_id, ordem)
);

comment on table fase is 'Decisao D1 (Lucas, 28/08): quarto tipo de segmento, ao lado de setor, curva e reta. Subdivide uma curva em entrada, meio e saida (ordem 1..3). E o que da tempo por fase (tempo_trecho.segmento_id aponta pra fase) sem precisar de uma segunda tabela de tempo. Origem: feedback do engenheiro de pista sobre o S do Senna, "piorou na primeira perna mas melhorou na segunda".';
comment on column fase.ordem is '1 = entrada, 2 = meio, 3 = saida.';
