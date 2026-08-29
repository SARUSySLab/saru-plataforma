import type { PerdaPorTrecho, Talvez } from "../types/contract";
import { Fases } from "../componentes/Fases";
import { Insight } from "../componentes/Insight";
import { Degradado } from "../componentes/Degradado";

// Bloco 3, no N0. Tres pontos a melhorar, no formato que o engenheiro pediu:
// "eu colocaria tres pontos a melhorar, o tempo total e o tempo separado".
// Le a MESMA fonte do bloco 9 (perdas por trecho), so truncada no top 3: eram
// dois codigos que podiam discordar entre si na mesma tela.
export function OndePerdiTempo({ perdas, onAbrir }: {
  perdas: Talvez<{ itens: PerdaPorTrecho[] }>;
  onAbrir: () => void;
}) {
  const disponivel = perdas.disponivel;
  const itens = disponivel ? perdas.itens : [];
  const recuperavel = itens.reduce((a, p) => a + Math.max(0, p.perda_s), 0);

  return (
    <button type="button" className="cartao chave" onClick={onAbrir}>
      <header>
        <h4>Onde perdi tempo?</h4>
        <span className="no">bloco 3</span>
        <span className="dir"><span className="pill pill-brand">3 pontos a melhorar</span></span>
      </header>

      {!disponivel ? (
        <Degradado estado={perdas} />
      ) : itens.length === 0 ? (
        <p style={{ margin: 0, fontSize: 12, color: "var(--faint)" }}>
          Nada a ganhar contra a referência atual. Troque a volta ou a comparação no painel.
        </p>
      ) : (
        <>
          {itens.map((p, i) => (
            <div className="perda" key={p.trecho_id}>
              <div className="perda-topo">
                <span className="rk">{i + 1}</span>
                <span className="nm">{p.rotulo}</span>
                <span className="dt">+{p.perda_s.toFixed(3)} s</span>
              </div>
              {p.tempo_por_fase.disponivel && <Fases fase={p.tempo_por_fase} />}
            </div>
          ))}
          <div className="rodape">
            <span>Recuperável nestes 3 trechos</span>
            <b style={{ color: "var(--d-loss)" }}>+{recuperavel.toFixed(3)} s</b>
          </div>
          <Insight ressalva={itens[0]?.ressalva ?? null} />
        </>
      )}

      <span className="ir"><span>abrir onde ganhar tempo</span><span>&rsaquo;</span></span>
    </button>
  );
}
