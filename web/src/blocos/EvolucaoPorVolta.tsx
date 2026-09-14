import { useRef } from "react";
import type { VoltaResumo } from "../types/contract";
import { useSelecao, type RunMetric } from "../state/selection";
import { Segmentado } from "../componentes/Segmentado";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useCursor } from "../graficos/useCursor";
import { useLargura } from "../graficos/useLargura";
import { escala, passoRotulo } from "../graficos/svg";
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

  // O seletor de metrica fica SEMPRE na tela, mesmo sem dado pra desenhar.
  // Antes o bloco inteiro sumia (`return null`), e quem escolhia "Litros por
  // volta" num arquivo sem canal de combustivel perdia junto o controle que
  // permitiria voltar: beco sem saida. Some o grafico, nunca a navegacao que
  // levou ate ele.
  const cabeca = (
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
  );

  if (vals.length === 0) {
    return (
      <article className="cartao">
        {cabeca}
        <div className="deg">
          <span className="ico">!</span>
          <p>
            Sem <b>{m.rotulo.toLowerCase()}</b> nesta captura: o arquivo não traz esse canal.
            Escolha outra métrica acima.
          </p>
        </div>
      </article>
    );
  }
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.18 || 1;
  const y = escala(lo - pad, hi + pad, H - PB, PT);
  const x = escala(0, voltas.length - 1, PL, W - PR);
  const baseY = H - PB;

  // fronteira de bateria: o degrau tem causa declarada, nao e ruido
  const corte = voltas.findIndex((v, i) => i > 0 && v.bateria?.id !== voltas[i - 1].bateria?.id);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => PT + (H - PT - PB) * f);
  const larg = Math.max(6, (W - PL - PR) / voltas.length - 6);
  // rotulo do numero da volta: passo calculado pela largura, nao "de dois em
  // dois" fixo (com poucas voltas isso pulava numero a toa, com muitas nao
  // pulava o bastante e os numeros se atropelavam)
  const passoLabel = passoRotulo(voltas.length, W - PL - PR);

  return (
    <article className="cartao">
      {cabeca}

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

          {/* pedido de uso real: cada volta e um evento discreto, nao uma
              serie continua, e a barra deixa comparar altura direto sem
              seguir curva. Melhor volta e volta em escopo continuam com o
              mesmo destaque de antes (cor e contorno), so trocou a forma. */}
          {voltas.map((v, i) => {
            const yv = y(m.valor(v) ?? lo);
            // mesmo clamp de borda do bloco 14 (Consumo): a largura e calculada
            // pra caber ENTRE pontos vizinhos, mas nas pontas o ponto fica em
            // cima da propria margem (PL/PR) e metade da barra sobrava pra
            // fora do plot. Presa aos limites antes de desenhar, nao so
            // calculada "no meio" e torcida pra caber.
            const xEsq = Math.max(PL, x(i) - larg / 2);
            const xDir = Math.min(W - PR, x(i) + larg / 2);
            return (
              <rect
                key={v.n}
                x={xEsq}
                y={Math.min(yv, baseY)}
                width={Math.max(1, xDir - xEsq)}
                height={Math.abs(baseY - yv)}
                rx={2}
                fill={v.n === melhorN ? "var(--brand)" : v.valida ? "var(--ch-spd)" : "var(--faint)"}
                opacity={v.n === emEscopo ? 1 : 0.78}
                stroke={v.n === emEscopo ? "var(--text)" : "none"}
                strokeWidth={v.n === emEscopo ? 1.5 : 0}
                style={{ cursor: "pointer" }}
                onClick={() => setVolta(v.n)}
                onPointerEnter={(e) => {
                  const r = host.current?.getBoundingClientRect();
                  if (r) cursor.definir({ i, xPx: e.clientX - r.left, yPx: e.clientY - r.top });
                }}
              />
            );
          })}
          {voltas.map((v, i) => i % passoLabel === 0 && (
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
