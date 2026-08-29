-- Invariantes que CHECK sozinho nao resolve porque atravessam tabela.
-- Todos deferrable initially deferred: a carga de um layout ou de uma volta
-- grava varias linhas relacionadas na mesma transacao (segmento antes do
-- subtipo, tempo_trecho de varios segmentos antes de fechar a volta), e a
-- ordem dentro da transacao nao devia importar pro invariante.

-- 1. segmento.s_fim_m contra layout.comprimento_m (decisao do Lucas, 28/08).
create or replace function trg_fn_segmento_dentro_do_layout()
returns trigger as $$
declare
    v_comprimento real;
begin
    select comprimento_m into v_comprimento from layout where id = new.layout_id;
    if v_comprimento is not null and new.s_fim_m > v_comprimento then
        raise exception 'segmento % (tipo %, ordem %) tem s_fim_m=% maior que layout.comprimento_m=% do layout %',
            new.id, new.tipo, new.ordem, new.s_fim_m, v_comprimento, new.layout_id;
    end if;
    return new;
end;
$$ language plpgsql;

create constraint trigger tg_segmento_dentro_do_layout
    after insert or update of s_fim_m, layout_id on segmento
    deferrable initially deferred
    for each row
    execute function trg_fn_segmento_dentro_do_layout();

comment on function trg_fn_segmento_dentro_do_layout() is 'CHECK nao atravessa tabela (segmento -> layout), por isso e trigger. O comprimento do layout manda; a setorizacao confere contra ele, nunca o contrario.';

-- 2. Todo segmento tem exatamente uma linha de subtipo (setor, curva ou fase).
-- reta fica de fora do recorte: um segmento tipo='reta' nunca passa aqui,
-- porque nao existe tabela reta nesta PoC. E o comportamento correto para uma
-- entidade fora de escopo (recusar em vez de aceitar orfao).
create or replace function trg_fn_segmento_tem_subtipo()
returns trigger as $$
declare
    v_existe boolean;
begin
    if new.tipo = 'setor' then
        select exists(select 1 from setor where segmento_id = new.id) into v_existe;
    elsif new.tipo = 'curva' then
        select exists(select 1 from curva where segmento_id = new.id) into v_existe;
    elsif new.tipo = 'fase' then
        select exists(select 1 from fase where segmento_id = new.id) into v_existe;
    else
        v_existe := false;
    end if;
    if not v_existe then
        raise exception 'segmento % tipo % nao tem linha de subtipo correspondente (reta fora do recorte desta PoC, ver 003_pista.sql)',
            new.id, new.tipo;
    end if;
    return new;
end;
$$ language plpgsql;

create constraint trigger tg_segmento_tem_subtipo
    after insert or update of tipo on segmento
    deferrable initially deferred
    for each row
    execute function trg_fn_segmento_tem_subtipo();

comment on function trg_fn_segmento_tem_subtipo() is 'Fecha o cadeado de subtipo que UNIQUE (id, tipo) + FK composta nao fecham sozinhos: sem isto, um segmento podia ficar sem nenhuma linha de setor/curva/fase (orfao total). Deferred pra dar tempo do INSERT do subtipo acontecer na mesma transacao.';

-- 3. Curva contida no setor dono (decisao do Lucas, 28/08: achou 13 de 148
-- curvas do tracks.yaml cruzando fronteira de setor ao medir).
create or replace function trg_fn_curva_dentro_do_setor()
returns trigger as $$
declare
    v_curva_inicio real;
    v_curva_fim    real;
    v_setor_inicio real;
    v_setor_fim    real;
begin
    select s_inicio_m, s_fim_m into v_curva_inicio, v_curva_fim
        from segmento where id = new.segmento_id;
    select s_inicio_m, s_fim_m into v_setor_inicio, v_setor_fim
        from segmento where id = (select segmento_id from setor where segmento_id = new.setor_id);

    if v_curva_inicio < v_setor_inicio or v_curva_fim > v_setor_fim then
        raise exception 'curva % (segmento %, s=[%,%]) nao cabe dentro do setor % (s=[%,%])',
            new.corner_id, new.segmento_id, v_curva_inicio, v_curva_fim,
            new.setor_id, v_setor_inicio, v_setor_fim;
    end if;
    return new;
end;
$$ language plpgsql;

create constraint trigger tg_curva_dentro_do_setor
    after insert or update of segmento_id, setor_id on curva
    deferrable initially deferred
    for each row
    execute function trg_fn_curva_dentro_do_setor();

comment on function trg_fn_curva_dentro_do_setor() is 'Curva pertence a exatamente um setor e nao atravessa fronteira, por decisao de dominio. Sem esta checagem os 13 casos medidos no tracks.yaml (Spoon de Suzuka, Remus do Red Bull Ring, Esse de Goiania) entrariam como dado errado silencioso.';

-- 4. Soma de tempo_trecho (so os trechos tipo=setor, que particionam a volta
-- inteira sem sobreposicao) nao pode passar do tempo do arquivo. Curva e fase
-- ficam de fora da soma de proposito: sao subdivisoes de um setor, somar os
-- tres niveis juntos contaria o mesmo trecho de pista mais de uma vez.
create or replace function trg_fn_tempo_trecho_soma_volta()
returns trigger as $$
declare
    v_soma_setores real;
    v_lap_time     real;
    v_tolerancia   constant real := 0.05; -- folga de arredondamento entre fontes, nao e guarda de negocio
begin
    select lap_time_s into v_lap_time from volta where id = new.volta_id;

    select coalesce(sum(tt.tempo_s), 0) into v_soma_setores
        from tempo_trecho tt
        join segmento sg on sg.id = tt.segmento_id
        where tt.volta_id = new.volta_id
          and sg.tipo = 'setor';

    if v_lap_time is not null and v_soma_setores > v_lap_time + v_tolerancia then
        raise exception 'volta %: soma dos tempos de setor (%) maior que lap_time_s do arquivo (%)',
            new.volta_id, v_soma_setores, v_lap_time;
    end if;
    return new;
end;
$$ language plpgsql;

create constraint trigger tg_tempo_trecho_soma_volta
    after insert or update of tempo_s, volta_id, segmento_id on tempo_trecho
    deferrable initially deferred
    for each row
    execute function trg_fn_tempo_trecho_soma_volta();

comment on function trg_fn_tempo_trecho_soma_volta() is 'O tempo do arquivo (volta.lap_time_s) manda; a soma dos setores e a decomposicao que confere contra ele, nunca a fonte (nota do catalogo, decisao do Lucas 28/08). Escopo restrito a segmento tipo=setor: curva e fase sao subdivisoes de um setor, e somar os tres niveis de granularidade juntos contaria o mesmo pedaco de pista mais de uma vez. Nao e a guarda do B1 (volta ideal <= melhor volta) - aquela e invariante de calculo entre voltas e fica fora do banco por decisao explicita desta tarefa.';
