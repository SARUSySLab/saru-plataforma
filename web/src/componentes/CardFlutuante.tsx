import type { ReactNode } from "react";

/**
 * Card que flutua sobre o grafico, preso a uma posicao em pixels do host.
 * Nao captura ponteiro: se capturasse, ele roubaria o proprio evento de
 * hover que o faz existir e o grafico piscaria embaixo do cursor.
 *
 * A posicao e limitada a caixa do host para o card nao sair pela borda quando
 * o cursor chega perto da ponta, que e justamente onde estao os trechos mais
 * interessantes de uma volta (a reta antes da freada e a saida da ultima).
 */
export function CardFlutuante({ x, y, largura, titulo, linhas, rodape }: {
  x: number;
  y: number;
  largura: number;
  titulo: string;
  linhas: { rot: string; a?: ReactNode; b?: ReactNode; unico?: ReactNode; cor?: string }[];
  rodape?: ReactNode;
}) {
  const L = 210;
  const esq = Math.max(4, Math.min(largura - L - 4, x - L / 2));
  return (
    <div className="flutuante" style={{ left: esq, top: Math.max(4, y), width: L }}>
      <div className="tt">{titulo}</div>
      {linhas.map((l) => (
        <div className="lin" key={l.rot}>
          <span>{l.rot}</span>
          <span style={l.cor ? { color: l.cor } : undefined}>
            {l.unico ?? (
              <>
                <b style={{ color: "var(--lap-a)" }}>{l.a}</b> <b style={{ color: "var(--lap-b)" }}>{l.b}</b>
              </>
            )}
          </span>
        </div>
      ))}
      {rodape && <div className="rodape-flut">{rodape}</div>}
    </div>
  );
}
