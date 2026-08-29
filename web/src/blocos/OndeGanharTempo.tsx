import type { PerdaPorTrecho, Talvez } from "../types/contract";
import { useSelecao, type LossMode } from "../state/selection";
import { Fases } from "../componentes/Fases";
import { Insight } from "../componentes/Insight";
import { Degradado } from "../componentes/Degradado";
import { Segmentado } from "../componentes/Segmentado";
import { divergente } from "../graficos/svg";
import { sinal } from "../dados/formato";

// Bloco 9. O produto, pelo engenheiro: "achei muito legal a parte de onde
// ganhar tempo, voce poderia desenvolver mais isso e menos algumas outras
// informacoes". Absorveu o bloco 3 (pedido de 29/08): o "onde perdi tempo"
// era a mesma fonte truncada no top 3, entao o total recuperavel virou o
// rodape daqui e o card separado saiu do box.
//
// Tres modos. "Tudo" e o default e MISTURA as duas fontes: curva nomeada
// onde ha catalogo, micro-setor de 200 m no resto da pista (os micro-setores
// que caem dentro de uma curva catalogada saem, senao o mesmo metro de pista
// contaria duas vezes). Os modos puros continuam como recorte secundario.
export function OndeGanharTempo({ porCurva, porMicro, comprimento_m }: {
  porCurva: Talvez<{ itens: PerdaPorTrecho[] }>;
  porMicro: Talvez<{ itens: PerdaPorTrecho[] }>;
  comprimento_m: number;
}) {
  const { lossMode, setLossMode, trecho, setTrecho } = useSelecao();
  const fonte: Talvez<{ itens: PerdaPorTrecho[] }> =
    lossMode === "corner" ? porCurva
    : lossMode === "micro" ? porMicro
    : misturar(porCurva, porMicro);

  if (!fonte.disponivel) {
    return (
      <article className="cartao degradado">
        <Cabecalho lossMode={lossMode} setLossMode={setLossMode} porCurva={porCurva} porMicro={porMicro} />
        <Degradado estado={fonte} />
      </article>
    );
  }

  const itens = fonte.itens;
  const maior = Math.max(0.02, ...itens.map((p) => Math.abs(p.perda_s)));
  const positivos = itens.filter((p) => p.perda_s > 0.004).sort((a, b) => b.perda_s - a.perda_s);
  // Ranking por perda total, MAIS os trechos onde houve troca de fase. Esses
  // ficam baixos no ranking justamente porque o agregado se anula, que e o
  // motivo de o engenheiro pedir a fase: sem este acrescimo, a decisao certa
  // do piloto sumiria da tela.
  const ranking = [...positivos.slice(0, 5)];
  itens.forEach((p) => {
    if (p.tempo_por_fase.disponivel && p.tempo_por_fase.troca_de_fase && !ranking.includes(p)) ranking.push(p);
  });

  const alvo = itens.find((p) => p.trecho_id === trecho) ?? ranking[0] ?? null;

  return (
    <article className="cartao">
      <Cabecalho lossMode={lossMode} setLossMode={setLossMode} porCurva={porCurva} porMicro={porMicro} />

      {/* faixa posicionada por distancia real: o espaco entre curvas e reta, e
          reta sem delta atribuido nao pode ser pintada como trecho analisado */}
      <div className="faixa">
        {itens.map((p) => (
          <button
            key={p.trecho_id}
            type="button"
            title={`${p.rotulo}: ${sinal(p.perda_s)} s`}
            onClick={() => setTrecho(p.trecho_id === trecho ? null : p.trecho_id)}
            style={{
              left: `${(p.s_inicio_m / comprimento_m) * 100}%`,
              width: `${((p.s_fim_m - p.s_inicio_m) / comprimento_m) * 100}%`,
              background: divergente((p.perda_s / maior) * 1.1),
              opacity: 0.4 + Math.min(1, Math.abs(p.perda_s) / maior) * 0.6,
              boxShadow: p.trecho_id === trecho ? "inset 0 0 0 2px var(--text)" : undefined,
            }}
          />
        ))}
      </div>
      <div className="faixa-eixo"><span>0 m</span><span>{comprimento_m} m</span></div>

      <div style={{ marginTop: "var(--s4)" }}>
        {ranking.length === 0 ? (
          <p className="nota">Volta de referência: nada a ganhar contra ela mesma. Troque a volta ou a comparação no painel.</p>
        ) : (
          ranking.map((p, i) => (
            <div
              key={p.trecho_id}
              className={`perda clicavel${p.trecho_id === trecho ? " ativa" : ""}`}
              onClick={() => setTrecho(p.trecho_id === trecho ? null : p.trecho_id)}
            >
              <div className="perda-topo">
                <span className="rk">{i + 1}</span>
                <span className="nm">
                  {p.rotulo}{" "}
                  <span className="mono" style={{ color: "var(--faint)", fontSize: 10 }}>
                    {p.s_inicio_m.toFixed(0)}-{p.s_fim_m.toFixed(0)} m
                  </span>
                </span>
                <span className="dt">{sinal(p.perda_s)} s</span>
              </div>
              {p.tempo_por_fase.disponivel && <Fases fase={p.tempo_por_fase} />}
            </div>
          ))
        )}
      </div>

      {positivos.length > 0 && (
        <div className="rodape">
          <span>Recuperável nos {Math.min(3, positivos.length)} piores trechos</span>
          <b style={{ color: "var(--d-loss)" }}>
            +{positivos.slice(0, 3).reduce((a, p) => a + p.perda_s, 0).toFixed(3)} s
          </b>
        </div>
      )}

      {alvo?.pilotagem.disponivel && <ComoFoiDirigido alvo={alvo} />}
      <Insight ressalva={alvo?.ressalva ?? null} />

      <p className="nota">
        {lossMode === "corner"
          ? <>Curvas nomeadas pelo catálogo do layout. Os três números são o tempo <b>por fase</b>, não a fase vencedora.</>
          : lossMode === "micro"
            ? <>Segmentos fixos de 200 m. Não precisa de catálogo, só de distância.</>
            : <>Curvas nomeadas onde há catálogo; o resto da pista em segmentos fixos de 200 m.</>}
      </p>
    </article>
  );
}

function Cabecalho({ lossMode, setLossMode, porCurva, porMicro }: {
  lossMode: LossMode;
  setLossMode: (m: LossMode) => void;
  porCurva: Talvez<{ itens: PerdaPorTrecho[] }>;
  porMicro: Talvez<{ itens: PerdaPorTrecho[] }>;
}) {
  return (
    <header>
      <h4>Onde ganhar tempo</h4>
      <span className="no">bloco 9</span>
      <span className="dir">
        <Segmentado
          valor={lossMode}
          onEscolher={setLossMode}
          opcoes={[
            { id: "all", rotulo: "Tudo", desabilitado: !porCurva.disponivel && !porMicro.disponivel },
            { id: "corner", rotulo: "Por curva", desabilitado: !porCurva.disponivel },
            { id: "micro", rotulo: "Por micro-setor", desabilitado: !porMicro.disponivel },
          ]}
        />
      </span>
    </header>
  );
}

/**
 * O modo "tudo": curvas catalogadas + micro-setores que nao caem dentro de
 * nenhuma curva. O criterio e o CENTRO do micro-setor, porque um segmento de
 * 200 m pode so encostar na borda de uma curva e ainda ser majoritariamente
 * reta. Com uma fonte so, o "tudo" e essa fonte; sem nenhuma, degrada com o
 * motivo do micro-setor, que e o requisito mais fraco (so distancia).
 */
function misturar(
  porCurva: Talvez<{ itens: PerdaPorTrecho[] }>,
  porMicro: Talvez<{ itens: PerdaPorTrecho[] }>,
): Talvez<{ itens: PerdaPorTrecho[] }> {
  if (!porCurva.disponivel) return porMicro;
  if (!porMicro.disponivel) return porCurva;
  const curvas = porCurva.itens;
  const soltos = porMicro.itens.filter((m) => {
    const centro = (m.s_inicio_m + m.s_fim_m) / 2;
    return !curvas.some((c) => centro >= c.s_inicio_m && centro < c.s_fim_m);
  });
  return {
    disponivel: true,
    itens: [...curvas, ...soltos].sort((a, b) => a.s_inicio_m - b.s_inicio_m),
  };
}

/**
 * As quatro componentes da antiga nota do piloto, agora em UNIDADE e com a
 * referencia ao lado. O placar de 0 a 100 saiu porque estava quebrado por
 * construcao, e porque numero sintetico nao sobrevive ao leitor especialista
 * so por vir com a formula do lado.
 */
function ComoFoiDirigido({ alvo }: { alvo: PerdaPorTrecho }) {
  if (!alvo.pilotagem.disponivel) return null;
  const p = alvo.pilotagem;
  const linhas = [
    { k: "Tempo no trecho", m: p.tempo_no_trecho, casas: 3, inverso: true },
    { k: "Pico de frenagem", m: p.pico_frenagem, casas: 0, inverso: false },
    { k: "Pico do envelope de grip", m: p.pico_envelope_grip, casas: 2, inverso: false },
  ];
  return (
    <>
      <p className="eyebrow" style={{ margin: "var(--s4) 0 var(--s2)" }}>
        Como o trecho foi dirigido &middot; {alvo.rotulo}
      </p>
      <div className="tabela-wrap">
        <table className="leitura">
          <thead>
            <tr><th>Medida</th><th>Neste trecho</th><th>Referência</th><th>&Delta;</th></tr>
          </thead>
          <tbody>
            {linhas.map(({ k, m, casas, inverso }) => {
              const temDelta = m.aplicavel && m.valor != null && m.referencia != null;
              const d = temDelta ? m.valor! - m.referencia! : null;
              const pior = d != null && (inverso ? d > 0 : d < 0);
              return (
                <tr key={k}>
                  <td>
                    {k}
                    {!m.aplicavel && <span style={{ color: "var(--faint)" }}> a medida não se aplica neste trecho</span>}
                  </td>
                  <td className="mono">{m.aplicavel && m.valor != null ? `${m.valor.toFixed(casas)} ${m.unidade}` : "sem freio"}</td>
                  <td className="mono" style={{ color: "var(--muted)" }}>
                    {m.aplicavel && m.referencia != null ? `${m.referencia.toFixed(casas)} ${m.unidade}` : "sem freio"}
                  </td>
                  <td className={`mono ${d == null ? "" : pior ? "perde" : "ganho"}`}>
                    {d == null ? "-" : `${sinal(d, casas)} ${m.unidade}`}
                  </td>
                </tr>
              );
            })}
            <tr>
              <td>Repetição entre voltas</td>
              <td className="mono">
                {p.repeticao_entre_voltas_s != null ? `±${p.repeticao_entre_voltas_s.toFixed(3)} s` : "-"}
              </td>
              <td className="mono" style={{ color: "var(--muted)" }}>desvio deste trecho nas válidas</td>
              <td className="mono">-</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="nota">
        Eram as quatro componentes da nota do piloto. A nota saiu, e o placar de 0 a 100 saiu junto.
        Aqui cada linha tem unidade e a referência ao lado, e o que não se aplica ao trecho é declarado
        em vez de virar zero.
      </p>
    </>
  );
}
