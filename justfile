# Justfile for pymarktools development tasks

# Show available tasks
default:
    @just --list

# Install development dependencies
install:
    uv sync --all-extras --dev

# Run all quality checks (matches CI)
check: type-check lint format-check mdformat-check test

# Run type checker
type-check:
    uv run ty check

# Run linter
lint:
    uv run ruff check src/pymarktools tests

# Run linter with auto-fix
lint-fix:
    uv run ruff check src/pymarktools tests --fix

# Check formatting
format-check:
    uv run ruff format --check src/pymarktools tests

# Format code
format: mdformat
    uv run ruff format src/pymarktools tests

# Check markdown formatting
mdformat-check:
    uv run mdformat --check .

# Format markdown files
mdformat:
    uv run mdformat .

# Run tests
test:
    uv run pytest

# Run tests with coverage
test-cov:
    uv run pytest --cov=src/pymarktools --cov-report=term-missing

# Run tests with coverage and generate HTML report
test-cov-html:
    uv run pytest --cov=src/pymarktools --cov-report=html

# Run pre-commit hooks on all files
pre-commit:
    uv run pre-commit run --all-files

# Install pre-commit hooks
pre-commit-install:
    uv run pre-commit install

# Run tests via pre-commit (manual stage)
test-pre-commit:
    uv run pre-commit run pytest --hook-stage manual

# Build the package
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist/
    rm -rf build/
    rm -rf *.egg-info/
    rm -rf htmlcov/
    rm -f coverage.xml
    rm -f .coverage

# Run the CLI for quick testing
cli *args:
    uv run pymarktools {{args}}

# Set up development environment from scratch
setup: install pre-commit-install
    @echo "✅ Development environment setup complete!"
