import { useRef } from "react";
import type { VoltaResumo } from "../types/contract";
import { useSelecao, type RunMetric } from "../state/selection";
import { Segmentado } from "../componentes/Segmentado";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useCursor } from "../graficos/useCursor";
import { useLargura } from "../graficos/useLargura";
import { caminho, escala } from "../graficos/svg";
import { sinal, tempo } from "../dados/formato";

// Bloco 5. Validado por nome pelo engenheiro: "acho que um grafico interessante
// e aquele de tempo, e legal ver: no inicio foi pior e foi melhorando".
//
// O botao diz O QUE esta plotado; o grafico precisa dizer em QUE unidade e em
// que direcao se le, senao o eixo e um monte de numero sem nome.
const METRICAS: Record<RunMetric, { rotulo: string; unidade: string; direcao: string; valor: (v: VoltaResumo) => number | null }> = {
  lapTime: { rotulo: "Tempo de volta", unidade: "min:seg", direcao: "menor é melhor", valor: (v) => v.tempo_s },
  vMax: { rotulo: "Vel. máxima", unidade: "km/h", direcao: "maior é melhor", valor: (v) => v.v_max_kmh },
  fuel: { rotulo: "Litros por volta", unidade: "L", direcao: "menor é melhor", valor: (v) => v.litros },
  fullThrottle: { rotulo: "Acelerador pleno", unidade: "% da volta", direcao: "maior é melhor", valor: (v) => v.acelerador_pleno_pct },
};

export function EvolucaoPorVolta({ voltas, melhorN, emEscopo }: {
  voltas: VoltaResumo[];
  melhorN: number;
  emEscopo: number;
}) {
  const { runMetric, setRunMetric, setVolta } = useSelecao();
  const host = useRef<HTMLDivElement>(null);
  const cursor = useCursor<{ i: number }>();
  const m = METRICAS[runMetric];

  const W = useLargura(host, 620);
  const H = 196, PL = 52, PR = 10, PT = 32, PB = 22;
  const vals = voltas.map((v) => m.valor(v)).filter((x): x is number => x != null);
  if (vals.length === 0) return null;
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.18 || 1;
  const y = escala(lo - pad, hi + pad, H - PB, PT);
  const x = escala(0, voltas.length - 1, PL, W - PR);
  const linha = voltas.map((v, i) => [x(i), y(m.valor(v) ?? lo)] as [number, number]);

  // fronteira de bateria: o degrau tem causa declarada, nao e ruido
  const corte = voltas.findIndex((v, i) => i > 0 && v.bateria?.id !== voltas[i - 1].bateria?.id);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => PT + (H - PT - PB) * f);

  return (
    <article className="cartao">
      <header>
        <h4>Evolução por volta</h4>
        <span className="no">bloco 5</span>
        <span className="dir">
          <Segmentado
            colunas
            valor={runMetric}
            onEscolher={setRunMetric}
            opcoes={(Object.keys(METRICAS) as RunMetric[]).map((k) => ({ id: k, rotulo: METRICAS[k].rotulo }))}
          />
        </span>
      </header>

      <div className="gr" ref={host} onPointerLeave={() => cursor.definir(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
          {ticks.map((t, i) => <line key={i} className="grade" x1={PL} y1={t} x2={W - PR} y2={t} />)}
          {ticks.map((t, i) => {
            const v = lo - pad + (hi - lo + 2 * pad) * (1 - (t - PT) / (H - PT - PB));
            return (
              <text key={i} className="eixo" x={PL - 6} y={t + 3} textAnchor="end">
                {runMetric === "lapTime" ? tempo(v).slice(0, 7) : v.toFixed(runMetric === "fuel" ? 2 : 0)}
              </text>
            );
          })}
          <text className="eixo" x={PL - 6} y={10} textAnchor="end" style={{ fill: "var(--text)", fontWeight: 700 }}>{m.unidade}</text>
          <text className="eixo" x={W - PR} y={10} textAnchor="end">{m.direcao}</text>
          <text className="eixo" x={(PL + W - PR) / 2} y={H - 4} textAnchor="middle">número da volta</text>

          {corte > 0 && (
            <>
              <line x1={(x(corte) + x(corte - 1)) / 2} y1={PT} x2={(x(corte) + x(corte - 1)) / 2} y2={H - PB} stroke="var(--warn)" strokeWidth={1} strokeDasharray="3 3" />
              <text className="eixo" x={(x(corte) + x(corte - 1)) / 2 + 4} y={PT + 9} style={{ fill: "var(--warn)" }}>
                {voltas[corte].bateria?.rotulo}
              </text>
            </>
          )}

          <path d={caminho(linha)} fill="none" stroke="var(--ch-spd)" strokeWidth={2} strokeLinejoin="round" opacity={0.55} />
          {voltas.map((v, i) => (
            <circle
              key={v.n}
              cx={x(i)} cy={y(m.valor(v) ?? lo)}
              r={v.n === emEscopo ? 5.5 : 4}
              fill={v.n === melhorN ? "var(--brand)" : v.valida ? "var(--ch-spd)" : "var(--faint)"}
              stroke="var(--surface)" strokeWidth={2}
              style={{ cursor: "pointer" }}
              onClick={() => setVolta(v.n)}
              onPointerEnter={(e) => {
                const r = host.current?.getBoundingClientRect();
                if (r) cursor.definir({ i, xPx: e.clientX - r.left, yPx: e.clientY - r.top });
              }}
            />
          ))}
          {voltas.map((v, i) => i % 2 === 0 && (
            <text key={v.n} className="eixo" x={x(i)} y={H - 12} textAnchor="middle">{v.n}</text>
          ))}
        </svg>

        {cursor.atual && (() => {
          const v = voltas[cursor.atual.i];
          return (
            <CardFlutuante
              x={cursor.atual.xPx}
              y={8}
              largura={W}
              titulo={`Volta ${v.n}${v.bateria ? ` · ${v.bateria.rotulo}` : ""}`}
              linhas={[
                { rot: "tempo", unico: tempo(v.tempo_s) },
                { rot: "vs referência", unico: sinal(v.delta_referencia_s), cor: v.delta_referencia_s > 0 ? "var(--d-loss)" : "var(--d-gain)" },
                { rot: "v. máxima", unico: `${v.v_max_kmh?.toFixed(0) ?? "-"} km/h` },
                { rot: "litros", unico: v.litros != null ? `${v.litros.toFixed(2)} L` : "-" },
                { rot: "acel. pleno", unico: `${v.acelerador_pleno_pct?.toFixed(0) ?? "-"}%` },
                ...(v.voltas_pneu != null ? [{ rot: "pneu", unico: `${v.voltas_pneu} voltas de uso` }] : []),
              ]}
              rodape={v.valida ? undefined : `${v.motivo_invalida}: fora de qualquer média`}
            />
          );
        })()}
      </div>

      <p className="nota">
        Cada ponto é uma volta. Out-lap e in-lap ficam fora de qualquer média. A linha tracejada é a
        virada de bateria: o degrau depois dela tem causa declarada no contexto, não é o piloto piorando.
      </p>
    </article>
  );
}
