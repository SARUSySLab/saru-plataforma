import { useRef } from "react";
import type { ConsumoCombustivel, VoltaResumo } from "../types/contract";
import type { Bateria } from "../services/operacao";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useCursor } from "../graficos/useCursor";
import { useLargura } from "../graficos/useLargura";
import { escala, passoRotulo } from "../graficos/svg";

// Bloco 14. A conta e a do engenheiro, literal: "pega todas as voltas, tira a
// media, mas exclui a pior e a melhor. Sempre exclui a pior e a melhor". Dois
// recortes: etapa inteira e bateria em escopo. Excluir os extremos e a mesma
// familia da exclusao de in-lap e out-lap que o pipeline ja fazia; ele chegou
// nela sozinho, o que valida o principio.
export function Consumo({ consumo, voltas, emEscopo, bateriaRotulo, bateriaEscopo, aoInserir, aoAbrir }: {
  consumo: ConsumoCombustivel;
  voltas: VoltaResumo[];
  emEscopo: number;
  bateriaRotulo: string | null;
  /** Bateria em escopo: fonte do consumo INFORMADO (litros na saida e na
      volta) quando o arquivo nao tem canal de combustivel. */
  bateriaEscopo?: Bateria | null;
  /** Abre o contexto da bateria, onde moram os litros de saída e de volta.
      Sem canal de combustível o dado só existe se alguém informar, e o card
      degradado tem que oferecer o caminho em vez de só declarar a falta. */
  aoInserir?: () => void;
  /** No box o footer e "ver detalhe" e navega pra pagina Consumo (padrao dos
      quatro cards, pedido de 29/08); o inserir/atualizar mora no detalhe. */
  aoAbrir?: () => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const cursor = useCursor<{ i: number }>();
  // hook nao pode vir depois de um return condicional (regra dos hooks): a
  // chamada precisa ser incondicional, entao ela sobe pra antes do "sem
  // canal" abaixo, mesmo que o grafico so va usar W quando ha dado pra mostrar.
  const W = useLargura(host, 620);
  const litros = voltas.map((v) => v.litros).filter((x): x is number => x != null);
  if (litros.length === 0) {
    // Sem canal, o dado que EXISTE e o informado pelo piloto na bateria:
    // saiu com X litros, voltou com Y (gaveta de contexto ou editar
    // bateria). E medicao de box, nao telemetria, e o selo diz isso.
    const saida = bateriaEscopo?.fuel_out_l ?? null;
    const volta = bateriaEscopo?.fuel_in_l ?? null;
    const consumido = saida != null && volta != null ? saida - volta : null;
    const nVoltas = voltas.length;
    return (
      <article className={`cartao${aoAbrir ? " chave" : ""}`}>
        <header>
          <h4>Consumo de combustível</h4><span className="no">bloco 14</span>
          {/* no box (aoAbrir) a pill sai: "números do box, não da
              telemetria" ja esta escrito no card; na pagina de detalhe a
              tag fica como selo de procedencia */}
          {consumido != null && !aoAbrir && (
            <span className="dir"><span className="pill pill-warn">informado</span></span>
          )}
        </header>
        {consumido != null ? (
          <>
            <p className="heroi">{consumido.toFixed(1).replace(".", ",")} L</p>
            <p className="heroi-sub">
              saiu com {saida!.toFixed(1).replace(".", ",")} L, voltou com {volta!.toFixed(1).replace(".", ",")} L
              {nVoltas > 0 && consumido > 0
                ? ` · ≈ ${(consumido / nVoltas).toFixed(2).replace(".", ",")} L/volta em ${nVoltas} voltas`
                : ""}
            </p>
            <p className="nota">Sem canal de combustível no arquivo: números do box, não da telemetria.</p>
          </>
        ) : (
          <p className="nota">Sem canal de combustível neste arquivo.</p>
        )}
        {aoAbrir ? (
          <button type="button" className="ir-link" onClick={aoAbrir}>
            <span>ver detalhe</span>
            <span>&rsaquo;</span>
          </button>
        ) : aoInserir ? (
          <button type="button" className="ir-link" onClick={aoInserir}>
            <span>{consumido != null ? "atualizar informações de combustível" : "inserir informações de combustível"}</span>
            <span>&rsaquo;</span>
          </button>
        ) : null}
      </article>
    );
  }

  const validas = voltas.filter((v) => v.valida && v.litros != null);
  const ordenadas = [...validas].sort((a, b) => (a.litros ?? 0) - (b.litros ?? 0));
  const fora = new Set([ordenadas[0]?.n, ordenadas[ordenadas.length - 1]?.n]);
  const etapa = consumo.media_etapa;
  const bateria = consumo.media_bateria;

  const H = 140, PL = 42, PR = 10, PT = 12, PB = 22;
  const lo = Math.min(...litros) * 0.96, hi = Math.max(...litros) * 1.02;
  const x = escala(0, voltas.length - 1, PL, W - PR);
  const y = escala(lo, hi, H - PB, PT);
  const larg = Math.max(6, (W - PL - PR) / voltas.length - 6);
  const passoLabel = passoRotulo(voltas.length, W - PL - PR);

  return (
    <article className={`cartao${aoAbrir ? " chave" : ""}`}>
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
          <p className="eyebrow">Outing em escopo</p>
          <p className="heroi" style={{ fontSize: 28, color: "var(--muted)" }}>
            {bateria.disponivel ? `${bateria.litros_por_volta.toFixed(2)} L` : "sem outing"}
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
            // o ultimo (e o primeiro) quadrado passava da borda do card: a
            // largura era calculada pra caber ENTRE pontos vizinhos, mas nas
            // pontas o ponto esta em cima da propria margem (PL/PR), entao
            // metade da barra sobrava pra fora do plot. Aqui a barra e presa
            // aos limites [PL, W-PR] antes de desenhar, e nao so calculada
            // "no meio" e torcida pra caber.
            const xEsq = Math.max(PL, x(i) - larg / 2);
            const xDir = Math.min(W - PR, x(i) + larg / 2);
            return (
              <rect
                key={v.n}
                x={xEsq} y={y(v.litros)} width={Math.max(1, xDir - xEsq)} height={H - PB - y(v.litros)} rx={2}
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
          {voltas.map((v, i) => i % passoLabel === 0 && (
            <text key={v.n} className="eixo" x={x(i)} y={H - 6} textAnchor="middle">{v.n}</text>
          ))}
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

      {aoAbrir && (
        <button type="button" className="ir-link" onClick={aoAbrir}>
          <span>ver detalhe</span>
          <span>&rsaquo;</span>
        </button>
      )}
    </article>
  );
}
