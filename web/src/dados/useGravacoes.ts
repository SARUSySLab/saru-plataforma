import { useRequisicao } from "./requisicao";
import { listarGravacoes, type Gravacao } from "../services/gravacoes";
import { useSelecao } from "../state/selection";

/**
 * O catalogo. `comVolta` filtra as que ja renderiam relatorio, que e o que a
 * tela de escolha quer; o upload quer o catalogo inteiro, pra ver a recem
 * enviada aparecer com zero volta e o pipeline andando.
 */
export function useGravacoes(comVolta = false) {
  // `versaoCatalogo` nas deps: upload concluido, vinculo e exclusao invalidam
  // TODAS as instancias deste hook, nao so a da tela que fez a mutacao. Sem
  // isso a casca ficava com o catalogo do primeiro fetch e a gravacao nova
  // "nao existia" ate o F5 (a travada de 29/08).
  const versao = useSelecao((e) => e.versaoCatalogo);
  return useRequisicao<Gravacao[]>(() => listarGravacoes(comVolta), [comVolta, versao]);
}
