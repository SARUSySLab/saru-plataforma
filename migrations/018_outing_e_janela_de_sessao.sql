-- D4 (decisao do Lucas, 29/08, opcao B): o vocabulario do dominio muda na
-- SUPERFICIE (tela fala "outing"), o banco mantem os nomes ate uma janela de
-- rename dedicada. O que entra AGORA e o que faltava de estrutura:
--   - sessao.ends_at: a sessao e a janela de pista aberta (horario fixo,
--     comeco E fim); so havia starts_at.
--   - bateria.label: "B1", "Outing 2"... nao existia coluna de nome.
--   - bateria.objective: o que o piloto saiu pra fazer nesta ida a pista.
-- Os dois horarios que o Vitor pediu ja existiam (created_at = criacao,
-- went_out_at = carro saiu do box); nada a fazer neles.

alter table sessao add column ends_at timestamptz;
comment on column sessao.ends_at is 'Fim da janela de pista. Sessao tem horario fixo; outings acontecem dentro dela.';

alter table bateria add column label text;
comment on column bateria.label is 'Nome do outing na tela (B1, Treino 1...). O banco ainda chama a entidade de bateria; rename estrutural fica pra depois da fase de testes (D4-B).';

alter table bateria add column objective text;
comment on column bateria.objective is 'O que o piloto saiu pra fazer neste outing (run sheet).';
