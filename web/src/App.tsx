import { useEffect, useState, type ReactNode } from "react";
import "./estilo/app.css";
import "./estilo/sessao.css";
import { useAmostras } from "./dados/useAmostras";
import { useRelatorio } from "./dados/useRelatorio";
import { useGravacoes } from "./dados/useGravacoes";
import { useContexto } from "./dados/useContexto";
import { useBaterias } from "./ciclo/useEspinha";
import type { Relatorio } from "./types/contract";
import { useSelecao } from "./state/selection";
import { rotuloRef, tempo } from "./dados/formato";
import { voltaEmEscopo } from "./dados/escopo";
import { BarraEscopo } from "./componentes/BarraEscopo";
import { Rail } from "./componentes/Rail";
import { PAGINAS } from "./componentes/paginas";
import { Quadros } from "./componentes/Quadros";
import { MelhorVolta } from "./blocos/MelhorVolta";
import { RaioXMelhorVolta } from "./blocos/RaioXMelhorVolta";
import { OndeGanharTempo } from "./blocos/OndeGanharTempo";
import { ResumoDasVoltas } from "./blocos/ResumoDasVoltas";
import { EvolucaoPorVolta } from "./blocos/EvolucaoPorVolta";
import { DeltaEntreVoltas } from "./blocos/DeltaEntreVoltas";
import { TabelaEstatistica } from "./blocos/TabelaEstatistica";
import { Consumo } from "./blocos/Consumo";
import { MapaDaPista } from "./blocos/MapaDaPista";
import { TracoNoTempo } from "./blocos/TracoNoTempo";
import { TemperaturaDosPneus } from "./blocos/TemperaturaDosPneus";
import { PneuResumo } from "./blocos/PneuResumo";
import { ContextoDaBateria } from "./gavetas/ContextoDaBateria";
import { FichaDeSetup } from "./gavetas/FichaDeSetup";
import { PainelSarue } from "./sarue/PainelSarue";
import { Ciclo } from "./ciclo/Ciclo";
import type { Gravacao } from "./services/gravacoes";
import { Login } from "./sessao/Login";
import { useSessao } from "./sessao/useSessao";
import { useAplicarTema } from "./tema/useTema";

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
function faltasDeContexto(relatorio: Relatorio): string[] {
  const s = relatorio.contexto.sessao;
  if (!s.disponivel) return ["estado do pneu", "temperaturas", "combustível"];
  const faltas: string[] = [];
  if (s.vento_kmh == null) faltas.push("vento");
  if (!s.notas_piloto) faltas.push("observações do piloto");
  // o aviso so renderiza quando a bateria nao tem registro NENHUM (ver o
  // caller); esta lista e so o texto da frase
  return faltas.length ? faltas : ["o primeiro registro de contexto"];
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
      <button type="button" className="ghost" onClick={onVoltar}>&lsaquo; Box</button>
      <h3>{titulo}</h3>
      <span className="pergunta-pagina">{pergunta}</span>
    </div>
  );
}

/**
 * A tela. Recebe o relatorio JA RESOLVIDO por prop e nao sabe de onde ele veio:
 * e a mesma regra que vale pros blocos, aplicada um nivel acima. Quem lida com
 * rede, carregando e erro e a casca `App`, abaixo.
 */
function Analyzer({
  relatorio,
  gravacaoId,
  catalogo,
}: {
  relatorio: Relatorio;
  gravacaoId: string;
  catalogo: Gravacao[];
}) {
  const { volta, compara, refGravacaoId, refVolta, vista, irPara, eventoId, sessaoId, bateriaId, contextoAberto, setContextoAberto, setupAberto, setSetupAberto } = useSelecao();
  const [railAberto, setRailAberto] = useState(true);

  const voltas = relatorio.n1.voltas;
  const melhorN = relatorio.n0.melhor_volta.melhor_volta_n;
  // A store nao conhece dado de servidor, entao o default da referencia e
  // resolvido aqui: a melhor propria, que e contra o que o relatorio veio.
  const refAtiva = compara ?? melhorN;
  // regra 1.12 (29/08): analisada e referencia nunca coincidem, nem no default
  const emEscopo = voltaEmEscopo(voltas, volta, refGravacaoId ? "media" : refAtiva);
  const ehRef = refAtiva !== "media" && refAtiva === emEscopo;
  // quando volta e referencia coincidem nao ha o que sobrepor: cai para a media
  // com referencia de outro arquivo, a volta do lado B vem de la, nao daqui
  const refDoTraco = refGravacaoId ? (refVolta ?? 1) : ehRef ? ("media" as const) : refAtiva;

  // `refGravacaoId` faz a serie B vir de OUTRA gravacao: e o que transforma a
  // segunda barra de escopo em comparacao real entre dias, e nao so em rotulo.
  const { par, erro: erroAmostras } = useAmostras(gravacaoId, emEscopo, refDoTraco, refGravacaoId);
  const bateriaEscopo = voltas.find((v) => v.n === emEscopo)?.bateria?.rotulo ?? null;
  // a bateria do card de melhor volta e a DA MELHOR VOLTA, nao a do escopo:
  // mostrar a bateria da volta 13 ao lado da frase que fala da volta 7 seria
  // mentira de contexto, justo no card que existe pra dizer a verdade
  const bateriaDaMelhor = voltas.find((v) => v.n === melhorN)?.bateria?.rotulo ?? null;
  const faltas = faltasDeContexto(relatorio);
  // O aviso de contexto le a fonte REAL (registros da bateria em escopo), e
  // nao o relatorio: o piloto registrava e o aviso nao reconhecia, entao ele
  // registrava de novo, e de novo (medido em producao em 29/08: 4 registros
  // iguais em 90 segundos). Registro feito = pergunta respondida.
  const contextoDaBateria = useContexto("baterias", bateriaId);
  const bateriasDaSessao = useBaterias(sessaoId);
  const bateriaEmEscopo = bateriasDaSessao.dado?.find((b) => b.id === bateriaId) ?? null;
  const comprimento = relatorio.layout?.comprimento_m ?? 0;
  // data/hora da captura mora no catalogo, nao no relatorio
  const capturadoEm = catalogo.find((g) => g.gravacao_id === gravacaoId)?.capturado_em ?? null;

  const pagina = vista.tipo === "pagina" ? PAGINAS.find((p) => p.id === vista.id) : null;
  const voltarParaGeral = () => irPara({ tipo: "geral" });

  const bloco9 = (
    <OndeGanharTempo porCurva={relatorio.n2.por_curva} porMicro={relatorio.n2.por_micro_setor} comprimento_m={comprimento} />
  );
  const bloco4 = <ResumoDasVoltas voltas={voltas} melhorN={melhorN} refAtiva={refAtiva} emEscopo={emEscopo} />;
  const bloco5 = <EvolucaoPorVolta voltas={voltas} melhorN={melhorN} emEscopo={emEscopo} />;
  const bloco14 = (
    <Consumo
      consumo={relatorio.n1.consumo}
      voltas={voltas}
      emEscopo={emEscopo}
      bateriaRotulo={bateriaEscopo}
      bateriaEscopo={bateriaEmEscopo}
      aoInserir={() => setContextoAberto(true)}
    />
  );
  const bloco6 = par && (
    <DeltaEntreVoltas a={par.a} b={par.b} rotuloPar={`V${emEscopo} vs ${rotuloRef(refDoTraco)}`} ehRef={ehRef} />
  );
  const bloco7 = par && <TabelaEstatistica a={par.a} b={par.b} ehRef={ehRef} />;
  const bloco8 = (larga?: boolean) =>
    par && <MapaDaPista tracado={relatorio.tracado} trechos={relatorio.trechos} a={par.a} b={par.b} larga={larga} />;
  // Bloco 16. Fica no funil e nao no box porque LE telemetria: os quatro cantos
  // saem dos canais da volta em foco, nao de cadastro.
  const blocoPneus = (
    <TemperaturaDosPneus canais={relatorio.n3.canais} serie={par?.a ?? null} />
  );
  const bloco10 = par && (
    <TracoNoTempo a={par.a} b={par.b} rotuloA={`Volta ${emEscopo}`} rotuloB={rotuloRef(refDoTraco)} trechos={relatorio.trechos} />
  );

  return (
    <div className={`app${railAberto ? "" : " recolhido"}`}>
      <Rail temDado onRecolher={() => setRailAberto(false)} />

      {/* no box o respiro de 120px pro FAB vira scroll fantasma em tela
          baixa; la o conteudo e projetado pra caber, entao o respiro encolhe.
          Nas paginas de detalhe, que scrollam de verdade, a folga fica. */}
      <main className={`principal${vista.tipo === "geral" ? " justa" : ""}`}>
        <div className="navbar">
          {!railAberto && (
            <button type="button" className="ghost" onClick={() => setRailAberto(true)} title="Abrir painel">
              &rsaquo;&rsaquo; painel
            </button>
          )}
          <div>
            {/* faixa de contexto (item 1.7, ordem de prioridade do Vitor):
                piloto, pista, voltas, melhor volta, temperatura, data/hora.
                Veiculo e categoria ficam de fora ate existirem no dominio
                (D5, decisao do Lucas: nao inventar entidade por rotulo). */}
            <h2>{relatorio.piloto ?? "Piloto não identificado"}</h2>
            <p className="meta">
              {relatorio.layout?.nome ?? "pista não resolvida"}
              {" · "}{voltas.length} voltas
              {" · melhor "}{tempo(relatorio.n0.melhor_volta.melhor_volta_s)}
              {relatorio.contexto.sessao.disponivel && relatorio.contexto.sessao.temperatura_ar_c != null
                ? ` · ${relatorio.contexto.sessao.temperatura_ar_c.toFixed(0)}°C ar`
                : ""}
              {capturadoEm ? ` · ${new Date(capturadoEm).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}` : ""}
            </p>
          </div>
          <div className="espaco" />
          <span className={`pill ${relatorio.resolucao_pista === "nao_resolvida" ? "pill-warn" : "pill-ok"}`}>
            pista por {relatorio.resolucao_pista}
          </span>
          {/* O catalogo entra aqui porque trocar de bateria troca a GRAVACAO,
              e e a gravacao que o relatorio segue. Sem ele a barra saberia a
              bateria e nao saberia que arquivo abrir. */}
          <BarraEscopo relatorio={relatorio} catalogo={catalogo} />
        </div>

        {erroAmostras && (
          <p className="aviso-falha">
            As séries de amostra não vieram ({erroAmostras}). Os blocos que dependem delas ficam
            fora da tela até a próxima tentativa.
          </p>
        )}

        {vista.tipo === "geral" && (
          <>
            {/* O convite so aparece com a espinha completa E a bateria ainda
                SEM registro de contexto. Assim que o piloto registra, o aviso
                some: contexto e por bateria, e completar o registro e decisao
                dele na gaveta, nao cobranca em loop da tela. */}
            {eventoId && sessaoId && bateriaId && contextoDaBateria.dado?.length === 0 && (
              <PerguntaDaIngestao faltas={faltas} onAbrir={() => setContextoAberto(true)} />
            )}

            {/* Box (ex visao geral), ordem de 29/08: duas linhas 1x4 que
                misturam capa de pagina e card de dado, todas no mesmo padrao
                visual. Linha 1: onde ganhar tempo, melhor volta, combustivel,
                pneu. Linha 2: mapa, evolucao, delta (que abre o traco no
                tempo) e qual volta olhar. */}
            <div className="n0 quatro">
              <Quadros relatorio={relatorio} emEscopo={emEscopo} melhorN={melhorN} ids={["perdas"]} />
              <MelhorVolta
                compacto
                dados={relatorio.n0.melhor_volta}
                bateria={bateriaDaMelhor}
                onAbrir={() => irPara({ tipo: "pagina", id: "melhor_volta" })}
              />
              <Consumo
                consumo={relatorio.n1.consumo}
                voltas={voltas}
                emEscopo={emEscopo}
                bateriaRotulo={bateriaEscopo}
                bateriaEscopo={bateriaEmEscopo}
                aoAbrir={() => irPara({ tipo: "pagina", id: "consumo" })}
              />
              <PneuResumo
                bateriaId={bateriaId}
                canais={relatorio.n3.canais}
                serie={par?.a ?? null}
                aoAbrirContexto={() => irPara({ tipo: "pagina", id: "consumo" })}
              />
            </div>

            <div className="n0 quatro" style={{ marginTop: "var(--s3)" }}>
              <Quadros relatorio={relatorio} emEscopo={emEscopo} melhorN={melhorN} ids={["mapa", "evolucao"]} />
              {par && (
                <DeltaEntreVoltas
                  compacto
                  a={par.a}
                  b={par.b}
                  rotuloPar={`V${emEscopo} vs ${rotuloRef(refDoTraco)}`}
                  ehRef={ehRef}
                  aoAbrir={() => irPara({ tipo: "pagina", id: "traco" })}
                />
              )}
              <Quadros relatorio={relatorio} emEscopo={emEscopo} melhorN={melhorN} ids={["voltas"]} />
            </div>
          </>
        )}

        {pagina && (
          <>
            <CabecaDaPagina titulo={pagina.titulo} pergunta={pagina.pergunta} onVoltar={voltarParaGeral} />
            <div className="pilha">
              {vista.tipo === "pagina" && vista.id === "perdas" && bloco9}
              {vista.tipo === "pagina" && vista.id === "melhor_volta" && (
                <>
                  <MelhorVolta dados={relatorio.n0.melhor_volta} bateria={bateriaDaMelhor} onAbrir={voltarParaGeral} />
                  <RaioXMelhorVolta dados={relatorio.n0.melhor_volta} voltas={voltas} />
                </>
              )}
              {vista.tipo === "pagina" && vista.id === "mapa" && bloco8(true)}
              {vista.tipo === "pagina" && vista.id === "evolucao" && bloco5}
              {vista.tipo === "pagina" && vista.id === "consumo" && <>{bloco14}{blocoPneus}</>}
              {vista.tipo === "pagina" && vista.id === "voltas" && <>{bloco4}{bloco6}</>}
              {vista.tipo === "pagina" && vista.id === "traco" && <>{bloco10}{bloco7}</>}
            </div>
          </>
        )}

        {/* "envio" avulso deixou de existir (regra de 29/08): telemetria so
            entra pelo dia de pista, com a bateria na mao. A vista antiga
            redireciona pro ciclo pra nao quebrar escopo persistido. */}
        {vista.tipo === "envio" && (
          <>
            <CabecaDaPagina titulo="Dia de pista" pergunta="Evento, sessão e outing" onVoltar={voltarParaGeral} />
            <Ciclo />
          </>
        )}

        {vista.tipo === "ciclo" && (
          <>
            <CabecaDaPagina
              titulo="Dia de pista"
              pergunta="Evento, sessão e outing"
              onVoltar={voltarParaGeral}
            />
            <Ciclo />
          </>
        )}

      </main>

      {/* O Saruê e sidebar direita, no modelo da Lana: montado SEMPRE, com FAB
          proprio, e por isso fora do switch de vista. Perguntar sobre a sessao
          nao e um lugar pra onde se navega, e uma coisa que se faz enquanto se
          olha outra. */}
      <PainelSarue gravacaoId={gravacaoId} />

      {/* Dono das gavetas: a bateria quando a espinha existe, a gravacao quando
          o arquivo e solto (decisao D3, e o CHECK num_nonnulls do banco). */}
      {/* `layoutId` e o que permite a gaveta preencher ar e vento pela API de
          tempo: sem a pista resolvida nao ha coordenada, e a gaveta diz isso em
          vez de deixar os campos vazios sem explicacao. */}
      <ContextoDaBateria
        aberta={contextoAberto && vista.tipo !== "ciclo" && vista.tipo !== "envio"}
        dono={bateriaId ? "baterias" : "gravacoes"}
        alvoId={bateriaId ?? gravacaoId}
        layoutId={relatorio.layout?.id ?? null}
        onFechar={() => setContextoAberto(false)}
      />
      <FichaDeSetup
        aberta={setupAberto && vista.tipo !== "ciclo" && vista.tipo !== "envio"}
        dono={bateriaId ? "baterias" : "gravacoes"}
        alvoId={bateriaId ?? gravacaoId}
        onFechar={() => setSetupAberto(false)}
      />
    </div>
  );
}

// --- casca: e aqui, e so aqui, que o front sabe que existe rede ------------

function Aviso({ titulo, texto, acao }: { titulo: string; texto: string; acao?: ReactNode }) {
  // Saida de emergencia: tela terminal sem painel lateral nao tinha NENHUM
  // botao, e quem caia aqui com sessao ou escopo podre nao conseguia nem
  // deslogar pra recomecar (o limbo de 29/08). Sair limpa cookie e escopo.
  const { usuario, sair } = useSessao();
  // Container proprio, FORA do grid do app. Usando `.app` o aviso herdava a
  // coluna de 300px reservada pro painel lateral, mesmo sem painel nenhum na
  // tela, entao ele aparecia centrado na coluna da direita e nao na pagina; e
  // o `padding-bottom: 120px` do `.principal` ainda o empurrava pra cima.
  return (
    <div className="tela-cheia">
      <div className="estado-vazio">
        <h2>{titulo}</h2>
        <p>{texto}</p>
        {acao}
        {usuario && (
          <button type="button" className="limpar" onClick={() => sair()}>
            sair e entrar de novo
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * A casca que existe SEM relatorio.
 *
 * Corrige um beco sem saida: a tela de envio morava dentro do Analyzer, que
 * exige relatorio, que exige gravacao com volta cortada. Quem chegava sem
 * nenhuma gravacao via "nenhuma gravação analisável" e nao tinha por onde
 * enviar a primeira. O envio e o ciclo NAO dependem de relatorio, entao vivem
 * aqui, com o mesmo painel lateral do resto do app.
 */
function SemRelatorio({
  motivo,
  acao,
}: {
  motivo: string;
  acao?: ReactNode;
}) {
  const { vista, irPara } = useSelecao();
  const [railAberto, setRailAberto] = useState(true);

  return (
    <div className={`app${railAberto ? "" : " recolhido"}`}>
      <Rail temDado={false} onRecolher={() => setRailAberto(false)} />
      {/* no box o respiro de 120px pro FAB vira scroll fantasma em tela
          baixa; la o conteudo e projetado pra caber, entao o respiro encolhe.
          Nas paginas de detalhe, que scrollam de verdade, a folga fica. */}
      <main className={`principal${vista.tipo === "geral" ? " justa" : ""}`}>
        <div className="navbar">
          {!railAberto && (
            <button type="button" className="ghost" onClick={() => setRailAberto(true)} title="Abrir painel">
              &rsaquo;&rsaquo; painel
            </button>
          )}
          <div>
            <h2>SARU Analyzer</h2>
            <p className="meta">sem sessão aberta</p>
          </div>
        </div>

        {vista.tipo === "envio" || vista.tipo === "ciclo" ? (
          <>
            <CabecaDaPagina
              titulo="Dia de pista"
              pergunta="Evento, sessão e outing"
              onVoltar={() => irPara({ tipo: "geral" })}
            />
            <Ciclo />
          </>
        ) : (
          <div className="estado-vazio">
            <h2>Nenhuma gravação analisável</h2>
            <p>{motivo}</p>
            {/* o unico caminho e o dia de pista: telemetria so entra
                pendurada em evento -> sessao -> bateria (regra de 29/08) */}
            <button type="button" className="primario" onClick={() => irPara({ tipo: "ciclo" })}>
              Montar o dia de pista
            </button>
            {acao}
          </div>
        )}
      </main>
    </div>
  );
}

/**
 * Resolve QUAL gravacao esta aberta e busca o relatorio dela.
 *
 * A escolha default e "a mais recente que ja tem volta cortada", que e a
 * primeira linha de `GET /api/gravacoes?com_volta=true` (o backend ja ordena
 * por `capturado_em desc`). Sem volta nao ha N0 nem N1, entao abrir uma
 * gravacao ainda em processamento daria tela vazia sem explicacao.
 */
function AppComSessao() {
  const { gravacaoId, setGravacao, sincronizarEspinha, volta, compara, refGravacaoId, refVolta, setRefGravacao } =
    useSelecao();
  const catalogo = useGravacoes(true);

  // O default so vale enquanto o usuario nao escolheu: depois disso a escolha
  // dele manda, mesmo que o catalogo recarregue.
  //
  // A escolha e pela gravacao mais COMPLETA, nao pela mais recente. Ordenar so
  // por data fazia a primeira tela cair numa captura com pista nao resolvida:
  // sem layout nao ha comprimento, sem comprimento nao ha grade de distancia, e
  // a tela abria com todos os blocos degradados. Quem chega no sistema tem que
  // ver o produto funcionando, e nao o pior caso do acervo.
  //
  // Ordem de preferencia: tem trecho (rende N2 inteiro) > tem pista resolvida >
  // tem volta. Dentro de cada faixa, a mais recente, que e a ordem que o
  // servidor ja devolve.
  useEffect(() => {
    if (gravacaoId || !catalogo.dado || catalogo.dado.length === 0) return;
    // So telemetria PENDURADA alimenta o sistema (regra de 29/08): dado
    // existe atraves de evento -> sessao -> bateria. Gravacao solta nao e
    // candidata a default; acervo so de soltas abre a tela vazia, que
    // aponta pro dia de pista.
    const lista = catalogo.dado.filter((g) => g.bateria_id && g.finalidade !== "referencia");
    if (lista.length === 0) return;
    const melhor =
      lista.find((g) => g.trechos > 0 && g.layout_id) ??
      lista.find((g) => g.layout_id && g.voltas > 0) ??
      lista.find((g) => g.voltas > 0) ??
      lista[0];
    setGravacao(melhor.gravacao_id);
  }, [gravacaoId, catalogo.dado, setGravacao]);

  // A gravacao aberta que ficou SOLTA fecha na hora: excluir a bateria (ou a
  // sessao, ou o evento) despendura a telemetria, e mante-la na tela seria
  // mostrar dado que a espinha ja nao sustenta.
  //
  // Gravacao que simplesmente NAO ESTA no catalogo desta render NAO fecha
  // aqui: logo apos o upload o catalogo pode estar uma rodada atras da
  // gravacao recem-criada, e fechar nesse instante era a travada de 29/08
  // (tela vazia ate o F5). Quem fecha a gravacao que sumiu DE VERDADE e o
  // effect do 404 do relatorio, logo abaixo.
  useEffect(() => {
    if (!gravacaoId || !catalogo.dado || catalogo.carregando) return;
    const g = catalogo.dado.find((x) => x.gravacao_id === gravacaoId);
    if (g && !g.bateria_id) setGravacao(null);
  }, [gravacaoId, catalogo.dado, catalogo.carregando, setGravacao]);

  // Com referencia de outro arquivo, a volta comparada e a de LA, e o servidor
  // recalcula as perdas contra ela. Sem isso a segunda barra mudava o traco e
  // nao mudava o veredito, que era duas verdades na mesma tela.
  // A gravacao aberta ARRASTA a espinha junto: abrir uma telemetria posiciona
  // evento, sessao e bateria dela, entao o "Dia de pista" abre no lugar certo e
  // o contexto e a ficha de setup penduram no dono certo. Sem isto as duas
  // telas viravam dois mundos, e elas sao a mesma coisa por dois angulos.
  //
  // Gravacao solta (sem bateria) limpa a espinha em vez de manter a anterior:
  // deixar o evento de outra sessao na tela seria rotular este arquivo com um
  // dia de pista que nao e o dele.
  useEffect(() => {
    const g = catalogo.dado?.find((x) => x.gravacao_id === gravacaoId);
    if (!g) return;
    sincronizarEspinha(g.evento_id, g.sessao_id, g.bateria_id);
  }, [gravacaoId, catalogo.dado, sincronizarEspinha]);

  const relatorio = useRelatorio(
    gravacaoId,
    volta,
    refGravacaoId ? (refVolta ?? 1) : compara,
    refGravacaoId,
  );

  // TODO HOOK ANTES DE QUALQUER RETURN. Este effect ja morou depois dos early
  // returns de carregando/erro, e derrubava o app INTEIRO com "Rendered more
  // hooks than during the previous render" no primeiro render depois de o
  // catalogo carregar: era a tela branca pos-login de 29/08, pra todo usuario.
  //
  // O que ele faz: o 422 de "pistas diferentes" e erro da COMPARACAO, nao da
  // gravacao aberta. Desfaz o lado B e a analise continua de pe; qualquer
  // outro erro e tratado nos returns abaixo.
  useEffect(() => {
    if (relatorio.erro && refGravacaoId && /pista/i.test(relatorio.erro)) {
      setRefGravacao(null);
    }
  }, [relatorio.erro, refGravacaoId, setRefGravacao]);

  // Gravacao que sumiu de verdade (excluida aqui ou em outra sessao): o
  // servidor responde 404 no relatorio, e o escopo fecha pra casca cair no
  // default (outra pendurada) ou na tela vazia. E o substituto correto do
  // antigo "fecha o que nao esta no catalogo", que fechava cedo demais.
  useEffect(() => {
    if (relatorio.erro && !refGravacaoId && /encontrad/i.test(relatorio.erro)) {
      setGravacao(null);
    }
  }, [relatorio.erro, refGravacaoId, setGravacao]);

  if (catalogo.erro) {
    return (
      <Aviso
        titulo="Sem contato com a API"
        texto={`${catalogo.erro}. Confira se o backend está de pé e se o Postgres respondeu.`}
        acao={<button type="button" className="ghost" onClick={catalogo.recarregar}>Tentar de novo</button>}
      />
    );
  }
  if (catalogo.carregando) return <Aviso titulo="Carregando" texto="Buscando o catálogo de gravações." />;

  // Sem gravacao nenhuma a casca AINDA existe, com painel lateral, envio e
  // ciclo. Antes isto era um `Aviso` sem saida: a tela explicava que faltava
  // telemetria e nao oferecia por onde enviar a primeira.
  if (!catalogo.dado || catalogo.dado.length === 0) {
    return (
      <SemRelatorio motivo="Nenhuma telemetria pendurada num dia de pista. Monte o dia (evento, sessão e outing) e envie o arquivo de lá: é ele que liga a análise ao seu evento." />
    );
  }

  // Sem gravacao em escopo nao ha relatorio a montar: e o estado "conta sem
  // telemetria pendurada" (tudo despendurado ou acervo virgem), e a saida e
  // uma so, montar o dia de pista. Precisa vir ANTES das checagens abaixo,
  // senao a tela fica em "Carregando" pra sempre.
  if (!gravacaoId) {
    return (
      <SemRelatorio motivo="Nenhuma telemetria pendurada num dia de pista. Monte o dia (evento, sessão e outing) e envie o arquivo de lá: é ele que liga a análise ao seu evento." />
    );
  }

  const erroDaComparacao = !!(relatorio.erro && refGravacaoId && /pista/i.test(relatorio.erro));
  if (relatorio.erro && !erroDaComparacao) {
    // gravacao que sumiu do acervo (excluida, ou despendurada em outra
    // sessao) nao e um erro a reportar: o effect acima ja vai limpar o
    // escopo, e ate la a tela mostra o estado vazio neutro, sem botao de
    // tentar de novo (pedido de 29/08: nao ha o que tentar)
    return <SemRelatorio motivo={/encontrad/i.test(relatorio.erro) ? "Nenhuma telemetria pendurada num dia de pista. Monte o dia (evento, sessão e outing) e envie o arquivo de lá: é ele que liga a análise ao seu evento." : `O relatório desta gravação não veio: ${relatorio.erro}`} />;
  }
  // dado antigo fica na tela durante a recarga por troca de escopo: apagar tudo
  // a cada troca de volta faria a tela piscar a cada clique
  if (!relatorio.dado) return <Aviso titulo="Carregando" texto="Montando o relatório da gravação." />;

  return (
    <Analyzer
      relatorio={relatorio.dado}
      gravacaoId={gravacaoId as string}
      catalogo={catalogo.dado}
    />
  );
}

/**
 * O portao de sessao. Nada do app existe antes de saber quem esta logado.
 *
 * `carregando` na primeira renderizacao nao e detalhe: o token esta num cookie
 * httpOnly que o JavaScript nao le, entao a unica forma de saber se ha sessao e
 * perguntar ao servidor. Renderizar o login enquanto a pergunta esta no ar
 * faria a tela de login piscar a cada F5 de quem ja esta logado.
 */
export default function App() {
  const { usuario, carregando, conferir } = useSessao();
  // antes de qualquer tela: o tema guardado tem que valer ja no primeiro
  // quadro, senao a interface pisca na cor errada a cada carregamento
  useAplicarTema();

  useEffect(() => {
    conferir();
  }, [conferir]);

  if (carregando) return <Aviso titulo="Carregando" texto="Conferindo a sessão." />;
  if (!usuario) return <Login />;
  return <AppComSessao />;
}
