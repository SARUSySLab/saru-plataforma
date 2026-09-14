-- A invariante de curva x setor estava estrita demais e barrava dado real.
--
-- A versao da 006 exigia que a curva coubesse INTEIRA dentro do setor dono. Ao
-- carregar o tracks.yaml do saru-app isso rejeitou a primeira curva que
-- encontrou, e a medicao mostrou que nao e caso isolado: 13 das 148 curvas
-- (9%) atravessam fronteira de setor. Exemplos:
--
--   senna_kart/T2    'Curva do S'  s=[300,450]   apex=370   S1=[0,380]
--   barcelona/T5     'Chicane S/F' s=[1200,1420] apex=1300  S2=[1300,3100]
--   red_bull_ring/T2 'Remus'       s=[650,900]   apex=780   S1=[0,850]
--   zolder/T4        'Chicane'     s=[2400,2700] apex=2550  S3=[2500,4011]
--
-- Sao curvas reais e nomeadas, nao erro de digitacao. Fronteira de setor e
-- ponto de cronometragem, escolhido por conveniencia de medicao, e nao tem
-- obrigacao nenhuma de coincidir com o fim de uma curva. A chicane de largada
-- de Barcelona atravessar a divisa do S2 e o esperado, nao a excecao.
--
-- O catalogo diz que `curva.setor_id` e o setor DONO ("Obrigatorio: toda curva
-- tem um setor dono"), e dono nao e o mesmo que continente. O ponto que define
-- a curva e o apex: o proprio catalogo registra que `s_apex_m` e "o unico dos
-- tres pontos que e da curva, e nao do segmento". Entao o dono passa a ser o
-- setor que contem o apex, e e isso que a trigger valida.
create or replace function trg_fn_curva_dentro_do_setor()
returns trigger as $$
declare
    v_apex         real;
    v_setor_inicio real;
    v_setor_fim    real;
begin
    select s_apex_m into v_apex from curva where segmento_id = new.segmento_id;
    select s_inicio_m, s_fim_m into v_setor_inicio, v_setor_fim
        from segmento
        where id = (select segmento_id from setor where segmento_id = new.setor_id);

    if v_apex is null then
        return new;  -- curva sem apex medido nao tem como ser ancorada
    end if;

    if v_apex < v_setor_inicio or v_apex >= v_setor_fim then
        raise exception
            'curva % tem apex em % fora do setor dono % (s=[%,%)). O dono de '
            'uma curva e o setor que contem o apex.',
            new.corner_id, v_apex, new.setor_id, v_setor_inicio, v_setor_fim;
    end if;
    return new;
end;
$$ language plpgsql;

comment on function trg_fn_curva_dentro_do_setor() is
    'O setor dono de uma curva e o que contem o APEX, nao o que a contem '
    'inteira. Medido em 29/08: 13 das 148 curvas do tracks.yaml atravessam '
    'fronteira de setor, porque fronteira de setor e linha de cronometragem e '
    'nao geometria. Exigir continencia rejeitava dado real.';
