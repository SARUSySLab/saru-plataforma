import type { Relatorio, SerieAmostras } from "../types/contract";
import { useContexto } from "../dados/useContexto";
import { useSetup } from "../dados/useSetup";

// Card de PNEU do N0 (protótipo dashboard-funil, coluna direita): um dos
// cinco dados que o cliente nomeou e, junto com combustível, o único que não
// é recorte da volta. Fica embaixo do consumo, no mesmo fôlego do veredito.
//
// A régua do número grande, na ordem de confiança:
//   1. MEDIDO: média dos cantos de temperatura de pneu da telemetria da volta
//      em foco (os mesmos canais do bloco 16).
//   2. INFORMADO: `carcaca_c` da ficha de setup da bateria (pirômetro do box).
//   3. Sem os dois, o card declara a ausência: número inventado aqui viraria
//      insight de pneu inventado (é a família do bug B2).
export function PneuResumo({ bateriaId, canais, serie, aoAbrirContexto }: {
  bateriaId: string | null;
  canais: Relatorio["n3"]["canais"];
  serie: SerieAmostras | null;
  aoAbrirContexto: () => void;
}) {
  const contexto = useContexto("baterias", bateriaId);
  const setup = useSetup("baterias", bateriaId);

  // histórico é append-only: o registro mais novo é o retrato atual do pneu
  const registro = (contexto.dado ?? [])
    .slice()
    .sort((a, b) => (a.criado_em < b.criado_em ? 1 : -1))[0] ?? null;
  const versao = (setup.dado ?? [])
    .slice()
    .sort((a, b) => b.versao - a.versao)[0] ?? null;

  const cantos = ["fl", "fr", "rl", "rr"].map((c) => `temp_pneu_${c}`);
  const medias = cantos
    .map((id) => {
      const v = (serie?.canais[id] ?? []).filter((x) => x != null && Number.isFinite(x));
      return v.length ? v.reduce((s, x) => s + x, 0) / v.length : null;
    })
    .filter((x): x is number => x != null);
  const temCanalDePneu = canais.some((c) => c.id.startsWith("temp_pneu_"));

  const carcacaInformada = versao ? Number(versao.valores["carcaca_c"]) : NaN;
  const pressaoAlvo = versao ? versao.valores["pressao_alvo_quente_psi"] : undefined;

  let grande: string | null = null;
  let selo: "medido" | "informado" | null = null;
  if (temCanalDePneu && medias.length > 0) {
    grande = (medias.reduce((s, x) => s + x, 0) / medias.length).toFixed(1);
    selo = "medido";
  } else if (Number.isFinite(carcacaInformada)) {
    grande = carcacaInformada.toFixed(1);
    selo = "informado";
  }

  const linhas: { rot: string; v: string }[] = [];
  if (registro?.pneu_estado) linhas.push({ rot: "Estado", v: registro.pneu_estado });
  if (registro?.pneu_composto) linhas.push({ rot: "Composto", v: registro.pneu_composto });
  if (registro?.pneu_voltas_rodadas != null)
    linhas.push({ rot: "Voltas rodadas", v: String(registro.pneu_voltas_rodadas) });
  if (pressaoAlvo != null && pressaoAlvo !== "")
    linhas.push({ rot: "Pressão-alvo a quente", v: `${pressaoAlvo} psi` });

  return (
    <button type="button" className="cartao chave" onClick={aoAbrirContexto}>
      <header>
        <h4>Pneu</h4>
        <span className="no">bloco 15</span>
        {/* a pill do selo saiu (pedido de 29/08): a procedencia ja esta
            declarada por extenso no heroi-sub, a tag so duplicava */}
      </header>

      {grande !== null ? (
        <>
          <p className="heroi">{grande} °C</p>
          <p className="heroi-sub">
            {selo === "medido"
              ? "média dos cantos, telemetria da volta em foco"
              : "carcaça informada na ficha de setup"}
          </p>
        </>
      ) : (
        <p className="nota">
          {bateriaId
            ? "Sem canal de temperatura de pneu e sem carcaça na ficha de setup."
            : "Gravação solta: pendure num outing para ter contexto de pneu."}
        </p>
      )}

      {linhas.length > 0 && (
        <p className="heroi-sub" style={{ marginTop: "var(--s2)" }}>
          {linhas.map((l) => `${l.rot.toLowerCase()}: ${l.v}`).join(" · ")}
        </p>
      )}

      <span className="ir"><span>ver detalhe</span><span>&rsaquo;</span></span>
    </button>
  );
}
