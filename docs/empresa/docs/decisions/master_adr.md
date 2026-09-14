---
titulo: "SARU Ecossistema, Master Architecture Decision Record (ADR)"
data: "2026-07-18"
origem: "_arquivo/saru-KB/40_software_arch/adr/MASTER_ADR.md"
status: "stale"
area: "arquitetura_software"
---

# SARU Ecossistema, Master Architecture Decision Record (ADR)

> **SoT das decisões de arquitetura cross-ecossistema, cópia canônica ÚNICA (aqui, `saru-KB`).**
> Modelo **single-SoT** (ADR-2026-07-15, §7): os repos NÃO carregam réplica deste arquivo, carregam
> um **stub-ponteiro** em `docs/adr/MASTER_ADR.md`. `saru-app` mantém seus ADRs locais `0001`-`0014`
> (repo-scoped). Estado vivo do ecossistema: `SGM.md` (raiz `SARU/`).
> Última revisão: **2026-07-15** (migração p/ single-SoT; nomes de repo = org SARUSySLab).

## Convenção de ADRs (ecossistema SARU)

- **ADRs locais do repo** → `<repo>/docs/adr/NNNN-slug.md`, numerados `0001+`, formato
  *Status / Contexto / Decisão / Consequências*, **imutáveis** (mudou → novo ADR c/ `Substitui:`).
- **MASTER_ADR (este)** → overview cross-ecossistema; decisões que valem p/ mais de um repo.
- Números fantasma são proibidos: nunca citar `ADR-009/010/011` como cross-eco, eram apelidos
  de notas do antigo `SARU_GLOBAL_MEMORY.md` (hoje `SGM.md`) e **não** arquivos. Os únicos ADRs
  numerados que existem são os locais do `saru-app` (`0001`-`0014`).

### Mapa de decisões → onde vivem

| Decisão | Fonte |
|---|---|
| Topologia multi-repo híbrido (monorepo rejeitado) | §5 deste doc (ADR-2026-07-05) |
| Storage 4 superfícies (Linux/Windows/Drive/GitHub) | §4 deste doc (ADR-2026-07-03) |
| Sistema de coordenadas ISO 8855 | §2 deste doc |
| Arquitetura 2-tier (QSS síncrono + 14-DOF assíncrono) e SSoT de setup | §3 deste doc · detalhe: saru-app [ADR-0010](https://github.com/SARUSySLab/saru-app) (`0010-vehicle-setup-ssot.md`, aceito 2026-07-01) |
| Borda NestJS + engine Python; multi-serviço; nomes | saru-app ADR-0002 · 0001 · 0003 |
| Cache Redis (nunca SQLite); auth JWT + rotação refresh | saru-app ADR-0004 · 0006 · 0008 (implementada A.2) |
| Dinâmica transiente SD (3-DOF core) · dono do 14-DOF | saru-app ADR-0005 |
| BFF como orquestração de cálculo (fila + SSE) | saru-app ADR-0007 |
| CRM/ERP demo na borda NestJS | saru-app ADR-0009 |
| UI Global Context & Trackside · Org GitHub/MVP docs · DDL single-owner | saru-app ADR-0011 · 0012 · 0013 · 0014 |

## 1. Topologia e Repositórios

- A raiz `SARU/` é o **meta-hub local** do ecossistema: versiona `SGM.md` e audits cross-repo.
  O remote `vitormtt/SARU` foi **deletado** (2026-07-07), o umbrella é local-only.
- `saru-KB/` = repositório independente **`SARUSySLab/saru-KB`** (P&D/conhecimento), gitignored no
  umbrella, como todos os repos aninhados: `platform/*` (saru-app, saru-physics-py, saru-physics-jl) e
  `partnerships/*` (lts-copatruck, lts-hase) têm remote próprio, **sem gitlinks/submodules**.
- `platform/telemetry-service/` era dir-fantasma (TRAP de `git` → umbrella), **deletado na
  Missão S2 (2026-07-05)**. O engine de telemetria de produto é `saru-os/services/telemetry-api`
  (rename → `engine` pendente, saru-os ADR-0003).

## 2. Sistema de Coordenadas, ISO 8855

Toda estrutura física, telemetria vetorial e sistemas de coordenadas globais (Earth-fixed) e
locais (Vehicle-fixed) adotam **ISO 8855**: X para frente, Y para a esquerda, Z para cima.
Evita inversão de sinais entre módulos C++/Python/Julia. (Exceção documentada: o QSS ponto-massa
do saru-core-jl usa SAE J670 **isolado** no harness de validação.)

## 3. Dinâmica Veicular, 2 Tiers (ratificado)

- **Tier síncrono (produto):** lap-time QSS + 3-DOF transiente em Python (`saru-core`), consumido
  pelo engine FastAPI do `saru-os`. É oráculo de regressão e produto ao mesmo tempo.
- **Tier assíncrono (alta fidelidade):** 14-DOF Julia (`saru-core-jl`, MTK acausal), worker de
  fila (BullMQ/Redis via BFF NestJS, resposta SSE). Surrogate neural end-to-end **rejeitado**.
- **SSoT de setup:** rumo `VehicleSetup` master no Julia c/ derivação de contratos (saru-os
  ADR-0010). Grafia canônica **`VehicleSetup`** (2026-07-07).
- ✅ **T-A RESOLVIDA (2026-07-15): contrato de setup é JSON-Schema-only**, saru-app
  **ADR-0013** (`0013-setup-contract-json-schema-only.md`). Evidência: zero consumidores de
  protobuf na stack 100% REST/JSON (pydantic no engine, DTO no BFF, fila JSON) e drift triplo
  comprovado (proto 16 campos × bounds 5 × cópia divergente do frontend). `setup.proto` e o
  `setup_bounds.json` morto foram removidos do saru-app; bounds vivos = arquivo local do
  frontend até derivação do `VehicleSetup` SSoT (ADR-0010, via só-JSON-Schema). **Follow-up
  registrado:** remover `export_protobuf.jl` no `saru-physics-jl` quando sair do freeze.

## 4. Topologia de Armazenamento (4 Superfícies), ADR-2026-07-03

Regras-âncora (espec. original `00_meta/00_STORAGE_ARCHITECTURE.md`, removida no restructure de
2026-07-13, histórico no git do saru-KB):
- **Fonte de verdade por tipo:** código → **GitHub**; conhecimento/pesquisa → **git (saru-KB)**
  espelhado no Drive (espelho = binário/refs + curado); binário grande → **Drive** c/ manifest.
- **Máquinas:** **Linux = dev canônico**; **Windows/SSD = runner VI-CarRealTime + fonte de dados**.
- **Single-writer NTFS:** só o Windows sincroniza NTFS↔nuvem; Linux monta via fstab sem daemon;
  Fast Startup OFF.
- **3-2-1:** SSD=hot, Drive/OneDrive=warm, HD externo=cold; ≥3 cópias/2 mídias/1 offsite.
- Consequências: repos Windows/SSD congelados (snapshot) e reconciliados por-repo; dados VI-CRT em
  `~/Projects/SARU/_shared/vicrt/` (gitignored) + backup Drive. Tooling `scripts/drive-reorg/`
  cumpriu a reorg (R5/P8/R7, 2026-07) e foi **removido**, histórico no git.

## 5. Topologia de Repositórios: Multi-Repo Híbrido, ADR-2026-07-05

**Mantém-se o multi-repo híbrido** (§1); proposta de monorepo (`git-filter-repo` + merge de
históricos) **rejeitada**. Fundamentos: agentes IA (N sessões paralelas, 1-sessão-por-repo,
contexto enxuto; a sessão no umbrella enxerga tudo p/ trabalho cross-repo) · risco/reversibilidade
(filter-repo = hard fork de SHAs; status quo risco zero) · CI por repo já funciona · cadências
comerciais independentes (`lts-copatruck` = entregável de cliente). Fonte "doc2" (deep research)
desqualificada como premissa por alucinações. `Marketing` → remote próprio `vitormtt/SARU-Marketing`.

## 6. Convenções de Código

- **Python/Postgres:** `snake_case` · **TypeScript/NestJS:** `camelCase` (`PascalCase` classes).
- **Inglês obrigatório** em variáveis, branches, docs técnicas e commits (Conventional Commits,
  sem `Co-Authored-By`).

## 7. Modelo de Seguimento do MASTER_ADR, single-SoT (ADR-2026-07-15)

**Decisão:** este arquivo (no `saru-KB`) é a **fonte única** das decisões cross-ecossistema. Os
repos **deixam de manter réplicas**, cada um carrega apenas um **stub-ponteiro** em
`docs/adr/MASTER_ADR.md` + seus **ADRs locais** `NNNN-*.md` (repo-scoped).

**Contexto:** o modelo anterior (réplicas byte-idênticas em `saru-physics-py` e `saru-physics-jl`)
driftou na prática, a auditoria 2026-07-15 achou uma 3ª réplica *vendored*
(`saru-app/services/telemetry-api/vendor/saru-core/docs/adr/MASTER_ADR.md`) defasada em rev
2026-06-29 (números-fantasma já banidos). Réplica = imposto de sync recorrente + risco de
divergência silenciosa. Submódulo/subtree foi rejeitado (ADR-2026-07-05, sem gitlinks).

**Consequências:** (1) `saru-physics-py`/`saru-physics-jl` `docs/adr/MASTER_ADR.md` = stubs;
(2) decisão cross-eco nova = seção datada `ADR-AAAA-MM-DD` **só aqui**; (3) decisão repo-local =
ADR local (skill `/adr` do saru-app); (4) auditoria periódica KB↔repos = backstop. A réplica
vendored resolve-se quando `vendor/saru-core` for re-vendorado do stub.

---
> Novas decisões cross-eco: seção datada aqui (`ADR-AAAA-MM-DD`), nunca número fantasma.
> Repos carregam **stub-ponteiro** (não réplica), ADR-2026-07-15 §7.
