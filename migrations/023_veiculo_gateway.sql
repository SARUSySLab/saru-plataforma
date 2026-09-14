-- Veiculo e gateway: identidade de carro para o pit wall ao vivo.
--
-- Decisao do Lucas em 30/08, escopo MINIMO de proposito. A entidade `veiculo`
-- estava declarada fora do recorte na 004, e volta agora porque sem ela nao
-- existe grid de n carros, nem alarme com dono, nem credencial por carro.
-- Continua SEM classe: o comparativo por evento segue rebaixado (decisao 13
-- do plano) ate alguem pedir, e classe sem dado de veiculo confiavel so
-- produziria pódio que mede preparacao, nao piloto.
--
-- `numero` e TEXTO, nunca inteiro. O grid real do MBR tem #08, #033, #001 e
-- #2 ao mesmo tempo: converter para numero funde carros diferentes num so.

create table if not exists veiculo (
  id          uuid primary key default gen_random_uuid(),
  dono_id     uuid not null references usuario(id) on delete cascade,
  numero      text,
  apelido     text not null,
  modelo_txt  text,
  criado_em   timestamptz not null default now(),
  unique (dono_id, apelido)
);

-- Um gateway por carro. O token e o que autentica a ingestao ao vivo: nao e
-- sessao de humano, e credencial de maquina, revogavel sozinha sem derrubar
-- ninguem. Guardado como sha256 pelo mesmo motivo do maquina_token: vazamento
-- de dump nao pode virar acesso.
create table if not exists gateway (
  id               uuid primary key default gen_random_uuid(),
  veiculo_id       uuid not null references veiculo(id) on delete cascade,
  token_sha256     text not null unique,
  nome             text not null,
  ultimo_pacote_em timestamptz,
  criado_em        timestamptz not null default now()
);

create index if not exists gateway_veiculo_idx on gateway (veiculo_id);

-- Lote recebido ao vivo. NAO guarda amostra: amostra vive em Parquet e o
-- Postgres guarda ponteiro (regra do 005). Aqui fica so o suficiente para
-- deduplicar reenvio e para saber o que foi recebido por radio, porque quando
-- o arquivo do cartao chegar ele VENCE o radio e o trecho ao vivo e descartado.
create table if not exists vivo_lote (
  id           uuid primary key default gen_random_uuid(),
  veiculo_id   uuid not null references veiculo(id) on delete cascade,
  sessao_txt   text not null default '',
  seq          bigint not null,
  amostras     integer not null,
  t_inicio_s   double precision,
  t_fim_s      double precision,
  recebido_em  timestamptz not null default now(),
  -- reenvio por rede ruim e ESPERADO: o gateway repete o POST quando nao ve
  -- resposta. Repetir nao pode duplicar amostra nem furar a contagem.
  unique (veiculo_id, sessao_txt, seq)
);

create index if not exists vivo_lote_recente_idx on vivo_lote (veiculo_id, recebido_em desc);
