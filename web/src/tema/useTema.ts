import { useEffect } from "react";
import { create } from "zustand";

// DOIS estados, por pedido de 29/08: "seguir o sistema" deixou de existir como
// modo. A preferencia do SO ainda manda UMA vez, na primeira visita (e o unico
// palpite razoavel antes de o usuario clicar), mas a partir dai o tema e uma
// escolha binaria persistida:
//
//   claro    data-theme="claro"  -> mapeado pra "light" no atributo
//   escuro   data-theme="escuro" -> mapeado pra "dark"
//
// O atributo esta SEMPRE presente no <html>, entao os guardas de
// prefers-color-scheme do tokens.css nunca mais decidem sozinhos.

export type Tema = "claro" | "escuro";

const CHAVE = "saru.tema";

function aplicar(tema: Tema): void {
  document.documentElement.setAttribute("data-theme", tema === "claro" ? "light" : "dark");
}

function inicial(): Tema {
  try {
    const v = localStorage.getItem(CHAVE);
    if (v === "claro" || v === "escuro") return v;
  } catch {
    // navegacao privada, ou site data bloqueado: cai no palpite do SO
  }
  try {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
  } catch {
    return "escuro";
  }
}

interface Estado {
  tema: Tema;
  setTema: (t: Tema) => void;
}

export const useTema = create<Estado>((set) => ({
  tema: inicial(),
  setTema: (tema) => {
    aplicar(tema);
    try {
      localStorage.setItem(CHAVE, tema);
    } catch {
      // preferencia nao persistir e aceitavel; ignorar a escolha nao e
    }
    set({ tema });
  },
}));

/** Aplica o tema guardado no primeiro render, antes de qualquer tela. */
export function useAplicarTema(): void {
  const tema = useTema((e) => e.tema);
  useEffect(() => aplicar(tema), [tema]);
}

/**
 * O tema efetivo pra escolher asset (a logo, o mascote). Com o modo "sistema"
 * extinto, e o proprio tema; o nome fica pra nao mexer em quem consome.
 */
export function useTemaEfetivo(): Tema {
  return useTema((e) => e.tema);
}
