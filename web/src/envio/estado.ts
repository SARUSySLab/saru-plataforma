import { create } from "zustand";
import type { Gravacao } from "../services/gravacoes";

// O estado do envio mora FORA do componente.
//
// Antes ele era `useState` dentro de `EnvioDeTelemetria`, e trocar de tela
// desmontava o componente e levava junto o acompanhamento. O pipeline continua
// rodando no servidor (a recepcao e sincrona, as etapas 2 a 6 sao background
// task), mas o usuario voltava e nao via mais nada, o que e indistinguivel de
// "cancelou". Aqui o estado sobrevive a navegacao dentro do app, e o polling
// e retomado na montagem seguinte.
//
// O que NAO sobrevive, e nao tem como sobreviver, e o upload em si: fechar ou
// recarregar a aba aborta a requisicao no meio e o arquivo nunca chega inteiro.
// Por isso existe o aviso de saida enquanto `enviando` estiver ligado.

/** Um arquivo do envio multi-captura, com o veredito dele (D1-A). */
export interface ItemDoEnvio {
  gravacaoId: string;
  arquivo: string;
  voltas: number;
  layoutNome: string | null;
  /** preenchido quando o pipeline terminou SEM render voltas */
  motivo: string | null;
}

export type Fase =
  | { nome: "escolhendo" }
  | { nome: "enviando"; fracao: number }
  | { nome: "processando"; gravacaoId: string; desde: number }
  // D1-A: N capturas processam em paralelo; os nomes ficam aqui pra
  // sobreviver a troca de tela (o resumo final nomeia cada arquivo)
  | { nome: "processando-varias"; itens: { id: string; nome: string }[]; bateriaAlvo: string | null; desde: number }
  | { nome: "pronto"; gravacao: Gravacao }
  | { nome: "pronto-varias"; itens: ItemDoEnvio[] }
  | { nome: "parou"; gravacaoId: string; motivo: string }
  | { nome: "erro"; motivo: string };

interface Estado {
  fase: Fase;
  vinculo: string | null;
  setFase: (f: Fase) => void;
  setVinculo: (v: string | null) => void;
}

export const useEnvio = create<Estado>((set) => ({
  fase: { nome: "escolhendo" },
  vinculo: null,
  setFase: (fase) => set({ fase }),
  setVinculo: (vinculo) => set({ vinculo }),
}));
