.PHONY: up down test migrate lint format install-hooks dev-setup

up:
	docker compose up --build -d

down:
	docker compose down

test:
	cd backend && pytest -v

migrate:
	cd backend && alembic upgrade head

lint:
	cd backend && ruff check . && ruff format --check .

format:
	cd backend && ruff check --fix . && ruff format .

install-hooks:
	pre-commit install

dev-setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r backend/requirements.txt
	.venv/bin/pip install pre-commit
	.venv/bin/pre-commit install
	cp -n .env.example .env || true
	cd frontend && npm install
	@echo "✅ Fejlesztői környezet kész!"
