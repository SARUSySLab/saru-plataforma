import { useRef, useState } from "react";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useLargura } from "../graficos/useLargura";
import { caminho, escala } from "../graficos/svg";

// Bloco 17, fora do funil. Alimenta metade do bloco 15 sozinho: temperatura de
// ar, de pista e vento entram no contexto da bateria sem ninguem digitar.
//
// DADO SINTETICO, e a tela diz isso. A integracao com API de tempo real e item
// do roadmap; inventar previsao sem marcar seria a mesma doenca do default
// silencioso, so que no bloco de fora.
const HORAS = Array.from({ length: 24 }, (_, h) => {
  const base = 20 + 11 * Math.sin(((h - 8) / 24) * Math.PI * 2 * 0.62);
  return { h, ar: base, pista: base + 6 + 12 * Math.max(0, Math.sin(((h - 7) / 15) * Math.PI)) };
});
const DIAS = [
  { d: "hoje", min: 21, max: 33, c: "sol, vento fraco" },
  { d: "amanhã", min: 22, max: 35, c: "sol com nuvens" },
  { d: "depois", min: 20, max: 28, c: "pancadas à tarde" },
];
const AGORA = 11;

export function TempoComPrevisao() {
  const host = useRef<HTMLDivElement>(null);
  // mesmo comportamento das series de telemetria: cursor em ref, card
  // flutuante e regua no eixo. E uma serie no tempo como as outras, e ler
  // duas series com dois gestos diferentes na mesma tela seria gratuito.
  const [cursor, setCursor] = useState<{ h: number; xPx: number } | null>(null);
  const W = useLargura(host, 620);
  const H = 162, PL = 34, PR = 12, PT = 12, PB = 30;
  const vals = HORAS.flatMap((p) => [p.ar, p.pista]);
  const y = escala(Math.min(...vals) - 2, Math.max(...vals) + 2, H - PB, PT);
  const x = escala(0, 23, PL, W - PR);
  const linha = (k: "ar" | "pista") => caminho(HORAS.map((p, i) => [x(i), y(p[k])] as [number, number]));
  const larguraHost = W;
  const emPx = (xv: number) => (xv / W) * larguraHost;
  // rotulo de hora a cada N marcas, para nao empilhar numero em tela estreita
  const aCada = Math.max(1, Math.ceil(34 / Math.max(1, larguraHost / 24)));

  return (
    <article className="cartao">
      <header>
        <h4>Tempo com previsão</h4>
        <span className="no">bloco 17</span>
        <span className="dir"><span className="pill pill-warn">dado sintético</span></span>
      </header>

      <div style={{ display: "flex", alignItems: "baseline", gap: "var(--s4)", flexWrap: "wrap" }}>
        <div><span className="numero">{HORAS[AGORA].ar.toFixed(0)}</span> <span className="un">°C ar</span></div>
        <div><span className="mono" style={{ fontSize: 22, fontWeight: 700 }}>{HORAS[AGORA].pista.toFixed(0)}</span> <span className="un">°C pista</span></div>
        <div style={{ marginLeft: "auto" }}><span className="mono" style={{ color: "var(--muted)", fontSize: 12 }}>vento 8 km/h NE · 11:00</span></div>
      </div>

      <div
        className="gr"
        ref={host}
        style={{ marginTop: "var(--s3)" }}
        onPointerMove={(e) => {
          const r = host.current?.getBoundingClientRect();
          if (!r?.width) return;
          const fx = ((e.clientX - r.left) / r.width) * W;
          if (fx < PL || fx > W - PR) return setCursor(null);
          const h = Math.max(0, Math.min(23, Math.round(((fx - PL) / (W - PL - PR)) * 23)));
          setCursor({ h, xPx: e.clientX - r.left });
        }}
        onPointerLeave={() => setCursor(null)}
      >
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
          {[PT, PT + (H - PT - PB) / 2, H - PB].map((t, i) => <line key={i} className="grade" x1={PL} y1={t} x2={W - PR} y2={t} />)}
          <line x1={x(AGORA)} y1={PT} x2={x(AGORA)} y2={H - PB} stroke="var(--brand)" strokeWidth={1.5} />
          <text className="eixo" x={x(AGORA) + 4} y={PT + 9} style={{ fill: "var(--brand)" }}>agora</text>
          <path d={linha("pista")} fill="none" stroke="var(--ch-brk)" strokeWidth={2} strokeLinejoin="round" />
          <path d={linha("ar")} fill="none" stroke="var(--ch-str)" strokeWidth={2} strokeLinejoin="round" />
          {cursor && (
            <line x1={x(cursor.h)} y1={PT} x2={x(cursor.h)} y2={H - PB} stroke="var(--text)" strokeWidth={1} opacity={0.7} />
          )}
          {HORAS.map((p, i) => {
            const rotula = i % aCada === 0;
            return (
              <g key={p.h}>
                <line x1={x(i)} y1={H - PB} x2={x(i)} y2={H - PB + (rotula ? 6 : 3)} stroke="var(--border-strong)" strokeWidth={1} opacity={rotula ? 0.9 : 0.45} />
                {rotula && <text className="eixo" x={x(i)} y={H - 12} textAnchor="middle">{String(p.h).padStart(2, "0")}</text>}
              </g>
            );
          })}
          <text className="eixo" x={W - PR} y={H - 2} textAnchor="end" style={{ fill: "var(--faint)" }}>hora do dia</text>
        </svg>

      </div>

      {/* Aqui o card desce para uma faixa propria em vez de pairar sobre a
          curva. Sao so duas linhas num grafico pequeno, e o card por cima
          cobria justamente o trecho que o cursor esta apontando. A faixa tem
          altura reservada, entao entrar e sair do grafico nao empurra o resto
          da tela para cima e para baixo. */}
      <div className="faixa-card">
        {cursor && (
          <CardFlutuante
            x={emPx(x(cursor.h))}
            y={0}
            largura={larguraHost}
            titulo={`${String(HORAS[cursor.h].h).padStart(2, "0")}:00`}
            linhas={[
              { rot: "ar", unico: <b style={{ color: "var(--ch-str)" }}>{HORAS[cursor.h].ar.toFixed(1)} °C</b> },
              { rot: "pista", unico: <b style={{ color: "var(--ch-brk)" }}>{HORAS[cursor.h].pista.toFixed(1)} °C</b> },
              {
                rot: "vs agora",
                unico: <>{(HORAS[cursor.h].pista - HORAS[AGORA].pista > 0 ? "+" : "") + (HORAS[cursor.h].pista - HORAS[AGORA].pista).toFixed(1)} °C de pista</>,
              },
            ]}
            rodape="alimenta o contexto da bateria sem ninguém digitar"
          />
        )}
      </div>

      <div className="legenda">
        <span><i style={{ background: "var(--ch-str)" }} />ar</span>
        <span><i style={{ background: "var(--ch-brk)" }} />pista</span>
        <span style={{ color: "var(--faint)" }}>hora a hora, hoje</span>
      </div>

      <div className="dias">
        {DIAS.map((d) => (
          <div className="dia" key={d.d}>
            <span className="d">{d.d}</span>
            <span className="r">{d.min}° / {d.max}°</span>
            <span className="c">{d.c}</span>
          </div>
        ))}
      </div>
    </article>
  );
}
