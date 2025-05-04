# Makefile for AGENT_TOOLING project

PYTHON=python
PIP=pip

# Install all project dependencies
install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Format the code with black
format:
	$(PYTHON) -m black src tests

# Run all tests
test:
	PYTHONPATH=src pytest

# Build package distributions
build:
	$(PYTHON) -m build

# Rebuild requirements.txt from pyproject.toml
compile-requirements:
	pip-compile pyproject.toml --output-file=requirements.txt

# Clean build artifacts
clean:
	rm -rf dist
	rm -rf *.egg-info
	rm -rf __pycache__ src/__pycache__ tests/__pycache__

# publis the package to PyPI
publish: clean test build
	$(PYTHON) -m twine upload dist/*
