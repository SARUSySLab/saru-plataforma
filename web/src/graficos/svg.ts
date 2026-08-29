// Helpers de grafico. SVG a mao, e nao recharts, por um motivo concreto: o
// que esta tela desenha (tracado de pista colorido por canal, faixa de perdas
// posicionada por distancia real, traco de 4 canais com selecao por arraste)
// nao e grafico de biblioteca, e desenho de dominio. Recharts continua na
// stack para o que for grafico comum; forcar tudo nele custaria mais codigo
// de contorno do que o desenho direto.

/** Escala linear com dominio e imagem explicitos. */
export const escala = (d0: number, d1: number, r0: number, r1: number) => (v: number) =>
  r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);

export const caminho = (pts: [number, number][]) =>
  pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");

// (grade fica no componente: JSX nao mora em .ts)

/** Le um token do tema em runtime: a cor muda com claro e escuro. */
export const token = (n: string) =>
  typeof window === "undefined" ? "" : getComputedStyle(document.documentElement).getPropertyValue(n).trim();

/** Sequencial de uma matiz, claro para escuro. */
export function rampa(t: number) {
  const c = [token("--seq-1"), token("--seq-2"), token("--seq-3"), token("--seq-4"), token("--seq-5")];
  return c[Math.max(0, Math.min(4, Math.round(t * 4)))];
}

/**
 * Marcha tem 6 degraus e a rampa tem 5 paradas, entao aqui ela e interpolada
 * em vez de arredondada: com arredondamento, 3a e 4a cairiam na mesma cor e o
 * mapa mentiria sobre onde o piloto troca.
 */
export function rampaFina(t: number) {
  const c = [token("--seq-1"), token("--seq-2"), token("--seq-3"), token("--seq-4"), token("--seq-5")];
  const p = Math.max(0, Math.min(1, t)) * (c.length - 1);
  const i = Math.floor(p);
  if (i >= c.length - 1) return c[c.length - 1];
  const mistura = (a: string, b: string, f: number) => {
    const ler = (h: string) => [1, 3, 5].map((k) => parseInt(h.slice(k, k + 2), 16));
    const [r1, g1, b1] = ler(a);
    const [r2, g2, b2] = ler(b);
    const m = (x: number, y: number) => Math.round(x + (y - x) * f).toString(16).padStart(2, "0");
    return "#" + m(r1, r2) + m(g1, g2) + m(b1, b2);
  };
  return mistura(c[i], c[i + 1], p - i);
}

/** Divergente: ganho de um lado, perda do outro, neutro no meio. */
export const divergente = (t: number) =>
  t > 0.12 ? token("--d-loss") : t < -0.12 ? token("--d-gain") : token("--d-mid");

/** Largura real do container. Sem isso o viewBox estica e deforma o texto. */
export function larguraDe(el: HTMLElement | null, padrao: number) {
  const w = el?.clientWidth ?? 0;
  return w > 240 ? Math.round(w) : padrao;
}
