.PHONY: dev test bench deploy lint

dev:
	docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d postgres redis
	@if [ -f playground/package.json ]; then (cd playground && npm run dev &) ; fi
	uvicorn server.app:app --reload

test:
	pytest

lint:
	ruff check .

bench:
	python -m bench.run

deploy:
	docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build
