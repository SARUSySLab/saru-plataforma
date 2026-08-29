// DECISAO PENDENTE (Lucas): este arquivo existe separado de contract.ts por
// uma escolha de modelagem que ainda nao foi confirmada com voce. O
// contract.ts de hoje e o contrato de LEITURA (saida da etapa 7, o
// relatorio). O bloco 15 (contexto de sessao) e diferente: e CAPTURA, e
// acontece no upload, nao no dashboard (plano, "Dashboard: organizacao
// visual e semantica", nota sobre o bloco 15; e decisao 6, "o sistema
// pergunta o que falta"). Misturar leitura e escrita num arquivo so e uma
// escolha, entao separei em vez de decidir sozinho. Opcoes, com tradeoff:
//
//   (A) Este arquivo separado (o que esta implementado aqui). Contract.ts
//       fica limpo, so leitura; ingestao.ts so escrita. Custo: dois lugares
//       pra olhar quando o assunto e "contexto de sessao" (o formulario aqui,
//       o formato salvo em ContextoSessao/ContextoPneu no contract.ts).
//   (B) Um unico arquivo contract.ts com leitura e escrita juntas. Menos
//       arquivo pra navegar, mas contract.ts deixa de ser "o que o backend
//       devolve" e vira "tudo que trafega", o que mistura duas perguntas
//       diferentes (o que a etapa 7 emite vs o que o upload pede).
//   (C) Pasta propria (types/contexto/{leitura,captura}.ts ou similar) se o
//       contexto de sessao crescer mais (ex.: virar tambem tipo de payload de
//       API de upload com validacao). Mais estrutura do que a PoC precisa
//       agora, provavel over-engineering neste estagio.
//
// Implementei (A) por ser a alternativa mais conservadora: nao mistura
// contratos de direcoes diferentes e e a que menos compromete decisao futura.
// Se voce preferir (B) ou (C), e um rename/merge de arquivo, nao um redesenho
// de tipo.

import type { ContextoPneu } from "./contract";

/**
 * Formulario de captura do bloco 15, decisoes 5 e 6. Roda no upload da
 * gravacao (ou da bateria, quando a espinha operacional existe, decisao 16).
 * Campo ausente ou envelhecido e o gatilho pra pergunta ativa da decisao 6
 * ("ultimo envio foi ha 2h, mudou temperatura ou vento?"); esse texto de
 * pergunta e responsabilidade do backend, este tipo so carrega o que foi
 * respondido (ou deixado em branco pra o backend decidir se pergunta).
 */
export interface CapturaContextoSessao {
  /** bateria_id OU gravacao_id, nunca os dois (decisao 16: dono polimorfico). */
  dono: { tipo: "bateria"; id: string } | { tipo: "gravacao"; id: string };
  pneu: ContextoPneu | null;
  temperatura_ar_c: number | null;
  temperatura_pista_c: number | null;
  vento_kmh: number | null;
  horario: string | null;
  notas_piloto: string | null;
  notas_engenheiro: string | null;
  /**
   * Timestamp do ultimo contexto capturado pra essa bateria/gravacao, se
   * houver. O backend usa pra decidir se pergunta "mudou alguma coisa desde
   * entao" (decisao 6) em vez de assumir que continua valendo.
   */
  contexto_anterior_em: string | null;
}
