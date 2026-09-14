import { useEffect, useState } from "react";
import type { Relatorio } from "../types/contract";
import { useSelecao } from "../state/selection";
import { useBateriasDoEvento, useEventos, useSessoes, useTrechos } from "../ciclo/useEspinha";
import type { Gravacao } from "../services/gravacoes";
import { tempo } from "../dados/formato";
import { voltaEmEscopo } from "../dados/escopo";
import { Modal } from "./Modal";
import { EnvioDeTelemetria } from "../envio/EnvioDeTelemetria";

// Escopo ativo na navbar. Regras de leitura:
//
// 1. Cor de destaque = o usuario muda. Cinza = vem do arquivo.
// 2. Volta e comparacao valem para o dashboard INTEIRO. Nenhum bloco tem
//    seletor de volta proprio: era assim que o traco no tempo acabava medindo
//    contra uma serie e o resto da tela contra outra.
// 3. Os dois seletores de volta dizem o PAPEL de cada um ("Volta analisada" e
//    "Comparar com"), nao o nome do campo.
//
// **Mudanca de 29/08 (decisao do Lucas):** evento, bateria e trecho tambem sao
// EDITAVEIS aqui. Antes eram texto cinza de proposito, pra ninguem tentar
// clicar no nome do evento. O custo daquilo era ter que ir ate "Dia de pista"
// pra trocar de bateria, que e o gesto mais frequente do dia. Agora troca no
// header, e a tela inteira acompanha no mesmo gesto: escolher bateria escolhe
// a gravacao pendurada nela, e a gravacao e o que o relatorio segue.
//
// **Mudanca de 29/08, segunda parte (decisao do Lucas): duas barras.** A linha
// de cima escolhe a volta ANALISADA (evento, bateria, volta, trecho). A linha
// de baixo escolhe a REFERENCIA, com o MESMO conjunto de campos, na MESMA
// ordem, so que pra outro dia ou outra bateria. Antes so dava pra comparar
// voltas dentro do MESMO arquivo (o `compara` de baixo). Agora existe um
// segundo escopo inteiro (`refEventoId`/`refBateriaId`/`refGravacaoId`/
// `refVolta`/`refTrecho`), e o antigo continua vivo como o caso default:
// `refGravacaoId` nulo e "comparar dentro do proprio arquivo", que e o
// comportamento de sempre.
//
// **Mudanca de 29/08, terceira parte (decisao do Lucas): simetria.** As duas
// linhas tem exatamente os mesmos 4 campos (Evento, Bateria, Volta, Trecho).
// Antes a linha de baixo nao tinha Trecho, e as duas ficavam com contagem
// diferente de campo, o que desalinhava os rotulos visualmente e insinuava
// que a referencia nao suportava escopo de trecho (suporta: `refTrecho`,
// alimentado pelo layout da gravacao de referencia via `useTrechos`, nao pelo
// da analisada).
export function BarraEscopo({
  relatorio,
  catalogo,
}: {
  relatorio: Relatorio;
  catalogo: Gravacao[];
}) {
  const {
    volta, compara, trecho, eventoId, sessaoId, bateriaId,
    refEventoId, refSessaoId, refBateriaId, refGravacaoId, refVolta,
    setVolta, setCompara, setTrecho, setSessao, setBateria, setGravacao,
    setRefEvento, setRefSessao, setRefBateria, setRefGravacao, setRefVolta,
    vista, irPara,
  } = useSelecao();

  const eventos = useEventos();
  const sessoes = useSessoes(eventoId);
  const baterias = useBateriasDoEvento(eventoId);
  const trechos = useTrechos(relatorio.layout?.id ?? null);

  // A linha de baixo tem o proprio par evento/bateria, entao pede o proprio
  // catalogo de baterias: o evento da referencia nao e o mesmo da analisada.
  const refEventosTodos = useEventos();
  const refSessoes = useSessoes(refEventoId);
  const refBateriasTodas = useBateriasDoEvento(refEventoId);

  /**
   * A comparacao so oferece o que E COMPARAVEL: mesmo layout da pista analisada.
   *
   * Antes a lista trazia tudo e um aviso avermelhava DEPOIS da escolha errada.
   * Avisar sobre um erro que a propria tela ofereceu e pior do que nao oferecer:
   * grade de distancia de outra pista nao compara com esta, entao evento de
   * outro layout nao e uma opcao ruim, e nao e opcao. O aviso continua no
   * codigo para o caso de uma selecao antiga sobreviver a troca de gravacao.
   */
  const layoutAnalisado = relatorio.layout?.id ?? null;
  const refEventos = {
    ...refEventosTodos,
    dado: refEventosTodos.dado?.filter((ev) => ev.track_id === layoutAnalisado) ?? null,
  };
  // Bateria sem telemetria nao rende comparacao, e bateria cuja gravacao esta
  // em outro layout tambem nao: as duas somem da lista pelo mesmo motivo.
  const refBaterias = {
    ...refBateriasTodas,
    dado:
      refBateriasTodas.dado?.filter(({ sessao: s, bateria }) => {
        if (refSessaoId && s.id !== refSessaoId) return false;
        const g = catalogo.find((x) => x.bateria_id === bateria.id);
        return g != null && g.layout_id === layoutAnalisado && g.voltas > 0;
      }) ?? null,
  };

  // A gravacao da referencia, quando ela e OUTRO arquivo. Vem do catalogo (a
  // mesma lista que a casca ja passa por prop), nunca de uma requisicao nova:
  // e so um lookup por id. Precisa vir antes do hook de trecho abaixo, porque
  // e dela que sai o layout que alimenta o seletor de trecho da referencia.
  const refGravacao = refGravacaoId ? catalogo.find((g) => g.gravacao_id === refGravacaoId) ?? null : null;

  // D3 (decisao do Vitor, 29/08): a cascata evento>sessao>outing vale pro
  // dado PRINCIPAL. Arquivo importado como referencia nao tem espinha: ele
  // entra na "base de dados do sistema", que ocupa o lugar do EVENTO na linha
  // de comparacao; sessao e outing nao se aplicam, e volta e setor seguem
  // selecionaveis. Mesmo corte de tracado dos eventos: pista diferente nao
  // rende delta com significado.
  const baseDeDados = catalogo.filter(
    (g) =>
      g.finalidade === "referencia" &&
      g.voltas > 0 &&
      (!layoutAnalisado || g.layout_id === layoutAnalisado),
  );
  // referencia vinda da base = gravacao pendurada SEM evento de referencia
  const modoBase = refGravacaoId != null && refEventoId == null;
  const [importando, setImportando] = useState(false);

  const voltas = relatorio.n1.voltas;
  // A store nao conhece dado de servidor, entao o default da referencia e
  // resolvido aqui: a melhor propria, que e contra o que o relatorio ja veio
  // calculado. Sem isto o seletor mostrava uma referencia e o insight, outra.
  const refAtiva = compara ?? relatorio.n0.melhor_volta.melhor_volta_n;
  // regra 1.12 (29/08): analisada e referencia nunca coincidem, nem no default
  const emEscopo = voltaEmEscopo(voltas, volta, refGravacaoId ? "media" : refAtiva);
  const bateriaDaVolta = voltas.find((v) => v.n === emEscopo)?.bateria ?? null;
  const sessao = relatorio.contexto.sessao;

  // GUARDA DE PISTA (o ponto mais importante desta mudanca): a grade de
  // distancia de uma pista nao serve pra outra, entao comparar volta de
  // layouts diferentes produz um delta sem significado, nao um delta ruim.
  // So dispara quando os dois layouts sao conhecidos e diferentes; layout
  // desconhecido nao e "diferente", e "ainda nao sei".
  const pistaDivergente = Boolean(
    refGravacao?.layout_id && relatorio.layout?.id && refGravacao.layout_id !== relatorio.layout.id,
  );

  /**
   * Trocar de bateria troca a GRAVACAO em escopo, e e isso que faz a tela
   * inteira atualizar: o relatorio e as amostras seguem a gravacao.
   *
   * Bateria sem gravacao pendurada e caso valido (a bateria existe antes de o
   * arquivo chegar). Nesse caso a selecao da bateria vale, e a gravacao fica
   * como estava, em vez de a tela esvaziar: o piloto marcou a saida pra pista,
   * nao pediu pra fechar a analise que estava lendo.
   */
  function escolherBateria(id: string) {
    marcarMudanca();
    setBateria(id);
    const dela = catalogo.find((g) => g.bateria_id === id);
    if (dela) setGravacao(dela.gravacao_id);
  }

  // Espelho de `escolherBateria` pro lado B: escolher a bateria da referencia
  // pendura a gravacao dela em `refGravacaoId`, que e o gatilho que tira a
  // comparacao de dentro do proprio arquivo.
  function escolherBateriaRef(id: string) {
    marcarMudanca();
    setRefBateria(id);
    const dela = catalogo.find((g) => g.bateria_id === id);
    if (dela) setRefGravacao(dela.gravacao_id);
  }

  const rotuloDoTrecho = (id: string) => {
    for (const fonte of [relatorio.n2.por_curva, relatorio.n2.por_micro_setor]) {
      if (!fonte.disponivel) continue;
      const achado = fonte.itens.find((p) => p.trecho_id === id);
      if (achado) return achado.rotulo;
    }
    return id;
  };

  // item 1.10 (29/08): cada volta com o tempo dela e a diferenca pra melhor.
  // Out lap e in lap nunca viram volta (o corte e ENTRE passagens na linha),
  // entao os tipos possiveis aqui sao melhor, valida (+delta) e invalida.
  const rotulo = (n: number) => {
    const v = voltas.find((x) => x.n === n)!;
    const t = tempo(v.tempo_s);
    const delta = v.tempo_s - relatorio.n0.melhor_volta.melhor_volta_s;
    const marca = v.n === relatorio.n0.melhor_volta.melhor_volta_n
      ? " · melhor"
      : v.valida
      ? ` · +${delta.toFixed(3)}`
      : ` · inválida (${v.motivo_invalida})`;
    return `Volta ${v.n} · ${t}${marca}${v.bateria ? ` · ${v.bateria.rotulo.replace("Bateria ", "B")}` : ""}`;
  };

  const hora = (iso: string | null) =>
    iso ? new Date(iso).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" }) : "sem horário";

  // Retratil, versao 1.9 (escolha A do Vitor): recolher esconde SO a linha de
  // referencia; a analisada fica sempre aberta e operavel. O estado e da
  // sessao de uso, nao persiste.
  //
  // Nasce FECHADA (pedido do Lucas, 30/08): comparar com outra captura e o
  // caso menos frequente, e a linha extra ocupava o topo da analise o tempo
  // todo. Quem vai comparar abre.
  const [aberto, setAberto] = useState(false);

  // item 1.11 (29/08): mudar o escopo fora do Box NAO navega sozinho
  // ("qualquer tela incomoda se nao for a de analise"): aparece um aviso com
  // "ver analise", e quem navega e o usuario.
  const [mudou, setMudou] = useState(false);
  const marcarMudanca = () => {
    if (vista.tipo !== "geral") setMudou(true);
  };
  useEffect(() => {
    if (vista.tipo === "geral") setMudou(false);
  }, [vista.tipo]);

  const refTexto = refGravacao
    ? refEventoId
      ? `volta ${refVolta ?? 1} · ${hora(refBaterias.dado?.find(({ bateria: b }) => b.id === refBateriaId)?.bateria.went_out_at ?? null)}`
      : `base: ${refGravacao.label ?? refGravacao.layout_nome ?? "arquivo"} · volta ${refVolta ?? 1}`
    : refAtiva === "media" ? "média das válidas" : `volta ${refAtiva}`;

  return (
    <div className="escopo">
      <div className="escopo-linha">
        <span className="escopo-rotulo escopo-rotulo-a">Volta analisada</span>

        {/* O evento da linha analisada NAO e seletor (regra de 29/08): a
            analise vive dentro do evento atual, e o banco inteiro de
            telemetria so abre na linha de baixo, pra comparar. Trocar de
            evento e gesto do Dia de pista, nao daqui. */}
        <div className="escopo-campo">
          <span className="k">Evento</span>
          <span
            className="v"
            title={eventos.dado?.find((ev) => ev.id === eventoId)?.name ?? undefined}
          >
            {eventos.dado?.find((ev) => ev.id === eventoId)?.name
              ?? relatorio.layout?.nome
              ?? "pista não resolvida"}
          </span>
        </div>

        {/* Sessao entrou como nivel proprio em 29/08 a pedido: sem ele, duas
            sessoes do mesmo evento viravam uma lista unica de baterias e nao
            dava pra COMPARAR a mesma sessao (ou sessoes diferentes) de
            proposito. Vazio = todas as sessoes do evento. */}
        <div className="escopo-campo editavel">
          <span className="k">Sessão</span>
          {eventoId && sessoes.dado && sessoes.dado.length > 0 ? (
            <select
              value={sessaoId ?? ""}
              onChange={(e) => { marcarMudanca(); setSessao(e.target.value || null); }}
              aria-label="Sessão em escopo"
            >
              {/* cascata (pedido de 29/08): sem sessao escolhida nao ha
                  bateria; o placeholder cobra a escolha em vez de "todas" */}
              <option value="" disabled>escolha a sessão</option>
              {sessoes.dado.map((s) => (
                <option key={s.id} value={s.id}>{s.label ?? s.type}</option>
              ))}
            </select>
          ) : (
            <span className="v">{eventoId ? "sem sessão cadastrada" : "arquivo solto"}</span>
          )}
        </div>

        <div className="escopo-campo editavel">
          <span className="k">Saída pra pista</span>
          {!sessaoId ? (
            // cascata: bateria so depois da sessao
            <span className="v fraco-cascata">escolha a sessão</span>
          ) : eventoId && baterias.dado && baterias.dado.length > 0 ? (
            <select
              value={bateriaId ?? ""}
              onChange={(e) => escolherBateria(e.target.value)}
              aria-label="Saída pra pista em escopo"
            >
              <option value="" disabled>escolha a saída</option>
              {baterias.dado
                .filter(({ sessao: s }) => s.id === sessaoId)
                .map(({ bateria: b }) => (
                <option key={b.id} value={b.id}>
                  {b.label ?? hora(b.went_out_at)}
                  {b.gravacoes ? "" : " · sem telemetria"}
                </option>
              ))}
            </select>
          ) : (
            <span className="v">
              {bateriaDaVolta
                ? `${bateriaDaVolta.rotulo}${sessao.disponivel && sessao.horario ? ` · ${sessao.horario}` : ""}`
                : "nula (arquivo solto)"}
            </span>
          )}
        </div>

        <div className="escopo-campo editavel">
          <span className="k">Volta</span>
          <select value={emEscopo} onChange={(e) => { marcarMudanca(); setVolta(Number(e.target.value)); }} aria-label="Volta em escopo">
            {/* 1.12: a volta que esta na referencia some daqui (mesmo arquivo) */}
            {voltas
              .filter((v) => refGravacaoId != null || refAtiva === "media" || v.n !== refAtiva)
              .map((v) => (
                <option key={v.n} value={v.n}>{rotulo(v.n)}</option>
              ))}
          </select>
        </div>

        <div className="escopo-campo editavel">
          <span className="k">Trecho</span>
          {trechos.dado && trechos.dado.length > 0 ? (
            <select
              value={trecho ?? ""}
              onChange={(e) => { marcarMudanca(); setTrecho(e.target.value || null); }}
              aria-label="Trecho em escopo"
            >
              <option value="">a volta inteira</option>
              {trechos.dado.map((t) => (
                <option key={t.id} value={t.id}>{t.rotulo}</option>
              ))}
            </select>
          ) : (
            // sem catalogo de curva no layout nao ha o que escolher, e select
            // vazio promete uma escolha que nao existe
            <span className="v">
              {trecho ? rotuloDoTrecho(trecho) : "a volta inteira"}
              {trecho && (
                <button type="button" className="limpar" onClick={() => setTrecho(null)} title="Voltar ao escopo da volta inteira">
                  limpar
                </button>
              )}
            </span>
          )}
        </div>
      </div>

      {!aberto && (
        <div className="escopo-resumo">
          <span className="par"><em>referência</em> {refTexto}</span>
          <button type="button" className="escopo-aba" onClick={() => setAberto(true)} title="Expandir a linha de referência">
            ▾ mostrar referência
          </button>
        </div>
      )}

      {aberto && (
      <div className="escopo-linha">
        <span className="escopo-rotulo escopo-rotulo-b">Comparar com</span>

        <div className="escopo-campo editavel">
          <span className="k">Evento</span>
          {(refEventos.dado && refEventos.dado.length > 0) || baseDeDados.length > 0 ? (
            <select
              value={modoBase ? `base:${refGravacaoId}` : (refEventoId ?? "")}
              onChange={(e) => {
                marcarMudanca();
                const valor = e.target.value;
                if (valor.startsWith("base:")) {
                  // base de dados no lugar do evento: limpa a espinha da
                  // referencia e pendura a gravacao direto
                  setRefEvento(null);
                  setRefGravacao(valor.slice(5));
                } else {
                  setRefEvento(valor || null);
                }
              }}
              aria-label="Evento da referência"
            >
              {/* vazio aqui volta pro default: comparar dentro do proprio arquivo */}
              <option value="">próprio arquivo</option>
              {(refEventos.dado ?? []).map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.name}{ev.layout_nome ? ` · ${ev.layout_nome}` : ""}
                </option>
              ))}
              {baseDeDados.length > 0 && (
                <optgroup label="Base de dados do sistema">
                  {baseDeDados.map((g) => (
                    <option key={g.gravacao_id} value={`base:${g.gravacao_id}`}>
                      {g.label ?? g.layout_nome ?? g.gravacao_id.slice(0, 8)} · {g.voltas} voltas
                    </option>
                  ))}
                </optgroup>
              )}
            </select>
          ) : (
            <span className="v">
              {layoutAnalisado
                ? "nenhum evento nesta pista"
                : "pista não resolvida, sem comparação entre arquivos"}
            </span>
          )}
          <button
            type="button"
            className="limpar"
            title="Importar arquivo de referência (ex.: de outro piloto) para a base de comparação"
            onClick={() => setImportando(true)}
          >
            + base
          </button>
        </div>

        <div className="escopo-campo editavel">
          <span className="k">Sessão</span>
          {refEventoId && refSessoes.dado && refSessoes.dado.length > 0 ? (
            <select
              value={refSessaoId ?? ""}
              onChange={(e) => { marcarMudanca(); setRefSessao(e.target.value || null); }}
              aria-label="Sessão da referência"
            >
              <option value="" disabled>escolha a sessão</option>
              {refSessoes.dado.map((s) => (
                <option key={s.id} value={s.id}>{s.label ?? s.type}</option>
              ))}
            </select>
          ) : (
            <span className="v">
              {modoBase ? "base de dados · não se aplica" : refEventoId ? "sem sessão cadastrada" : "escolha um evento"}
            </span>
          )}
        </div>

        <div className="escopo-campo editavel">
          <span className="k">Saída pra pista</span>
          {modoBase ? (
            <span className="v">base de dados · não se aplica</span>
          ) : !refEventoId ? (
            <span className="v">escolha o evento</span>
          ) : !refSessaoId ? (
            // cascata (pedido de 29/08): sem sessao nao ha bateria
            <span className="v">escolha a sessão</span>
          ) : refBaterias.dado && refBaterias.dado.length > 0 ? (
            <select
              value={refBateriaId ?? ""}
              onChange={(e) => escolherBateriaRef(e.target.value)}
              aria-label="Saída pra pista da referência"
            >
              <option value="" disabled>escolha a saída</option>
              {refBaterias.dado.map(({ bateria: b }) => (
                <option key={b.id} value={b.id}>
                  {b.label ?? hora(b.went_out_at)}
                  {b.gravacoes ? "" : " · sem telemetria"}
                </option>
              ))}
            </select>
          ) : (
            <span className="v">nenhuma saída com telemetria nesta sessão</span>
          )}
        </div>

        <div className="escopo-campo editavel">
          <span className="k">Volta</span>
          {refEventoId && !refGravacaoId ? (
            // cascata: evento escolhido mas bateria ainda nao. A volta e da
            // gravacao pendurada na bateria, entao nao ha o que listar antes.
            <span className="v">escolha a saída</span>
          ) : refGravacaoId ? (
            // gravacao de outro arquivo: a unica coisa que se sabe dela aqui e
            // quantas voltas tem (o catalogo), nao qual e a melhor ou invalida,
            // porque o relatorio dela nao foi carregado nesta tela
            refGravacao && refGravacao.voltas > 0 ? (
              <select
                value={refVolta ?? ""}
                onChange={(e) => { marcarMudanca(); setRefVolta(Number(e.target.value)); }}
                aria-label="Volta da referência"
              >
                {/* cascata: a volta e escolha explicita, nao default mudo */}
                <option value="" disabled>escolha a volta</option>
                {Array.from({ length: refGravacao.voltas }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>Volta {n}</option>
                ))}
              </select>
            ) : (
              <span className="v">sem voltas processadas</span>
            )
          ) : (
            <select
              value={String(refAtiva)}
              onChange={(e) => { marcarMudanca(); setCompara(e.target.value === "media" ? "media" : Number(e.target.value)); }}
              aria-label="Volta da referência"
            >
              <option value="media">Média das válidas</option>
              {/* 1.12: a volta analisada some da lista de referencia */}
              {voltas
                .filter((v) => v.n !== emEscopo)
                .map((v) => (
                  <option key={v.n} value={v.n}>{rotulo(v.n)}</option>
                ))}
            </select>
          )}
        </div>

        {/* 1.8 (29/08): trecho e UM campo so, o da linha analisada, valendo
            pros dois lados. Comparar a curva 3 com a curva 5 de outro dia
            nunca faz sentido em pista (palavras do Vitor), entao a referencia
            espelha o trecho analisado em vez de oferecer outro. */}
        <div className="escopo-campo">
          <span className="k">Trecho</span>
          <span className="v">{trecho ? rotuloDoTrecho(trecho) : "a volta inteira"} · o mesmo dos dois lados</span>
        </div>
      </div>
      )}

      {aberto && (
        <button type="button" className="escopo-aba" onClick={() => setAberto(false)} title="Recolher a linha de referência">
          ▴ recolher referência
        </button>
      )}

      {/* item 1.11: mudanca de escopo fora do Box avisa e espera; navegar e
          gesto do usuario, nunca efeito colateral de um select */}
      {mudou && vista.tipo !== "geral" && (
        <div className="escopo-aviso info">
          Escopo atualizado. A análise recalculou com a nova seleção.
          <button type="button" className="ghost" onClick={() => { setMudou(false); irPara({ tipo: "geral" }); }}>
            ver análise
          </button>
        </div>
      )}

      <Modal
        titulo="Base de comparação"
        aberto={importando}
        aoFechar={() => setImportando(false)}
      >
        {/* D3-B: o arquivo entra marcado como referencia; nao pendura em
            outing e nao vira volta analisada. Fechar o modal nao cancela o
            processamento, que continua no servidor. */}
        <EnvioDeTelemetria referencia />
      </Modal>

      {pistaDivergente && (
        // aviso duro, nao silencioso: a grade de distancia de uma pista nao
        // serve pra outra, entao o delta calculado seria ruido travestido de dado
        <div className="escopo-aviso">
          Pista da referência ({refGravacao?.layout_nome ?? "layout diferente"}) não é a mesma da volta analisada
          ({relatorio.layout?.nome ?? "layout não resolvido"}). Comparação não é válida entre pistas diferentes.
        </div>
      )}

    </div>
  );
}
