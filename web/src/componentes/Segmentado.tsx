// Controle de modo. Botoes lado a lado em vez de menu suspenso: as opcoes sao
// poucas e a comparacao entre elas e o proprio ponto, entao escondê-las num
// dropdown esconde a escolha.
export function Segmentado<T extends string>({ valor, opcoes, onEscolher, colunas }: {
  valor: T;
  opcoes: { id: T; rotulo: string; desabilitado?: boolean }[];
  onEscolher: (v: T) => void;
  colunas?: boolean;
}) {
  return (
    <div className={`segmentado${colunas ? " igual" : ""}`} style={colunas ? { gridTemplateColumns: `repeat(${opcoes.length}, minmax(0, 1fr))` } : undefined}>
      {opcoes.map((o) => (
        <button
          key={o.id}
          type="button"
          aria-pressed={valor === o.id}
          disabled={o.desabilitado}
          onClick={() => onEscolher(o.id)}
        >
          {o.rotulo}
        </button>
      ))}
    </div>
  );
}
