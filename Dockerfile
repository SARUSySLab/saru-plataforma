# Build multi-stage: front (node) e API (python) num unico servico Railway.
# Um servico so servindo API + estatico na mesma origem, sem CORS pra
# configurar e sem cookie cross-site: ver docs/deploy-railway.md pro porque.

# ---------- stage 1: build do front (Vite/React) ----------
FROM node:22-alpine AS front

WORKDIR /app/web

# Copia so o manifesto primeiro pra cachear o npm ci entre builds que nao
# mexem em dependencia.
COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ ./
RUN npm run build
# saida: /app/web/dist

# ---------- stage 2: runtime da API (Python) ----------
FROM python:3.14-slim AS api

# uv oficial via imagem distroless da Astral, sem precisar de pip install.
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /uvx /bin/

WORKDIR /app

# Manifesto de dependencia primeiro, de novo pra cache: so reinstala quando
# pyproject.toml/uv.lock mudam, nao a cada alteracao de codigo.
COPY pyproject.toml uv.lock ./

# --extra aim traz o leitor nativo do AiM (.xrk), usado na ingestao de bundle
# via POST /api/gravacoes. E parte do fluxo real de producao, nao so dev.
# --frozen: nunca resolve versao nova aqui, usa exatamente o que esta no lock.
# --no-dev: pytest/ruff nao tem por que ir pra imagem de producao.
RUN uv sync --frozen --no-dev --extra aim

COPY src/ ./src
COPY migrations/ ./migrations
# Catalogo de pista e de canal. Versionado no repo porque producao nao pode
# depender do snapshot do saru-app, que so existe no disco do Lucas: sem isto
# o container sobe com o catalogo vazio e nao ha pista pra escolher na tela.
COPY seeds/ ./seeds

# Dist do front no lugar que src/saru_poc/api.py espera
# (REPO_ROOT/web/dist, ver linha ~427 de api.py).
COPY --from=front /app/web/dist ./web/dist

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8010

# Migration roda no start, antes do uvicorn: o Railway pode reiniciar o
# container a qualquer redeploy, e subir com schema desatualizado quebra
# silencioso em vez de falhar alto. `saru-poc migrate` e no-op quando ja
# esta em dia (ver src/saru_poc/migrate.py).
# $PORT vem do Railway em runtime, por isso shell form (nao exec form/JSON)
# pra variavel ser expandida.
# migrate e os dois seeds sao idempotentes, entao rodam a cada boot: schema ou
# catalogo desatualizado quebra silencioso, e falhar alto no start e melhor.
CMD uv run saru-poc migrate \
 && uv run saru-poc seed-pistas \
 && uv run saru-poc seed \
 && uv run uvicorn saru_poc.api:app --host 0.0.0.0 --port ${PORT:-8010}
