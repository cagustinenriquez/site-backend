.PHONY: migrate import-data check-uv docker-build docker-run docker-up docker-down docker-logs help install install-dev run test clean lint format setup init-data

help:
	@echo "Site Backend - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Complete setup (clone, install, generate .env)"
	@echo "  make install        - Install production dependencies (uv sync --no-dev)"
	@echo "  make install-dev    - Install with dev dependencies (uv sync)"
	@echo ""
	@echo "Development:"
	@echo "  make run            - Run development server with auto-reload"
	@echo "  make test           - Run test suite"
	@echo "  make lint           - Check code with ruff/flake8"
	@echo "  make format         - Format code with black/isort"
	@echo ""
	@echo "Data & Database:"
	@echo "  make migrate        - Create/update database tables (alembic upgrade head)"
	@echo "  make import-data    - Copy data/*.json into the database"
	@echo "  make init-data      - Initialize sample data"
	@echo "  make clean-data     - Clear data/posts.json"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up      - Build and start with docker compose"
	@echo "  make docker-down    - Stop docker compose services"
	@echo "  make docker-logs    - Follow container logs"
	@echo "  make docker-build   - Build the image only"
	@echo "  make docker-run     - Run the image with docker run"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove cache, .pyc, virtual env artifacts"
	@echo "  make clean-all      - Full clean including .env"

check-uv:
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }

setup: create-env install-dev migrate
	@echo ""
	@echo "✅ Setup complete!"
	@echo "Run 'make run' to start the server"

create-env:
	@if [ ! -f .env ]; then \
		cp .env.example .env 2>/dev/null || echo "SECRET_KEY=your-secret-key-here" > .env; \
		echo "✅ .env file created"; \
	else \
		echo "ℹ️  .env already exists"; \
	fi

install: check-uv
	@echo "Installing dependencies..."
	uv sync --no-dev
	@echo "✅ Dependencies installed"

install-dev: check-uv
	@echo "Installing development dependencies..."
	uv sync
	@echo "✅ Dev dependencies installed"

run:
	@echo "Starting development server at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
	uv run python main.py

migrate:
	@echo "Applying database migrations..."
	uv run alembic upgrade head

import-data:
	@echo "Importing data/*.json into the database..."
	uv run python scripts/import_json_data.py

test:
	@echo "Running tests..."
	uv run pytest -v

test-watch:
	@echo "Running tests in watch mode..."
	uv run pytest -v --tb=short -k "test_" --looponfail

lint:
	@echo "Linting code..."
	-uv run ruff check .
	-uv run flake8 app/ tests/ --max-line-length=100

format:
	@echo "Formatting code..."
	uv run black app/ tests/ main.py
	uv run isort app/ tests/ main.py

init-data:
	@if [ ! -d data ]; then \
		mkdir -p data; \
	fi
	@if [ ! -f data/posts.json ]; then \
		uv run python -c "import json; json.dump({'welcome-to-my-blog': {'id': '1', 'slug': 'welcome-to-my-blog', 'title': 'Welcome to My Blog', 'content': 'This is the first blog post on agustinenriquez.dev.', 'excerpt': 'Welcome to agustinenriquez.dev blog', 'tags': ['welcome', 'intro'], 'date': '2026-08-28T00:00:00'}}, open('data/posts.json', 'w'), indent=2)"; \
		echo "✅ Sample data initialized"; \
	else \
		echo "ℹ️  data/posts.json already exists"; \
	fi

clean-data:
	@echo "Clearing data/posts.json..."
	rm -f data/posts.json
	@echo "✅ Data cleared"

clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".venv" -o -name "venv" -o -name "env" 2>/dev/null | grep -v ".git" | xargs rm -rf 2>/dev/null || true
	@echo "✅ Cleaned"

clean-all: clean
	@echo "Full clean including .env..."
	rm -f .env
	rm -f data/posts.json
	@echo "✅ Full clean complete"

install-lint-tools:
	@echo "Installing linting tools..."
	uv add --dev ruff flake8 black isort
	@echo "✅ Lint tools installed"

docker-build:
	@echo "Building Docker image..."
	docker build -t site-backend:latest .

docker-run: create-env
	@echo "Running in Docker at http://localhost:8000 ..."
	docker run --rm -p 8000:8000 --env-file .env -v site-backend-data:/app/data site-backend:latest

docker-up: create-env
	docker compose up -d --build
	@echo "✅ Running at http://localhost:8000 (logs: make docker-logs)"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f api

.DEFAULT_GOAL := help
