import type { MelhorVolta as TMelhorVolta } from "../types/contract";
import { tempo } from "../dados/formato";

// Bloco 1, no N0. A guarda do B1 vive aqui: se a soma dos melhores setores
// passasse a melhor volta, a ideal e SUPRIMIDA em vez de exibida. O bug antigo
// somava setores de Interlagos numa volta de kart e cuspia uma volta ideal
// impossivel; a invariante agora e visivel na tela, nao so no teste.
export function MelhorVolta({ dados, bateria, onAbrir }: {
  dados: TMelhorVolta;
  /** Bateria DA MELHOR VOLTA, nao a do escopo: a frase fala da volta 7, e
      mostrar a bateria da volta 13 ao lado dela seria mentira de contexto. */
  bateria: string | null;
  onAbrir: () => void;
}) {
  const ok = !dados.ideal_suprimida;
  return (
    <button type="button" className="cartao chave" onClick={onAbrir}>
      <header>
        <h4>Melhor volta</h4>
        <span className="no">bloco 1</span>
        <span className="dir">
          <span className={`pill ${ok ? "pill-ok" : "pill-warn"}`}>
            {ok ? "ideal <= melhor" : "invariante violada"}
          </span>
        </span>
      </header>

      <p className="heroi">{tempo(dados.melhor_volta_s)}</p>
      <p className="heroi-sub">
        volta <b>{dados.melhor_volta_n}</b> de {dados.voltas_totais}
        {bateria ? <> · {bateria}</> : null}
      </p>

      <div style={{ marginTop: "var(--s4)", width: "100%" }}>
        <div className="kv">
          <span className="k">Volta ideal <span style={{ color: "var(--faint)" }}>(melhores setores)</span></span>
          <span className="v">{ok && dados.volta_ideal_s != null ? tempo(dados.volta_ideal_s) : "suprimida"}</span>
        </div>
        <div className="kv">
          <span className="k">Margem para a ideal</span>
          <span className="v">
            {ok && dados.margem_para_ideal_s != null ? `-${dados.margem_para_ideal_s.toFixed(3)} s` : "-"}
          </span>
        </div>
        <div className="kv">
          <span className="k">Voltas válidas</span>
          <span className="v">{dados.voltas_validas} de {dados.voltas_totais}</span>
        </div>
      </div>

      <span className="ir"><span>ver detalhe</span><span>&rsaquo;</span></span>
    </button>
  );
}
