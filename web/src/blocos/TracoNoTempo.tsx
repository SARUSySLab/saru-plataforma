import { useRef, useState } from "react";
import type { Relatorio, SerieAmostras } from "../types/contract";
import { useSelecao } from "../state/selection";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useLargura } from "../graficos/useLargura";
import { caminho, escala } from "../graficos/svg";
import { sinal } from "../dados/formato";

// Bloco 10. A cor identifica a SERIE, nao o canal: o canal ja e identificado
// pela faixa e pelo rotulo. E a convencao de overlay de MoTeC e AiM, e o
// engenheiro le assim sem precisar aprender nada novo.
const FAIXAS = [
  { id: "velocidade", nome: "Velocidade", unidade: "km/h", lo: 0, hi: 240 },
  { id: "acelerador", nome: "Acelerador", unidade: "%", lo: 0, hi: 105 },
  { id: "freio", nome: "Freio", unidade: "%", lo: 0, hi: 105 },
  { id: "direcao", nome: "Direção", unidade: "°", lo: -105, hi: 105 },
];

export function TracoNoTempo({ a, b, rotuloA, rotuloB, trechos }: {
  a: SerieAmostras;
  b: SerieAmostras;
  rotuloA: string;
  rotuloB: string;
  trechos: Relatorio["trechos"];
}) {
  const { trecho, intervalo, setIntervalo } = useSelecao();
  const host = useRef<HTMLDivElement>(null);
  /* O GESTO fica num ref e o DESENHO num estado, e os dois nao sao a mesma
     coisa. O ref e necessario porque o handler de pointermove le a closure do
     render em que foi criado: com estado sozinho, um movimento que chega antes
     do re-render enxerga null e e descartado, e um arraste rapido perde metade
     do caminho. O estado e necessario porque a faixa precisa ser desenhada, e
     ler ref durante o render deixa o desenho um quadro atras do ponteiro. */
  const gesto = useRef<{ de: number; ate: number } | null>(null);
  const [faixa, setFaixa] = useState<{ de: number; ate: number } | null>(null);
  const [cursor, setCursor] = useState<{ k: number; xPx: number; yPx: number } | null>(null);

  // O escopo do traco e o trecho selecionado, se houver: e assim que a selecao
  // de um nivel vira o escopo do nivel seguinte.
  const janela = (() => {
    if (!trecho || !trechos.disponivel) return { d0: 0, d1: a.distancia_m[a.distancia_m.length - 1] };
    const t = trechos.itens.find((x) => x.id === trecho);
    if (!t) return { d0: 0, d1: a.distancia_m[a.distancia_m.length - 1] };
    const folga = (t.s_fim_m - t.s_inicio_m) * 0.25;
    return { d0: Math.max(0, t.s_inicio_m - folga), d1: t.s_fim_m + folga };
  })();

  const idx = a.distancia_m.map((_, i) => i).filter((i) => a.distancia_m[i] >= janela.d0 && a.distancia_m[i] <= janela.d1);
  const W = useLargura(host, 900);
  const alturaFaixa = 84, vao = 10, PL = 62, PR = 14, PT = 8;
  const H = PT + FAIXAS.length * (alturaFaixa + vao) + 24; // folga para a régua de 100 m
  const base = PT + FAIXAS.length * (alturaFaixa + vao) - vao;
  const x = escala(0, idx.length - 1, PL, W - PR);
  const passo = Math.max(1, Math.floor(idx.length / 520));

  const dPara = (clientX: number) => {
    const r = host.current?.getBoundingClientRect();
    if (!r?.width) return null;
    const fx = ((clientX - r.left) / r.width) * W;
    if (fx < PL || fx > W - PR) return null;
    const k = Math.round(((fx - PL) / (W - PL - PR)) * (idx.length - 1));
    return a.distancia_m[idx[Math.max(0, Math.min(idx.length - 1, k))]];
  };

  const marcado = faixa ?? (intervalo ? { de: intervalo.s_inicio_m, ate: intervalo.s_fim_m } : null);
  const xDe = (d: number) => {
    const k = idx.findIndex((i) => a.distancia_m[i] >= d);
    return x(k < 0 ? idx.length - 1 : k);
  };
  const larguraHost = W;
  const emPx = (xv: number) => (xv / W) * larguraHost;

  /* Regua de distancia de 100 em 100 m. A marca fica sempre nos 100; o ROTULO
     e ralead0 conforme a largura disponivel, senao os numeros se sobrepoem e
     viram uma tarja preta. Com o escopo num trecho a janela encurta e os
     rotulos voltam a caber de 100 em 100 sozinhos. */
  const xDeDistancia = (d: number) => {
    const k = idx.findIndex((i) => a.distancia_m[i] >= d);
    return x(k < 0 ? idx.length - 1 : k);
  };
  const PASSO_M = 100;
  const marcas: number[] = [];
  for (let d = Math.ceil(janela.d0 / PASSO_M) * PASSO_M; d <= janela.d1; d += PASSO_M) marcas.push(d);
  const pxPorMarca = larguraHost * (PASSO_M / Math.max(1, janela.d1 - janela.d0));
  const aCada = Math.max(1, Math.ceil(46 / Math.max(1, pxPorMarca)));

  // resumo do intervalo: mesma conta do resto da tela, so com outra janela
  const resumo = (() => {
    if (!intervalo) return null;
    const ks = idx.filter((i) => a.distancia_m[i] >= intervalo.s_inicio_m && a.distancia_m[i] <= intervalo.s_fim_m);
    if (ks.length < 2) return null;
    const tempoDe = (s: SerieAmostras) =>
      ks.reduce((acc, i) => {
        const d = (a.distancia_m[i + 1] ?? a.distancia_m[i]) - a.distancia_m[i];
        return acc + (d > 0 ? d / (s.canais.velocidade[i] / 3.6) : 0);
      }, 0);
    const media = (s: SerieAmostras, c: string) => ks.reduce((acc, i) => acc + (s.canais[c]?.[i] ?? 0), 0) / ks.length;
    return { tA: tempoDe(a), tB: tempoDe(b), media, n: ks.length };
  })();

  return (
    <article className="cartao">
      <header>
        <h4>Traço no tempo</h4>
        <span className="no">bloco 10</span>
        <span className="dir">
          <span className="pill pill-brand">{trecho && trechos.disponivel ? trechos.itens.find((t) => t.id === trecho)?.rotulo ?? "trecho" : "volta inteira"}</span>
          <span className="eyebrow">{rotuloA} vs {rotuloB}</span>
          {intervalo && (
            <button type="button" className="limpar" onClick={() => setIntervalo(null)}>limpar intervalo</button>
          )}
        </span>
      </header>

      <div
        className="gr traco"
        ref={host}
        onPointerDown={(e) => {
          const d = dPara(e.clientX);
          if (d == null) return;
          (e.target as Element).setPointerCapture?.(e.pointerId);
          gesto.current = { de: d, ate: d };
          setFaixa(gesto.current);
        }}
        onPointerMove={(e) => {
          const r = host.current?.getBoundingClientRect();
          const d = dPara(e.clientX);
          if (gesto.current) {
            if (d == null) return;
            gesto.current = { ...gesto.current, ate: d };
            setFaixa(gesto.current);
            return;
          }
          if (d == null || !r) return setCursor(null);
          const k = idx.findIndex((i) => a.distancia_m[i] >= d);
          setCursor({ k: k < 0 ? idx.length - 1 : k, xPx: e.clientX - r.left, yPx: e.clientY - r.top });
        }}
        onPointerLeave={() => {
          if (gesto.current) return;
          setCursor(null);
        }}
        onPointerUp={() => {
          const g = gesto.current;
          if (!g) return;
          gesto.current = null;
          setFaixa(null);
          // arraste curto conta como clique, e clique limpa: o mesmo gesto abre
          // e fecha, sem botao extra na tela
          const larguraM = Math.abs(g.ate - g.de);
          setIntervalo(larguraM < 40 ? null : { s_inicio_m: Math.min(g.de, g.ate), s_fim_m: Math.max(g.de, g.ate) });
        }}
      >
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
          {marcado && (
            <rect
              x={Math.min(xDe(marcado.de), xDe(marcado.ate))} y={PT}
              width={Math.abs(xDe(marcado.ate) - xDe(marcado.de))} height={base - PT}
              fill="var(--brand)" opacity={0.14} pointerEvents="none"
            />
          )}
          {FAIXAS.map((f, li) => {
            const topo = PT + li * (alturaFaixa + vao);
            const y = escala(f.lo, f.hi, topo + alturaFaixa, topo);
            const serie = (s: SerieAmostras) => {
              const pts: [number, number][] = [];
              for (let k = 0; k < idx.length; k += passo) pts.push([x(k), y(s.canais[f.id]?.[idx[k]] ?? 0)]);
              return caminho(pts);
            };
            return (
              <g key={f.id}>
                <line className="grade" x1={PL} y1={topo} x2={W - PR} y2={topo} />
                <line className="grade" x1={PL} y1={topo + alturaFaixa} x2={W - PR} y2={topo + alturaFaixa} />
                <path d={serie(b)} fill="none" stroke="var(--lap-b)" strokeWidth={2} strokeLinejoin="round" opacity={0.9} />
                <path d={serie(a)} fill="none" stroke="var(--lap-a)" strokeWidth={2} strokeLinejoin="round" />
                <text className="eixo" x={PL - 8} y={topo + 10} textAnchor="end" style={{ fontWeight: 700, fill: "var(--text)", fontSize: 10 }}>{f.nome}</text>
                <text className="eixo" x={PL - 8} y={topo + 22} textAnchor="end">{f.hi} {f.unidade}</text>
                <text className="eixo" x={PL - 8} y={topo + alturaFaixa} textAnchor="end">{f.lo}</text>
              </g>
            );
          })}
          {cursor && !marcado && (
            <line x1={x(cursor.k)} y1={PT} x2={x(cursor.k)} y2={base} stroke="var(--text)" strokeWidth={1} opacity={0.7} />
          )}
          {marcas.map((d, i) => {
            const xv = xDeDistancia(d);
            const rotula = i % aCada === 0;
            return (
              <g key={d}>
                <line x1={xv} y1={base} x2={xv} y2={base + (rotula ? 6 : 3)} stroke="var(--border-strong)" strokeWidth={1} opacity={rotula ? 0.9 : 0.45} />
                {rotula && <text className="eixo" x={xv} y={H - 4} textAnchor="middle">{d}</text>}
              </g>
            );
          })}
          <text className="eixo" x={W - PR} y={H - 4} textAnchor="end" style={{ fill: "var(--faint)" }}>metros</text>
        </svg>

        {/* Um card so, que troca de conteudo: com faixa marcada ele resume o
            intervalo e fica ancorado no centro dela; sem faixa, ele segue o
            cursor e mostra o ponto. Dois cards disputando a mesma area seria
            o usuario tendo que descobrir qual deles esta respondendo. */}
        {marcado && resumo ? (
          <div className="flutuante marcado" style={{ left: Math.max(4, Math.min(larguraHost - 214, emPx((xDe(marcado.de) + xDe(marcado.ate)) / 2) - 105)), top: 6, width: 210 }}>
            <div className="tt">
              {Math.min(marcado.de, marcado.ate).toFixed(0)} a {Math.max(marcado.de, marcado.ate).toFixed(0)} m ·{" "}
              {Math.abs(marcado.ate - marcado.de).toFixed(0)} m
            </div>
            <div className="lin"><span>tempo</span><span>
              <b style={{ color: "var(--lap-a)" }}>{resumo.tA.toFixed(3)}</b>{" "}
              <b style={{ color: "var(--lap-b)" }}>{resumo.tB.toFixed(3)}</b>
            </span></div>
            <div className="lin"><span>diferença</span>
              <span style={{ color: resumo.tA > resumo.tB ? "var(--d-loss)" : "var(--d-gain)" }}>{sinal(resumo.tA - resumo.tB)} s</span>
            </div>
            {FAIXAS.map((f) => (
              <div className="lin" key={f.id}><span>{f.nome} méd</span><span>
                <b style={{ color: "var(--lap-a)" }}>{resumo.media(a, f.id).toFixed(f.unidade === "%" ? 0 : 1)}</b>{" "}
                <b style={{ color: "var(--lap-b)" }}>{resumo.media(b, f.id).toFixed(f.unidade === "%" ? 0 : 1)}</b>
              </span></div>
            ))}
            <div className="rodape-flut">clique no gráfico para limpar</div>
          </div>
        ) : cursor ? (
          <CardFlutuante
            x={emPx(x(cursor.k))}
            y={8}
            largura={larguraHost}
            titulo={`${a.distancia_m[idx[cursor.k]].toFixed(0)} m`}
            linhas={[
              { rot: "", unico: <><b style={{ color: "var(--lap-a)" }}>{rotuloA}</b> <b style={{ color: "var(--lap-b)" }}>{rotuloB}</b></> },
              ...FAIXAS.map((f) => ({
                rot: f.nome,
                a: (a.canais[f.id]?.[idx[cursor!.k]] ?? 0).toFixed(f.unidade === "%" ? 0 : 1),
                b: (b.canais[f.id]?.[idx[cursor!.k]] ?? 0).toFixed(f.unidade === "%" ? 0 : 1),
              })),
              {
                rot: "marcha",
                a: String(a.canais.marcha?.[idx[cursor.k]] ?? "-"),
                b: String(b.canais.marcha?.[idx[cursor.k]] ?? "-"),
              },
            ]}
          />
        ) : null}
      </div>

      <div className="legenda">
        <span><i style={{ background: "var(--lap-a)" }} />{rotuloA}</span>
        <span><i style={{ background: "var(--lap-b)" }} />{rotuloB}</span>
        <span style={{ color: "var(--faint)" }}>a cor é a série, o canal é a faixa</span>
        <span style={{ color: "var(--brand)" }}>arraste para medir um intervalo</span>
      </div>
    </article>
  );
}
