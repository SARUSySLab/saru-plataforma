import { useCallback, useEffect, useState } from "react";
import { ErroDaApi } from "../services/api";

/**
 * O estado de UMA requisicao, e nada mais.
 *
 * Existe porque o `SaDashboard.tsx` do saru-app carregava loading e erro de
 * cinco coisas diferentes em useState soltos, e a tela nao sabia dizer qual
 * das cinco tinha falhado. Aqui cada dado tem o proprio estado, e a tela
 * decide o que fazer com cada um.
 */
export interface Requisicao<T> {
  dado: T | null;
  carregando: boolean;
  /** Mensagem ja legivel. A tela nao formata erro de servidor. */
  erro: string | null;
  recarregar: () => void;
}

/**
 * `chaves` e a lista de valores que, ao mudarem, refazem a busca. E explicita
 * porque `buscar` e uma closure nova a cada render e nao serve de dependencia.
 */
export function useRequisicao<T>(
  buscar: () => Promise<T>,
  chaves: readonly unknown[],
  ativo = true,
): Requisicao<T> {
  const [dado, setDado] = useState<T | null>(null);
  const [carregando, setCarregando] = useState(ativo);
  const [erro, setErro] = useState<string | null>(null);
  const [tentativa, setTentativa] = useState(0);

  useEffect(() => {
    if (!ativo) {
      setCarregando(false);
      return;
    }
    let vivo = true;
    setCarregando(true);
    setErro(null);
    buscar()
      .then((resultado) => {
        if (!vivo) return;
        setDado(resultado);
        setCarregando(false);
      })
      .catch((e: unknown) => {
        if (!vivo) return;
        // dado anterior fica na tela quando a recarga falha: apagar a tela
        // inteira por causa de um refetch que deu 500 e perder contexto que o
        // usuario ainda consegue ler
        setErro(e instanceof ErroDaApi ? e.message : "falha inesperada ao buscar dado");
        setCarregando(false);
      });
    return () => {
      vivo = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...chaves, ativo, tentativa]);

  const recarregar = useCallback(() => setTentativa((n) => n + 1), []);
  return { dado, carregando, erro, recarregar };
}
