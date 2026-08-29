import { create } from "zustand";

// O estado de selecao compartilhado do funil, e nada mais.
// Espelha o objeto S do prototipo SARU Analyzer: uma selecao num nivel e o
// escopo do nivel seguinte. Deliberadamente NAO guarda dado do servidor: o
// SaDashboard.tsx do saru-app misturou os dois e virou 685 linhas com ~20
// useState. Widget recebe dado por prop, nunca puxa da store.
//
// ESCOPO GLOBAL (validado no prototipo em 29/08). `volta` e `compara` valem
// para o dashboard inteiro. Antes o traco no tempo tinha o proprio par de
// series (refA/refB) enquanto o resto da tela media contra a melhor volta sem
// ninguem poder mudar: duas verdades na mesma tela, e o usuario sem saber
// contra o que estava olhando. Agora existe um seletor so, na barra de escopo.

/**
 * "media" e a media das voltas validas; um numero e a volta N. `null` e
 * "ainda nao escolhida": quem resolve o default e a tela, a partir do
 * relatorio (a melhor propria), porque a store nao conhece dado de servidor.
 */
export type Referencia = number | "media";

/**
 * As paginas do funil. A ordem e a das tres perguntas que o engenheiro
 * nomeou: onde perdi, se estou melhorando, quanto gastei.
 */
export type PaginaId = "perdas" | "melhor_volta" | "mapa" | "evolucao" | "consumo" | "voltas" | "traco";

// Contexto (gaveta lateral) e Box (ferramentas) ficam fora do funil vertical
// de proposito: nao sao um "nivel" de zoom, sao acessiveis de qualquer nivel
// (plano, tabela do funil de zoom). O estado de qual gaveta/ferramenta esta
// aberta ainda e selecao pura, nao dado de servidor, entao mora aqui.
export type Vista = { tipo: "geral" } | { tipo: "pagina"; id: PaginaId } | { tipo: "box" };

export type MapMode = "speed" | "brake" | "gear" | "delta";
export type LossMode = "corner" | "micro";
export type RunMetric = "lapTime" | "vMax" | "fuel" | "fullThrottle";
/** Acumulado e a integral da diferenca; instantaneo e a derivada dela. */
export type DeltaMode = "acumulado" | "instantaneo";

/** Intervalo marcado por arraste no traco, em distancia. */
export interface Intervalo {
  s_inicio_m: number;
  s_fim_m: number;
}

interface Selecao {
  // --- escopo, valido para a tela inteira ---
  volta: number | null;
  compara: Referencia | null;
  /** id do trecho (curva ou micro-setor). Entra pelo clique no mapa ou na lista. */
  trecho: string | null;
  /** Intervalo livre marcado no traco. Independe do trecho catalogado. */
  intervalo: Intervalo | null;
  cursor_m: number | null;

  // --- modo de leitura de cada bloco ---
  mapMode: MapMode;
  lossMode: LossMode;
  runMetric: RunMetric;
  deltaMode: DeltaMode;

  // --- navegacao ---
  vista: Vista;
  /** Gaveta de contexto da bateria (bloco 15) aberta ou nao. */
  contextoAberto: boolean;
  /** Gaveta da ficha de setup (bloco 13) aberta ou nao. */
  setupAberto: boolean;

  setVolta: (n: number | null) => void;
  setCompara: (r: Referencia) => void;
  setTrecho: (id: string | null) => void;
  setIntervalo: (i: Intervalo | null) => void;
  setCursor: (m: number | null) => void;
  setMapMode: (m: MapMode) => void;
  setLossMode: (m: LossMode) => void;
  setRunMetric: (m: RunMetric) => void;
  setDeltaMode: (m: DeltaMode) => void;
  irPara: (v: Vista) => void;
  setContextoAberto: (aberto: boolean) => void;
  setSetupAberto: (aberto: boolean) => void;
}

export const useSelecao = create<Selecao>((set) => ({
  volta: null,
  compara: null,
  trecho: null,
  intervalo: null,
  cursor_m: null,
  mapMode: "speed",
  lossMode: "corner",
  runMetric: "lapTime",
  deltaMode: "acumulado",
  vista: { tipo: "geral" },
  contextoAberto: false,
  setupAberto: false,

  // Escolher volta reabre o N2/N3 nela: o escopo antigo nao sobrevive.
  setVolta: (volta) => set({ volta, trecho: null, intervalo: null, cursor_m: null }),
  // Trocar a referencia nao muda o zoom, muda contra o que tudo e medido.
  setCompara: (compara) => set({ compara }),
  setTrecho: (trecho) => set({ trecho, intervalo: null, cursor_m: null }),
  setIntervalo: (intervalo) => set({ intervalo }),
  setCursor: (cursor_m) => set({ cursor_m }),
  setMapMode: (mapMode) => set({ mapMode }),
  // Trocar de modo limpa o trecho: id de curva nao vale como id de
  // micro-setor. Quem decide se o modo por curva existe e o dado
  // (resolucao_pista no relatorio), nao o usuario.
  setLossMode: (lossMode) => set({ lossMode, trecho: null }),
  setRunMetric: (runMetric) => set({ runMetric }),
  setDeltaMode: (deltaMode) => set({ deltaMode }),
  irPara: (vista) => set({ vista }),
  setContextoAberto: (contextoAberto) => set({ contextoAberto }),
  setSetupAberto: (setupAberto) => set({ setupAberto }),
}));
