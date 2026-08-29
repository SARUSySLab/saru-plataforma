import { useState } from "react";
import { useSessao } from "./useSessao";
import { ErroDaApi } from "../services/api";
import { Marca } from "../componentes/Marca";

const SENHA_MINIMA = 10;

/**
 * Entrar e cadastrar na mesma tela, alternando por um link.
 *
 * Duas telas separadas para dois formularios de dois campos seria roteamento
 * de graca. O front espelha a regra de senha do backend (10 caracteres) pra
 * avisar antes do round-trip, mas quem MANDA e o servidor: validacao de
 * cliente e conveniencia, nunca garantia.
 */
export function Login() {
  const { entrar, cadastrar } = useSessao();
  const [modo, setModo] = useState<"entrar" | "cadastrar">("entrar");
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [nome, setNome] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const cadastrando = modo === "cadastrar";

  async function submeter(e: React.FormEvent) {
    e.preventDefault();
    if (cadastrando && senha.length < SENHA_MINIMA) {
      setErro(`a senha precisa de pelo menos ${SENHA_MINIMA} caracteres`);
      return;
    }
    setEnviando(true);
    setErro(null);
    try {
      if (cadastrando) await cadastrar(email, senha, nome);
      else await entrar(email, senha);
    } catch (e) {
      setErro(e instanceof ErroDaApi ? e.message : "não foi possível falar com o servidor");
      setEnviando(false);
    }
  }

  return (
    <div className="login-fundo">
      <form className="login-caixa" onSubmit={submeter}>
        {/* A marca completa carrega o nome, entao o texto ao lado seria o nome
            duas vezes. Fica so "Analyzer", que e o que a logo nao diz. */}
        <div className="login-marca">
          <Marca
            claro="/saru-logo-claro-v2.svg"
            escuro="/saru-logo.png"
            alt="SARU"
            className="login-logo"
          />
          <h1>Analyzer</h1>
        </div>
        <p className="login-sub">
          {cadastrando ? "Crie a sua conta para começar." : "Entre para abrir as suas sessões."}
        </p>

        {cadastrando && (
          <label>
            Nome
            <input value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="name" />
          </label>
        )}
        <label>
          E-mail
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
        </label>
        <label>
          Senha
          <input
            type="password"
            required
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            autoComplete={cadastrando ? "new-password" : "current-password"}
          />
          {cadastrando && <span className="dica">mínimo de {SENHA_MINIMA} caracteres</span>}
        </label>

        {erro && <p className="login-erro">{erro}</p>}

        <button type="submit" className="primario" disabled={enviando}>
          {enviando ? "..." : cadastrando ? "Criar conta" : "Entrar"}
        </button>

        <button
          type="button"
          className="ghost"
          onClick={() => {
            setModo(cadastrando ? "entrar" : "cadastrar");
            setErro(null);
          }}
        >
          {cadastrando ? "Já tenho conta" : "Criar uma conta"}
        </button>
      </form>
    </div>
  );
}
