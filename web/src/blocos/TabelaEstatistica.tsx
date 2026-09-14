import type { SerieAmostras } from "../types/contract";
import { sinal } from "../dados/formato";

// Bloco 7. Os numeros crus da volta em escopo contra a referencia. Sem grafico
// de proposito: e a tabela que o engenheiro confere quando desconfia do resto.
const CANAIS: { id: string; rotulo: string; unidade: string; cor: string; absoluto?: boolean }[] = [
  { id: "velocidade", rotulo: "Velocidade", unidade: "km/h", cor: "--ch-spd" },
  { id: "acelerador", rotulo: "Acelerador", unidade: "%", cor: "--ch-thr" },
  { id: "freio", rotulo: "Freio", unidade: "%", cor: "--ch-brk" },
  { id: "direcao", rotulo: "Direção", unidade: "°", cor: "--ch-str" },
  { id: "acel_lat", rotulo: "Acel. lateral", unidade: "g", cor: "--ch-spd", absoluto: true },
];

export function TabelaEstatistica({ a, b, ehRef }: { a: SerieAmostras; b: SerieAmostras; ehRef: boolean }) {
  return (
    <article className="cartao">
      <header><h4>Tabela estatística</h4><span className="no">bloco 7</span></header>
      <div className="tabela-wrap">
        <table className="leitura">
          <thead>
            <tr><th>Canal</th><th>Mín</th><th>Méd</th><th>Máx</th><th>&Delta; vs ref</th></tr>
          </thead>
          <tbody>
            {CANAIS.map((c) => {
              const prep = (s: SerieAmostras) => {
                const v = s.canais[c.id] ?? [];
                return c.absoluto ? v.map(Math.abs) : v;
              };
              const va = prep(a);
              const vb = prep(b);
              if (va.length === 0) return null;
              const media = (x: number[]) => x.reduce((p, q) => p + q, 0) / x.length;
              const d = media(va) - media(vb);
              return (
                <tr key={c.id}>
                  <td>
                    <span className="amostra-cor" style={{ background: `var(${c.cor})` }} />
                    {c.rotulo} <span style={{ color: "var(--faint)" }}>{c.unidade}</span>
                  </td>
                  <td className="mono">{Math.min(...va).toFixed(1)}</td>
                  <td className="mono">{media(va).toFixed(1)}</td>
                  <td className="mono">{Math.max(...va).toFixed(1)}</td>
                  <td className={`mono ${d >= 0 ? "ganho" : "perde"}`}>
                    {ehRef ? <span className="tag marca">ref</span> : sinal(d, 1)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </article>
  );
}
