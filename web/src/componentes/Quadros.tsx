import type { Relatorio } from "../types/contract";
import { useSelecao, type PaginaId } from "../state/selection";
import { caminho, escala } from "../graficos/svg";

// Capas de pagina do box, no MESMO padrao visual dos cards de dado (cartao
// chave: header, numero heroi, miniatura, "ver detalhe"). Desde 29/08 as
// capas se misturam com os cards de dado nas duas linhas 1x4, entao este
// componente renderiza SO as capas pedidas em `ids`, na ordem pedida, sem
// grid proprio: a composicao da linha e do App. O detalhe abre no clique em
// vez de empilhar aqui, que e a regra que segura a tela depois do "muita
// informacao nao e legal" do engenheiro.
function Faisca({ vals, destaque, selecionado }: { vals: number[]; destaque: number; selecionado: number }) {
  const W = 200, H = 62;
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.2 || 1;
  const x = escala(0, vals.length - 1, 0, W);
  const y = escala(lo - pad, hi + pad, H - 6, 6);
  const pts = vals.map((v, i) => [x(i), y(v)] as [number, number]);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
      <path d={caminho(pts) + ` L ${W} ${H} L 0 ${H} Z`} fill="var(--ch-spd)" opacity={0.12} />
      <path d={caminho(pts)} fill="none" stroke="var(--ch-spd)" strokeWidth={2} strokeLinejoin="round" />
      <circle cx={x(destaque)} cy={y(vals[destaque])} r={3.5} fill="var(--brand)" />
      <circle cx={x(selecionado)} cy={y(vals[selecionado])} r={3} fill="none" stroke="var(--text)" strokeWidth={2} />
    </svg>
  );
}

/**
 * Miniatura do tracado pro quadro do mapa (pedido de 29/08: o card estava so
 * com numero, e o mapa e justamente o quadro cuja forma o piloto reconhece).
 * So a linha da pista, ajustada na caixa SEM esticar: pista distorcida deixa
 * de ser reconhecivel, que era o unico trabalho da miniatura.
 */
function MiniPista({ pontos }: { pontos: { x: number; y: number }[] }) {
  const W = 200, H = 62, M = 6;
  const passo = Math.max(1, Math.floor(pontos.length / 240));
  const usados = pontos.filter((_, i) => i % passo === 0);
  const xs = usados.map((p) => p.x), ys = usados.map((p) => p.y);
  const lox = Math.min(...xs), hix = Math.max(...xs);
  const loy = Math.min(...ys), hiy = Math.max(...ys);
  const k = Math.min((W - 2 * M) / (hix - lox || 1), (H - 2 * M) / (hiy - loy || 1));
  const dx = (W - (hix - lox) * k) / 2, dy = (H - (hiy - loy) * k) / 2;
  const pts = usados.map((p) => [dx + (p.x - lox) * k, H - dy - (p.y - loy) * k] as [number, number]);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img">
      <path d={caminho(pts) + " Z"} fill="none" stroke="var(--ch-spd)" strokeWidth={2} strokeLinejoin="round" />
    </svg>
  );
}

export function Quadros({ relatorio, emEscopo, melhorN, ids }: {
  relatorio: Relatorio;
  emEscopo: number;
  melhorN: number;
  /** Quais capas renderizar, na ordem em que devem aparecer na linha. */
  ids: PaginaId[];
}) {
  const { irPara } = useSelecao();
  const voltas = relatorio.n1.voltas;
  const validas = voltas.filter((v) => v.valida);
  const perdas = relatorio.n2.por_curva.disponivel ? relatorio.n2.por_curva.itens : [];
  const recuperavel = perdas.filter((p) => p.perda_s > 0).reduce((a, p) => a + p.perda_s, 0);
  const pior = [...perdas].sort((a, b) => b.perda_s - a.perda_s)[0];
  const primeiraValida = validas[0];
  const melhor = voltas.find((v) => v.n === melhorN);

  const defs: { id: PaginaId; pergunta: string; nome: string; valor: string; sub: React.ReactNode; viz?: React.ReactNode }[] = [
    {
      id: "perdas", pergunta: "Onde perdi?", nome: "Onde ganhar tempo",
      valor: perdas.length ? `+${recuperavel.toFixed(3)} s` : "sem posição",
      sub: pior ? <>maior perda em <b>{pior.rotulo}</b></> : <span style={{ color: "var(--warn)" }}>o N2 degrada e diz por quê</span>,
    },
    {
      id: "mapa", pergunta: "Onde na pista?", nome: "Mapa da pista",
      valor: relatorio.tracado.disponivel ? `${voltas.find((v) => v.n === emEscopo)?.v_max_kmh?.toFixed(0) ?? "-"} km/h` : "sem GPS",
      sub: relatorio.tracado.disponivel
        ? <>pico da volta · {relatorio.trechos.disponivel ? `${relatorio.trechos.itens.length} curvas` : "curvas não catalogadas"}</>
        : <span style={{ color: "var(--warn)" }}>sem coordenada no arquivo</span>,
      viz: relatorio.tracado.disponivel ? <MiniPista pontos={relatorio.tracado.pontos} /> : undefined,
    },
    {
      id: "evolucao", pergunta: "Estou melhorando?", nome: "Evolução por volta",
      valor: melhor && primeiraValida ? `${(melhor.tempo_s - primeiraValida.tempo_s).toFixed(2)} s` : "-",
      sub: <>da 1ª válida à melhor</>,
      viz: <Faisca vals={voltas.map((v) => v.tempo_s)} destaque={voltas.findIndex((v) => v.n === melhorN)} selecionado={voltas.findIndex((v) => v.n === emEscopo)} />,
    },
    {
      id: "voltas", pergunta: "Qual volta olhar?", nome: "Resumo das voltas",
      valor: String(voltas.length),
      sub: <>voltas · <b>{validas.length}</b> válidas · em escopo: <b>volta {emEscopo}</b></>,
      viz: <Faisca vals={voltas.map((v) => v.v_max_kmh ?? 0)} destaque={voltas.findIndex((v) => v.n === melhorN)} selecionado={voltas.findIndex((v) => v.n === emEscopo)} />,
    },
  ];

  const pedidos = ids
    .map((id) => defs.find((d) => d.id === id))
    .filter((d): d is (typeof defs)[number] => d != null);

  return (
    <>
      {pedidos.map((d) => {
        const degradado = /[a-z]/.test(d.valor) && !/km|s$|L$|%$/.test(d.valor);
        return (
          <button key={d.id} type="button" className="cartao chave" onClick={() => irPara({ tipo: "pagina", id: d.id })}>
            <header>
              <h4>{d.nome}</h4>
              <span className="no">{d.pergunta}</span>
            </header>
            <p className="heroi" style={degradado ? { fontSize: 17, color: "var(--warn)" } : undefined}>{d.valor}</p>
            <p className="heroi-sub">{d.sub}</p>
            <span className="viz-q">{d.viz}</span>
            <span className="ir"><span>ver detalhe</span><span>&rsaquo;</span></span>
          </button>
        );
      })}
    </>
  );
}
