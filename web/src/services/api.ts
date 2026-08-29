// O unico lugar do front que sabe falar HTTP.
//
// Base `/api` e relativa de proposito: em dev o proxy do vite.config.ts manda
// pra 127.0.0.1:8010, e em producao o front sai da mesma origem da API. Assim
// nao ha CORS pra configurar nem URL de ambiente pra vazar no bundle.
//
// Regra da casa: componente nao chama isto, hook chama servico, servico chama
// isto. Ver `services/gravacoes.ts` e `services/relatorio.ts`.

/** Erro de resposta da API, com o status preservado pra quem precisa distinguir. */
export class ErroDaApi extends Error {
  // campos declarados e atribuidos a mao: `erasableSyntaxOnly` esta ligado no
  // tsconfig e nao aceita parameter property
  readonly status: number;
  readonly detalhe: unknown;

  constructor(status: number, detalhe: unknown, mensagem: string) {
    super(mensagem);
    this.name = "ErroDaApi";
    this.status = status;
    this.detalhe = detalhe;
  }
}

const BASE = "/api";

/**
 * O texto que a tela mostra. O backend erra em dois formatos: `detail` string
 * (os `HTTPException` simples) e `detail` objeto (a divergencia de contrato do
 * `_validado`, que traz `erro` e `divergencias`). Os dois viram frase legivel
 * aqui, porque tela nao deve saber a forma do erro do servidor.
 */
/**
 * Assinantes de 401. A sessao caiu, e quem mostra tela precisa saber AGORA.
 *
 * Sem isto, token expirado virava uma mensagem de erro criptica no meio de uma
 * acao qualquer, e o usuario ficava tentando de novo contra uma sessao morta.
 * O modulo de sessao se inscreve aqui e derruba o estado, o que leva a tela de
 * login sozinha. Fica neste arquivo, e nao no de sessao, porque e aqui que a
 * resposta 401 chega primeiro, seja de qual rota for.
 */
const aoExpirar: Array<() => void> = [];

export function quandoSessaoExpirar(f: () => void): void {
  aoExpirar.push(f);
}

function avisarExpiracao(): void {
  for (const f of aoExpirar) f();
}

function mensagemDoErro(status: number, corpo: unknown): string {
  const detalhe = (corpo as { detail?: unknown } | null)?.detail;
  if (typeof detalhe === "string") return detalhe;
  if (detalhe && typeof detalhe === "object" && "erro" in detalhe) {
    return String((detalhe as { erro: unknown }).erro);
  }
  if (status === 401) return "sua sessão expirou, entre de novo";
  if (status === 404) return "não encontrado";
  // 502 e 504 vem do proxy, nao da aplicacao: o corpo e HTML do Cloudflare e
  // nao tem `detail`. Acontece de verdade durante um redeploy, e dizer
  // "indisponivel no momento, tente de novo" e acionavel, enquanto "o servidor
  // falhou" faz o usuario achar que o arquivo dele quebrou alguma coisa.
  if (status === 502 || status === 503 || status === 504) {
    return "servidor indisponível no momento (pode ser um deploy em curso), tente de novo em instantes";
  }
  if (status >= 500) return "o servidor falhou ao responder";
  return `falha na requisição (${status})`;
}

async function tratar<T>(resposta: Response): Promise<T> {
  if (resposta.status === 401) avisarExpiracao();
  if (!resposta.ok) {
    // corpo de erro pode nao ser JSON (proxy fora do ar, HTML de gateway)
    const corpo = await resposta.json().catch(() => null);
    throw new ErroDaApi(resposta.status, corpo, mensagemDoErro(resposta.status, corpo));
  }
  // 204 e 205 nao tem corpo por definicao, e `Content-Length: 0` tambem nao.
  // Chamar `.json()` nesses casos levanta SyntaxError, que nao e ErroDaApi e
  // por isso escapava do catch de quem chamou. Foi assim que o logout parou de
  // funcionar: o servidor respondia 204, o parse estourava, e o `set({usuario:
  // null})` depois do await nunca rodava. A sessao so caia no F5 seguinte.
  if (resposta.status === 204 || resposta.status === 205) return undefined as T;
  const texto = await resposta.text();
  if (!texto) return undefined as T;
  return JSON.parse(texto) as T;
}

/**
 * GET com query. `undefined` e `null` somem da query em vez de virar a string
 * "undefined": o backend trata parametro AUSENTE e parametro vazio de formas
 * diferentes (em `/api/relatorio`, ausente significa "escolha voce o par").
 */
export async function obter<T>(
  caminho: string,
  parametros: Record<string, string | number | boolean | null | undefined> = {},
): Promise<T> {
  const query = new URLSearchParams();
  for (const [chave, valor] of Object.entries(parametros)) {
    if (valor !== undefined && valor !== null) query.set(chave, String(valor));
  }
  const sufixo = query.size > 0 ? `?${query}` : "";
  return tratar<T>(await fetch(`${BASE}${caminho}${sufixo}`));
}

/** POST de JSON. */
export async function enviar<T>(caminho: string, corpo: unknown): Promise<T> {
  return tratar<T>(
    await fetch(`${BASE}${caminho}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    }),
  );
}

/** PATCH de JSON. Mesma disciplina do POST: erro vira `ErroDaApi`. */
export async function enviarPatch<T>(caminho: string, corpo: unknown): Promise<T> {
  return tratar<T>(
    await fetch(`${BASE}${caminho}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    }),
  );
}

/**
 * POST de multipart com progresso. Usa XMLHttpRequest, nao fetch: `fetch` nao
 * expoe progresso de UPLOAD (o `ReadableStream` de request tem suporte parcial
 * e exige HTTP/2), e o bundle da PoC tem arquivo de centenas de MB. Barra de
 * progresso falsa seria pior que barra nenhuma.
 */
export function enviarArquivos<T>(
  caminho: string,
  formulario: FormData,
  aoProgredir?: (fracao: number) => void,
): Promise<T> {
  return new Promise<T>((resolver, rejeitar) => {
    const req = new XMLHttpRequest();
    req.open("POST", `${BASE}${caminho}`);
    req.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable && aoProgredir) aoProgredir(e.loaded / e.total);
    });
    req.addEventListener("load", () => {
      const corpo = (() => {
        try {
          return JSON.parse(req.responseText) as unknown;
        } catch {
          return null;
        }
      })();
      if (req.status >= 200 && req.status < 300) {
        resolver(corpo as T);
        return;
      }
      if (req.status === 401) avisarExpiracao();
      rejeitar(new ErroDaApi(req.status, corpo, mensagemDoErro(req.status, corpo)));
    });
    req.addEventListener("error", () =>
      rejeitar(new ErroDaApi(0, null, "não foi possível falar com o servidor")),
    );
    req.addEventListener("abort", () => rejeitar(new ErroDaApi(0, null, "envio cancelado")));
    req.send(formulario);
  });
}

/** DELETE. Mesma disciplina: 204 sem corpo e sucesso, erro vira `ErroDaApi`. */
export async function excluir(caminho: string): Promise<void> {
  return tratar<void>(
    await fetch(`${BASE}${caminho}`, { method: "DELETE" }),
  );
}
