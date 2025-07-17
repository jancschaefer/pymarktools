# Pre-commit Hooks

> [!IMPORTANT]
> **Essential for Code Quality:** Pre-commit hooks are essential for maintaining code quality and ensuring
> your contributions meet the project's standards. They run the same checks as the CI pipeline.

This project uses [pre-commit](https://pre-commit.com/) to run quality checks before each commit. The hooks ensure that
code quality standards are maintained and match the checks run in CI.

## Setup

Pre-commit hooks are automatically installed when you run:

```bash
uv sync --dev
uv run pre-commit install
```

Or using the justfile:

```bash
uv run just setup
```

## Hooks Configured

The following hooks run on every commit:

1. **Ruff Linter** - Automatically fixes linting issues where possible
1. **Ruff Formatter** - Ensures consistent code formatting
1. **Type Checker (ty)** - Validates type annotations
1. **Standard hooks**:
   - Trim trailing whitespace
   - Fix end of files
   - Check YAML/TOML syntax
   - Check for merge conflicts
   - Check for large files
   - Fix mixed line endings

## Manual Execution

Run all hooks on all files:

```bash
uv run pre-commit run --all-files
# or using justfile
uv run just pre-commit
```

Run specific hooks:

```bash
uv run pre-commit run ruff
uv run pre-commit run ty-check
# or using justfile
uv run just lint
uv run just type-check
```

Run tests manually (not included in default commit hooks):

```bash
uv run pre-commit run pytest --hook-stage manual
# or using justfile
uv run just test-pre-commit
```

## Development Tasks with Justfile

This project includes a `justfile` for common development tasks:

```bash
# Show all available tasks
uv run just

# Run all quality checks (matches CI)
uv run just check

# Individual tasks
uv run just type-check
uv run just lint
uv run just format-check
uv run just test

# With auto-fixing
uv run just lint-fix
uv run just format
```

## CI Alignment

These pre-commit hooks align with the CI checks in `.github/workflows/test.yml`:

- **Type checking**: `uv run ty check`
- **Linting**: `uv run ruff check src/pymarktools tests`
- **Formatting**: `uv run ruff format --check src/pymarktools tests`
- **Testing**: `uv run pytest` (manual hook only)

## Bypassing Hooks

> [!CAUTION]
> **Use with Extreme Care:** Bypassing pre-commit hooks should be used sparingly and only when you're certain
> the code is correct. This can lead to CI failures if code quality issues are introduced.

If you need to bypass pre-commit hooks temporarily:

```bash
git commit --no-verify -m "commit message"
```

**Note**: This should be used sparingly and only when you're certain the code is correct.

## Updating Hooks

Update to the latest versions:

```bash
uv run pre-commit autoupdate
```
