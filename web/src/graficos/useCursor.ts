import { useState } from "react";

/**
 * Cursor de grafico: qual ponto o mouse esta apontando e onde ele esta em
 * pixels do container.
 *
 * Mora em ESTADO, e nao em ref. A tentacao e usar ref para nao re-renderizar
 * a cada pixel, mas o valor precisa aparecer no render (a linha do cursor e o
 * card saem dele), e ler `ref.current` durante o render e justamente o que o
 * linter proibe: nada garante que o React redesenhou depois da ultima
 * escrita, entao o desenho pode ficar um quadro atras do ponteiro.
 *
 * Ref continua sendo o lugar certo para estado de GESTO, que o handler le e
 * escreve entre renders sem precisar aparecer na tela por si so.
 */
export function useCursor<T>() {
  const [atual, definir] = useState<({ xPx: number; yPx: number } & T) | null>(null);
  return { atual, definir };
}
