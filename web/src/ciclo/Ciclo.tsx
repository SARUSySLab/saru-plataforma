import { useState } from "react";
import "../estilo/ciclo.css";
import { useSelecao } from "../state/selection";
import { useBaterias, useEventos, useLayouts, useSessoes } from "./useEspinha";
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

type Passo = "evento" | "sessao" | "bateria" | "pronto";
type ModalAberto =
  | null | "evento" | "editar-evento" | "sessao" | "editar-sessao" | "bateria" | "editar-bateria";

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
  return b.label ?? `outing das ${hora(b.went_out_at)}`;
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

export function Ciclo() {
  const {
    eventoId, sessaoId, bateriaId, setEvento, setSessao, setBateria,
    contextoAberto, setContextoAberto, setupAberto, setSetupAberto,
  } = useSelecao();
  const eventos = useEventos();
  const layouts = useLayouts();
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
  const passoNatural: Passo = !eventoId ? "evento" : !sessaoId ? "sessao" : !bateriaId ? "bateria" : "pronto";
  const passo: Passo = passoForcado ?? passoNatural;

  const evento = eventos.dado?.find((e) => e.id === eventoId) ?? null;
  const sessao = sessoes.dado?.find((s) => s.id === sessaoId) ?? null;
  const bateria = baterias.dado?.find((b) => b.id === bateriaId) ?? null;

  const alcancavel: Record<Passo, boolean> = {
    evento: true,
    sessao: eventoId !== null,
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
        <input name="starts_at" type="datetime-local" required defaultValue={paraInputDatetime(padrao?.starts_at ?? null)} />
      </label>
    </>
  );

  const PASSOS: { id: Passo; rotulo: string; resumo: string | null }[] = [
    { id: "evento", rotulo: "Evento", resumo: evento?.name ?? null },
    { id: "sessao", rotulo: "Sessão", resumo: sessao ? (sessao.label ?? sessao.type) : null },
    { id: "bateria", rotulo: "Outing", resumo: bateria ? nomeDoOuting(bateria) : null },
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
            <ul className="ciclo-lista">
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
            </ul>
          ) : (
            <p className="fraco">Nenhum evento ainda. Crie o primeiro no botão acima.</p>
          )}
        </section>
      )}

      {/* --- etapa atual: SESSAO --- */}
      {passo === "sessao" && (
        <section className="ciclo-bloco">
          <header>
            <h3>Sessão</h3>
            <span className="ciclo-cabeca-contexto">{evento?.name}</span>
            <button type="button" className="criar" onClick={() => setModal("sessao")}>+ sessão</button>
          </header>
          {sessoes.carregando ? (
            <p className="fraco">carregando sessões...</p>
          ) : sessoes.dado && sessoes.dado.length > 0 ? (
            <ul className="ciclo-lista">
              {sessoes.dado.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    className={s.id === sessaoId ? "escolhido" : ""}
                    onClick={() => { setSessao(s.id); setPassoForcado(null); }}
                  >
                    <span className="t">{s.label ?? s.type}</span>
                    {/* uma sessao E um conjunto de baterias: a contagem delas
                        diz mais que o tipo repetido do rotulo */}
                    <span className="q">{s.baterias ?? 0} outing(s) · {s.voltas ?? 0} voltas</span>
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
            </ul>
          ) : (
            <p className="fraco">Nenhuma sessão neste evento. Crie a primeira no botão acima.</p>
          )}
        </section>
      )}

      {/* --- etapa atual: BATERIA (escolha) --- */}
      {passo === "bateria" && (
        <section className="ciclo-bloco">
          <header>
            <h3>Outing</h3>
            <span className="ciclo-cabeca-contexto">
              {evento?.name}{sessao ? ` · ${sessao.label ?? sessao.type}` : ""}
            </span>
            <button type="button" className="criar" onClick={() => setModal("bateria")}>+ outing</button>
          </header>
          {baterias.carregando ? (
            <p className="fraco">carregando baterias...</p>
          ) : baterias.dado && baterias.dado.length > 0 ? (
            <ul className="ciclo-lista">
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
                      setConfirmar({ tipo: "bateria", id: b.id, rotulo: b.label ?? `outing das ${hora(b.went_out_at)}` })
                    }
                  >
                    excluir
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="fraco">Nenhum outing nesta sessão. Registre a saída no botão acima.</p>
          )}
        </section>
      )}

      {/* --- etapa atual: BATERIA ESCOLHIDA (telemetria + registro do box) --- */}
      {passo === "pronto" && bateria && (
        <section className="ciclo-bloco">
          <header>
            <h3>{bateria.label ?? `Outing das ${hora(bateria.went_out_at)}`}</h3>
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
              <span className="fraco">outros outings:</span>
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
              <h4>Telemetria</h4>
              {penduradas.length > 0 ? (
                <ul className="ciclo-lista compacta">
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
                          title="Solta o arquivo deste outing sem apagar nada"
                          onClick={() => soltar(g.gravacao_id)}
                        >
                          soltar
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
                </ul>
              ) : (
                <p className="fraco">Nenhum arquivo pendurado ainda.</p>
              )}

              {/* Enviar telemetria AQUI, com a bateria ja escolhida, e o caminho
                  do dia de pista: o arquivo entra pendurado nela e, processado,
                  abre direto no Box. */}
              <div className="ciclo-envio">
                <EnvioDeTelemetria aoConcluir={() => baterias.recarregar()} />
              </div>
            </div>

            {/* coluna B: o registro do box, com estado de preenchimento
                (pedido de 29/08: feedback visual quando preenchido) */}
            <div className="ciclo-coluna">
              <h4>Registro do box</h4>
              <button type="button" className={`ciclo-registro${registros > 0 ? " ok" : ""}`} onClick={() => setContextoAberto(true)}>
                <span className="cabeca">
                  <span className="nome">Contexto do outing</span>
                  <span className="estado">{registros > 0 ? "✓ preenchido" : "não preenchido"}</span>
                </span>
                <span className="detalhe">
                  {registros > 0
                    ? `${registros} registro(s) · último às ${hora(contexto.dado![0].criado_em)}`
                    : "pneu, temperaturas, vento e notas da ida à pista"}
                </span>
              </button>
              <button type="button" className={`ciclo-registro${ultimaVersao > 0 ? " ok" : ""}`} onClick={() => setSetupAberto(true)}>
                <span className="cabeca">
                  <span className="nome">Ficha de setup</span>
                  <span className="estado">{ultimaVersao > 0 ? `✓ versão ${ultimaVersao}` : "não preenchida"}</span>
                </span>
                <span className="detalhe">
                  {ultimaVersao > 0
                    ? `${setup.dado!.length} versão(ões) salvas`
                    : "pressões, alturas, asas: o carro com que este outing saiu"}
                </span>
              </button>
            </div>
          </div>
        </section>
      )}

      <p className="ciclo-nota">
        Telemetria entra por aqui, pendurada no outing: é o vínculo com o evento que
        liga a análise ao seu dia de pista e permite comparar dia com dia.
      </p>

      {/* --- modais de cadastro/edicao (pedido de 29/08) --- */}
      <Modal titulo="Novo evento" aberto={modal === "evento"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); novoEvento(ev.currentTarget); }}>
          {camposDeEvento()}
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Criar evento</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal titulo="Editar evento" aberto={modal === "editar-evento"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); salvarEvento(ev.currentTarget); }}>
          {evento && camposDeEvento({ name: evento.name, track_id: evento.track_id, starts_at: evento.starts_at, tipo: evento.tipo })}
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Salvar</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal titulo="Nova sessão" aberto={modal === "sessao"} aoFechar={() => setModal(null)}>
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
            <input name="starts_at" type="datetime-local" />
          </label>
          <label>
            Janela: termina
            <input name="ends_at" type="datetime-local" />
          </label>
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Criar sessão</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal titulo="Editar sessão" aberto={modal === "editar-sessao"} aoFechar={() => setModal(null)}>
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
            <input name="starts_at" type="datetime-local" defaultValue={paraInputDatetime(sessao?.starts_at ?? null)} />
          </label>
          <label>
            Janela: termina
            <input name="ends_at" type="datetime-local" defaultValue={paraInputDatetime(sessao?.ends_at ?? null)} />
          </label>
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Salvar</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal titulo="Novo outing: saída para a pista" aberto={modal === "bateria"} aoFechar={() => setModal(null)}>
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
            <input name="went_out_at" type="datetime-local" defaultValue={paraInputDatetime(new Date().toISOString())} />
          </label>
          <Erro e={erro} />
          <div className="ciclo-acoes">
            <button type="submit" className="primario" disabled={criando}>Registrar outing</button>
            <button type="button" className="ghost" onClick={() => setModal(null)}>Cancelar</button>
          </div>
        </form>
      </Modal>

      <Modal titulo="Editar outing" aberto={modal === "editar-bateria"} aoFechar={() => setModal(null)}>
        <form className="ciclo-form" onSubmit={(ev) => { ev.preventDefault(); salvarBateria(ev.currentTarget); }}>
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
            <input name="went_out_at" type="datetime-local" required defaultValue={paraInputDatetime(bateria?.went_out_at ?? null)} />
          </label>
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
                ? "O outing, o contexto e a ficha de setup dele serão apagados. A telemetria pendurada NÃO é apagada: vira arquivo solto."
                : confirmar.tipo === "sessao"
                ? "A sessão e os outings dela serão apagados (com contexto e setup). As telemetrias NÃO são apagadas: viram arquivos soltos."
                : "O evento, as sessões e os outings dele serão apagados (com contexto e setup). As telemetrias NÃO são apagadas: viram arquivos soltos."}
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
