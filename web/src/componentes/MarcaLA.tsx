// A marca da LA, em SVG inline.
//
// **Por que nao e PNG.** Os arquivos `la_software_*.png` do repo do site sao
// arte antiga, e nao a identidade que lassoftware.com.br usa hoje: o site
// desenha a marca como monograma vetorial (`stroke #12b7a3`, o mesmo do
// favicon inline dele) mais o nome em texto. Foi por isso que as tentativas
// com PNG sairam erradas tres vezes: a fonte estava errada, nao o recorte.
//
// Vetor tambem resolve o resto de graca: nao ha asset pra faltar, nao ha cache
// de CDN pra furar a cada deploy (o `la-software.png` ficou 4 horas servindo a
// versao antiga pelo Cloudflare), e a cor do texto acompanha o tema.
//
// Geometria transcrita do favicon do proprio site (viewBox 0 0 48 44,
// stroke-width 4, cap square, join miter): o "L" e o "A" como dois tracos.

export function MarcaLA({ className }: { className?: string }) {
  return (
    // link pro site da LA (pedido de 29/08); nova aba pra nao derrubar a
    // sessao de analise de quem so quis ver quem assina
    <a
      href="https://lassoftware.com.br"
      target="_blank"
      rel="noopener noreferrer"
      className={`marca-la-svg${className ? ` ${className}` : ""}`}
    >
      <svg viewBox="0 0 48 44" aria-hidden="true" focusable="false">
        <g fill="none" stroke="#12b7a3" strokeWidth="4" strokeLinecap="square" strokeLinejoin="miter">
          <path d="M9 6 V38 H38" />
          <path d="M24 38 L31 12 L38 38" />
        </g>
      </svg>
      {/* O nome completo e "LA Soluções de Software", como o site assina. */}
      <span className="nome">
        LA Soluções
        <span className="cauda"> de Software</span>
      </span>
    </a>
  );
}
