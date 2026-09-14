-- Modulo acervo/ingestao (parte de vocabulario, 6 entidades):
-- formato_telemetria, perfil_origem, grandeza, canal_canonico, mapa_canal, mapeamento_canal.
-- ingestao mora em 005_telemetria.sql porque depende de arquivo_bruto e gravacao.
-- Fora do recorte: colecao (piloto tem dono direto no user_id).

create table formato_telemetria (
    id              text    primary key,
    rotulo          text    not null,
    fabricante      text    not null,
    extensao_tipica text    not null,
    assinatura      text,
    binario         boolean not null,
    leitor          text    not null,
    leitor_ref      text,
    constraint uq_formato_telemetria_assinatura unique (assinatura),
    constraint ck_formato_telemetria_leitor check (leitor in ('nativo', 'vendor', 'ausente'))
);

comment on table formato_telemetria is 'Vocabulario controlado dos formatos de arquivo. Identificacao e por bytes magicos (assinatura), nunca por extensao: no acervo .dat e .bak aparecem em ecossistemas diferentes.';
comment on column formato_telemetria.leitor is 'leitor = ausente e estado valido: formato sem parser ainda entra no catalogo, ganha checksum, e espera o leitor em vez de ficar fora do banco.';

create table perfil_origem (
    id         text    primary key,
    formato_id text    not null references formato_telemetria (id),
    rotulo     text    not null,
    simulado   boolean not null,
    heuristica text
);

comment on table perfil_origem is 'Mais fino que formato: o mesmo .ld serve ACC, GT7 e MoTeC com colunas diferentes. Perfil e resultado de deteccao (muda com a versao do detector), por isso mora na ingestao e nao no arquivo bruto.';

create table grandeza (
    id              text primary key,
    rotulo          text not null,
    unidade_canonica text not null,
    dimensao_si     text
);

comment on table grandeza is 'Sete linhas que existem so para impedir a transitiva: se unidade_canonica morasse no canal canonico, dependeria da grandeza dele, nao da chave.';

create table canal_canonico (
    id               text    primary key,
    rotulo           text    not null,
    grandeza_id      text    not null references grandeza (id),
    canto            text,
    ponto            text,
    dominio          text    not null,
    obrigatorio      boolean not null,
    constraint ck_canal_canonico_canto check (canto is null or canto in ('fl', 'fr', 'rl', 'rr')),
    constraint ck_canal_canonico_dominio check (dominio in ('carro', 'moto', 'ambos'))
);

comment on table canal_canonico is 'Vocabulario do dominio: cerca de 60 canais. canto e ponto ficam nulos na maioria; a unicidade real e o proprio id (o catalogo registra que a chave composta anterior era decorativa, NULL nao colide em unique).';
comment on column canal_canonico.canto is 'Nulo quando o canal nao e por canto. Valores validos inferidos a partir da nota do catalogo (fl/fr/rl/rr).';
comment on column canal_canonico.ponto is 'inner/mid/outer na temperatura de pneu. Sem CHECK explicito no catalogo alem do exemplo; nao travado aqui por falta de enumeracao fechada no texto-fonte.';

create table mapa_canal (
    versao        text primary key,
    publicado_em  timestamptz not null default now(),
    nota          text
);

comment on table mapa_canal is 'Cabecalho da versao do mapa de canais. Existe porque mapa_versao aparece em tres tabelas com FK para Mapeamento de canal, cuja chave e tripla: uma coluna solta nao referencia chave tripla.';

create table mapeamento_canal (
    perfil_id         text not null references perfil_origem (id),
    canal_canonico_id text not null references canal_canonico (id),
    mapa_versao       text not null references mapa_canal (versao),
    coluna_bruta      text not null,
    unidade_entrada   text not null,
    fator_escala      real not null,
    "offset"          real not null default 0,
    nota              text,
    primary key (perfil_id, canal_canonico_id, mapa_versao),
    constraint uq_mapeamento_canal_coluna unique (perfil_id, coluna_bruta, mapa_versao)
);

comment on table mapeamento_canal is 'Perfil x canal canonico, versionado. Sem versao, corrigir um alias apaga a auditoria: o caso real foi o fator do G_LAT do ACC, que era 1,0 e passou a 9,80665.';
comment on column mapeamento_canal."offset" is 'Zero no caso linear puro. Sem ele Fahrenheit para Celsius nao fecha: fator sozinho so cobre conversao proporcional.';
