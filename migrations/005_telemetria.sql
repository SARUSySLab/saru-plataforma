-- Modulo telemetria (6/6 do catalogo) + acervo/ingestao (ingestao, que depende
-- de arquivo_bruto e gravacao) + tracado/subtracado (modulo pista no catalogo,
-- movidos pra cá por dependencia de FK: precisam de volta, que precisa de
-- layout). Fecha com o ALTER que amarra contexto.gravacao_id, coluna criada em
-- 004_operacao.sql antes de gravacao existir.

create table gravacao (
    id            uuid primary key default gen_random_uuid(),
    user_id       uuid references usuario (id),
    bateria_id    uuid references bateria (id),
    piloto_id     uuid references piloto (id),
    layout_id     text references layout (id),
    capturado_em  timestamptz,
    duracao_s     real,
    lap_count     int,
    fastest_lap_s real,
    label         text,
    notes         text,
    metadata      jsonb not null default '{}'::jsonb,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now(),
    constraint uq_gravacao_id_layout unique (id, layout_id),
    constraint ck_gravacao_piloto_sem_bateria check (piloto_id is null or bateria_id is null)
);

comment on table gravacao is 'Era Arquivo de telemetria. Passa a ser a ida a pista capturada por um logger, nao o arquivo em si (um bundle pode ter ate 6 arquivos pra mesma volta, ver arquivo_bruto). Sobrevive a bateria: pode ser importada sozinha, antes de existir evento nenhum (decisao D3 do Lucas).';
comment on column gravacao.bateria_id is 'Nome do plano fechado (o catalogo chama de run_id). Anulavel por decisao D3: a espinha operacional e opcional, nunca pre-requisito. Arquivo solto ingere sem bateria nenhuma.';
comment on column gravacao.piloto_id is 'So preenchido quando bateria_id e nulo: com bateria, o piloto viria da inscricao (fora do recorte). Trava em ck_gravacao_piloto_sem_bateria.';
comment on column gravacao.user_id is 'Anulavel: gravacao de acervo nao tem dono (colecao responderia pela propriedade no catalogo original, mas colecao fica fora do recorte de 26 entidades). Sem colecao, nao ha CHECK de "pelo menos um dos dois" aqui: user_id sozinho pode ser nulo sem alternativa.';
comment on column gravacao.metadata is 'Isencao de 1FN declarada no catalogo: cabecalho cru do arquivo.';
comment on constraint ck_gravacao_piloto_sem_bateria on gravacao is 'D3: piloto_id preenchido apenas quando bateria_id e nulo. Regra dura do catalogo original, mantida.';

create table arquivo_bruto (
    id            uuid primary key default gen_random_uuid(),
    gravacao_id   uuid not null references gravacao (id),
    papel         text not null,
    formato_id    text not null references formato_telemetria (id),
    nome_arquivo  text not null,
    sha256        char(64) not null,
    bytes         bigint not null,
    objeto_uri    text not null,
    compressao    text,
    importado_em  timestamptz not null default now(),
    constraint uq_arquivo_bruto_gravacao_sha256 unique (gravacao_id, sha256),
    constraint uq_arquivo_bruto_gravacao_papel_nome unique (gravacao_id, papel, nome_arquivo),
    constraint uq_arquivo_bruto_id_gravacao unique (id, gravacao_id),
    constraint ck_arquivo_bruto_papel check (papel in ('primario', 'indice', 'gps', 'backup', 'workbook'))
);

create unique index uq_arquivo_bruto_um_primario_por_gravacao
    on arquivo_bruto (gravacao_id)
    where papel = 'primario';

comment on table arquivo_bruto is 'Um por arquivo fisico do bundle. Unique de sha256 e por gravacao, nao global: um .bak byte-identico ao primario tem o mesmo hash, e os dois papeis sao legitimos no mesmo bundle. O indice parcial garante exatamente um papel=primario por gravacao.';
comment on column arquivo_bruto.sha256 is 'Chave natural (gravacao, sha256). Dedupe entre gravacoes vira consulta pelo hash, nao constraint.';

create table serie_amostral (
    id                    uuid primary key default gen_random_uuid(),
    gravacao_id           uuid not null references gravacao (id),
    camada                text not null,
    frequencia_hz         real not null,
    mapa_versao           text references mapa_canal (versao),
    uri                   text not null,
    formato_armazenamento text not null default 'parquet',
    linhas                bigint not null,
    bytes                 bigint not null,
    sha256                char(64) not null,
    t_inicio_s            real,
    t_fim_s               real,
    escrito_em            timestamptz not null default now(),
    constraint uq_serie_amostral_sha256 unique (sha256),
    constraint uq_serie_amostral_gravacao_camada_freq_mapa unique (gravacao_id, camada, frequencia_hz, mapa_versao),
    constraint ck_serie_amostral_camada check (camada in ('bruta', 'canonica')),
    constraint ck_serie_amostral_mapa_por_camada check (
        (camada = 'bruta' and mapa_versao is null)
        or (camada = 'canonica' and mapa_versao is not null)
    )
);

create unique index uq_serie_amostral_gravacao_camada_freq_sem_mapa
    on serie_amostral (gravacao_id, camada, frequencia_hz)
    where mapa_versao is null;

comment on table serie_amostral is 'O ponteiro. O Postgres nunca guarda amostra: guarda onde ela esta (uri em Parquet, particionado por gravacao e taxa nativa), quantas sao e o que a produziu. Analise le com DuckDB. Uma serie por taxa nativa e por camada evita reamostrar (medido no acervo real: um .ld do ACC tem 55 canais em 5 taxas simultaneas).';
comment on column serie_amostral.mapa_versao is 'Nulo na camada bruta (os nomes sao do fabricante, sem mapa). Obrigatorio na canonica: e o mapa que produziu aquela serie.';

create table canal_gravado (
    id                 uuid primary key default gen_random_uuid(),
    gravacao_id        uuid not null references gravacao (id),
    nome_bruto         text not null,
    unidade_declarada  text,
    frequencia_hz      real not null,
    n_amostras         bigint not null,
    valor_min          real,
    valor_max          real,
    canal_canonico_id  text references canal_canonico (id),
    serie_id           uuid not null references serie_amostral (id),
    constraint uq_canal_gravado_gravacao_nome unique (gravacao_id, nome_bruto)
);

comment on table canal_gravado is 'Uma linha por canal presente na captura. canal_canonico_id nulo e resultado valido: canal sem mapa fica registrado e achavel em vez de descartado na porta de entrada (o vocabulario canonico tem ~60 canais, um .ld de MoTeC do acervo tem 221).';
comment on column canal_gravado.unidade_declarada is 'O que o arquivo diz, nao o que o canal e (caso real do catalogo: G_LAT/G_LON do ACC declaram m/s2 e estao em g).';
comment on column canal_gravado.serie_id is 'Aponta pra serie da camada bruta, onde os valores nativos moram. A canonica se resolve por chave (gravacao, camada=canonica, frequencia, mapa_versao), nao por FK direta daqui.';

create table ingestao (
    id               uuid primary key default gen_random_uuid(),
    arquivo_id       uuid not null references arquivo_bruto (id) on delete restrict,
    gravacao_id      uuid not null references gravacao (id) on delete restrict,
    perfil_id        text references perfil_origem (id),
    leitor_versao    text not null,
    mapa_versao      text references mapa_canal (versao),
    status           text not null,
    erro             text,
    canais_lidos     int not null default 0,
    canais_sem_mapa  int not null default 0,
    amostras_escritas bigint not null default 0,
    iniciada_em      timestamptz not null default now(),
    concluida_em     timestamptz,
    constraint fk_ingestao_arquivo_gravacao foreign key (arquivo_id, gravacao_id) references arquivo_bruto (id, gravacao_id),
    constraint uq_ingestao_arquivo_leitor_mapa_inicio unique (arquivo_id, leitor_versao, mapa_versao, iniciada_em),
    constraint ck_ingestao_status check (status in ('ok', 'parcial', 'falhou'))
);

create unique index uq_ingestao_arquivo_leitor_inicio_sem_mapa
    on ingestao (arquivo_id, leitor_versao, iniciada_em)
    where mapa_versao is null;

comment on table ingestao is 'Uma linha por execucao de leitor sobre um arquivo. Append-only: nunca sobrescreve, estado atual = ultimo sucesso. FKs em ON DELETE RESTRICT (decisao do catalogo, 28/08): tabela de auditoria nao pode perder historico em CASCADE silencioso.';
comment on column ingestao.canais_sem_mapa is 'Termometro do vocabulario: se um arquivo entra com 221 canais lidos e 180 sem mapa, nao e erro de ingestao, e o vocabulario canonico nao cobrindo o que aquele logger grava.';

create table volta (
    id         uuid primary key default gen_random_uuid(),
    session_id uuid not null references gravacao (id),
    layout_id  text references layout (id),
    lap_number int not null,
    lap_time_s real not null,
    is_valid   boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint uq_volta_gravacao_numero unique (session_id, lap_number),
    constraint uq_volta_id_layout unique (id, layout_id),
    constraint fk_volta_gravacao_layout foreign key (session_id, layout_id) references gravacao (id, layout_id)
);

comment on table volta is 'Fraca da gravacao. session_id e nome literal do catalogo (legado: aponta pra gravacao, nao pra sessao do modulo operacao - manter o nome evita reescrever o catalogo, mas e fonte de confusao proposital marcada aqui).';
comment on column volta.layout_id is 'Denormalizado da gravacao, nulo enquanto ela nao tem layout resolvido. FK composta (session_id, layout_id) -> gravacao impede tempo_trecho ou tracado cruzarem layout (decisao do catalogo, 28/08).';
comment on column volta.lap_time_s is 'O tempo do arquivo manda sobre a soma dos tempos de trecho; checado por trigger em 006_invariantes.sql porque CHECK nao soma outra tabela.';

create table tracado (
    id            uuid primary key default gen_random_uuid(),
    volta_id      uuid references volta (id),
    layout_id     text not null references layout (id),
    tipo          text not null,
    metodo        text not null,
    metodo_versao text not null,
    n_pontos      int not null,
    uri           text not null,
    sha256        char(64) not null,
    criado_em     timestamptz not null default now(),
    constraint uq_tracado_sha256 unique (sha256),
    constraint uq_tracado_id_layout unique (id, layout_id),
    constraint fk_tracado_volta_layout foreign key (volta_id, layout_id) references volta (id, layout_id),
    constraint ck_tracado_tipo check (tipo in ('medido', 'ideal', 'referencia')),
    constraint ck_tracado_volta_por_tipo check (
        (tipo = 'medido' and volta_id is not null)
        or (tipo in ('ideal', 'referencia') and volta_id is null)
    )
);

create unique index uq_tracado_layout_tipo_metodo_sem_volta
    on tracado (layout_id, tipo, metodo_versao)
    where volta_id is null;

create unique index uq_tracado_volta_tipo_metodo
    on tracado (volta_id, tipo, metodo_versao)
    where volta_id is not null;

comment on table tracado is 'A linha que o carro fez (racing line), derivada de uma volta por GPS, integracao ou otimizador. Nao e sinonimo de layout. tipo=medido exige volta; ideal e referencia nao tem volta de origem (sao a linha otima calculada ou a curada por engenheiro).';
comment on column tracado.metodo_versao is 'Entra na chave natural: rederivar com outro algoritmo produz linha diferente da mesma volta, e as duas sao legitimas (mesmo raciocinio do mapa_canal.versao).';

create table subtracado (
    id             uuid primary key default gen_random_uuid(),
    tracado_id     uuid not null references tracado (id),
    segmento_id    uuid not null references segmento (id),
    layout_id      text not null,
    uri            text,
    n_pontos       int not null,
    offset_medio_m real,
    tracado_ref_id uuid references tracado (id),
    constraint uq_subtracado_tracado_segmento unique (tracado_id, segmento_id),
    constraint fk_subtracado_tracado_layout foreign key (tracado_id, layout_id) references tracado (id, layout_id),
    constraint fk_subtracado_segmento_layout foreign key (segmento_id, layout_id) references segmento (id, layout_id)
);

comment on table subtracado is 'Recorte de um tracado dentro de um segmento (setor, curva ou fase): a linha desta volta neste trecho. uri nula quando o recorte e so uma janela do objeto do tracado, sem objeto proprio.';
comment on column subtracado.tracado_ref_id is 'Tracado de referencia contra o qual offset_medio_m foi calculado. Sem o ponteiro o derivado nao e reproduzivel (mesmo raciocinio do mapa_versao).';

create table tempo_trecho (
    volta_id    uuid not null references volta (id),
    segmento_id uuid not null references segmento (id),
    layout_id   text not null,
    tempo_s     real not null,
    primary key (volta_id, segmento_id),
    constraint fk_tempo_trecho_volta_layout foreign key (volta_id, layout_id) references volta (id, layout_id),
    constraint fk_tempo_trecho_segmento_layout foreign key (segmento_id, layout_id) references segmento (id, layout_id)
);

comment on table tempo_trecho is 'Era tempo_setor. Decisao D1 (Lucas, 28/08): renomeada e o segmento_id passa a apontar pra segmento de qualquer tipo (setor, curva ou fase), nao so setor. E o que da tempo por fase (entrada/meio/saida de uma curva) sem criar uma segunda tabela de tempo: o mesmo segmento_id que hoje aponta pra um setor passa a apontar tambem pra uma fase.';
comment on column tempo_trecho.tempo_s is 'A coluna e_melhor do catalogo original nao foi transcrita: e o proprio catalogo que a marca como erro de modelagem (nao passa na 2FN, depende do conjunto de comparacao, nao da chave). Volta ideal via soma de minimos por setor e calculo do pipeline, nao guarda no banco (guarda dura da tarefa).';

alter table contexto
    add constraint fk_contexto_gravacao foreign key (gravacao_id) references gravacao (id);

comment on constraint fk_contexto_gravacao on contexto is 'Adicionada aqui porque gravacao so existe a partir desta migration; contexto foi criada em 004_operacao.sql.';
