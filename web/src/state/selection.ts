import { create } from "zustand";

// O estado de selecao compartilhado do funil, e nada mais.
// Espelha o objeto S do prototipo SARU Analyzer: uma selecao num nivel e o
// escopo do nivel seguinte. Deliberadamente NAO guarda dado do servidor: o
// SaDashboard.tsx do saru-app misturou os dois e virou 685 linhas com ~20
// useState. Widget recebe dado por prop, nunca puxa da store.

export type MapMode = "speed" | "brake" | "delta";
export type LossMode = "corner" | "micro";
export type RunMetric = "lapTime" | "vMax" | "fullThrottle";

interface Selecao {
  volta: number | null;
  trecho: string | null;
  cursor_s: number | null;
  mapMode: MapMode;
  lossMode: LossMode;
  runMetric: RunMetric;
  refA: number | null;
  refB: number | null;
  setVolta: (n: number | null) => void;
  setTrecho: (id: string | null) => void;
  setCursor: (s: number | null) => void;
  setMapMode: (m: MapMode) => void;
  setLossMode: (m: LossMode) => void;
  setRunMetric: (m: RunMetric) => void;
  setRefs: (a: number | null, b: number | null) => void;
}

export const useSelecao = create<Selecao>((set) => ({
  volta: null,
  trecho: null,
  cursor_s: null,
  mapMode: "speed",
  lossMode: "corner",
  runMetric: "lapTime",
  refA: null,
  refB: null,
  // Escolher volta reabre o N2/N3 nela: o escopo antigo nao sobrevive.
  setVolta: (volta) => set({ volta, trecho: null, cursor_s: null }),
  setTrecho: (trecho) => set({ trecho, cursor_s: null }),
  setCursor: (cursor_s) => set({ cursor_s }),
  setMapMode: (mapMode) => set({ mapMode }),
  setLossMode: (lossMode) => set({ lossMode }),
  setRunMetric: (runMetric) => set({ runMetric }),
  setRefs: (refA, refB) => set({ refA, refB }),
}));
