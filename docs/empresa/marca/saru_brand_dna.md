---
titulo: "SARU Dynamics, Brand DNA & UI Design System"
data: "2026-07-15"
origem: "_arquivo/saru-KB/50_company/SARU_BRAND_DNA.md"
status: "vigente"
area: "marca"
---

# SARU Dynamics, Brand DNA & UI Design System

Este documento serve como a Única Fonte de Verdade (SoT) para a identidade visual e o design system do ecossistema SARU Dynamics.

---

## 1. Conceito Visual (Mascote Saruê), decisão 2026-07-15
Mascote oficial da SARU é o **saruê** (gambá-de-orelha-branca, *Didelphis albiventris*, marsupial brasileiro), na variante **albina**. Decisão do operador (2026-07-15); **substitui** o conceito anterior "Grande Felino Discreto" (superseded).

**Status do logo:** esboço existente em iteração, versão atual ainda "parece rato"; operador gerando variações para ampliar opções de cor. **Paleta #HEX do mascote em definição** (candidatos pendentes). Ao fechar: salvar **SVG master** + PNG transparente ≥1000 px (versões dark/light) em `50_company/brand_assets/` e registrar os #HEX finais neste documento.

Easter eggs de UI abaixo foram desenhados na era felina, **manter o espírito (sutileza técnica), revisar a metáfora** quando o logo do saruê fechar:
- **Padrão de Rosetas** *(legado felino → revisar motivo)*: grid de pontos de fundo na telemetria que se reorganiza de forma orgânica ao passar o mouse.
- **Aceleração Apex** *(revisar constelação)*: contorno dourado sutil no painel do gráfico G-Sum ao atingir $>1.4\text{ G}$ lateral.
- Comando Secreto: digitar `saru` ativa tema exclusivo escuro dourado (manter; trocar micro-ranhuras de "garras" por motivo do saruê).

---

## 2. Tipografia
- Outfit: Utilizada para títulos de alto impacto e chamadas.
- Inter: Utilizada para dados numéricos, tabulares, telemetria e textos corridos.

---

## 3. Cores Corporativas Base (HSL)
Calibradas para alto contraste sob luz solar (Solar Mode) e baixa fadiga visual em boxes escuros (Dark Pit Mode).

- Stealth Dark Base: `hsl(220, 20%, 8%)` (Fundo principal do app)
- Daylight Light Base: `hsl(220, 15%, 96%)` (Fundo principal em modo solar)
- Apex Gold: `hsl(45, 95%, 55%)` (Cor de destaque e branding corporativo)

---

## 4. Paleta de Cores por Módulo (Identidade do Ecossistema)

Cada módulo do ecossistema SARU possui sua cor de acento dedicada e modos escuro (Box) e claro (Solar):

| Módulo | Nome e Função | Accent HSL | Dark Mode Base (Box) | Light Mode Base (Solar) |
|---|---|---|---|---|
| **A. SARU LTS** | Lap Time Simulation (Speed Orange) | `hsl(24, 95%, 53%)` | Fundo: `hsl(24, 15%, 10%)`<br>Texto: `hsl(24, 90%, 90%)` | Fundo: `hsl(24, 20%, 94%)`<br>Texto: `hsl(24, 100%, 25%)` |
| **B. SARU SA** | Lap Analyzer (Telemetry Teal) | `hsl(180, 85%, 45%)` | Fundo: `hsl(180, 20%, 9%)`<br>Texto: `hsl(180, 80%, 90%)` | Fundo: `hsl(180, 30%, 93%)`<br>Texto: `hsl(180, 100%, 20%)` |
| **C. SARU SD** | Vehicle Dynamics (Kinetic Green) | `hsl(135, 80%, 48%)` | Fundo: `hsl(135, 20%, 9%)`<br>Texto: `hsl(135, 80%, 90%)` | Fundo: `hsl(135, 30%, 93%)`<br>Texto: `hsl(135, 100%, 20%)` |
| **D. SARU CRM** | Pit Operations (Strategy Blue) | `hsl(210, 85%, 55%)` | Fundo: `hsl(210, 25%, 10%)`<br>Texto: `hsl(210, 85%, 92%)` | Fundo: `hsl(210, 35%, 94%)`<br>Texto: `hsl(210, 100%, 25%)` |
| **E. SARU ERP** | Inventory Management (Steel Carbon) | `hsl(0, 0%, 75%)` | Fundo: `hsl(0, 0%, 12%)`<br>Texto: `hsl(0, 0%, 95%)` | Fundo: `hsl(0, 0%, 92%)`<br>Texto: `hsl(0, 0%, 20%)` |

---

## 5. Diretrizes de Interface (UI/UX)
- Fidelidade Cromática: Todos os gradientes, glows e estados interativos devem mapear cirurgicamente as cores da tabela acima.
- Micro-interações: Glows e transições suaves de acento no módulo ativo.
- Arquitetura de Estilo: Uso estrito de Vanilla CSS (CSS Modules) para Next.js 15, evitando dependências pesadas e preservando a portabilidade para o Tauri v2.
