import type { Bateria } from "../services/operacao";
import "../estilo/gavetas.css";

// Fase 11: card novo do Box, so LEITURA. Antes o combustivel nao tinha card
// nenhum aqui (o cadastro morava solto no Box); agora o cadastro dos litros
// (fuel_in_l/fuel_out_l) vive na gaveta de contexto (bloco 15,
// `ContextoDaBateria.tsx`), e este card so deriva o consumo a partir do que
// foi cadastrado la. Os litros persistem em `bateria`, nao em `contexto`
// (a tabela `contexto` nao tem essas colunas), entao esse card so faz
// sentido com bateria em escopo: gravacao solta nunca tem os dois numeros.
//
// Numero derivado sai com a regua do lado (mesma regra do `PressaoAFrio.tsx`,
// bloco 16): aqui a regua e so a formula, porque nao e estimativa por
// modelo fisico, e subtracao direta de duas leituras de tanque. A parte que
// pode enganar e outra: se faltar QUALQUER um dos dois litros, o consumo
// nao aparece como zero, aparece declarado como "falta".

interface Consumo {
  litros: number;
  litrosPorVolta: number | null;
}

/** `null` quando faltou fuel_in_l ou fuel_out_l: a funcao nao inventa 0 pra
 * leitura ausente, so devolve o consumo quando os dois numeros existem. */
function calcularConsumo(fuelInL: number | null, fuelOutL: number | null, voltas: number | null): Consumo | null {
  if (fuelInL == null || fuelOutL == null) return null;
  const litros = fuelInL - fuelOutL;
  const litrosPorVolta = voltas != null && voltas > 0 ? litros / voltas : null;
  return { litros, litrosPorVolta };
}

export function ConsumoDeCombustivel({ bateria }: {
  bateria: Pick<Bateria, "fuel_in_l" | "fuel_out_l" | "voltas"> | null;
}) {
  const semBateria = bateria === null;
  const faltaSaida = !semBateria && bateria.fuel_in_l == null;
  const faltaVolta = !semBateria && bateria.fuel_out_l == null;
  const consumo = semBateria ? null : calcularConsumo(bateria.fuel_in_l, bateria.fuel_out_l, bateria.voltas ?? null);

  return (
    <article className="cartao">
      <header>
        <h4>Gasolina</h4>
        <span className="dir"><span className="pill pill-warn">derivado</span></span>
      </header>

      {semBateria && (
        <div className="deg-inline">
          <span className="ico">!</span>
          <p className="nota" style={{ margin: 0 }}>
            Sem bateria em escopo, não há onde ler o combustível: os litros de saída e volta vivem em
            <code> bateria.fuel_in_l/fuel_out_l</code>, e essa gravação está solta.
          </p>
        </div>
      )}

      {!semBateria && (faltaSaida || faltaVolta) && (
        <div className="deg-inline">
          <span className="ico">!</span>
          <p className="nota" style={{ margin: 0 }}>
            Falta{faltaSaida && faltaVolta ? "m" : ""} {faltaSaida && "litros na saída"}
            {faltaSaida && faltaVolta && " e "}
            {faltaVolta && "litros na volta"}: cadastre no contexto da bateria (gaveta, bloco 15) pra
            calcular o consumo.
          </p>
        </div>
      )}

      {consumo && (
        <>
          <div className="saida">
            <div>
              <span className="numero">{consumo.litros.toFixed(1).replace(".", ",")}</span>{" "}
              <span className="un">L gastos na bateria</span>
            </div>
            <div style={{ marginLeft: "auto", textAlign: "right" }}>
              <span className="eyebrow">Por volta</span>
              <div className="mono" style={{ fontSize: 13 }}>
                {consumo.litrosPorVolta != null
                  ? `${consumo.litrosPorVolta.toFixed(2).replace(".", ",")} L/volta`
                  : "sem contagem de voltas"}
              </div>
            </div>
          </div>

          <div className="modelo">
            <b>Como saiu esse número:</b>{" "}
            <code>consumo_L = fuel_in_l - fuel_out_l</code>, litros na saída menos litros na volta.{" "}
            {consumo.litrosPorVolta != null ? (
              <>
                <code>L/volta = consumo_L / voltas</code>, dividido pelas voltas que a telemetria mediu
                nesta bateria.
              </>
            ) : (
              <>Não deu pra dividir por volta: esta bateria não tem contagem de voltas.</>
            )}
            <br /><br />
            <b>Não é estimativa.</b> É subtração direta de duas leituras de tanque cadastradas à mão no
            contexto; a precisão do resultado é a precisão de quem leu o tanque, isso aqui não modela
            nada.
          </div>
        </>
      )}
    </article>
  );
}
