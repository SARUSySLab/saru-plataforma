// Visao de campeonato: live timing externo (XML MyLaps/Orbits via relay).
//
// O caminho quente e o SSE (`streamDoEvento`): o backend empurra o estado a
// cada snapshot novo. O `estadoDoEvento` por GET existe como fallback quando o
// EventSource morre (proxy velho, rede movel), e o hook da tela decide quando
// degradar pra poll. Mesma regra da casa: componente nao chama isto, hook
// chama servico, servico chama a api.

import { obter } from "./api";

export interface EventoLt {
  id: string;
  nome: string;
  grupo: string | null;
  run_nome: string;
  run_tipo: string | null;
  pista_nome: string | null;
  track_length_m: number | null;
  layout_id: string | null;
  ultimo_snapshot_em: string | null;
  snapshots: number;
}

export interface ResultadoLt {
  posicao: number | null;
  posicao_classe: number | null;
  numero: string;
  transponder: string | null;
  nome: string;
  carro: string | null;
  classe: string | null;
  voltas: number | null;
  ultima_volta_s: number | null;
  penultima_volta_s: number | null;
  antepenultima_volta_s: number | null;
  melhor_volta_s: number | null;
  melhor_volta_n: number | null;
  melhor_vel_kmh: number | null;
  segunda_melhor_s: number | null;
  media_s: number | null;
  total_s: number | null;
  gap: string | null;
  diff: string | null;
  ultima_vel_kmh: number | null;
  ultima_passagem_tod: string | null;
  ultima_passagem_s: number | null;
  pits: number | null;
  setores: Record<string, number>;
  melhores_setores: Record<string, number>;
}

export interface EstadoLt {
  evento: {
    id: string;
    nome: string;
    grupo: string | null;
    run_nome: string;
    run_tipo: string | null;
    pista_nome: string | null;
    track_length_m: number | null;
    layout_id: string | null;
  };
  snapshot: {
    id: string;
    timeofday: string | null;
    timeofday_s: number | null;
    racetime: string | null;
    flag: string | null;
    labels: Record<string, string>;
    resultados: ResultadoLt[];
    recebido_em: string;
  } | null;
}

export interface TracadoLt {
  disponivel: boolean;
  motivo: string | null;
  layout_id?: string;
  comprimento_m?: number | null;
  pontos: { x: number; y: number; s_m: number }[];
}

export const eventosLt = () => obter<EventoLt[]>("/campeonato/eventos");
export const estadoDoEvento = (id: string) => obter<EstadoLt>(`/campeonato/${id}/estado`);
export const tracadoDoEvento = (id: string) => obter<TracadoLt>(`/campeonato/${id}/tracado`);

/**
 * SSE do estado. Devolve a funcao de encerrar; erros vao pro `aoFalhar`, e o
 * chamador decide degradar pra poll (o EventSource ja tenta reconectar
 * sozinho antes disso).
 */
export function streamDoEvento(
  id: string,
  aoChegar: (estado: EstadoLt) => void,
  aoFalhar: () => void,
): () => void {
  const fonte = new EventSource(`/api/campeonato/${id}/stream`);
  fonte.addEventListener("estado", (ev) => {
    try {
      aoChegar(JSON.parse((ev as MessageEvent).data) as EstadoLt);
    } catch {
      // payload podre num evento nao derruba o stream inteiro
    }
  });
  fonte.onerror = () => {
    // readyState CLOSED = desistiu de reconectar; ate la e soluço de rede
    if (fonte.readyState === EventSource.CLOSED) aoFalhar();
  };
  return () => fonte.close();
}
