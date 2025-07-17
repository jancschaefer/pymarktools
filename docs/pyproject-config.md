# pyproject.toml Configuration Support

This document describes how to configure pymarktools using `pyproject.toml`.

## Configuration Section

Add configuration under the `[tool.pymarktools]` section in your `pyproject.toml`:

```toml
[tool.pymarktools]
# Paths to check (array of strings)
paths = ["src", "docs", "README.md"]

# Check options
timeout = 60
check_external = false
check_local = true
fix_redirects = true
follow_gitignore = true
include_pattern = "*.md"
exclude_pattern = "test_*.md"
parallel = true
fail = true
workers = 4
check_dead_links = true
check_dead_images = true

# Output file for reports
output = "link_report.txt"
```

## Supported Options

All command-line options for the `check` command can be configured in `pyproject.toml`:

| Option              | Type             | Description                               |
| ------------------- | ---------------- | ----------------------------------------- |
| `paths`             | array of strings | Directories or files to check             |
| `timeout`           | integer          | Request timeout in seconds                |
| `output`            | string           | Output file for the report                |
| `check_external`    | boolean          | Check external URLs with HTTP requests    |
| `check_local`       | boolean          | Check if local file links/images exist    |
| `fix_redirects`     | boolean          | Update links with permanent redirects     |
| `follow_gitignore`  | boolean          | Respect .gitignore patterns               |
| `include_pattern`   | string           | File pattern to include                   |
| `exclude_pattern`   | string           | File pattern to exclude                   |
| `parallel`          | boolean          | Enable parallel processing                |
| `fail`              | boolean          | Exit with status 1 if invalid items found |
| `workers`           | integer          | Number of worker threads                  |
| `check_dead_links`  | boolean          | Validate links                            |
| `check_dead_images` | boolean          | Validate images                           |

## Configuration Discovery

pymarktools automatically searches for `pyproject.toml` by walking up the directory tree from the current working
directory until it finds one.

## Priority Order

Configuration values are applied in the following order (highest priority first):

1. **Command-line arguments** - Explicit CLI flags and options
1. **pyproject.toml configuration** - Values from `[tool.pymarktools]` section
1. **Default values** - Built-in defaults

## Examples

### Basic Configuration

```toml
[tool.pymarktools]
paths = ["docs"]
check_external = false
parallel = false
```

```bash
# Uses config values
pymarktools check

# CLI args override config
pymarktools check --check-external --timeout 30
```

### Multiple Paths

```toml
[tool.pymarktools]
paths = ["src", "docs", "README.md", "CHANGELOG.md"]
include_pattern = "*.md"
exclude_pattern = "test_*.md"
```

### CI/CD Configuration

```toml
[tool.pymarktools]
paths = ["."]
timeout = 30
check_external = true
parallel = true
fail = true
workers = 8
output = "link-check-report.txt"
```

## Note

This implementation uses the `[tool.pymarktools]` section for consistency with the package name. If you see references
to `[tool.pymarkdocs]` in issues or documentation, please use `[tool.pymarktools]` instead.
