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
  // Marcha é sinal de DEGRAU: a reamostragem na grade de distância interpola
  // e produz 2.37, 3.81... Arredondar aqui impede a legenda de virar um chip
  // por valor distinto (centenas de chips derrubavam o layout inteiro,
  // medido em produção em 29/08) e o cursor de mostrar marcha fracionária.
  const marcha = (a.canais.marcha ?? []).map((g) => Math.round(g));
  const { local } = calcularDelta(a, b);
  const vmax = Math.max(...vel);

  const cor = (i: number) => {
    if (mapMode === "speed") return rampa(vel[i] / vmax);
    if (mapMode === "brake") return rampa(brk[i] / 100);
    if (mapMode === "gear") return rampaFina((marcha[i] - 1) / 5);
    return divergente(local[i] * 4);
  };

  // conversao de coordenada do viewBox pra pixel de tela: so serve pra
  // REPOSICIONAR um ponto que a gente ja sabe (navegacao por teclado), nunca
  // pra descobrir qual ponto esta sob o cursor (isso continua sendo o
  // segmento, como o comentario logo acima explica). A direcao ponto->tela e
  // direta, so aplicar a mesma escala do preserveAspectRatio "meet"; a
  // direcao tela->ponto, que exigiria reconstruir essa escala na mao, e que o
  // comentario original evitava, e continua evitando.
  const paraTela = (vx: number, vy: number) => {
    const r = host.current?.getBoundingClientRect();
    if (!r) return { x: vx, y: vy };
    const esc = Math.min(r.width / W, r.height / H);
    const offX = (r.width - W * esc) / 2;
    const offY = (r.height - H * esc) / 2;
    return { x: offX + vx * esc, y: offY + vy * esc };
  };

  const passo = 3;
  const indices = pts.map((_, i) => i).filter((i) => i % passo === 0);

  // pontos vizinhos disputam o hover porque os segmentos sao curtos e ficam
  // colados na tela, e o mouse troca de um pro outro so pelo jitter do
  // sensor. Com um ponto ja selecionado, seta esquerda/direita anda pro
  // vizinho sem depender de acertar o pixel certo.
  const navegarTeclado = (e: React.KeyboardEvent) => {
    if (!cursor.atual) return;
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const pos = indices.indexOf(cursor.atual.i);
    if (pos < 0) return;
    const prox = e.key === "ArrowRight" ? Math.min(indices.length - 1, pos + 1) : Math.max(0, pos - 1);
    const i = indices[prox];
    const tela = paraTela(px(pts[i]), py(pts[i]));
    cursor.definir({ i, xPx: tela.x, yPx: tela.y });
  };

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
    if (mapMode === "gear") {
      if (marcha.length === 0)
        // degradação declarada: sem canal, o traçado fica neutro e a legenda
        // diz o porquê, em vez de o modo quebrar a tela
        return [{ cor: "var(--faint)", rot: "sem canal de marcha neste arquivo" }];
      // Marchas já inteiras (arredondadas acima); o filtro de faixa é cinto
      // de segurança contra canal podre (0 ou 99 não são marcha e não podem
      // multiplicar chips de legenda).
      return [...new Set(marcha)]
        .filter((g) => Number.isFinite(g) && g >= 1 && g <= 8)
        .sort((p, q) => p - q)
        .map((g) => ({ cor: rampaFina((g - 1) / 5), rot: `${g}ª` }));
    }
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

      <div
        className={`gr mapa${larga ? " larga" : ""}`}
        ref={host}
        tabIndex={0}
        onKeyDown={navegarTeclado}
        onPointerLeave={() => cursor.definir(null)}
      >
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
          // o card antigo seguia o cursor a 130px de distancia, e numa curva
          // fechada isso ainda cai em cima do proprio tracado (a pista dobra
          // sobre ela mesma na tela). Aqui ele vai sempre pro canto do host
          // mais longe do ponto apontado: a pista tem folga (padding P) perto
          // das bordas, entao o canto mais distante e o que tem menos chance
          // de ter desenho por baixo.
          const rect = host.current?.getBoundingClientRect();
          const hostH = rect?.height ?? H;
          const L = 210, alturaCard = 150; // estimativa: titulo + 4 linhas + rodape
          const cantos = [
            { x: 4, y: 4 },
            { x: Math.max(4, largura - L - 4), y: 4 },
            { x: 4, y: Math.max(4, hostH - alturaCard) },
            { x: Math.max(4, largura - L - 4), y: Math.max(4, hostH - alturaCard) },
          ];
          let canto = cantos[0];
          let melhorDist = -1;
          for (const c of cantos) {
            const d = Math.hypot(c.x - cursor.atual.xPx, c.y - cursor.atual.yPx);
            if (d > melhorDist) { melhorDist = d; canto = c; }
          }
          return (
            <CardFlutuante
              x={canto.x + L / 2}
              y={canto.y}
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

