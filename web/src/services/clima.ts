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
  previsao_horaria: PontoPrevisao[];
}

export const climaDoLayout = (layoutId: string) => obter<Clima>(`/clima/${layoutId}`);
