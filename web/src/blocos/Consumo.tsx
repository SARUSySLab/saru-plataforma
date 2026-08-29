import { useRef } from "react";
import type { ConsumoCombustivel, VoltaResumo } from "../types/contract";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useCursor } from "../graficos/useCursor";
import { useLargura } from "../graficos/useLargura";
import { escala } from "../graficos/svg";

// Bloco 14. A conta e a do engenheiro, literal: "pega todas as voltas, tira a
// media, mas exclui a pior e a melhor. Sempre exclui a pior e a melhor". Dois
// recortes: etapa inteira e bateria em escopo. Excluir os extremos e a mesma
// familia da exclusao de in-lap e out-lap que o pipeline ja fazia; ele chegou
// nela sozinho, o que valida o principio.
export function Consumo({ consumo, voltas, emEscopo, bateriaRotulo }: {
  consumo: ConsumoCombustivel;
  voltas: VoltaResumo[];
  emEscopo: number;
  bateriaRotulo: string | null;
}) {
  const host = useRef<HTMLDivElement>(null);
  const cursor = useCursor<{ i: number }>();
  const litros = voltas.map((v) => v.litros).filter((x): x is number => x != null);
  if (litros.length === 0) {
    return (
      <article className="cartao">
        <header><h4>Consumo de combustível</h4><span className="no">bloco 14</span></header>
        <p className="nota">Sem canal de combustível neste arquivo.</p>
      </article>
    );
  }

  const validas = voltas.filter((v) => v.valida && v.litros != null);
  const ordenadas = [...validas].sort((a, b) => (a.litros ?? 0) - (b.litros ?? 0));
  const fora = new Set([ordenadas[0]?.n, ordenadas[ordenadas.length - 1]?.n]);
  const etapa = consumo.media_etapa;
  const bateria = consumo.media_bateria;

  const W = useLargura(host, 620);
  const H = 140, PL = 42, PR = 10, PT = 12, PB = 22;
  const lo = Math.min(...litros) * 0.96, hi = Math.max(...litros) * 1.02;
  const x = escala(0, voltas.length - 1, PL, W - PR);
  const y = escala(lo, hi, H - PB, PT);
  const larg = Math.max(6, (W - PL - PR) / voltas.length - 6);

  return (
    <article className="cartao">
      <header>
        <h4>Consumo de combustível</h4>
        <span className="no">bloco 14</span>
        <span className="dir"><span className="pill pill-brand">exclui melhor e pior</span></span>
      </header>

      <div style={{ display: "flex", gap: "var(--s6)", flexWrap: "wrap", alignItems: "flex-start" }}>
        <div>
          <p className="eyebrow">Etapa inteira</p>
          <p className="heroi" style={{ fontSize: 38 }}>
            {etapa.disponivel ? `${etapa.litros_por_volta.toFixed(2)} L` : "-"}
          </p>
          <p className="heroi-sub">
            {etapa.disponivel
              ? <>por volta · média de <b>{etapa.voltas_consideradas}</b> voltas · fora: as de menor e maior consumo</>
              : etapa.texto}
          </p>
        </div>
        <div>
          <p className="eyebrow">Bateria em escopo</p>
          <p className="heroi" style={{ fontSize: 28, color: "var(--muted)" }}>
            {bateria.disponivel ? `${bateria.litros_por_volta.toFixed(2)} L` : "sem bateria"}
          </p>
          <p className="heroi-sub">
            {bateria.disponivel
              ? <>{bateriaRotulo} · média de <b>{bateria.voltas_consideradas}</b> voltas
                  {etapa.disponivel && <> · {(bateria.litros_por_volta - etapa.litros_por_volta > 0 ? "+" : "")}
                    {(bateria.litros_por_volta - etapa.litros_por_volta).toFixed(2)} L contra a etapa</>}</>
              : bateria.texto}
          </p>
        </div>
      </div>

      <div className="gr" ref={host} style={{ marginTop: "var(--s4)" }} onPointerLeave={() => cursor.definir(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
          {[PT, PT + (H - PT - PB) / 2, H - PB].map((t, i) => <line key={i} className="grade" x1={PL} y1={t} x2={W - PR} y2={t} />)}
          {voltas.map((v, i) => {
            if (v.litros == null) return null;
            const excluida = !v.valida || fora.has(v.n);
            return (
              <rect
                key={v.n}
                x={x(i) - larg / 2} y={y(v.litros)} width={larg} height={H - PB - y(v.litros)} rx={2}
                fill={excluida ? "var(--faint)" : "var(--ch-thr)"}
                opacity={excluida ? 0.38 : v.n === emEscopo ? 1 : 0.78}
                onPointerEnter={(e) => {
                  const r = host.current?.getBoundingClientRect();
                  if (r) cursor.definir({ i, xPx: e.clientX - r.left, yPx: e.clientY - r.top });
                }}
              />
            );
          })}
          {etapa.disponivel && (
            <>
              <line x1={PL} y1={y(etapa.litros_por_volta)} x2={W - PR} y2={y(etapa.litros_por_volta)} stroke="var(--brand)" strokeWidth={1.5} strokeDasharray="4 3" />
              <text className="eixo" x={W - PR} y={y(etapa.litros_por_volta) - 4} textAnchor="end" style={{ fill: "var(--brand)" }}>
                média {etapa.litros_por_volta.toFixed(2)} L
              </text>
            </>
          )}
          <text className="eixo" x={PL - 6} y={PT + 4} textAnchor="end">{hi.toFixed(2)}</text>
          <text className="eixo" x={PL - 6} y={H - PB} textAnchor="end">{lo.toFixed(2)}</text>
          {voltas.map((v, i) => <text key={v.n} className="eixo" x={x(i)} y={H - 6} textAnchor="middle">{v.n}</text>)}
        </svg>

        {cursor.atual && (() => {
          const v = voltas[cursor.atual.i];
          const excluida = !v.valida || fora.has(v.n);
          return (
            <CardFlutuante
              x={cursor.atual.xPx}
              y={8}
              largura={W}
              titulo={`Volta ${v.n}${v.bateria ? ` · ${v.bateria.rotulo}` : ""}`}
              linhas={[
                { rot: "consumo", unico: v.litros != null ? `${v.litros.toFixed(2)} L` : "-" },
                ...(etapa.disponivel && v.litros != null
                  ? [{
                      rot: "vs média da etapa",
                      unico: `${v.litros - etapa.litros_por_volta > 0 ? "+" : ""}${(v.litros - etapa.litros_por_volta).toFixed(2)} L`,
                      cor: v.litros > etapa.litros_por_volta ? "var(--d-loss)" : "var(--d-gain)",
                    }]
                  : []),
              ]}
              rodape={excluida ? (v.valida ? "extremo: fora da média" : `${v.motivo_invalida}: fora da média`) : undefined}
            />
          );
        })()}
      </div>

      <p className="nota">
        Cinza é o que ficou fora da conta: out-lap, in-lap, a volta de menor e a de maior consumo.
      </p>
    </article>
  );
}
