import { useRequisicao } from "./requisicao";
import { historicoContexto, type Dono, type RegistroContexto } from "../services/operacao";

/**
 * O historico de contexto do dono em escopo, mais novo primeiro.
 *
 * Contexto e append-only de proposito: temperatura de pista as 9h e as 14h sao
 * dois fatos, nao uma correcao do outro. Quem quer "o atual" pega `[0]`, e quem
 * quer mostrar o que mudou pega a lista.
 */
export function useContexto(dono: Dono, alvoId: string | null) {
  return useRequisicao<RegistroContexto[]>(
    () => historicoContexto(dono, alvoId as string),
    [dono, alvoId],
    alvoId !== null,
  );
}
