.PHONY: up down setup migrate reset doctor test fmt psql

up:            ## sobe o Postgres da PoC
	docker compose --env-file .env up -d
	@echo "aguardando healthcheck..."
	@until [ "$$(docker inspect -f '{{.State.Health.Status}}' saru-poc-postgres 2>/dev/null)" = healthy ]; do sleep 1; done
	@echo "postgres pronto"

down:          ## para o Postgres (mantem o volume)
	docker compose down

reset:         ## derruba tudo, INCLUSIVE o volume de dados
	docker compose down -v

setup:         ## venv + deps + .env
	uv sync --extra dev
	@test -f .env || cp .env.example .env

migrate:       ## aplica as migrations pendentes
	uv run saru-poc migrate

doctor:        ## inventaria o acervo e confere o ambiente
	uv run saru-poc doctor

psql:
	psql "postgresql://$${SARU_PG_USER:-saru}:$${SARU_PG_PASSWORD:-saru}@127.0.0.1:$${SARU_PG_PORT:-5442}/$${SARU_PG_DB:-saru_poc}"

test:
	uv run pytest -q

fmt:
	uv run ruff format src tests && uv run ruff check --fix src tests

web-setup:     ## instala as deps do frontend
	cd web && npm install

web:           ## sobe o dev server do frontend (porta 5177)
	cd web && npm run dev

web-build:
	cd web && npm run build
