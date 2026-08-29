import { useEffect, useRef, useState } from "react";
import { listarAvisos, listarTurnos, marcarVisto, perguntar, type Aviso, type Turno } from "../services/sarue";
import { ErroDaApi } from "../services/api";
import { useSarue } from "./estado";
import { useTecladoVirtual } from "./useTecladoVirtual";
import { useEspacoDaPagina, useTravaDeArrasto } from "./useEspacoDaPagina";
import { useTemaEfetivo } from "../tema/useTema";
import "../estilo/sarue.css";

// Fases 9 e 12, reescrito pra virar sidebar (mesmo padrao da Lana e da Pivo:
// painel fixo a direita + FAB, nao mais uma pagina do funil).
//
// O que este painel faz e SO apresentar. Ele nao monta prompt, nao escolhe
// modelo e nao dispara o ciclo de 30 minutos: o timer mora no servidor, porque
// timer no browser morre com a aba fechada, roda N vezes com N abas abertas e
// some quando a tela do celular bloqueia, que e exatamente quando o piloto
// esta na pista.
//
// `numeros_nao_conferidos` aparece na tela quando vem preenchido. E o guardrail
// do servidor dizendo "este numero a base de fatos nao sustenta". Esconder isso
// seria pior do que nao ter guardrail nenhum: daria ao texto uma autoridade que
// o proprio sistema ja sabe que ele nao tem. Regra dura do projeto, nao sai
// nesta reescrita.

const SUGESTOES = [
  "Onde eu perdi tempo?",
  "Estou melhorando ao longo da sessão?",
  "O que mudou desde a bateria anterior?",
];

/**
 * gravacaoId pode vir null: o painel existe fora do funil (FAB visivel em
 * qualquer tela), e nem toda tela tem uma gravacao aberta (ex.: tela de envio
 * de telemetria, ou catalogo vazio). Sem gravacao o painel abre mas explica
 * que ainda nao ha o que perguntar, em vez de deixar o formulario quebrar
 * numa chamada com gravacao_id vazio.
 */
export function PainelSarue({ gravacaoId }: { gravacaoId: string | null }) {
  const { aberto, ampliado, fechar, abrir, alternarLargura } = useSarue();

  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [avisos, setAvisos] = useState<Aviso[]>([]);
  const [pergunta, setPergunta] = useState("");
  const [pensando, setPensando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const painelRef = useRef<HTMLElement>(null);
  const campoRef = useRef<HTMLTextAreaElement>(null);
  const fimRef = useRef<HTMLDivElement>(null);

  const { tecladoAberto, aoFocarCampo, aoDesfocarCampo, ehAparelhoDeToque } = useTecladoVirtual();
  // o mascote tem um traco por tema, igual a logo do rail
  const simbolo = useTemaEfetivo() === "escuro" ? "/saru-simbolo.png" : "/saru-simbolo-preto.png";
  useEspacoDaPagina(painelRef, aberto, ampliado);
  useTravaDeArrasto(aberto, ".sarue-sb__lista, .sarue-sb__campo textarea");

  // Historico e avisos recarregam a cada troca de gravacao. Sem gravacaoId
  // nao ha o que buscar, e o estado anterior (de outra gravacao) some: turno
  // da volta 1 do bundle B nao pode continuar na tela depois de trocar pro
  // bundle A.
  useEffect(() => {
    if (!gravacaoId) {
      setTurnos([]);
      setAvisos([]);
      return;
    }
    let vivo = true;
    Promise.all([listarTurnos(gravacaoId), listarAvisos(gravacaoId)])
      .then(([t, a]) => {
        if (!vivo) return;
        setTurnos(t.slice().reverse());
        setAvisos(a);
      })
      .catch(() => {
        // historico vazio nao impede perguntar: falha aqui e silenciosa de
        // proposito, o erro que importa e o da pergunta
      });
    return () => {
      vivo = false;
    };
  }, [gravacaoId]);

  // So rola quando ja HA conversa. Rolagem suave na montagem, com a lista
  // vazia, deixava a pagina em animacao permanente: o alvo estava no fim de um
  // container que ainda estava crescendo, entao o scroll nunca chegava.
  useEffect(() => {
    if (!aberto) return;
    if (turnos.length === 0 && !pensando) return;
    fimRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [turnos.length, pensando, aberto]);

  // Foco no campo ao abrir, so no desktop: em aparelho de toque o foco
  // programatico nao sobe o teclado de verdade (exige gesto do usuario), entao
  // so serviria pra o painel se comportar como se o teclado estivesse aberto
  // sem ele realmente estar.
  useEffect(() => {
    if (!aberto) return;
    if (!ehAparelhoDeToque()) campoRef.current?.focus();
  }, [aberto, ehAparelhoDeToque]);

  async function mandar(texto: string) {
    const limpo = texto.trim();
    if (!limpo || pensando || !gravacaoId) return;
    setPergunta("");
    setPensando(true);
    setErro(null);
    try {
      const turno = await perguntar(gravacaoId, limpo);
      setTurnos((t) => [...t, turno]);
    } catch (e) {
      // 503 e o Sarue indisponivel (sem chave, ou o provedor caiu). E diferente
      // de "ele nao soube responder", e a tela precisa dizer qual dos dois foi.
      setErro(
        e instanceof ErroDaApi && e.status === 503
          ? `O Saruê está fora do ar: ${e.message}`
          : e instanceof ErroDaApi
            ? e.message
            : "não foi possível falar com o Saruê",
      );
    } finally {
      setPensando(false);
    }
  }

  function aoTeclar(ev: React.KeyboardEvent<HTMLTextAreaElement>) {
    // Enter envia, Shift+Enter quebra linha (mesmo padrao da Lana).
    if (ev.key === "Enter" && !ev.shiftKey) {
      ev.preventDefault();
      mandar(pergunta);
    }
  }

  const naoVistos = avisos.filter((a) => !a.visto_em);

  return (
    <>
      {/* Backdrop: so existe no mobile (a folha cobre a tela e precisa de um
          alvo de fechar). No desktop o site continua clicavel ao lado. */}
      {aberto && <div className="sarue-sb-backdrop" aria-hidden="true" onClick={fechar} />}

      {aberto && (
        <aside
          ref={painelRef}
          className={`sarue-sb${ampliado ? " sarue-sb--ampla" : ""}${tecladoAberto ? " sarue-sb--teclado" : ""}`}
          role="dialog"
          aria-modal="false"
          aria-label="Assistente Saruê"
          onKeyDown={(ev) => {
            if (ev.key === "Escape") fechar();
          }}
        >
          <header className="sarue-sb__topo">
            <div>
              <strong className="sarue-sb__nome">Saruê</strong>
              <span className="sarue-sb__papel">Assistente da sessão</span>
            </div>
            <div className="sarue-sb__acoes">
              <button
                type="button"
                className="sarue-sb__x sarue-sb__largura"
                aria-label={ampliado ? "Comprimir a conversa" : "Expandir a conversa"}
                aria-pressed={ampliado}
                title={ampliado ? "Comprimir a conversa" : "Expandir a conversa"}
                onClick={alternarLargura}
              >
                {!ampliado ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M14 4h6v6M20 4l-7 7M10 20H4v-6M4 20l7-7"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M20 10h-6V4M14 10l6-6M4 14h6v6M10 14l-6 6"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </button>
              <button
                type="button"
                className="sarue-sb__x"
                aria-label="Fechar conversa"
                title="Fechar conversa"
                onClick={fechar}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          </header>

          <p className="sarue-sb__lema">
            Ele só fala de números que o pipeline calculou. O que falta, ele diz que falta.
          </p>

          {naoVistos.length > 0 && (
            <div className="sarue-sb__avisos">
              {naoVistos.map((a) => (
                <div key={a.id} className="sarue-sb__aviso">
                  <p>{a.texto}</p>
                  <button
                    type="button"
                    className="sarue-sb__limpar"
                    onClick={() => {
                      marcarVisto(a.id).catch(() => undefined);
                      setAvisos((t) => t.map((x) => (x.id === a.id ? { ...x, visto_em: "agora" } : x)));
                    }}
                  >
                    ok, vi
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="sarue-sb__lista">
            {!gravacaoId && (
              <p className="sarue-sb__msg sarue-sb__msg--dela">
                Ainda não há gravação aberta. Abra uma sessão pra eu poder olhar os dados dela.
              </p>
            )}

            {gravacaoId && turnos.length === 0 && !pensando && (
              <div className="sarue-sb__sugestoes">
                {SUGESTOES.map((s) => (
                  <button key={s} type="button" className="sarue-sb__sugestao" onClick={() => mandar(s)}>
                    {s}
                  </button>
                ))}
              </div>
            )}

            {turnos.map((t) => (
              <div key={t.id} className="sarue-sb__turno">
                <p className="sarue-sb__msg sarue-sb__msg--minha">{t.pergunta}</p>
                {t.resposta ? (
                  <p className="sarue-sb__msg sarue-sb__msg--dela">{t.resposta}</p>
                ) : (
                  <p className="sarue-sb__msg sarue-sb__msg--dela sarue-sb__msg--falhou">
                    não veio resposta para esta pergunta
                  </p>
                )}
                {t.numeros_nao_conferidos && t.numeros_nao_conferidos.length > 0 && (
                  <p className="sarue-sb__suspeita">
                    Números que a base de fatos não sustenta: {t.numeros_nao_conferidos.join(", ")}. Trate com
                    desconfiança.
                  </p>
                )}
              </div>
            ))}

            {pensando && (
              <p className="sarue-sb__msg sarue-sb__msg--dela sarue-sb__correndo" aria-hidden="true">
                <span className="sarue-sb__corredor">
                  <img src={simbolo} alt="" width={30} height={30} />
                </span>
              </p>
            )}
            {erro && <p className="sarue-sb__erro">{erro}</p>}
            <div ref={fimRef} />
          </div>

          <form
            className="sarue-sb__forma"
            onSubmit={(ev) => {
              ev.preventDefault();
              mandar(pergunta);
            }}
          >
            <div className="sarue-sb__campo">
              <textarea
                ref={campoRef}
                rows={2}
                value={pergunta}
                placeholder={gravacaoId ? "Pergunte sobre esta sessão" : "Abra uma gravação pra perguntar"}
                disabled={pensando || !gravacaoId}
                onChange={(ev) => setPergunta(ev.target.value)}
                onKeyDown={aoTeclar}
                onFocus={aoFocarCampo}
                onBlur={aoDesfocarCampo}
              />
              <button type="submit" disabled={pensando || !gravacaoId || !pergunta.trim()} aria-label="Perguntar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path
                    d="M4 12h15M13 6l6 6-6 6"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            </div>
          </form>
        </aside>
      )}

      {/* FAB: some enquanto a conversa esta aberta, mesmo padrao da Lana. */}
      {!aberto && (
        <button type="button" className="sarue-sb-fab" onClick={abrir}>
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span>Saruê</span>
        </button>
      )}
    </>
  );
}
