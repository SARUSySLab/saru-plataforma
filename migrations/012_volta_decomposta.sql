-- Etapa 6 (decomposicao): `volta` passa a declarar como o eixo de distancia
-- daquela volta foi obtido e o quanto ele foi ajustado.
--
-- Setor e curva moram em DISTANCIA (`segmento.s_inicio_m`/`s_fim_m`), e a
-- amostra vem em TEMPO. Decompor e cruzar os dois, e pra isso a volta precisa
-- de um eixo de distancia. Ele vem por cascata, decisao do Lucas (29/08): canal
-- de distancia do proprio arquivo, integral da velocidade, ou deslocamento
-- acumulado do GPS. As tres produzem o mesmo tipo de numero com confianca
-- diferente, e sem `dist_origem` gravada ninguem sabe depois qual delas
-- respondeu (mesmo raciocinio de `volta.origem`, migration 011).
--
-- `dist_fator` e o ajuste que fechou a volta no comprimento do layout. Medir
-- distancia integrando velocidade acumula erro de calibracao, e sem fechar, o
-- ultimo setor absorve toda a sobra e as fronteiras internas escorregam. O
-- fator fica gravado porque escalar dado sem dizer o quanto e maquiagem: com a
-- coluna, um fator de 1,08 aparece como calibracao ruim daquele logger em vez
-- de virar tempo de setor plausivel e errado.
--
-- A guarda de faixa (0,9 a 1,1) e a mesma familia do B1: fora dela nao e
-- calibracao, e pista errada ou volta mal cortada, e a volta fica sem
-- decomposicao em vez de ganhar setor de outra pista. Comparar: o B1 somava
-- setores de Interlagos (4.309 m) numa volta de kart de 1,1 km, o que daria
-- fator 3,9 aqui.
--
-- As duas colunas moram em `volta`, nao em `tempo_trecho`: origem e fator sao
-- da volta inteira, e repeti-los por segmento seria a transitiva que o
-- catalogo rejeita em outros pontos (o proprio catalogo cortou `e_melhor` de
-- tempo_trecho pelo mesmo motivo).

alter table volta
    add column dist_origem text,
    add column dist_fator  real;

alter table volta
    add constraint ck_volta_dist_origem
        check (dist_origem is null or dist_origem in ('canal', 'velocidade', 'gps')),
    add constraint ck_volta_dist_fator_faixa
        check (dist_fator is null or dist_fator between 0.9 and 1.1),
    add constraint ck_volta_dist_par
        check ((dist_origem is null) = (dist_fator is null));

comment on column volta.dist_origem is 'Como o eixo de distancia desta volta foi obtido: canal (o arquivo mede distancia), velocidade (integral de speed no tempo) ou gps (deslocamento acumulado). Nulo enquanto a volta nao foi decomposta, que e estado valido: volta cortada sem setorizacao existe.';
comment on column volta.dist_fator is 'Fator aplicado pra fechar a distancia medida no comprimento do layout (comprimento / medido). 1,0 significa que fechou sozinho. Nulo junto com dist_origem.';
comment on constraint ck_volta_dist_fator_faixa on volta is 'Fora de 0,9 a 1,1 a divergencia deixa de ser calibracao e passa a ser pista errada ou volta mal cortada, e a volta tem que ficar sem decomposicao. O CHECK existe pra tornar impossivel gravar o caso: se o codigo tentar, o banco recusa em vez de aceitar setor de outra pista.';
comment on constraint ck_volta_dist_par on volta is 'As duas contam a mesma historia: origem sem fator seria decomposicao sem ajuste declarado, fator sem origem seria ajuste sem fonte.';
