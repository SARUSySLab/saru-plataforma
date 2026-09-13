// Contrato de saida da etapa 7 do pipeline (relatorio) mais os tipos de
// leitura dos blocos de contexto e de box. Os 6 linhas do funil (N0, N1, N2,
// N3, Contexto, Box) e os blocos de cada uma, na ordem do plano. O backend em
// Python emite este shape; o front nao inventa campo. Quando um bloco nao tem
// dado, ele DECLARA por que: degradacao silenciosa e a doenca do B2.
//
// Nota do piloto (bloco 2) saiu do nucleo (decisao 12, dois votos contra). As
// quatro componentes que a alimentavam nao morrem: viram atributos de
// pilotagem no trecho onde a perda acontece, dentro do bloco 9 (PerdaPorTrecho).

export type MotivoDegradacao =
  | "sem_gps"
  | "sem_venue"
  | "sem_catalogo_de_curva"
  | "sem_setor"
  | "sem_contexto_pneu"
  | "sem_contexto_sessao"
  | "sem_canal_combustivel"
  | "somente_inventario";

export type Degradado = { disponivel: false; motivo: MotivoDegradacao; texto: string };
export type Disponivel<T> = { disponivel: true } & T;
export type Talvez<T> = Disponivel<T> | Degradado;

/** Bloco 1. A guarda do B1 vive aqui: ideal nunca pode passar a melhor. */
export interface MelhorVolta {
  melhor_volta_s: number;
  melhor_volta_n: number;
  volta_ideal_s: number | null;
  margem_para_ideal_s: number | null;
  voltas_validas: number;
  voltas_totais: number;
  /** true quando a soma dos melhores setores violaria ideal <= melhor. */
  ideal_suprimida: boolean;
}

/**
 * Tempo por fase dentro de um trecho de curva (decisao 4, feedback do
 * engenheiro item 4). Fase e subtipo de segmento no banco, nao campo
 * especial: aqui e so o tempo de cada fase, sem fase "vencedora". Perder a
 * entrada pra ganhar a saida e decisao valida, e o agregado por curva
 * escondia isso, motivo pelo qual "dominante" foi removido do contrato.
 */
export interface TempoPorFase {
  entrada_s: number;
  meio_s: number;
  saida_s: number;
  /**
   * true quando o piloto perdeu na entrada e ganhou na saida. E o caso que o
   * engenheiro nomeou (o S do Senna) e o motivo de a fase existir: o agregado
   * por curva se anula e manda corrigir o que foi feito de proposito. Vem do
   * backend em vez de ser derivado na tela pra os dois nao discordarem sobre o
   * limiar do que conta como troca.
   */
  troca_de_fase: boolean;
}

/**
 * A ressalva que invalida (ou relativiza) o insight (decisao 7). Campo
 * estruturado, nunca string solta, pra o front sempre poder renderizar a
 * condicao junto do numero. Ex.: "ganho previsto de 3 decimos na curva 1,
 * porem o pneu tinha X voltas a mais na referencia".
 */
export interface Ressalva {
  fator: "pneu" | "temperatura_pista" | "temperatura_ar" | "vento" | "outro";
  /** Texto pronto pra tela, ja com o numero embutido quando houver. */
  descricao: string;
  /** true quando o trecho de referencia difere do trecho analisado nesse fator. */
  referencia_diverge: boolean;
}

/** Um numero do trecho ao lado do mesmo numero na referencia. */
export interface MedidaComparada {
  valor: number | null;
  referencia: number | null;
  unidade: string;
  /**
   * false quando a medida nao faz sentido no trecho (ex.: pico de frenagem
   * num trecho de acelerador). Nao aplicavel e diferente de zero, e o front
   * declara em vez de desenhar barra vazia.
   */
  aplicavel: boolean;
}

/**
 * As quatro componentes que alimentavam a Nota do Piloto (removida, decisao
 * 12). Continuam calculadas e agora saem EM UNIDADE, com a referencia ao
 * lado, nunca como placar de 0 a 100.
 *
 * O placar foi testado no prototipo e estava quebrado por construcao: o ritmo
 * era normalizado pelo tamanho da janela e saturava em 0 em qualquer curva com
 * perda; a frenagem zerava em trecho sem freio, que nao e nota baixa; e o uso
 * do grip batia em 100 em toda curva, porque dentro de curva o envelope esta
 * sempre carregado. E a mesma doenca do numero sintetico que o engenheiro
 * reprovou, so que escondida em quatro numeros em vez de um.
 */
export interface AtributosPilotagem {
  /** Tempo gasto no trecho, contra o mesmo trecho na referencia. */
  tempo_no_trecho: MedidaComparada;
  /** Desvio do tempo DESTE trecho entre as voltas validas: diz se a perda e erro pontual ou padrao. */
  repeticao_entre_voltas_s: number | null;
  pico_frenagem: MedidaComparada;
  pico_envelope_grip: MedidaComparada;
}

/** Fonte unica dos blocos 3 (top 3, N0) e 9 (lista completa, N2). */
export interface PerdaPorTrecho {
  trecho_id: string;
  rotulo: string;
  modo: "curva" | "micro_setor";
  s_inicio_m: number;
  s_fim_m: number;
  perda_s: number;
  /** So disponivel em modo "curva" com fases catalogadas (motivo: sem_catalogo_de_curva). */
  tempo_por_fase: Talvez<TempoPorFase>;
  /** null quando nao ha condicao conhecida que relativize o insight. */
  ressalva: Ressalva | null;
  pilotagem: Talvez<AtributosPilotagem>;
}

export interface VoltaResumo {
  n: number;
  tempo_s: number;
  setores_s: (number | null)[];
  v_max_kmh: number | null;
  /** Contra a REFERENCIA em escopo, nao contra a melhor: a comparacao e global e o usuario a escolhe. */
  delta_referencia_s: number;
  valida: boolean;
  motivo_invalida: string | null;
  /** Bloco 14 por volta, e metrica do bloco 5. null quando nao ha canal de combustivel. */
  litros: number | null;
  /** Metrica do bloco 5. */
  acelerador_pleno_pct: number | null;
  /** Espinha operacional (decisao 16). null em arquivo solto: `bateria_id` e anulavel. */
  bateria: { id: string; rotulo: string } | null;
  /** Voltas de uso do pneu nesta volta, quando ha contexto. Alimenta a ressalva do insight. */
  voltas_pneu: number | null;
}

export interface Canal {
  id: string;
  rotulo: string;
  unidade: string;
  /** Ponteiro pro Parquet. O front busca sob demanda, nao vem no JSON. */
  uri: string;
  frequencia_hz: number;
  n_amostras: number;
}

/**
 * O que o endpoint de amostra devolve quando o front pede uma volta. Fica
 * fora do Relatorio de proposito: o relatorio e leve e cabe numa resposta, a
 * amostra e pesada e vem sob demanda, uma serie por volta.
 *
 * `distancia_m` e a grade comum: todas as voltas caem nela, e e o que
 * permite sobrepor duas series e integrar delta entre elas sem reamostrar no
 * cliente.
 */
export interface SerieAmostras {
  volta: number | "media";
  distancia_m: number[];
  /** canal_id -> valores, um por ponto de `distancia_m`. */
  canais: Record<string, number[]>;
}

/**
 * Bloco 14. Media de litros por volta excluindo a melhor e a pior volta
 * (decisao 8, conta literal do engenheiro). Dois recortes: etapa inteira e
 * bateria em escopo.
 */
export interface MediaConsumo {
  litros_por_volta: number;
  voltas_consideradas: number;
}

export interface ConsumoCombustivel {
  media_etapa: Talvez<MediaConsumo>;
  media_bateria: Talvez<MediaConsumo>;
}

/**
 * Bloco 15, forma de LEITURA. Contexto de sessao mora na tabela `contexto`
 * com dono polimorfico (bateria_id OU gravacao_id, decisao 16); aqui e so o
 * que ja foi capturado, pra exibir na gaveta "Contexto". A CAPTURA (o
 * formulario que roda no upload, decisoes 5 e 6) fica em types/ingestao.ts,
 * ver comentario de decisao pendente la.
 */
export interface ContextoPneu {
  estado: "novo" | "usado";
  voltas_rodadas: number | null;
  composto: string | null;
}

export interface ContextoSessao {
  pneu: Talvez<ContextoPneu>;
  temperatura_ar_c: number | null;
  temperatura_pista_c: number | null;
  vento_kmh: number | null;
  horario: string | null;
  notas_piloto: string | null;
  notas_engenheiro: string | null;
  /** De onde veio o registro: bateria (espinha operacional) ou direto na gravacao (arquivo solto). */
  origem: "bateria" | "gravacao";
}

/**
 * Bloco de captura (excecao 3e do E-UC-01, issue #2). Diz se algum arquivo do
 * bundle chegou a virar amostra, ou se a gravacao entrou so como inventario.
 *
 * Existe porque `aim_gpk` e `aim_rrk` tem leitor de INVENTARIO: leem cabecalho
 * e contagem de registros e nao decodificam canal (PIL-RN-11). A ingestao ja
 * marcava isso com `status = 'parcial'`, e o piloto nao via em lugar nenhum: o
 * relatorio saia sem os blocos, sem dizer por que. Bloco vazio sem motivo e a
 * doenca do B2, e aqui ela tinha uma fonte a mais.
 *
 * Degradado com motivo `somente_inventario` quando NENHUM arquivo da captura
 * materializou serie. O texto nomeia os formatos que entraram: o motivo diz a
 * classe do problema, o texto diz qual arquivo do piloto o causou.
 */
export interface AmostraDaCaptura {
  /** Arquivos do bundle, um por `arquivo_bruto` desta gravacao. */
  arquivos_lidos: number;
  /** Desses, quantos materializaram serie de amostra. Nunca zero neste ramo. */
  arquivos_com_amostra: number;
}

export interface Relatorio {
  gravacao_id: string;
  piloto: string | null;
  layout: { id: string; nome: string; comprimento_m: number } | null;
  /** Como a pista foi resolvida. Nunca "default silencioso" (fix do B2). */
  resolucao_pista: "alias" | "gps" | "perguntado" | "nao_resolvida";
  /** Se a captura virou amostra ou entrou so como inventario (excecao 3e). */
  amostra_da_captura: Talvez<AmostraDaCaptura>;

  n0: { melhor_volta: MelhorVolta; perdas_top3: Talvez<{ itens: PerdaPorTrecho[] }> };
  n1: { voltas: VoltaResumo[]; consumo: ConsumoCombustivel };
  /** Curvas catalogadas do layout, quando ha. Serve o mapa (bloco 8) e o eixo do traco. */
  trechos: Talvez<{ itens: { id: string; rotulo: string; s_inicio_m: number; s_fim_m: number; apex_m: number }[] }>;
  /** Tracado da pista para o bloco 8. Ausente quando nao ha coordenada (fix do B2). */
  tracado: Talvez<{ pontos: { x: number; y: number; s_m: number }[] }>;
  /**
   * Os DOIS recortes vem juntos. Quem decide qual esta disponivel e o dado
   * (curva exige catalogo de layout; micro-setor so exige distancia), e o
   * usuario alterna entre os que existem sem round-trip. Emitir um so
   * obrigaria o front a pedir de novo pra trocar de modo, e o modo e leitura,
   * nao consulta.
   */
  n2: {
    por_curva: Talvez<{ itens: PerdaPorTrecho[] }>;
    por_micro_setor: Talvez<{ itens: PerdaPorTrecho[] }>;
  };
  n3: { canais: Canal[] };
  contexto: { setup: Record<string, string | number> | null; sessao: Talvez<ContextoSessao> };
}

// --- Ferramentas de box (blocos 16 e 17) ---------------------------------
// Fora do funil de proposito (decisoes 9 e 10): nao leem telemetria, entao
// nao vem no Relatorio da etapa 7. Vivem numa area de box separada,
// acessivel de qualquer nivel, e nao competem por atencao com o loop
// principal (arquivo entra > insight sai).

/** Bloco 16. Entrada da calculadora de pressao a frio. */
export interface EntradaPressaoFria {
  temperatura_ambiente_c: number;
  temperatura_pista_c: number;
  pressao_alvo_quente_psi: number;
}

/**
 * Saida da calculadora de pressao a frio. O engenheiro relativizou a propria
 * precisao ("na Porsche nao e assim"), entao o modelo e a margem sao
 * obrigatorios na saida, nao rodape: e a mesma regra que a nota do piloto
 * violou, so que aplicada certo desta vez.
 */
export interface SaidaPressaoFria {
  pressao_fria_psi: number;
  modelo: string;
  margem_psi: number;
}

/** Bloco 17. Um ponto da previsao horaria de 2 dias. */
export interface PontoPrevisao {
  horario: string;
  temperatura_c: number;
  condicao: string | null;
  /** Chance de chuva em 0 a 100. `null` quando a fonte nao entrega o campo:
   *  ausencia de dado nao vira zero, que seria afirmar tempo seco. */
  chuva_prob?: number | null;
}

export interface TempoComPrevisao {
  temperatura_atual_c: number;
  previsao_horaria: PontoPrevisao[];
}
