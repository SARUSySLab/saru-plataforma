import type { Ressalva } from "../types/contract";

// A condicao que relativiza o insight (decisao 7). E a degradacao declarada do
// B2 aplicada a recomendacao: sem coordenada a tela diz que nao sabe onde, e
// sem contexto de pneu ela diz sob que hipotese o ganho vale. Usa a cor de
// destaque, nao a de alerta: a ressalva nao e um erro do sistema, e a leitura.
export function Insight({ ressalva }: { ressalva: Ressalva | null }) {
  if (!ressalva) return null;
  return (
    <div className="insight">
      <span className="ci">Insight</span>
      <p>{ressalva.descricao}</p>
    </div>
  );
}
