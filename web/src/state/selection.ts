import { create } from "zustand";

// O estado de selecao compartilhado do funil, e nada mais.
// Espelha o objeto S do prototipo SARU Analyzer: uma selecao num nivel e o
// escopo do nivel seguinte. Deliberadamente NAO guarda dado do servidor: o
// SaDashboard.tsx do saru-app misturou os dois e virou 685 linhas com ~20
// useState. Widget recebe dado por prop, nunca puxa da store.
//
// ESCOPO GLOBAL (validado no prototipo em 29/08). `volta` e `compara` valem
// para o dashboard inteiro. Antes o traco no tempo tinha o proprio par de
// series (refA/refB) enquanto o resto da tela media contra a melhor volta sem
// ninguem poder mudar: duas verdades na mesma tela, e o usuario sem saber
// contra o que estava olhando. Agora existe um seletor so, na barra de escopo.

/**
 * "media" e a media das voltas validas; um numero e a volta N. `null` e
 * "ainda nao escolhida": quem resolve o default e a tela, a partir do
 * relatorio (a melhor propria), porque a store nao conhece dado de servidor.
 */
export type Referencia = number | "media";

/**
 * As paginas do funil. A ordem e a das tres perguntas que o engenheiro
 * nomeou: onde perdi, se estou melhorando, quanto gastei.
 */
export type PaginaId = "perdas" | "melhor_volta" | "mapa" | "evolucao" | "consumo" | "voltas" | "traco";

// Contexto (gaveta lateral) e Box (ferramentas) ficam fora do funil vertical
// de proposito: nao sao um "nivel" de zoom, sao acessiveis de qualquer nivel
// (plano, tabela do funil de zoom). O estado de qual gaveta/ferramenta esta
// aberta ainda e selecao pura, nao dado de servidor, entao mora aqui.
export type Vista =
  | { tipo: "geral" }
  | { tipo: "pagina"; id: PaginaId }
  // O envio de telemetria fica fora do funil pelo mesmo motivo que o box: nao
  // e nivel de zoom sobre a volta, e o que ACONTECE ANTES do funil existir.
  // O Sarue NAO esta aqui de proposito: ele virou sidebar com botao flutuante
  // proprio, entao nao e um lugar pra onde se navega.
  | { tipo: "envio" }
  // O dia de pista: evento, sessao, bateria. Fora do funil porque e o que
  // organiza a telemetria, nao um nivel de zoom sobre ela.
  | { tipo: "ciclo" }
  // A visao de campeonato (29/08): o grid inteiro pela cronometragem externa
  // (live timing MyLaps/Orbits via relay). Fora do funil porque nao le a
  // telemetria da conta: e outro zoom, o mais aberto de todos, o autodromo
  // visto de cima. Nao depende de gravacao nenhuma.
  | { tipo: "campeonato" };

export type MapMode = "speed" | "brake" | "gear" | "delta";
// "all" (default de 29/08) mistura curva nomeada com micro-setor: catalogo
// onde existe, 200 m no resto da pista.
export type LossMode = "all" | "corner" | "micro";
export type RunMetric = "lapTime" | "vMax" | "fuel" | "fullThrottle";
/** Acumulado e a integral da diferenca; instantaneo e a derivada dela. */
export type DeltaMode = "acumulado" | "instantaneo";

/** Intervalo marcado por arraste no traco, em distancia. */
export interface Intervalo {
  s_inicio_m: number;
  s_fim_m: number;
}

interface Selecao {
  // --- escopo, valido para a tela inteira ---
  /**
   * A espinha operacional em escopo: onde o piloto esta no dia de pista.
   *
   * Sao ids, nunca os objetos: a store nao guarda dado de servidor. Quem busca
   * evento, sessao e bateria e a tela do ciclo, e ela distribui por prop.
   * `null` em qualquer um significa "ainda nao escolhido", e nao "nao existe":
   * gravacao solta (decisao D3) roda sem espinha nenhuma, e e caso valido.
   */
  eventoId: string | null;
  sessaoId: string | null;
  bateriaId: string | null;
  /**
   * Contador de invalidacao da espinha. Toda MUTACAO (criar evento/sessao/
   * bateria, editar, pendurar gravacao) incrementa; os hooks de leitura
   * (useEventos/useSessoes/useBaterias/useBateriasDoEvento) o poem nas
   * dependencias e recarregam. Sem isso, a lista de baterias do header era
   * o cache do primeiro fetch da sessao SPA: bateria criada depois nao
   * aparecia e contagem de gravacao ficava velha (medido em 29/08).
   */
  versaoEspinha: number;
  /**
   * Contador de invalidacao do CATALOGO de gravacoes. Mesmo mecanismo do
   * `versaoEspinha`, pro `useGravacoes`: upload concluido, vinculo, exclusao.
   * Sem ele o catalogo da casca era o cache do primeiro fetch, e a gravacao
   * recem-enviada nao existia pra tela ate o F5 (a travada de 29/08).
   */
  versaoCatalogo: number;

  // --- O LADO B da comparacao ---------------------------------------------
  //
  // Escopo proprio pra referencia: outro evento, outra bateria, outra
  // gravacao, outra volta. Existe porque comparar so dentro do mesmo arquivo
  // responde "melhorei nesta sessao?" e nao responde "melhorei desde o mes
  // passado?", que e a pergunta que o piloto faz olhando o historico.
  //
  // `refGravacaoId` nulo significa "comparar dentro da propria gravacao", que
  // e o comportamento antigo e continua sendo o default.
  refEventoId: string | null;
  refSessaoId: string | null;
  refBateriaId: string | null;
  refGravacaoId: string | null;
  refVolta: number | null;
  /** id do trecho da referencia. Id de curva pertence ao layout dela, nunca ao da analisada. */
  refTrecho: string | null;

  /**
   * A gravacao aberta. E selecao, nao dado de servidor: guarda o id que o
   * usuario escolheu no catalogo, nunca o relatorio dela. Quem busca o
   * relatorio e `useRelatorio`, e quem o distribui e a casca.
   */
  gravacaoId: string | null;
  volta: number | null;
  compara: Referencia | null;
  /** id do trecho (curva ou micro-setor). Entra pelo clique no mapa ou na lista. */
  trecho: string | null;
  /** Intervalo livre marcado no traco. Independe do trecho catalogado. */
  intervalo: Intervalo | null;
  cursor_m: number | null;

  // --- modo de leitura de cada bloco ---
  mapMode: MapMode;
  lossMode: LossMode;
  runMetric: RunMetric;
  deltaMode: DeltaMode;

  // --- navegacao ---
  vista: Vista;
  /** Gaveta de contexto da bateria (bloco 15) aberta ou nao. */
  contextoAberto: boolean;
  /** Gaveta da ficha de setup (bloco 13) aberta ou nao. */
  setupAberto: boolean;

  /**
   * Posiciona a espinha inteira de uma vez, SEM a cascata de limpeza.
   *
   * Os setters individuais zeram o que esta abaixo deles, o que e certo quando
   * o usuario escolhe, e errado quando o sistema esta apenas SINCRONIZANDO com
   * a gravacao aberta: chamar os tres em sequencia faria cada um apagar o
   * anterior e o resultado seria sempre vazio.
   */
  sincronizarEspinha: (evento: string | null, sessao: string | null, bateria: string | null) => void;
  setEvento: (id: string | null) => void;
  setSessao: (id: string | null) => void;
  tocarEspinha: () => void;
  tocarCatalogo: () => void;
  setBateria: (id: string | null) => void;
  setGravacao: (id: string | null) => void;
  setRefEvento: (id: string | null) => void;
  setRefSessao: (id: string | null) => void;
  setRefBateria: (id: string | null) => void;
  setRefGravacao: (id: string | null) => void;
  setRefVolta: (n: number | null) => void;
  setRefTrecho: (id: string | null) => void;
  setVolta: (n: number | null) => void;
  setCompara: (r: Referencia) => void;
  setTrecho: (id: string | null) => void;
  setIntervalo: (i: Intervalo | null) => void;
  setCursor: (m: number | null) => void;
  setMapMode: (m: MapMode) => void;
  setLossMode: (m: LossMode) => void;
  setRunMetric: (m: RunMetric) => void;
  setDeltaMode: (m: DeltaMode) => void;
  irPara: (v: Vista) => void;
  setContextoAberto: (aberto: boolean) => void;
  setSetupAberto: (aberto: boolean) => void;
}

/**
 * O escopo sobrevive ao recarregar a pagina.
 *
 * Fase 6 do plano pede "persistir selecao" do trecho, e o mesmo argumento vale
 * pro resto do escopo: quem estava olhando a Curva 3 da volta 7 e apertou F5
 * voltava pro default e tinha que refazer tres cliques. Isso e preferencia de
 * quem olha, nao fato do dominio, entao mora no browser e nao no banco: e por
 * viewer, nao viaja entre contas, e nao precisa de migration.
 *
 * Guardo so o ESCOPO (o que o usuario escolheu), nunca dado de servidor. Se a
 * gravacao guardada tiver sumido, a casca cai no default sozinha, porque ela ja
 * valida contra o catalogo antes de abrir.
 */
const CHAVE = "saru.escopo";

type Escopo = Pick<
  Selecao,
  | "eventoId" | "sessaoId" | "bateriaId" | "gravacaoId"
  | "volta" | "compara" | "trecho"
  | "refEventoId" | "refSessaoId" | "refBateriaId" | "refGravacaoId" | "refVolta" | "refTrecho"
  | "vista"
>;

function lerEscopo(): Partial<Escopo> {
  try {
    return JSON.parse(localStorage.getItem(CHAVE) ?? "{}") as Partial<Escopo>;
  } catch {
    // navegacao privada, storage bloqueado, ou JSON velho de outra versao:
    // cair no default e sempre melhor que quebrar a tela por causa de uma
    // preferencia
    return {};
  }
}

function gravarEscopo(e: Selecao): void {
  try {
    const escopo: Escopo = {
      eventoId: e.eventoId, sessaoId: e.sessaoId, bateriaId: e.bateriaId,
      gravacaoId: e.gravacaoId, volta: e.volta, compara: e.compara, trecho: e.trecho,
      vista: e.vista,
      refEventoId: e.refEventoId, refSessaoId: e.refSessaoId, refBateriaId: e.refBateriaId,
      refGravacaoId: e.refGravacaoId, refVolta: e.refVolta, refTrecho: e.refTrecho,
    };
    localStorage.setItem(CHAVE, JSON.stringify(escopo));
  } catch {
    // nao persistir e aceitavel; travar a interface por isso nao e
  }
}

const guardado = lerEscopo();

/**
 * Apaga o escopo persistido e zera a store. Chamado no LOGOUT: escopo e
 * preferencia da conta que estava aberta, e deixa-lo para o proximo login e
 * como entregar a mesa com as gavetas cheias do ocupante anterior. Foi um dos
 * ingredientes do limbo de 29/08: cookie morto + escopo velho apontando pra
 * gravacao que a proxima sessao nao enxerga.
 */
export function limparEscopo(): void {
  try {
    localStorage.removeItem(CHAVE);
  } catch {
    // storage bloqueado: o reset da store abaixo ainda vale
  }
  useSelecao.setState({
    eventoId: null, sessaoId: null, bateriaId: null, gravacaoId: null,
    volta: null, compara: null, trecho: null, intervalo: null, cursor_m: null,
    refEventoId: null, refSessaoId: null, refBateriaId: null, refGravacaoId: null,
    refVolta: null, refTrecho: null,
    vista: { tipo: "geral" },
  });
}

export const useSelecao = create<Selecao>((set) => ({
  refEventoId: guardado.refEventoId ?? null,
  refSessaoId: guardado.refSessaoId ?? null,
  refBateriaId: guardado.refBateriaId ?? null,
  refGravacaoId: guardado.refGravacaoId ?? null,
  refVolta: guardado.refVolta ?? null,
  refTrecho: guardado.refTrecho ?? null,
  eventoId: guardado.eventoId ?? null,
  sessaoId: guardado.sessaoId ?? null,
  bateriaId: guardado.bateriaId ?? null,
  gravacaoId: guardado.gravacaoId ?? null,
  versaoEspinha: 0,
  versaoCatalogo: 0,
  volta: guardado.volta ?? null,
  compara: guardado.compara ?? null,
  trecho: guardado.trecho ?? null,
  intervalo: null,
  cursor_m: null,
  mapMode: "speed",
  lossMode: "all",
  runMetric: "lapTime",
  // instantaneo por padrao (pedido de 29/08): o piloto le primeiro ONDE
  // ganha e perde; a soma corrida fica a um clique.
  deltaMode: "instantaneo",
  // F5 volta pra onde o usuario estava (pedido de 29/08): a vista persiste
  // junto com o escopo. Gaveta aberta NAO persiste: sobreposicao e gesto.
  vista: guardado.vista ?? { tipo: "geral" },
  contextoAberto: false,
  setupAberto: false,

  // Cada nivel da espinha zera os de baixo. Sessao de outro evento e bateria de
  // outra sessao nao existem, e manter o id antigo faria a tela pedir um
  // recurso que devolve 404, ou pior, mostrar rotulo de uma bateria com numero
  // de outra.
  sincronizarEspinha: (eventoId, sessaoId, bateriaId) => set({ eventoId, sessaoId, bateriaId }),
  setEvento: (eventoId) => set({ eventoId, sessaoId: null, bateriaId: null }),
  setSessao: (sessaoId) => set({ sessaoId, bateriaId: null }),
  tocarEspinha: () => set((e) => ({ versaoEspinha: e.versaoEspinha + 1 })),
  tocarCatalogo: () => set((e) => ({ versaoCatalogo: e.versaoCatalogo + 1 })),
  setBateria: (bateriaId) => set({ bateriaId }),

  // Trocar de gravacao zera TODO o escopo abaixo dela: volta 7 de uma gravacao
  // nao e volta 7 de outra, e trecho e id de layout. Manter qualquer coisa
  // daqui pra baixo seria mostrar numero de uma sessao com rotulo de outra.
  setGravacao: (gravacaoId) =>
    set({ gravacaoId, volta: null, compara: null, trecho: null, intervalo: null, cursor_m: null }),
  // O lado B zera para baixo pelo mesmo motivo do lado A: volta 7 de uma
  // gravacao nao e volta 7 de outra, e trecho e id de layout.
  setRefEvento: (refEventoId) =>
    set({ refEventoId, refSessaoId: null, refBateriaId: null, refGravacaoId: null, refVolta: null, refTrecho: null }),
  // Sessao da referencia: mesmo papel do `setSessao` do lado A, zerando os
  // niveis de baixo (bateria de outra sessao nao existe).
  setRefSessao: (refSessaoId) =>
    set({ refSessaoId, refBateriaId: null, refGravacaoId: null, refVolta: null, refTrecho: null }),
  setRefBateria: (refBateriaId) =>
    set({ refBateriaId, refGravacaoId: null, refVolta: null, refTrecho: null }),
  setRefGravacao: (refGravacaoId) => set({ refGravacaoId, refVolta: null, refTrecho: null }),
  // Espelha setVolta: trocar a volta de referencia reabre o escopo de trecho
  // dela, pelo mesmo motivo (o trecho antigo era de outra volta/layout).
  setRefVolta: (refVolta) => set({ refVolta, refTrecho: null }),
  setRefTrecho: (refTrecho) => set({ refTrecho }),

  // Escolher volta reabre o N2/N3 nela: o escopo antigo nao sobrevive.
  setVolta: (volta) => set({ volta, trecho: null, intervalo: null, cursor_m: null }),
  // Trocar a referencia nao muda o zoom, muda contra o que tudo e medido.
  setCompara: (compara) => set({ compara }),
  setTrecho: (trecho) => set({ trecho, intervalo: null, cursor_m: null }),
  setIntervalo: (intervalo) => set({ intervalo }),
  setCursor: (cursor_m) => set({ cursor_m }),
  setMapMode: (mapMode) => set({ mapMode }),
  // Trocar de modo limpa o trecho: id de curva nao vale como id de
  // micro-setor. Quem decide se o modo por curva existe e o dado
  // (resolucao_pista no relatorio), nao o usuario.
  setLossMode: (lossMode) => set({ lossMode, trecho: null }),
  setRunMetric: (runMetric) => set({ runMetric }),
  setDeltaMode: (deltaMode) => set({ deltaMode }),
  irPara: (vista) => set({ vista }),
  setContextoAberto: (contextoAberto) => set({ contextoAberto }),
  setSetupAberto: (setupAberto) => set({ setupAberto }),
}));

// Um assinante so, em vez de gravar dentro de cada setter: assim nenhum setter
// novo esquece de persistir, que e o jeito de a preferencia sumir de um campo
// so e ninguem entender por que.
useSelecao.subscribe(gravarEscopo);
