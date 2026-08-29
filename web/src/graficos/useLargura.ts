import { useEffect, useState, type RefObject } from "react";

/**
 * Largura real do container, observada.
 *
 * Ler `ref.current.clientWidth` durante o render parece mais simples e tem
 * dois defeitos. No primeiro render o ref ainda e null, entao o grafico nasce
 * com a largura de reserva e so corrige se alguma outra coisa causar um novo
 * render. E redimensionar a janela, ou recolher o painel lateral, nao dispara
 * render nenhum: o viewBox fica com a largura antiga e o SVG estica, o que
 * deforma texto e traco na horizontal.
 *
 * Com ResizeObserver a largura vira estado e o desenho acompanha a caixa.
 */
export function useLargura(ref: RefObject<HTMLElement | null>, reserva: number) {
  const [largura, setLargura] = useState(reserva);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const medir = () => {
      const w = el.clientWidth;
      if (w > 240) setLargura(Math.round(w));
    };
    medir();
    const obs = new ResizeObserver(medir);
    obs.observe(el);
    return () => obs.disconnect();
  }, [ref]);

  return largura;
}
