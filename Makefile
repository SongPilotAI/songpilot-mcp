.PHONY: format lint test install-dev venv show-venv clean build publish

# Use project venv (venv or .venv) in project root so make works without activating
VENV_DIR := $(if $(wildcard $(CURDIR)/venv),$(CURDIR)/venv,$(CURDIR)/.venv)
PY := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip

# Show venv info for debugging
show-venv:
	@echo "VENV_DIR=$(VENV_DIR)"
	@echo "PY=$(PY)"
	@$(PY) --version 2>/dev/null || echo "Python not found"

# Create venv with Python 3.12
PYTHON ?= python3.12
venv:
	@echo "Creating venv with $(PYTHON)..."
	rm -rf venv .venv
	$(PYTHON) -m venv venv
	$(CURDIR)/venv/bin/pip install --upgrade pip
	$(CURDIR)/venv/bin/pip install -r requirements.txt -r requirements-dev.txt

install-dev:
	$(PIP) install -r requirements.txt -r requirements-dev.txt

format:
	$(PY) -m black src/ tests/
	$(PY) -m isort src/ tests/

lint:
	$(PY) -m ruff check src/ tests/
	$(PY) -m black --check src/ tests/
	$(PY) -m isort --check-only src/ tests/

lint-fix:
	$(PY) -m ruff check --fix src/ tests/
	$(PY) -m black src/ tests/
	$(PY) -m isort src/ tests/

test:
	$(PY) -m pytest tests/ -v

test-cov:
	$(PY) -m pytest tests/ -v --cov=songpilot_mcp --cov-report=term --cov-report=html

# Build package for distribution
build:
	$(PY) -m build

# Publish to PyPI (requires PYPI_API_TOKEN env var)
publish:
	$(PY) -m twine upload dist/*

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the MCP server locally (for testing)
run:
	$(PY) -m songpilot_mcp

# Quick check before committing
check: lint test
	@echo "All checks passed!"
