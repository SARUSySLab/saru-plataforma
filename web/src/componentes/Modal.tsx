import type { ReactNode } from "react";

/**
 * Modal flutuante mínimo da casa (pedido de 29/08: cadastro de evento,
 * sessão e bateria sai do fluxo da página e vira sobreposição).
 *
 * Fecha no véu e no ✕, nunca sozinho: formulário pela metade é decisão do
 * usuário, não do componente. Sem biblioteca de dialog de propósito, é uma
 * sobreposição fixa com um cartão dentro, o mesmo padrão do véu das gavetas.
 */
export function Modal({ titulo, aberto, aoFechar, children }: {
  titulo: string;
  aberto: boolean;
  aoFechar: () => void;
  children: ReactNode;
}) {
  if (!aberto) return null;
  return (
    <div className="modal-veu" onClick={aoFechar} role="presentation">
      <div
        className="modal-cartao"
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-cabeca">
          <h3>{titulo}</h3>
          <button type="button" className="ghost" onClick={aoFechar} aria-label="Fechar">✕</button>
        </header>
        {children}
      </div>
    </div>
  );
}
