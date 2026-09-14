/**
 * Paginacao de formulario em passos, sem rolagem.
 *
 * Pedido do Lucas, repetido em 30/08: as modais de contexto e de configuracoes
 * do carro nao podem rolar. Elas sao preenchidas no box, de pe, com o carro
 * parado e pouco tempo; rolagem custa reencontrar onde parou. E a mesma regra
 * que o pit wall ao vivo ja adotou: o que nao couber nao entra, vai pra outro
 * passo.
 *
 * DETALHE QUE FAZ A COISA FUNCIONAR: o passo inativo continua MONTADO, so
 * escondido com `hidden`. Desmontar perderia o que ja foi digitado e, pior,
 * tiraria os campos do formulario no submit, entao salvar no ultimo passo
 * mandaria so o ultimo pedaco. Escondido, o input continua no form e o valor
 * continua indo junto.
 */

import { useState, type ReactNode } from "react";

export interface Passo {
  id: string;
  rotulo: string;
  conteudo: ReactNode;
}

export function Passos({ passos, erroNoPasso }: {
  passos: Passo[];
  /** id do passo que contem o campo recusado pelo backend, para saltar ate ele */
  erroNoPasso?: string | null;
}) {
  const [indice, setIndice] = useState(0);
  // O backend recusa nomeando o campo, e o campo pode estar num passo que nem
  // esta na tela: sem isto, a mensagem apareceria sozinha, sem o input do lado.
  const alvo = erroNoPasso ? passos.findIndex((p) => p.id === erroNoPasso) : -1;
  const atual = alvo >= 0 ? alvo : Math.min(indice, passos.length - 1);

  return (
    <div className="passos">
      <nav className="passos-trilha" aria-label="Passos do formulário">
        {passos.map((p, i) => (
          <button
            key={p.id}
            type="button"
            className={`passo-aba${i === atual ? " ativo" : ""}`}
            aria-current={i === atual ? "step" : undefined}
            onClick={() => setIndice(i)}
          >
            {p.rotulo}
          </button>
        ))}
      </nav>

      {passos.map((p, i) => (
        <div key={p.id} className="passo-corpo" hidden={i !== atual}>
          {p.conteudo}
        </div>
      ))}

      <div className="passos-rodape">
        <button type="button" className="ghost" disabled={atual === 0}
          onClick={() => setIndice(atual - 1)}>
          Voltar
        </button>
        <span className="passos-conta">passo {atual + 1} de {passos.length}</span>
        <button type="button" className="ghost" disabled={atual === passos.length - 1}
          onClick={() => setIndice(atual + 1)}>
          Avançar
        </button>
      </div>
    </div>
  );
}
