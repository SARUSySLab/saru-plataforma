import { useEffect, useState } from "react";
import type { SerieAmostras } from "../types/contract";
import { carregarAmostras } from "./fixture";

/**
 * Carrega as duas series em escopo: a volta e a referencia. Vem sob demanda
 * porque amostra e pesada; o relatorio e leve e ja veio. Quando existir API,
 * so `carregarAmostras` troca de origem.
 */
export function useAmostras(volta: number, referencia: number | "media") {
  const [par, setPar] = useState<{ a: SerieAmostras; b: SerieAmostras } | null>(null);

  useEffect(() => {
    let vivo = true;
    Promise.all([carregarAmostras(volta), carregarAmostras(referencia)]).then(([a, b]) => {
      if (vivo && a && b) setPar({ a, b });
    });
    return () => {
      vivo = false;
    };
  }, [volta, referencia]);

  return par;
}

/** Delta de tempo entre duas series, ponto a ponto e acumulado. */
export function calcularDelta(a: SerieAmostras, b: SerieAmostras) {
  const d = a.distancia_m;
  const va = a.canais.velocidade;
  const vb = b.canais.velocidade;
  const local: number[] = [];
  const acumulado: number[] = [];
  let soma = 0;
  for (let i = 0; i < d.length; i++) {
    const passo = (d[i + 1] ?? d[i]) - d[i];
    // velocidade vem em km/h no contrato; tempo pede m/s
    const q = passo > 0 ? passo / (va[i] / 3.6) - passo / (vb[i] / 3.6) : 0;
    soma += q;
    local.push(passo > 0 ? (q / passo) * 100 : 0); // s por 100 m
    acumulado.push(soma);
  }
  // a derivada e ruidosa por natureza: media movel de 7 pontos deixa o sinal
  // legivel sem mover o lugar onde a perda acontece
  const suave = local.map((_, k) => {
    let s = 0;
    let n = 0;
    for (let j = -3; j <= 3; j++) {
      const q = local[k + j];
      if (q !== undefined) { s += q; n++; }
    }
    return s / n;
  });
  return { local: suave, acumulado, total: soma };
}
