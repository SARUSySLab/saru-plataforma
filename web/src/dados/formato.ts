// Formatacao de numero da tela. Um lugar so: tempo de volta e mm:ss.mmm em
// todo bloco, e delta sempre sai com sinal, senao o leitor tem que descobrir
// pela cor se ganhou ou perdeu.

export const tempo = (s: number) => {
  const m = Math.floor(s / 60);
  const r = s - m * 60;
  return `${m}:${r < 10 ? "0" : ""}${r.toFixed(3)}`;
};

export const sinal = (v: number, casas = 3) => (v > 0 ? "+" : "") + v.toFixed(casas);

export const rotuloRef = (r: number | "media") => (r === "media" ? "media das validas" : `V${r}`);
