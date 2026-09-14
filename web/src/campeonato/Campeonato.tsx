import { useEffect, useMemo, useRef, useState } from "react";
import "../estilo/campeonato.css";
import {
  eventosLt,
  estadoDoEvento,
  streamDoEvento,
  tracadoDoEvento,
  type EstadoLt,
  type EventoLt,
  type ResultadoLt,
  type TracadoLt,
} from "../services/campeonato";
import { tempo } from "../dados/formato";
import { climaDoLayout, type Clima } from "../services/clima";

// A visao de campeonato (decisoes do Lucas, 29/08). E o zoom mais aberto do
// sistema: o autodromo inteiro, nao a volta de um piloto. Tres peças:
// leaderboard (a cronometragem como ela e), mapa ao vivo (estilo HH Timing) e
// clima. A fonte e o XML resultspage que o Orbits streama na rede local,
// chegando aqui por relay + SSE.
//
// REGRA DE HONESTIDADE do mapa: o XML nao tem GPS. A posicao de cada carro e
// ESTIMADA por cronometragem (tempo desde a ultima passagem na linha dividido
// pelo ritmo esperado, projetado sobre o traçado de referencia do acervo), que
// e exatamente como paineis de timing animam carro sem telemetria. A tela
// declara a estimativa em vez de fingir GPS; carro ha muito sem passar no loop
// vai pro box em vez de vagar pela pista fantasma.

/** Paleta por classe: 9 classes no MBR, cores estaveis por ordem alfabetica. */
const CORES_CLASSE = [
  "#e5484d", "#0091ff", "#f5a524", "#30a46c", "#8e4ec6",
  "#00b8d9", "#e93d82", "#946800", "#5b5bd6", "#688464",
];

function corDaClasse(classe: string | null, classes: string[]): string {
  if (!classe) return "#8b8b8b";
  const i = classes.indexOf(classe);
  return i >= 0 ? CORES_CLASSE[i % CORES_CLASSE.length] : "#8b8b8b";
}

/** Ritmo esperado do carro, na ordem do que mente menos: a ultima volta e o
 * presente, a media segura o treino todo, a melhor e o piso otimista. */
function ritmoEsperado(r: ResultadoLt): number | null {
  return r.ultima_volta_s ?? r.media_s ?? r.melhor_volta_s;
}

/** Total de setores da volta, inferido do carro mais adiantado do grid: as
 * chaves sao s1..sN, o maior indice visto e o N. Usado tanto pelo mapa
 * (estimar posicao) quanto pelo calculo de trafego (mesmo modelo de posicao). */
function calcularNSetGrid(resultados: ResultadoLt[]): number {
  return resultados.reduce((max, r) => {
    for (const c of [...Object.keys(r.melhores_setores ?? {}), ...Object.keys(r.setores ?? {})]) {
      const i = parseInt(c.slice(1), 10);
      if (Number.isFinite(i) && i > max) max = i;
    }
    return max;
  }, 0);
}

/** Segundos do dia -> "HH:MM:SS", pro relogio da pista. */
function fmtTod(s: number): string {
  const t = Math.max(0, Math.floor(s)) % 86400;
  const h = Math.floor(t / 3600), m = Math.floor((t % 3600) / 60), seg = t % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(seg).padStart(2, "0")}`;
}

const BANDEIRAS: Record<string, { rotulo: string; classe: string }> = {
  // rotulo era "pista livre" ate 29/08: colidia com o sentido novo do termo
  // (trafego livre a frente do carro, calculado por carro na leaderboard).
  // A bandeira verde agora se chama pelo que ela e.
  green: { rotulo: "bandeira verde", classe: "pill-ok" },
  yellow: { rotulo: "amarela", classe: "pill-warn" },
  red: { rotulo: "vermelha", classe: "pill-warn" },
  finish: { rotulo: "quadriculada", classe: "pill-brand" },
};

export function Campeonato() {
  const [eventos, setEventos] = useState<EventoLt[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [eventoId, setEventoId] = useState<string | null>(null);
  const [estado, setEstado] = useState<EstadoLt | null>(null);
  const [tracado, setTracado] = useState<TracadoLt | null>(null);
  const [aoVivo, setAoVivo] = useState(false);
  const [filtroClasse, setFiltroClasse] = useState<string>("");
  // instante local (performance.now) em que o snapshot corrente chegou: e a
  // ancora da animacao, o relogio da cronometragem anda a partir dele
  const recebidoEmLocal = useRef<number>(0);
  // Relogio da pista com ANCORA ESTAVEL. Re-ancorar a cada snapshot (2 s) e
  // amostrar com tick de 1 s batia fora de fase: o segundo repetia e depois
  // pulava 2 (medido pelo Lucas em 29/08). A ancora so muda quando deriva
  // mais de 1.5 s do relogio corrente, e o tick e de 250 ms pra virada de
  // segundo nunca ser perdida pela amostragem.
  const relogioRef = useRef<{ tod0: number; perf0: number } | null>(null);
  const ancorarRelogio = (todSnapshot: number | null) => {
    if (todSnapshot == null) return;
    const r = relogioRef.current;
    const corrente = r ? r.tod0 + (performance.now() - r.perf0) / 1000 : null;
    if (corrente == null || Math.abs(corrente - todSnapshot) > 1.5) {
      relogioRef.current = { tod0: todSnapshot, perf0: performance.now() };
    }
  };
  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((n) => n + 1), 250);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const buscar = () =>
      eventosLt()
        .then((lista) => {
          setEventos(lista);
          // o mais recente primeiro (ordem do servidor); sem escolha previa,
          // abre nele. A escolha do usuario nunca e trocada por baixo.
          if (lista.length > 0) setEventoId((atual) => atual ?? lista[0].id);
        })
        .catch((e: Error) => setErro(e.message));
    buscar();
    // a lista se renova sozinha: evento novo comecando (um simulado, a
    // proxima bateria do dia) aparece no seletor sem F5 (caso real de 29/08,
    // a aba aberta nao via o evento recem-criado)
    const id = setInterval(buscar, 30_000);
    return () => clearInterval(id);
  }, []);

  // SSE com degradacao pra poll: o EventSource reconecta sozinho; se ele
  // desistir (CLOSED), cai pra GET de 5 em 5 s ate a pagina recarregar.
  useEffect(() => {
    if (!eventoId) return;
    let poll: ReturnType<typeof setInterval> | null = null;
    const receber = (novo: EstadoLt) => {
      recebidoEmLocal.current = performance.now();
      ancorarRelogio(novo.snapshot?.timeofday_s ?? null);
      setEstado(novo);
    };
    const fechar = streamDoEvento(eventoId, (novo) => {
      setAoVivo(true);
      receber(novo);
    }, () => {
      setAoVivo(false);
      if (!poll) {
        poll = setInterval(() => {
          estadoDoEvento(eventoId).then(receber).catch(() => undefined);
        }, 5000);
      }
    });
    return () => {
      fechar();
      if (poll) clearInterval(poll);
    };
  }, [eventoId]);

  // o traçado so muda quando o layout resolve, nao a cada snapshot
  const layoutId = estado?.evento.layout_id ?? null;
  useEffect(() => {
    if (!eventoId) return;
    tracadoDoEvento(eventoId).then(setTracado).catch(() => setTracado(null));
  }, [eventoId, layoutId]);

  // trafego por carro: uma vez por snapshot (nao a cada tick de 250ms do
  // relogio), usando o timeofday CRU do snapshot. O componente pai calcula
  // pra nao repetir a conta em cada linha da leaderboard no render. Hook
  // precisa ficar ANTES dos returns condicionais abaixo (regra dos hooks);
  // sem snapshot ainda, roda sobre lista vazia e devolve mapa vazio.
  const resultadosParaTrafego = estado?.snapshot?.resultados ?? [];
  const todParaTrafego = estado?.snapshot?.timeofday_s ?? 0;
  const trafego = useMemo(
    () => calcularTrafego(resultadosParaTrafego, todParaTrafego, calcularNSetGrid(resultadosParaTrafego)),
    [resultadosParaTrafego, todParaTrafego]
  );

  if (erro) {
    return (
      <div className="estado-vazio">
        <h2>Campeonato indisponível</h2>
        <p>{erro}</p>
      </div>
    );
  }
  if (eventos && eventos.length === 0) {
    return (
      <div className="estado-vazio">
        <h2>Nenhuma cronometragem recebida</h2>
        <p>
          A visão de campeonato liga quando o relay da pista começar a postar o live
          timing (XML do Orbits/MyLaps). Crie um usuário máquina e rode
          <code> scripts/relay_livetiming.py</code> na rede local do autódromo.
        </p>
      </div>
    );
  }
  if (!estado?.snapshot) {
    return <div className="estado-vazio"><h2>Carregando cronometragem…</h2></div>;
  }

  const snap = estado.snapshot;
  const resultados = snap.resultados;
  const classes = [...new Set(resultados.map((r) => r.classe).filter((c): c is string => !!c))].sort();
  const visiveis = filtroClasse ? resultados.filter((r) => r.classe === filtroClasse) : resultados;
  const bandeira = snap.flag && snap.flag !== "none" ? BANDEIRAS[snap.flag] ?? { rotulo: snap.flag, classe: "pill-warn" } : null;

  return (
    <div className="campeonato">
      <div className="camp-cabeca">
        <div className="camp-titulo">
          {/* o titulo E o seletor de evento (pedido de 29/08: nome duplicado
              em titulo + dropdown era ruido). Com um evento so, vira texto. */}
          {eventos && eventos.length > 1 ? (
            <select
              className="camp-titulo-sel"
              value={eventoId ?? ""}
              onChange={(e) => { setEstado(null); relogioRef.current = null; setEventoId(e.target.value); }}
              aria-label="Evento de cronometragem"
              title="Trocar de evento"
            >
              {eventos.map((ev) => (
                <option key={ev.id} value={ev.id}>{ev.nome} ({ev.run_nome})</option>
              ))}
            </select>
          ) : (
            <h2>{estado.evento.nome}</h2>
          )}
          <p className="meta">
            {estado.evento.grupo ? `${estado.evento.grupo} · ` : ""}
            {estado.evento.pista_nome ?? "pista não identificada"}
            {estado.evento.track_length_m ? ` · ${(estado.evento.track_length_m / 1000).toFixed(3)} km` : ""}
            {snap.labels.bestlaptime ? ` · melhor do dia ${snap.labels.bestlaptime} (${snap.labels.bestlapby ?? "?"})` : ""}
          </p>
        </div>
        <div className="espaco" />
        {bandeira && <span className={`pill ${bandeira.classe}`}>{bandeira.rotulo}</span>}
        <span className={`pill ${aoVivo ? "pill-ok" : "pill-warn"}`}>
          {aoVivo ? "ao vivo" : "atualizando por poll"}
        </span>
        {relogioRef.current != null ? (
          <span className="pill">
            {fmtTod(relogioRef.current.tod0 + (performance.now() - relogioRef.current.perf0) / 1000)} na pista
          </span>
        ) : (
          snap.timeofday && <span className="pill">{snap.timeofday} na pista</span>
        )}
      </div>

      <div className="camp-grade">
        <article className="cartao camp-leaderboard">
          <header>
            <h4>Leaderboard</h4>
            <span className="no">{visiveis.length} de {resultados.length} carros</span>
            <div className="espaco" />
            <div className="camp-campo">
              <span className="k">Classe</span>
              <select value={filtroClasse} onChange={(e) => setFiltroClasse(e.target.value)} aria-label="Filtro de classe">
                <option value="">todas</option>
                {classes.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </header>
          {/* legenda das classes (pedido de 29/08): a borda colorida de cada
              linha so significa algo se a cor tiver nome ao lado. Compacta,
              uma linha so, pra nao empurrar a tabela pra fora do cartao. */}
          {classes.length > 0 && (
            <div className="camp-lb-legenda">
              {classes.map((c) => (
                <span key={c}>
                  <i style={{ background: corDaClasse(c, classes) }} />
                  {c}
                </span>
              ))}
            </div>
          )}
          <Leaderboard resultados={visiveis} classes={classes} porClasse={!!filtroClasse} trafego={trafego} />
        </article>

        <div className="camp-direita">
          <MapaAoVivo
            tracado={tracado}
            resultados={visiveis}
            classes={classes}
            snapTod={snap.timeofday_s}
            recebidoEmLocal={recebidoEmLocal}
          />
          <CartaoClima layoutId={layoutId} />
        </div>
      </div>
    </div>
  );
}

/**
 * Grade compacta estilo painel de autodromo (requisitos de 29/08): a visao
 * INTEIRA cabe numa tela, sem scroll; UMA coluna sempre (o modo de duas
 * colunas foi abandonado a pedido, espremia o nome e escondia a parcial); e
 * acima de 14 atletas o quadro PAGINA e troca de pagina sozinho a cada 5 s,
 * com setas manuais nos cantos. A altura do corpo e MEDIDA (ResizeObserver),
 * nao estimada.
 */
const ATLETAS_POR_PAGINA_MAX = 14;
const TROCA_DE_PAGINA_MS = 5000;

function Leaderboard({ resultados, classes, porClasse, trafego }: {
  resultados: ResultadoLt[];
  classes: string[];
  porClasse: boolean;
  trafego: Map<string, InfoTrafego>;
}) {
  const corpoRef = useRef<HTMLDivElement>(null);
  const [corpoH, setCorpoH] = useState(0);
  useEffect(() => {
    const el = corpoRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setCorpoH(el.clientHeight));
    ro.observe(el);
    setCorpoH(el.clientHeight);
    return () => ro.disconnect();
  }, []);

  // melhor pessoal por carro, do render anterior: quando o novo snapshot traz
  // um tempo MENOR, o carro entra no conjunto que pisca verde (pedido de
  // 29/08). O primeiro tempo visto nao pisca: nao ha marca anterior batida.
  const melhoresRef = useRef(new Map<string, number>());
  const [comMelhora, setComMelhora] = useState<Set<string>>(new Set());
  // mesma mecanica pra POSICAO: quem subiu ganha uma setinha verde por uns
  // segundos, quem desceu uma vermelha (pedidos de 29/08)
  const posicoesRef = useRef(new Map<string, number>());
  const [comSubida, setComSubida] = useState<Set<string>>(new Set());
  const [comDescida, setComDescida] = useState<Set<string>>(new Set());
  useEffect(() => {
    const melhoraram: string[] = [];
    const subiram: string[] = [];
    const desceram: string[] = [];
    for (const r of resultados) {
      if (r.melhor_volta_s != null) {
        const anterior = melhoresRef.current.get(r.numero);
        if (anterior != null && r.melhor_volta_s < anterior - 0.0005) melhoraram.push(r.numero);
        melhoresRef.current.set(r.numero, r.melhor_volta_s);
      }
      if (r.posicao != null) {
        const anterior = posicoesRef.current.get(r.numero);
        if (anterior != null && r.posicao < anterior) subiram.push(r.numero);
        if (anterior != null && r.posicao > anterior) desceram.push(r.numero);
        posicoesRef.current.set(r.numero, r.posicao);
      }
    }
    const timers: ReturnType<typeof setTimeout>[] = [];
    if (melhoraram.length) {
      setComMelhora((atual) => new Set([...atual, ...melhoraram]));
      timers.push(setTimeout(() => {
        setComMelhora((atual) => {
          const proximo = new Set(atual);
          for (const numero of melhoraram) proximo.delete(numero);
          return proximo;
        });
      }, 2600));
    }
    if (subiram.length) {
      setComSubida((atual) => new Set([...atual, ...subiram]));
      timers.push(setTimeout(() => {
        setComSubida((atual) => {
          const proximo = new Set(atual);
          for (const numero of subiram) proximo.delete(numero);
          return proximo;
        });
      }, 5000));
    }
    if (desceram.length) {
      setComDescida((atual) => new Set([...atual, ...desceram]));
      timers.push(setTimeout(() => {
        setComDescida((atual) => {
          const proximo = new Set(atual);
          for (const numero of desceram) proximo.delete(numero);
          return proximo;
        });
      }, 5000));
    }
    return () => timers.forEach(clearTimeout);
  }, [resultados]);

  const n = Math.max(1, resultados.length);

  // paginacao: navegacao manual (setas nos cantos) segura o rodizio por uns
  // segundos, quem clicou quer LER aquela pagina
  const [pagina, setPagina] = useState(0);
  const pausaAteRef = useRef(0);

  // altura util do corpo: reserva a faixa do indicador quando paginado
  const paginadoProvavel = n > ATLETAS_POR_PAGINA_MAX;
  const alturaCorpo = Math.max(120, corpoH - (paginadoProvavel ? 22 : 0));
  // linha entre 18 e 26px: a maior em que a pagina cheia (ou o grid inteiro,
  // se menor) cabe; -1 desconta a linha de cabecalho
  const cabem = (linha: number) => Math.max(1, Math.floor(alturaCorpo / linha) - 1);
  let linha = 26;
  while (linha > 18 && cabem(linha) < Math.min(n, ATLETAS_POR_PAGINA_MAX)) linha -= 2;
  const porPagina = Math.min(ATLETAS_POR_PAGINA_MAX, cabem(linha));
  const paginado = n > porPagina;
  const totalPaginas = Math.max(1, Math.ceil(n / porPagina));
  const paginaAtual = ((pagina % totalPaginas) + totalPaginas) % totalPaginas;
  const visiveis = paginado
    ? resultados.slice(paginaAtual * porPagina, (paginaAtual + 1) * porPagina)
    : resultados;

  useEffect(() => {
    if (totalPaginas <= 1) return;
    const id = setInterval(() => {
      if (Date.now() < pausaAteRef.current) return;
      setPagina((pg) => pg + 1);
    }, TROCA_DE_PAGINA_MS);
    return () => clearInterval(id);
  }, [totalPaginas]);
  const navegar = (delta: number) => {
    pausaAteRef.current = Date.now() + 10_000;
    setPagina((pg) => pg + delta);
  };

  // Delta instantaneo por setor (pedido de 29/08): a cronometragem atualiza
  // por PARCIAL, e uma parcial verde nao garante acumulado melhor no fim da
  // volta. A referencia e o acumulado dos MELHORES setores do lider em tela
  // (P1 geral, ou P1 da classe quando filtrado): parcial do carro ate o
  // setor k contra a soma s1..sk do lider. Negativo = mais rapido ate ali.
  const lider = resultados.find((r) => ((porClasse ? r.posicao_classe : r.posicao) ?? 0) === 1);
  const parcialDe = (r: ResultadoLt): { rotulo: string; delta: number } | null => {
    if (!lider || r === lider) return null;
    const chaves = Object.keys(r.setores ?? {}).filter((c) => r.setores[c] != null).sort();
    if (chaves.length === 0) return null;
    let acumulado = 0;
    let referencia = 0;
    for (const c of chaves) {
      const ref = lider.melhores_setores?.[c];
      if (ref == null) return null;
      acumulado += r.setores[c];
      referencia += ref;
    }
    return { rotulo: `S${chaves.length}`, delta: acumulado - referencia };
  };

  return (
    <div ref={corpoRef} className="camp-lb-corpo">
      <div className="camp-lb" style={{ "--lb-linha": `${linha}px` } as React.CSSProperties}>
        <div className="camp-lb-col">
          <div className="camp-lb-l camp-lb-cab">
            <span className="pos">P</span>
            <span className="cno">Nº</span>
            <span className="quem">Piloto</span>
            <span className="vts">V</span>
            <span className="parcial">Parcial</span>
            <span className="ult">Última</span>
            <span className="melhor">Melhor</span>
            <span className="trafego" title="pista livre de verdade: gap pro carro mais proximo, na frente e atras">Ar</span>
            <span className="gap">Líder</span>
          </div>
          {visiveis.map((r) => (
            <div key={r.numero} className="camp-lb-l" style={{ borderLeftColor: corDaClasse(r.classe, classes) }}>
              <span className="num pos">
                {(porClasse ? r.posicao_classe : r.posicao) ?? ""}
                {comSubida.has(r.numero) && (
                  <svg className="camp-sobe" viewBox="0 0 24 24" width="9" height="9" fill="none"
                    stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" aria-label="ganhou posição">
                    <path d="M5 16l7-8 7 8" />
                  </svg>
                )}
                {!comSubida.has(r.numero) && comDescida.has(r.numero) && (
                  <svg className="camp-desce" viewBox="0 0 24 24" width="9" height="9" fill="none"
                    stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" aria-label="perdeu posição">
                    <path d="M5 8l7 8 7-8" />
                  </svg>
                )}
              </span>
              <span className="num cno">{r.numero}</span>
              <span className="quem" title={`${r.nome}${r.carro ? ` (${r.carro})` : ""} · ${r.classe ?? ""}`}>
                <b>{r.nome}</b>
                {r.carro && <i>{r.carro}</i>}
              </span>
              <span className="num vts">{r.voltas ?? ""}</span>
              <Parcial valor={parcialDe(r)} />
              <span className="num ult">{r.ultima_volta_s != null ? tempo(r.ultima_volta_s) : ""}</span>
              <span className={`num melhor${comMelhora.has(r.numero) ? " pb" : ""}${((porClasse ? r.posicao_classe : r.posicao) ?? 0) === 1 ? " p1" : ""}`}>
                {r.melhor_volta_s != null ? tempo(r.melhor_volta_s) : ""}
              </span>
              <MarcaTrafego info={trafego.get(r.numero)} />
              <span className="num gap">{r.diff ? (/^\d/.test(r.diff) ? `+${r.diff}` : r.diff) : ""}</span>
            </div>
          ))}
        </div>
      </div>
      {paginado && (
        <div className="camp-lb-paginas">
          <button type="button" className="camp-lb-seta" onClick={() => navegar(-1)} aria-label="Página anterior">&lsaquo;</button>
          <span className="centro">
            <span>página {paginaAtual + 1} de {totalPaginas}</span>
            <span className="pontos">
              {Array.from({ length: totalPaginas }, (_, i) => (
                <i key={i} className={i === paginaAtual ? "ativo" : ""} />
              ))}
            </span>
          </span>
          <button type="button" className="camp-lb-seta" onClick={() => navegar(1)} aria-label="Próxima página">&rsaquo;</button>
        </div>
      )}
    </div>
  );
}

/** Chip do delta instantaneo de setor: "S2 -0.312" verde, "S1 +0.084" vermelho. */
function Parcial({ valor }: { valor: { rotulo: string; delta: number } | null }) {
  if (!valor) return <span className="num parcial" />;
  const ganhou = valor.delta < 0;
  return (
    <span className={`num parcial ${ganhou ? "ganha" : "perde"}`}>
      {valor.rotulo} {ganhou ? "" : "+"}{valor.delta.toFixed(3)}
    </span>
  );
}

/**
 * Icone de condicao do tempo: traço monocromatico inline, mesma linguagem do
 * `Icone.tsx` (sem emoji, regra de 29/08: emoji muda por sistema e destoa).
 * A escolha e por palavra-chave sobre o texto que o backend ja normaliza em
 * portugues; condicao desconhecida cai na nuvem, que e o neutro honesto.
 */
function IconeClima({ condicao, tamanho = 16 }: { condicao: string | null; tamanho?: number }) {
  const c = (condicao ?? "").toLowerCase();
  const nuvem = <path d="M7 17h9.5a3.5 3.5 0 0 0 .6-6.95A5 5 0 0 0 7.3 9.1 3.8 3.8 0 0 0 7 17z" />;
  let desenho: React.ReactNode;
  if (c.includes("trovoada")) {
    desenho = <>{nuvem}<polyline points="12 18 10.5 21 13 21 11.5 24" transform="translate(0 -1.5) scale(0.92)" /></>;
  } else if (c.includes("neve") || c.includes("granizo")) {
    desenho = <>{nuvem}<path d="M9 20v.01M12 21.5v.01M15 20v.01" /></>;
  } else if (c.includes("chuva") || c.includes("pancada")) {
    desenho = <>{nuvem}<path d="M9 19.5l-.8 2M12.5 19.5l-.8 2M16 19.5l-.8 2" /></>;
  } else if (c.includes("garoa")) {
    desenho = <>{nuvem}<path d="M10 20v.01M13.5 20.5v.01" /></>;
  } else if (c.includes("névoa") || c.includes("nevoa") || c.includes("nevoeiro") || c.includes("neblina")) {
    desenho = <><path d="M4 10h16M6 14h13M5 18h14" /></>;
  } else if (c.includes("parcial") || c.includes("poucas") || c.includes("predominantemente")) {
    desenho = <><circle cx="9" cy="9" r="3" /><path d="M9 3.5v1M3.5 9h1M5.2 5.2l.7.7" /><path d="M11 18h7a3 3 0 0 0 .4-5.97A4.2 4.2 0 0 0 10.3 11 3.2 3.2 0 0 0 11 18z" /></>;
  } else if (c.includes("limpo") || c.includes("sol") || c.includes("ensolarado")) {
    desenho = (
      <>
        <circle cx="12" cy="12" r="4" />
        <path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M18.4 5.6L17 7M7 17l-1.4 1.4" />
      </>
    );
  } else {
    desenho = nuvem;
  }
  return (
    <svg viewBox="0 0 24 24" width={tamanho} height={tamanho} fill="none" stroke="currentColor"
      strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {desenho}
    </svg>
  );
}

/** Rosa dos ventos em 8 pontos. O angulo e DE ONDE o vento vem. */
const ROSA = ["N", "NE", "L", "SE", "S", "SO", "O", "NO"];
const rosaDoVento = (g: number | null | undefined) =>
  g == null ? null : ROSA[Math.round(g / 45) % 8];

/** Acima disto a chance de chuva muda decisao de pneu, entao muda de cor. */
const CHUVA_ALTA = 40;
const molhado = (p: number | null | undefined) => p != null && p >= CHUVA_ALTA;

/** A fonte que nao entrega probabilidade DECLARA que nao entrega: zero por
 *  cento seria afirmar tempo seco, e ausencia de dado nao e ausencia de chuva. */
function textoChuva(p: number | null | undefined) {
  if (p == null) return "sem dado de chuva nesta fonte";
  return `${p}% de chance de chuva agora`;
}

/**
 * Clima como CARTAO PROPRIO abaixo do mapa (pedido do Lucas, 29/08 noite): a
 * coluna da direita passa a ser duas metades, mapa em cima e clima embaixo.
 * Antes ele era um subcard espremido dentro do cartao do mapa, e a previsao
 * cabia em 4 horas; com metade da coluna cabem 6 e o agora fica legivel de
 * longe, que e como o painel do box e lido.
 * Mesma fonte do backend (`/api/clima/:layout`), mesmo cache de 15 min.
 */
function CartaoClima({ layoutId }: { layoutId: string | null }) {
  const [clima, setClima] = useState<Clima | null>(null);
  const [falha, setFalha] = useState<string | null>(null);
  useEffect(() => {
    if (!layoutId) return;
    let vivo = true;
    const buscar = () =>
      climaDoLayout(layoutId)
        .then((c) => { if (vivo) { setClima(c); setFalha(null); } })
        .catch((e: Error) => { if (vivo) setFalha(e.message); });
    buscar();
    const intervalo = setInterval(buscar, 15 * 60 * 1000);
    return () => { vivo = false; clearInterval(intervalo); };
  }, [layoutId]);

  // Degradacao declarada: sem pista resolvida nao ha coordenada, e sem
  // coordenada nao ha previsao. A tela diz isso em vez de mostrar vazio.
  const moldura = (dentro: React.ReactNode) => (
    <article className="cartao camp-clima-cartao">
      <header>
        <h4>Clima</h4>
        {clima?.condicao_atual && <span className="no">{clima.condicao_atual}</span>}
      </header>
      {dentro}
    </article>
  );

  if (!layoutId) return moldura(<p className="camp-degradado">sem pista resolvida, sem previsão</p>);
  if (falha) return moldura(<p className="camp-degradado">{falha}</p>);
  if (!clima) return moldura(<p className="camp-degradado">buscando a previsão</p>);

  return moldura(
    <div className="camp-clima-corpo">
      <div className="camp-clima-agora" title={clima.condicao_atual ?? undefined}>
        <IconeClima condicao={clima.condicao_atual} tamanho={34} />
        <b>{clima.temperatura_atual_c.toFixed(0)}°C</b>
        <span className="camp-clima-lado">
          <em>{textoChuva(clima.chuva_prob_atual)}</em>
          <i>
            {clima.vento_kmh != null ? `vento ${clima.vento_kmh.toFixed(0)} km/h` : "vento sem dado"}
            {rosaDoVento(clima.vento_dir_graus) && ` de ${rosaDoVento(clima.vento_dir_graus)}`}
            {clima.umidade_pct != null && ` · ${clima.umidade_pct}% de umidade`}
          </i>
          {/* Pista sai SEMPRE marcada como estimativa, com a fonte no title:
              o valor vem de solo modelado, nao de asfalto, e quem le decide
              pressao de pneu com ele. Sem a marca, vira numero cravado. */}
          {clima.pista_estimada_c != null && (
            <i title={`estimado a partir de ${clima.pista_estimada_fonte ?? "solo modelado"}, nao e medida de asfalto`}>
              pista ~{clima.pista_estimada_c.toFixed(0)} °C <u>estimada</u>
            </i>
          )}
        </span>
      </div>
      <div className="camp-horas">
        {clima.previsao_horaria.slice(0, 6).map((h) => (
          <span key={h.horario} title={h.condicao ?? undefined}>
            <em>{h.horario.slice(11, 16)}</em>
            <IconeClima condicao={h.condicao} tamanho={16} />
            <b>{h.temperatura_c.toFixed(0)}°</b>
            <u className={molhado(h.chuva_prob) ? "camp-chuva-alta" : undefined}>
              {h.chuva_prob == null ? "--" : `${h.chuva_prob}%`}
            </u>
          </span>
        ))}
      </div>
    </div>
  );
}

// --- mapa ao vivo -----------------------------------------------------------

/** Onde um carro esta AGORA, no modelo da cronometragem. */
type PosicaoEstimada =
  | { estado: "pista"; frac: number }
  | { estado: "linha"; frac: number } // passou do esperado: segura no limite ate o sensor confirmar
  | { estado: "box" };

function estimar(r: ResultadoLt, agoraTod: number, nSetGrid: number): PosicaoEstimada {
  if (r.ultima_passagem_s == null) return { estado: "box" };

  // SECTOR-AWARE (29/08): quando o evento manda parciais, a ultima passagem e
  // no sensor do setor, nao na linha de chegada. O carro ancora no limite do
  // ultimo setor cruzado e avanca dentro do setor corrente, entao ele aparece
  // no mapa ja na PRIMEIRA parcial da PRIMEIRA volta (antes disso ele nem
  // cruzou sensor, e box e o honesto). Sem dado de setor no evento (MBR),
  // nSet = 1 e a conta degenera pra interpolacao de volta inteira.
  // `nSetGrid` vem do grid todo: um carro novo na pista ainda nao sabe
  // quantos setores a volta tem, mas o resto do grid ja mostrou.
  const nSet = nSetGrid >= 2 ? nSetGrid : 1;

  // ritmo de volta: tempo real quando existe; sem volta fechada ainda, os
  // proprios setores conhecidos estimam (media por setor x total de setores).
  // Era o buraco que deixava carro com parcial na tabela e fora do mapa.
  let ritmo = ritmoEsperado(r);
  if (!ritmo) {
    const chaves = Object.keys(r.melhores_setores ?? {});
    if (chaves.length > 0) {
      const soma = chaves.reduce((acc, c) => acc + r.melhores_setores[c], 0);
      ritmo = (soma / chaves.length) * nSet;
    }
  }
  if (!ritmo) return { estado: "box" };

  const decorrido = agoraTod - r.ultima_passagem_s;
  if (decorrido < 0) return { estado: "box" };
  // 60% alem do ritmo de volta sem passar em sensor nenhum = quase certeza de
  // box (time attack roda em levas; metade do grid do MBR tinha ultima
  // passagem horas antes)
  if (decorrido > ritmo * 1.6) return { estado: "box" };

  const k = nSet > 1
    ? Object.keys(r.setores ?? {}).filter((c) => r.setores[c] != null).length % nSet
    : 0;
  const duracaoSetor = nSet > 1
    ? (r.melhores_setores?.[`s${k + 1}`] ?? ritmo / nSet)
    : ritmo;
  const fSetor = decorrido / duracaoSetor;
  const base = k / nSet;
  const frac = base + Math.min(fSetor, 0.985) / nSet;
  if (fSetor > 0.985) return { estado: "linha", frac };
  return { estado: "pista", frac };
}

/** Marcador de pista livre. Sem dado nao mostra nada e o title diz por que:
 *  mostrar "livre" por falta de informacao seria inventar pista limpa. */
function MarcaTrafego({ info }: { info: InfoTrafego | undefined }) {
  if (!info) return <span className="trafego" title="carro no box, sem posicao em pista" />;
  if (info.estado === "indisponivel") {
    return <span className="trafego" title={`sem estimativa de pista livre: ${info.motivo}`}>?</span>;
  }
  const titulo = `${info.gapFrenteS.toFixed(1)} s pro carro da frente, `
    + `${info.gapAtrasS.toFixed(1)} s pro de tras (estimado pelo ritmo medio do grid)`;
  return (
    <span className={`trafego ${info.estado === "livre" ? "livre" : "preso"}`} title={titulo}>
      <i />
    </span>
  );
}

// --- trafego (pista livre de verdade) ---------------------------------------

/** Abaixo disto o carro mais proximo (na frente ou atras) conta como "preso":
 * gap curto o bastante pra ainda estar respirando o ar sujo do carro da
 * frente ou segurando o de tras. Acima, pista livre pra ele. Constante
 * nomeada porque vira decisao de exibicao, nao so numero solto no meio da
 * conta (pedido de 29/08). */
const LIVRE_S = 5;

/** Resultado do calculo de trafego por carro: livre/preso com os dois gaps
 * (uteis pro title), ou indisponivel com o motivo (degradacao declarada,
 * regra da casa: nunca mostrar "livre" por falta de dado). */
type InfoTrafego =
  | { estado: "livre" | "preso"; gapFrenteS: number; gapAtrasS: number }
  | { estado: "indisponivel"; motivo: string };

/**
 * Pista livre de verdade (pedido de 29/08), por carro: usa a MESMA posicao
 * estimada do mapa ao vivo (`estimar`), so que aqui a distancia angular entre
 * carros (fracao de volta) vira SEGUNDOS pelo ritmo MEDIO do grid em pista.
 * FORMULA: gapS = (fracVizinho - fracCarro, normalizada em [0,1)) * ritmoMedioGrid.
 * A pista nao e percorrida em velocidade constante (curva x reta), entao isto
 * e ESTIMATIVA de proximidade, nao medicao de gap real como um cronometro por
 * setor entre os dois carros daria.
 */
function calcularTrafego(resultados: ResultadoLt[], agoraTod: number, nSetGrid: number): Map<string, InfoTrafego> {
  const mapa = new Map<string, InfoTrafego>();
  const posicoes = resultados.map((r) => ({ r, pos: estimar(r, agoraTod, nSetGrid) }));
  const emPista = posicoes.filter(
    (p): p is { r: ResultadoLt; pos: { estado: "pista" | "linha"; frac: number } } => p.pos.estado !== "box"
  );

  // carro no box nao entra na conta e nao recebe indicador (nem entra no mapa).
  if (emPista.length < 2) {
    for (const { r } of emPista) {
      mapa.set(r.numero, { estado: "indisponivel", motivo: "menos de 2 carros em pista pra comparar" });
    }
    return mapa;
  }

  // ritmo medio do grid: media do ritmo esperado de quem esta em pista. Sem
  // NENHUM carro com ritmo conhecido, nao ha como converter fracao em segundo.
  const ritmos = emPista.map(({ r }) => ritmoEsperado(r)).filter((v): v is number => v != null);
  if (ritmos.length === 0) {
    for (const { r } of emPista) {
      mapa.set(r.numero, { estado: "indisponivel", motivo: "grid sem ritmo de volta conhecido pra converter distancia em segundos" });
    }
    return mapa;
  }
  const ritmoMedioGrid = ritmos.reduce((a, b) => a + b, 0) / ritmos.length;

  const ordenado = [...emPista].sort((a, b) => a.pos.frac - b.pos.frac);
  const n = ordenado.length;
  for (let i = 0; i < n; i++) {
    const atual = ordenado[i];
    // carro sem ritmo proprio: a posicao dele no mapa ja e mais fraca (vem so
    // do setor), entao o gap dele tambem nao e confiavel o bastante pra afirmar.
    if (ritmoEsperado(atual.r) == null) {
      mapa.set(atual.r.numero, { estado: "indisponivel", motivo: "carro sem ritmo de volta conhecido pra estimar o gap" });
      continue;
    }
    const frente = ordenado[(i + 1) % n];
    const atras = ordenado[(i - 1 + n) % n];
    const distFrenteFrac = (((frente.pos.frac - atual.pos.frac) % 1) + 1) % 1;
    const distAtrasFrac = (((atual.pos.frac - atras.pos.frac) % 1) + 1) % 1;
    const gapFrenteS = distFrenteFrac * ritmoMedioGrid;
    const gapAtrasS = distAtrasFrac * ritmoMedioGrid;
    const estado = gapFrenteS >= LIVRE_S && gapAtrasS >= LIVRE_S ? "livre" : "preso";
    mapa.set(atual.r.numero, { estado, gapFrenteS, gapAtrasS });
  }
  return mapa;
}

function MapaAoVivo({ tracado, resultados, classes, snapTod, recebidoEmLocal }: {
  tracado: TracadoLt | null;
  resultados: ResultadoLt[];
  classes: string[];
  snapTod: number | null;
  recebidoEmLocal: React.RefObject<number>;
}) {
  // Posicao EXIBIDA por carro, amortecida. A cada snapshot o alvo recalcula
  // (ultima passagem + ritmo novos) e da um degrau; renderizar o degrau cru e
  // o trimilique medido em 29/08. O exibido persegue o alvo com meia-vida de
  // ~0.4 s: continuo aos olhos, e converge antes do proximo snapshot.
  const exibidas = useRef(new Map<string, number>());
  const ultimoQuadro = useRef(performance.now());
  // rAF: um tick por quadro re-renderiza so este componente; a conta por carro
  // e O(1) sobre o frac + uma busca binaria no traçado
  const [, setQuadro] = useState(0);
  useEffect(() => {
    let vivo = true;
    let id = 0;
    const tick = () => {
      if (!vivo) return;
      setQuadro((q) => q + 1);
      id = requestAnimationFrame(tick);
    };
    id = requestAnimationFrame(tick);
    return () => {
      vivo = false;
      cancelAnimationFrame(id);
    };
  }, []);

  const geo = useMemo(() => {
    if (!tracado?.disponivel || tracado.pontos.length < 2) return null;
    const pts = tracado.pontos;
    const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
    const W = 400, H = 280, P = 20;
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    const sc = Math.min((W - 2 * P) / (x1 - x0 || 1), (H - 2 * P) / (y1 - y0 || 1));
    const px = (x: number) => P + (x - x0) * sc + ((W - 2 * P) - (x1 - x0) * sc) / 2;
    const py = (y: number) => H - P - (y - y0) * sc - ((H - 2 * P) - (y1 - y0) * sc) / 2;
    const total = tracado.comprimento_m ?? pts[pts.length - 1].s_m;
    return { pts, W, H, px, py, total };
  }, [tracado]);

  if (!geo) {
    return (
      <article className="cartao camp-mapa-cartao">
        <header><h4>Mapa ao vivo</h4></header>
        <p className="camp-degradado">
          {tracado && !tracado.disponivel
            ? tracado.motivo
            : "carregando o traçado de referência"}
        </p>
      </article>
    );
  }

  // ponto no traçado pela distancia acumulada (s_m ja e o eixo de distancia)
  const noTracado = (frac: number): { x: number; y: number } => {
    const alvo = ((frac % 1) + 1) % 1 * geo.total;
    const pts = geo.pts;
    let lo = 0, hi = pts.length - 1;
    while (lo < hi) {
      const meio = (lo + hi) >> 1;
      if (pts[meio].s_m < alvo) lo = meio + 1;
      else hi = meio;
    }
    const b = pts[lo], a = pts[Math.max(0, lo - 1)];
    const trecho = b.s_m - a.s_m || 1;
    const t = Math.min(1, Math.max(0, (alvo - a.s_m) / trecho));
    return { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t };
  };

  const agoraQuadro = performance.now();
  const dt = Math.min(0.25, (agoraQuadro - ultimoQuadro.current) / 1000);
  ultimoQuadro.current = agoraQuadro;
  // fator de perseguicao: meia-vida de ~0.4 s (1 - 2^(-dt/0.4))
  const alcance = 1 - Math.pow(2, -dt / 0.4);

  const agoraTod = (snapTod ?? 0) + (agoraQuadro - recebidoEmLocal.current) / 1000;
  const nSetGrid = calcularNSetGrid(resultados);
  const posicoes = resultados.map((r) => {
    const pos = estimar(r, agoraTod, nSetGrid);
    if (pos.estado === "box") {
      exibidas.current.delete(r.numero);
      return { r, pos };
    }
    const anterior = exibidas.current.get(r.numero);
    let frac = pos.frac % 1;
    if (anterior != null) {
      // erro no circulo: -0.5..0.5, senao a correcao daria a volta errada
      let erro = frac - anterior;
      if (erro > 0.5) erro -= 1;
      if (erro < -0.5) erro += 1;
      frac = (((anterior + erro * alcance) % 1) + 1) % 1;
    }
    exibidas.current.set(r.numero, frac);
    return { r, pos: { estado: pos.estado, frac } };
  });
  const emPista = posicoes.filter((p) => p.pos.estado !== "box");
  const noBox = posicoes.length - emPista.length;
  const largada = noTracado(0);

  return (
    <article className="cartao camp-mapa-cartao">
      <header>
        <h4>Mapa ao vivo</h4>
        <span className="no">{emPista.length} em pista · {noBox} no box</span>
        <div className="espaco" />
        <span className="pill pill-warn" title="O live timing não tem GPS: a posição é interpolada entre passagens na linha de cronometragem, sobre o traçado de uma volta real do acervo.">
          posições estimadas
        </span>
      </header>
      <svg viewBox={`0 0 ${geo.W} ${geo.H}`} className="camp-mapa" role="img" aria-label="Mapa da pista com os carros">
        <polyline
          points={geo.pts.map((p) => `${geo.px(p.x)},${geo.py(p.y)}`).join(" ")}
          className="camp-asfalto"
        />
        <line
          x1={geo.px(largada.x) - 8} y1={geo.py(largada.y) - 8}
          x2={geo.px(largada.x) + 8} y2={geo.py(largada.y) + 8}
          className="camp-largada"
        />
        {emPista.map(({ r, pos }) => {
          const frac = pos.estado === "box" ? 0 : pos.frac;
          const { x, y } = noTracado(frac);
          const cor = corDaClasse(r.classe, classes);
          return (
            <g key={r.numero} transform={`translate(${geo.px(x)}, ${geo.py(y)})`}>
              <circle r="15" fill={cor} className="camp-carro" opacity={pos.estado === "linha" ? 0.45 : 1}>
                <title>{`#${r.numero} ${r.nome}${r.carro ? ` (${r.carro})` : ""} · ${r.classe ?? ""}`}</title>
              </circle>
              <text y="3" textAnchor="middle" className="camp-carro-no">{r.numero}</text>
            </g>
          );
        })}
      </svg>
    </article>
  );
}
