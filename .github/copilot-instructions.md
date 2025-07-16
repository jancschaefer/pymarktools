## Project Overview

pymarktools is a Python library and CLI for validating and refactoring markdown files with link and image handling.
For contribution workflow and style guidance, see `AGENTS.md` in the project root.
## Style Guide

- Target Python 3.13 with type hints on all public APIs.
- Use NumPy-style docstrings (no inline type hints).
- Follow `snake_case` for functions and variables; `PascalCase` for classes.
- Organize imports in three groups: standard library, third-party, local modules.
- Enforce linting and formatting with Ruff and ty.
- Write tests in `tests/` mirroring the source structure; use pytest and mock external calls.
- The library is intended for use in both CLI and programmatic contexts
- Properly document all public APIs and provide type hints for all functions
- Use `uv` for managing the virtual environment and running commands

## Architecture

The project follows a modular structure:

```
src/pymarktools/
├── __init__.py          # Public API exports
├── cli.py               # Main CLI app entry point with global options
├── state.py             # Global state management for CLI options
├── commands/            # CLI command implementations
│   ├── __init__.py      # Commands module exports
│   ├── check.py         # Link/image validation commands with callback architecture
│   └── refactor.py      # File movement and reference updating
└── core/                # Core business logic
    ├── __init__.py      # Core module exports
    ├── async_checker.py # Base async checker functionality
    ├── gitignore.py     # Git repository and .gitignore handling
    ├── image_checker.py # Image validation with pattern filtering support
    ├── link_checker.py  # Link validation with pattern filtering support
    ├── markdown.py      # Re-exports for backward compatibility
    ├── models.py        # Data classes (LinkInfo, ImageInfo)
    └── refactor.py      # Markdown reference refactoring logic

```

## Workflow Guidelines

### CLI Usage

- Use `uv` for virtual environment and commands: `uv install`, `uv run`, especially `uv run python`.
- Commands follow Typer patterns with shared options in `state.py`.
- Common flags:
    - `--check-external`, `--check-local`, `--fix-redirects`
    - `--include`, `--exclude`, `--parallel`, `--workers`
    - `--quiet` (errors only), `--verbose` (detailed output), default (status + summary)

### Async Processing

- External URL checks use `httpx.AsyncClient` without redirects.
- Use `asyncio.gather()` and semaphores for concurrency.
- Local file checks are synchronous via `pathlib.Path`.

### Refactoring

- File moves update markdown references using `FileReferenceManager`.
- Respect `.gitignore` patterns by default; override with `--no-follow-gitignore`.

### Color Output

- Use automated color detection; fallback to plain text.
- Status indicators:
    - ✓ valid
    - ✗ broken
    - ⚠ warnings

### Changelog

- When adding, changing, or removing features, update the `CHANGELOG.md` file with a clear description of the change, the reason for it, and any relevant context.
- Use the format: `## [version] - [date]` (e.g., `## [0.2.0] - 2025-07-08`).
    - Separate changes into sections: `Added`, `Changed`, `Removed`, `Fixed`, etc.
- For unreleased changes, use `[unreleased]` as the version and date.
- Follow the existing changelog structure for consistency.

### Testing

- Use pytest for all tests
- Test files are organized to mirror the source structure
- Mock HTTP requests in tests to avoid external dependencies
- Use `tempfile` for isolated test environments
- Comprehensive test coverage includes edge cases and error conditions

## Common Tasks

### Adding New Commands

1. Create a new function in the appropriate commands module
1. Decorate with `@app_name.command("command-name")`
1. Define parameters using typer's type annotations and options
1. Include both callback-level and command-level options for flexibility
1. Implement the command logic using core services
1. Follow the established pattern for option precedence (command overrides callback)

### Adding New Core Functionality

1. Determine the appropriate core module (`models.py`, `link_checker.py`, `image_checker.py`, `gitignore.py`, or `refactor.py`)
1. Implement the functionality as instance methods in existing classes or as new classes
1. Write comprehensive tests in `tests/test_core/`
1. Export public APIs through `__init__.py`
1. Update type hints and documentation
1. Update the changelog

## Testing and Running

### Development Setup

```bash
# Install in development mode
uv install -e .

# Install dev dependencies 
uv install pytest pytest-cov
```

### Running Python

```bash
uv run python ... # Always use `uv run` to ensure the correct environment is used
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific tests
uv run pytest tests/test_core/test_markdown.py

# Run tests with coverage
uv run pytest --cov=src/pymarktools
uv run pytest --cov=src/pymarktools --cov-fail-under=80

```

### Running Quality Checks

#### Typechecker

```bash
uv run ty check
```

#### Ruff

```bash
uv run ruff check src/pymarktools tests --fix
uv run ruff format --check src/pymarktools tests
```
