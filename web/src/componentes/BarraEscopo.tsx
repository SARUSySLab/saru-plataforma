import type { Relatorio } from "../types/contract";
import { useSelecao } from "../state/selection";

// Escopo ativo na navbar. Duas regras de leitura:
//
// 1. Cor de destaque = o usuario muda. Cinza = vem do arquivo. Evento e
//    bateria nao tem afordancia nenhuma, senao o piloto fica tentando clicar
//    no nome do evento.
// 2. Volta e comparacao valem para o dashboard INTEIRO. Nenhum bloco tem
//    seletor de volta proprio: era assim que o traco no tempo acabava medindo
//    contra uma serie e o resto da tela contra outra.
export function BarraEscopo({ relatorio }: { relatorio: Relatorio }) {
  const { volta, compara, trecho, setVolta, setCompara, setTrecho } = useSelecao();
  const voltas = relatorio.n1.voltas;
  const emEscopo = volta ?? voltas.filter((v) => v.valida).at(-1)?.n ?? voltas[0].n;
  // A store nao conhece dado de servidor, entao o default da referencia e
  // resolvido aqui: a melhor propria, que e contra o que o relatorio ja veio
  // calculado. Sem isto o seletor mostrava uma referencia e o insight, outra.
  const refAtiva = compara ?? relatorio.n0.melhor_volta.melhor_volta_n;
  const bateria = voltas.find((v) => v.n === emEscopo)?.bateria ?? null;
  const sessao = relatorio.contexto.sessao;

  // o trecho pode ter vindo de qualquer um dos dois recortes, entao procura
  // nos dois em vez de assumir o modo ativo
  const rotuloDoTrecho = (id: string) => {
    for (const fonte of [relatorio.n2.por_curva, relatorio.n2.por_micro_setor]) {
      if (!fonte.disponivel) continue;
      const achado = fonte.itens.find((p) => p.trecho_id === id);
      if (achado) return achado.rotulo;
    }
    return id;
  };

  const rotulo = (n: number) => {
    const v = voltas.find((x) => x.n === n)!;
    const marca = v.n === relatorio.n0.melhor_volta.melhor_volta_n ? " · melhor" : v.valida ? "" : ` · ${v.motivo_invalida}`;
    return `Volta ${v.n}${marca}${v.bateria ? ` · ${v.bateria.rotulo.replace("Bateria ", "B")}` : ""}`;
  };

  return (
    <div className="escopo">
      <div className="escopo-campo">
        <span className="k">Evento</span>
        <span className="v">{relatorio.layout?.nome ?? "pista não resolvida"}</span>
      </div>
      <div className="escopo-campo">
        <span className="k">Bateria</span>
        <span className="v">
          {bateria ? `${bateria.rotulo}${sessao.disponivel && sessao.horario ? ` · ${sessao.horario}` : ""}` : "nula (arquivo solto)"}
        </span>
      </div>
      <div className="escopo-campo editavel">
        <span className="k">Volta</span>
        <select value={emEscopo} onChange={(e) => setVolta(Number(e.target.value))} aria-label="Volta em escopo">
          {voltas.map((v) => (
            <option key={v.n} value={v.n}>{rotulo(v.n)}</option>
          ))}
        </select>
      </div>
      <div className="escopo-campo editavel">
        <span className="k">Compara</span>
        <select
          value={String(refAtiva)}
          onChange={(e) => setCompara(e.target.value === "media" ? "media" : Number(e.target.value))}
          aria-label="Volta de referência"
        >
          <option value="media">Média das válidas</option>
          {voltas.map((v) => (
            <option key={v.n} value={v.n}>{rotulo(v.n)}</option>
          ))}
        </select>
      </div>
      <div className="escopo-campo editavel">
        <span className="k">Trecho</span>
        <span className="v">
          {trecho ? rotuloDoTrecho(trecho) : "a volta inteira"}
          {trecho && (
            <button type="button" className="limpar" onClick={() => setTrecho(null)} title="Voltar ao escopo da volta inteira">
              limpar
            </button>
          )}
        </span>
      </div>
    </div>
  );
}
