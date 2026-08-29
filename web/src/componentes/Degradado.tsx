import type { Degradado as TDegradado } from "../types/contract";

// Bloco sem dado DIZ por que. Default silencioso e proibido: era exatamente o
// bug B2, o layout do cliente entrando por baixo quando o arquivo nao declara
// venue, e o piloto recebendo o nome de uma curva que nao e a dele.
export function Degradado({ estado }: { estado: TDegradado }) {
  return (
    <div className="deg">
      <span className="ico">!</span>
      <p>{estado.texto}</p>
    </div>
  );
}
