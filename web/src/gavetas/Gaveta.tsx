import type { ReactNode } from "react";

export function Gaveta({ aberta, titulo, eyebrow, onFechar, children }: {
  aberta: boolean;
  titulo: string;
  eyebrow: string;
  onFechar: () => void;
  children: ReactNode;
}) {
  return (
    <>
      <div className={`veu${aberta ? " on" : ""}`} onClick={onFechar} />
      <aside className={`gaveta${aberta ? " aberta" : ""}`} aria-hidden={!aberta}>
        <header>
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h3>{titulo}</h3>
          </div>
          <button type="button" className="fechar" onClick={onFechar} aria-label="Fechar">&#10005;</button>
        </header>
        {children}
      </aside>
    </>
  );
}
