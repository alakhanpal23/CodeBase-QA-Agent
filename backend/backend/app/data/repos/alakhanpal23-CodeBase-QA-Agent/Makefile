.PHONY: help install dev test clean docker-build docker-run

help: ## Show this help message
	@echo "Codebase QA Agent - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

dev: ## Run development server
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	pytest tests/ -v

test-coverage: ## Run tests with coverage
	pytest tests/ --cov=backend --cov-report=html --cov-report=term

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf backend/app/data/indexes/*
	rm -rf backend/app/data/temp/*
	rm -rf .pytest_cache
	rm -rf htmlcov

docker-build: ## Build Docker image
	docker build -t codebase-qa-agent .

docker-run: ## Run Docker container
	docker-compose up --build

docker-stop: ## Stop Docker container
	docker-compose down

format: ## Format code with black
	black backend/ scripts/ tests/

lint: ## Lint code with flake8
	flake8 backend/ scripts/ tests/

type-check: ## Type check with mypy
	mypy backend/ scripts/

setup-env: ## Setup environment file
	cp env.example .env
	@echo "Please edit .env with your OpenAI API key"

ingest-example: ## Ingest an example repository
	python scripts/ingest_repo.py --url https://github.com/fastapi/fastapi --repo fastapi/fastapi --verbose

query-example: ## Query the example repository
	python scripts/query.py --repo fastapi/fastapi --q "How is routing implemented?" --verbose
