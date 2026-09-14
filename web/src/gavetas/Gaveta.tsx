import type { ReactNode } from "react";

// Padrao do sistema (pedido de 29/08): contexto da bateria e ficha de setup
// abrem como MODAL centrado, igual aos cadastros do dia de pista, e nao mais
// como gaveta lateral. O nome do componente fica: quem importa nao precisa
// saber da mudanca de forma, e o historico do porque esta no git.
export function Gaveta({ aberta, titulo, eyebrow, onFechar, children }: {
  aberta: boolean;
  titulo: string;
  eyebrow: string;
  onFechar: () => void;
  children: ReactNode;
}) {
  if (!aberta) return null;
  return (
    <div className="modal-veu" onClick={onFechar} role="presentation">
      <div
        className="modal-cartao modal-gaveta"
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-cabeca">
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h3>{titulo}</h3>
          </div>
          <button type="button" className="ghost" onClick={onFechar} aria-label="Fechar">&#10005;</button>
        </header>
        {children}
      </div>
    </div>
  );
}
