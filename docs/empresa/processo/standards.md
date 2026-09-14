---
titulo: "SARU, Padrões de Engenharia"
data: "2026-08-11"
origem: "_arquivo/saru-app/docs/STANDARDS.md"
status: "vigente"
area: "arquitetura_software"
---

# SARU, Padrões de Engenharia

> SoT de convenções de código cross-repo do ecossistema SARU. Vale para os **7 repos**
> ativos. Cada repo herda daqui; divergência só com justificativa no `CLAUDE.md` /
> `AGENTS.md` do repo. Memória global: `SGM.md` (raiz do workspace).
>
> **Regras globais do operador** (Git Flow, commits, sudo, modelo): `~/.claude/CLAUDE.md`.
> **Regras por stack já existentes** (não duplicar, apontar): `<repo>/.claude/rules/`.
> Este doc consolida o que é específico de SARU.

---

## 1. Topologia

NÃO existe monorepo. **7 repos** git independentes; a física vive em `saru-physics-py` /
`saru-physics-jl` (ex-`saru-core`/`saru-core-jl`, o **pacote pip continua `saru-core`**).
O engine consome a física por **submódulo git**, não por dependência de path editable:

```gitmodules
[submodule "services/telemetry-api/vendor/saru-core"]
	path = services/telemetry-api/vendor/saru-core
	url = https://github.com/SARUSySLab/saru-physics-py.git
	branch = develop
```

Domínios em `SARU/` (pós-reorg 2026-07-15, o nível `platform/` foi **extinto**):

| Camada | Repos |
|---|---|
| raiz do workspace | `saru-app` · `saru-physics-py` · `saru-physics-jl` · `saru-telemetry-gt7` · `saru-KB` · `saru-docs` (desktop-app arquivado 2026-06-27; ghost telemetry-service deletado 2026-07-05) |
| `partnerships/` | `lts-copatruck` · `lts-hase` |

Mapa completo: [`architecture/system-overview.md`](architecture/system-overview.md).

---

## 2. Árvore canônica por linguagem

### Python (lib ou serviço), layout `src/`
```
<repo>/
  src/<pkg>/            código (import absoluto; layout src/ evita ImportError ambíguo)
  tests/{unit,integration,smoke}/
  pyproject.toml        SSoT de build/deps/ruff/mypy/pytest (PEP 621). Sem setup.py/requirements.txt duplicado
  uv.lock               lock determinístico (uv)
  .python-version       pin (3.11 libs/produtos; 3.12 serviços do gateway)
  README.md  CLAUDE.md  (ou AGENTS.md)
```

### FastAPI (serviço backend), domain-driven
```
src/<svc>/
  api/                  routers (1 arquivo por recurso), deps, schemas
  application/          casos de uso / services (lógica de negócio)
  domain/               entidades/modelos puros (sem I/O)
  infra/                database, datasources, config, seeding, mapping
  main.py               app factory: CORS, routers, lifespan
```

### Next.js 15+/React 19 (frontend), feature-first + hub modular
```
services/frontend/src/
  app/(public)/ (hub)/  App Router: rotas; (hub)/layout.tsx = AppShell
  components/            UI compartilhada
  features/<prod>/       produto plugável: views/ api/client.ts store.ts contract.ts
  lib/{store,query,shell}  Zustand root + TanStack Query + AppShell
```
> Estrutura travada do hub: [`ARCHITECTURE.md` §4](ARCHITECTURE.md). Next 16 tem breaking
> changes, ler `node_modules/next/dist/docs/` antes de editar (ver `services/frontend/AGENTS.md`).

### Julia (saru-core-jl)
```
src/SaruCore.jl  +  Project.toml (deps + compat)  +  test/runtests.jl
```

### Rust (telemetry-processor futuro)
```
src/  +  Cargo.toml  +  Cargo.lock  +  benches/  tests/
```

### C++/pybind11 (suspension-solver)
```
src/  include/  CMakeLists.txt  Makefile  python/  tests/
```
> `_deps/` e `build/` NUNCA commitados (vêm do CMake FetchContent).

---

## 3. Tooling, config canônica

Fonte de verdade = `saru-core/pyproject.toml`. Copiar, não reinventar.

| Ferramenta | Config | Gate |
|---|---|---|
| **ruff** | `line-length=100`, `target=py311`, select `E,F,I,N,B,UP,ANN,S,C4,SIM,RUF` | zero erro |
| **mypy** | `strict=true`, `python_version=3.11` | zero erro em domínio |
| **pytest** | `testpaths=["tests"]`, `--strict-markers --strict-config`, markers `integration/slow` |, |
| **coverage** | `--cov-fail-under=85` em módulos de domínio | ≥85% |
| **uv** | `uv sync` / `uv.lock` commitado | lock atualizado |

---

## 4. .gitignore, sempre ignorar

```gitignore
# Python
__pycache__/  *.py[cod]  *.egg-info/  .venv/  .pytest_cache/  .mypy_cache/  .ruff_cache/
.coverage  htmlcov/  .cache/
# Node
node_modules/  .next/  dist/  *.tsbuildinfo
# C++/CMake
build/  _deps/  *.so  *.o
# MATLAB
slprj/  codegen/  *.asv  *.slxc
# Dados/saída (nunca commitar)
output/  data/raw/  *.hdf5
# Env/segredos
.env  .env.*  !.env.example  *.credentials*
```

---

## 5. CI, pipeline mínimo (GitHub Actions)

Todo repo Python: `lint (ruff) → type-check (mypy) → test (pytest+coverage)`. Template de
referência = `saru-lts-generic/.github/workflows/ci.yml` (jobs kernel/backend/smoke).
Dispara em `push`/`pull_request` para `main`, `develop`, `release/*`, `hotfix/*`.

---

## 6. Docker

Multi-stage, imagem final non-root, `HEALTHCHECK`, `.dockerignore` obrigatório, versão de base
pinada (nunca `latest`, exceção atual: `minio:latest`, pendência de pin). `COPY` específico,
nunca `COPY . .` na imagem final. Detalhe: [`architecture/deployment.md`](architecture/deployment.md).

---

## 7. GitHub Flow + commits

Para o MVP, SARU usa **GitHub Flow** (ADR-0012), não GitFlow clássico:

- `main` protegida e sempre demonstrável;
- branches curtas `feat/*`, `fix/*`, `docs/*`, `chore/*`, `research/*`;
- PR obrigatório com CI verde;
- CODEOWNERS para física, produto, plataforma e docs;
- sem self-merge em física, contratos, auth, segurança ou claims comerciais;
- Conventional Commits, título EN imperativo ≤72c, corpo só o porquê;
- tags SemVer: `v0.1.0-alpha.N`, `v0.1.0-beta.N`, `v0.1.0`.

`develop` existe apenas como transição nos repos atuais até a migração para a nova organização.

---

## 8. Integração de boas práticas externas

> Espaço reservado para consolidar conteúdo de pesquisa/boas-práticas (cursos, Instagram eng,
> blogs, papers) à medida que chega. Cada item: o que é, por que adotar, onde aplica nos repos
> SARU. Não inflar, só o que vira regra real entra aqui ou vira `.claude/rules/`.
