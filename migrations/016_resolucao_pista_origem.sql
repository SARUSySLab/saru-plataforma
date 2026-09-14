-- Degrau "perguntado" da cascata de resolucao de pista (plano original:
-- alias > GPS > perguntar ao usuario). O contrato de leitura ja reservava
-- `resolucao_pista: "perguntado"` desde o primeiro dia; faltava o banco saber
-- COMO cada gravacao resolveu, porque o relatorio inferia "alias" de qualquer
-- layout preenchido, o que mentiria no dia em que o usuario cravasse a pista.

alter table gravacao add column layout_origem text;

alter table gravacao add constraint ck_gravacao_layout_origem
  check (layout_origem is null or layout_origem in ('alias', 'gps', 'perguntado'));

comment on column gravacao.layout_origem is 'Como layout_id foi resolvido: alias (venue declarado no arquivo), gps (tracado), perguntado (o usuario cravou). NULL quando layout_id e nulo ou quando a gravacao e anterior a esta migration, caso em que o relatorio assume alias, que era o unico degrau existente ate entao.';
