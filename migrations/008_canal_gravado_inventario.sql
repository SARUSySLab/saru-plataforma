-- Modo inventario: o leitor cataloga os canais antes de existir amostra.
--
-- `canal_gravado.serie_id` apontava obrigatoriamente pra `serie_amostral`, o
-- que assumia que catalogar canal e materializar amostra acontecem juntos. Nao
-- acontecem: `inspecionar()` le so o cabecalho, e e ele que responde a pergunta
-- que importa primeiro, "o que este arquivo tem dentro".
--
-- Nulo aqui significa canal catalogado com amostra ainda nao materializada.
alter table canal_gravado alter column serie_id drop not null;

comment on column canal_gravado.serie_id is
    'Serie amostral da camada bruta onde os valores nativos moram. Nulo '
    'enquanto o canal foi so catalogado por inspecionar() e a amostra nao foi '
    'escrita. Deixa de ser nulo quando o leitor passar a suportar ler().';

-- A unidade que o mapa espera contra a unidade que o arquivo declara.
--
-- Nao e refinamento: e a doenca que o cabecalho do aliases.yaml do saru-app
-- documenta, sete perfis emitindo `g` onde o dominio comparava contra m/s2, e
-- o caso vivo esta no acervo. Nos 22 arquivos ACC do lote .ld, os canais
-- G_LAT e G_LON NAO sao GPS: sao aceleracao lateral e longitudinal em m/s2. O
-- nome sugere coordenada e a unidade no byte +72 desmente. Sem esta coluna, um
-- mapeamento que confunda os dois passa em silencio, que e o B2 de novo.
alter table canal_gravado
    add column unidade_divergente boolean not null default false;

comment on column canal_gravado.unidade_divergente is
    'true quando unidade_declarada do arquivo diverge da unidade_entrada que o '
    'mapeamento_canal espera. Divergencia nao bloqueia a ingestao, fica '
    'marcada pra quem for confiar no numero saber que tem que olhar.';
