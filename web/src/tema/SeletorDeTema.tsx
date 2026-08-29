import { useTema } from "./useTema";

// UM botao compacto que ALTERNA claro <-> escuro (pedido de 29/08: so existem
// os dois modos; o "auto" que seguia o sistema saiu do ciclo).

export function SeletorDeTema() {
  const { tema, setTema } = useTema();
  const proximo = tema === "claro" ? "escuro" : "claro";
  return (
    <button
      type="button"
      className="tema-ciclo"
      title={`Tema: ${tema}. Clique para ${proximo}.`}
      onClick={() => setTema(proximo)}
    >
      <span aria-hidden="true">{tema === "claro" ? "○" : "●"}</span> tema: {tema}
    </button>
  );
}
