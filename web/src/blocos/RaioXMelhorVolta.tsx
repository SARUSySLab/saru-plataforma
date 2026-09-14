import type { MelhorVolta, VoltaResumo } from "../types/contract";
import { tempo } from "../dados/formato";

// O raio-x da melhor volta (pedido de 29/08: a pagina dela deixou de ser um
// apanhado generico e passou a detalhar AQUELA volta). Duas leituras:
//
//   1. Setor a setor contra o teto da sessao: onde a melhor volta ja e o
//      melhor setor de todas as voltas validas (ponto forte) e onde outra
//      volta foi mais rapida (ponto fraco, com quanto ficou na mesa e em
//      qual volta o teto esta).
//   2. Os numeros proprios da volta: pico de velocidade, acelerador pleno,
//      combustivel e idade do pneu, cada um com a posicao dela na sessao.
//
// Tudo sai de `setores_s` e dos campos por volta que o relatorio ja emite:
// nenhum numero novo e inventado aqui, e a soma dos "na mesa" e por
// construcao a mesma margem para a ideal do bloco 1 (mesma fonte, mesmo
// recorte de voltas validas).
export function RaioXMelhorVolta({ dados, voltas }: {
  dados: MelhorVolta;
  voltas: VoltaResumo[];
}) {
  const mv = voltas.find((v) => v.n === dados.melhor_volta_n) ?? null;
  const validas = voltas.filter((v) => v.valida);

  if (!mv) return null;

  const nSetores = mv.setores_s.length;
  const temSetores = nSetores > 0 && mv.setores_s.some((s) => s != null);

  // teto de cada setor entre as VALIDAS (mesmo recorte da volta ideal do
  // bloco 1, senao os dois blocos discordariam na mesma tela)
  const setores = temSetores
    ? mv.setores_s.map((meu, i) => {
        if (meu == null) return null;
        let melhor = meu;
        let dona = mv.n;
        for (const v of validas) {
          const s = v.setores_s[i];
          if (s != null && s < melhor) {
            melhor = s;
            dona = v.n;
          }
        }
        return { i, meu, melhor, dona, mesa: meu - melhor };
      })
    : [];

  const fortes = setores.filter((s) => s != null && s.mesa <= 0.0005);
  const fracos = setores
    .filter((s): s is NonNullable<typeof s> => s != null && s.mesa > 0.0005)
    .sort((a, b) => b.mesa - a.mesa);

  // segunda melhor valida: diz o quao isolada a melhor esta
  const ordenadas = [...validas].sort((a, b) => a.tempo_s - b.tempo_s);
  const vice = ordenadas.find((v) => v.n !== mv.n) ?? null;

  const posicao = (extrair: (v: VoltaResumo) => number | null, maiorMelhor: boolean) => {
    const meu = extrair(mv);
    if (meu == null) return null;
    const universo = validas
      .map(extrair)
      .filter((x): x is number => x != null)
      .sort((a, b) => (maiorMelhor ? b - a : a - b));
    return { meu, rank: universo.findIndex((x) => x === meu) + 1, de: universo.length };
  };

  const pVmax = posicao((v) => v.v_max_kmh, true);
  const pPleno = posicao((v) => v.acelerador_pleno_pct, true);
  const pLitros = posicao((v) => v.litros, false);

  const linhas: { k: string; v: string }[] = [];
  if (vice) linhas.push({ k: `Vantagem sobre a 2ª melhor (volta ${vice.n})`, v: `${(vice.tempo_s - mv.tempo_s).toFixed(3)} s` });
  if (pVmax) linhas.push({ k: "Pico de velocidade", v: `${pVmax.meu.toFixed(1)} km/h · ${pVmax.rank}º de ${pVmax.de}` });
  if (pPleno) linhas.push({ k: "Acelerador pleno", v: `${pPleno.meu.toFixed(0)}% da volta · ${pPleno.rank}º de ${pPleno.de}` });
  if (pLitros) linhas.push({ k: "Combustível na volta", v: `${pLitros.meu.toFixed(2)} L · ${pLitros.rank}º menor de ${pLitros.de}` });
  if (mv.voltas_pneu != null) linhas.push({ k: "Idade do pneu nesta volta", v: `${mv.voltas_pneu} voltas de uso` });

  return (
    <article className="cartao">
      <header>
        <h4>Raio-X da volta {mv.n}</h4>
        <span className="no">melhor volta</span>
      </header>

      {temSetores ? (
        <>
          <p className="eyebrow" style={{ margin: "0 0 var(--s2)" }}>
            Setor a setor · contra o melhor setor das {validas.length} válidas
          </p>
          {setores.map((s) =>
            s == null ? null : (
              <div className="perda" key={s.i}>
                <div className="perda-topo">
                  <span className="nm">
                    Setor {s.i + 1}{" "}
                    <span className="mono" style={{ color: "var(--faint)", fontSize: 10 }}>
                      {tempo(s.meu)}
                    </span>
                  </span>
                  {s.mesa <= 0.0005 ? (
                    <span className="dt" style={{ color: "var(--d-gain)" }}>ponto forte · é o teto da sessão</span>
                  ) : (
                    <span className="dt" style={{ color: "var(--d-loss)" }}>
                      +{s.mesa.toFixed(3)} s na mesa · teto na volta {s.dona}
                    </span>
                  )}
                </div>
              </div>
            ),
          )}

          <div className="rodape">
            <span>
              {fortes.length} de {setores.filter((s) => s != null).length} setores no teto
              {fracos[0] ? <> · maior sobra no setor {fracos[0].i + 1}</> : null}
            </span>
            {dados.margem_para_ideal_s != null && !dados.ideal_suprimida && (
              <b style={{ color: "var(--d-loss)" }}>-{dados.margem_para_ideal_s.toFixed(3)} s até a ideal</b>
            )}
          </div>
        </>
      ) : (
        <p className="nota">
          Sem tempos de setor neste arquivo: o raio-x por setor precisa deles. Os números da volta
          seguem abaixo.
        </p>
      )}

      {linhas.length > 0 && (
        <div style={{ marginTop: "var(--s4)" }}>
          <p className="eyebrow" style={{ margin: "0 0 var(--s2)" }}>Os números desta volta na sessão</p>
          {linhas.map((l) => (
            <div className="kv" key={l.k}>
              <span className="k">{l.k}</span>
              <span className="v">{l.v}</span>
            </div>
          ))}
        </div>
      )}

      <p className="nota">
        Ponto forte é setor em que esta volta já é o teto da sessão; ponto fraco diz quanto outra
        volta deixou provado que dava. A soma das sobras é a margem para a volta ideal do card ao lado.
      </p>
    </article>
  );
}
