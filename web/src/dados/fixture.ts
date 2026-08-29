// Fonte de dado do front nesta fase da PoC.
//
// O JSON e emitido por `scripts/gerar-fixture.mjs`. Quando a API existir,
// este arquivo troca o import por um fetch e nada mais muda, porque o resto
// do app so conhece o tipo, nunca a origem.
//
// LIMITE CONHECIDO, nao varrido pra baixo do tapete: o cast abaixo NAO valida
// nada em runtime, e `satisfies` tambem nao resolveria, porque o TS infere
// `string` para um literal de union vindo de JSON (`resolucao_pista: "alias"`
// vira `string` e o satisfies falha por motivo errado). Validacao de verdade
// pede um schema em runtime (zod ou similar), que e dependencia nova e
// portanto decisao do Lucas. Ate la, o contrato e acordo, nao garantia.
import bruto from "../fixtures/relatorio.json";
import type { Relatorio, SerieAmostras } from "../types/contract";

export const relatorio = bruto as unknown as Relatorio;

// As series de amostra vem sob demanda, uma por volta, como virao do endpoint
// de amostra: o relatorio e leve e cabe numa resposta, a amostra e pesada.
const modulos = import.meta.glob<{ default: SerieAmostras }>("../fixtures/amostras/*.json");

export async function carregarAmostras(ref: number | "media"): Promise<SerieAmostras | null> {
  const carregar = modulos[`../fixtures/amostras/volta-${ref}.json`];
  if (!carregar) return null;
  return (await carregar()).default;
}
