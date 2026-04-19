PYTHON ?= python

.PHONY: install run worker test lint format typecheck audit security up down

install:
	$(PYTHON) -m pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	$(PYTHON) -m app.workers.main

test:
	pytest

lint:
	ruff check .

format:
	black .

typecheck:
	mypy app

audit:
	pip-audit

security:
	bandit -r app

up:
	docker compose up --build

down:
	docker compose down -v
