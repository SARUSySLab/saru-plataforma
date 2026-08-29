-- Cache persistente de clima (resiliencia a 429 do provedor, 29/08).
--
-- Diagnostico em producao: o Open-Meteo limita por IP, e o IP de saida do
-- Railway e compartilhado entre varios clientes da plataforma. A cota diaria
-- ja chega estourada mesmo sem o nosso trafego. Nao e bug de codigo, e
-- escolha de provedor incompativel com hospedagem de IP compartilhado.
--
-- O cache em memoria (dict do processo) morria a cada deploy e nao era
-- compartilhado entre instancias. Uma tabela resolve as duas coisas: uma
-- busca bem sucedida serve todos os clientes, e sobrevive a reinicio, o que
-- reduz muito o consumo da cota que resta.
--
-- Chave e a coordenada arredondada (mesmo arredondamento que o modulo ja usava
-- pro cache em memoria): layouts proximos cairiam na mesma previsao de
-- qualquer forma, arredondar so evita uma linha por decimal irrelevante.

create table clima_cache (
    latitude    numeric(6, 3) not null,
    longitude   numeric(6, 3) not null,
    payload     jsonb not null,
    buscado_em  timestamptz not null,
    primary key (latitude, longitude)
);

comment on table clima_cache is 'Ultima previsao valida por coordenada arredondada. Sobrevive a deploy e e compartilhada entre todos os clientes, ao contrario do cache em memoria anterior. Quando a fonte falha (429, timeout), a rota serve esta linha com a idade declarada em vez de 502.';
comment on column clima_cache.payload is 'O dado normalizado (mesmo shape independente do provedor: Open-Meteo ou OpenWeather). Nao guarda a resposta bruta da fonte.';
comment on column clima_cache.buscado_em is 'Quando este payload foi obtido da fonte com sucesso. E o campo que a rota usa pra calcular a idade do dado quando serve degradado.';
