.PHONY: up down logs migrate seed demo-data backend-test backend-lint backend-typecheck frontend-install frontend-build frontend-typecheck evals smoke-test verify mlflow

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.scripts.seed

demo-data:
	python scripts/generate_demo_data.py

backend-test:
	cd backend && pytest

backend-lint:
	cd backend && ruff check .

backend-typecheck:
	cd backend && mypy app

frontend-install:
	cd frontend && npm install

frontend-build:
	cd frontend && npm run build

frontend-typecheck:
	cd frontend && npm run typecheck

evals:
	cd backend && python -m app.scripts.run_evals

smoke-test:
	cd backend && python -m app.scripts.smoke

verify: demo-data backend-lint backend-typecheck backend-test frontend-typecheck frontend-build

mlflow:
	mlflow ui --backend-store-uri ./mlruns --port 5000
