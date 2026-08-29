// Espinha operacional: evento, sessao, bateria, contexto, setup, layouts.

import { enviar, enviarPatch, obter, excluir } from "./api";

export interface Layout {
  id: string;
  nome: string;
  comprimento_m: number | null;
  pista_nome: string | null;
  cidade: string | null;
}

export interface Evento {
  id: string;
  track_id: string;
  name: string;
  /** D2-B: formato do evento; decide as sessoes pre-montadas. null em evento antigo. */
  tipo?: string | null;
  starts_at: string;
  ends_at: string | null;
  local_date: string | null;
  created_at: string;
  layout_nome?: string | null;
  sessoes?: number;
}

export interface Sessao {
  id: string;
  event_id: string;
  type: string;
  label: string | null;
  planned_laps: number | null;
  starts_at: string | null;
  /** D4: a sessao e a janela de pista aberta; tem fim, nao so comeco. */
  ends_at: string | null;
  /** Quantas baterias a sessao reune, e quantas voltas elas somam. */
  baterias?: number;
  voltas?: number;
}

export interface Bateria {
  id: string;
  session_id: string;
  evento_id: string;
  /** D4: nome do outing na tela ("B1", "Treino 1"...). */
  label: string | null;
  /** D4: o que o piloto saiu pra fazer (run sheet). */
  objective: string | null;
  laps: number | null;
  fuel_in_l: number | null;
  fuel_out_l: number | null;
  started_at: string | null;
  went_out_at: string | null;
  created_at: string;
  gravacoes?: number;
  /**
   * O que a bateria E: as voltas que a telemetria dela mediu, contadas na
   * tabela `volta`. Nao vem da coluna `laps`, que e denormalizada e sem
   * recalculo automatico nesta PoC.
   */
  voltas?: number;
  melhor_volta_s?: number | null;
}

export interface RegistroContexto {
  id: string;
  bateria_id: string | null;
  gravacao_id: string | null;
  pneu_estado: string | null;
  pneu_voltas_rodadas: number | null;
  pneu_composto: string | null;
  temp_ar_c: number | null;
  temp_pista_c: number | null;
  vento_kmh: number | null;
  horario: string | null;
  notas_piloto: string | null;
  notas_engenheiro: string | null;
  criado_em: string;
}

/** Uma versao da ficha. `valores` e livre por decisao: a ficha ainda nao fechou formato. */
export interface VersaoSetup {
  id: string;
  bateria_id: string | null;
  gravacao_id: string | null;
  versao: number;
  valores: Record<string, string | number>;
  notas: string | null;
  criado_em: string;
}

export interface Trecho {
  id: string;
  rotulo: string;
  s_inicio_m: number;
  s_fim_m: number;
  apex_m: number | null;
}

/** `bateria` ou `gravacao`: contexto e setup penduram nos dois (num_nonnulls = 1 no banco). */
export type Dono = "baterias" | "gravacoes";

import { useSelecao } from "../state/selection";

// Toda mutacao da espinha invalida os caches de leitura (ver
// `versaoEspinha` na store). Feito AQUI, no service, e nao em cada tela:
// quem muda o dado e quem sabe que ele mudou, e nenhuma tela nova esquece.
const tocando = <T,>(promessa: Promise<T>): Promise<T> =>
  promessa.then((v) => {
    useSelecao.getState().tocarEspinha();
    return v;
  });

// Mutacao que muda O QUE EXISTE no catalogo de gravacoes (vinculo, exclusao)
// invalida tambem o `useGravacoes`: a casca decide a tela inteira por ele.
const tocandoCatalogo = <T,>(promessa: Promise<T>): Promise<T> =>
  promessa.then((v) => {
    const estado = useSelecao.getState();
    estado.tocarEspinha();
    estado.tocarCatalogo();
    return v;
  });

export const listarLayouts = () => obter<Layout[]>("/layouts");
export const listarTrechos = (layoutId: string) =>
  obter<Trecho[]>(`/layouts/${layoutId}/trechos`);

export const listarEventos = () => obter<Evento[]>("/eventos");
export const criarEvento = (dados: Partial<Evento>) =>
  tocando(enviar<Evento>("/eventos", dados));
/** Edita o evento. Mesmo padrao do `editarBateria`: PATCH so aceita o que esta
 *  na lista branca do backend (name, starts_at, ends_at, local_date, track_id),
 *  mandar outro campo nao tem efeito. */
export const editarEvento = (eventoId: string, dados: Partial<Evento>) =>
  tocando(enviarPatch<Evento>(`/eventos/${eventoId}`, dados));
export const listarSessoes = (eventoId: string) =>
  obter<Sessao[]>(`/eventos/${eventoId}/sessoes`);
/** Edita a sessao (nome, tipo). Mesma lista branca do backend. */
export const editarSessao = (sessaoId: string, dados: Partial<Sessao>) =>
  tocando(enviarPatch<Sessao>(`/sessoes/${sessaoId}`, dados));
export const criarSessao = (eventoId: string, dados: Partial<Sessao>) =>
  tocando(enviar<Sessao>(`/eventos/${eventoId}/sessoes`, dados));
/** Edita a bateria. Combustivel mora aqui, nao no contexto: `fuel_in_l` e
 *  `fuel_out_l` sao colunas da bateria, porque combustivel e por ida a pista. */
export const editarBateria = (bateriaId: string, dados: Partial<Bateria>) =>
  tocando(enviarPatch<Bateria>(`/baterias/${bateriaId}`, dados));

export const listarBaterias = (sessaoId: string) =>
  obter<Bateria[]>(`/sessoes/${sessaoId}/baterias`);
export const criarBateria = (sessaoId: string, dados: Partial<Bateria>) =>
  tocando(enviar<Bateria>(`/sessoes/${sessaoId}/baterias`, dados));

/** Pendura uma gravacao numa bateria: o momento em que o arquivo solto deixa de ser solto. */
export const vincularGravacao = (bateriaId: string, gravacaoId: string) =>
  tocandoCatalogo(enviar<void>(`/baterias/${bateriaId}/gravacoes/${gravacaoId}`, {}));
/** Solta a gravacao da bateria SEM apagar nada: corrige anexo errado. */
export const desvincularGravacao = (bateriaId: string, gravacaoId: string) =>
  tocandoCatalogo(excluir(`/baterias/${bateriaId}/gravacoes/${gravacaoId}`));

export const historicoContexto = (dono: Dono, id: string) =>
  obter<RegistroContexto[]>(`/${dono}/${id}/contexto`);
export const registrarContexto = (dono: Dono, id: string, captura: unknown) =>
  enviar<RegistroContexto>(`/${dono}/${id}/contexto`, captura);
/** Corrige um registro existente. Historico continua sendo a regra; isto e pro dedo errado. */
export const editarContexto = (contextoId: string, captura: unknown) =>
  enviarPatch<RegistroContexto>(`/contexto/${contextoId}`, captura);
export const excluirContexto = (contextoId: string) =>
  excluir(`/contexto/${contextoId}`);

export const versoesSetup = (dono: Dono, id: string) =>
  obter<VersaoSetup[]>(`/${dono}/${id}/setup`);
/** Salvar cria versao nova, nunca sobrescreve: e o que sustenta "o que mudou da B2 pra B3". */
export const salvarSetup = (
  dono: Dono,
  id: string,
  valores: Record<string, string | number>,
  notas?: string,
) => enviar<VersaoSetup>(`/${dono}/${id}/setup`, { valores, notas: notas ?? null });
/** Corrige a versao EM CIMA, sem criar nova: e pro dedo errado, nao pra evolucao de setup. */
export const editarSetup = (
  setupId: string,
  valores: Record<string, string | number>,
  notas?: string,
) => enviarPatch<VersaoSetup>(`/setup/${setupId}`, { valores, notas: notas ?? null });
export const excluirSetup = (setupId: string) => excluir(`/setup/${setupId}`);

// --- exclusao (29/08): sempre confirmada por modal no front ---------------
// Evento/sessao/bateria sao registro administrativo: apagar DESPENDURA a
// telemetria (vira arquivo solto), nunca a apaga. So excluirGravacao apaga
// telemetria de verdade, com tudo que deriva dela.
export const excluirEvento = (eventoId: string) =>
  tocandoCatalogo(excluir(`/eventos/${eventoId}`));
export const excluirSessao = (sessaoId: string) =>
  tocandoCatalogo(excluir(`/sessoes/${sessaoId}`));
export const excluirBateria = (bateriaId: string) =>
  tocandoCatalogo(excluir(`/baterias/${bateriaId}`));
export const excluirGravacao = (gravacaoId: string) =>
  tocandoCatalogo(excluir(`/gravacoes/${gravacaoId}`));
