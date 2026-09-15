-- Issue #36: o zero de Acc Long/Acc Lat do `.pid` do F3 muda por sessao (offset
-- medido entre 12,85 e 13,18 G no longitudinal, 12,44 a 12,50 G no lateral,
-- 23 pares contra o `.dat` do Pi Toolbox, ver `docs/pi-pid-medicao.md` secao 3
-- e 7). `mapeamento_canal` e por PERFIL: fator_escala/offset valem pra toda
-- gravacao daquele perfil, entao nao cabe guardar ali um offset que muda
-- arquivo a arquivo. E a lacuna de esquema que a issue pede pra declarar em
-- vez de forcar constante estatica no aliases.yaml.
--
-- Uma linha por (gravacao, canal canonico) calibrado. O pipeline de ingestao
-- mede o proprio arquivo (media da contagem crua num trecho de referencia,
-- ex.: carro parado, Speed = 0 sustentado) e grava aqui; sem trecho
-- identificavel, NENHUMA linha e escrita e o canal fica fora do vocabulario
-- canonico daquela gravacao (nunca adivinha constante).
create table calibracao_canal_gravado (
    gravacao_id      uuid not null references gravacao (id) on delete cascade,
    canal_canonico_id text not null references canal_canonico (id),
    offset_contagem  double precision not null,
    metodo           text not null,
    n_amostras       integer not null,
    t_inicio_s       double precision not null,
    t_fim_s          double precision not null,
    calculado_em     timestamptz not null default now(),
    primary key (gravacao_id, canal_canonico_id)
);

comment on table calibracao_canal_gravado is
    'Offset calibrado POR GRAVACAO (na unidade nativa/contagem, nao na '
    'canonica), medido pelo proprio arquivo pelo pipeline de ingestao. '
    'Complementa mapeamento_canal (fator/offset por PERFIL, estatico): '
    'leitura.fator_do_canal combina os dois — canonico = fator*bruto + '
    'offset_perfil - fator*offset_contagem. Gravacao sem linha aqui para um '
    'canal que exige calibracao fica com esse canal fora do inventario '
    '(canal_gravado.canal_canonico_id nulo), nunca com offset adivinhado.';

comment on column calibracao_canal_gravado.offset_contagem is
    'Media da contagem crua no trecho de referencia (ex.: carro parado). '
    'Fica em unidade nativa (contagem), nao convertida, pra a conversao '
    'ficar so em fator_do_canal e nao duplicar a constante medida.';

comment on column calibracao_canal_gravado.metodo is
    'Como o offset foi medido, ex. "zero_estacionario_speed" (media da '
    'contagem crua no maior trecho contiguo com Speed = 0). Documenta a '
    'premissa pra quem for confiar no numero.';

comment on column calibracao_canal_gravado.n_amostras is
    'Tamanho do trecho de referencia usado pra medir o offset. Trecho curto '
    'demais e ruido, nao calibracao: quem consome decide o piso.';
