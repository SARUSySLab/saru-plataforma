import type { TempoPorFase } from "../types/contract";
import { sinal } from "../dados/formato";

// Tempo POR FASE, nao a fase vencedora. Pedido literal do engenheiro: numa
// sequencia, perder a entrada pra ganhar a saida e a decisao certa, e um
// numero agregado por curva esconde isso e manda o piloto corrigir o que ele
// fez de proposito. A fase dominante nao aparece de proposito.
export function Fases({ fase }: { fase: TempoPorFase }) {
  const linhas: [string, number][] = [
    ["entrada", fase.entrada_s],
    ["meio", fase.meio_s],
    ["saída", fase.saida_s],
  ];
  return (
    <>
      <div className="fases">
        {linhas.map(([nome, v]) => (
          <span className="fase" key={nome}>
            <span className="pn">{nome}</span>
            <span className={`pv ${v > 0 ? "perde" : "ganho"}`}>{sinal(v)}</span>
          </span>
        ))}
      </div>
      {fase.troca_de_fase && (
        <p className="escolha">
          Perdeu na entrada e <b>ganhou na saida</b>: numa sequência isso costuma ser escolha, não erro.
          O agregado por curva mandaria desfazer.
        </p>
      )}
    </>
  );
}
