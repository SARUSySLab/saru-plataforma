import { useRequisicao } from "./requisicao";
import { versoesSetup, type Dono, type VersaoSetup } from "../services/operacao";

/**
 * As versoes da ficha, da mais nova pra mais velha.
 *
 * Salvar cria versao nova em vez de sobrescrever, entao `[0]` e a ficha vigente
 * e a lista inteira responde "o que mudou da bateria 2 pra 3".
 */
export function useSetup(dono: Dono, alvoId: string | null) {
  return useRequisicao<VersaoSetup[]>(
    () => versoesSetup(dono, alvoId as string),
    [dono, alvoId],
    alvoId !== null,
  );
}
