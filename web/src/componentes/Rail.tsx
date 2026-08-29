import { useSelecao } from "../state/selection";
import { PAGINAS } from "./paginas";

// O navegador do funil. Cada pagina responde UMA pergunta, e a ordem e a das
// tres que o engenheiro nomeou: onde perdi, se estou melhorando, quanto
// gastei. Contexto, box e ficha de setup ficam fora do funil de proposito:
// nao sao um nivel de zoom sobre a volta, sao acessiveis de qualquer nivel.

export function Rail({ contextoIncompleto, onRecolher }: {
  contextoIncompleto: boolean;
  onRecolher: () => void;
}) {
  const { vista, irPara, setContextoAberto, setSetupAberto } = useSelecao();
  const atual = vista.tipo === "pagina" ? vista.id : null;

  return (
    <aside className="rail">
      <div className="rail-head">
        <button type="button" className="rail-toggle" onClick={onRecolher} aria-label="Recolher painel">
          &lsaquo;&lsaquo; ocultar
        </button>
        <div className="marca">
          <span className="g">SARU</span>
          <span className="v">poc v0</span>
        </div>
        <h1>Analyzer</h1>
        <p className="sub">funil de 4 níveis</p>
      </div>

      <nav className="niveis" aria-label="Níveis do funil">
        <button type="button" className="nivel" aria-current={vista.tipo === "geral"} onClick={() => irPara({ tipo: "geral" })}>
          <span className="n">&#9646;</span>
          <span><span className="t">Visão geral</span><span className="q">Veredito e os quadros</span></span>
        </button>
        {PAGINAS.map((p, i) => (
          <button key={p.id} type="button" className="nivel" aria-current={atual === p.id} onClick={() => irPara({ tipo: "pagina", id: p.id })}>
            <span className="n">{i + 1}</span>
            <span><span className="t">{p.titulo}</span><span className="q">{p.pergunta}</span></span>
          </button>
        ))}
      </nav>

      <div className="rail-sec">
        <p className="eyebrow">Fora do funil</p>
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--s1)", marginTop: "var(--s2)" }}>
          <button type="button" className="nivel raso" aria-current={vista.tipo === "box"} onClick={() => irPara({ tipo: "box" })}>
            <span className="n">&#9881;</span>
            <span><span className="t">Box</span><span className="q">Pressão a frio e tempo</span></span>
          </button>
          <button type="button" className={`nivel raso${contextoIncompleto ? " alerta" : ""}`} onClick={() => setContextoAberto(true)}>
            <span className="n">&#8801;</span>
            <span>
              <span className="t">{contextoIncompleto ? "Contexto incompleto" : "Contexto da bateria"}</span>
              <span className="q">Pneu, temperatura, notas</span>
            </span>
          </button>
          <button type="button" className="nivel raso" onClick={() => setSetupAberto(true)}>
            <span className="n">&#9636;</span>
            <span><span className="t">Ficha de setup</span><span className="q">Pneu, suspensão, transmissão</span></span>
          </button>
        </div>
      </div>
    </aside>
  );
}
