import type { Canal, SerieAmostras } from "../types/contract";
import "../estilo/pneus.css";

// Bloco 16. Temperatura de pneu, 4 cantos. O backend ja resolve qual sensor
// alimenta cada canto (mid > inner > outer, ver APRESENTACAO em
// relatorio.py) e emite todos os 3 sob o MESMO id de front, "temp_pneu_fl"
// etc: este componente nao sabe nem precisa saber qual variante venceu, so
// le o canto pronto.
//
// A maioria das gravacoes do acervo NAO tem esse canal (so 36 das ~90 tem
// algum canto de pneu mapeado). Por isso o caso comum aqui e AUSENCIA, e ela
// e cidada de primeira classe: os 4 cantos sempre aparecem no grid, mesmo
// quando nenhum tem dado, cada um com o motivo, nunca como "0°C" nem como
// espaco em branco (regra do B2: degradacao silenciosa nao entra).

type Canto = "fl" | "fr" | "rl" | "rr";
const CANTOS: { canto: Canto; rotulo: string }[] = [
  { canto: "fl", rotulo: "dianteira esquerda" },
  { canto: "fr", rotulo: "dianteira direita" },
  { canto: "rl", rotulo: "traseira esquerda" },
  { canto: "rr", rotulo: "traseira direita" },
];

/** Media dos pontos finitos da serie. `null` quando nao ha nenhum ponto valido. */
function mediaFinita(vs: number[] | undefined): number | null {
  if (!vs || vs.length === 0) return null;
  const validos = vs.filter((v) => v != null && Number.isFinite(v));
  if (validos.length === 0) return null;
  return validos.reduce((a, b) => a + b, 0) / validos.length;
}

function fmt(v: number): string {
  return v.toFixed(1).replace(".", ",");
}

export function TemperaturaDosPneus({ canais, serie }: {
  /** relatorio.n3.canais: diz se o canto EXISTE nesta gravacao (o id
      "temp_pneu_<canto>" so aparece aqui quando algum dos 3 sensores foi
      mapeado) e com que rotulo bruto e unidade. */
  canais: Canal[];
  /** Amostra da volta em foco (normalmente "media" das voltas validas).
      `null` enquanto ainda nao carregou ou nao ha volta selecionada: nesse
      caso o canto fica "carregando", nao "sem canal" (motivo errado e pior
      que nenhum motivo). */
  serie: SerieAmostras | null;
}) {
  const idPorCanto = (c: Canto) => `temp_pneu_${c}`;
  const canalDoCanto = (c: Canto) => canais.find((x) => x.id === idPorCanto(c));

  const medias: Record<Canto, number | null> = {
    fl: mediaFinita(serie?.canais[idPorCanto("fl")]),
    fr: mediaFinita(serie?.canais[idPorCanto("fr")]),
    rl: mediaFinita(serie?.canais[idPorCanto("rl")]),
    rr: mediaFinita(serie?.canais[idPorCanto("rr")]),
  };
  const presentes = (Object.entries(medias) as [Canto, number | null][])
    .filter(([, v]) => v != null)
    .map(([, v]) => v as number);

  // regua compartilhada: min/max do que a PROPRIA gravacao mediu nos cantos
  // presentes. Nao existe janela ideal de temperatura documentada no acervo
  // (ver relatorio.py), entao a regua compara os cantos entre si, nunca
  // contra um alvo inventado.
  const reguaMin = presentes.length ? Math.min(...presentes) : 0;
  const reguaMax = presentes.length ? Math.max(...presentes) : 0;
  const span = reguaMax - reguaMin;

  const unidade = canais.find((c) => c.id.startsWith("temp_pneu_"))?.unidade ?? "°C";

  const nenhumCanal = CANTOS.every(({ canto }) => !canalDoCanto(canto));

  const posNaRegua = (v: number) => {
    if (span <= 0) return 50; // 1 unico valor ou todos iguais: bolinha no meio
    return ((v - reguaMin) / span) * 100;
  };

  // deltas so saem quando os 4 cantos tem numero: comparar lado com metade
  // faltando seria inventar simetria que ninguem mediu.
  const completos = presentes.length === 4;
  const deltaEsqDir = completos
    ? (medias.fl! + medias.rl!) / 2 - (medias.fr! + medias.rr!) / 2
    : null;
  const deltaDiantTras = completos
    ? (medias.fl! + medias.fr!) / 2 - (medias.rl! + medias.rr!) / 2
    : null;
  const maxAbsDelta = Math.max(
    Math.abs(deltaEsqDir ?? 0),
    Math.abs(deltaDiantTras ?? 0),
    0.1, // piso pra barra nao sumir quando o delta e ~0
  );

  function celulaCanto(canto: Canto, rotulo: string) {
    const canal = canalDoCanto(canto);
    const media = medias[canto];

    if (!canal) {
      return (
        <div className={`canto canto-falta canto-${canto}`} key={canto}>
          <p className="canto-rotulo">{rotulo}</p>
          <p className="nota" style={{ margin: 0 }}>sem canal de temperatura neste arquivo</p>
        </div>
      );
    }
    if (media == null) {
      return (
        <div className={`canto canto-falta canto-${canto}`} key={canto}>
          <p className="canto-rotulo">{rotulo}</p>
          <p className="nota" style={{ margin: 0 }}>
            {serie ? "canal existe, mas sem amostra nesta volta" : "carregando…"}
          </p>
        </div>
      );
    }
    return (
      <div className={`canto canto-${canto}`} key={canto}>
        <p className="canto-rotulo">{rotulo}</p>
        <p className="canto-numero">{fmt(media)}<span className="un">{unidade}</span></p>
        <div className="regua">
          <div className="regua-ponto" style={{ left: `${posNaRegua(media)}%` }} />
        </div>
        <div className="regua-rotulos">
          <span>{fmt(reguaMin)}</span>
          <span>{fmt(reguaMax)}</span>
        </div>
      </div>
    );
  }

  function linhaDelta(rotulo: string, valor: number | null, positivoRotula: string, negativoRotula: string) {
    const pct = valor == null ? 0 : (Math.abs(valor) / maxAbsDelta) * 50;
    const lado = valor != null && valor >= 0 ? positivoRotula : negativoRotula;
    return (
      <div className="delta-linha">
        <span className="k">{rotulo}</span>
        <div className="delta-barra">
          {valor != null && (
            <div
              className="preenchido"
              style={{
                width: `${pct}%`,
                left: valor >= 0 ? "50%" : `${50 - pct}%`,
              }}
            />
          )}
        </div>
        <span className="v">
          {valor == null ? "-" : `${valor >= 0 ? "+" : ""}${fmt(valor)} ${unidade}`}
        </span>
        {valor != null && (
          <span className="pill pill-brand" style={{ marginLeft: 0 }}>{lado} mais quente</span>
        )}
      </div>
    );
  }

  return (
    <article className="cartao">
      <header>
        <h4>Temperatura dos pneus</h4>
        <span className="no">bloco 16</span>
        <span className="dir">
          <span className="pill pill-brand">mid &gt; inner &gt; outer</span>
        </span>
      </header>

      {nenhumCanal && (
        <p className="pneus-falta-tudo">
          Esta gravação não tem canal de temperatura de pneu em nenhum dos 4 cantos
          (a maioria do acervo não tem esse sensor). Os cantos abaixo declaram a
          ausência individualmente.
        </p>
      )}

      <div className="pneus-grade">
        {CANTOS.map(({ canto, rotulo }) => celulaCanto(canto, rotulo))}
      </div>

      <div className="pneus-deltas">
        {linhaDelta("Esquerda vs direita", deltaEsqDir, "esquerda", "direita")}
        {linhaDelta("Dianteira vs traseira", deltaDiantTras, "dianteira", "traseira")}
      </div>

      <p className="nota">
        Média da volta em foco por canto. Régua ao lado de cada número é o
        mínimo e o máximo entre os 4 cantos NESTA gravação (não existe janela
        ideal de temperatura documentada no acervo, então a comparação é
        sempre entre os próprios pneus, nunca contra um alvo inventado).
        Deltas só aparecem com os 4 cantos presentes: comparar um lado com o
        outro faltando inventaria uma simetria que não foi medida.
      </p>
    </article>
  );
}
