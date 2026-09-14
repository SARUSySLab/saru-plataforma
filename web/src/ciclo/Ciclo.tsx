import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import "../estilo/ciclo.css";
import { useSelecao } from "../state/selection";
import { useBaterias, useEventos, useLayouts, usePilotos, useSessoes } from "./useEspinha";
import {
  criarBateria,
  criarEvento,
  criarSessao,
  desvincularGravacao,
  editarBateria,
  editarEvento,
  editarSessao,
  excluirBateria,
  excluirEvento,
  excluirGravacao,
  excluirSessao,
} from "../services/operacao";
import { ErroDaApi } from "../services/api";
import { EnvioDeTelemetria } from "../envio/EnvioDeTelemetria";
import { useGravacoes } from "../dados/useGravacoes";
import { useContexto } from "../dados/useContexto";
import { useSetup } from "../dados/useSetup";
import { Modal } from "../componentes/Modal";
import { CampoDataHora } from "../componentes/CampoDataHora";
import { ContextoDaBateria } from "../gavetas/ContextoDaBateria";
import { FichaDeSetup } from "../gavetas/FichaDeSetup";

// Fases 2, 3 e 11. A espinha operacional e a maquina de estados do dia:
//
//   evento > sessao > outing > (setup, contexto) > telemetria > analise
//
// D4-B (29/08): a TELA fala "outing" (o carro saindo do box); o codigo e o
// banco ainda chamam de bateria, e o rename estrutural fica pra depois da
// fase de testes. Sessao e a janela de pista aberta, com comeco e fim.
//
// **Reorganizacao de 29/08 (pedido do dono):**
//
// 1. A trilha do topo NAVEGA de verdade (pedido 2.1): clicar num passo ja
//    cumprido abre a lista daquele nivel SEM desfazer a escolha atual. A
//    escolha so muda quando o usuario clica em outro item da lista.
// 2. Os niveis escolhidos sao CARDS lado a lado, com editar/excluir ali, e
//    clicar no card tambem navega pro nivel.
// 3. O passo da bateria escolhida se organiza em duas colunas: telemetria
//    (o que a bateria mediu + envio) e registro do box (contexto e ficha de
//    setup, com estado de preenchimento visivel).
// 4. Contexto e ficha abrem em MODAL (padrao do sistema) e sao renderizados
//    AQUI, entao funcionam tambem na conta ainda sem relatorio nenhum.

type Passo = "evento" | "piloto" | "sessao" | "bateria" | "pronto";
type ModalAberto =
  | null | "evento" | "editar-evento" | "sessao" | "editar-sessao" | "bateria" | "editar-bateria"
  | "telemetria";

function Erro({ e }: { e: unknown }) {
  if (!e) return null;
  return <p className="ciclo-erro">{e instanceof ErroDaApi ? e.message : "falha inesperada"}</p>;
}

/** mm:ss.mmm, o formato que o resto do app usa pra tempo de volta. */
function tempo(s: number | null | undefined): string | null {
  if (s == null) return null;
  const m = Math.floor(s / 60);
  const r = s - m * 60;
  return `${m}:${r.toFixed(3).padStart(6, "0")}`;
}

function Data({ iso }: { iso: string | null }) {
  if (!iso) return <span className="fraco">sem horário</span>;
  return <span>{new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}</span>;
}

/** Nome do outing na tela: o label cadastrado, senao a hora de saida. */
function nomeDoOuting(b: { label: string | null; went_out_at: string | null }): string {
  return b.label ?? `saída das ${hora(b.went_out_at)}`;
}

function hora(iso: string | null): string {
  return iso
    ? new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
    : "sem horário";
}

/** ISO -> "YYYY-MM-DDTHH:mm", o formato que o input datetime-local aceita como
 *  defaultValue. Sem isto o campo de editar abre em branco mesmo com valor
 *  salvo, porque o input nao entende ISO com segundos/timezone. */
function paraInputDatetime(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/**
 * Lista que NUNCA rola (pedido de 29/08: o dia de pista inteiro cabe numa
 * tela). A altura disponivel e medida (ResizeObserver) e o que nao couber
 * vira pagina, com setas manuais. Mesma linguagem do leaderboard do
 * campeonato, sem o rodizio automatico: aqui a lista e de trabalho, nao
 * telao.
 */
function ListaPaginada({ children, compacta = false }: {
  children: ReactNode[];
  compacta?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const refLista = useRef<HTMLUListElement>(null);
  const [altura, setAltura] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setAltura(el.clientHeight));
    ro.observe(el);
    setAltura(el.clientHeight);
    return () => ro.disconnect();
  }, []);

  // A altura do item NAO pode ser chutada. Item de uma linha (evento) e item
  // de duas (piloto, sessao, saida, telemetria: titulo + subtitulo) tem
  // alturas bem diferentes, e o palpite fixo fazia a conta caber mais itens
  // do que a caixa aguenta -- como a caixa e overflow:hidden, o excedente
  // sumia cortado no meio, que era o "scroll bugado". Medir o primeiro item
  // ja renderizado resolve pros dois casos e pra qualquer fonte do usuario.
  const [alturaMedida, setAlturaMedida] = useState(0);
  useLayoutEffect(() => {
    const primeiro = refLista.current?.firstElementChild as HTMLElement | null;
    if (!primeiro) return;
    const gap = 2; // mesmo gap de .ciclo-lista
    const h = primeiro.getBoundingClientRect().height + gap;
    if (h > 0 && Math.abs(h - alturaMedida) > 0.5) setAlturaMedida(h);
  });

  const [pagina, setPagina] = useState(0);
  const n = children.length;
  const alturaItem = alturaMedida > 0 ? alturaMedida : compacta ? 36 : 48;
  // reserva a faixa do pager quando ha mais de uma pagina
  const porPagina = Math.max(1, Math.floor(Math.max(alturaItem, altura - 26) / alturaItem));
  const paginado = n > porPagina;
  const totalPaginas = Math.max(1, Math.ceil(n / porPagina));
  const atual = ((pagina % totalPaginas) + totalPaginas) % totalPaginas;
  const visiveis = paginado ? children.slice(atual * porPagina, (atual + 1) * porPagina) : children;

  return (
    <div ref={ref} className="ciclo-lista-caixa">
      <ul ref={refLista} className={`ciclo-lista${compacta ? " compacta" : ""}`}>{visiveis}</ul>
      {paginado && (
        <div className="ciclo-paginas">
          <button type="button" className="ciclo-seta" onClick={() => setPagina(atual - 1)} aria-label="Página anterior">&lsaquo;</button>
          <span>página {atual + 1} de {totalPaginas}</span>
          <button type="button" className="ciclo-seta" onClick={() => setPagina(atual + 1)} aria-label="Próxima página">&rsaquo;</button>
        </div>
      )}
    </div>
  );
}

/**
 * Campos de formulario em paginas, pro modal que NAO rola (pedido de 29/08:
 * cadastro grande pagina em vez de rolar). As paginas ocultas continuam
 * MONTADAS (atributo hidden), entao o valor digitado sobrevive a navegacao e
 * o submit envia o formulario inteiro. Campo required fica na pagina 1, que
 * sempre foi vista antes do submit.
 */
function CamposPaginados({ paginas }: {
  paginas: { titulo: string; campos: ReactNode }[];
}) {
  const [atual, setAtual] = useState(0);
  return (
    <>
      {paginas.map((pg, i) => (
        <div key={pg.titulo} className="ciclo-form-pagina" hidden={i !== atual}>
          {pg.campos}
        </div>
      ))}
      {paginas.length > 1 && (
        <div className="ciclo-paginas form">
          <button type="button" className="ciclo-seta" disabled={atual === 0} onClick={() => setAtual(atual - 1)} aria-label="Página anterior">&lsaquo;</button>
          <span>{paginas[atual].titulo} · {atual + 1} de {paginas.length}</span>
          <button type="button" className="ciclo-seta" disabled={atual === paginas.length - 1} onClick={() => setAtual(atual + 1)} aria-label="Próxima página">&rsaquo;</button>
        </div>
      )}
    </>
  );
}

export function Ciclo() {
  const {
    eventoId, pilotoId, sessaoId, bateriaId, setEvento, setPiloto, setSessao, setBateria,
    contextoAberto, setContextoAberto, setupAberto, setSetupAberto,
  } = useSelecao();
  const eventos = useEventos();
  const layouts = useLayouts();
  const pilotos = usePilotos(eventoId);
  const sessoes = useSessoes(eventoId);
  const baterias = useBaterias(sessaoId);
  const [erro, setErro] = useState<unknown>(null);
  const [criando, setCriando] = useState(false);
  const [modal, setModal] = useState<ModalAberto>(null);
  // Exclusao SEMPRE confirmada (pedido de 29/08). `confirmar` guarda o alvo e
  // o modal explica exatamente o que vai acontecer com cada tipo.
  const [confirmar, setConfirmar] = useState<
    null | { tipo: "evento" | "sessao" | "bateria" | "gravacao"; id: string; rotulo: string }
  >(null);
  const gravacoes = useGravacoes(false);
  const penduradas = (gravacoes.dado ?? []).filter((g) => g.bateria_id === bateriaId);

  // Estado de preenchimento do registro do box (pedido de 29/08: feedback
  // visual). Le a MESMA fonte das telas de leitura, nao um flag proprio.
  const contexto = useContexto("baterias", bateriaId);
  const setup = useSetup("baterias", bateriaId);
  const registros = contexto.dado?.length ?? 0;
  const ultimaVersao = (setup.dado ?? []).reduce((m, v) => Math.max(m, v.versao), 0);

  // A trilha NAVEGA (pedido 2.1): `passoForcado` abre a lista de um nivel ja
  // cumprido sem desfazer a escolha. Escolher outro item e o que troca (os
  // setters ja zeram os niveis de baixo); escolher o MESMO so volta ao fluxo.
  const [passoForcado, setPassoForcado] = useState<Passo | null>(null);
  const passoNatural: Passo = !eventoId ? "evento" : !pilotoId ? "piloto"
    : !sessaoId ? "sessao" : !bateriaId ? "bateria" : "pronto";
  const passo: Passo = passoForcado ?? passoNatural;

  const evento = eventos.dado?.find((e) => e.id === eventoId) ?? null;
  const piloto = (pilotos.dado ?? []).find((p) => (p.piloto_id ?? "sem") === pilotoId) ?? null;
  const sessao = sessoes.dado?.find((s) => s.id === sessaoId) ?? null;
  // So as sessoes do piloto em escopo. O balde "sem" agrupa as sessoes sem
  // piloto declarado, que e como o acervo antigo aparece.
  const sessoesDoPiloto = (sessoes.dado ?? []).filter(
    (s) => !pilotoId || (s.piloto_id ?? "sem") === pilotoId,
  );

  // Escopo restaurado do localStorage pode trazer uma sessao de OUTRO piloto,
  // ou de antes do degrau do piloto existir. Quem manda e a SESSAO: ela diz de
  // quem e, e o escopo se ajusta a ela. Sem isto a trilha mostrava piloto
  // vazio com sessao preenchida, que e um estado que nao existe no dominio:
  // nao se chega em sessao sem passar por piloto.
  useEffect(() => {
    if (!sessao) return;
    const dono = sessao.piloto_id ?? "sem";
    if (dono !== pilotoId) setPiloto(dono);
  }, [sessao, pilotoId, setPiloto]);

  // A recíproca: sessao escolhida que a lista ainda nao trouxe (evento trocado,
  // escopo velho) nao pode deixar a tela num passo inalcancavel. Sem piloto, o
  // caminho volta pro comeco em vez de mostrar sessao orfa.
  useEffect(() => {
    if (sessaoId && !pilotoId && sessoes.dado && !sessao) setSessao(null);
  }, [sessaoId, pilotoId, sessoes.dado, sessao, setSessao]);
  const bateria = baterias.dado?.find((b) => b.id === bateriaId) ?? null;

  const alcancavel: Record<Passo, boolean> = {
    evento: true,
    piloto: eventoId !== null,
    sessao: pilotoId !== null,
    bateria: sessaoId !== null,
    pronto: bateriaId !== null,
  };

  function irParaPasso(p: Passo) {
    if (!alcancavel[p]) return;
    setPassoForcado(p === passoNatural ? null : p);
  }

  async function rodar(acao: () => Promise<void>) {
    setCriando(true);
    setErro(null);
    try {
      await acao();
      setModal(null);
    } catch (e) {
      setErro(e);
    } finally {
      setCriando(false);
    }
  }

  const novoEvento = (form: HTMLFormElement) =>
    rodar(async () => {
      const dados = new FormData(form);
      const criado = await criarEvento({
        track_id: String(dados.get("track_id")),
        name: String(dados.get("name")),
        tipo: String(dados.get("tipo") || "") || null,
        starts_at: new Date(String(dados.get("starts_at"))).toISOString(),
      });
      eventos.recarregar();
      sessoes.recarregar();
      setEvento(criado.id);
      setPassoForcado(null);
    });

  const salvarEvento = (form: HTMLFormElement) =>
    rodar(async () => {
      if (!eventoId) return;
      const dados = new FormData(form);
      await editarEvento(eventoId, {
        track_id: String(dados.get("track_id")),
        name: String(dados.get("name")),
        tipo: String(dados.get("tipo") || "") || null,
        starts_at: new Date(String(dados.get("starts_at"))).toISOString(),
      });
      eventos.recarregar();
    });

  const novaSessao = (form: HTMLFormElement) =>
    rodar(async () => {
      const dados = new FormData(form);
      const inicio = String(dados.get("starts_at") || "");
      const fim = String(dados.get("ends_at") || "");
      const criada = await criarSessao(eventoId as string, {
        type: String(dados.get("type")),
        label: String(dados.get("label")),
        starts_at: inicio ? new Date(inicio).toISOString() : null,
        ends_at: fim ? new Date(fim).toISOString() : null,
      });
      sessoes.recarregar();
      setSessao(criada.id);
      setPassoForcado(null);
    });

  const salvarSessao = (form: HTMLFormElement) =>
    rodar(async () => {
      if (!sessaoId) return;
      const dados = new FormData(form);
      const inicio = String(dados.get("starts_at") || "");
      const fim = String(dados.get("ends_at") || "");
      await editarSessao(sessaoId, {
        label: String(dados.get("label")),
        type: String(dados.get("type")),
        starts_at: inicio ? new Date(inicio).toISOString() : null,
        ends_at: fim ? new Date(fim).toISOString() : null,
      });
      sessoes.recarregar();
    });

  const novaBateria = (form: HTMLFormElement) =>
    rodar(async () => {
      const dados = new FormData(form);
      const bruto = String(dados.get("went_out_at") || "");
      const criada = await criarBateria(sessaoId as string, {
        label: String(dados.get("label") || "") || null,
        objective: String(dados.get("objective") || "") || null,
        went_out_at: (bruto ? new Date(bruto) : new Date()).toISOString(),
      });
      baterias.recarregar();
      setBateria(criada.id);
      setPassoForcado(null);
    });

  const salvarBateria = (form: HTMLFormElement) =>
    rodar(async () => {
      if (!bateriaId) return;
      const dados = new FormData(form);
      // campo vazio no numero vira null (apagar valor), nao NaN nem string:
      // o backend so aceita numero ou ausencia do campo
      const numeroOuNulo = (chave: string) => {
        const bruto = dados.get(chave);
        return bruto === null || bruto === "" ? null : Number(bruto);
      };
      await editarBateria(bateriaId, {
        label: String(dados.get("label") || "") || null,
        objective: String(dados.get("objective") || "") || null,
        went_out_at: new Date(String(dados.get("went_out_at"))).toISOString(),
        laps: numeroOuNulo("laps"),
        fuel_out_l: numeroOuNulo("fuel_out_l"),
        fuel_in_l: numeroOuNulo("fuel_in_l"),
      });
      baterias.recarregar();
    });

  const executarExclusao = () =>
    rodar(async () => {
      if (!confirmar) return;
      const { tipo, id } = confirmar;
      if (tipo === "evento") {
        await excluirEvento(id);
        if (id === eventoId) setEvento(null);
      } else if (tipo === "sessao") {
        await excluirSessao(id);
        if (id === sessaoId) setSessao(null);
      } else if (tipo === "bateria") {
        await excluirBateria(id);
        if (id === bateriaId) setBateria(null);
      } else {
        await excluirGravacao(id);
        gravacoes.recarregar();
      }
      eventos.recarregar();
      sessoes.recarregar();
      baterias.recarregar();
      setPassoForcado(null);
      setConfirmar(null);
    });

  const soltar = (gravacaoId: string) =>
    rodar(async () => {
      if (!bateriaId) return;
      await desvincularGravacao(bateriaId, gravacaoId);
      gravacoes.recarregar();
      baterias.recarregar();
    });

  const camposDeEvento = (padrao?: { name: string; track_id: string; starts_at: string | null; tipo?: string | null }) => (
    <>
      <label>
        Nome
        <input name="name" required placeholder="Track day Curitiba" defaultValue={padrao?.name ?? ""} />
      </label>
      <label>
        Tipo
        {/* D2-B: o tipo pre-monta as sessoes do formato (modelo no servidor) */}
        <select name="tipo" defaultValue={padrao?.tipo ?? ""}>
          <option value="">sem formato (sessões manuais)</option>
          <option value="track_day">Track day (Manhã + Tarde)</option>
          <option value="corrida">Corrida (Treino + Classificação + Corrida)</option>
          <option value="teste">Teste</option>
        </select>
      </label>
      <label>
        Pista
        <select name="track_id" required defaultValue={padrao?.track_id ?? ""}>
          <option value="" disabled>escolha o layout</option>
          {(layouts.dado ?? []).map((l) => (
            <option key={l.id} value={l.id}>
              {l.nome}{l.comprimento_m ? ` (${(l.comprimento_m / 1000).toFixed(3)} km)` : ""}
            </option>
          ))}
        </select>
      </label>
      <label>
        Começa em
        <CampoDataHora name="starts_at" required defaultValue={paraInputDatetime(padrao?.starts_at ?? null)} />
      </label>
    </>
  );

  const PASSOS: { id: Passo; rotulo: string; resumo: string | null }[] = [
    { id: "evento", rotulo: "Evento", resumo: evento?.name ?? null },
    { id: "piloto", rotulo: "Piloto", resumo: piloto?.nome ?? null },
    { id: "sessao", rotulo: "Sessão", resumo: sessao ? (sessao.label ?? sessao.type) : null },
    { id: "bateria", rotulo: "Saída pra pista", resumo: bateria ? nomeDoOuting(bateria) : null },
    { id: "pronto", rotulo: "Telemetria", resumo: bateriaId ? `${penduradas.length} arquivo(s)` : null },
  ];

  return (
    <div className="ciclo-area">
    <div className="ciclo">
      {/* A trilha e NAVEGACAO (pedido 2.1): cada passo alcancavel e clicavel
          e abre a lista daquele nivel sem desfazer a escolha atual. */}
      <ol className="ciclo-trilha">
        {PASSOS.map((p) => (
          <li key={p.id} className={passo === p.id ? "atual" : p.resumo ? "feito" : ""}>
            {alcancavel[p.id] ? (
              <button type="button" className="trilha-link" onClick={() => irParaPasso(p.id)}>
                <span className="trilha-rotulo">{p.rotulo}</span>
                {p.resumo && <span className="trilha-resumo">{p.resumo}</span>}
              </button>
            ) : (
              <span className="trilha-morta">
                <span className="trilha-rotulo">{p.rotulo}</span>
              </span>
            )}
          </li>
        ))}
      </ol>

      {modal === null && <Erro e={erro} />}

      {/* --- etapa atual: EVENTO --- */}
      {passo === "evento" && (
        <section className="ciclo-bloco">
          <header>
            <h3>Evento</h3>
            <button type="button" className="criar" onClick={() => setModal("evento")}>+ evento</button>
          </header>
          {eventos.carregando ? (
            <p className="fraco">carregando eventos...</p>
          ) : eventos.dado && eventos.dado.length > 0 ? (
            <ListaPaginada>
              {eventos.dado.map((e) => (
                <li key={e.id}>
                  <button
                    type="button"
                    className={e.id === eventoId ? "escolhido" : ""}
                    onClick={() => { setEvento(e.id); setPassoForcado(null); }}
                  >
                    <span className="t">{e.name}</span>
                    <span className="q">{e.layout_nome ?? e.track_id} · <Data iso={e.starts_at} /></span>
                  </button>
                  {e.id === eventoId && (
                    <button type="button" className="limpar" onClick={() => setModal("editar-evento")}>
                      editar
                    </button>
                  )}
                  <button
                    type="button"
                    className="limpar perigo"
                    onClick={() => setConfirmar({ tipo: "evento", id: e.id, rotulo: e.name })}
                  >
                    excluir
                  </button>
                </li>
              ))}
            </ListaPaginada>
          ) : (
            <p className="fraco">Nenhum evento ainda. Crie o primeiro no botão acima.</p>
          )}
        </section>
      )}

      {/* --- etapa atual: PILOTO (degrau novo, 30/08) --- */}
      {passo === "piloto" && (
        <section className="ciclo-bloco">
          <header>
            <h3>Piloto</h3>
            <span className="ciclo-cabeca-contexto">{evento?.name}</span>
          </header>
          {pilotos.carregando ? (
            <p className="fraco">carregando pilotos...</p>
          ) : pilotos.dado && pilotos.dado.length > 0 ? (
            <ListaPaginada>
              {pilotos.dado.map((p) => {
                // "sem" nao e id: e o balde das sessoes sem piloto declarado,
                // que e como o acervo antigo aparece. Sem esse balde elas
                // sumiriam da tela depois que o filtro por piloto entrou.
                const chave = p.piloto_id ?? "sem";
                return (
                  <li key={chave}>
                    <button
                      type="button"
                      className={chave === pilotoId ? "escolhido" : ""}
                      onClick={() => { setPiloto(chave); setPassoForcado(null); }}
                    >
                      <span className="t">{p.nome}</span>
                      <span className="q">
                        {p.sessoes} sessão(ões) · {p.saidas} saída(s) · {p.voltas} voltas
                        {p.melhor_volta_s != null && ` · melhor ${tempo(p.melhor_volta_s)}`}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ListaPaginada>
          ) : (
            <p className="fraco">Nenhuma sessão neste evento ainda.</p>
          )}
        </section>
      )}

      {/* --- etapa atual: SESSAO --- */}
      {passo === "sessao" && (
        <section className="ciclo-bloco">
          <header>
            <h3>Sessão</h3>
            <span className="ciclo-cabeca-contexto">
              {evento?.name}{piloto ? ` · ${piloto.nome}` : ""}
            </span>
            <button type="button" className="criar" onClick={() => setModal("sessao")}>+ sessão</button>
          </header>
          {sessoes.carregando ? (
            <p className="fraco">carregando sessões...</p>
          ) : sessoesDoPiloto.length > 0 ? (
            <ListaPaginada>
              {sessoesDoPiloto.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    className={s.id === sessaoId ? "escolhido" : ""}
                    onClick={() => { setSessao(s.id); setPassoForcado(null); }}
                  >
                    <span className="t">{s.label ?? s.type}</span>
                    {/* uma sessao E um conjunto de baterias: a contagem delas
                        diz mais que o tipo repetido do rotulo */}
                    <span className="q">{s.baterias ?? 0} saída(s) · {s.voltas ?? 0} voltas</span>
                  </button>
                  {s.id === sessaoId && (
                    <button type="button" className="limpar" onClick={() => setModal("editar-sessao")}>
                      editar
                    </button>
                  )}
                  <button
                    type="button"
                    className="limpar perigo"
                    onClick={() => setConfirmar({ tipo: "sessao", id: s.id, rotulo: s.label ?? "sessão" })}
                  >
                    excluir
                  </button>
                </li>
              ))}
            </ListaPaginada>
          ) : (
            <p className="fraco">Nenhuma sessão neste evento. Crie a primeira no botão acima.</p>
          )}
        </section>
      )}

      {/* --- etapa atual: BATERIA (escolha) --- */}
      {passo === "bateria" && (
        <section className="ciclo-bloco">
          <header>
            <h3>Saídas pra pista</h3>
            <span className="ciclo-cabeca-contexto">
              {evento?.name}{sessao ? ` · ${sessao.label ?? sessao.type}` : ""}
            </span>
            <button type="button" className="criar" onClick={() => setModal("bateria")}>+ saída</button>
          </header>
          {baterias.carregando ? (
            <p className="fraco">carregando baterias...</p>
          ) : baterias.dado && baterias.dado.length > 0 ? (
            <ListaPaginada>
              {baterias.dado.map((b) => (
                <li key={b.id}>
                  <button
                    type="button"
                    className={b.id === bateriaId ? "escolhido" : ""}
                    onClick={() => { setBateria(b.id); setPassoForcado(null); }}
                  >
                    <span className="t">{b.label ? <>{b.label} · <Data iso={b.went_out_at} /></> : <Data iso={b.went_out_at} />}</span>
                    {/* uma bateria E a colecao de voltas que a telemetria dela
                        mediu. Sem telemetria ela existe, mas nao tem conteudo,
                        e a tela diz isso em vez de "0 voltas" */}
                    <span className="q">
                      {b.voltas
                        ? `${b.voltas} voltas${tempo(b.melhor_volta_s) ? ` · melhor ${tempo(b.melhor_volta_s)}` : ""}`
                        : "sem telemetria enviada"}
                    </span>
                  </button>
                  <button
                    type="button"
                    className="limpar perigo"
                    onClick={() =>
                      setConfirmar({ tipo: "bateria", id: b.id, rotulo: b.label ?? `saída das ${hora(b.went_out_at)}` })
                    }
                  >
                    excluir
                  </button>
                </li>
              ))}
            </ListaPaginada>
          ) : (
            <p className="fraco">Nenhuma saída pra pista nesta sessão. Registre no botão acima.</p>
          )}
        </section>
      )}

      {/* --- etapa atual: BATERIA ESCOLHIDA (telemetria + registro do box) --- */}
      {passo === "pronto" && bateria && (
        <section className="ciclo-bloco">
          <header>
            <h3>{bateria.label ?? `Saída das ${hora(bateria.went_out_at)}`}</h3>
            <span className="ciclo-cabeca-contexto">
              {evento?.name}{sessao ? ` · ${sessao.label ?? sessao.type}` : ""}
              {` · saiu às ${hora(bateria.went_out_at)}`}
              {bateria.objective ? ` · ${bateria.objective}` : ""}
              {bateria.voltas
                ? ` · ${bateria.voltas} voltas${tempo(bateria.melhor_volta_s) ? `, melhor ${tempo(bateria.melhor_volta_s)}` : ""}`
                : ""}
            </span>
            <button type="button" className="ghost" onClick={() => setModal("editar-bateria")}>editar</button>
            <button
              type="button"
              className="limpar perigo"
              onClick={() => setConfirmar({ tipo: "bateria", id: bateria.id, rotulo: nomeDoOuting(bateria) })}
            >
              excluir
            </button>
          </header>

          {/* As irmas ficam a um clique, sem passar pela lista: alternar
              entre baterias da mesma sessao e o gesto mais repetido do dia. */}
          {(baterias.dado?.length ?? 0) > 1 && (
            <div className="ciclo-irmas">
              <span className="fraco">outras saídas:</span>
              {baterias.dado!.filter((b) => b.id !== bateriaId).map((b) => (
                <button key={b.id} type="button" className="ghost" onClick={() => setBateria(b.id)}>
                  {nomeDoOuting(b)}{b.voltas ? ` · ${b.voltas} voltas` : ""}
                </button>
              ))}
            </div>
          )}

          <div className="ciclo-duas">
            {/* coluna A: a telemetria desta bateria */}
            <div className="ciclo-coluna">
              <h4>
                Telemetria
                {/* Enviar vira MODAL, no mesmo padrao dos outros cadastros
                    (pedido do Lucas, 30/08): a coluna mostra o que ja existe,
                    e criar coisa nova sempre comeca por um botao "+". Antes o
                    formulario ficava aberto embaixo da lista o tempo todo,
                    ocupando a tela mesmo quando ninguem ia enviar nada. */}
                <button type="button" className="criar" onClick={() => setModal("telemetria")}>
                  + telemetria
                </button>
              </h4>
              {penduradas.length > 0 ? (
                <ListaPaginada compacta>
                  {penduradas.map((g) => (
                    <li key={g.gravacao_id} className="linha-gravacao">
                      <span className="t">
                        {g.label ?? g.layout_nome ?? g.gravacao_id.slice(0, 8)}
                        <span className="q"> · {g.voltas} voltas</span>
                      </span>
                      <span className="acoes">
                        <button
                          type="button"
                          className="limpar"
                          title="Desfaz o vínculo com esta saída pra pista. O arquivo continua no acervo e pode ser pendurado em outra saída."
                          onClick={() => soltar(g.gravacao_id)}
                        >
                          tirar da saída
                        </button>
                        <button
                          type="button"
                          className="limpar perigo"
                          onClick={() => setConfirmar({ tipo: "gravacao", id: g.gravacao_id, rotulo: g.label ?? g.layout_nome ?? "esta telemetria" })}
                        >
                          excluir
                        </button>
                      </span>
                    </li>
                  ))}
                </ListaPaginada>
              ) : (
                <p className="fraco">Nenhum arquivo pendurado ainda.</p>
              )}

            </div>

            {/* coluna B: o registro do box, com estado de preenchimento
                (pedido de 29/08: feedback visual quando preenchido) */}
            <div className="ciclo-coluna">
              <h4>Registro do box</h4>
              {/* Vazio e CONVITE, nao aviso: o cartao ja era clicavel, mas
                  "nao preenchido" em cinza parecia rotulo de estado morto.
                  Em rosa ele diz o que fazer (pedido do Lucas, 30/08). */}
              <button type="button" className={`ciclo-registro${registros > 0 ? " ok" : " falta"}`} onClick={() => setContextoAberto(true)}>
                <span className="cabeca">
                  <span className="nome">Contexto da saída</span>
                  <span className="estado">{registros > 0 ? "✓ preenchido" : "+ adicionar"}</span>
                </span>
                <span className="detalhe">
                  {registros > 0
                    ? `${registros} registro(s) · último às ${hora(contexto.dado![0].criado_em)}`
                    : "pneu, temperaturas, vento e notas da ida à pista"}
                </span>
              </button>
              <button type="button" className={`ciclo-registro${ultimaVersao > 0 ? " ok" : " falta"}`} onClick={() => setSetupAberto(true)}>
                <span className="cabeca">
                  <span className="nome">Configurações do carro</span>
                  <span className="estado">{ultimaVersao > 0 ? `✓ versão ${ultimaVersao}` : "+ adicionar"}</span>
                </span>
                <span className="detalhe">
                  {ultimaVersao > 0
                    ? `${setup.dado!.length} versão(ões) salvas`
                    : "pressões, alturas, asas: o carro com que esta saída foi feita"}
                </span>
              </button>
            </div>
          </div>
        </section>
      )}

      <p className="ciclo-nota">
        Telemetria entra por aqui, pendurada na saída pra pista: é o vínculo com o evento que
        liga a análise ao seu dia de pista e permite comparar dia com dia.
      </p>

      {/* --- modais de cadastro/edicao (pedido de 29/08) --- */}
      <Modal classe="sem-scroll" titulo="Novo evento" aberto={modal === "evento"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); novoEvento(ev.currentTarget); }}>
          {camposDeEvento()}
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Criar evento</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal classe="sem-scroll" titulo="Editar evento" aberto={modal === "editar-evento"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); salvarEvento(ev.currentTarget); }}>
          {evento && camposDeEvento({ name: evento.name, track_id: evento.track_id, starts_at: evento.starts_at, tipo: evento.tipo })}
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Salvar</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal classe="sem-scroll" titulo="Nova sessão" aberto={modal === "sessao"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); novaSessao(ev.currentTarget); }}>
          <label>
            Nome da sessão
            <input name="label" required placeholder="Manhã, Tomada 2, Classificação..." />
          </label>
          <label>
            Tipo
            <select name="type" required defaultValue="trackday_battery">
              <option value="trackday_battery">Track day</option>
              <option value="practice">Treino</option>
            </select>
          </label>
          <label>
            Janela: começa
            <CampoDataHora name="starts_at" />
          </label>
          <label>
            Janela: termina
            <CampoDataHora name="ends_at" rotulo="Data do fim" />
          </label>
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Criar sessão</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal classe="sem-scroll" titulo="Editar sessão" aberto={modal === "editar-sessao"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); salvarSessao(ev.currentTarget); }}>
          <label>
            Nome da sessão
            <input name="label" required defaultValue={sessao?.label ?? ""} />
          </label>
          <label>
            Tipo
            <select name="type" required defaultValue={sessao?.type ?? "trackday_battery"}>
              <option value="trackday_battery">Track day</option>
              <option value="practice">Treino</option>
            </select>
          </label>
          <label>
            Janela: começa
            <CampoDataHora name="starts_at" defaultValue={paraInputDatetime(sessao?.starts_at ?? null)} />
          </label>
          <label>
            Janela: termina
            <CampoDataHora name="ends_at" rotulo="Data do fim" defaultValue={paraInputDatetime(sessao?.ends_at ?? null)} />
          </label>
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Salvar</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal classe="sem-scroll" titulo="Nova saída pra pista" aberto={modal === "bateria"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); novaBateria(ev.currentTarget); }}>
          <label>
            Nome
            <input name="label" placeholder={`B${(baterias.dado?.length ?? 0) + 1}`} />
          </label>
          <label>
            Objetivo
            <input name="objective" placeholder="acerto de pressão, long run..." />
          </label>
          <label>
            Saída
            {/* default = agora: o horario e da MAQUINA (2.1.5.4), o campo
                existe pra correcao explicita, nao pra digitacao de rotina */}
            <CampoDataHora name="went_out_at" defaultValue={paraInputDatetime(new Date().toISOString())} />
          </label>
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Registrar saída</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      {/* Com a saida ja escolhida, o arquivo entra pendurado nela e, depois de
          processado, abre direto no Box. */}
      <Modal titulo="Enviar telemetria" aberto={modal === "telemetria"} aoFechar={() => setModal(null)}>
        <EnvioDeTelemetria aoConcluir={() => { baterias.recarregar(); setModal(null); }} />
      </Modal>

      <Modal classe="sem-scroll" titulo="Editar saída pra pista" aberto={modal === "editar-bateria"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); salvarBateria(ev.currentTarget); }}>
          <CamposPaginados
            paginas={[
              {
                titulo: "Identificação",
                campos: (
                  <>
                    <label>
                      Nome
                      <input name="label" defaultValue={bateria?.label ?? ""} />
                    </label>
                    <label>
                      Objetivo
                      <input name="objective" defaultValue={bateria?.objective ?? ""} />
                    </label>
                    <label>
                      Saída
                      <CampoDataHora name="went_out_at" required defaultValue={paraInputDatetime(bateria?.went_out_at ?? null)} />
                    </label>
                  </>
                ),
              },
              {
                titulo: "Números da saída",
                campos: (
                  <>
                    <label>
                      Voltas
                      <input name="laps" type="number" min={0} step={1} defaultValue={bateria?.laps ?? ""} />
                    </label>
                    <label>
                      Litros na saída
                      <input name="fuel_out_l" type="number" min={0} step={0.1} defaultValue={bateria?.fuel_out_l ?? ""} />
                    </label>
                    <label>
                      Litros na volta
                      <input name="fuel_in_l" type="number" min={0} step={0.1} defaultValue={bateria?.fuel_in_l ?? ""} />
                    </label>
                  </>
                ),
              },
            ]}
          />
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Salvar</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>
      <Modal
        titulo={confirmar ? `Excluir ${confirmar.rotulo}?` : "Excluir"}
        aberto={confirmar !== null}
        aoFechar={() => setConfirmar(null)}
      >
        {confirmar && (
          <div className="ciclo-form">
            <p className="ciclo-nota" style={{ margin: 0 }}>
              {confirmar.tipo === "gravacao"
                ? "A telemetria e tudo que deriva dela (voltas, trechos, análises) serão apagados. Não dá para desfazer."
                : confirmar.tipo === "bateria"
                ? "A saída, o contexto e as configurações do carro dela serão apagados. A telemetria pendurada NÃO é apagada: vira arquivo solto."
                : confirmar.tipo === "sessao"
                ? "A sessão e as saídas dela serão apagadas (com contexto e configurações do carro). As telemetrias NÃO são apagadas: viram arquivos soltos."
                : "O evento, as sessões e as saídas dele serão apagados (com contexto e configurações do carro). As telemetrias NÃO são apagadas: viram arquivos soltos."}
            </p>
            <Erro e={erro} />
            <div className="ciclo-acoes">
              <button type="button" className="perigoso" disabled={criando} onClick={executarExclusao}>
                Excluir
              </button>
              <button type="button" className="ghost" onClick={() => setConfirmar(null)}>Cancelar</button>
            </div>
          </div>
        )}
      </Modal>

      {/* Contexto e ficha moram AQUI (alem do Analyzer) porque o dia de pista
          existe antes do primeiro relatorio: sem isto os botoes do registro do
          box nao abriam nada na conta recem-criada. Ao fechar, o estado de
          preenchimento recarrega, senao o "✓" so aparecia no F5. */}
      {bateriaId && (
        <>
          <ContextoDaBateria
            aberta={contextoAberto}
            dono="baterias"
            alvoId={bateriaId}
            layoutId={evento?.track_id ?? null}
            onFechar={() => { setContextoAberto(false); contexto.recarregar(); }}
          />
          <FichaDeSetup
            aberta={setupAberto}
            dono="baterias"
            alvoId={bateriaId}
            onFechar={() => { setSetupAberto(false); setup.recarregar(); }}
          />
        </>
      )}
    </div>
    </div>
  );
}
