import { useRef, useState } from "react";
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
export function DeltaEntreVoltas({ a, b, rotuloPar, ehRef, compacto, aoAbrir }: {
  a: SerieAmostras;
  b: SerieAmostras;
  rotuloPar: string;
  ehRef: boolean;
  /** No Box: grafico + total, sem as frases (o detalhe mora na pagina). */
  compacto?: boolean;
  /** No box o card ganha o footer "ver detalhe" (padrao dos quatro), que
      navega pra evolucao por volta; nas paginas de detalhe nao ha footer. */
  aoAbrir?: () => void;
}) {
  const { deltaMode, setDeltaMode, intervalo, setIntervalo } = useSelecao();
  const host = useRef<HTMLDivElement>(null);
  const cursor = useCursor<{ k: number }>();
  /* Mesmo seletor de intervalo do traco no tempo (pedido de 29/08), sobre o
     MESMO estado global: marcar aqui marca la, porque os dois blocos falam da
     mesma volta na mesma regua de metros. O gesto fica num ref e o desenho num
     estado, pela mesma razao documentada no traco (pointermove le a closure do
     render em que nasceu). */
  const gesto = useRef<{ de: number; ate: number } | null>(null);
  const [faixa, setFaixa] = useState<{ de: number; ate: number } | null>(null);
  const inst = deltaMode === "instantaneo";
  const { local, acumulado } = calcularDelta(a, b);
  const serie = inst ? local : acumulado;

  const W = useLargura(host, 620);
  /* PB cobre DUAS linhas de texto, nao uma: a régua de 100 m (numeros) e a
     legenda "metros" que nomeia essa régua. Antes as duas dividiam a mesma
     linha de base (mesmo y), e a legenda ficava presa no canto direito por
     coordenada fixa (x = W - PR) sem reservar espaco nenhum; quando a pista
     nao e multiplo redondo do passo de rotulagem, o ultimo numero cai bem
     onde a legenda esta e as duas colidem. Separando por LINHA (y diferente,
     nao x calculado) a colisao some pra qualquer comprimento de pista e
     qualquer largura de tela, sem depender de o texto "metros" ser curto. */
  const H = 202, PL = 46, PR = 10, PT = 20, PB = 40;
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

  /* x de tela -> distancia na pista, para o gesto de intervalo */
  const dPara = (clientX: number): number | null => {
    const r = host.current?.getBoundingClientRect();
    if (!r?.width) return null;
    const fx = ((clientX - r.left) / r.width) * W;
    if (fx < PL || fx > W - PR) return null;
    return ((fx - PL) / (W - PL - PR)) * fim;
  };
  const marcado = faixa ?? (intervalo ? { de: intervalo.s_inicio_m, ate: intervalo.s_fim_m } : null);
  // resumo do intervalo: o delta que NASCE dentro dele (diferenca do acumulado
  // entre as bordas), que e a pergunta que o recorte responde. Calculado sobre
  // o MARCADO (faixa em arraste ou intervalo commitado), como no traco: o
  // card ja acompanha o gesto.
  const resumoIntervalo = (() => {
    if (!marcado) return null;
    const de = Math.min(marcado.de, marcado.ate);
    const ate = Math.max(marcado.de, marcado.ate);
    const kDe = Math.max(0, Math.round((de / fim) * (serie.length - 1)));
    const kAte = Math.min(serie.length - 1, Math.round((ate / fim) * (serie.length - 1)));
    if (kAte <= kDe) return null;
    return { delta: acumulado[kAte] - acumulado[kDe], de, ate };
  })();

  return (
    <article className={`cartao${compacto ? " chave" : ""}`}>
      <header>
        <h4>Delta entre voltas</h4>
        <span className="no">bloco 6</span>
        <span className="dir">
          {/* no box (compacto) o card e so o grafico e o numero: a pill da
              referencia e o seletor de modo moram na pagina de detalhe */}
          {!compacto && (
            <span className="pill pill-brand">{ehRef ? "é a própria referência" : rotuloPar}</span>
          )}
          {!compacto && (
            <Segmentado
              valor={deltaMode}
              onEscolher={setDeltaMode}
              opcoes={[{ id: "acumulado", rotulo: "Acumulado" }, { id: "instantaneo", rotulo: "Instantâneo" }]}
            />
          )}
          {intervalo && (
            <button type="button" className="limpar" onClick={() => setIntervalo(null)}>limpar intervalo</button>
          )}
        </span>
      </header>

      <div
        className="gr"
        ref={host}
        onPointerDown={(e) => {
          const d = dPara(e.clientX);
          if (d == null) return;
          try {
            (e.target as Element).setPointerCapture?.(e.pointerId);
          } catch {
            // pointer ja encerrado (ou sintetico): o gesto segue sem captura,
            // que so existe pra nao perder o arraste fora do elemento
          }
          gesto.current = { de: d, ate: d };
          setFaixa(gesto.current);
        }}
        onPointerMove={(e) => {
          const d = dPara(e.clientX);
          if (gesto.current) {
            if (d == null) return;
            gesto.current = { ...gesto.current, ate: d };
            setFaixa(gesto.current);
            return;
          }
          const r = host.current?.getBoundingClientRect();
          if (d == null || !r) return cursor.definir(null);
          const k = Math.max(0, Math.min(serie.length - 1, Math.round((d / fim) * (serie.length - 1))));
          cursor.definir({ k, xPx: e.clientX - r.left, yPx: e.clientY - r.top });
        }}
        onPointerLeave={() => {
          if (gesto.current) return;
          cursor.definir(null);
        }}
        onPointerUp={() => {
          const g = gesto.current;
          if (!g) return;
          gesto.current = null;
          setFaixa(null);
          // arraste curto conta como clique, e clique limpa: mesma regra do traco
          const larguraM = Math.abs(g.ate - g.de);
          setIntervalo(larguraM < 40 ? null : { s_inicio_m: Math.min(g.de, g.ate), s_fim_m: Math.max(g.de, g.ate) });
        }}
      >
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
          <defs>
            <clipPath id="acima"><rect x="0" y="0" width={W} height={y0} /></clipPath>
            <clipPath id="abaixo"><rect x="0" y={y0} width={W} height={H - y0} /></clipPath>
          </defs>
          {marcado && (
            <rect
              x={Math.min(x(marcado.de), x(marcado.ate))} y={PT}
              width={Math.abs(x(marcado.ate) - x(marcado.de))} height={H - PB - PT}
              fill="var(--brand)" opacity={0.14} pointerEvents="none"
            />
          )}
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
                {/* linha de cima da faixa inferior: so os numeros da regua */}
                {rotula && <text className="eixo" x={x(d)} y={H - PB + 16} textAnchor="middle">{d}</text>}
              </g>
            );
          })}
          {/* linha de baixo da faixa inferior: a legenda "metros", numa base
              propria abaixo dos numeros. Nao ha como colidir com o ultimo
              rotulo porque elas nunca ocupam o mesmo y. */}
          <text className="eixo" x={W - PR} y={H - 4} textAnchor="end" style={{ fill: "var(--faint)" }}>metros</text>
          {cursor.atual && (
            <line x1={x(a.distancia_m[cursor.atual.k])} y1={PT} x2={x(a.distancia_m[cursor.atual.k])} y2={H - PB} stroke="var(--text)" strokeWidth={1} opacity={0.7} />
          )}
        </svg>

        {/* Um card so, que troca de conteudo (mesma regra do traco no tempo):
            com faixa marcada ele resume o intervalo, ancorado no centro dela;
            sem faixa, segue o cursor. */}
        {marcado && resumoIntervalo ? (
          <div
            className="flutuante marcado"
            style={{
              left: Math.max(4, Math.min(W - 214, (x(resumoIntervalo.de) + x(resumoIntervalo.ate)) / 2 - 105)),
              top: H + 8,
              width: 210,
            }}
          >
            <div className="tt">
              {resumoIntervalo.de.toFixed(0)} a {resumoIntervalo.ate.toFixed(0)} m ·{" "}
              {(resumoIntervalo.ate - resumoIntervalo.de).toFixed(0)} m
            </div>
            <div className="lin">
              <span>delta no intervalo</span>
              <span style={{ color: resumoIntervalo.delta > 0 ? "var(--d-loss)" : "var(--d-gain)" }}>
                {sinal(resumoIntervalo.delta)} s
              </span>
            </div>
            <div className="lin">
              <span>ritmo</span>
              <span>
                {sinal(resumoIntervalo.delta / Math.max(0.01, (resumoIntervalo.ate - resumoIntervalo.de) / 100))} s/100 m
              </span>
            </div>
            <div className="rodape-flut">clique no gráfico para limpar</div>
          </div>
        ) : cursor.atual && (
          // card ficava fixo no topo (y=8) e cobria justo a area onde a
          // curva de perda/ganho passa. O viewBox usa a mesma largura que o
          // host medido, entao 1 unidade de svg = 1px de tela, e H já é a
          // altura real renderizada: abrir logo abaixo do grafico (y = H)
          // garante que o card nunca fica em cima do traçado.
          <CardFlutuante
            x={cursor.atual.xPx}
            y={H + 8}
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
        {!compacto && <span><i style={{ background: "var(--d-gain)" }} />ganhando</span>}
        {!compacto && <span><i style={{ background: "var(--d-loss)" }} />perdendo</span>}
        {!compacto && (
          <span style={{ color: "var(--faint)" }}>
            {inst ? "quanto se ganha ou perde em cada ponto da pista" : "soma corrida da diferença, do começo da volta até ali"}
          </span>
        )}
        <span style={{ color: "var(--faint)" }}>{sinal(acumulado[acumulado.length - 1])} s no total</span>
        {resumoIntervalo ? (
          <span>
            intervalo {resumoIntervalo.de.toFixed(0)}–{resumoIntervalo.ate.toFixed(0)} m:{" "}
            <b style={{ color: resumoIntervalo.delta > 0 ? "var(--d-loss)" : "var(--d-gain)" }}>
              {sinal(resumoIntervalo.delta)} s
            </b>
          </span>
        ) : (
          <span style={{ color: "var(--brand)" }}>arraste para medir um intervalo</span>
        )}
      </div>

      {aoAbrir && (
        <button type="button" className="ir-link" onClick={aoAbrir}>
          <span>ver detalhe</span>
          <span>&rsaquo;</span>
        </button>
      )}
    </article>
  );
}
