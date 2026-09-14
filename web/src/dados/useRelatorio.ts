import { useRequisicao } from "./requisicao";
import { obterRelatorio } from "../services/relatorio";
import type { Relatorio } from "../types/contract";
import type { Referencia } from "../state/selection";

/**
 * O relatorio do par (volta, referencia) em escopo.
 *
 * Refaz a busca ao trocar a selecao porque as perdas sao calculadas contra o
 * par NO SERVIDOR. Isso e round-trip a cada troca de volta, e e proposital: a
 * alternativa seria o front recalcular perda, que e exatamente a linha que a
 * PoC nao cruza (o backend nao calcula nada na camada HTTP, e o front nao
 * calcula nada que o pipeline ja calculou).
 */
export function useRelatorio(
  gravacaoId: string | null,
  volta: number | null,
  referencia: Referencia | null,
  /** Gravacao da referencia, quando a comparacao atravessa arquivos. */
  refGravacaoId?: string | null,
) {
  return useRequisicao<Relatorio>(
    () => obterRelatorio(gravacaoId as string, volta, referencia, refGravacaoId),
    [gravacaoId, volta, referencia, refGravacaoId],
    gravacaoId !== null,
  );
}
