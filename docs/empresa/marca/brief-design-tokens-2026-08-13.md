---
titulo: "Brief, reforma do design system (tokens, paleta, tipografia)"
data: "2026-08-13"
origem: "_arquivo/saru-app/docs/product/brief-design-tokens-2026-08-13.md"
status: "stale"
area: "ui_marca"
---

# Brief, reforma do design system (tokens, paleta, tipografia)

> **Branch:** `feature/claude-design-tokens` · worktree isolada.
> **Não mergear na `develop` antes da demo de 14/08.** Esta trilha existe justamente
> para não amassar o carro que corre amanhã.
> **Decisão do dono (2026-08-13):** direções **1 e 3**, paleta da marca (rosa/grená)
> **e** estética Bento Box sóbria (creme/sálvia/teal).

---

## 0. Regra de escopo

O agente desta trilha **não desenha SVG, não gera imagem, não vetoriza**. Os assets da marca
já existem em `saru-docs/docs/project/product/assets/brand/` (6 SVGs + PNGs; Variação 2
escolhida). O trabalho aqui é **arquitetura de tokens**: variáveis HSL, escalas, papéis,
tipografia, espaçamento, z-index. Plataforma especializada faz imagem.

---

## 1. ⛔ Corrigir antes de copiar qualquer coisa

O doc [`paleta_marca_e_ui.md`](../../../../saru-docs/docs/project/product/paleta_marca_e_ui.md)
(status: *proposto*) traz a paleta medida por k-means na arte. Os **HEX são a verdade medida**.
A **coluna HSL está errada nas 7 cores**, conferido com conversão RGB→HLS em 2026-08-13:

| HEX (medido, correto) | HSL no doc | HSL real | erro |
|---|---|---|---|
| `#19191F` preto da marca | `hsl(233 20% 12%)` | `hsl(240 11% 11%)` | saturação ~2× |
| `#591829` grená | `hsl(344 73% 35%)` | `hsl(344 58% 22%)` | **13 pontos de luz a mais** |
| `#F39CA3` **rosa (o acento)** | `hsl(356 36% 95%)` | `hsl(355 78% 78%)` | 🔴 **quase branco vs rosa** |
| `#C36A75` rosa escuro | `hsl(352 46% 77%)` | `hsl(353 43% 59%)` | 18 pontos de luz |
| `#4A474D` cinza | `hsl(264 7% 30%)` | `hsl(270 4% 29%)` | pequeno |
| `#E5E0DC` bege | `hsl(22 4% 90%)` | `hsl(27 15% 88%)` | saturação ~4× |
| `#802C3B` vermelho | `hsl(349 65% 50%)` | `hsl(349 49% 34%)` | 16 pontos de luz |

**Por que isso é o item nº 1:** `tokens.css` é **100% HSL, zero hex** (gate `check:tokens`).
Quem copiar o bloco `--saru-brand-*` do §4 do doc para o `tokens.css` publica um acento
`hsl(356 36% 95%)`, um rosa lavado, quase branco, no lugar do rosa da marca. O gate passa
(a sintaxe é válida), o contraste medido no §3 deixa de valer, e a reforma inteira sai errada
em silêncio. É o mesmo modo de falha do resto deste pipeline: **não crasha, produz número
errado calado.**

**Ação:** corrigir o §4 do doc no `saru-docs` (é o SoT documental) **antes** de escrever token.
Os contrastes WCAG do §3 foram calculados a partir do HEX e continuam válidos.

---

## 2. A síntese "1 e 3"

As duas direções escolhidas parecem brigar, paleta da marca (rosa/grená) **e** Bento Box
creme/sálvia/teal. Encaixam, e o encaixe é limpo porque o repo **já tem dois temas**
(`:root` dark + `[data-theme="solar"]` claro, `tokens.css:93-115`).

| Camada | Direção |
|---|---|
| **Layout (vale nos dois temas)** | Grid Bento Box: cards modulares, `radius-lg` suave, hierarquia tipográfica forte, densidade controlada |
| **`:root`, dark, uso de pista/trackside** | Mantém near-black flat. Acento migra de Apex Gold `#FBAF18` → **rosa `#F39CA3` = `hsl(355 78% 78%)`** (contraste 9,29 vs 10,35 do ouro, os dois passam AAA; a troca é de significado, não de legibilidade) |
| **`[data-theme="solar"]`, claro, escritório/demo** | Vira o Bento sóbrio: fundo creme `hsl(38 34% 95%)`, cards sálvia `hsl(150 14% 91%)`, texto teal `hsl(192 44% 15%)`. Acento vira **teal profundo `hsl(188 62% 28%)`**, 5,82:1 (o rosa tem 1,83 no claro, invisível; o grená `#A83A52` foi descartado por ficar na mesma família do `danger`) |
| **Marca** | Grená `hsl(344 58% 22%)` = massa e selo. **Nunca texto no dark** (contraste 1,46) |

⚠️ **Isto muda o ADR do padrão estético** ("dark flat Hybrid", 2026-06-13) e o `CLAUDE.md` §3 do
`saru-app`, que hoje aponta o SoT de marca para `saru-KB` (caminho morto). Precisa de ADR novo,
nascendo **Proposto**, ratificado pelo dono, não vira código antes disso.

### Travas já medidas que o brief carrega

1. **Rosa e grená não podem ser as duas primeiras séries de gráfico.** Matiz 344-356: mesma
   família, indistinguíveis em linha fina. A escala categórica nasce de matizes distantes; a
   marca entra como *destaque*, não como paleta de dados.
2. **Delta ganho/perda não pode ser rosa × vermelho**, 7° de distância. Se vermelho é perda,
   ganho sai de ciano/verde-azulado.
3. ✅ O creme/sálvia/teal do Bento **agora tem valor**, e com contraste calculado (não estimado):
   matiz veio do brief do operador; cada razão WCAG foi computada contra o fundo E contra o card,
   e os accents de módulo desceram até o primeiro L que cruza 4,5:1. Tabela no ADR-0045.

---

## 3. As cinco cópias derivadas da paleta

Mudam **no mesmo passo**, senão divergem:

```
services/frontend/src/app/tokens.css            (SSoT, é o que renderiza)
  → services/frontend/.design-sync/ds-styles.css   (GERADO, receita em .design-sync/NOTES.md)
  → services/frontend/src/lib/shell/shell.config.ts (espelha os accents à mão, 11 hits)
  → saru-docs .../20_identidade_visual_consolidada.md §4  (espelho documental)
  → saru-docs/mkdocs.yml  `accent: amber`            (última sobrevivência do Apex Gold fora do app)
```

---

## 4. Gaps estruturais, fechar na mesma passada

| # | Gap | Evidência |
|---|---|---|
| G1 | **Tokens fantasma fora do gate** | `VideoSyncWidget.module.css:4,5,18,41,53` usa `--surface-card`, `--surface-border`, `--text-dim`, namespace que **não existe**. `scripts/check-tokens.mjs` só policia `^--(saru-\|accent)`, então passam limpos e renderizam pelo fallback hardcoded. **Numa troca de paleta esses componentes congelam na paleta velha, em silêncio.** Consertar o componente E alargar o gate |
| G2 | **Sem escala de z-index** | 12 usos crus, de `10` a `99999` |
| G3 | **`[data-module="lts"]` sem preset** | Usado em `LtsView.tsx:18`; herda o laranja do SFL por acidente. 8 valores usados, 7 definidos |
| G4 | **SKILL.md fora de sincronia** | `~/.claude/skills/saru-frontend-design-system/SKILL.md` prescreve `--bg-flat`, `--bg-surface`, `--border-subtle`, `--accent-telemetry`, **nenhum existe**. Quem seguir a skill ao pé da letra escreve exatamente o bug que o `check-tokens.mjs` foi criado para pegar |

### Cor hardcoded, 318 ocorrências em 44 arquivos, só a 3ª classe é alvo

- ✅ **Legítimo:** `lib/channelColors.ts` e canvas em geral. `ctx.strokeStyle = 'var(--accent)'` é
  inválido e o browser ignora calado; o arquivo já resolve via `resolveColor`. Não tocar.
- 🟡 **Fallback redundante:** `var(--saru-surface-raised, #161a22)`, o token existe, o hex vai
  divergir na troca. Limpar.
- 🔴 **Violação real:** `LtsSetupView.tsx` (26), `LiveTelemetryChart.tsx` (23, paleta Tailwind
  escrita à mão), `VideoSyncWidget.module.css` (38).

---

## 5. Terreno (medido, para não redescobrir)

| Item | Estado |
|---|---|
| SSoT | `services/frontend/src/app/tokens.css`, 124 linhas, **100% HSL, zero hex** |
| Framework | **Sem Tailwind, sem shadcn.** CSS Modules (48 arquivos) + gate `npm run check:tokens` |
| Chaveamento | `[data-module]` (accent por módulo) + `[data-theme]` (flip de superfície), pintados em `lib/shell/AppShell.tsx:102-104` |
| Fontes | Outfit (display) + Inter (data) via `next/font/google`, self-host. `globals.css:7` **proíbe** reintroduzir `@import` do Google Fonts |
| `prefers-reduced-motion` | Já tratado (`tokens.css:122-124`) |
| Portal | `saru-docs/mkdocs.yml`: Material, `scheme: slate`, `accent: amber`, **zero CSS custom**, trocar é one-liner |

---

## 6. Ferramentas

| Recurso | Uso |
|---|---|
| `anthropic-skills:brand-guidelines` + `theme-factory` | escala de tokens a partir das cores medidas |
| `dataviz` (skill) | **obrigatória**, resolve as travas 1 e 2 do §2 |
| `saru-frontend-design-system` (skill) | ⚠️ **corrigir o G4 antes de usar** |
| `frontend-auditor` (agent, read-only) | auditoria pós-mudança |

---

## 7. Ordem sugerida, **executada em 2026-08-13**

1. ✅ 7 HSL corrigidos no `saru-docs` (pushado na develop, `45d0b1d`).
2. ✅ [ADR-0045](../adr/0045-paleta-da-marca-e-tema-bento.md), **Proposto**.
3. ✅ G1 + gate ampliado (`--surface-*|--text-*|--border-*|--bg-*`) e agora **reprova
   fantasma com fallback**; os 14 do `VideoSyncWidget` remapeados. Testado injetando
   um fantasma: reprova (exit 1) e volta a passar limpo (exit 0).
4. ✅ G2 (escala `--saru-z-*`) e G3 (`[data-module="lts"]`).
5. ✅ G4, `~/.claude/skills/saru-frontend-design-system/SKILL.md` reescrita.
6. ✅ Camada `--saru-brand-*`; `--saru-gold` vira alias depreciado (22 arquivos consomem).
7. ✅ Tema Bento no `[data-theme="solar"]`, com contraste **calculado**, não estimado.
8. ✅ Portal: branch `feature/claude-brand-portal` no `saru-docs`.

**Continuação:** [`PROMPT-agente-design-2026-08-13.md`](PROMPT-agente-design-2026-08-13.md), escala de série de gráfico (`dataviz`), limpeza das 318 cores hardcoded, aplicar o z-index,
regenerar o `.design-sync`, grid Bento de verdade.

> **Gate de saída:** `npm run verify` verde + `frontend-auditor` sem achado + antes/depois das
> telas de telemetria conferidos no olho. Sem isso, não vira PR.
