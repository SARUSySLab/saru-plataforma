import { useEffect, useState } from "react";
import { useRequisicao } from "../dados/requisicao";
import { editarSetup, excluirSetup, salvarSetup, versoesSetup, type Dono, type VersaoSetup } from "../services/operacao";
import { Gaveta } from "./Gaveta";
import "../estilo/gavetas.css";

// Bloco 13. Contexto, nao nivel: nao responde "como foi", responde "com o
// que". Gaveta acessivel de qualquer nivel, nunca no fluxo vertical, senao
// empurra o sinal para baixo da dobra.
//
// Fase 4: virou leitura E escrita reais. `valores` e Record<string,
// string|number> livre de proposito (o formato da ficha ainda nao fechou), e
// isso vira a UI de editor de pares chave/valor em vez de formulario fixo.
// Salvar SEMPRE cria versao nova (services/operacao.ts ja documenta isso na
// API): nao existe PUT que sobrescreve, entao a tela precisa deixar isso
// visivel, senao o usuario acha que perdeu a versao anterior.

/** Um par chave/valor em edicao. `id` e so pra o React ter key estavel
 * enquanto a chave em si ainda esta sendo digitada (pode ficar vazia ou
 * duplicada no meio da edicao). */
interface Par {
  id: number;
  chave: string;
  valor: string;
}

function paresDeValores(valores: Record<string, string | number>): Par[] {
  let proximoId = 0;
  return Object.entries(valores).map(([chave, valor]) => ({
    id: proximoId++,
    chave,
    valor: String(valor),
  }));
}

/** Converte de volta pro formato livre da API. Chave vazia e descartada (nao
 * faz sentido salvar campo sem nome). Valor que parece numero vira numero;
 * o resto fica string. E heuristica, nao validacao: o formato ainda nao
 * fechou, entao nao ha "tipo certo" pra impor aqui. */
function valoresDePares(pares: Par[]): Record<string, string | number> {
  const out: Record<string, string | number> = {};
  for (const p of pares) {
    const chave = p.chave.trim();
    if (!chave) continue;
    const valorTrim = p.valor.trim();
    const ehNumero = valorTrim !== "" && !Number.isNaN(Number(valorTrim));
    out[chave] = ehNumero ? Number(valorTrim) : valorTrim;
  }
  return out;
}

export function FichaDeSetup({ aberta, dono, alvoId, onFechar }: {
  aberta: boolean;
  dono: Dono;
  alvoId: string;
  onFechar: () => void;
}) {
  const { dado: versoes, carregando, erro, recarregar } = useRequisicao(
    () => versoesSetup(dono, alvoId),
    [dono, alvoId],
    aberta,
  );

  const [pares, setPares] = useState<Par[]>([]);
  const [notas, setNotas] = useState("");
  const [salvando, setSalvando] = useState(false);
  const [erroSalvar, setErroSalvar] = useState<string | null>(null);
  // exclusao de versao em dois cliques, sem modal em cima de modal
  const [confirmandoId, setConfirmandoId] = useState<string | null>(null);
  const [contadorId, setContadorId] = useState(0);

  // ordena por versao desc: a API nao garante ordem, entao a tela nao confia
  // em posicao de array pra saber qual e "a mais recente"
  const ordenadas = [...(versoes ?? [])].sort((a, b) => b.versao - a.versao);
  const atual: VersaoSetup | undefined = ordenadas[0];
  const anteriores = ordenadas.slice(1);

  // repopula o formulario quando a busca traz dado novo (primeira carga ou
  // apos salvar). Nao roda a cada digitacao: so quando `versoes` muda de
  // referencia, que e o que useRequisicao troca ao completar um fetch.
  useEffect(() => {
    if (atual) {
      setPares(paresDeValores(atual.valores));
      setNotas(atual.notas ?? "");
    } else {
      setPares([]);
      setNotas("");
    }
    setErroSalvar(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [versoes]);

  /**
   * Campos sugeridos da ficha.
   *
   * A ficha e um `Record<string, string|number>` livre de proposito, porque o
   * formato dela ainda nao fechou (decisao de 29/08, JSONB versionado). O custo
   * disso e a folha em branco: quem abre pela primeira vez nao sabe o que
   * escrever, e cada um inventa a sua chave, o que impede comparar bateria com
   * bateria depois. As sugestoes resolvem os dois sem travar nada: sao um ponto
   * de partida clicavel, e quem quiser outra chave continua digitando a sua.
   *
   * A unidade vai no NOME da chave, nao no valor. `pressao_diant_psi` compara
   * entre baterias; "27 psi" no valor vira texto e nao compara com nada.
   */
  const SUGESTOES: { chave: string; exemplo: string; grupo: string }[] = [
    { chave: "pressao_diant_psi", exemplo: "27", grupo: "Pneu" },
    { chave: "pressao_tras_psi", exemplo: "26", grupo: "Pneu" },
    { chave: "composto", exemplo: "medio", grupo: "Pneu" },
    { chave: "camber_diant_graus", exemplo: "-2.5", grupo: "Suspensão" },
    { chave: "camber_tras_graus", exemplo: "-1.8", grupo: "Suspensão" },
    { chave: "convergencia_diant_mm", exemplo: "1.0", grupo: "Suspensão" },
    { chave: "altura_diant_mm", exemplo: "55", grupo: "Suspensão" },
    { chave: "altura_tras_mm", exemplo: "62", grupo: "Suspensão" },
    { chave: "mola_diant_nmm", exemplo: "80", grupo: "Suspensão" },
    { chave: "mola_tras_nmm", exemplo: "95", grupo: "Suspensão" },
    { chave: "barra_estab_diant", exemplo: "3", grupo: "Suspensão" },
    { chave: "asa_tras", exemplo: "4", grupo: "Aerodinâmica" },
    { chave: "splitter_diant", exemplo: "2", grupo: "Aerodinâmica" },
    { chave: "relacao_final", exemplo: "3.90", grupo: "Transmissão" },
    { chave: "diferencial_bloqueio", exemplo: "45", grupo: "Transmissão" },
    { chave: "freio_balanco_pct", exemplo: "54", grupo: "Freio" },
    { chave: "combustivel_saida_l", exemplo: "12", grupo: "Carro" },
    { chave: "lastro_kg", exemplo: "0", grupo: "Carro" },
  ];

  const usarSugestao = (chave: string, exemplo: string) => {
    // ja existe: nao duplica a chave, so leva o foco pra ela seria melhor mas
    // exigiria ref por linha; ignorar e o comportamento menos surpreendente
    if (pares.some((p) => p.chave === chave)) return;
    setContadorId((n) => n + 1);
    setPares((ps) => [...ps, { id: contadorId, chave, valor: exemplo }]);
  };

  const adicionarCampo = () => {
    setContadorId((n) => n + 1);
    setPares((ps) => [...ps, { id: contadorId, chave: "", valor: "" }]);
  };
  const removerCampo = (id: number) => setPares((ps) => ps.filter((p) => p.id !== id));
  const atualizarChave = (id: number, chave: string) =>
    setPares((ps) => ps.map((p) => (p.id === id ? { ...p, chave } : p)));
  const atualizarValor = (id: number, valor: string) =>
    setPares((ps) => ps.map((p) => (p.id === id ? { ...p, valor } : p)));

  const salvar = () => {
    setSalvando(true);
    setErroSalvar(null);
    salvarSetup(dono, alvoId, valoresDePares(pares), notas.trim() || undefined)
      .then(() => {
        setSalvando(false);
        recarregar();
      })
      .catch((e: unknown) => {
        setSalvando(false);
        setErroSalvar(e instanceof Error ? e.message : "falha ao salvar ficha de setup");
      });
  };

  /** Correcao em cima da versao atual, sem criar nova (pedido de 29/08):
   *  e pro dedo errado, a evolucao de setup continua criando versao. */
  const corrigir = () => {
    if (!atual) return;
    setSalvando(true);
    setErroSalvar(null);
    editarSetup(atual.id, valoresDePares(pares), notas.trim() || undefined)
      .then(() => {
        setSalvando(false);
        recarregar();
      })
      .catch((e: unknown) => {
        setSalvando(false);
        setErroSalvar(e instanceof Error ? e.message : "falha ao corrigir a versão");
      });
  };

  const apagarVersao = (id: string) => {
    setErroSalvar(null);
    excluirSetup(id)
      .then(() => {
        setConfirmandoId(null);
        recarregar();
      })
      .catch((e: unknown) => {
        setErroSalvar(e instanceof Error ? e.message : "não consegui excluir a versão");
      });
  };

  const botaoExcluirVersao = (id: string) =>
    confirmandoId === id ? (
      <>
        <button type="button" className="mini-acao perigo" onClick={() => apagarVersao(id)}>
          confirmar exclusão
        </button>
        <button type="button" className="mini-acao" onClick={() => setConfirmandoId(null)}>
          manter
        </button>
      </>
    ) : (
      <button type="button" className="mini-acao perigo" onClick={() => setConfirmandoId(id)}>
        excluir
      </button>
    );

  return (
    <Gaveta aberta={aberta} titulo="Ficha de setup" eyebrow="Contexto · bloco 13" onFechar={onFechar}>
      {carregando && <p className="nota">Carregando ficha...</p>}
      {erro && <p className="nota erro-txt">Falha ao carregar: {erro}</p>}

      {!carregando && !erro && (
        <>
          {!atual && <p className="nota">Ainda não há ficha de setup para esta bateria.</p>}

          <div className="grupo">
            <h5>
              {atual ? `Editando a partir da versão ${atual.versao}` : "Primeira versão"}
              {atual && <span className="hist-acoes">{botaoExcluirVersao(atual.id)}</span>}
            </h5>
            <p className="nota">
              Salvar <b>cria uma versão nova</b>, nunca sobrescreve a anterior: é o que sustenta
              comparar "o que mudou da bateria 2 pra 3".
            </p>

            <div className="pares-setup">
              {pares.length === 0 && <p className="nota">Nenhum campo ainda. Adicione um abaixo.</p>}
              {pares.map((p) => (
                <div className="par-setup" key={p.id}>
                  <input
                    className="par-chave"
                    value={p.chave}
                    placeholder="campo"
                    onChange={(e) => atualizarChave(p.id, e.target.value)}
                  />
                  <input
                    className="par-valor"
                    value={p.valor}
                    placeholder="valor"
                    onChange={(e) => atualizarValor(p.id, e.target.value)}
                  />
                  <button type="button" className="par-remover" onClick={() => removerCampo(p.id)} aria-label="Remover campo">
                    &#10005;
                  </button>
                </div>
              ))}
            </div>
            <button type="button" className="btn-secundario" onClick={adicionarCampo}>+ campo</button>

            {/* As sugestoes ficam DEPOIS do editor, nao antes: quem ja sabe o
                que quer digita direto, e quem nao sabe encontra a lista logo
                abaixo sem ela roubar a tela. */}
            <div className="sugestoes-setup">
              <p className="nota">
                Campos comuns. Clicar acrescenta com um valor de exemplo, que você troca.
                A unidade vai no nome da chave, para dar pra comparar bateria com bateria depois.
              </p>
              {[...new Set(SUGESTOES.map((s) => s.grupo))].map((grupo) => (
                <div key={grupo} className="sugestao-grupo">
                  <span className="eyebrow">{grupo}</span>
                  <div className="sugestao-chips">
                    {SUGESTOES.filter((s) => s.grupo === grupo).map((s) => (
                      <button
                        key={s.chave}
                        type="button"
                        className="chip"
                        disabled={pares.some((p) => p.chave === s.chave)}
                        title={`exemplo: ${s.exemplo}`}
                        onClick={() => usarSugestao(s.chave, s.exemplo)}
                      >
                        {s.chave}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grupo">
            <h5>Notas da versão</h5>
            <textarea
              className="notas-setup"
              value={notas}
              placeholder="o que mudou e por quê"
              onChange={(e) => setNotas(e.target.value)}
            />
          </div>

          {erroSalvar && <p className="nota erro-txt">{erroSalvar}</p>}

          <button type="button" className="btn-primario" onClick={salvar} disabled={salvando}>
            {salvando ? "Salvando..." : `Salvar como versão ${atual ? atual.versao + 1 : 1}`}
          </button>
          {atual && (
            <button type="button" className="btn-secundario" onClick={corrigir} disabled={salvando}>
              Corrigir a versão {atual.versao} (sem criar nova)
            </button>
          )}

          {anteriores.length > 0 && (
            <div className="grupo">
              <h5>Versões anteriores</h5>
              {anteriores.map((v) => (
                <div className="versao-anterior" key={v.id}>
                  <div className="versao-anterior-cab">
                    <span className="versao-tag">v{v.versao}</span>
                    <span className="versao-data">{new Date(v.criado_em).toLocaleString("pt-BR")}</span>
                    <span className="hist-acoes">{botaoExcluirVersao(v.id)}</span>
                  </div>
                  {v.notas && <p className="nota">{v.notas}</p>}
                  <div className="grupo">
                    {Object.entries(v.valores).map(([k, val]) => (
                      <div className="kv" key={k}>
                        <span className="k">{k}</span>
                        <span className="v">{val}</span>
                      </div>
                    ))}
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
