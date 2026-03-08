#!/bin/bash

# Quality checks script
# Runs the same checks as pre-commit hooks:
# - ruff format (code formatting)
# - ruff check (linting)
# - mypy (type checking)

set -e

echo "Running code quality checks..."
echo

echo "1. Checking code formatting with ruff..."
uv run ruff format .

echo
echo "2. Running ruff linting..."
uv run ruff check .

echo
echo "3. Running type checking with mypy..."
uv run mypy src/

echo
echo "✓ All quality checks passed!"
