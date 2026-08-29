import { useState } from "react";
import type { SaidaPressaoFria } from "../types/contract";

// Bloco 16, fora do funil: nao le telemetria. O engenheiro relativizou a
// propria precisao ("me disseram que na Porsche nao e assim"), entao o valor
// esta em DAR UM NORTE, e o modelo e a margem sao obrigatorios na saida, nao
// rodape. E a mesma regra que a nota do piloto violou, aplicada certo desta vez.
//
// psi e a unidade do box: e nela que o manometro e lido e a pressao ajustada.
// A conversao para bar fica ao lado porque a ficha do fabricante vem em bar.
const ATM_PSI = 14.696;
const PSI_BAR = 0.0689476;

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

export function PressaoAFrio() {
  const [ar, setAr] = useState(29);
  const [pista, setPista] = useState(47);
  const [quente, setQuente] = useState(27);
  const [carcaca, setCarcaca] = useState<string>("");

  const r = calcular(ar, pista, quente, carcaca.trim() === "" ? null : Number(carcaca));

  return (
    <article className="cartao">
      <header>
        <h4>Pressão a frio</h4>
        <span className="no">bloco 16</span>
        <span className="dir"><span className="pill pill-warn">estimativa</span></span>
      </header>

      <div className="campo"><label>Temperatura do ar</label>
        <input type="number" step="0.5" value={ar} onChange={(e) => setAr(Number(e.target.value))} /></div>
      <div className="campo"><label>Temperatura da pista</label>
        <input type="number" step="0.5" value={pista} onChange={(e) => setPista(Number(e.target.value))} /></div>
      <div className="campo"><label>Pressão-alvo a quente</label>
        <input type="number" step="0.5" value={quente} onChange={(e) => setQuente(Number(e.target.value))} /></div>
      <div className="campo"><label>Carcaça medida</label>
        <input type="number" step="1" value={carcaca} placeholder="vazio = estimar" onChange={(e) => setCarcaca(e.target.value)} /></div>

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
        ) : (
          <><b>Não deu para calcular.</b> A pressão a quente precisa ser maior que zero, em psi, e a
          carcaça precisa ficar acima da temperatura do ar.</>
        )}
      </div>
    </article>
  );
}
