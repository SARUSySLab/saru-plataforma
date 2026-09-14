import type { VoltaResumo } from "../types/contract";
import { useSelecao } from "../state/selection";
import { sinal, tempo } from "../dados/formato";

// Bloco 4. Clique numa linha e ela vira o escopo do dashboard inteiro.
export function ResumoDasVoltas({ voltas, melhorN, refAtiva, emEscopo }: {
  voltas: VoltaResumo[];
  melhorN: number;
  refAtiva: number | "media";
  emEscopo: number;
}) {
  const { setVolta } = useSelecao();
  const melhoresSetores = [0, 1, 2].map((i) =>
    Math.min(...voltas.filter((v) => v.valida).map((v) => v.setores_s[i] ?? Infinity)),
  );

  return (
    <article className="cartao">
      <header>
        <h4>Resumo das voltas</h4>
        <span className="no">bloco 4</span>
        <span className="dir"><span className="pill pill-brand">clique = escopo</span></span>
      </header>
      <div className="tabela-wrap">
        <table>
          <thead>
            <tr>
              <th>Volta</th><th>Bat.</th><th>Tempo</th><th>S1</th><th>S2</th><th>S3</th>
              <th>V.máx</th><th>L/volta</th><th>&Delta; ref</th>
            </tr>
          </thead>
          <tbody>
            {voltas.map((v) => {
              const ehRef = refAtiva !== "media" && refAtiva === v.n;
              return (
                <tr key={v.n} aria-selected={v.n === emEscopo} onClick={() => setVolta(v.n)}>
                  <td>
                    {v.n}
                    {!v.valida && <span className="tag">{v.motivo_invalida}</span>}
                  </td>
                  <td>{v.bateria ? <span className="tag marca">{v.bateria.rotulo.replace("Bateria ", "B")}</span> : <span className="tag">nula</span>}</td>
                  <td className="mono" style={{ fontWeight: v.n === melhorN ? 700 : 400, color: v.n === melhorN ? "var(--brand)" : undefined }}>
                    {tempo(v.tempo_s)}
                  </td>
                  {v.setores_s.map((s, i) => (
                    <td key={i} className="mono" style={{ color: s != null && Math.abs(s - melhoresSetores[i]) < 1e-9 ? "var(--d-gain)" : undefined }}>
                      {s?.toFixed(3) ?? "-"}
                    </td>
                  ))}
                  <td className="mono">{v.v_max_kmh?.toFixed(0) ?? "-"}</td>
                  <td className="mono">{v.litros?.toFixed(2) ?? "-"}</td>
                  <td className={`mono ${v.delta_referencia_s > 0 ? "perde" : "ganho"}`}>
                    {ehRef ? <span className="tag marca">ref</span> : sinal(v.delta_referencia_s)}
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
