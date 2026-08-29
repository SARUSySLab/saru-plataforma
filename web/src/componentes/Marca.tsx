import { useState } from "react";
import { useTemaEfetivo } from "../tema/useTema";

/**
 * Imagem de marca que escolhe a variante pelo tema e sobrevive a asset ausente.
 *
 * O `onError` nao e paranoia: as variantes clara e escura sao geradas em
 * momentos diferentes, e um deploy que sai no meio disso deixaria um `img`
 * quebrado no header, que e pior do que a variante de contraste errado. Cair
 * pra irma e degradacao visivel e legivel; icone de imagem quebrada nao e.
 */
export function Marca({
  claro,
  escuro: escuroSrc,
  alt,
  className,
}: {
  /** arquivo pra usar quando o tema e CLARO (arte escura) */
  claro: string;
  /** arquivo pra usar quando o tema e ESCURO (arte clara) */
  escuro: string;
  alt: string;
  className?: string;
}) {
  const temaEscuro = useTemaEfetivo() === "escuro";
  const preferida = temaEscuro ? escuroSrc : claro;
  const [src, setSrc] = useState(preferida);
  const [tentouIrma, setTentouIrma] = useState(false);

  // trocar de tema volta pra preferida, senao o fallback de uma sessao
  // anterior gruda pra sempre
  if (!tentouIrma && src !== preferida) setSrc(preferida);

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => {
        if (tentouIrma) return;
        setTentouIrma(true);
        setSrc(temaEscuro ? claro : escuroSrc);
      }}
    />
  );
}
