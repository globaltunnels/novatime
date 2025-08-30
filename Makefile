# NovaTime Development Makefile
.PHONY: help install clean test lint format check-all build-frontend build-backend run-frontend run-backend migrate setup-db

# Default target
help:
	@echo "NovaTime Development Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Complete project setup (backend + frontend)"
	@echo "  make setup-db       - Set up PostgreSQL database"
	@echo "  make install         - Install all dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make run            - Run both frontend and backend"
	@echo "  make run-frontend   - Run frontend development server"
	@echo "  make run-backend    - Run backend development server"
	@echo "  make migrate        - Run Django migrations"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           - Run all linting tools"
	@echo "  make format         - Format code with Black and Prettier"
	@echo "  make check-all      - Run all quality checks"
	@echo "  make test           - Run all tests"
	@echo ""
	@echo "Build:"
	@echo "  make build          - Build both frontend and backend"
	@echo "  make build-frontend - Build frontend for production"
	@echo "  make build-backend  - Build backend (collect static)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Clean build artifacts and caches"

# Setup commands
setup: setup-db install migrate
	@echo "✅ NovaTime setup complete!"

setup-db:
	@echo "🔧 Setting up PostgreSQL database..."
	@cd backend && python manage.py dbshell < setup_db.sql 2>/dev/null || echo "Database setup script not found. Please run manually."

install:
	@echo "📦 Installing dependencies..."
	@cd backend && pip install -r requirements.txt
	@cd frontend && npm install
	@echo "✅ Dependencies installed!"

# Development commands
run:
	@echo "🚀 Starting NovaTime development servers..."
	@make -j2 run-backend run-frontend

run-frontend:
	@echo "🎨 Starting frontend development server..."
	@cd frontend && npm run dev

run-backend:
	@echo "⚙️  Starting backend development server..."
	@cd backend && python manage.py runserver 0.0.0.0:8000

migrate:
	@echo "🗄️  Running Django migrations..."
	@cd backend && python manage.py migrate

# Code quality commands
lint:
	@echo "🔍 Running code quality checks..."
	@echo "Frontend linting:"
	@cd frontend && npm run lint
	@echo "Backend linting:"
	@cd backend && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@cd backend && flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	@echo "✅ Linting complete!"

format:
	@echo "🎨 Formatting code..."
	@echo "Formatting Python code:"
	@cd backend && black .
	@cd backend && isort .
	@echo "Formatting JavaScript/TypeScript code:"
	@cd frontend && npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,css,md}"
	@echo "✅ Code formatting complete!"

check-all: lint test
	@echo "✅ All quality checks passed!"

test:
	@echo "🧪 Running tests..."
	@echo "Backend tests:"
	@cd backend && python manage.py test --verbosity=2
	@echo "Frontend tests:"
	@cd frontend && npm test -- --run
	@echo "End-to-end tests:"
	@npx playwright test
	@echo "✅ All tests completed!"

# Build commands
build: build-frontend build-backend
	@echo "✅ Build complete!"

build-frontend:
	@echo "🔨 Building frontend..."
	@cd frontend && npm run build

build-backend:
	@echo "🔨 Building backend..."
	@cd backend && python manage.py collectstatic --noinput

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	@cd frontend && rm -rf dist node_modules/.vite
	@cd backend && find . -type d -name __pycache__ -exec rm -rf {} +
	@cd backend && find . -name "*.pyc" -delete
	@cd backend && find . -name "*.pyo" -delete
	@cd backend && find . -name "*.pyd" -delete
	@cd backend && rm -rf .mypy_cache .pytest_cache
	@echo "✅ Cleanup complete!"

# Development shortcuts
backend-shell:
	@cd backend && python manage.py shell

frontend-shell:
	@cd frontend && npm run dev -- --open

# Database management
db-makemigrations:
	@cd backend && python manage.py makemigrations

db-migrate:
	@cd backend && python manage.py migrate

db-reset:
	@echo "⚠️  This will reset the database. Are you sure? (y/N)"
	@read -p "" confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		cd backend && python manage.py reset_db --noinput; \
		make migrate; \
		echo "✅ Database reset complete!"; \
	else \
		echo "❌ Database reset cancelled."; \
	fi

# Quality gates
quality-gate: check-all
	@echo "🎯 Quality gate passed! Ready for commit."

pre-commit: format lint test
	@echo "✅ Pre-commit checks passed!"

# Docker commands (if using Docker)
docker-build:
	@echo "🐳 Building Docker containers..."
	@docker-compose build

docker-up:
	@echo "🐳 Starting Docker containers..."
	@docker-compose up -d

docker-down:
	@echo "🐳 Stopping Docker containers..."
	@docker-compose down

# Help for specific commands
help-setup:
	@echo "Setup Commands:"
	@echo "  make setup          - Complete project setup"
	@echo "  make setup-db       - Set up PostgreSQL database"
	@echo "  make install        - Install all dependencies"
	@echo "  make migrate        - Run Django migrations"

help-dev:
	@echo "Development Commands:"
	@echo "  make run            - Run both frontend and backend"
	@echo "  make run-frontend   - Run frontend dev server"
	@echo "  make run-backend    - Run backend dev server"
	@echo "  make backend-shell  - Open Django shell"
	@echo "  make frontend-shell - Open frontend dev server with browser"

help-quality:
	@echo "Code Quality Commands:"
	@echo "  make lint           - Run all linting tools"
	@echo "  make format         - Format code with Black and Prettier"
	@echo "  make check-all      - Run all quality checks"
	@echo "  make test           - Run all tests"
	@echo "  make quality-gate   - Run quality checks for CI/CD"
	@echo "  make pre-commit     - Run pre-commit checks"