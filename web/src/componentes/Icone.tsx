// Iconografia da sidebar: traço monocromático em SVG inline, herdando a cor
// do texto (currentColor). Escolha de 29/08, substituindo emoji: emoji vem
// colorido, muda de desenho por sistema operacional e destoa do resto da
// interface; traço fino fica igual em todo lugar e acompanha o tema. Sem
// biblioteca de ícones de propósito: doze paths não justificam dependência
// (regra da casa: dependência nova é decisão do Lucas).

const PATHS: Record<string, React.ReactNode> = {
  // campeonato: bandeira de chegada no mastro
  bandeira: (
    <>
      <path d="M5 21V4" />
      <path d="M5 4h13l-2.5 3.5L18 11H5" />
    </>
  ),
  // visão geral: quatro quadros, o dashboard
  grade: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </>
  ),
  // onde ganhar tempo: relógio
  relogio: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  // melhor volta: troféu
  trofeu: (
    <>
      <path d="M7 4h10v5a5 5 0 0 1-10 0z" />
      <path d="M7 5H4v1.5A3.5 3.5 0 0 0 7.5 10" />
      <path d="M17 5h3v1.5A3.5 3.5 0 0 1 16.5 10" />
      <path d="M12 14v4" />
      <path d="M8 21h8" />
      <path d="M9.5 18h5" />
    </>
  ),
  // mapa da pista: pino de localização
  pino: (
    <>
      <path d="M12 21s-7-5.4-7-11a7 7 0 0 1 14 0c0 5.6-7 11-7 11z" />
      <circle cx="12" cy="10" r="2.5" />
    </>
  ),
  // evolução: tendência subindo
  tendencia: (
    <>
      <path d="M3 17l6-6 4 4 8-8" />
      <path d="M15 7h6v6" />
    </>
  ),
  // consumo: gota
  gota: <path d="M12 3s6 6.4 6 10.4a6 6 0 0 1-12 0C6 9.4 12 3 12 3z" />,
  // resumo das voltas: lista
  lista: (
    <>
      <path d="M4 6h2" />
      <path d="M4 12h2" />
      <path d="M4 18h2" />
      <path d="M9 6h11" />
      <path d="M9 12h11" />
      <path d="M9 18h11" />
    </>
  ),
  // traço no tempo: linha de atividade
  atividade: <path d="M3 12h4l3-7 4 14 3-7h4" />,
  // dia de pista: calendário
  calendario: (
    <>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18" />
      <path d="M8 3v4" />
      <path d="M16 3v4" />
    </>
  ),
  // enviar telemetria: seta pra cima
  subir: (
    <>
      <path d="M12 16V4" />
      <path d="M6 10l6-6 6 6" />
      <path d="M4 20h16" />
    </>
  ),
  // box: chave de boca
  chave: (
    <path d="M14.7 6.3a4.5 4.5 0 0 0-5.9 5.9L3 18v3h3l5.8-5.8a4.5 4.5 0 0 0 5.9-5.9l-3.1 3.1-2.7-.3-.3-2.7z" />
  ),
  // contexto: nota com linhas
  nota: (
    <>
      <path d="M14 2H6a1 1 0 0 0-1 1v18a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V7z" />
      <path d="M14 2v5h5" />
      <path d="M9 13h6" />
      <path d="M9 17h6" />
    </>
  ),
  // ficha de setup: ajustes deslizantes
  ajustes: (
    <>
      <path d="M4 7h9" />
      <path d="M17 7h3" />
      <path d="M15 5v4" />
      <path d="M4 17h3" />
      <path d="M11 17h9" />
      <path d="M9 15v4" />
    </>
  ),
};

export function Icone({ nome }: { nome: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="16"
      height="16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[nome] ?? <circle cx="12" cy="12" r="9" />}
    </svg>
  );
}
