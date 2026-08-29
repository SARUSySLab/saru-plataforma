import { useRef } from "react";
import type { Relatorio, SerieAmostras } from "../types/contract";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useCursor } from "../graficos/useCursor";
import { useLargura } from "../graficos/useLargura";
import { sinal } from "../dados/formato";
import { useSelecao, type MapMode } from "../state/selection";
import { Segmentado } from "../componentes/Segmentado";
import { Degradado } from "../componentes/Degradado";
import { calcularDelta } from "../dados/useAmostras";
import { divergente, rampa, rampaFina } from "../graficos/svg";

// Bloco 8. Sem coordenada nao ha traçado, nao ha curva e nao ha corte de volta
// por linha. O default silencioso e proibido aqui: a tela declara o que falta
// em vez de desenhar a pista errada. Era exatamente o bug B2.
export function MapaDaPista({ tracado, trechos, a, b, larga }: {
  tracado: Relatorio["tracado"];
  trechos: Relatorio["trechos"];
  a: SerieAmostras;
  b: SerieAmostras;
  larga?: boolean;
}) {
  const { mapMode, setMapMode, trecho, setTrecho } = useSelecao();
  const host = useRef<HTMLDivElement>(null);
  // no percurso o ponto apontado vem do proprio segmento sob o cursor, e nao
  // de uma conta de coordenada: o svg usa preserveAspectRatio "meet", entao
  // converter tela para indice na mao exigiria refazer a escala do meet, e o
  // segmento ja sabe qual amostra ele desenha
  const cursor = useCursor<{ i: number }>();
  const largura = useLargura(host, 460);

  if (!tracado.disponivel) {
    return (
      <article className="cartao degradado">
        <header><h4>Mapa da pista</h4><span className="no">bloco 8</span></header>
        <Degradado estado={tracado} />
      </article>
    );
  }

  const pts = tracado.pontos;
  const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
  const W = 460, H = 330, P = 26;
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const sc = Math.min((W - 2 * P) / (x1 - x0), (H - 2 * P) / (y1 - y0));
  const px = (p: { x: number }) => P + (p.x - x0) * sc + ((W - 2 * P) - (x1 - x0) * sc) / 2;
  const py = (p: { y: number }) => H - P - (p.y - y0) * sc - ((H - 2 * P) - (y1 - y0) * sc) / 2;

  const vel = a.canais.velocidade ?? [];
  const brk = a.canais.freio ?? [];
  const marcha = a.canais.marcha ?? [];
  const { local } = calcularDelta(a, b);
  const vmax = Math.max(...vel);

  const cor = (i: number) => {
    if (mapMode === "speed") return rampa(vel[i] / vmax);
    if (mapMode === "brake") return rampa(brk[i] / 100);
    if (mapMode === "gear") return rampaFina((marcha[i] - 1) / 5);
    return divergente(local[i] * 4);
  };

  const passo = 3;
  const indices = pts.map((_, i) => i).filter((i) => i % passo === 0);
  const segmentos = indices.map((i) => {
    const j = (i + passo) % pts.length;
    return (
      <line
        key={i}
        x1={px(pts[i])} y1={py(pts[i])} x2={px(pts[j])} y2={py(pts[j])}
        stroke={cor(i)} strokeWidth={9} strokeLinecap="round"
        onPointerEnter={(e) => {
          const r = host.current?.getBoundingClientRect();
          if (r) cursor.definir({ i, xPx: e.clientX - r.left, yPx: e.clientY - r.top });
        }}
      />
    );
  });

  const marcas = trechos.disponivel ? trechos.itens : [];
  const legenda = (() => {
    if (mapMode === "speed")
      return [0, 0.25, 0.5, 0.75, 1].map((t) => ({ cor: rampa(t), rot: (t * vmax).toFixed(0) }));
    if (mapMode === "brake")
      return [0, 0.5, 1].map((t) => ({ cor: rampa(t), rot: `${(t * 100).toFixed(0)}%` }));
    if (mapMode === "gear")
      return [...new Set(marcha)].sort((p, q) => p - q).map((g) => ({ cor: rampaFina((g - 1) / 5), rot: `${g}ª` }));
    return [
      { cor: "var(--d-gain)", rot: "ganhando" },
      { cor: "var(--d-mid)", rot: "igual" },
      { cor: "var(--d-loss)", rot: "perdendo" },
    ];
  })();

  return (
    <article className="cartao">
      <header>
        <h4>Mapa da pista</h4>
        <span className="no">bloco 8</span>
        <span className="dir">
          <Segmentado
            valor={mapMode}
            onEscolher={(m: MapMode) => setMapMode(m)}
            opcoes={[
              { id: "speed", rotulo: "Velocidade" },
              { id: "brake", rotulo: "Freio" },
              { id: "gear", rotulo: "Marcha" },
              { id: "delta", rotulo: "Delta" },
            ]}
          />
        </span>
      </header>

      <div className={`gr mapa${larga ? " larga" : ""}`} ref={host} onPointerLeave={() => cursor.definir(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet" role="img">
          {segmentos}
          <line
            x1={px(pts[0]) - 11} y1={py(pts[0]) - 11} x2={px(pts[0]) + 11} y2={py(pts[0]) + 11}
            stroke="var(--text)" strokeWidth={2.5}
          />
          {marcas.map((c, i) => {
            const p = pts.reduce((melhor, q) => (Math.abs(q.s_m - c.apex_m) < Math.abs(melhor.s_m - c.apex_m) ? q : melhor), pts[0]);
            const sel = trecho === c.id;
            return (
              <g key={c.id} style={{ cursor: "pointer" }} onClick={() => setTrecho(sel ? null : c.id)}>
                <circle cx={px(p)} cy={py(p)} r={sel ? 11 : 8} fill="var(--surface)" stroke={sel ? "var(--brand)" : "var(--border-strong)"} strokeWidth={sel ? 2.5 : 1.5} />
                <text x={px(p)} y={py(p) + 3.5} textAnchor="middle" style={{ fontFamily: "var(--mono)", fontSize: 9, fontWeight: 700, fill: sel ? "var(--brand)" : "var(--muted)" }}>
                  {i + 1}
                </text>
                <title>{c.rotulo}</title>
              </g>
            );
          })}
          {cursor.atual && (
            <circle cx={px(pts[cursor.atual.i])} cy={py(pts[cursor.atual.i])} r={6} fill="none" stroke="var(--text)" strokeWidth={2} pointerEvents="none" />
          )}
        </svg>

        {cursor.atual && (() => {
          const i = cursor.atual.i;
          return (
            <CardFlutuante
              x={cursor.atual.xPx}
              y={Math.max(4, cursor.atual.yPx - 130)}
              largura={largura}
              titulo={`${pts[i].s_m.toFixed(0)} m`}
              linhas={[
                { rot: "velocidade", unico: `${vel[i]?.toFixed(0) ?? "-"} km/h` },
                { rot: "freio", unico: `${brk[i]?.toFixed(0) ?? "-"} %` },
                { rot: "marcha", unico: String(marcha[i] ?? "-") },
                { rot: "perda local", unico: `${sinal(local[i])} s/100 m`, cor: local[i] > 0 ? "var(--d-loss)" : "var(--d-gain)" },
              ]}
              rodape={trechos.disponivel ? trechos.itens.find((t) => pts[i].s_m >= t.s_inicio_m && pts[i].s_m <= t.s_fim_m)?.rotulo : undefined}
            />
          );
        })()}
      </div>

      <div className="legenda">
        {legenda.map((l) => (
          <span key={l.rot}><i style={{ background: l.cor, width: 16, height: 8, borderRadius: 2 }} />{l.rot}</span>
        ))}
        {mapMode === "speed" && <span style={{ color: "var(--faint)" }}>km/h</span>}
        {!trechos.disponivel && <span style={{ color: "var(--warn)" }}>curvas não catalogadas para este layout</span>}
      </div>
    </article>
  );
}

