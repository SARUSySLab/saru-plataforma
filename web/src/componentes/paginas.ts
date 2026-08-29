import type { PaginaId } from "../state/selection";

// Cada pagina responde UMA pergunta, e a ordem e a das tres que o engenheiro
// nomeou: onde perdi, se estou melhorando, quanto gastei. Contexto, box e
// ficha de setup ficam fora do funil de proposito: nao sao um nivel de zoom
// sobre a volta, sao acessiveis de qualquer nivel.
//
// Mora em arquivo proprio, e nao junto do Rail, porque exportar constante do
// mesmo arquivo que exporta componente quebra o fast refresh do Vite.
export const PAGINAS: { id: PaginaId; titulo: string; pergunta: string }[] = [
  { id: "perdas", titulo: "Onde ganhar tempo", pergunta: "Onde perdi, e o que treinar primeiro?" },
  { id: "melhor_volta", titulo: "Melhor volta", pergunta: "Qual foi o teto da sessão?" },
  { id: "mapa", titulo: "Mapa da pista", pergunta: "Onde na pista isso aconteceu?" },
  { id: "evolucao", titulo: "Evolução por volta", pergunta: "Estou melhorando?" },
  { id: "consumo", titulo: "Consumo", pergunta: "Quanto gastei?" },
  { id: "voltas", titulo: "Resumo das voltas", pergunta: "Qual volta olhar?" },
  { id: "traco", titulo: "Traço no tempo", pergunta: "O que fiz com os pés e as mãos?" },
];
