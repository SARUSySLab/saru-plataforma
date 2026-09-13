// Catalogo de gravacoes, envio de bundle e captura de contexto.
//
// Espelha o que `src/saru_poc/api.py` serve, sem inventar campo. O tipo
// `Gravacao` abaixo e a resposta de `GET /api/gravacoes`, que NAO esta no
// contract.ts porque contract.ts e a saida da etapa 7 (o relatorio), e o
// catalogo e outra coisa: e o que existe pra escolher antes de haver relatorio.

import { enviar, enviarArquivos, obter } from "./api";
import type { CapturaContextoSessao } from "../types/ingestao";
import type { SerieAmostras } from "../types/contract";

/** Uma linha do catalogo. `voltas > 0` e o sinal de que ha relatorio pra pedir. */
export interface Gravacao {
  gravacao_id: string;
  label: string | null;
  layout_id: string | null;
  layout_nome: string | null;
  capturado_em: string | null;
  /**
   * A espinha a que a gravacao pertence, ou null quando o arquivo e solto
   * (decisao D3). Vem no catalogo, e nao numa segunda consulta, porque a tela
   * de analise e a do dia de pista precisam das duas coisas ao mesmo tempo.
   */
  bateria_id: string | null;
  sessao_id: string | null;
  evento_id: string | null;
  evento_nome: string | null;
  duracao_s: number | null;
  /** Sai de zero quando a etapa 5 (corte de voltas) termina. Sem volta nao ha N0 nem N1. */
  voltas: number;
  /** Sai de zero quando a etapa 6 termina. Sem trecho nao ha N2. */
  trechos: number;
  /** D3-B: 'referencia' e arquivo importado so pra comparar; nunca e a volta analisada. */
  finalidade: "piloto" | "referencia";
}

export interface RecepcaoDeBundle {
  gravacao_id: string;
  /** Bundle ja recebido antes (dedupe por hash). Nesse caso o pipeline nao roda de novo. */
  ja_existia: boolean;
  arquivos: { papel: string; nome: string; formato: string | null }[];
  recusados: unknown[];
}

/** D1-A (29/08): um envio de N capturas vira N gravacoes. Sidecars da mesma
 *  captura (mesmo radical de nome) continuam juntos na mesma gravacao. */
export interface RecepcaoDeUpload {
  gravacoes: RecepcaoDeBundle[];
  pipeline: string;
}

export function listarGravacoes(comVolta = false): Promise<Gravacao[]> {
  return obter<Gravacao[]>("/gravacoes", { com_volta: comVolta });
}

/**
 * Serie de amostras de UMA volta, ou a media das validas.
 *
 * Fica fora do relatorio porque amostra e pesada: o relatorio cabe numa
 * resposta e a serie vem sob demanda, uma por volta. Essa separacao e do
 * backend, nao escolha do front.
 */
export function obterAmostras(
  gravacaoId: string,
  volta: number | "media",
): Promise<SerieAmostras> {
  return obter<SerieAmostras>(`/gravacoes/${gravacaoId}/amostras`, { volta });
}

/**
 * Manda o bundle e devolve 202 com o id da gravacao.
 *
 * O processamento NAO acontece dentro deste request: a recepcao e sincrona
 * (hash e registro), as etapas 2 a 6 rodam em background no servidor. Quem
 * chama isto tem que acompanhar por `listarGravacoes` ate `voltas > 0`, e nao
 * esperar relatorio na resposta. Ver `useProcessamento`.
 */
export function enviarBundle(
  arquivos: File[],
  aoProgredir?: (fracao: number) => void,
  finalidade: "piloto" | "referencia" = "piloto",
): Promise<RecepcaoDeUpload> {
  const formulario = new FormData();
  for (const arquivo of arquivos) formulario.append("arquivos", arquivo, arquivo.name);
  // D3-B: referencia entra na base de comparacao, nunca vira volta analisada
  formulario.append("finalidade", finalidade);
  return enviarArquivos<RecepcaoDeUpload>("/gravacoes", formulario, aoProgredir);
}

/**
 * Captura de contexto pendurada na gravacao (bloco 15).
 *
 * `dono` sai do corpo de proposito: quem manda no dono e a URL, e o banco exige
 * exatamente um (`num_nonnulls(bateria_id, gravacao_id) = 1`). Mandar os dois
 * seria duas verdades pro mesmo fato.
 */
export function registrarContexto(
  gravacaoId: string,
  captura: Omit<CapturaContextoSessao, "dono">,
): Promise<{ contexto_id: string; criado_em: string }> {
  return enviar(`/gravacoes/${gravacaoId}/contexto`, captura);
}


/**
 * Em que pe esta o processamento, com o MOTIVO quando ele para sem render volta.
 *
 * Existe porque contagem zero e ambigua: "ainda processando" e "nao vai dar" sao
 * a mesma coisa vista de `GET /api/gravacoes`. A tela ficava girando pra sempre
 * num caso em que o servidor ja sabia a resposta.
 */
export interface EstadoDaGravacao {
  etapa: "recebido" | "ingestao" | "resolucao_pista" | "corte_voltas" | "pronto";
  /** true quando o pipeline terminou, com ou sem sucesso. Parar de perguntar. */
  concluido: boolean;
  voltas: number;
  trechos: number;
  motivo: string | null;
  /** O que o usuario pode FAZER a respeito. Erro sem saida e erro decorativo. */
  sugestao: string | null;
  arquivos: number;
  /**
   * Estado da leitura dos arquivos do bundle (excecao 3e do E-UC-01, issue #2).
   * `null` enquanto nenhum arquivo foi ingerido. `parcial` e o caso do formato
   * que so tem leitor de inventario (`.gpk`, `.rrk`): o arquivo entrou, o
   * cabecalho foi lido e nenhum canal foi decodificado. `motivo` e a mesma
   * coisa em prosa, e fica `null` quando o status e `ok`.
   */
  ingestao: { status: "ok" | "parcial" | "falhou"; motivo: string | null } | null;
}

export const estadoDaGravacao = (gravacaoId: string) =>
  obter<EstadoDaGravacao>(`/gravacoes/${gravacaoId}/estado`);


/**
 * Crava a pista de uma gravacao que nao resolveu sozinha (degrau "perguntado").
 * O servidor recorta e redecompoe em background; acompanhar pelo estado.
 */
export const cravarPista = (gravacaoId: string, layoutId: string) =>
  enviar<{ gravacao_id: string; layout_id: string; pipeline: string }>(
    `/gravacoes/${gravacaoId}/pista`,
    { layout_id: layoutId },
  );
