import type { ContextoSessao, Talvez } from "../types/contract";
import { Gaveta } from "./Gaveta";

// Bloco 15. Nao e tela de leitura: e CAPTURA, e acontece no upload. O que
// falta aparece marcado em vez de preenchido por default, que e a regra do B2
// aplicada ao contexto. O que a API de tempo ja sabe vem marcado como
// automatico e ninguem digita.
export function ContextoDaBateria({ aberta, sessao, onFechar }: {
  aberta: boolean;
  sessao: Talvez<ContextoSessao>;
  onFechar: () => void;
}) {
  const s = sessao.disponivel ? sessao : null;
  const campo = (rot: string, valor: string | number | null, estado: "ok" | "auto" | "falta") => (
    <div className={`campo ${estado}`} key={rot}>
      <label>{rot}</label>
      <input defaultValue={valor == null ? "" : String(valor)} placeholder={estado === "falta" ? "o sistema perguntou" : ""} />
    </div>
  );

  return (
    <Gaveta aberta={aberta} titulo="Contexto da bateria" eyebrow="Captura · bloco 15" onFechar={onFechar}>
      {!s && (
        <div className="deg">
          <span className="ico">!</span>
          <p>
            Esta gravação chegou <b>sem bateria</b>. <code>bateria_id</code> é anulável de propósito:
            arquivo solto ingere e gera os quatro níveis sem evento nenhum. O que ninguém informar, a
            tela declara em vez de assumir.
          </p>
        </div>
      )}

      <div className="grupo">
        <h5>Pneu</h5>
        {campo("Composto", s?.pneu.disponivel ? s.pneu.composto : null, s?.pneu.disponivel ? "ok" : "falta")}
        {campo("Estado", s?.pneu.disponivel ? s.pneu.estado : null, s?.pneu.disponivel ? "ok" : "falta")}
        {campo("Voltas rodadas", s?.pneu.disponivel ? s.pneu.voltas_rodadas : null, s?.pneu.disponivel ? "ok" : "falta")}
      </div>

      <div className="grupo">
        <h5>Condição</h5>
        {campo("Temp. do ar", s?.temperatura_ar_c != null ? `${s.temperatura_ar_c} °C` : null, s?.temperatura_ar_c != null ? "auto" : "falta")}
        {campo("Temp. da pista", s?.temperatura_pista_c != null ? `${s.temperatura_pista_c} °C` : null, s?.temperatura_pista_c != null ? "auto" : "falta")}
        {campo("Vento", s?.vento_kmh != null ? `${s.vento_kmh} km/h` : null, s?.vento_kmh != null ? "auto" : "falta")}
        {campo("Horário", s?.horario ?? null, s?.horario ? "ok" : "falta")}
      </div>

      <div className="grupo">
        <h5>Observações</h5>
        <div className={`campo ${s?.notas_piloto ? "ok" : "falta"}`}>
          <label>Do piloto</label>
          <textarea defaultValue={s?.notas_piloto ?? ""} placeholder={s?.notas_piloto ? "" : "o sistema perguntou"} />
        </div>
        <div className={`campo ${s?.notas_engenheiro ? "ok" : "falta"}`}>
          <label>Do engenheiro</label>
          <textarea defaultValue={s?.notas_engenheiro ?? ""} placeholder={s?.notas_engenheiro ? "" : "o sistema perguntou"} />
        </div>
      </div>

      <p className="nota">
        Campo marcado <b>auto</b> vem da API de tempo (bloco 17) sem ninguém digitar. Campo marcado{" "}
        <b>falta</b> é o que a ingestão pergunta antes de qualificar qualquer ganho: o contexto que não
        está no log é o que decide se o insight vale. Este protótipo não persiste o que for digitado.
      </p>
    </Gaveta>
  );
}
