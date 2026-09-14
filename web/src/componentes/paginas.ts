import type { PaginaId } from "../state/selection";

// Cada pagina responde UMA pergunta, e a ordem e a das tres que o engenheiro
// nomeou: onde perdi, se estou melhorando, quanto gastei. Contexto, box e
// ficha de setup ficam fora do funil de proposito: nao sao um nivel de zoom
// sobre a volta, sao acessiveis de qualquer nivel.
//
// Mora em arquivo proprio, e nao junto do Rail, porque exportar constante do
// mesmo arquivo que exporta componente quebra o fast refresh do Vite.
// O icone e SEMANTICO, um por pergunta, no lugar do numero de nivel que a
// sidebar usava: numero dizia a ordem do funil, mas nao dizia nada sobre o
// que a pagina responde. O valor e o NOME de um traço em `Icone.tsx`
// (traço monocromatico, nao emoji: emoji muda por sistema e destoa do
// resto, feedback de 29/08).
// Ordem da sidebar (pedido de 29/08): perdas, melhor volta, consumo, mapa,
// evolucao, traco, e o resumo das voltas fecha a lista.
export const PAGINAS: { id: PaginaId; titulo: string; pergunta: string; icone: string }[] = [
  { id: "perdas", titulo: "Onde ganhar tempo", pergunta: "Onde perdi, e o que treinar primeiro?", icone: "relogio" },
  { id: "melhor_volta", titulo: "Melhor volta", pergunta: "Qual foi o teto da sessão?", icone: "trofeu" },
  { id: "consumo", titulo: "Consumo", pergunta: "Quanto gastei?", icone: "gota" },
  { id: "mapa", titulo: "Mapa da pista", pergunta: "Onde na pista isso aconteceu?", icone: "pino" },
  { id: "evolucao", titulo: "Evolução por volta", pergunta: "Estou melhorando?", icone: "tendencia" },
  { id: "traco", titulo: "Traço no tempo", pergunta: "O que fiz com os pés e as mãos?", icone: "atividade" },
  { id: "voltas", titulo: "Resumo das voltas", pergunta: "Qual volta olhar?", icone: "lista" },
];
