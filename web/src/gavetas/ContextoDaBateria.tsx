import { useEffect, useState } from "react";
import { useRequisicao } from "../dados/requisicao";
import { useSelecao } from "../state/selection";
import { useBaterias } from "../ciclo/useEspinha";
import {
  editarBateria,
  editarContexto,
  excluirContexto,
  historicoContexto,
  registrarContexto,
  salvarSetup,
  versoesSetup,
  type Dono,
  type RegistroContexto,
  type VersaoSetup,
} from "../services/operacao";
import { climaDoLayout } from "../services/clima";
import { ErroDaApi } from "../services/api";
import type { CapturaContextoSessao } from "../types/ingestao";
import { Gaveta } from "./Gaveta";
import "../estilo/gavetas.css";

// Bloco 15. Nao e tela de leitura: e CAPTURA. O que falta aparece marcado em
// vez de preenchido por default, que e a regra do B2 aplicada ao contexto.
//
// Fase 4: virou leitura E escrita reais contra /baterias|gravacoes/:id/contexto.
// Contexto e append-only de proposito (decisao do plano): temperatura as 9h e
// as 14h sao dois fatos, nao uma correcao um do outro. Por isso esta tela tem
// DUAS partes: o registro mais recente como referencia (cinza, vem do
// arquivo) e um formulario de captura novo (destaque, o usuario digita),
// mais o historico completo embaixo com horario de cada registro.
//
// Fase 10: temperatura do ar e vento pararam de ser digitados. O que a API de
// tempo ja sabe vem marcado como automatico e ninguem digita: `/clima/:id`
// (mesma fonte do bloco 17, `TempoComPrevisao.tsx`) devolve os dois, a gaveta
// so pede confirmacao. Assim que o piloto edita um desses campos, ele vira
// dado do usuario (perde o rotulo "auto", ganha a cor de destaque da casa) e
// para de ser atualizado pela API, porque o que foi digitado a mao e mais
// confiavel que o numero da estacao mais proxima.
//
// Fase 11: o cadastro de combustivel muda de casa. Antes vivia solto no Box
// (que agora e so leitura); o lugar certo e aqui, porque combustivel e um
// fato do momento igual pneu e clima, nao uma metrica calculada. Os litros
// nao persistem na tabela `contexto` (ela nao tem essa coluna e essa tarefa
// nao cria migration): eles moram em `bateria.fuel_in_l/fuel_out_l`, e por
// isso salvar aqui faz DUAS chamadas em sequencia, registrar o contexto e
// depois (so quando ha bateria em escopo) o PATCH da bateria. Gravacao solta
// nao tem bateria pra ancorar o dado: os campos ficam desabilitados com o
// motivo em vez de aceitar e perder o numero em silencio.
//
// O wrapper de PATCH pra bateria ainda nao existe em `services/operacao.ts`
// (arquivo fora do escopo desta sessao, outra sessao mexe la agora). Em vez
// de inventar um nome e quebrar quando o de verdade aparecer, o fetch fica
// local aqui embaixo, no mesmo formato de `services/api.ts` (base `/api`,
// erro tipado como `ErroDaApi`). Quando `operacao.ts` ganhar essa funcao,
// isso deveria migrar pra la e este helper local some.
//
// Fase 12: pressao-alvo a quente e carcaca medida migram do Box (que virou
// so leitura, `box/PressaoAFrio.tsx`) pra ca. Nenhuma das duas tem coluna em
// `contexto` e esta tarefa nao cria migration, entao elas nao vao no POST de
// contexto: vao pra ficha de SETUP (`valores` livre em JSONB, mesma tabela
// que `gavetas/FichaDeSetup.tsx` edita como pares chave/valor). Chaves
// estaveis e explicitas, pra o Box saber exatamente onde ler:
// `pressao_alvo_quente_psi` e `carcaca_c`. Por ser JSONB livre, salvar aqui
// tem que carregar a versao mais recente da ficha e so SOBRESCREVER essas
// duas chaves (preservando o resto que a Ficha de Setup já tenha gravado),
// senao um registro de contexto apaga setup que nao tem nada a ver com ele.
// Setup e versionado (nunca PUT), entao isso cria uma versao nova, igual a
// Ficha de Setup faria.

/** Campo de LEITURA do registro mais recente: so mostra, nunca edita. Cinza
 * quando tem valor, marcado "falta" quando nao tem, porque nao existe
 * default silencioso aqui tambem. */
function campoLeitura(rot: string, valor: string | number | null, unidade = "") {
  const tem = valor != null && valor !== "";
  return (
    <div className={`campo ${tem ? "ok" : "falta"}`} key={rot}>
      <label>{rot}</label>
      <input
        disabled
        value={tem ? `${valor}${unidade}` : ""}
        placeholder={tem ? "" : "sem registro"}
      />
    </div>
  );
}

/** Horario local, formato HH:MM, pra pre-preencher o campo sem precisar de
 * biblioteca de data. */
function horarioAgora(): string {
  return new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

/** "1h20min" ou "12min": idade de um timestamp em texto curto, pro aviso de
 * registro envelhecido logo abaixo. */
function formatarIdade(ms: number): string {
  const minTotal = Math.max(0, Math.floor(ms / 60000));
  if (minTotal < 60) return `${minTotal}min`;
  const h = Math.floor(minTotal / 60);
  const resto = minTotal % 60;
  return resto > 0 ? `${h}h${resto}min` : `${h}h`;
}

/** Fase 5: "implementar atualização a cada 30 minutos" do contexto. O
 * contexto e append-only por decisao (temperatura as 9h e as 14h sao dois
 * fatos, nao uma correcao), entao nao ha o que atualizar sozinho: o sistema
 * so PEDE um registro novo quando o mais recente envelheceu, no espirito do
 * texto que o app ja usa ("ultimo envio foi ha 2h, mudou temperatura ou
 * vento?"). Nunca registra nada automatico, so avisa. */
const LIMITE_ATUALIZACAO_MS = 30 * 60 * 1000;

/**
 * Estimativa de temperatura de pista a partir do ar. Nenhum servico de
 * meteorologia mede asfalto (mesma nota do `PressaoAFrio.tsx`, bloco 16): o
 * que existe e o principio fisico de que o asfalto exposto ao sol aquece bem
 * acima do ar, e chuva colapsa essa diferenca porque a agua escoa o calor. Os
 * numeros (+10°C seco, +2°C molhado) sao regra de bolso de trackday, nao
 * medicao por pista: por isso a margem e larga e o resultado sai marcado como
 * estimativa, nunca como leitura.
 */
function estimarTempPista(
  arC: number,
  condicao: string | null,
): { valorC: number; offsetC: number; margemC: number; molhada: boolean } {
  const molhada = condicao != null && /chuva|garoa|pancada|trovoada/i.test(condicao);
  const offsetC = molhada ? 2 : 10;
  const margemC = molhada ? 4 : 12;
  return { valorC: arC + offsetC, offsetC, margemC, molhada };
}

/**
 * PATCH direto de `/api/baterias/:id`, so pros dois campos de combustivel.
 * Ver nota da Fase 11 no topo do arquivo: isso deveria ser um wrapper em
 * `services/operacao.ts`, mas esse arquivo esta fora do escopo desta sessao
 * e a funcao ainda nao existe la.
 */

export function ContextoDaBateria({ aberta, dono, alvoId, layoutId, onFechar }: {
  aberta: boolean;
  dono: Dono;
  alvoId: string;
  layoutId: string | null;
  onFechar: () => void;
}) {
  const { dado: historico, carregando, erro, recarregar } = useRequisicao(
    () => historicoContexto(dono, alvoId),
    [dono, alvoId],
    aberta,
  );
  const atual: RegistroContexto | null = historico && historico.length > 0 ? historico[0] : null;

  // Heranca entre baterias (pedido de 29/08): com 4 baterias ha 4 contextos,
  // e o da bateria N nasce do da N-1, o piloto so altera o que mudou. Quando
  // ESTA bateria ainda nao tem registro, o formulario pre-preenche com o
  // ultimo contexto da bateria ANTERIOR da mesma sessao (pneu, composto,
  // voltas, notas de engenheiro). Nada e salvo sozinho: continua sendo um
  // registro que o piloto confirma.
  const { sessaoId } = useSelecao();
  const irmas = useBaterias(dono === "baterias" ? sessaoId : null);
  const anteriorId = (() => {
    if (dono !== "baterias" || !irmas.dado) return null;
    const ordenadas = [...irmas.dado].sort((x, y) =>
      String(x.went_out_at ?? x.created_at).localeCompare(String(y.went_out_at ?? y.created_at)),
    );
    const pos = ordenadas.findIndex((b) => b.id === alvoId);
    return pos > 0 ? ordenadas[pos - 1].id : null;
  })();
  const semRegistro = historico != null && historico.length === 0;
  const { dado: historicoAnterior } = useRequisicao(
    () => historicoContexto("baterias", anteriorId as string),
    [anteriorId],
    aberta && semRegistro && anteriorId !== null,
  );
  const herdado: RegistroContexto | null =
    semRegistro && historicoAnterior && historicoAnterior.length > 0 ? historicoAnterior[0] : null;

  // Fase 5: relogio que reavalia a idade do registro mais recente enquanto a
  // gaveta fica aberta. So um `Date.now()` no render nao bastava: o piloto
  // pode deixar a gaveta aberta por cima do formulario, e o aviso tem que
  // aparecer sozinho quando o registro completa 30min, sem precisar de
  // acao pra "descobrir" isso. Para o timer quando fecha, pra nao gastar
  // relogio com painel escondido.
  const [agora, setAgora] = useState(() => Date.now());
  useEffect(() => {
    if (!aberta) return;
    setAgora(Date.now());
    const intervalo = setInterval(() => setAgora(Date.now()), 60 * 1000);
    return () => clearInterval(intervalo);
  }, [aberta]);
  const idadeRegistroMs = atual ? agora - new Date(atual.criado_em).getTime() : null;
  const registroEnvelhecido = idadeRegistroMs !== null && !Number.isNaN(idadeRegistroMs) && idadeRegistroMs > LIMITE_ATUALIZACAO_MS;

  // ficha de setup: so precisa da versao mais recente, pra pre-preencher os
  // dois campos novos e pra carregar o resto das chaves na hora de salvar
  // (ver nota da Fase 12 no topo do arquivo, o POST de setup e um snapshot
  // completo, nao um patch).
  const { dado: versoesFicha, recarregar: recarregarSetup } = useRequisicao(
    () => versoesSetup(dono, alvoId),
    [dono, alvoId],
    aberta,
  );
  const setupAtual: VersaoSetup | undefined = versoesFicha
    ? [...versoesFicha].sort((a, b) => b.versao - a.versao)[0]
    : undefined;

  // clima so busca com a gaveta aberta e pista conhecida: gaveta fechada nao
  // precisa do dado, e sem layoutId a chamada nem faz sentido (o backend
  // devolveria 422 de qualquer forma). Reembala 422/502 do mesmo jeito que o
  // `TempoComPrevisao.tsx` (bloco 17) ja faz, pra distinguir "pista sem
  // coordenada" de "fonte de meteorologia fora do ar" sem tocar em
  // `requisicao.ts`.
  const {
    dado: clima,
    erro: erroClima,
    recarregar: recarregarClima,
  } = useRequisicao(
    () =>
      climaDoLayout(layoutId as string).catch((e: unknown) => {
        if (e instanceof ErroDaApi && e.status === 422) throw new ErroDaApi(422, e.detalhe, "SEM_COORDENADA");
        if (e instanceof ErroDaApi && e.status === 502) throw new ErroDaApi(502, e.detalhe, "FONTE_INDISPONIVEL");
        throw e;
      }),
    [layoutId],
    aberta && layoutId !== null,
  );
  const climaSemCoordenada = layoutId === null || erroClima === "SEM_COORDENADA";
  const climaFonteIndisponivel = erroClima === "FONTE_INDISPONIVEL";
  const climaOutroErro = erroClima !== null && !climaSemCoordenada && !climaFonteIndisponivel;

  // formulario de captura: comeca sempre vazio (pneu, composto, notas...).
  // Nao pre-preenche com o valor do registro anterior, senao vira "correcao"
  // do fato antigo em vez de um fato novo, o que quebra o append-only.
  //
  // Temperatura do ar, vento e horario sao a excecao: eles nao vem do
  // registro anterior, vem de fonte externa ao contexto (a API de tempo e o
  // relogio), entao pre-preencher nao cria a confusao "isso e o registro de
  // 9h de novo". Ar e vento tem um par de estado cada: o valor mostrado, e
  // se o piloto ja digitou por cima (`*Tocado`). Enquanto nao tocado, o
  // valor segue a fonte automatica; a partir do primeiro toque, vira dado do
  // usuario e a fonte automatica para de escrever nele.
  const [pneuEstado, setPneuEstado] = useState<"" | "novo" | "usado">("");
  const [voltasRodadas, setVoltasRodadas] = useState("");
  const [composto, setComposto] = useState("");
  const [tempAr, setTempAr] = useState("");
  const [tempArTocado, setTempArTocado] = useState(false);
  const [tempPista, setTempPista] = useState("");
  const [tempPistaTocado, setTempPistaTocado] = useState(false);
  const [vento, setVento] = useState("");
  const [ventoTocado, setVentoTocado] = useState(false);
  const [horario, setHorario] = useState(() => horarioAgora());
  const [notasPiloto, setNotasPiloto] = useState("");
  const [notasEngenheiro, setNotasEngenheiro] = useState("");
  // litros na saida e na volta (fuel_in_l/fuel_out_l da bateria). So fazem
  // sentido com bateria em escopo: gravacao solta nao tem onde guardar (ver
  // nota da Fase 11).
  const [litrosSaida, setLitrosSaida] = useState("");
  const [litrosVolta, setLitrosVolta] = useState("");
  // pressao-alvo a quente e carcaca medida: ao contrario do pneu, aqui NAO e
  // append-only na cara, e edicao de ficha de setup (mesma logica da
  // `FichaDeSetup.tsx`), entao pre-preenche com o valor mais recente em vez
  // de comecar vazio.
  const [pressaoAlvoQuente, setPressaoAlvoQuente] = useState("");
  const [carcacaMedida, setCarcacaMedida] = useState("");
  const [salvando, setSalvando] = useState(false);
  // correcao de registro existente (pedido de 29/08): o formulario de captura
  // vira formulario de correcao daquele registro, e salvar faz PATCH nele.
  const [editandoId, setEditandoId] = useState<string | null>(null);
  // exclusao em dois cliques, sem modal em cima de modal
  const [confirmandoId, setConfirmandoId] = useState<string | null>(null);
  const [erroSalvar, setErroSalvar] = useState<string | null>(null);
  const [erroCombustivel, setErroCombustivel] = useState<string | null>(null);
  const [erroSetup, setErroSetup] = useState<string | null>(null);

  // heranca: quando o formulario esta intocado e chegou contexto da bateria
  // anterior, ele vira o ponto de partida (o piloto so altera o que mudou)
  useEffect(() => {
    if (!herdado) return;
    if (pneuEstado === "" && (herdado.pneu_estado === "novo" || herdado.pneu_estado === "usado")) {
      setPneuEstado(herdado.pneu_estado);
    }
    if (composto === "" && herdado.pneu_composto) setComposto(herdado.pneu_composto);
    if (voltasRodadas === "" && herdado.pneu_voltas_rodadas != null) {
      setVoltasRodadas(String(herdado.pneu_voltas_rodadas));
    }
    if (notasEngenheiro === "" && herdado.notas_engenheiro) setNotasEngenheiro(herdado.notas_engenheiro);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [herdado]);

  // clima chegou (ou mudou) e o piloto ainda nao mexeu no campo: preenche
  // automatico. Roda de novo quando `*Tocado` volta a false (depois de
  // salvar, ver `limparFormulario`), o que reaplica o ultimo clima
  // conhecido no proximo registro sem precisar de nova chamada.
  useEffect(() => {
    if (!clima) return;
    if (!tempArTocado) setTempAr(clima.temperatura_atual_c.toFixed(1));
    if (!ventoTocado) setVento(clima.vento_kmh != null ? clima.vento_kmh.toFixed(0) : "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clima, tempArTocado, ventoTocado]);

  // estimativa de pista: recalcula toda vez que a temperatura do ar muda
  // (auto ou digitada), a menos que o piloto ja tenha escrito um numero de
  // pista com a mao (aí e leitura dele, nao vamos por cima).
  const arNum = tempAr.trim() === "" ? null : Number(tempAr);
  const estimativaPista =
    arNum !== null && isFinite(arNum) ? estimarTempPista(arNum, clima?.condicao_atual ?? null) : null;
  useEffect(() => {
    if (tempPistaTocado) return;
    setTempPista(estimativaPista ? estimativaPista.valorC.toFixed(0) : "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [estimativaPista?.valorC, tempPistaTocado]);

  // pre-preenche os dois campos de setup com a versao mais recente sempre
  // que ela chega ou muda (primeira carga, ou apos salvar e o `recarregar`
  // trazer a versao nova). Chave ausente (nunca cadastrada) fica vazia, nao
  // vira zero por default.
  useEffect(() => {
    const valores = setupAtual?.valores ?? {};
    const quente = valores.pressao_alvo_quente_psi;
    const carcaca = valores.carcaca_c;
    setPressaoAlvoQuente(quente != null ? String(quente) : "");
    setCarcacaMedida(carcaca != null ? String(carcaca) : "");
  }, [setupAtual]);

  const corrigirRegistro = (r: RegistroContexto) => {
    setEditandoId(r.id);
    setPneuEstado((r.pneu_estado as "" | "novo" | "usado" | null) ?? "");
    setVoltasRodadas(r.pneu_voltas_rodadas != null ? String(r.pneu_voltas_rodadas) : "");
    setComposto(r.pneu_composto ?? "");
    setTempAr(r.temp_ar_c != null ? String(r.temp_ar_c) : "");
    setTempArTocado(true);
    setTempPista(r.temp_pista_c != null ? String(r.temp_pista_c) : "");
    setTempPistaTocado(true);
    setVento(r.vento_kmh != null ? String(r.vento_kmh) : "");
    setVentoTocado(true);
    setHorario(r.horario ? new Date(r.horario).toTimeString().slice(0, 5) : horarioAgora());
    setNotasPiloto(r.notas_piloto ?? "");
    setNotasEngenheiro(r.notas_engenheiro ?? "");
  };

  const apagarRegistro = async (id: string) => {
    try {
      await excluirContexto(id);
      setConfirmandoId(null);
      if (editandoId === id) setEditandoId(null);
      recarregar();
    } catch (e: unknown) {
      setErroSalvar(e instanceof Error ? e.message : "não consegui excluir o registro");
    }
  };

  const limparFormulario = () => {
    setEditandoId(null);
    setPneuEstado("");
    setVoltasRodadas("");
    setComposto("");
    setTempAr("");
    setTempArTocado(false);
    setTempPista("");
    setTempPistaTocado(false);
    setVento("");
    setVentoTocado(false);
    setHorario(horarioAgora());
    setNotasPiloto("");
    setNotasEngenheiro("");
    setLitrosSaida("");
    setLitrosVolta("");
  };

  const salvar = async () => {
    // pneu so entra na captura se o piloto marcou o estado; sem isso nao ha
    // como distinguir "pneu novo" de "ninguem preencheu"
    const pneuPreenchido = pneuEstado !== "";
    const captura: Omit<CapturaContextoSessao, "dono"> = {
      pneu: pneuPreenchido
        ? {
            estado: pneuEstado,
            voltas_rodadas: voltasRodadas.trim() === "" ? null : Number(voltasRodadas),
            composto: composto.trim() === "" ? null : composto.trim(),
          }
        : null,
      temperatura_ar_c: tempAr.trim() === "" ? null : Number(tempAr),
      temperatura_pista_c: tempPista.trim() === "" ? null : Number(tempPista),
      vento_kmh: vento.trim() === "" ? null : Number(vento),
      horario: horario.trim() === "" ? null : horario.trim(),
      notas_piloto: notasPiloto.trim() === "" ? null : notasPiloto.trim(),
      notas_engenheiro: notasEngenheiro.trim() === "" ? null : notasEngenheiro.trim(),
      contexto_anterior_em: atual?.criado_em ?? null,
    };

    setSalvando(true);
    setErroSalvar(null);
    setErroCombustivel(null);
    setErroSetup(null);

    // Corrigindo um registro existente: PATCH nele e pronto. Combustivel e
    // setup NAO entram no ramo de correcao de proposito: a correcao mira o
    // registro errado, nao redispara as escritas laterais.
    if (editandoId) {
      try {
        await editarContexto(editandoId, captura);
      } catch (e: unknown) {
        setSalvando(false);
        setErroSalvar(e instanceof Error ? e.message : "falha ao corrigir o registro");
        return;
      }
      setSalvando(false);
      limparFormulario();
      recarregar();
      return;
    }

    try {
      await registrarContexto(dono, alvoId, captura);
    } catch (e: unknown) {
      setSalvando(false);
      setErroSalvar(e instanceof Error ? e.message : "falha ao registrar contexto");
      return;
    }

    // combustivel so tem onde persistir com bateria em escopo (a tabela
    // `gravacao` nao tem essas colunas). So manda o que foi preenchido: campo
    // vazio nao vira PATCH nenhum, pra nao sobrescrever com null um valor que
    // ja estava salvo de um registro anterior.
    if (dono === "baterias") {
      // fuel_OUT e o tanque na SAIDA pra pista e fuel_IN e na volta ao box
      // (mesma semantica do formulario de editar bateria). Estava invertido
      // ate 29/08, e o consumo informado saia negativo ou nao "computava".
      const camposCombustivel: { fuel_in_l?: number; fuel_out_l?: number } = {};
      if (litrosSaida.trim() !== "") camposCombustivel.fuel_out_l = Number(litrosSaida);
      if (litrosVolta.trim() !== "") camposCombustivel.fuel_in_l = Number(litrosVolta);
      if (Object.keys(camposCombustivel).length > 0) {
        try {
          await editarBateria(alvoId, camposCombustivel);
        } catch (e: unknown) {
          // o contexto ja salvou: nao desfaz, so avisa que o combustivel
          // falhou separado, pra nao passar a impressao de que nada foi
          // registrado.
          setSalvando(false);
          setErroCombustivel(
            e instanceof Error ? e.message : "contexto salvo, mas o combustível não",
          );
          limparFormulario();
          recarregar();
          return;
        }
      }
    }

    // ficha de setup: so entra na jogada se pressao-alvo ou carcaca foi
    // preenchida. `salvarSetup` grava um snapshot inteiro, entao a base e o
    // que ja existia (pra nao apagar chaves da Ficha de Setup) com essas
    // duas sobrescritas por cima.
    const setupTocado = pressaoAlvoQuente.trim() !== "" || carcacaMedida.trim() !== "";
    if (setupTocado) {
      const valores: Record<string, string | number> = { ...(setupAtual?.valores ?? {}) };
      if (pressaoAlvoQuente.trim() !== "") valores.pressao_alvo_quente_psi = Number(pressaoAlvoQuente);
      if (carcacaMedida.trim() !== "") valores.carcaca_c = Number(carcacaMedida);
      try {
        await salvarSetup(dono, alvoId, valores);
      } catch (e: unknown) {
        // contexto (e combustivel, se aplicavel) ja salvaram: mesma logica
        // do erro de combustivel acima, avisa separado em vez de sugerir
        // que nada foi registrado.
        setSalvando(false);
        setErroSetup(e instanceof Error ? e.message : "contexto salvo, mas a pressão/carcaça não");
        limparFormulario();
        recarregar();
        recarregarSetup();
        return;
      }
    }

    setSalvando(false);
    limparFormulario();
    recarregar();
    recarregarSetup();
  };

  return (
    <Gaveta aberta={aberta} titulo="Contexto do outing" eyebrow="Captura · bloco 15" onFechar={onFechar}>
      {carregando && <p className="nota">Carregando contexto...</p>}
      {erro && <p className="nota erro-txt">Falha ao carregar: {erro}</p>}

      {!carregando && !erro && (
        <>
          {!atual && (
            <div className="deg">
              <span className="ico">!</span>
              <p>Ainda não há nenhum registro de contexto para esta bateria. O primeiro fica abaixo.</p>
            </div>
          )}

          {atual && (
            <div className="grupo">
              <h5>Registro mais recente ({new Date(atual.criado_em).toLocaleString("pt-BR")})</h5>

              {/* Fase 5: convite, nunca gravacao automatica. Contexto e
                  declaracao de quem estava la; inventar um registro novo
                  sozinho seria falsificar historico. So avisa que envelheceu
                  e aponta pro formulario logo abaixo. */}
              {registroEnvelhecido && idadeRegistroMs !== null && (
                <div className="deg-inline" style={{ marginBottom: "var(--s3)" }}>
                  <span className="ico">!</span>
                  <p className="nota">
                    Último registro foi há <b>{formatarIdade(idadeRegistroMs)}</b>. Mudou temperatura, vento ou
                    pneu? Registre de novo no formulário abaixo, o histórico não corrige, só acumula.
                  </p>
                </div>
              )}

              {campoLeitura("Composto", atual.pneu_composto)}
              {campoLeitura("Estado do pneu", atual.pneu_estado)}
              {campoLeitura("Voltas rodadas", atual.pneu_voltas_rodadas)}
              {campoLeitura("Temp. do ar", atual.temp_ar_c, " °C")}
              {campoLeitura("Temp. da pista", atual.temp_pista_c, " °C")}
              {campoLeitura("Vento", atual.vento_kmh, " km/h")}
              {campoLeitura("Horário", atual.horario)}
              {campoLeitura("Notas do piloto", atual.notas_piloto)}
              {campoLeitura("Notas do engenheiro", atual.notas_engenheiro)}
            </div>
          )}

          <div className="grupo">
            <h5>Novo registro</h5>
            <p className="nota">
              Contexto é <b>append-only</b>: temperatura às 9h e às 14h são dois fatos, não uma
              correção um do outro. Salvar aqui adiciona um registro novo, não altera o de cima.
            </p>

            {climaSemCoordenada && (
              <p className="nota">
                Temperatura do ar e vento não vêm automáticos:{" "}
                {layoutId === null
                  ? "essa bateria ainda não tem pista/layout definido."
                  : "essa pista não tem coordenada de referência no catálogo."}{" "}
                Preencha à mão.
              </p>
            )}
            {climaFonteIndisponivel && (
              <p className="nota">
                A fonte de meteorologia não respondeu agora, por isso temperatura do ar e vento não
                vieram automáticos.{" "}
                <button type="button" className="btn-secundario" onClick={recarregarClima}>tentar de novo</button>
              </p>
            )}
            {climaOutroErro && (
              <p className="nota erro-txt">
                Falha ao buscar o clima ({erroClima}). Temperatura do ar e vento ficam à mão até
                resolver.
              </p>
            )}

            <div className={`campo destaque ${pneuEstado ? "ok" : "falta"}`}>
              <label>Estado do pneu</label>
              <select value={pneuEstado} onChange={(e) => setPneuEstado(e.target.value as "" | "novo" | "usado")}>
                <option value="">o sistema perguntou</option>
                <option value="novo">novo</option>
                <option value="usado">usado</option>
              </select>
            </div>
            <div className={`campo destaque ${composto.trim() ? "ok" : "falta"}`}>
              <label>Composto</label>
              <input value={composto} placeholder="o sistema perguntou" onChange={(e) => setComposto(e.target.value)} />
            </div>
            <div className={`campo destaque ${voltasRodadas.trim() ? "ok" : "falta"}`}>
              <label>Voltas rodadas</label>
              <input
                type="number"
                value={voltasRodadas}
                placeholder="o sistema perguntou"
                onChange={(e) => setVoltasRodadas(e.target.value)}
              />
            </div>

            {/* auto enquanto ninguem mexeu (verde, rotulo "auto" vem do
                app.css); no primeiro toque perde o auto e vira destaque
                comum, como qualquer campo que o piloto preenche. */}
            <div className={`campo ${tempArTocado ? "destaque" : "auto"} ${tempAr.trim() ? "ok" : "falta"}`}>
              <label>Temp. do ar (°C)</label>
              <input
                type="number"
                value={tempAr}
                placeholder="o sistema perguntou"
                onChange={(e) => {
                  setTempArTocado(true);
                  setTempAr(e.target.value);
                }}
              />
            </div>

            <div className={`campo destaque ${tempPista.trim() ? "ok" : "falta"}`}>
              <label>
                Temp. da pista (°C)
                {!tempPistaTocado && tempPista.trim() !== "" && (
                  <span className="pill pill-warn" style={{ marginLeft: 6 }}>estimativa</span>
                )}
              </label>
              <input
                type="number"
                value={tempPista}
                placeholder="o sistema perguntou"
                onChange={(e) => {
                  setTempPistaTocado(true);
                  setTempPista(e.target.value);
                }}
              />
            </div>
            {estimativaPista && (
              <p className="nota mono" style={{ fontSize: 11 }}>
                Estimativa: T_pista ≈ T_ar + {estimativaPista.offsetC}°C (
                {estimativaPista.molhada
                  ? "pista molhada, a chuva encosta a temperatura na do ar"
                  : "pista seca, o sol aquece o asfalto acima do ar"}
                ), margem ±{estimativaPista.margemC}°C. Nenhuma fonte de meteorologia mede asfalto: isso é
                regra de bolso de trackday, não leitura. Ajuste pelo pirômetro se tiver.
              </p>
            )}

            {/* mesma logica do ar: auto ate o piloto tocar */}
            <div className={`campo ${ventoTocado ? "destaque" : "auto"} ${vento.trim() ? "ok" : "falta"}`}>
              <label>Vento (km/h)</label>
              <input
                type="number"
                value={vento}
                placeholder="o sistema perguntou"
                onChange={(e) => {
                  setVentoTocado(true);
                  setVento(e.target.value);
                }}
              />
            </div>

            <div className={`campo destaque ${horario.trim() ? "ok" : "falta"}`}>
              <label>Horário</label>
              <input value={horario} placeholder="o sistema perguntou" onChange={(e) => setHorario(e.target.value)} />
            </div>
            <div className={`campo destaque ${notasPiloto.trim() ? "ok" : "falta"}`}>
              <label>Notas do piloto</label>
              <textarea value={notasPiloto} placeholder="o sistema perguntou" onChange={(e) => setNotasPiloto(e.target.value)} />
            </div>
            <div className={`campo destaque ${notasEngenheiro.trim() ? "ok" : "falta"}`}>
              <label>Notas do engenheiro</label>
              <textarea value={notasEngenheiro} placeholder="o sistema perguntou" onChange={(e) => setNotasEngenheiro(e.target.value)} />
            </div>

            {/* pressao-alvo a quente e carcaca medida: cadastro migrou pra
                ca (Fase 12), o Box (`PressaoAFrio.tsx`, bloco 16) virou so
                leitura. Nao vao no POST de contexto acima, vao pra ficha de
                setup por baixo dos panos (ver nota da Fase 12 no topo do
                arquivo); por isso ficam marcadas "falta" so visualmente,
                igual notas/litros, sem travar o registro de contexto se
                ficarem vazias. */}
            <div className={`campo destaque ${pressaoAlvoQuente.trim() ? "ok" : "falta"}`}>
              <label>Pressão-alvo a quente (psi)</label>
              <input
                type="number"
                step="0.5"
                value={pressaoAlvoQuente}
                placeholder="o sistema perguntou"
                onChange={(e) => setPressaoAlvoQuente(e.target.value)}
              />
            </div>
            <div className={`campo destaque ${carcacaMedida.trim() ? "ok" : "falta"}`}>
              <label>Carcaça medida (°C)</label>
              <input
                type="number"
                step="1"
                value={carcacaMedida}
                placeholder="vazio = Box estima"
                onChange={(e) => setCarcacaMedida(e.target.value)}
              />
            </div>
            {erroSetup && <p className="nota erro-txt">{erroSetup}</p>}

            {/* combustivel: cadastro migrou pra ca (Fase 11), Box virou so
                leitura. Sem bateria em escopo nao ha onde guardar (a
                gravacao solta nao tem fuel_in_l/fuel_out_l), entao os campos
                ficam desabilitados com o motivo em vez de aceitar e perder o
                numero em silencio. */}
            {dono !== "baterias" && (
              <p className="nota">
                Sem bateria, não há onde guardar o combustível: os campos abaixo ficam desabilitados
                nesta gravação solta.
              </p>
            )}
            <div className={`campo destaque ${litrosSaida.trim() ? "ok" : "falta"}`}>
              <label>Litros na saída</label>
              <input
                type="number"
                step="0.1"
                value={litrosSaida}
                disabled={dono !== "baterias"}
                placeholder={dono === "baterias" ? "o sistema perguntou" : "sem bateria em escopo"}
                onChange={(e) => setLitrosSaida(e.target.value)}
              />
            </div>
            <div className={`campo destaque ${litrosVolta.trim() ? "ok" : "falta"}`}>
              <label>Litros na volta</label>
              <input
                type="number"
                step="0.1"
                value={litrosVolta}
                disabled={dono !== "baterias"}
                placeholder={dono === "baterias" ? "o sistema perguntou" : "sem bateria em escopo"}
                onChange={(e) => setLitrosVolta(e.target.value)}
              />
            </div>
            {erroCombustivel && <p className="nota erro-txt">{erroCombustivel}</p>}

            {erroSalvar && <p className="nota erro-txt">{erroSalvar}</p>}

            <button type="button" className="btn-primario" onClick={() => void salvar()} disabled={salvando}>
              {salvando ? "Salvando..." : editandoId ? "Salvar correção" : "Registrar contexto"}
            </button>
            {editandoId && (
              <button type="button" className="btn-secundario" onClick={limparFormulario}>
                Cancelar correção (voltar a registrar novo)
              </button>
            )}
          </div>

          {historico && historico.length > 0 && (
            <div className="grupo">
              <h5>Histórico ({historico.length} registro{historico.length > 1 ? "s" : ""})</h5>
              {historico.map((r) => (
                <div className={`historico-item${editandoId === r.id ? " em-correcao" : ""}`} key={r.id}>
                  <div className="versao-anterior-cab">
                    <span className="versao-data">{new Date(r.criado_em).toLocaleString("pt-BR")}</span>
                    <span className="hist-acoes">
                      <button type="button" className="mini-acao" onClick={() => corrigirRegistro(r)}>
                        {editandoId === r.id ? "corrigindo..." : "corrigir"}
                      </button>
                      {confirmandoId === r.id ? (
                        <>
                          <button type="button" className="mini-acao perigo" onClick={() => void apagarRegistro(r.id)}>
                            confirmar exclusão
                          </button>
                          <button type="button" className="mini-acao" onClick={() => setConfirmandoId(null)}>
                            manter
                          </button>
                        </>
                      ) : (
                        <button type="button" className="mini-acao perigo" onClick={() => setConfirmandoId(r.id)}>
                          excluir
                        </button>
                      )}
                    </span>
                  </div>
                  <div className="grupo">
                    <div className="kv"><span className="k">Pneu</span><span className="v">{r.pneu_estado ?? "?"} · {r.pneu_composto ?? "?"} · {r.pneu_voltas_rodadas ?? "?"} voltas</span></div>
                    <div className="kv"><span className="k">Ar / pista / vento</span><span className="v">{r.temp_ar_c ?? "?"}°C / {r.temp_pista_c ?? "?"}°C / {r.vento_kmh ?? "?"}km/h</span></div>
                    {r.notas_piloto && <div className="kv"><span className="k">Piloto</span><span className="v">{r.notas_piloto}</span></div>}
                    {r.notas_engenheiro && <div className="kv"><span className="k">Engenheiro</span><span className="v">{r.notas_engenheiro}</span></div>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </Gaveta>
  );
}
