// O relatorio da etapa 7, no shape de `types/contract.ts`.

import { obter } from "./api";
import type { Relatorio } from "../types/contract";
import type { Referencia } from "../state/selection";

/**
 * `volta` e `referencia` viajam na query porque as perdas saem calculadas
 * contra ESTE par no servidor, nao no cliente (decisao do Lucas, 29/08).
 * Trocar a selecao na barra de escopo refaz a busca; sem isso, trocar a volta
 * na tela nao mudava as perdas e ninguem via porque o front lia fixture.
 *
 * Os dois sao opcionais: ausentes, o servidor escolhe o par (melhor volta
 * contra a media). Por isso `obter` remove `null`/`undefined` da query em vez
 * de mandar string vazia.
 */
export function obterRelatorio(
  gravacaoId: string,
  volta?: number | null,
  referencia?: Referencia | null,
  /**
   * Gravacao da referencia, quando o lado B vem de OUTRO arquivo.
   *
   * O servidor recusa com 422 se as duas gravacoes forem de pistas diferentes:
   * sem grade de distancia comum, comparar perda entre pistas produz numero
   * confiante e errado, que e a familia de bug que o B2 inaugurou.
   */
  refGravacaoId?: string | null,
): Promise<Relatorio> {
  return obter<Relatorio>(`/relatorio/${gravacaoId}`, {
    volta,
    referencia,
    ref_gravacao: refGravacaoId,
  });
}
