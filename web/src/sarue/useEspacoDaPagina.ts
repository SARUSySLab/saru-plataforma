import { useEffect } from "react";
import type { RefObject } from "react";

// Portado de useLana.ts (ajustarEspacoDaPagina) + LanaSidebar.vue (barrarArrasto).
//
// A largura vai pro CSS como --sarue-largura em vez de virar uma constante
// duplicada: ela e um clamp() que depende da viewport e ainda muda quando o
// painel amplia. Ler do elemento renderizado e a unica fonte que nao sai do
// ar quando o CSS muda. O conteudo por baixo (App.tsx, fora do escopo desta
// tarefa) pode usar essa property pra ceder espaco, se um dia quiser.
export function useEspacoDaPagina(
  painelRef: RefObject<HTMLElement | null>,
  aberto: boolean,
  ampliado: boolean,
) {
  useEffect(() => {
    const html = document.documentElement;

    function ajustar() {
      if (!aberto) {
        html.classList.remove("sarue-aberto");
        return;
      }
      const painel = painelRef.current;
      if (!painel) return;
      html.style.setProperty("--sarue-largura", `${Math.round(painel.getBoundingClientRect().width)}px`);
      html.classList.add("sarue-aberto");
    }

    ajustar();
    window.addEventListener("resize", ajustar);
    return () => {
      window.removeEventListener("resize", ajustar);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aberto, ampliado]);

  useEffect(
    () => () => {
      // limpeza final: se o painel desmontar aberto, nao deixa a classe presa
      document.documentElement.classList.remove("sarue-aberto");
    },
    [],
  );
}

/**
 * Trava a rolagem da pagina atras do painel, no celular (mesmo raciocinio da
 * Lana: o overflow:hidden do body nao segura o Safari do iOS, que arrasta o
 * site inteiro por baixo do dedo que pega o backdrop ou o cabecalho).
 *
 * O listener precisa ser nao passivo: preventDefault em listener passivo e
 * ignorado, e e justamente ele que segura o gesto.
 */
export function useTravaDeArrasto(aberto: boolean, seletorLivre: string) {
  useEffect(() => {
    function barrar(e: TouchEvent) {
      if (!aberto) return;
      if (window.innerWidth > 940) return;
      const alvo = e.target as HTMLElement | null;
      if (alvo?.closest(seletorLivre)) return;
      e.preventDefault();
    }
    document.addEventListener("touchmove", barrar, { passive: false });
    return () => document.removeEventListener("touchmove", barrar);
  }, [aberto, seletorLivre]);
}
