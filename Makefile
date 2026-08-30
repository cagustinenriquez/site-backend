.PHONY: help install install-dev run test clean lint format setup init-data

help:
	@echo "Site Backend - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Complete setup (clone, install, generate .env)"
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install with dev dependencies (testing, linting)"
	@echo ""
	@echo "Development:"
	@echo "  make run            - Run development server with auto-reload"
	@echo "  make test           - Run test suite"
	@echo "  make lint           - Check code with ruff/flake8"
	@echo "  make format         - Format code with black/isort"
	@echo ""
	@echo "Data & Database:"
	@echo "  make init-data      - Initialize sample data"
	@echo "  make clean-data     - Clear data/posts.json"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Remove cache, .pyc, virtual env artifacts"
	@echo "  make clean-all      - Full clean including .env"

setup: create-env install init-data
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

install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

install-dev:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"
	@echo "✅ Dev dependencies installed"

run:
	@echo "Starting development server at http://localhost:8000"
	@echo "API docs available at http://localhost:8000/docs"
	python main.py

test:
	@echo "Running tests..."
	pytest -v

test-watch:
	@echo "Running tests in watch mode..."
	pytest -v --tb=short -k "test_" --looponfail

lint:
	@echo "Linting code..."
	-ruff check .
	-flake8 app/ tests/ --max-line-length=100

format:
	@echo "Formatting code..."
	black app/ tests/ main.py
	isort app/ tests/ main.py

init-data:
	@if [ ! -d data ]; then \
		mkdir -p data; \
	fi
	@if [ ! -f data/posts.json ]; then \
		python -c "import json; json.dump({'welcome-to-my-blog': {'id': '1', 'slug': 'welcome-to-my-blog', 'title': 'Welcome to My Blog', 'content': 'This is the first blog post on agustinenriquez.dev.', 'excerpt': 'Welcome to agustinenriquez.dev blog', 'tags': ['welcome', 'intro'], 'date': '2026-08-28T00:00:00'}}, open('data/posts.json', 'w'), indent=2)"; \
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
	pip install ruff flake8 black isort
	@echo "✅ Lint tools installed"

docker-build:
	@echo "Building Docker image..."
	docker build -t site-backend:latest .

docker-run:
	@echo "Running in Docker..."
	docker run -p 8000:8000 site-backend:latest

.DEFAULT_GOAL := help
