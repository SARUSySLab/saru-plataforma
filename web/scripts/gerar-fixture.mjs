// Gerador do fixture de desenvolvimento do front.
//
// Emite `src/fixtures/relatorio.json` no shape de `types/contract.ts` e uma
// serie de amostras por volta em `src/fixtures/amostras/`. Roda uma vez e
// grava; NAO e importado pelo app. O app le so JSON no shape do contrato,
// exatamente como vai ler da API depois, entao trocar fixture por endpoint e
// trocar a origem do fetch e mais nada.
//
// O motor sintetico e o do prototipo SARU Analyzer, ja validado com o Lucas:
// o tracado gera a curvatura, a curvatura gera o perfil de velocidade, e do
// perfil saem acelerador, freio, direcao, marcha, RPM e consumo. Por isso os
// blocos concordam entre si: sao o mesmo sinal visto de alturas diferentes.
//
// Escrito em JS puro de proposito: rodar TypeScript aqui exigiria tsx ou
// ts-node, e dependencia nova e decisao do Lucas, nao minha. A garantia de
// tipo vem do outro lado, no `satisfies Relatorio` de quem importa o JSON.

import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const SAIDA = join(AQUI, "..", "src", "fixtures");

const TAU = Math.PI * 2;
const LEN = 3835; // m
const N = 900; // amostras por volta
const NLAPS = 14;

const mulberry = (a) => () => {
  a |= 0;
  a = (a + 0x6d2b79f5) | 0;
  let t = Math.imul(a ^ (a >>> 15), 1 | a);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

// --- tracado: perturbacao radial de uma elipse. Star-shaped por construcao,
// entao nunca se auto-intersecta, e a variacao de raio produz retas longas e
// curvas fechadas de verdade.
function construirPista() {
  const pts = [];
  for (let i = 0; i < N; i++) {
    const t = (i / N) * TAU;
    const r = 1 + 0.3 * Math.sin(2 * t + 0.4) + 0.15 * Math.cos(3 * t - 0.9) + 0.085 * Math.sin(5 * t + 2.1);
    pts.push({ x: Math.cos(t) * r * 1.28, y: Math.sin(t) * r });
  }
  let per = 0;
  const seg = [];
  for (let i = 0; i < N; i++) {
    const a = pts[i];
    const b = pts[(i + 1) % N];
    const d = Math.hypot(b.x - a.x, b.y - a.y);
    seg.push(d);
    per += d;
  }
  const k = LEN / per;
  const dist = [0];
  for (let i = 0; i < N; i++) dist.push(dist[i] + seg[i] * k);
  const curv = new Array(N);
  const sign = new Array(N);
  for (let i = 0; i < N; i++) {
    const p = pts[(i - 4 + N) % N];
    const c = pts[i];
    const q = pts[(i + 4) % N];
    const ax = (c.x - p.x) * k;
    const ay = (c.y - p.y) * k;
    const bx = (q.x - c.x) * k;
    const by = (q.y - c.y) * k;
    const cross = ax * by - ay * bx;
    const la = Math.hypot(ax, ay);
    const lb = Math.hypot(bx, by);
    const lc = Math.hypot((q.x - p.x) * k, (q.y - p.y) * k);
    const area = Math.abs(cross) / 2;
    curv[i] = area < 1e-9 ? 1e-6 : Math.max(1e-6, (4 * area) / (la * lb * lc));
    sign[i] = Math.sign(cross) || 1;
  }
  const suave = curv.map((_, i) => {
    let s = 0;
    for (let j = -6; j <= 6; j++) s += curv[(i + j + N) % N];
    return s / 13;
  });
  return { pts, dist, curv: suave, sign };
}
const PISTA = construirPista();

// --- curvas: picos locais de curvatura
function acharCurvas(tr) {
  const c = tr.curv;
  const out = [];
  for (let i = 0; i < N; i++) {
    const prev = c[(i - 1 + N) % N];
    const next = c[(i + 1) % N];
    if (c[i] >= prev && c[i] > next && c[i] > 0.0016) out.push({ i, k: c[i] });
  }
  out.sort((a, b) => b.k - a.k);
  const keep = out.slice(0, 11).sort((a, b) => a.i - b.i);
  const apelidos = { 0: "Curva do Sol", 1: "Ferradura", 3: "Esses", 4: "Descida do Lago", 6: "Bico de Pato", 7: "Molha", 9: "Cotovelo" };
  return keep.map((p, n) => {
    const prev = keep[(n - 1 + keep.length) % keep.length].i;
    const next = keep[(n + 1) % keep.length].i;
    const a = (p.i - Math.min(46, Math.abs((p.i - prev + N) % N) / 2) + N) % N;
    const b = (p.i + Math.min(46, Math.abs((next - p.i + N) % N) / 2)) % N;
    return {
      id: "curva-" + (n + 1),
      indice: n,
      rotulo: apelidos[n] ?? "Curva " + (n + 1),
      nome: "Curva " + (n + 1),
      apex: p.i,
      a: Math.round(a),
      b: Math.round(b),
      d0: tr.dist[Math.round(a)],
      d1: tr.dist[Math.round(b)],
    };
  });
}
const CURVAS = acharCurvas(PISTA);

// --- espinha operacional: evento > sessao > bateria > gravacao.
// `bateria_id` e anulavel de proposito (decisao 16): arquivo solto ingere e
// gera os quatro niveis. Aqui o fixture sempre traz bateria; o caso sem
// contexto e exercitado por um segundo fixture, mais adiante.
const BATERIAS = [
  {
    id: "bat-1",
    rotulo: "Bateria 1",
    sessao: "Manhã",
    horario: "08:42",
    voltas: [1, 9],
    pneu: { estado: "novo", composto: "Pirelli SC1 / SC0", voltas0: 4 },
    temperatura_ar_c: 24,
    temperatura_pista_c: 33,
    vento_kmh: 8,
    notas_piloto: "Pista com bastante grip. Moto entrando bem na Ferradura.",
    notas_engenheiro: "Pré-carga traseira 9 mm. Pneu com 4 voltas do dia anterior.",
  },
  {
    id: "bat-2",
    rotulo: "Bateria 2",
    sessao: "Meio-dia",
    horario: "11:20",
    voltas: [10, 14],
    pneu: { estado: "usado", composto: "Pirelli SC1 / SC0", voltas0: 22 },
    temperatura_ar_c: 31,
    temperatura_pista_c: 49,
    vento_kmh: null, // falta de proposito: dispara a pergunta ativa da decisao 6
    notas_piloto: null,
    notas_engenheiro: "Mesmo jogo de pneu da bateria 1, sem troca.",
  },
];
const bateriaDe = (n) => BATERIAS.find((b) => n >= b.voltas[0] && n <= b.voltas[1]);

// --- perfil de uma volta
function construirVolta(seed, skill) {
  const rnd = mulberry(seed);
  const aLat = 11.6 * skill.grip;
  const aAcc = 5.4 * skill.acc;
  const aBrk = 9.8 * skill.brk;
  const vMax = 61 * skill.top;
  const err = CURVAS.map(() => 1 - (rnd() * 0.11 + 0.005) * skill.sloppy);
  const errAt = new Array(N).fill(1);
  CURVAS.forEach((c, ci) => {
    for (let j = 0; j < N; j++) {
      const d = Math.min(Math.abs(j - c.apex), N - Math.abs(j - c.apex));
      if (d < 60) errAt[j] = Math.min(errAt[j], 1 - (1 - err[ci]) * (1 - d / 60));
    }
  });
  // Troca deliberada de fase numa curva: entra mais devagar para abrir o
  // acelerador antes e sair mais forte. E o caso que o engenheiro nomeou e o
  // motivo de o tempo por fase existir.
  const aAccAt = new Array(N).fill(aAcc);
  if (skill.trade != null) {
    const c = CURVAS[skill.trade];
    for (let j = 0; j < N; j++) {
      const rel = ((j - c.apex + N + N / 2) % N) - N / 2;
      if (rel > -54 && rel < -10) errAt[j] = Math.min(errAt[j], 1 - 0.075 * Math.sin(((rel + 54) / 44) * Math.PI));
      if (rel >= 0 && rel < 90) aAccAt[j] = aAcc * (1 + 1.05 * (1 - rel / 90));
    }
  }
  const ds = (i) => PISTA.dist[i + 1] - PISTA.dist[i];
  const v = new Array(N);
  for (let i = 0; i < N; i++) v[i] = Math.min(vMax, Math.sqrt(aLat / PISTA.curv[i])) * errAt[i];
  for (let pass = 0; pass < 3; pass++) {
    for (let i = 0; i < N; i++) {
      const p = (i - 1 + N) % N;
      v[i] = Math.min(v[i], Math.sqrt(v[p] * v[p] + 2 * aAccAt[p] * ds(p)));
    }
    for (let i = N - 1; i >= 0; i--) {
      const nx = (i + 1) % N;
      v[i] = Math.min(v[i], Math.sqrt(v[nx] * v[nx] + 2 * aBrk * ds(i)));
    }
  }
  const thr = [], brk = [], str = [], gear = [], rpm = [], latA = [], lonA = [];
  const t = [0];
  let litros = 0;
  for (let i = 0; i < N; i++) {
    const nx = (i + 1) % N;
    const d = ds(i);
    const a = (v[nx] * v[nx] - v[i] * v[i]) / (2 * d);
    lonA[i] = a / 9.81;
    latA[i] = ((v[i] * v[i] * PISTA.curv[i]) / 9.81) * PISTA.sign[i];
    if (a > 0.35) { thr[i] = Math.min(100, (a / aAccAt[i]) * 100); brk[i] = 0; }
    else if (a < -0.35) { brk[i] = Math.min(100, (-a / aBrk) * 100); thr[i] = 0; }
    else { thr[i] = 22 + v[i] * 0.45; brk[i] = 0; }
    str[i] = Math.max(-100, Math.min(100, PISTA.curv[i] * PISTA.sign[i] * 9000 * (2 - errAt[i])));
    const kmh = v[i] * 3.6;
    gear[i] = kmh < 62 ? 1 : kmh < 92 ? 2 : kmh < 124 ? 3 : kmh < 158 ? 4 : kmh < 192 ? 5 : 6;
    const faixa = [0, 62, 92, 124, 158, 192, 240][gear[i] - 1];
    const topo = [62, 92, 124, 158, 192, 240][gear[i] - 1];
    rpm[i] = 6200 + ((kmh - faixa) / (topo - faixa)) * 7300;
    const dt = d / ((v[i] + v[nx]) / 2 || 1);
    t[i + 1] = t[i] + dt;
    // vazao proporcional a rotacao e carga, integrada no TEMPO e nao na
    // distancia: integrar na distancia faria a volta lenta parecer economica.
    litros += 0.0000135 * rpm[i] * (0.2 + (0.8 * thr[i]) / 100) * dt;
  }
  return { v, thr, brk, str, gear, rpm, latA, lonA, t, tempo_s: t[N], litros };
}

const habilidades = [];
for (let i = 0; i < NLAPS; i++) {
  const warm = i < 2 ? 0.955 + i * 0.022 : 1;
  // a partir da volta 10 comeca a bateria 2: pneu com 22 voltas e pista 16 C
  // mais quente. A queda e o efeito do contexto, nao ruido nem piloto pior.
  const fade = i >= 9 ? 1 - (i - 8) * 0.0075 : 1;
  const rnd = mulberry(700 + i * 13);
  habilidades.push({
    grip: (0.985 + rnd() * 0.03) * warm * fade,
    acc: (0.98 + rnd() * 0.04) * warm,
    brk: (0.97 + rnd() * 0.06) * warm * fade,
    top: (0.995 + rnd() * 0.01) * warm,
    sloppy: (i < 2 ? 2.4 : 1) * (0.72 + rnd() * 0.7) * (i >= 9 ? 1.3 : 1),
    trade: i >= 9 ? 3 : null,
  });
}

const VOLTAS = habilidades.map((s, i) => {
  const L = construirVolta(1000 + i * 37, s);
  L.n = i + 1;
  L.tipo = i === 0 ? "out" : i === NLAPS - 1 ? "in" : "";
  L.valida = !L.tipo;
  L.bateria = bateriaDe(L.n);
  L.voltas_pneu = L.bateria.pneu.voltas0 + (L.n - L.bateria.voltas[0]);
  return L;
});

const LIM_SETOR = [0, Math.round(N / 3), Math.round((2 * N) / 3), N];
VOLTAS.forEach((L) => {
  L.setores_s = [0, 1, 2].map((s) => L.t[LIM_SETOR[s + 1]] - L.t[LIM_SETOR[s]]);
  L.v_max_kmh = Math.max(...L.v) * 3.6;
  L.acelerador_pleno_pct = (L.thr.filter((x) => x > 96).length / N) * 100;
});
const VALIDAS = VOLTAS.filter((L) => L.valida);
const MELHOR = VALIDAS.reduce((a, b) => (b.tempo_s < a.tempo_s ? b : a));
const MELHOR_SETOR = [0, 1, 2].map((s) => Math.min(...VALIDAS.map((L) => L.setores_s[s])));
const IDEAL = MELHOR_SETOR.reduce((a, b) => a + b, 0);

// media canal a canal: todas as voltas caem na MESMA grade de distancia, entao
// a media por indice e legitima. O tempo dela e integrado do proprio perfil,
// nao a media dos tempos: sao contas diferentes.
const MEDIA = (() => {
  const media = (f) => {
    const a = new Array(N);
    for (let i = 0; i < N; i++) {
      let sm = 0;
      VALIDAS.forEach((L) => (sm += f(L)[i]));
      a[i] = sm / VALIDAS.length;
    }
    return a;
  };
  const o = {
    v: media((L) => L.v), thr: media((L) => L.thr), brk: media((L) => L.brk),
    str: media((L) => L.str), rpm: media((L) => L.rpm),
    latA: media((L) => L.latA), lonA: media((L) => L.lonA),
  };
  o.gear = media((L) => L.gear).map((g) => Math.round(g));
  o.t = [0];
  for (let i = 0; i < N; i++) {
    const d = PISTA.dist[i + 1] - PISTA.dist[i];
    o.t[i + 1] = o.t[i] + d / ((o.v[i] + o.v[(i + 1) % N]) / 2 || 1);
  }
  o.tempo_s = o.t[N];
  o.n = "media";
  return o;
})();

const serieDe = (ref) => (ref === "media" ? MEDIA : VOLTAS[ref - 1]);

// --- consumo: a conta do engenheiro, literal. Pega todas as voltas, exclui a
// melhor e a pior, tira a media do que sobra.
function consumo(voltas) {
  const usaveis = voltas.filter((L) => L.valida);
  if (usaveis.length < 3) return null;
  const ord = usaveis.slice().sort((a, b) => a.litros - b.litros);
  const nucleo = ord.slice(1, -1);
  return {
    litros_por_volta: nucleo.reduce((a, L) => a + L.litros, 0) / nucleo.length,
    voltas_consideradas: nucleo.length,
  };
}

// --- perdas por trecho, com tempo POR FASE. Fonte unica dos blocos 3 e 9.
function perdas(volta, ref, modo) {
  const R = serieDe(ref);
  const janelas =
    modo === "micro_setor"
      ? Array.from({ length: Math.round(LEN / 200) }, (_, k) => {
          const d0 = k * 200;
          const d1 = Math.min(LEN, (k + 1) * 200);
          const a = PISTA.dist.findIndex((d) => d >= d0);
          let b = PISTA.dist.findIndex((d) => d >= d1);
          if (b < 0) b = N;
          return { id: "micro-" + (k + 1), rotulo: "Trecho " + (k + 1), a, b, d0, d1 };
        })
      : CURVAS;
  return janelas.map((w) => {
    const idx = [];
    for (let i = w.a; i !== w.b; i = (i + 1) % N) { idx.push(i); if (idx.length > 260) break; }
    let dt = 0;
    const fase = { entrada_s: 0, meio_s: 0, saida_s: 0 };
    idx.forEach((i, k) => {
      const d = PISTA.dist[i + 1] - PISTA.dist[i] || 0;
      const q = d / volta.v[i] - d / R.v[i];
      dt += q;
      const f = k / idx.length;
      fase[f < 0.38 ? "entrada_s" : f < 0.66 ? "meio_s" : "saida_s"] += q;
    });
    return { janela: w, idx, perda_s: dt, fase };
  });
}

// --- atributos do trecho: em UNIDADE, com a referencia ao lado.
function atributos(volta, ref, idx) {
  const R = serieDe(ref);
  const tempo = (S) => idx.reduce((a, i) => a + (PISTA.dist[i + 1] - PISTA.dist[i] || 0) / S.v[i], 0);
  const picoBrk = (S) => Math.max(...idx.map((i) => S.brk[i]));
  const picoG = (S) => Math.max(...idx.map((i) => Math.hypot(S.latA[i], S.lonA[i])));
  const ts = VALIDAS.map(tempo);
  const m = ts.reduce((a, b) => a + b, 0) / ts.length;
  const sd = Math.sqrt(ts.reduce((a, b) => a + (b - m) ** 2, 0) / ts.length);
  const bA = picoBrk(volta);
  const bR = picoBrk(R);
  const temFreio = bA >= 3 || bR >= 3;
  return {
    tempo_no_trecho: { valor: tempo(volta), referencia: tempo(R), unidade: "s", aplicavel: true },
    repeticao_entre_voltas_s: sd,
    pico_frenagem: { valor: temFreio ? bA : null, referencia: temFreio ? bR : null, unidade: "%", aplicavel: temFreio },
    pico_envelope_grip: { valor: picoG(volta), referencia: picoG(R), unidade: "g", aplicavel: true },
  };
}

// --- a ressalva que relativiza o insight (decisao 7)
function ressalvaDe(volta, ref) {
  if (ref === "media") {
    return {
      fator: "outro",
      descricao:
        "A referência é a média das válidas, que mistura as duas baterias do dia: pneu novo de manhã e pneu com " +
        BATERIAS[1].pneu.voltas0 + "+ voltas ao meio-dia. Serve para ver tendência, não para cravar ganho.",
      referencia_diverge: true,
    };
  }
  const R = VOLTAS[ref - 1];
  if (R.n === volta.n) return null;
  const a = volta.bateria;
  const b = R.bateria;
  if (a.id === b.id) {
    return {
      fator: "outro",
      descricao:
        "Volta e referência são da mesma bateria (" + a.rotulo + ", " + a.horario +
        "), mesmo jogo de pneu e mesma condição de pista. A comparação é limpa.",
      referencia_diverge: false,
    };
  }
  const dPneu = volta.voltas_pneu - R.voltas_pneu;
  const dPista = a.temperatura_pista_c - b.temperatura_pista_c;
  return {
    fator: "pneu",
    descricao:
      "A referência é a volta " + R.n + ", da " + b.rotulo + " (" + b.horario + "), quando o pneu tinha " +
      R.voltas_pneu + " voltas e a pista estava a " + b.temperatura_pista_c + " °C. Nesta volta o pneu tem " +
      volta.voltas_pneu + " e a pista está a " + a.temperatura_pista_c + " °C: são " + Math.abs(dPneu) +
      " voltas " + (dPneu > 0 ? "a mais" : "a menos") + " de borracha e " + Math.abs(dPista) + " °C " +
      (dPista > 0 ? "a mais" : "a menos") + " de asfalto. Houve troca de pneu? Caso não, parte do ganho previsto não é técnica.",
    referencia_diverge: true,
  };
}

// ============================================================================
// MONTAGEM DO RELATORIO
// ============================================================================
const REF_PADRAO = MELHOR.n; // a melhor propria e o default; o usuario troca
const EM_ESCOPO = VALIDAS[VALIDAS.length - 1]; // ultima volta valida

const CANAIS = [
  { id: "velocidade", rotulo: "Velocidade", unidade: "km/h" },
  { id: "acelerador", rotulo: "Acelerador", unidade: "%" },
  { id: "freio", rotulo: "Freio", unidade: "%" },
  { id: "direcao", rotulo: "Direção", unidade: "graus" },
  { id: "marcha", rotulo: "Marcha", unidade: "" },
  { id: "rpm", rotulo: "RPM", unidade: "rpm" },
  { id: "acel_lat", rotulo: "Acel. lateral", unidade: "g" },
  { id: "acel_lon", rotulo: "Acel. longitudinal", unidade: "g" },
];

function perdaContrato(p, volta, ref) {
  return {
    trecho_id: p.janela.id,
    rotulo: p.janela.rotulo,
    modo: p.janela.id.startsWith("curva") ? "curva" : "micro_setor",
    s_inicio_m: p.janela.d0,
    s_fim_m: p.janela.d1,
    perda_s: p.perda_s,
    tempo_por_fase: {
      disponivel: true,
      entrada_s: p.fase.entrada_s,
      meio_s: p.fase.meio_s,
      saida_s: p.fase.saida_s,
      troca_de_fase: p.fase.entrada_s > 0.004 && p.fase.saida_s < -0.004,
    },
    ressalva: ressalvaDe(volta, ref),
    pilotagem: { disponivel: true, ...atributos(volta, ref, p.idx) },
  };
}

function montarRelatorio(volta, ref) {
  const todas = perdas(volta, ref, "curva").map((p) => perdaContrato(p, volta, ref));
  const micro = perdas(volta, ref, "micro_setor").map((p) => perdaContrato(p, volta, ref));
  const top3 = todas.filter((p) => p.perda_s > 0).sort((a, b) => b.perda_s - a.perda_s).slice(0, 3);
  const cE = consumo(VOLTAS);
  const cB = consumo(VOLTAS.filter((L) => L.bateria.id === volta.bateria.id));
  const R = serieDe(ref);

  return {
    gravacao_id: "grav-goiania-2022-11-19",
    piloto: "M. Ferraz",
    layout: { id: "goiania-completo", nome: "Autódromo de Goiânia", comprimento_m: LEN },
    resolucao_pista: "alias",
    // Captura de .xrk com amostra: o ramo degradado (`somente_inventario`) e
    // o do .gpk/.rrk sozinho, que nem chega a ter volta cortada.
    amostra_da_captura: { disponivel: true, arquivos_lidos: 3, arquivos_com_amostra: 1 },

    n0: {
      melhor_volta: {
        melhor_volta_s: MELHOR.tempo_s,
        melhor_volta_n: MELHOR.n,
        volta_ideal_s: IDEAL,
        margem_para_ideal_s: MELHOR.tempo_s - IDEAL,
        voltas_validas: VALIDAS.length,
        voltas_totais: NLAPS,
        // a guarda do B1: se a soma dos melhores setores passasse a melhor
        // volta, a ideal seria suprimida em vez de exibida
        ideal_suprimida: IDEAL > MELHOR.tempo_s + 1e-9,
      },
      perdas_top3: { disponivel: true, itens: top3 },
    },

    n1: {
      voltas: VOLTAS.map((L) => ({
        n: L.n,
        tempo_s: L.tempo_s,
        setores_s: L.setores_s,
        v_max_kmh: L.v_max_kmh,
        delta_referencia_s: L.tempo_s - R.tempo_s,
        valida: L.valida,
        motivo_invalida: L.tipo === "out" ? "out-lap" : L.tipo === "in" ? "in-lap" : null,
        litros: L.litros,
        acelerador_pleno_pct: L.acelerador_pleno_pct,
        bateria: { id: L.bateria.id, rotulo: L.bateria.rotulo },
        voltas_pneu: L.voltas_pneu,
      })),
      consumo: {
        media_etapa: cE ? { disponivel: true, ...cE } : { disponivel: false, motivo: "sem_canal_combustivel", texto: "Sem voltas válidas suficientes para a média." },
        media_bateria: cB ? { disponivel: true, ...cB } : { disponivel: false, motivo: "sem_contexto_sessao", texto: "Sem bateria em escopo." },
      },
    },

    trechos: {
      disponivel: true,
      itens: CURVAS.map((c) => ({ id: c.id, rotulo: c.rotulo, s_inicio_m: c.d0, s_fim_m: c.d1, apex_m: PISTA.dist[c.apex] })),
    },
    tracado: {
      disponivel: true,
      pontos: PISTA.pts.map((p, i) => ({ x: p.x, y: p.y, s_m: PISTA.dist[i] })),
    },

    n2: {
      por_curva: { disponivel: true, itens: todas },
      por_micro_setor: { disponivel: true, itens: micro },
    },
    n3: {
      canais: CANAIS.map((c) => ({
        ...c,
        uri: "fixture://amostras/volta-" + volta.n + ".json#" + c.id,
        frequencia_hz: 20,
        n_amostras: N,
      })),
    },

    contexto: {
      setup: {
        "Pneu dianteiro": "Pirelli SC1 · 27,0 psi",
        "Pneu traseiro": "Pirelli SC0 · 22,5 psi",
        "Pré-carga dianteira": "12 mm",
        "Pré-carga traseira": "9 mm",
        "Pinhão / coroa": "16 / 43",
        "Mapa do motor": "2 (pista seca)",
        "Controle de tração": "nível 4",
        "Combustível na largada": "14,0 L",
        Piloto: "M. Ferraz · 72 kg",
      },
      sessao: {
        disponivel: true,
        pneu: { disponivel: true, estado: volta.bateria.pneu.estado, voltas_rodadas: volta.voltas_pneu, composto: volta.bateria.pneu.composto },
        temperatura_ar_c: volta.bateria.temperatura_ar_c,
        temperatura_pista_c: volta.bateria.temperatura_pista_c,
        vento_kmh: volta.bateria.vento_kmh,
        horario: volta.bateria.horario,
        notas_piloto: volta.bateria.notas_piloto,
        notas_engenheiro: volta.bateria.notas_engenheiro,
        origem: "bateria",
      },
    },
  };
}

function serieAmostras(ref) {
  const S = serieDe(ref);
  return {
    volta: ref,
    distancia_m: PISTA.dist.slice(0, N).map((d) => +d.toFixed(2)),
    canais: {
      velocidade: S.v.map((x) => +(x * 3.6).toFixed(2)),
      acelerador: S.thr.map((x) => +x.toFixed(1)),
      freio: S.brk.map((x) => +x.toFixed(1)),
      direcao: S.str.map((x) => +x.toFixed(1)),
      marcha: S.gear.slice(0, N),
      rpm: S.rpm.map((x) => Math.round(x)),
      acel_lat: S.latA.map((x) => +x.toFixed(3)),
      acel_lon: S.lonA.map((x) => +x.toFixed(3)),
    },
  };
}

// ============================================================================
mkdirSync(join(SAIDA, "amostras"), { recursive: true });

const relatorio = montarRelatorio(EM_ESCOPO, REF_PADRAO);
writeFileSync(join(SAIDA, "relatorio.json"), JSON.stringify(relatorio, null, 1));

const refs = ["media", ...VOLTAS.map((L) => L.n)];
refs.forEach((r) => {
  writeFileSync(join(SAIDA, "amostras", "volta-" + r + ".json"), JSON.stringify(serieAmostras(r)));
});

console.log("relatorio.json: volta em escopo", EM_ESCOPO.n, "| referencia", REF_PADRAO);
console.log("melhor", MELHOR.tempo_s.toFixed(3), "| ideal", IDEAL.toFixed(3), "| ideal <= melhor:", IDEAL <= MELHOR.tempo_s);
console.log("amostras:", refs.length, "series de", N, "pontos");
