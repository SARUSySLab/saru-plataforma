import { create } from "zustand";

// Store propria do Sarue, fora de state/selection.ts de proposito: o pedido
// e poder abrir o painel de qualquer lugar do app (um botao no Rail, um link
// num bloco, etc), sem acoplar essa decisao ao estado de selecao do funil.

const CHAVE_LARGURA = "saru-sarue-ampliado";

/** Le a preferencia de largura salva. Modo privado/sem storage cai no padrao. */
function larguraSalva(): boolean {
  try {
    return localStorage.getItem(CHAVE_LARGURA) === "1";
  } catch {
    return false;
  }
}

interface EstadoSarue {
  /** Painel aberto ou fechado. */
  aberto: boolean;
  /**
   * Painel ampliado (quase o dobro da largura padrao). Fica em localStorage
   * porque quem ampliou uma vez normalmente quer assim sempre; refazer o
   * gesto a cada visita e atrito a toa (mesmo raciocinio da Lana).
   */
  ampliado: boolean;
  abrir: () => void;
  fechar: () => void;
  alternar: () => void;
  alternarLargura: () => void;
}

export const useSarue = create<EstadoSarue>((set, get) => ({
  aberto: false,
  ampliado: larguraSalva(),

  abrir: () => set({ aberto: true }),
  fechar: () => set({ aberto: false }),
  alternar: () => set({ aberto: !get().aberto }),

  alternarLargura: () => {
    const novo = !get().ampliado;
    set({ ampliado: novo });
    try {
      localStorage.setItem(CHAVE_LARGURA, novo ? "1" : "0");
    } catch {
      // modo privado: a escolha so vale pra esta sessao de aba
    }
  },
}));
