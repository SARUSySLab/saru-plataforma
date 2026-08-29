// Contrato de saida da etapa 7 do pipeline. Os 4 niveis e os 13 blocos do
// funil, na ordem do plano. O backend em Python emite este shape; o front nao
// inventa campo. Quando um bloco nao tem dado, ele DECLARA por que: degradacao
// silenciosa e a doenca do B2.

export type MotivoDegradacao =
  | "sem_gps"
  | "sem_venue"
  | "sem_catalogo_de_curva"
  | "sem_setor";

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

/** Bloco 2. Score sintetico: a unica coisa da tela que e opiniao, nao medida. */
export interface NotaDoPiloto {
  nota: number;
  componentes: { ritmo: number; consistencia: number; frenagem: number; grip: number };
  /** A regua declarada. Score sem regua exposta o piloto descarta como chute. */
  medida_contra: string;
}

/** Fonte unica dos blocos 3 (top 3, N0) e 9 (lista completa, N2). */
export interface PerdaPorTrecho {
  trecho_id: string;
  rotulo: string;
  modo: "curva" | "micro_setor";
  s_inicio_m: number;
  s_fim_m: number;
  perda_s: number;
  dominante: "entrada" | "apex" | "saida" | null;
}

export interface VoltaResumo {
  n: number;
  tempo_s: number;
  setores_s: (number | null)[];
  v_max_kmh: number | null;
  delta_melhor_s: number;
  valida: boolean;
  motivo_invalida: string | null;
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

export interface Relatorio {
  gravacao_id: string;
  piloto: string | null;
  layout: { id: string; nome: string; comprimento_m: number } | null;
  /** Como a pista foi resolvida. Nunca "default silencioso" (fix do B2). */
  resolucao_pista: "alias" | "gps" | "perguntado" | "nao_resolvida";

  n0: { melhor_volta: MelhorVolta; nota: NotaDoPiloto; perdas_top3: Talvez<{ itens: PerdaPorTrecho[] }> };
  n1: { voltas: VoltaResumo[] };
  n2: { perdas: Talvez<{ modo: "curva" | "micro_setor"; itens: PerdaPorTrecho[] }> };
  n3: { canais: Canal[] };
  contexto: { setup: Record<string, string | number> | null };
}
