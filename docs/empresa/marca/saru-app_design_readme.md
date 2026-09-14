---
titulo: "SARU Hub, Design (handoff Claude design)"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/design/README.md"
status: "stale"
area: "ui_marca"
---

# SARU Hub, Design (handoff Claude design)

Design canônico do **Hub Shell** (o *chrome* do front): module rail + top bar + view-tabs +
um content slot pluggável. Direção **Hybrid** (2026-06-13): dark-first, **FLAT** (sem
gradiente/glow/sombra), HSL em tudo, **Outfit** (títulos) + **Inter** (dados). Accent por
módulo (Layer B) + tema Solar (daylight).

## Onde vive (implementação fiel, verificado 2026-06-26)

| Peça | Local | Status vs handoff |
|---|---|---|
| **Tokens (SSoT)** | `services/frontend/src/app/tokens.css` | **idêntico** |
| **Shell** | `services/frontend/src/lib/shell/` (AppShell · ModuleRail · TopBar · ViewTabs · shell.config) | CSS **idêntico**; `.tsx` diferem só na fiação |
| **Mockup interativo** | `mockup/SARU Hub Shell.html` (espelho vanilla, fake data) | referência |
| **Screenshots** | `screenshots/` | referência visual |

As diferenças nos `.tsx` são exatamente a fiação que o handoff marcou como *"Claude Code: você é
dono disso"*, Next `<Link>` (em vez de `<a>`), estado `ModuleId | null` (home sem módulo ativo),
tipo `React.ReactElement`, **+ 1 view extra `track`** (Track Builder, produto SD). Sem deriva visual.

## Regra de coerência (anti-monstro)

- **Um shell, um front-end.** O shell **não tem estado** (props + callbacks; routing/Zustand é do
  app). Não criar front-ends/chrome paralelos, ver ADRs em `../adr/`.
- Adicionar um produto = **1 linha em `MODULES`** (`shell.config.ts`) + **1 bloco `[data-module]`**
  em `tokens.css`. Cores nunca no código de componente, são data-driven (`data-module`).
- Acessibilidade e movimento (focus ring Apex-Gold, `prefers-reduced-motion`) vêm dos tokens.

> Os 5 produtos canônicos (lts/sa/sd/crm/erp) e suas cores: ver `../ARCHITECTURE.md` §4.2.
