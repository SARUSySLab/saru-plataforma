-- Etapa 5 (corte de voltas): `volta` passa a declarar de onde ela veio e onde
-- ela esta na captura.
--
-- Duas adicoes, decisao do Lucas (29/08):
--
-- 1. PROVENIENCIA (origem + metodo_versao). A volta pode nascer de tres
--    lugares diferentes: o canal de volta gravado na propria amostra, os
--    tempos de beacon do sidecar .ldx, ou o cruzamento da linha de chegada
--    calculado por GPS. Sem a coluna, volta lida do arquivo e volta calculada
--    por nos ficam indistinguiveis no banco, que e a mesma doenca do B2 com
--    outra roupa: o numero existe e ninguem sabe de onde saiu.
--
-- 2. JANELA (t_inicio_s + t_fim_s). `lap_time_s` diz quanto a volta durou, nao
--    ONDE ela esta na serie. A etapa 6 precisa recortar a amostra e o tracado
--    daquela volta, e o endpoint de amostra precisa devolver uma volta so.
--    Guardar a janela aqui evita refazer o corte pra descobrir a fronteira, e
--    evita a mesma verdade morar em dois lugares.
--
-- metodo_versao entra pelo mesmo motivo de mapa_canal.versao e de
-- tracado.metodo_versao: trocar o algoritmo de corte produz fronteira
-- diferente da mesma captura, e as duas sao legitimas enquanto estiver escrito
-- qual produziu qual.

alter table volta
    add column origem        text not null,
    add column metodo_versao text not null,
    add column t_inicio_s    real not null,
    add column t_fim_s       real not null;

alter table volta
    add constraint ck_volta_origem check (origem in ('beacon', 'gps')),
    add constraint ck_volta_janela check (t_fim_s > t_inicio_s),
    add constraint ck_volta_janela_bate_lap_time
        check (abs((t_fim_s - t_inicio_s) - lap_time_s) <= 0.05);

comment on column volta.origem is 'De onde saiu o corte: beacon (o arquivo demarcou, seja por canal na amostra ou por tempo declarado no sidecar) ou gps (nos calculamos o cruzamento da linha de chegada). Nao existe terceiro valor: volta que o sistema nao conseguiu cortar nao vira linha, e o motivo fica no relatorio da etapa 5, nunca em volta com origem nula.';
comment on column volta.metodo_versao is 'Qual metodo produziu esta fronteira, com versao. Ex.: canal_contador-1, canal_pulso-1, ldx_beacon-1, gate_perpendicular-1. Entra na leitura da etapa 6: recortar amostra contra fronteira de metodo antigo e reproduzir dado velho sem saber.';
comment on column volta.t_inicio_s is 'Inicio da volta no eixo de tempo da captura (o mesmo t_s das series em Parquet). E o que permite recortar a amostra desta volta sem refazer o corte.';
comment on column volta.t_fim_s is 'Fim da volta no mesmo eixo. Coincide com o t_inicio_s da volta seguinte quando as duas sao consecutivas: a passagem pela linha e um instante so, fim de uma e inicio da outra.';
comment on constraint ck_volta_janela_bate_lap_time on volta is 'A janela e o tempo tem que contar a mesma historia. Tolerancia de 0,05 s e a mesma folga de arredondamento do trigger de soma de tempo_trecho (006), nao guarda de negocio: e para absorver a precisao de real, nao para tolerar corte errado.';
