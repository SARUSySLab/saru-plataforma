// Sessao do usuario.
//
// Nao ha token nesta camada de proposito. O backend manda o JWT num cookie
// httpOnly, entao o browser o anexa sozinho e o JavaScript nao consegue le-lo,
// que e justamente o ponto: token que o JS nao le, XSS nao rouba. O front
// descobre se esta logado perguntando (`eu()`), nao lendo storage.

import { enviar, obter, ErroDaApi } from "./api";

export interface Usuario {
  id: string;
  email: string;
  nome: string | null;
  papel: string;
}

export function registro(email: string, senha: string, nome?: string): Promise<Usuario> {
  return enviar<Usuario>("/auth/registro", { email, senha, nome: nome || null });
}

export function login(email: string, senha: string): Promise<Usuario> {
  return enviar<Usuario>("/auth/login", { email, senha });
}

export function logout(): Promise<void> {
  return enviar<void>("/auth/logout", {});
}

/** O usuario da sessao, ou `null` se nao ha sessao. 401 nao e erro aqui: e resposta. */
export async function eu(): Promise<Usuario | null> {
  try {
    return await obter<Usuario>("/auth/eu");
  } catch (e) {
    if (e instanceof ErroDaApi && e.status === 401) return null;
    throw e;
  }
}
