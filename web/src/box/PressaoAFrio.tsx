import type { SaidaPressaoFria } from "../types/contract";
import type { RegistroContexto } from "../services/operacao";
import "../estilo/gavetas.css";

// Bloco 16, fora do funil: nao le telemetria. O engenheiro relativizou a
// propria precisao ("me disseram que na Porsche nao e assim"), entao o valor
// esta em DAR UM NORTE, e o modelo e a margem sao obrigatorios na saida, nao
// rodape. E a mesma regra que a nota do piloto violou, aplicada certo desta vez.
//
// psi e a unidade do box: e nela que o manometro e lido e a pressao ajustada.
// A conversao para bar fica ao lado porque a ficha do fabricante vem em bar.
const ATM_PSI = 14.696;
const PSI_BAR = 0.0689476;

// Fase 11: o Box virou so leitura, cadastro de pneu mora na gaveta de
// contexto (bloco 15). Este card ganhou uma segunda metade: o estado/composto/
// voltas do pneu, mas so em LEITURA, puxado do contexto mais recente. Nao
// cadastra nada aqui, so mostra o que foi registrado por ultimo, com a mesma
// disciplina de "o que falta aparece declarado" que ja vale pro calculo de
// pressao acima.
//
// Fase 12: o card perde os 4 inputs que vivia editando (temp ar, temp pista,
// pressao-alvo a quente, carcaca medida). Os dois primeiros ja eram coluna de
// `contexto` e so estavam duplicados aqui; os outros dois nao tem coluna e
// viraram chave de `setup` (JSONB livre, ver `services/operacao.ts`). O
// cadastro dos quatro agora mora inteiro na gaveta de contexto
// (`gavetas/ContextoDaBateria.tsx`, bloco 15): este card so LE contexto +
// setup por prop e calcula, igual aos cards da visao geral (`blocos/`).
// Chaves de setup usadas (estaveis, documentadas la tambem):
// `pressao_alvo_quente_psi` e `carcaca_c`.

function linhaPneu(rot: string, valor: string | number | null) {
  const tem = valor != null && valor !== "";
  return (
    <div className={`kv ${tem ? "" : "falta"}`} key={rot}>
      <span className="k">{rot}</span>
      <span className="v">{tem ? valor : "sem registro"}</span>
    </div>
  );
}

/** Le uma chave numerica da ficha de setup. `valores` e livre (string|number)
 * por decisao do formato (ver `services/operacao.ts`), entao aqui converte e
 * descarta o que nao vira numero em vez de propagar NaN pro calculo. */
function numDoSetup(setup: Record<string, string | number> | null, chave: string): number | null {
  if (!setup) return null;
  const bruto = setup[chave];
  if (bruto == null) return null;
  const n = typeof bruto === "number" ? bruto : Number(bruto);
  return isFinite(n) ? n : null;
}

function calcular(ar: number, pista: number, quente: number, carcacaInformada: number | null): SaidaPressaoFria & { carcaca: number; estimada: boolean } | null {
  // a pista pesa mais que o ar porque e o contato que aquece a borracha
  const estimada = 0.35 * ar + 0.65 * pista + 18;
  const carcaca = carcacaInformada ?? estimada;
  const fria = (quente + ATM_PSI) * ((ar + 273.15) / (carcaca + 273.15)) - ATM_PSI;
  if (!isFinite(fria) || fria <= 0 || carcaca <= ar) return null;
  return {
    pressao_fria_psi: fria,
    modelo: "lei dos gases a volume constante",
    margem_psi: 1.2,
    carcaca,
    estimada: carcacaInformada == null,
  };
}

export function PressaoAFrio({ contexto, setup }: {
  contexto: RegistroContexto | null;
  setup: Record<string, string | number> | null;
}) {
  const ar = contexto?.temp_ar_c ?? null;
  const pista = contexto?.temp_pista_c ?? null;
  const quente = numDoSetup(setup, "pressao_alvo_quente_psi");
  const carcacaInformada = numDoSetup(setup, "carcaca_c");

  // entrada obrigatoria pro calculo (ar, pista, pressao-alvo a quente):
  // carcaca e opcional de proposito, sem ela o calculo estima. Sem as tres
  // acima nao ha conta possivel, e a regra do bloco e nao rodar com default
  // silencioso: declara o que falta e onde cadastrar.
  const faltando: string[] = [];
  if (ar == null) faltando.push("temperatura do ar");
  if (pista == null) faltando.push("temperatura da pista");
  if (quente == null) faltando.push("pressão-alvo a quente");

  const r = ar != null && pista != null && quente != null ? calcular(ar, pista, quente, carcacaInformada) : null;

  return (
    <article className="cartao">
      <header>
        <h4>Pressão a frio</h4>
        <span className="no">bloco 16</span>
        <span className="dir"><span className="pill pill-warn">estimativa</span></span>
      </header>

      {faltando.length > 0 && (
        <div className="deg">
          <span className="ico">!</span>
          <p>
            Falta {faltando.join(", ")} para calcular. Cadastro fica na gaveta de contexto (bloco 15):
            temperatura do ar e da pista no formulário de contexto, pressão-alvo a quente na ficha de
            setup dentro da mesma gaveta.
          </p>
        </div>
      )}

      <div className="saida">
        <div>
          <span className="numero">{r ? r.pressao_fria_psi.toFixed(1) : "·"}</span>{" "}
          <span className="un">psi a frio</span>
          <div className="un">{r ? `${(r.pressao_fria_psi * PSI_BAR).toFixed(2).replace(".", ",")} bar` : "·"}</div>
        </div>
        <div style={{ marginLeft: "auto", textAlign: "right" }}>
          <span className="eyebrow">Margem</span>
          <div className="mono" style={{ fontSize: 13 }}>{r ? `±${r.margem_psi.toFixed(1).replace(".", ",")} psi` : "·"}</div>
        </div>
      </div>

      <div className="modelo">
        {r ? (
          <>
            <b>Modelo:</b> {r.modelo},{" "}
            <code>P_frio = (P_quente + 14,696) × (T_ar / T_carcaça) - 14,696</code>, pressão manométrica
            em psi e temperaturas em kelvin.{" "}
            {r.estimada
              ? <>A carcaça foi <b>estimada</b> em <b>{r.carcaca.toFixed(0)} °C</b> por <code>0,35·T_ar + 0,65·T_pista + 18</code>, constante empírica de moto em pista seca.</>
              : <>Carcaça <b>medida</b>: {r.carcaca.toFixed(0)} °C, então a estimativa saiu da conta.</>}
            <br /><br />
            <b>Margem e limites.</b> A conta ignora o volume de ar deslocado pela deformação do pneu, o
            composto e a carga. Serve de norte, não de verdade: os desvios ficam na ordem de{" "}
            <b>1,2 psi</b>, e cada equipe tem a sua tabela.
          </>
        ) : faltando.length === 0 ? (
          <><b>Não deu para calcular.</b> A pressão a quente precisa ser maior que zero, em psi, e a
          carcaça precisa ficar acima da temperatura do ar.</>
        ) : null}
      </div>

      <div className="grupo">
        <h5>Pneu (último contexto)</h5>
        {contexto ? (
          <>
            {linhaPneu("Estado", contexto.pneu_estado)}
            {linhaPneu("Composto", contexto.pneu_composto)}
            {linhaPneu("Voltas rodadas", contexto.pneu_voltas_rodadas)}
          </>
        ) : (
          <p className="nota">
            Nenhum contexto registrado ainda para esta bateria/gravação. Cadastro fica na gaveta de
            contexto, este card só lê.
          </p>
        )}
      </div>
    </article>
  );
}
