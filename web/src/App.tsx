import { useSelecao } from "./state/selection";
import type { Relatorio } from "./types/contract";

// Casca do funil. Os 13 blocos entram aqui, um por vez, cada um recebendo
// dado por prop. Nada de conteudo inventado enquanto nao houver relatorio real.
const NIVEIS = [
  { id: "n0", titulo: "N0 Veredito", pergunta: "Como foi?", blocos: ["Melhor volta", "Nota do piloto", "Onde perdi tempo?"] },
  { id: "n1", titulo: "N1 Sessao", pergunta: "Qual volta?", blocos: ["Resumo das voltas", "Evolucao por volta", "Delta entre voltas", "Tabela estatistica"] },
  { id: "n2", titulo: "N2 Volta", pergunta: "Onde na pista?", blocos: ["Mapa da pista", "Onde ganhar tempo"] },
  { id: "n3", titulo: "N3 Trecho", pergunta: "O que fiz com os pes e as maos?", blocos: ["Traco no tempo", "Dispersao XY", "Canais matematicos"] },
] as const;

export default function App({ relatorio }: { relatorio?: Relatorio }) {
  const { volta, trecho } = useSelecao();

  return (
    <main>
      <header>
        <h1>SARU Analyzer</h1>
        <p>
          escopo: volta {volta ?? "-"} · trecho {trecho ?? "a volta inteira"}
        </p>
      </header>

      {!relatorio && <p>Sem relatorio carregado. O pipeline ainda nao emitiu saida.</p>}

      {NIVEIS.map((n) => (
        <section key={n.id}>
          <h2>
            {n.titulo} <small>{n.pergunta}</small>
          </h2>
          <ul>
            {n.blocos.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        </section>
      ))}
    </main>
  );
}
