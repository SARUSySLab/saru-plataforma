// Sarue, o assistente de IA. O front so apresenta: nao monta prompt, nao
// escolhe modelo, nao dispara o ciclo periodico. Tudo isso mora no servidor.

import { enviar, obter } from "./api";

export interface Turno {
  id: string;
  pergunta: string;
  resposta: string | null;
  /** Numeros que a resposta afirmou e a base de fatos nao sustenta. Vazio e o normal. */
  numeros_nao_conferidos?: string[];
  criado_em: string;
}

export interface Aviso {
  id: string;
  texto: string;
  modelo: string;
  visto_em: string | null;
  criado_em: string;
}

export const perguntar = (gravacaoId: string, pergunta: string) =>
  enviar<Turno>("/sarue/perguntar", { gravacao_id: gravacaoId, pergunta });

export const listarTurnos = (gravacaoId: string) =>
  obter<Turno[]>("/sarue/turnos", { gravacao_id: gravacaoId });

export const listarAvisos = (gravacaoId: string, apenasNovos = false) =>
  obter<Aviso[]>("/sarue/avisos", { gravacao_id: gravacaoId, apenas_novos: apenasNovos });

export const marcarVisto = (avisoId: string) =>
  enviar<void>(`/sarue/avisos/${avisoId}/visto`, {});
