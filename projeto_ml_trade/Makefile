.PHONY: setup install clean test lint format help

# Variables
PYTHON = python3
PIP = pip
STREAMLIT = streamlit

help:
	@echo "Available commands:"
	@echo "  make setup      - Set up development environment"
	@echo "  make install    - Install dependencies"
	@echo "  make clean      - Clean up build artifacts"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make run        - Run the application"
	@echo "  make build      - Build package"
	@echo "  make help       - Show this help message"

setup:
	@echo "Setting up development environment..."
	$(PYTHON) setup_env.py
	$(MAKE) install

install:
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt

clean:
	@echo "Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".eggs" -exec rm -rf {} +

test:
	@echo "Running tests..."
	pytest tests/ -v

lint:
	@echo "Running linter..."
	pylint projeto_ml_trade/
	pylint app/

format:
	@echo "Formatting code..."
	black .

run:
	@echo "Running application..."
	$(STREAMLIT) run app_streamlit.py

build:
	@echo "Building package..."
	$(PYTHON) setup.py sdist bdist_wheel

# Development setup
dev-setup: setup
	$(PIP) install -e ".[dev]"
	pre-commit install

# Create directories
create-dirs:
	@echo "Creating project directories..."
	mkdir -p data/dataset
	mkdir -p data/historical
	mkdir -p data/enriched_dataset
	mkdir -p logs

# Environment setup
env-setup:
	@echo "Setting up environment..."
	test -f attribs.env || cp attribs.env.example attribs.env
	@echo "Please edit attribs.env with your settings"

# Full installation
full-install: clean create-dirs env-setup install

# Run with specific environment
run-dev:
	ENVIRONMENT=development $(STREAMLIT) run app_streamlit.py

run-prod:
	ENVIRONMENT=production $(STREAMLIT) run app_streamlit.py

# Documentation
docs:
	@echo "Generating documentation..."
	cd docs && make html

# Security checks
security:
	@echo "Running security checks..."
	bandit -r projeto_ml_trade/
	safety check

# Dependencies
requirements:
	@echo "Updating requirements.txt..."
	pip freeze > requirements.txt

# Default target
all: help
