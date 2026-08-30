// Clima pela coordenada do layout. Passa pelo backend, nao pela fonte direto:
// o cache de 15 min vale pra todos os clientes de uma vez, e no dia em que a
// fonte exigir chave, a chave nao vai pro bundle.

import { obter } from "./api";
import type { PontoPrevisao } from "../types/contract";

export interface Clima {
  layout_id: string;
  temperatura_atual_c: number;
  vento_kmh: number | null;
  condicao_atual: string | null;
  chuva_prob_atual?: number | null;
  umidade_pct?: number | null;
  /** Temperatura de PISTA ESTIMADA. Nao e medida de asfalto: vem de solo
   *  modelado, e a diferenca chega a passar de 15 graus em dia de sol. Sempre
   *  exibir junto de `pista_estimada_fonte`, nunca como numero cravado. */
  pista_estimada_c?: number | null;
  pista_estimada_fonte?: string | null;
  /** Direcao DE ONDE o vento vem, em graus (0 = norte), convencao meteorologica. */
  vento_dir_graus?: number | null;
  previsao_horaria: PontoPrevisao[];
}

export const climaDoLayout = (layoutId: string) => obter<Clima>(`/clima/${layoutId}`);
