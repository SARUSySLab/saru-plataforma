-- Duas decisoes do Lucas (29/08), tomadas ao carregar o aliases.yaml real do
-- saru-app e descobrir que o dado nao cabia no schema.

-- 1. A chave de `mapeamento_canal` estava invertida.
--
-- A dependencia funcional real e coluna bruta -> canal canonico, nunca o
-- contrario: `G_Lat` resolve pra `lat_acc`, e `lat_acc` nao resolve pra um
-- nome so. Medido: 35 das 306 linhas do aliases.yaml (11%) aceitam mais de um
-- nome de coluna pro mesmo canal, e o `fueltech.lat_acc` sozinho aceita tres
-- (Acelerometro Y, Accel_Y, G_Lat).
--
-- Com a PK antiga so cabia um nome por canal por versao de mapa. Com a nova,
-- N colunas brutas apontam pro mesmo canonico, cada uma com unidade e fator
-- proprios, que e o que importa: `G_Lat` chega em g e `Accel_Y` pode chegar
-- em m/s2, e o fator nao e o mesmo.
alter table mapeamento_canal
    drop constraint uq_mapeamento_canal_coluna,
    drop constraint mapeamento_canal_pkey,
    add primary key (perfil_id, coluna_bruta, mapa_versao);

-- Indice pro caminho inverso, que a analise usa: dado o canal canonico, quais
-- colunas brutas daquele perfil o alimentam.
create index ix_mapeamento_canal_canonico
    on mapeamento_canal (perfil_id, canal_canonico_id, mapa_versao);

comment on table mapeamento_canal is
    'Coluna bruta -> canal canonico, por perfil e por versao de mapa. A chave e '
    'a coluna bruta porque e ela que resolve: N nomes de fabricante caem no '
    'mesmo canal do dominio, cada um com sua unidade e seu fator. Sem versao, '
    'corrigir um alias apaga a auditoria: o caso real foi o fator do G_LAT do '
    'ACC, que era 1,0 e passou a 9,80665.';

comment on column mapeamento_canal.coluna_bruta is
    'O nome exato que o fabricante escreveu no arquivo. Parte da chave.';

-- 2. `normalize_by_max` sai. O freio fica na unidade nativa.
--
-- Nove linhas do aliases.yaml usam normalizacao pelo maximo do proprio
-- arquivo, e sao todas `brake`, exatamente nos 9 perfis de logger real
-- (motec_ld, aim_xrk, aim_drk, vbox, fueltech, protune, pi_core,
-- listhead_dat, pi_pid).
--
-- Alem de nao ser transformacao afim (nao cabe em fator + offset), ela quebra
-- o produto: normalizar pelo maximo do arquivo faz a mesma pressao fisica
-- virar numero diferente em arquivos diferentes, e comparar volta contra
-- referencia e o que o bloco 9 vende. E a mesma doenca que o cabecalho do
-- aliases.yaml descreve no bug do `g`: mais de uma unidade viva no mesmo
-- canal canonico.
--
-- Decisao: a serie canonica guarda o freio na unidade nativa. Quem precisa de
-- 0 a 1 normaliza na analise, declarando contra o que normalizou.
alter table mapeamento_canal
    add constraint ck_mapeamento_canal_transformacao_afim
    check (fator_escala is not null and "offset" is not null);

comment on constraint ck_mapeamento_canal_transformacao_afim on mapeamento_canal is
    'A traducao bruto -> canonico e afim e so afim: bruto * fator + offset. '
    'Normalizacao dependente do conteudo do arquivo (o normalize_by_max do '
    'aliases.yaml) nao entra aqui, por decisao do Lucas em 29/08.';
