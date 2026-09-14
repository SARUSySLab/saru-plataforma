import { useSelecao } from "../state/selection";
import { useSessao } from "../sessao/useSessao";
import { SeletorDeTema } from "../tema/SeletorDeTema";
import { Marca } from "./Marca";
import { MarcaLA } from "./MarcaLA";
import { Icone } from "./Icone";
import { PAGINAS } from "./paginas";

// O navegador do funil. Cada pagina responde UMA pergunta, e a ordem e a das
// tres que o engenheiro nomeou: onde perdi, se estou melhorando, quanto
// gastei. Contexto e ficha de setup moram no Dia de pista (sao por bateria)
// e nas gavetas; o antigo Box virou o nome do painel-resumo (29/08).

/**
 * `temDado` e falso quando nao ha gravacao analisavel aberta.
 *
 * Nesse estado o funil inteiro, o Sarue e as gavetas nao tem sobre o que
 * falar: o funil le o relatorio, o Sarue le a base de fatos que sai dele e
 * as gavetas penduram na bateria ou na gravacao.
 * Eles continuam VISIVEIS, desabilitados e com o motivo no title, em vez de
 * sumirem: menu que muda de tamanho conforme o estado faz o usuario procurar
 * um item que ele jura que existia. O que some e a promessa de que clicar
 * funciona, nao o item.
 */
export function Rail({ temDado, onRecolher }: {
  temDado: boolean;
  onRecolher: () => void;
}) {
  const { vista, irPara } = useSelecao();
  const atual = vista.tipo === "pagina" ? vista.id : null;
  const semDado = "Envie uma telemetria para habilitar";

  return (
    <aside className="rail">
      <div className="rail-head">
        {/* A arte tem duas variantes, e a escolha e por CONTRASTE, nao por
            gosto: a preta some no fundo escuro e a clara some no claro. Segue
            o tema efetivo, entao troca junto quando o sistema muda no meio da
            sessao, sem precisar recarregar. */}
        {/* A variante escolhida pelo Lucas (mascote colorido, palavra em
            branco) e a do TEMA ESCURO. No claro ela some, porque a palavra e
            branca sobre fundo quase branco, entao no claro entra a irma de
            traco preto. A troca e por contraste, nao por gosto. */}
        {/* Escolha do Lucas: no tema CLARO entra a arte COM o fundo preto dela
            (`saru-logo-fundo.png`), porque esse fundo e parte do desenho e e
            justamente o que da contraste sobre a interface clara. No escuro
            entra a mesma arte recortada com transparencia, que funde com o
            painel. A variante de traco preto nao e usada em nenhum dos dois. */}
        {/* A marca leva pra visao geral: e a convencao de todo app, e aqui
            resolve o caso concreto de estar tres niveis dentro do funil e
            querer voltar ao veredito sem caçar o item no menu. */}
        <button
          type="button"
          className="marca-home"
          onClick={() => irPara({ tipo: "geral" })}
          title="Voltar para a visão geral"
        >
          <Marca
            claro="/saru-logo-claro-v2.svg"
            escuro="/saru-logo.png"
            alt="SARU"
            className="marca-logo"
          />
        </button>
        <button type="button" className="rail-toggle" onClick={onRecolher} aria-label="Recolher painel">
          &lsaquo;&lsaquo;
        </button>
      </div>

      {/* Dia de pista PRIMEIRO e destacado (pedido de 29/08): e a primeira
          coisa que o usuario configura, e o envio de telemetria mora dentro
          dele (o item proprio de envio saiu da sidebar pelo mesmo motivo). */}
      <nav className="niveis" aria-label="Operação do dia">
        <button type="button" className="nivel destaque" aria-current={vista.tipo === "ciclo"} onClick={() => irPara({ tipo: "ciclo" })}>
          <span className="n"><Icone nome="calendario" /></span>
          <span><span className="t">Dia de pista</span><span className="q">Evento, sessão, saída pra pista e envio</span></span>
        </button>
        {/* Campeonato NAO depende de telemetria da conta: le a cronometragem
            externa (live timing do autodromo). Fica habilitado sempre, mesmo
            sem gravacao nenhuma, porque a fonte dele e outra. */}
        <button type="button" className="nivel destaque" aria-current={vista.tipo === "campeonato"} onClick={() => irPara({ tipo: "campeonato" })}>
          <span className="n"><Icone nome="bandeira" /></span>
          <span><span className="t">Campeonato</span><span className="q">Grid ao vivo, mapa e clima</span></span>
        </button>
      </nav>

      <nav className="niveis" aria-label="Níveis do funil">
        {/* "Box" e o nome da casa pro painel-resumo (pedido de 29/08): e a
            tela que se olha do box entre baterias. O subtitulo diz o que ela
            e pra quem chega agora. */}
        <button type="button" className="nivel" disabled={!temDado} title={temDado ? undefined : semDado} aria-current={vista.tipo === "geral"} onClick={() => irPara({ tipo: "geral" })}>
          <span className="n"><Icone nome="grade" /></span>
          <span><span className="t">Box</span><span className="q">Visão geral</span></span>
        </button>
        {PAGINAS.map((p) => (
          <button key={p.id} type="button" className="nivel" disabled={!temDado} title={temDado ? undefined : semDado} aria-current={atual === p.id} onClick={() => irPara({ tipo: "pagina", id: p.id })}>
            <span className="n"><Icone nome={p.icone} /></span>
            <span><span className="t">{p.titulo}</span><span className="q">{p.pergunta}</span></span>
          </button>
        ))}
      </nav>

      <Rodape />
    </aside>
  );
}

/**
 * Rodape de marca. A versao sai do `package.json` via `define` do Vite
 * (`vite.config.ts`), nao de uma string escrita a mao aqui: versao repetida em
 * dois lugares e versao que desencontra no primeiro release.
 */
function Rodape() {
  const { usuario, sair } = useSessao();
  return (
    <footer className="rail-rodape">
      {/* Quem esta logado fica ao lado do botao de sair, e nao numa tela de
          perfil: a pergunta "estou na conta certa?" so aparece na hora de
          sair, e ai a resposta tem que estar do lado. */}
      {/* duas linhas ao todo (29/08, sem scroll): tema, nome e sair numa
          linha; assinatura na de baixo */}
      <div className="rail-linha">
        <SeletorDeTema />
        {usuario && (
          <div className="rail-conta">
            <span className="quem">{usuario.nome || usuario.email}</span>
            <button type="button" className="sair" onClick={() => sair()}>
              Sair
            </button>
          </div>
        )}
      </div>
      {/* uma linha so, miuda: assinatura e rodape, nao conteudo (29/08) */}
      <span className="assinatura">
        <span className="powered">powered by</span> <MarcaLA /> <span className="versao">v{__VERSAO__}</span>
      </span>
    </footer>
  );
}
