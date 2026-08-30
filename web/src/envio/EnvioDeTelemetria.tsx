import { useEffect, useRef, useState } from "react";
import { cravarPista, enviarBundle, estadoDaGravacao, listarGravacoes, type Gravacao } from "../services/gravacoes";
import { useLayouts } from "../ciclo/useEspinha";
import { ErroDaApi } from "../services/api";
import { criarBateria, vincularGravacao } from "../services/operacao";
import { useSelecao } from "../state/selection";
import { useBateriasDoEvento } from "../ciclo/useEspinha";
import { useEnvio } from "./estado";

// Fase 7. O front ORQUESTRA o envio, nao processa nada: escolher, mandar,
// mostrar progresso, e depois esperar. Duplicar aqui o corte de voltas ou a
// leitura de canal seria manter dois pipelines que divergem no primeiro bug.
//
// O backend devolve 202, nao o relatorio pronto: a recepcao (hash e registro) e
// sincrona, as etapas 2 a 6 rodam em background porque ha `.ld` de 400 MB no
// acervo e nenhum proxy aguenta esse request. Nao existe entidade de "job", e
// por isso o acompanhamento aqui e POLLING do catalogo: `voltas` sair de zero e
// o sinal de que o pipeline chegou na etapa 5.

const INTERVALO_POLL_MS = 3000;
const TENTATIVAS_MAX = 100; // ~5 min, depois disso a tela para de perguntar


function tamanho(bytes: number): string {
  if (bytes > 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  if (bytes > 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1e3))} KB`;
}

export function EnvioDeTelemetria({ aoConcluir, referencia = false }: {
  aoConcluir?: (g: Gravacao) => void;
  /** D3-B: modo base de comparacao. O arquivo entra marcado como referencia,
   *  nao pendura em outing nenhum e nao abre no Box: o destino dele e a linha
   *  "Comparar com". */
  referencia?: boolean;
}) {
  const [arquivos, setArquivos] = useState<File[]>([]);
  // fase e vinculo vem da store: sobrevivem a troca de tela
  const { fase, setFase, vinculo, setVinculo } = useEnvio();
  const input = useRef<HTMLInputElement>(null);

  // A bateria e o que faltava fechar no ciclo. Upload cria gravacao SOLTA de
  // proposito (`gravacao.bateria_id` e anulavel, decisao D3: arquivo entra sem
  // evento nenhum), mas o fluxo nunca oferecia o momento de pendurar, e a
  // bateria simplesmente nunca passava a existir pra quem so importava arquivo.
  // Agora: com bateria em escopo, pendura sozinho; sem bateria, a tela pergunta.
  const { eventoId, sessaoId, bateriaId, setBateria, setGravacao, irPara } = useSelecao();
  const baterias = useBateriasDoEvento(eventoId);
  // catalogo de pistas pro degrau "perguntado": quando o arquivo nao declara o
  // autodromo, quem estava la e a unica fonte que resta, e a tela pergunta
  const layouts = useLayouts();
  const [pistaEscolhida, setPistaEscolhida] = useState("");

  function adicionar(novos: FileList | null) {
    if (!novos) return;
    // Materializa AGORA, fora do updater: FileList de <input> e VIVO, e o
    // handler limpa `input.value` logo depois de chamar esta funcao, o que
    // ESVAZIA a lista antes de o updater (assincrono) rodar. Medido em
    // producao em 29/08: no instante do change havia 1 arquivo, 0 ms depois
    // havia 0, e o botao "Escolher arquivos" nunca adicionava nada (so o
    // drag and drop funcionava, porque DataTransfer nao e vivo).
    const chegando = Array.from(novos);
    // dedupe por (nome, tamanho): escolher a mesma pasta duas vezes e comum, e
    // mandar o mesmo arquivo duas vezes so faz o servidor recusar depois
    setArquivos((atuais) => {
      const chave = new Set(atuais.map((a) => `${a.name}:${a.size}`));
      return [...atuais, ...chegando.filter((a) => !chave.has(`${a.name}:${a.size}`))];
    });
  }

  // Retoma o acompanhamento ao voltar pra tela: o pipeline nao parou, so o
  // polling e que tinha morrido junto com o componente anterior.
  useEffect(() => {
    if (fase.nome === "processando") acompanhar(fase.gravacaoId, 0);
    if (fase.nome === "processando-varias") acompanharVarias(fase.itens, fase.bateriaAlvo, 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sair no meio do UPLOAD aborta a requisicao e o arquivo nunca chega inteiro.
  // Esse e o unico momento em que sair estraga alguma coisa, entao e o unico em
  // que vale interromper o usuario.
  useEffect(() => {
    if (fase.nome !== "enviando") return;
    const avisar = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", avisar);
    return () => window.removeEventListener("beforeunload", avisar);
  }, [fase.nome]);

  async function acompanhar(gravacaoId: string, tentativa = 0, bateriaAlvo: string | null = bateriaId) {
    if (tentativa >= TENTATIVAS_MAX) {
      setFase({
        nome: "parou",
        gravacaoId,
        motivo: "o pipeline ainda não cortou volta nenhuma. A gravação está registrada; abra o catálogo mais tarde.",
      });
      return;
    }
    setFase({ nome: "processando", gravacaoId, desde: fase.nome === "processando" ? fase.desde : Date.now() });
    await new Promise((r) => setTimeout(r, INTERVALO_POLL_MS));
    try {
      // Pergunta o ESTADO, nao a contagem: contagem zero nao distingue "ainda
      // rodando" de "terminou e nao deu". Era isso que fazia a tela girar pra
      // sempre num caso que o servidor ja sabia responder.
      const estado = await estadoDaGravacao(gravacaoId);
      if (estado.concluido && estado.voltas === 0) {
        setFase({
          nome: "parou",
          gravacaoId,
          motivo: `${estado.motivo ?? "o processamento terminou sem render voltas"}${
            estado.sugestao ? ` ${estado.sugestao}` : ""
          }`,
        });
        return;
      }
      const catalogo = await listarGravacoes(false);
      const minha = catalogo.find((g) => g.gravacao_id === gravacaoId);
      if (minha && minha.voltas > 0) {
        const pendurou = await pendurar(minha, bateriaAlvo);
        aoConcluir?.(minha);
        if (pendurou) {
          abrirNoBox(minha);
          return;
        }
        useSelecao.getState().tocarCatalogo();
        setFase({ nome: "pronto", gravacao: minha });
        return;
      }
      await acompanhar(gravacaoId, tentativa + 1, bateriaAlvo);
    } catch (e) {
      setFase({ nome: "erro", motivo: e instanceof ErroDaApi ? e.message : "falha ao consultar o catálogo" });
    }
  }

  /** D1-A: acompanha N gravacoes do mesmo envio ate TODAS concluirem, e
   *  monta o placar por arquivo (quantas voltas cada um trouxe, nomeando o
   *  arquivo). Nao abre o Box sozinho: com mais de uma captura, qual abrir e
   *  escolha de quem enviou, e o placar e a resposta que o envio deve. */
  async function acompanharVarias(
    itens: { id: string; nome: string }[],
    alvo: string | null,
    tentativa: number,
  ) {
    if (tentativa >= TENTATIVAS_MAX) {
      setFase({
        nome: "parou",
        gravacaoId: itens[0].id,
        motivo: "o pipeline ainda não terminou os arquivos. Eles ficam registrados; abra o catálogo mais tarde.",
      });
      return;
    }
    setFase({
      nome: "processando-varias",
      itens,
      bateriaAlvo: alvo,
      desde: fase.nome === "processando-varias" ? fase.desde : Date.now(),
    });
    await new Promise((r) => setTimeout(r, INTERVALO_POLL_MS));
    try {
      const estados = await Promise.all(itens.map((i) => estadoDaGravacao(i.id)));
      const prontos = estados.every((e) => e.concluido || e.voltas > 0);
      if (!prontos) {
        await acompanharVarias(itens, alvo, tentativa + 1);
        return;
      }
      const catalogo = await listarGravacoes(false);
      const placar = [];
      for (let i = 0; i < itens.length; i++) {
        const est = estados[i];
        const g = catalogo.find((x) => x.gravacao_id === itens[i].id) ?? null;
        if (est.voltas > 0 && g && alvo) await pendurar(g, alvo);
        placar.push({
          gravacaoId: itens[i].id,
          arquivo: itens[i].nome,
          voltas: est.voltas,
          layoutNome: g?.layout_nome ?? null,
          motivo: est.voltas > 0 ? null : (est.motivo ?? "terminou sem voltas"),
        });
      }
      useSelecao.getState().tocarCatalogo();
      const primeira = catalogo.find((x) => x.gravacao_id === itens[0].id);
      if (primeira) aoConcluir?.(primeira);
      setFase({ nome: "pronto-varias", itens: placar });
    } catch (e) {
      setFase({ nome: "erro", motivo: e instanceof ErroDaApi ? e.message : "falha ao consultar o catálogo" });
    }
  }

  /** Pendura na bateria ALVO, quando ha uma. Falha aqui nao perde o upload.
   *
   * O alvo e um SNAPSHOT da bateria em escopo no momento do clique em
   * "Finalizar envio", passado por parametro. Ler o escopo corrente aqui
   * pendurava na bateria errada: quando um upload cai no dedupe, `aoConcluir`
   * abre a gravacao ja existente e o App sincroniza a espinha pra bateria
   * DELA, e o proximo pendurar (que roda depois do polling) lia esse escopo
   * ja trocado (medido em producao em 29/08, arquivo caiu na bateria de
   * outra sessao). */
  async function pendurar(g: Gravacao, alvo: string | null): Promise<boolean> {
    if (!alvo) return false;
    try {
      await vincularGravacao(alvo, g.gravacao_id);
      setVinculo("pendurada na saída pra pista em escopo");
      return true;
    } catch (e) {
      // o arquivo ja esta no servidor e analisavel; so o vinculo falhou, e a
      // tela mostra o MOTIVO do servidor (caso tipico: o mesmo arquivo ja
      // esta pendurado em outra bateria, e mover roubaria de la) em vez de
      // fingir que o upload deu errado
      setVinculo(
        e instanceof ErroDaApi
          ? e.message
          : "o arquivo entrou, mas não consegui pendurar na saída",
      );
      return false;
    }
  }

  /** 2.1.7.3: anexou e pendurou, abre o Box direto. A tela de "pronto" so
   *  sobrevive pro caso em que ainda ha decisao a tomar (arquivo solto ou
   *  vinculo recusado). O catalogo e invalidado ANTES de navegar, entao a
   *  casca ja encontra a gravacao nova sem F5. */
  function abrirNoBox(g: Gravacao) {
    useSelecao.getState().tocarCatalogo();
    setVinculo(null);
    setFase({ nome: "escolhendo" });
    setGravacao(g.gravacao_id);
    irPara({ tipo: "geral" });
  }

  /** Cria bateria agora e pendura. Atalho pra quem importou sem montar o dia. */
  async function criarEPendurar(g: Gravacao): Promise<void> {
    if (!sessaoId) return;
    try {
      const nova = await criarBateria(sessaoId, { went_out_at: new Date().toISOString() });
      await vincularGravacao(nova.id, g.gravacao_id);
      setBateria(nova.id);
      baterias.recarregar();
      setVinculo("saída criada e telemetria pendurada nela");
    } catch (e) {
      setVinculo(e instanceof ErroDaApi ? e.message : "não consegui criar a saída");
    }
  }

  async function enviar() {
    if (arquivos.length === 0) return;
    // snapshot: a bateria que o usuario esta vendo AGORA e o alvo do pendurar,
    // mesmo que o escopo mude durante o polling (ver docstring de `pendurar`).
    // Referencia NUNCA pendura: o lugar dela e a base de comparacao.
    const bateriaAlvo = referencia ? null : bateriaId;
    setFase({ nome: "enviando", fracao: 0 });
    try {
      const recepcao = await enviarBundle(
        arquivos,
        (fracao) => setFase({ nome: "enviando", fracao }),
        referencia ? "referencia" : "piloto",
      );
      setArquivos([]);
      // D1-A: o servidor separa capturas; mais de uma vira o fluxo de placar
      if (recepcao.gravacoes.length > 1) {
        await acompanharVarias(
          recepcao.gravacoes.map((b) => ({
            id: b.gravacao_id,
            nome: b.arquivos.find((a) => a.papel === "primario")?.nome ?? b.arquivos[0]?.nome ?? "arquivo",
          })),
          bateriaAlvo,
          0,
        );
        return;
      }
      const unica = recepcao.gravacoes[0];
      if (unica.ja_existia) {
        // dedupe por hash no servidor: o pipeline nao roda de novo, entao
        // esperar por ele seria esperar pra sempre
        const catalogo = await listarGravacoes(false);
        const minha = catalogo.find((g) => g.gravacao_id === unica.gravacao_id);
        if (minha) {
          const pendurou = await pendurar(minha, bateriaAlvo);
          aoConcluir?.(minha);
          if (pendurou) {
            abrirNoBox(minha);
            return;
          }
          useSelecao.getState().tocarCatalogo();
          setFase({ nome: "pronto", gravacao: minha });
          return;
        }
      }
      await acompanhar(unica.gravacao_id, 0, bateriaAlvo);
    } catch (e) {
      setFase({ nome: "erro", motivo: e instanceof ErroDaApi ? e.message : "o envio falhou" });
    }
  }

  return (
    <div className="envio-area">
    <div className="envio">
      <div className="envio-cabeca">
        <h3>{referencia ? "Importar para a base de comparação" : "Enviar telemetria"}</h3>
        <p className="envio-sub">
          {referencia
            ? "Arquivo de referência (ex.: de outro piloto): entra marcado, fora da sua análise, e só aparece na linha \"Comparar com\"."
            : "O arquivo é lido e processado no servidor. Pode mandar o bundle inteiro de uma vez."}
        </p>
      </div>

      {/* `accept`: extensoes que o servidor cataloga (FAMILIAS de cli.py
          mais .xrz/.bak do AiM). Filtro de CONVENIENCIA do seletor: o
          servidor continua decidindo, e drag and drop nao passa por ele. */}
      <input
        ref={input}
        type="file"
        multiple
        hidden
        accept=".xrk,.xrz,.drk,.bak,.gpk,.rrk,.ld,.ldx,.dlf,.vbo,.dat,.pid,.csv,.mf4,.bmsbin"
        onChange={(e) => {
          adicionar(e.target.files);
          e.target.value = "";
        }}
      />

      {fase.nome === "escolhendo" && (
        <>
          <button type="button" className="ghost" onClick={() => input.current?.click()}>
            Escolher arquivos
          </button>

          {arquivos.length > 0 && (
            <ul className="envio-lista">
              {arquivos.map((a) => (
                <li key={`${a.name}:${a.size}`}>
                  <span className="nome">{a.name}</span>
                  <span className="peso">{tamanho(a.size)}</span>
                  <button
                    type="button"
                    className="limpar"
                    onClick={() => setArquivos((t) => t.filter((x) => x !== a))}
                    aria-label={`Remover ${a.name}`}
                  >
                    remover
                  </button>
                </li>
              ))}
            </ul>
          )}

          <button type="button" className="primario" disabled={arquivos.length === 0} onClick={enviar}>
            Finalizar envio{arquivos.length > 0 ? ` (${arquivos.length})` : ""}
          </button>
        </>
      )}

      {fase.nome === "enviando" && (
        <div className="envio-estado">
          <p><span className="giro" aria-hidden="true" /> Enviando</p>
          <div className="barra">
            <div className="preenchida" style={{ width: `${Math.round(fase.fracao * 100)}%` }} />
          </div>
          <span className="peso">{Math.round(fase.fracao * 100)}%</span>
        </div>
      )}

      {fase.nome === "processando" && (
        <div className="envio-estado">
          <p>
            <span className="giro" aria-hidden="true" />{" "}
            Recebido. O servidor está lendo os canais e cortando as voltas.
          </p>
          {/* O tempo decorrido aparece porque "processando" parado ha tres
              minutos sem nenhum sinal e indistinguivel de travado. Conta desde
              o inicio real, guardado na store, e nao desde a montagem deste
              componente: trocar de tela e voltar nao pode zerar o relogio. */}
          <span className="peso">
            processando há {Math.round((Date.now() - fase.desde) / 1000)}s. Pode navegar,
            o servidor continua mesmo com esta tela fechada.
          </span>
        </div>
      )}

      {fase.nome === "processando-varias" && (
        <div className="envio-estado">
          <p>
            <span className="giro" aria-hidden="true" />{" "}
            Recebidos {fase.itens.length} arquivos. O servidor está processando cada captura.
          </p>
          <span className="peso">
            processando há {Math.round((Date.now() - fase.desde) / 1000)}s. Pode navegar,
            o servidor continua mesmo com esta tela fechada.
          </span>
        </div>
      )}

      {fase.nome === "pronto-varias" && (
        <div className="envio-estado ok">
          <p>Pronto. Cada arquivo virou uma gravação própria:</p>
          <ul className="envio-lista">
            {fase.itens.map((i) => (
              <li key={i.gravacaoId}>
                <span className="nome">{i.arquivo}</span>
                <span className="peso">
                  {i.motivo ? i.motivo : `${i.voltas} voltas${i.layoutNome ? ` em ${i.layoutNome}` : ""}`}
                </span>
              </li>
            ))}
          </ul>
          {vinculo && <p className="peso">{vinculo}</p>}
          {fase.itens.some((i) => !i.motivo) && (
            <button
              type="button"
              className="primario"
              onClick={() => {
                const melhor = [...fase.itens].filter((i) => !i.motivo).sort((a, b) => b.voltas - a.voltas)[0];
                setGravacao(melhor.gravacaoId);
                setVinculo(null);
                setFase({ nome: "escolhendo" });
                irPara({ tipo: "geral" });
              }}
            >
              Abrir no Box
            </button>
          )}
          <button
            type="button"
            className="ghost"
            onClick={() => {
              setVinculo(null);
              setFase({ nome: "escolhendo" });
            }}
          >
            Enviar outro
          </button>
        </div>
      )}

      {fase.nome === "pronto" && (
        <div className="envio-estado ok">
          <p>
            Pronto: {fase.gravacao.voltas} voltas
            {fase.gravacao.layout_nome ? ` em ${fase.gravacao.layout_nome}` : ""}.
          </p>

          {vinculo && <p className="peso">{vinculo}</p>}

          {referencia && (
            <p className="peso">
              Este arquivo está na <b>base de comparação</b>: escolha ele na linha
              "Comparar com", no lugar do evento. Ele não aparece como volta analisada.
            </p>
          )}

          {/* Sem bateria em escopo, a gravacao fica solta. Isso e valido, mas
              tem que ser ESCOLHA, nao consequencia de a tela nao ter
              perguntado: sem bateria nao ha contexto, setup nem comparacao
              entre dias. */}
          {!referencia && !bateriaId && !vinculo && (
            <div className="envio-bateria">
              <p>
                Esta telemetria está <b>solta</b>, sem saída pra pista. Pendure numa saída para
                ela ter contexto, configurações do carro e comparação com os outros dias.
              </p>

              {baterias.dado && baterias.dado.length > 0 && (
                <label>
                  Pendurar numa saída existente
                  <select
                    defaultValue=""
                    onChange={async (e) => {
                      const id = e.target.value;
                      if (!id) return;
                      setBateria(id);
                      try {
                        await vincularGravacao(id, fase.gravacao.gravacao_id);
                        setVinculo("pendurada na saída escolhida");
                      } catch (err) {
                        setVinculo(
                          err instanceof ErroDaApi
                            ? err.message
                            : "não consegui pendurar nessa saída",
                        );
                      }
                    }}
                  >
                    <option value="" disabled>escolha a saída</option>
                    {baterias.dado.map(({ sessao: s, bateria: b }) => (
                      <option key={b.id} value={b.id}>
                        {s.label ?? s.type} · {b.label ?? (b.went_out_at
                          ? new Date(b.went_out_at).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })
                          : "sem horário")}
                      </option>
                    ))}
                  </select>
                </label>
              )}

              {sessaoId ? (
                <button type="button" className="ghost" onClick={() => criarEPendurar(fase.gravacao)}>
                  Criar saída pra pista agora e pendurar
                </button>
              ) : (
                <p className="peso">
                  Escolha um evento e uma sessão em <b>Dia de pista</b> para poder criar a saída.
                </p>
              )}
            </div>
          )}

          {/* O destino natural depois do upload que deu certo e OLHAR o dado.
              Poe a gravacao recem-processada em escopo e volta pra visao
              geral, que carrega o relatorio dela. Referencia NAO tem esse
              botao: ela nunca vira a volta analisada. */}
          {!referencia && (
            <button
              type="button"
              className="primario"
              onClick={() => {
                setGravacao(fase.gravacao.gravacao_id);
                irPara({ tipo: "geral" });
              }}
            >
              Ir para a visão geral
            </button>
          )}

          <button
            type="button"
            className="ghost"
            onClick={() => {
              setVinculo(null);
              setFase({ nome: "escolhendo" });
            }}
          >
            Enviar outro
          </button>
        </div>
      )}

      {fase.nome === "parou" && (
        <div className="envio-estado alerta">
          <p>{fase.motivo}</p>

          {/* Degrau "perguntado" da cascata (alias > GPS > perguntar): quando a
              pista nao resolveu, a pergunta vai pra quem estava la. A resposta
              fica marcada como "perguntado" no relatorio, nunca se disfarca de
              deteccao automatica. */}
          {/pista não foi resolvida/i.test(fase.motivo) && layouts.dado && (
            <div className="envio-bateria">
              <label>
                Em que pista foi gravado?
                <select value={pistaEscolhida} onChange={(e) => setPistaEscolhida(e.target.value)}>
                  <option value="" disabled>escolha a pista</option>
                  {layouts.dado.map((l) => (
                    <option key={l.id} value={l.id}>
                      {l.nome}{l.comprimento_m ? ` (${(l.comprimento_m / 1000).toFixed(3)} km)` : ""}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="primario"
                disabled={!pistaEscolhida}
                onClick={async () => {
                  try {
                    await cravarPista(fase.gravacaoId, pistaEscolhida);
                    await acompanhar(fase.gravacaoId, 0);
                  } catch (e) {
                    setFase({
                      nome: "erro",
                      motivo: e instanceof ErroDaApi ? e.message : "não consegui cravar a pista",
                    });
                  }
                }}
              >
                Usar esta pista e reprocessar
              </button>
            </div>
          )}

          <button type="button" className="ghost" onClick={() => acompanhar(fase.gravacaoId)}>
            Verificar de novo
          </button>

          {/* Saida sempre disponivel: "parou" e um RESULTADO (a gravação está
              registrada no servidor com o motivo acima), não uma prisão. Sem
              este botão o estado persistia fora do componente (useEnvio) e o
              usuário ficava preso aqui até limpar o storage — medido em
              produção em 29/08. */}
          <button
            type="button"
            className="ghost"
            onClick={() => {
              setVinculo(null);
              setArquivos([]);
              setFase({ nome: "escolhendo" });
            }}
          >
            Enviar outro arquivo
          </button>
        </div>
      )}

      {fase.nome === "erro" && (
        <div className="envio-estado alerta">
          <p>{fase.motivo}</p>
          <button type="button" className="ghost" onClick={() => setFase({ nome: "escolhendo" })}>
            Tentar de novo
          </button>
        </div>
      )}
    </div>
    </div>
  );
}
