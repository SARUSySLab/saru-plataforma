import { useRef } from "react";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useCursor } from "../graficos/useCursor";
import { useLargura } from "../graficos/useLargura";
import type { SerieAmostras } from "../types/contract";
import { useSelecao } from "../state/selection";
import { Segmentado } from "../componentes/Segmentado";
import { calcularDelta } from "../dados/useAmostras";
import { caminho, escala } from "../graficos/svg";
import { sinal } from "../dados/formato";

// Bloco 6. Dois modos, e nao um: acumulado responde "quanto estou perdendo ate
// aqui"; instantaneo responde "onde a perda esta nascendo". Sao a integral e a
// derivada do mesmo sinal, e o acumulado so sobe, entao ele esconde o trecho em
// que o piloto GANHA. Sem o instantaneo, a troca de fase dos Esses some.
export function DeltaEntreVoltas({ a, b, rotuloPar, ehRef }: {
  a: SerieAmostras;
  b: SerieAmostras;
  rotuloPar: string;
  ehRef: boolean;
}) {
  const { deltaMode, setDeltaMode } = useSelecao();
  const host = useRef<HTMLDivElement>(null);
  const cursor = useCursor<{ k: number }>();
  const inst = deltaMode === "instantaneo";
  const { local, acumulado } = calcularDelta(a, b);
  const serie = inst ? local : acumulado;

  const W = useLargura(host, 620);
  const H = 202, PL = 46, PR = 10, PT = 20, PB = 28; // PB maior: cabe a régua de 100 m
  const mx = Math.max(inst ? 0.02 : 0.08, ...serie.map(Math.abs)) * 1.2;
  const x = escala(0, a.distancia_m[a.distancia_m.length - 1], PL, W - PR);
  const y = escala(-mx, mx, H - PB, PT);
  const y0 = y(0);
  const passo = Math.max(1, Math.floor(serie.length / 600));
  /* mesma regua de 100 m do traco: os dois falam da mesma volta, e um eixo com
     escala diferente do outro faria o leitor traduzir de cabeca entre blocos */
  const fim = a.distancia_m[a.distancia_m.length - 1];
  const PASSO_M = 100;
  const marcas: number[] = [];
  for (let d = PASSO_M; d <= fim; d += PASSO_M) marcas.push(d);
  const larguraHost = W;
  const aCada = Math.max(1, Math.ceil(46 / Math.max(1, larguraHost * (PASSO_M / fim))));
  const pts: [number, number][] = [];
  for (let i = 0; i < serie.length; i += passo) pts.push([x(a.distancia_m[i]), y(serie[i])]);
  const area = caminho(pts) + ` L ${x(a.distancia_m[a.distancia_m.length - 1])} ${y0} L ${PL} ${y0} Z`;

  return (
    <article className="cartao">
      <header>
        <h4>Delta entre voltas</h4>
        <span className="no">bloco 6</span>
        <span className="dir">
          <span className="pill pill-brand">{ehRef ? "é a própria referência" : rotuloPar}</span>
          <Segmentado
            valor={deltaMode}
            onEscolher={setDeltaMode}
            opcoes={[{ id: "acumulado", rotulo: "Acumulado" }, { id: "instantaneo", rotulo: "Instantâneo" }]}
          />
        </span>
      </header>

      <div
        className="gr"
        ref={host}
        onPointerMove={(e) => {
          const r = host.current?.getBoundingClientRect();
          if (!r?.width) return;
          const fx = ((e.clientX - r.left) / r.width) * W;
          if (fx < PL || fx > W - PR) return cursor.definir(null);
          const d = ((fx - PL) / (W - PL - PR)) * fim;
          const k = Math.max(0, Math.min(serie.length - 1, Math.round((d / fim) * (serie.length - 1))));
          cursor.definir({ k, xPx: e.clientX - r.left, yPx: e.clientY - r.top });
        }}
        onPointerLeave={() => cursor.definir(null)}
      >
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
          <defs>
            <clipPath id="acima"><rect x="0" y="0" width={W} height={y0} /></clipPath>
            <clipPath id="abaixo"><rect x="0" y={y0} width={W} height={H - y0} /></clipPath>
          </defs>
          {[y(mx * 0.66), y0, y(-mx * 0.66)].map((t, i) => <line key={i} className="grade" x1={PL} y1={t} x2={W - PR} y2={t} />)}
          <path d={area} fill="var(--d-loss)" opacity={0.2} clipPath="url(#acima)" />
          <path d={area} fill="var(--d-gain)" opacity={0.2} clipPath="url(#abaixo)" />
          <line x1={PL} y1={y0} x2={W - PR} y2={y0} stroke="var(--border-strong)" strokeWidth={1} />
          <path d={caminho(pts)} fill="none" stroke="var(--text)" strokeWidth={2} strokeLinejoin="round" />
          <text className="eixo" x={PL - 6} y={y(mx * 0.66) + 3} textAnchor="end">+{(mx * 0.66).toFixed(2)}</text>
          <text className="eixo" x={PL - 6} y={y0 + 3} textAnchor="end">0</text>
          <text className="eixo" x={PL - 6} y={y(-mx * 0.66) + 3} textAnchor="end">{(-mx * 0.66).toFixed(2)}</text>
          <text className="eixo" x={PL - 6} y={PT - 6} textAnchor="end" style={{ fill: "var(--text)", fontWeight: 700 }}>
            {inst ? "s / 100 m" : "s acum."}
          </text>
          {marcas.map((d, i) => {
            const rotula = i % aCada === 0;
            return (
              <g key={d}>
                <line x1={x(d)} y1={H - PB} x2={x(d)} y2={H - PB + (rotula ? 6 : 3)} stroke="var(--border-strong)" strokeWidth={1} opacity={rotula ? 0.9 : 0.45} />
                {rotula && <text className="eixo" x={x(d)} y={H - 6} textAnchor="middle">{d}</text>}
              </g>
            );
          })}
          <text className="eixo" x={W - PR} y={H - 6} textAnchor="end" style={{ fill: "var(--faint)" }}>metros</text>
          {cursor.atual && (
            <line x1={x(a.distancia_m[cursor.atual.k])} y1={PT} x2={x(a.distancia_m[cursor.atual.k])} y2={H - PB} stroke="var(--text)" strokeWidth={1} opacity={0.7} />
          )}
        </svg>

        {cursor.atual && (
          <CardFlutuante
            x={cursor.atual.xPx}
            y={8}
            largura={W}
            titulo={`${a.distancia_m[cursor.atual.k].toFixed(0)} m`}
            linhas={[
              {
                rot: inst ? "perda local" : "delta acum.",
                unico: `${sinal(serie[cursor.atual.k])}${inst ? " s/100 m" : " s"}`,
                cor: serie[cursor.atual.k] > 0 ? "var(--d-loss)" : "var(--d-gain)",
              },
              { rot: inst ? "acumulado até aqui" : "perda local aqui",
                unico: inst
                  ? `${sinal(acumulado[cursor.atual.k])} s`
                  : `${sinal(local[cursor.atual.k])} s/100 m` },
            ]}
          />
        )}
      </div>

      <div className="legenda">
        <span><i style={{ background: "var(--d-gain)" }} />ganhando</span>
        <span><i style={{ background: "var(--d-loss)" }} />perdendo</span>
        <span style={{ color: "var(--faint)" }}>
          {inst ? "quanto se ganha ou perde em cada ponto da pista" : "soma corrida da diferença, do começo da volta até ali"}
        </span>
        <span style={{ color: "var(--faint)" }}>{sinal(acumulado[acumulado.length - 1])} s no total</span>
      </div>
    </article>
  );
}
