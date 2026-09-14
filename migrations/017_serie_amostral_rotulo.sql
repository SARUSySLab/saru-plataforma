-- 017: rotulo de serie em serie_amostral.
--
-- O leitor .xrk passou a decodificar o chunk GPS (NAV-SOL) como uma serie
-- PROPRIA, com relogio e colunas proprios, que em 23 dos 113 arquivos com GPS
-- do acervo (medido em 29/08) cai na MESMA taxa de um grupo CHS ja existente
-- (25 Hz e comum aos dois). A unicidade por (gravacao, camada, taxa) da 005
-- passa a incluir o rotulo: duas series na mesma taxa convivem quando sao
-- fluxos declaradamente diferentes, e continuam proibidas quando nao sao.
--
-- '' (vazio) e a serie principal da taxa, o comportamento de sempre; 'gps' e
-- o primeiro rotulo real. Linhas existentes ganham '' e nada muda pra elas.

alter table serie_amostral add column serie text not null default '';

comment on column serie_amostral.serie is
    'Rotulo do fluxo dentro da taxa: vazio = serie principal (comportamento anterior a esta migration); gps = canais sintetizados do chunk GPS do .xrk, que tem relogio proprio e podem cair na mesma taxa de um grupo de canais do fabricante.';

alter table serie_amostral
    drop constraint uq_serie_amostral_gravacao_camada_freq_mapa;
alter table serie_amostral
    add constraint uq_serie_amostral_gravacao_camada_freq_mapa
    unique (gravacao_id, camada, frequencia_hz, mapa_versao, serie);

drop index uq_serie_amostral_gravacao_camada_freq_sem_mapa;
create unique index uq_serie_amostral_gravacao_camada_freq_sem_mapa
    on serie_amostral (gravacao_id, camada, frequencia_hz, serie)
    where mapa_versao is null;
