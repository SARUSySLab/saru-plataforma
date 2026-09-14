-- Avisos da direcao de prova: track limits e penalidades.
--
-- Pedido do Vitor Saru em 29/08 ("e bom ter, pq tem tracklimits; tem um .xml
-- que tem isso"). O feed `announcements` do MyLaps/Orbits e um resultspage sem
-- labels de evento, so com data, hora e texto.
--
-- O TEXTO CRU E COLUNA OBRIGATORIA. A extracao de carro e reincidencia mora em
-- `carros` (jsonb) e e camada por cima: aviso que nao casa com padrao nenhum
-- entra com `carros` vazio e tipo 'texto', nunca e descartado. Se um dia a
-- regra de extracao melhorar, o cru permite reprocessar sem pedir o XML de
-- volta pra organizacao.
--
-- Numero de carro e TEXTO dentro do jsonb, nunca inteiro: o grid real tem #08,
-- #033, #001 e #2, e converter pra numero funde carros diferentes.

create table if not exists lt_aviso (
  id            uuid primary key default gen_random_uuid(),
  evento_id     uuid not null references lt_evento(id) on delete cascade,
  data_txt      text not null,
  hora_txt      text not null,
  texto         text not null,
  tipo          text not null check (tipo in ('track_limit', 'perda_de_volta', 'indefinido', 'texto')),
  carros        jsonb not null default '[]'::jsonb,
  criado_em     timestamptz not null default now(),
  -- o feed e relido a cada poll e o mesmo aviso chega dezenas de vezes:
  -- deduplica pelo que identifica o aviso na origem, nao por id gerado aqui.
  unique (evento_id, data_txt, hora_txt, texto)
);

create index if not exists lt_aviso_evento_idx on lt_aviso (evento_id, hora_txt desc);
