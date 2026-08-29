import { useEffect, useState } from "react";
import type { SerieAmostras } from "../types/contract";
import { obterAmostras } from "../services/gravacoes";

/**
 * Carrega as duas series em escopo: a volta e a referencia. Vem sob demanda,
 * uma requisicao por volta, porque amostra e pesada; o relatorio e leve e ja
 * veio inteiro.
 *
 * Devolve `null` enquanto o par nao esta completo (carregando OU falhou). Os
 * blocos que dependem de amostra ja tratam esse `null` desde a fixture, entao
 * a troca de origem nao muda a tela: o que muda e que agora ha rede no meio, e
 * `erro` diz por que o par nao veio em vez de a tela ficar vazia calada.
 */
export function useAmostras(
  gravacaoId: string | null,
  volta: number,
  referencia: number | "media",
  /** Gravacao da referencia, quando o lado B vem de OUTRO arquivo. */
  refGravacaoId?: string | null,
) {
  const [par, setPar] = useState<{ a: SerieAmostras; b: SerieAmostras } | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (!gravacaoId) return;
    let vivo = true;
    // a referencia pode vir de outra gravacao: e o que permite comparar dia
    // com dia em vez de so voltas do mesmo arquivo
    const ondeB = refGravacaoId || gravacaoId;
    Promise.all([obterAmostras(gravacaoId, volta), obterAmostras(ondeB, referencia)])
      .then(([a, b]) => {
        if (!vivo) return;
        setPar({ a, b });
        setErro(null);
      })
      .catch((e: unknown) => {
        if (!vivo) return;
        setPar(null);
        setErro(e instanceof Error ? e.message : "falha ao buscar amostras");
      });
    return () => {
      vivo = false;
    };
  }, [gravacaoId, volta, referencia, refGravacaoId]);

  return { par, erro };
}

/** Delta de tempo entre duas series, ponto a ponto e acumulado. */
export function calcularDelta(a: SerieAmostras, b: SerieAmostras) {
  const d = a.distancia_m;
  const va = a.canais.velocidade;
  const vb = b.canais.velocidade;
  const local: number[] = [];
  const acumulado: number[] = [];
  let soma = 0;
  // Piso de velocidade pro integrando 1/v: carro PARADO na grade (velocidade
  // zero em pit stop, bandeira, fim de in-lap) faz passo/v estourar Infinity
  // e contaminar o acumulado inteiro (medido em produção em 29/08, volta com
  // v mín 0.0 mostrava "+Infinity s"). 3 km/h é andar a pé: abaixo disso o
  // delta de tempo naquele passo deixa de ser comparação de pilotagem e vira
  // artefato, então o piso limita o integrando sem mover o sinal em pista.
  const PISO_KMH = 3;
  for (let i = 0; i < d.length; i++) {
    const passo = (d[i + 1] ?? d[i]) - d[i];
    const va_i = Math.max(va[i] ?? 0, PISO_KMH);
    const vb_i = Math.max(vb[i] ?? 0, PISO_KMH);
    // velocidade vem em km/h no contrato; tempo pede m/s
    const q = passo > 0 ? passo / (va_i / 3.6) - passo / (vb_i / 3.6) : 0;
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
