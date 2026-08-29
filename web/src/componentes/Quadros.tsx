import type { Relatorio } from "../types/contract";
import { useSelecao, type PaginaId } from "../state/selection";
import { caminho, escala } from "../graficos/svg";

// A faixa de quadros da visao geral. Cada quadro e a CAPA de uma pagina: uma
// pergunta, um numero dominante, uma miniatura da forma do dado. O detalhe
// abre no clique em vez de empilhar aqui, que e a regra que segura a tela
// depois do "muita informacao nao e legal" do engenheiro.
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

function Barras({ vals, selecionado, foraDaConta }: { vals: number[]; selecionado: number; foraDaConta: Set<number> }) {
  const W = 200, H = 62;
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const larg = W / vals.length - 3;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
      {vals.map((v, i) => {
        const t = (v - lo) / (hi - lo || 1);
        const h = Math.max(3, (H - 8) * (1 - t * 0.8));
        return (
          <rect
            key={i} x={i * (W / vals.length)} y={H - h} width={larg} height={h} rx={2}
            fill={foraDaConta.has(i) ? "var(--faint)" : "var(--ch-thr)"}
            opacity={i === selecionado ? 1 : 0.55}
          />
        );
      })}
    </svg>
  );
}

export function Quadros({ relatorio, emEscopo, melhorN }: {
  relatorio: Relatorio;
  emEscopo: number;
  melhorN: number;
}) {
  const { irPara } = useSelecao();
  const voltas = relatorio.n1.voltas;
  const validas = voltas.filter((v) => v.valida);
  const perdas = relatorio.n2.por_curva.disponivel ? relatorio.n2.por_curva.itens : [];
  const recuperavel = perdas.filter((p) => p.perda_s > 0).reduce((a, p) => a + p.perda_s, 0);
  const pior = [...perdas].sort((a, b) => b.perda_s - a.perda_s)[0];
  const consumo = relatorio.n1.consumo.media_etapa;
  const litros = voltas.map((v) => v.litros ?? 0);
  const ordenadas = [...validas].sort((a, b) => (a.litros ?? 0) - (b.litros ?? 0));
  const fora = new Set(
    voltas.map((v, i) => (!v.valida || v.n === ordenadas[0]?.n || v.n === ordenadas.at(-1)?.n ? i : -1)).filter((i) => i >= 0),
  );
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
    },
    {
      id: "evolucao", pergunta: "Estou melhorando?", nome: "Evolução por volta",
      valor: melhor && primeiraValida ? `${(melhor.tempo_s - primeiraValida.tempo_s).toFixed(2)} s` : "-",
      sub: <>da 1ª válida à melhor</>,
      viz: <Faisca vals={voltas.map((v) => v.tempo_s)} destaque={voltas.findIndex((v) => v.n === melhorN)} selecionado={voltas.findIndex((v) => v.n === emEscopo)} />,
    },
    {
      id: "consumo", pergunta: "Quanto por volta?", nome: "Consumo",
      valor: consumo.disponivel ? `${consumo.litros_por_volta.toFixed(2)} L` : "sem dado",
      sub: consumo.disponivel ? <>por volta na etapa</> : consumo.texto,
      viz: <Barras vals={litros} selecionado={voltas.findIndex((v) => v.n === emEscopo)} foraDaConta={fora} />,
    },
    {
      id: "voltas", pergunta: "Qual volta olhar?", nome: "Resumo das voltas",
      valor: String(voltas.length),
      sub: <>voltas · <b>{validas.length}</b> válidas · em escopo: <b>volta {emEscopo}</b></>,
      viz: <Faisca vals={voltas.map((v) => v.v_max_kmh ?? 0)} destaque={voltas.findIndex((v) => v.n === melhorN)} selecionado={voltas.findIndex((v) => v.n === emEscopo)} />,
    },
    {
      id: "traco", pergunta: "O que fiz nos controles?", nome: "Traço no tempo",
      valor: `${voltas.find((v) => v.n === emEscopo)?.acelerador_pleno_pct?.toFixed(0) ?? "-"}%`,
      sub: <>de acelerador pleno · 4 canais sobrepostos</>,
    },
  ];

  return (
    <>
      <div className="quadros">
        {defs.map((d) => (
          <button key={d.id} type="button" className="quadro" onClick={() => irPara({ tipo: "pagina", id: d.id })}>
            <span className="pergunta-q">{d.pergunta}</span>
            <span className="nome-q">{d.nome}</span>
            <span className={`valor-q${/[a-z]/.test(d.valor) && !/km|s$|L$|%$/.test(d.valor) ? " degradado-q" : ""}`}>{d.valor}</span>
            <span className="sub-q">{d.sub}</span>
            <span className="viz-q">{d.viz}</span>
            <span className="ir"><span>ver detalhe</span><span>&rsaquo;</span></span>
          </button>
        ))}
      </div>
      <p className="nota">Seis quadros, uma pergunta cada. Clique para abrir o detalhe.</p>
    </>
  );
}
