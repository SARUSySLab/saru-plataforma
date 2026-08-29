import { Gaveta } from "./Gaveta";

// Bloco 13. Contexto, nao nivel: nao responde "como foi", responde "com o
// que". Gaveta acessivel de qualquer nivel, nunca no fluxo vertical, senao
// empurra o sinal para baixo da dobra.
export function FichaDeSetup({ aberta, setup, onFechar }: {
  aberta: boolean;
  setup: Record<string, string | number> | null;
  onFechar: () => void;
}) {
  return (
    <Gaveta aberta={aberta} titulo="Ficha de setup" eyebrow="Contexto · bloco 13" onFechar={onFechar}>
      {!setup ? (
        <p className="nota">Sem ficha de setup para esta gravação.</p>
      ) : (
        <div className="grupo">
          {Object.entries(setup).map(([k, v]) => (
            <div className="kv" key={k}>
              <span className="k">{k}</span>
              <span className="v">{v}</span>
            </div>
          ))}
        </div>
      )}
      <p className="nota">Comparação com outra sessão entra quando houver uma segunda ficha.</p>
    </Gaveta>
  );
}
