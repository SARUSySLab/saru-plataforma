import { create } from "zustand";
import { eu, login as apiLogin, logout as apiLogout, registro as apiRegistro, type Usuario } from "../services/auth";
import { quandoSessaoExpirar } from "../services/api";
import { limparEscopo } from "../state/selection";

/**
 * Quem esta logado.
 *
 * Store separada da de selecao de proposito: selecao e efemera e cabe na tela,
 * sessao atravessa a aplicacao inteira e decide se ha tela. `carregando` comeca
 * true porque, no primeiro render, o front ainda nao sabe: o token esta num
 * cookie httpOnly que ele nao consegue ler, entao a unica forma de saber e
 * perguntar. Renderizar o login antes da resposta faria a tela de login piscar
 * a cada F5 de quem ja esta logado.
 */
interface Sessao {
  usuario: Usuario | null;
  carregando: boolean;
  conferir: () => Promise<void>;
  entrar: (email: string, senha: string) => Promise<void>;
  cadastrar: (email: string, senha: string, nome: string) => Promise<void>;
  sair: () => Promise<void>;
}

export const useSessao = create<Sessao>((set) => {
  // Qualquer 401, de qualquer rota, derruba a sessao e leva pro login. O
  // `eu()` e a excecao: ele PERGUNTA se ha sessao, e 401 ali e resposta
  // esperada, nao expiracao; por isso ele trata o 401 por conta propria antes
  // de chegar aqui.
  quandoSessaoExpirar(() => set({ usuario: null, carregando: false }));
  return {
  usuario: null,
  carregando: true,

  conferir: async () => {
    try {
      set({ usuario: await eu(), carregando: false });
    } catch {
      // falha de rede nao e "deslogado": deixa null e a tela mostra o login,
      // que e o unico caminho honesto sem saber o estado da sessao
      set({ usuario: null, carregando: false });
    }
  },

  entrar: async (email, senha) => set({ usuario: await apiLogin(email, senha) }),
  cadastrar: async (email, senha, nome) => set({ usuario: await apiRegistro(email, senha, nome) }),
  sair: async () => {
    await apiLogout();
    // escopo persistido morre junto com a sessao: e da conta, nao do browser
    limparEscopo();
    set({ usuario: null });
  },
  };
});
