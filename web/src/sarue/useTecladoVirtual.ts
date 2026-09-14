import { useCallback, useEffect, useRef, useState } from "react";

// Portado de useLana.ts / LanaSidebar.vue. Duas coisas diferentes acontecem
// aqui, e confundi-las foi a origem de um bug la:
//
// 1. ONDE o painel termina. No iOS o teclado nao encolhe a janela: um painel
//    ancorado em bottom:0 fica atras dele. Quem sabe a area REALMENTE visivel
//    e a visualViewport, e e dela que sai o quanto o painel precisa subir.
//
// 2. SE o teclado esta aberto. Medir isso pela mesma conta nao funciona: no
//    Chrome do Android o layout viewport encolhe JUNTO com o teclado, entao
//    innerHeight ja vem menor e a diferenca da zero. O sinal confiavel nos
//    dois mundos e o foco no campo de escrever, em aparelho de toque.
//
// As duas medidas saem como custom properties no <html> (--sarue-oculto e
// --sarue-visivel) pro CSS usar sem precisar de outro state React por frame.

function ehAparelhoDeToque() {
  return window.matchMedia("(pointer: coarse)").matches;
}

export function useTecladoVirtual() {
  const [tecladoAberto, setTecladoAberto] = useState(false);
  const campoFocadoRef = useRef(false);

  const ajustar = useCallback(() => {
    const raiz = document.documentElement;
    const vv = window.visualViewport;

    const oculto = vv ? Math.max(0, window.innerHeight - vv.height - vv.offsetTop) : 0;
    const visivel = vv ? vv.height : window.innerHeight;

    raiz.style.setProperty("--sarue-oculto", `${Math.round(oculto)}px`);
    raiz.style.setProperty("--sarue-visivel", `${Math.round(visivel)}px`);

    // 120px separa um teclado de uma barra de endereco que so recolheu.
    const comTeclado = (campoFocadoRef.current && ehAparelhoDeToque()) || oculto > 120;
    setTecladoAberto((atual) => (atual === comTeclado ? atual : comTeclado));
  }, []);

  useEffect(() => {
    window.addEventListener("orientationchange", ajustar);
    const vv = window.visualViewport;
    vv?.addEventListener("resize", ajustar);
    vv?.addEventListener("scroll", ajustar);
    ajustar();
    return () => {
      window.removeEventListener("orientationchange", ajustar);
      vv?.removeEventListener("resize", ajustar);
      vv?.removeEventListener("scroll", ajustar);
    };
  }, [ajustar]);

  const aoFocarCampo = useCallback(() => {
    campoFocadoRef.current = true;
    ajustar();
  }, [ajustar]);

  const aoDesfocarCampo = useCallback(() => {
    campoFocadoRef.current = false;
    // O viewport leva alguns quadros pra voltar ao tamanho cheio depois que o
    // teclado desce; medir na hora do blur pegaria a altura antiga.
    ajustar();
    setTimeout(ajustar, 260);
  }, [ajustar]);

  return { tecladoAberto, aoFocarCampo, aoDesfocarCampo, ehAparelhoDeToque };
}
