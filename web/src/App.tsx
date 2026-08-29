import { useState } from "react";
import "./estilo/app.css";
import { relatorio } from "./dados/fixture";
import { useAmostras } from "./dados/useAmostras";
import { useSelecao } from "./state/selection";
import { rotuloRef } from "./dados/formato";
import { BarraEscopo } from "./componentes/BarraEscopo";
import { Rail } from "./componentes/Rail";
import { PAGINAS } from "./componentes/paginas";
import { Quadros } from "./componentes/Quadros";
import { MelhorVolta } from "./blocos/MelhorVolta";
import { OndePerdiTempo } from "./blocos/OndePerdiTempo";
import { OndeGanharTempo } from "./blocos/OndeGanharTempo";
import { ResumoDasVoltas } from "./blocos/ResumoDasVoltas";
import { EvolucaoPorVolta } from "./blocos/EvolucaoPorVolta";
import { DeltaEntreVoltas } from "./blocos/DeltaEntreVoltas";
import { TabelaEstatistica } from "./blocos/TabelaEstatistica";
import { Consumo } from "./blocos/Consumo";
import { MapaDaPista } from "./blocos/MapaDaPista";
import { TracoNoTempo } from "./blocos/TracoNoTempo";
import { ContextoDaBateria } from "./gavetas/ContextoDaBateria";
import { FichaDeSetup } from "./gavetas/FichaDeSetup";
import { PressaoAFrio } from "./box/PressaoAFrio";
import { TempoComPrevisao } from "./box/TempoComPrevisao";

// Casca do funil. O que ela faz e so isto: sustenta o escopo global, decide
// qual pagina esta aberta e passa DADO POR PROP para os blocos.
//
// O que ela deliberadamente NAO faz e o motivo de existir. O SaDashboard.tsx
// do saru-app tinha 685 linhas, ~20 useState e 8 useEffect num componente so
// (sessao, aba, volta, voltas extras, referencia, dados da referencia, pista,
// benchmark, acervo, loading e erro de cada um), e toda troca de selecao
// re-renderizava tudo. Aqui a selecao mora na store e o dado vem de fora:
// nenhum bloco puxa do store por dentro, senao ele nao da pra testar isolado.

/**
 * O que o usuario precisa responder antes de o sistema qualificar o ganho
 * (decisao 6). Vem primeiro na tela porque e a condicao de validade de tudo
 * que esta abaixo dela, nao um aviso de rodape.
 */
function faltasDeContexto(): string[] {
  const s = relatorio.contexto.sessao;
  if (!s.disponivel) return ["bateria", "estado do pneu", "temperaturas", "hora da sessão"];
  const faltas: string[] = [];
  if (s.vento_kmh == null) faltas.push("vento");
  if (!s.notas_piloto) faltas.push("observações do piloto");
  return faltas;
}

function PerguntaDaIngestao({ faltas, onAbrir }: { faltas: string[]; onAbrir: () => void }) {
  if (faltas.length === 0) return null;
  return (
    <div className="pergunta">
      <span className="qi">?</span>
      <p>
        Antes de eu qualificar o ganho, falta <b>{faltas.join(", ")}</b>. Mudou temperatura ou vento
        desde o envio anterior?
      </p>
      <button type="button" className="ghost" onClick={onAbrir}>Preencher contexto</button>
    </div>
  );
}

function CabecaDaPagina({ titulo, pergunta, onVoltar }: { titulo: string; pergunta: string; onVoltar: () => void }) {
  return (
    <div className="cabeca-pagina">
      <button type="button" className="ghost" onClick={onVoltar}>&lsaquo; Visão geral</button>
      <h3>{titulo}</h3>
      <span className="pergunta-pagina">{pergunta}</span>
    </div>
  );
}

export default function App() {
  const { volta, compara, vista, irPara, contextoAberto, setContextoAberto, setupAberto, setSetupAberto } = useSelecao();
  const [railAberto, setRailAberto] = useState(true);

  const voltas = relatorio.n1.voltas;
  const melhorN = relatorio.n0.melhor_volta.melhor_volta_n;
  const emEscopo = volta ?? voltas.filter((v) => v.valida).at(-1)?.n ?? voltas[0].n;
  // A store nao conhece dado de servidor, entao o default da referencia e
  // resolvido aqui: a melhor propria, que e contra o que o relatorio veio.
  const refAtiva = compara ?? melhorN;
  const ehRef = refAtiva !== "media" && refAtiva === emEscopo;
  // quando volta e referencia coincidem nao ha o que sobrepor: cai para a media
  const refDoTraco = ehRef ? ("media" as const) : refAtiva;

  const par = useAmostras(emEscopo, refDoTraco);
  const bateriaEscopo = voltas.find((v) => v.n === emEscopo)?.bateria?.rotulo ?? null;
  // a bateria do card de melhor volta e a DA MELHOR VOLTA, nao a do escopo:
  // mostrar a bateria da volta 13 ao lado da frase que fala da volta 7 seria
  // mentira de contexto, justo no card que existe pra dizer a verdade
  const bateriaDaMelhor = voltas.find((v) => v.n === melhorN)?.bateria?.rotulo ?? null;
  const faltas = faltasDeContexto();
  const comprimento = relatorio.layout?.comprimento_m ?? 0;

  const pagina = vista.tipo === "pagina" ? PAGINAS.find((p) => p.id === vista.id) : null;
  const voltarParaGeral = () => irPara({ tipo: "geral" });

  const bloco9 = (
    <OndeGanharTempo porCurva={relatorio.n2.por_curva} porMicro={relatorio.n2.por_micro_setor} comprimento_m={comprimento} />
  );
  const bloco4 = <ResumoDasVoltas voltas={voltas} melhorN={melhorN} refAtiva={refAtiva} emEscopo={emEscopo} />;
  const bloco5 = <EvolucaoPorVolta voltas={voltas} melhorN={melhorN} emEscopo={emEscopo} />;
  const bloco14 = <Consumo consumo={relatorio.n1.consumo} voltas={voltas} emEscopo={emEscopo} bateriaRotulo={bateriaEscopo} />;
  const bloco6 = par && (
    <DeltaEntreVoltas a={par.a} b={par.b} rotuloPar={`V${emEscopo} vs ${rotuloRef(refDoTraco)}`} ehRef={ehRef} />
  );
  const bloco7 = par && <TabelaEstatistica a={par.a} b={par.b} ehRef={ehRef} />;
  const bloco8 = (larga?: boolean) =>
    par && <MapaDaPista tracado={relatorio.tracado} trechos={relatorio.trechos} a={par.a} b={par.b} larga={larga} />;
  const bloco10 = par && (
    <TracoNoTempo a={par.a} b={par.b} rotuloA={`Volta ${emEscopo}`} rotuloB={rotuloRef(refDoTraco)} trechos={relatorio.trechos} />
  );

  return (
    <div className={`app${railAberto ? "" : " recolhido"}`}>
      <Rail contextoIncompleto={faltas.length > 0} onRecolher={() => setRailAberto(false)} />

      <main className="principal">
        <div className="navbar">
          {!railAberto && (
            <button type="button" className="ghost" onClick={() => setRailAberto(true)} title="Abrir painel">
              &rsaquo;&rsaquo; painel
            </button>
          )}
          <div>
            <h2>{relatorio.layout?.nome ?? "Pista não resolvida"}</h2>
            <p className="meta">
              {relatorio.piloto} · {voltas.length} voltas
              {relatorio.layout ? ` · ${(relatorio.layout.comprimento_m / 1000).toFixed(3)} km` : ""}
            </p>
          </div>
          <div className="espaco" />
          <span className={`pill ${relatorio.resolucao_pista === "nao_resolvida" ? "pill-warn" : "pill-ok"}`}>
            pista por {relatorio.resolucao_pista}
          </span>
          <BarraEscopo relatorio={relatorio} />
        </div>

        {vista.tipo === "geral" && (
          <>
            <PerguntaDaIngestao faltas={faltas} onAbrir={() => setContextoAberto(true)} />

            {/* N0: veredito. Dois numeros e tres frases, sem nenhum controle.
                E a tela que o piloto olha por 5 segundos no box. */}
            <div className="n0">
              <div className="coluna">
                <MelhorVolta
                  dados={relatorio.n0.melhor_volta}
                  bateria={bateriaDaMelhor}
                  onAbrir={() => irPara({ tipo: "pagina", id: "melhor_volta" })}
                />
                {bloco6}
              </div>

              <OndePerdiTempo perdas={relatorio.n0.perdas_top3} onAbrir={() => irPara({ tipo: "pagina", id: "perdas" })} />

              <div className="coluna">{bloco14}</div>
            </div>

            <Quadros relatorio={relatorio} emEscopo={emEscopo} melhorN={melhorN} />

            <div className="pilha">{bloco10}{bloco7}</div>
          </>
        )}

        {pagina && (
          <>
            <CabecaDaPagina titulo={pagina.titulo} pergunta={pagina.pergunta} onVoltar={voltarParaGeral} />
            <div className="pilha">
              {vista.tipo === "pagina" && vista.id === "perdas" && <>{bloco9}{bloco10}</>}
              {vista.tipo === "pagina" && vista.id === "melhor_volta" && (
                <>
                  <MelhorVolta dados={relatorio.n0.melhor_volta} bateria={bateriaDaMelhor} onAbrir={voltarParaGeral} />
                  {bloco10}
                  <div className="dupla">{bloco4}{bloco7}</div>
                </>
              )}
              {vista.tipo === "pagina" && vista.id === "mapa" && <>{bloco8(true)}{bloco10}</>}
              {vista.tipo === "pagina" && vista.id === "evolucao" && <>{bloco5}{bloco6}{bloco4}</>}
              {vista.tipo === "pagina" && vista.id === "consumo" && <>{bloco14}{bloco4}</>}
              {vista.tipo === "pagina" && vista.id === "voltas" && <>{bloco6}{bloco4}</>}
              {vista.tipo === "pagina" && vista.id === "traco" && <>{bloco10}{bloco8()}{bloco7}</>}
            </div>
          </>
        )}

        {vista.tipo === "box" && (
          <>
            <CabecaDaPagina titulo="Box" pergunta="Ferramentas que não leem o log" onVoltar={voltarParaGeral} />
            <div className="box-grid">
              <PressaoAFrio />
              <TempoComPrevisao />
            </div>
          </>
        )}
      </main>

      <ContextoDaBateria
        aberta={contextoAberto}
        sessao={relatorio.contexto.sessao}
        onFechar={() => setContextoAberto(false)}
      />
      <FichaDeSetup aberta={setupAberto} setup={relatorio.contexto.setup} onFechar={() => setSetupAberto(false)} />
    </div>
  );
}
