import { useRequisicao } from "../dados/requisicao";
import { useSelecao } from "../state/selection";
import {
  listarBaterias,
  listarEventos,
  listarLayouts,
  listarPilotosDoEvento,
  listarSessoes,
  listarTrechos,
  type Bateria,
  type Evento,
  type Layout,
  type PilotoDoEvento,
  type Sessao,
  type Trecho,
} from "../services/operacao";

// Um hook por nivel da espinha. Cada um so busca quando o nivel de cima ja foi
// escolhido: pedir sessao sem evento seria uma requisicao que o servidor
// responderia com 404 e que a tela nao teria como usar.

export const useEventos = () => {
  const versao = useSelecao((e) => e.versaoEspinha);
  return useRequisicao<Evento[]>(() => listarEventos(), [versao]);
};

export const useLayouts = () => useRequisicao<Layout[]>(() => listarLayouts(), []);

/** Pilotos que rodaram no evento. Degrau entre evento e sessao (30/08). */
export const usePilotos = (eventoId: string | null) => {
  const versao = useSelecao((e) => e.versaoEspinha);
  return useRequisicao<PilotoDoEvento[]>(
    () => listarPilotosDoEvento(eventoId as string), [eventoId, versao], eventoId !== null,
  );
};

/** Sessoes do evento, filtradas pelo piloto quando ha um em escopo. */
export const useSessoes = (eventoId: string | null, pilotoId: string | null = null) => {
  const versao = useSelecao((e) => e.versaoEspinha);
  return useRequisicao<Sessao[]>(
    () => listarSessoes(eventoId as string, pilotoId),
    [eventoId, pilotoId, versao],
    eventoId !== null,
  );
};

export const useBaterias = (sessaoId: string | null) => {
  const versao = useSelecao((e) => e.versaoEspinha);
  return useRequisicao<Bateria[]>(
    () => listarBaterias(sessaoId as string), [sessaoId, versao], sessaoId !== null,
  );
};

/**
 * Curvas catalogadas do layout (fase 6).
 *
 * Vem daqui, e nao do `Relatorio`, quando o objetivo e ESCOLHER trecho antes de
 * haver volta pra comparar. Dentro do relatorio os mesmos trechos aparecem com
 * a perda junto, calculada contra o par em escopo, que e outra pergunta.
 */
export const useTrechos = (layoutId: string | null) =>
  useRequisicao<Trecho[]>(() => listarTrechos(layoutId as string), [layoutId], layoutId !== null);


/**
 * Todas as baterias do evento, achatadas das suas sessoes.
 *
 * O header troca BATERIA, nao sessao: sessao e agrupamento administrativo, e
 * quem sai pra pista sai numa bateria. Achatar aqui evita um seletor a mais na
 * barra pra um nivel que o piloto nao pensa.
 */
export function useBateriasDoEvento(eventoId: string | null) {
  const sessoes = useSessoes(eventoId);
  const versao = useSelecao((e) => e.versaoEspinha);
  const ids = (sessoes.dado ?? []).map((s) => s.id).join(",");
  const req = useRequisicao<{ sessao: Sessao; bateria: Bateria }[]>(
    async () => {
      const lista = sessoes.dado ?? [];
      const porSessao = await Promise.all(lista.map((s) => listarBaterias(s.id)));
      return lista.flatMap((s, i) => porSessao[i].map((b) => ({ sessao: s, bateria: b })));
    },
    // `versao` nas deps: bateria criada ou gravacao pendurada em outra tela
    // invalida esta lista (ver `versaoEspinha` na store). Sem isso o header
    // mostrava so as baterias do primeiro fetch da sessao SPA.
    [ids, versao],
    ids.length > 0,
  );
  return { ...req, carregando: sessoes.carregando || req.carregando };
}
