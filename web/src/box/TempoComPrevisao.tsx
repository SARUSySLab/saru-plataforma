import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { CardFlutuante } from "../componentes/CardFlutuante";
import { useLargura } from "../graficos/useLargura";
import { caminho, escala } from "../graficos/svg";
import { useRequisicao } from "../dados/requisicao";
import { climaDoLayout, type Clima } from "../services/clima";
import { ErroDaApi } from "../services/api";

// Fase 10 (dois itens deste arquivo): atualizacao periodica e horario da
// bateria na serie. `services/clima.ts` esta fora do escopo desta sessao
// (outra sessao mexe la), entao os campos que o backend ja manda
// (`buscado_em`, `defasado`, `fuso`, ver docstring de `clima.py`) e que a
// interface `Clima` ainda nao declara sao lidos aqui por cima, sem editar o
// arquivo de servico. Quando `Clima` for atualizada la, este tipo local
// deveria sumir.
type ClimaComMetadados = Clima & {
  buscado_em?: string;
  defasado?: boolean;
  fuso?: string;
};

/** A cada quanto tempo o componente rebusca. Mesmo TTL do cache do servidor
 * (`_TTL_S` em `clima.py`): pedir mais rapido que isso so bateria a API sem
 * trazer dado mais novo, o cache do backend nao teria virado ainda. */
const INTERVALO_ATUALIZACAO_MS = 15 * 60 * 1000;

// Bloco 17, fora do funil. Alimenta metade do bloco 15 sozinho: temperatura de
// ar e vento entram no contexto da bateria sem ninguem digitar.
//
// Dado real, vindo do backend (`/clima/:layoutId`), nao da fonte de
// meteorologia direto do browser: o cache de 15 min do backend vale pra todos
// os clientes de uma vez (nao um refetch por aba aberta), e no dia em que a
// fonte exigir chave de API, essa chave fica no servidor e nunca vaza pro
// bundle do front.
//
// Temperatura de PISTA nao vem daqui. Nenhum servico de meteorologia mede
// asfalto: o que a fonte devolve e temperatura do ar. Pista fica de fora ate
// existir sensor de fato (ou telemetria) alimentando esse numero.

/**
 * Hora do rotulo do eixo, como "14h".
 *
 * O campo `horario` vem em ISO 8601 com deslocamento explicito, ja convertido
 * pro fuso DA PISTA no backend (`_no_fuso_da_pista` em `clima.py`). Passar
 * `fuso` aqui formata no fuso da pista de verdade, em vez de assumir que o
 * fuso do browser bate com o da pista (o bug antigo: o box pode estar sendo
 * lido de qualquer lugar, quem importa e a hora NA PISTA). Sem `fuso`, cai no
 * fuso do browser como fallback, nao trava a tela por causa de um campo
 * ausente.
 */
function horaDoEixo(iso: string, fuso?: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(11, 16); // ISO malformado: corta na mao
  const partes = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", hour12: false, timeZone: fuso }).formatToParts(d);
  const hora = partes.find((p) => p.type === "hour")?.value ?? "00";
  return `${hora}h`;
}

/** Dia e hora por extenso, pro card do cursor, onde cabe mais que no eixo.
 * Mesma logica de fuso de `horaDoEixo` acima. */
function horaCompleta(iso: string, fuso?: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("pt-BR", { weekday: "short", hour: "2-digit", minute: "2-digit", timeZone: fuso });
}

/** "9h42" pro carimbo de ultima atualizacao, mesma regra de fuso. */
function horaCurta(iso: string, fuso?: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", timeZone: fuso });
}

export function TempoComPrevisao({ layoutId, horarioDaBateria }: {
  layoutId: string | null;
  /** ISO 8601 em UTC, do relogio do banco (bateria). Fase 10: relaciona a
   * previsao ao horario da bateria, destacando o ponto correspondente na
   * serie. `null` quando nao ha bateria em escopo (arquivo solto, ou nenhuma
   * selecionada ainda). */
  horarioDaBateria: string | null;
}) {
  const host = useRef<HTMLDivElement>(null);
  // mesmo comportamento das series de telemetria: cursor em ref, card
  // flutuante e regua no eixo. E uma serie no tempo como as outras, e ler
  // duas series com dois gestos diferentes na mesma tela seria gratuito.
  const [cursor, setCursor] = useState<{ h: number; xPx: number } | null>(null);
  const W = useLargura(host, 620);
  const H = 162, PL = 34, PR = 12, PT = 12, PB = 30;

  // `useRequisicao` so devolve `erro` como string (a mensagem ja formatada
  // pro usuario), o status HTTP se perde no caminho. Pra distinguir 422 de
  // 502 sem tocar em `requisicao.ts`, a gente reembala o erro aqui com uma
  // mensagem propria que carrega o status disfarcado de texto, e le essa
  // mensagem depois em vez de adivinhar pelo conteudo (o backend pode mudar
  // o texto humano sem avisar, o status nao muda).
  const buscar = useCallback(
    () =>
      climaDoLayout(layoutId as string).catch((e: unknown) => {
        if (e instanceof ErroDaApi && e.status === 422) throw new ErroDaApi(422, e.detalhe, "SEM_COORDENADA");
        if (e instanceof ErroDaApi && e.status === 502) throw new ErroDaApi(502, e.detalhe, "FONTE_INDISPONIVEL");
        throw e;
      }),
    [layoutId],
  );
  const { dado, carregando, erro, recarregar } = useRequisicao(buscar, [layoutId], layoutId !== null);
  const dadoExt = dado as ClimaComMetadados | null;

  // Fase 10: "exibir dados a cada 15 minutos". Antes buscava so na montagem
  // e nunca mais, entao um box aberto a tarde inteira mostrava a previsao do
  // momento em que foi aberto. Dois disparos: o intervalo fixo (mesmo TTL do
  // cache do servidor, ver `INTERVALO_ATUALIZACAO_MS`) e o retorno de
  // visibilidade, porque e nesse instante que alguem de fato vai olhar a
  // tela de novo. Os dois so agem com a aba VISIVEL: rebuscar em aba oculta
  // gasta rede sem ninguem ler o resultado.
  useEffect(() => {
    if (layoutId === null) return;
    const intervalo = setInterval(() => {
      if (document.visibilityState === "visible") recarregar();
    }, INTERVALO_ATUALIZACAO_MS);
    const aoMudarVisibilidade = () => {
      if (document.visibilityState === "visible") recarregar();
    };
    document.addEventListener("visibilitychange", aoMudarVisibilidade);
    return () => {
      clearInterval(intervalo);
      document.removeEventListener("visibilitychange", aoMudarVisibilidade);
    };
  }, [layoutId, recarregar]);

  // pista sem coordenada de referencia no catalogo: nem tenta buscar (ver
  // `ativo` acima) nem inventa numero. 422 e o backend confirmando a mesma
  // coisa depois de tentar.
  const semCoordenada = layoutId === null || erro === "SEM_COORDENADA";
  // fonte de meteorologia fora do ar: acontece de verdade, o IP do Railway
  // toma 429 do Open-Meteo de vez em quando. Isso e transitorio, coordenada
  // ausente nao e.
  const fonteIndisponivel = erro === "FONTE_INDISPONIVEL";
  // qualquer outro erro (rede fora, 500 generico): mostra a mensagem que a
  // API mandou em vez de sumir com o bloco inteiro.
  const outroErro = erro !== null && !semCoordenada && !fonteIndisponivel;

  const horas = useMemo(() => dado?.previsao_horaria ?? [], [dado]);
  const agora = horas.length > 0 ? Math.min(horas.length - 1, new Date().getHours()) : 0;

  // Fase 10: "relacionar previsao ao horario da bateria". `horarioDaBateria`
  // vem em UTC (relogio do banco); `p.horario` ja vem no fuso da pista, mas
  // com deslocamento explicito, entao os dois viram o MESMO instante em
  // milissegundos e a comparacao e sempre por `getTime()`, nunca por texto
  // (comparar string ia falhar toda vez que os fusos escritos diferissem,
  // mesmo representando o mesmo momento). A janela de tolerancia e meia hora
  // pra cada lado: a serie e horaria, entao o ponto mais proximo pode estar
  // ate 30min do horario real da bateria sem deixar de ser "esse" ponto.
  const TOLERANCIA_JANELA_MS = 30 * 60 * 1000;
  const { indiceBateria, bateriaForaDaJanela } = useMemo(() => {
    if (!horarioDaBateria || horas.length === 0) return { indiceBateria: null as number | null, bateriaForaDaJanela: false };
    const alvoMs = new Date(horarioDaBateria).getTime();
    if (Number.isNaN(alvoMs)) return { indiceBateria: null, bateriaForaDaJanela: false };
    const primeiroMs = new Date(horas[0].horario).getTime();
    const ultimoMs = new Date(horas[horas.length - 1].horario).getTime();
    if (Number.isNaN(primeiroMs) || Number.isNaN(ultimoMs)) return { indiceBateria: null, bateriaForaDaJanela: false };
    if (alvoMs < primeiroMs - TOLERANCIA_JANELA_MS || alvoMs > ultimoMs + TOLERANCIA_JANELA_MS) {
      // fora da janela da previsao: nao inventa destaque no ponto errado,
      // so avisa (renderizado mais abaixo).
      return { indiceBateria: null, bateriaForaDaJanela: true };
    }
    let melhorI = 0;
    let melhorDiff = Infinity;
    horas.forEach((p, i) => {
      const diff = Math.abs(new Date(p.horario).getTime() - alvoMs);
      if (diff < melhorDiff) {
        melhorDiff = diff;
        melhorI = i;
      }
    });
    return { indiceBateria: melhorI, bateriaForaDaJanela: false };
  }, [horarioDaBateria, horas]);

  const vals = horas.map((p) => p.temperatura_c);
  const y = escala(vals.length ? Math.min(...vals) - 2 : 0, vals.length ? Math.max(...vals) + 2 : 1, H - PB, PT);
  const x = escala(0, Math.max(1, horas.length - 1), PL, W - PR);
  const linha = horas.length ? caminho(horas.map((p, i) => [x(i), y(p.temperatura_c)] as [number, number])) : "";
  const larguraHost = W;
  const emPx = (xv: number) => (xv / W) * larguraHost;
  // rotulo de hora a cada N marcas, para nao empilhar numero em tela estreita
  const aCada = Math.max(1, Math.ceil(34 / Math.max(1, larguraHost / Math.max(1, horas.length))));

  return (
    <article className="cartao">
      <header>
        <h4>Tempo com previsão</h4>
        <span className="no">bloco 17</span>
      </header>

      {semCoordenada && (
        <p className="muted">
          essa pista não tem coordenada de referência no catálogo, por isso não há previsão de tempo.
        </p>
      )}

      {!semCoordenada && fonteIndisponivel && (
        <div style={{ display: "flex", alignItems: "center", gap: "var(--s3)", flexWrap: "wrap" }}>
          <span className="muted">a fonte de meteorologia não respondeu.</span>
          <button type="button" onClick={recarregar}>tentar de novo</button>
        </div>
      )}

      {outroErro && (
        <div style={{ display: "flex", alignItems: "center", gap: "var(--s3)", flexWrap: "wrap" }}>
          <span className="muted">{erro}</span>
          <button type="button" onClick={recarregar}>tentar de novo</button>
        </div>
      )}

      {!semCoordenada && !fonteIndisponivel && !outroErro && carregando && <p className="muted">carregando previsão...</p>}

      {!semCoordenada && !fonteIndisponivel && !outroErro && !carregando && dado && (
        <>
          <div style={{ display: "flex", alignItems: "baseline", gap: "var(--s4)", flexWrap: "wrap" }}>
            <div><span className="numero">{dado.temperatura_atual_c.toFixed(0)}</span> <span className="un">°C ar</span></div>
            {dado.condicao_atual && <div className="muted">{dado.condicao_atual}</div>}
            {(dado.vento_kmh !== null || dadoExt?.buscado_em) && (
              <div style={{ marginLeft: "auto", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                {dado.vento_kmh !== null && (
                  <span className="mono" style={{ color: "var(--muted)", fontSize: 12 }}>vento {dado.vento_kmh.toFixed(0)} km/h</span>
                )}
                {/* Fase 10: sem isso o numero na tela nao dizia se era de
                    agora ou de tres horas atras, e um box aberto o dia
                    inteiro nunca sabia. `buscado_em` e a hora que o BACKEND
                    buscou na fonte (nao a hora local do refetch do front),
                    entao reflete o cache de verdade; `defasado` sinaliza
                    quando a fonte falhou e isso e o ultimo dado bom que
                    sobrou. */}
                {dadoExt?.buscado_em && (
                  <span className="mono" style={{ color: dadoExt.defasado ? "var(--warn)" : "var(--faint)", fontSize: 11 }}>
                    atualizado às {horaCurta(dadoExt.buscado_em, dadoExt.fuso)}
                    {dadoExt.defasado ? " (fonte fora do ar, dado antigo)" : ""}
                  </span>
                )}
              </div>
            )}
          </div>

          <div
            className="gr"
            ref={host}
            style={{ marginTop: "var(--s3)" }}
            onPointerMove={(e) => {
              const r = host.current?.getBoundingClientRect();
              if (!r?.width || horas.length === 0) return;
              const fx = ((e.clientX - r.left) / r.width) * W;
              if (fx < PL || fx > W - PR) return setCursor(null);
              const h = Math.max(0, Math.min(horas.length - 1, Math.round(((fx - PL) / (W - PL - PR)) * (horas.length - 1))));
              setCursor({ h, xPx: e.clientX - r.left });
            }}
            onPointerLeave={() => setCursor(null)}
          >
            <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
              {[PT, PT + (H - PT - PB) / 2, H - PB].map((t, i) => <line key={i} className="grade" x1={PL} y1={t} x2={W - PR} y2={t} />)}
              {horas.length > 0 && (
                <>
                  <line x1={x(agora)} y1={PT} x2={x(agora)} y2={H - PB} stroke="var(--brand)" strokeWidth={1.5} />
                  <text className="eixo" x={x(agora) + 4} y={PT + 9} style={{ fill: "var(--brand)" }}>agora</text>
                  <path d={linha} fill="none" stroke="var(--ch-str)" strokeWidth={2} strokeLinejoin="round" />
                </>
              )}
              {cursor && (
                <line x1={x(cursor.h)} y1={PT} x2={x(cursor.h)} y2={H - PB} stroke="var(--text)" strokeWidth={1} opacity={0.7} />
              )}
              {/* Fase 10: ponto correspondente ao horario da bateria, so
                  quando cai dentro da janela da previsao. Cor propria
                  (--ok) pra nao se confundir com "agora" (--brand) nem com
                  a linha da serie (--ch-str). */}
              {indiceBateria !== null && horas[indiceBateria] && (
                <g>
                  <line
                    x1={x(indiceBateria)} y1={PT} x2={x(indiceBateria)} y2={H - PB}
                    stroke="var(--ok)" strokeWidth={1.5} strokeDasharray="3 2"
                  />
                  <circle cx={x(indiceBateria)} cy={y(horas[indiceBateria].temperatura_c)} r={4} fill="var(--ok)" stroke="var(--surface)" strokeWidth={1.5} />
                  <text className="eixo" x={x(indiceBateria) + 4} y={PT + 9} textAnchor={indiceBateria === agora ? "end" : "start"} style={{ fill: "var(--ok)" }}>
                    bateria
                  </text>
                </g>
              )}
              {horas.map((p, i) => {
                const rotula = i % aCada === 0;
                return (
                  <g key={p.horario}>
                    <line x1={x(i)} y1={H - PB} x2={x(i)} y2={H - PB + (rotula ? 6 : 3)} stroke="var(--border-strong)" strokeWidth={1} opacity={rotula ? 0.9 : 0.45} />
                    {rotula && (
                      <text className="eixo" x={x(i)} y={H - 12} textAnchor="middle">
                        {horaDoEixo(p.horario, dadoExt?.fuso)}
                      </text>
                    )}
                  </g>
                );
              })}
              <text className="eixo" x={W - PR} y={H - 2} textAnchor="end" style={{ fill: "var(--faint)" }}>hora do dia</text>
            </svg>
          </div>

          {/* Aqui o card desce para uma faixa propria em vez de pairar sobre a
              curva. E so uma linha num grafico pequeno, e o card por cima
              cobria justamente o trecho que o cursor esta apontando. A faixa tem
              altura reservada, entao entrar e sair do grafico nao empurra o resto
              da tela para cima e para baixo. */}
          <div className="faixa-card">
            {cursor && horas[cursor.h] && (
              <CardFlutuante
                x={emPx(x(cursor.h))}
                y={0}
                largura={larguraHost}
                titulo={horaCompleta(horas[cursor.h].horario, dadoExt?.fuso)}
                linhas={[
                  { rot: "ar", unico: <b style={{ color: "var(--ch-str)" }}>{horas[cursor.h].temperatura_c.toFixed(1)} °C</b> },
                  ...(horas[cursor.h].condicao ? [{ rot: "condição", unico: <>{horas[cursor.h].condicao}</> }] : []),
                ]}
                rodape="alimenta o contexto da bateria sem ninguém digitar"
              />
            )}
          </div>

          <div className="legenda">
            <span><i style={{ background: "var(--ch-str)" }} />ar</span>
            {indiceBateria !== null && <span><i style={{ background: "var(--ok)" }} />bateria</span>}
            <span style={{ color: "var(--faint)" }}>hora a hora, hoje. temperatura de pista não vem de fonte de meteorologia</span>
          </div>

          {/* Fase 10: horario da bateria fora da janela da previsao (ex.: a
              bateria e daqui a 3 dias, e a previsao so cobre as proximas
              horas). Diz isso em vez de destacar um ponto que nao corresponde
              de fato ao horario pedido, que seria pior que nao mostrar nada. */}
          {bateriaForaDaJanela && (
            <p className="muted" style={{ marginTop: "var(--s2)" }}>
              o horário da bateria está fora da janela desta previsão, por isso nenhum ponto foi destacado.
            </p>
          )}
        </>
      )}
    </article>
  );
}
