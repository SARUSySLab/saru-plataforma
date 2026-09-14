import type { VoltaResumo } from "../types/contract";
import type { Referencia } from "../state/selection";

/**
 * A volta analisada default, com a regra 1.12 (29/08): analisada e referencia
 * NUNCA sao a mesma volta. O default continua sendo a ultima valida; quando
 * ela colide com a referencia (tipicamente porque a ultima valida E a melhor,
 * que e o default da referencia), a analisada cai pra segunda melhor valida.
 *
 * Mora num helper porque a MESMA conta roda na casca (App) e na barra de
 * escopo: divergir aqui seria a tela medir uma volta e o seletor mostrar outra.
 */
export function voltaEmEscopo(
  voltas: VoltaResumo[],
  volta: number | null,
  refAtiva: Referencia,
): number {
  if (volta != null) return volta;
  const validas = voltas.filter((v) => v.valida);
  const ultima = validas.at(-1)?.n ?? voltas[0].n;
  if (refAtiva === "media" || refAtiva !== ultima) return ultima;
  const ordenadas = [...validas].sort((a, b) => a.tempo_s - b.tempo_s);
  return ordenadas.find((v) => v.n !== refAtiva)?.n ?? ultima;
}
