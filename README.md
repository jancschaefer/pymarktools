# pymarktools

![PyPI - Status](https://img.shields.io/pypi/status/pymarktools)
![PyPI - Version](https://img.shields.io/pypi/v/pymarktools)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/jancschaefer/pymarktools/.github%2Fworkflows%2Ftest.yml?branch=main)
![GitHub License](https://img.shields.io/github/license/jancschaefer/pymarktools)
![Codecov](https://img.shields.io/codecov/c/github/jancschaefer/pymarktools)
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fjancschaefer%2Fpymarktools%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)

A set of markdown utilities for Python, designed to simplify the manipulation and parsing of markdown text. This project
leverages Typer for a user-friendly command line interface and is built with a solid codebase structure to facilitate
easy development and testing.

![check-screenshot](./docs/.attachments/readme-screenshot-check.png)

## Features

### Validation

- **Link validation** with local and external URL checking
- **Image validation** with comprehensive error reporting
- **Automatic fixing** of permanent redirects in markdown files
- **Pattern filtering** with include/exclude glob patterns
- **Local file checking** with proper path resolution and anchor support
- **External URL validation** with HTTP requests and redirect handling

### Workflow

- **Optional fail behavior** with `--fail/--no-fail` to control exit codes
- **Gitignore integration** respecting `.gitignore` patterns
- **File refactoring** capabilities to move files and update references

### Usability and Performance

- **Async processing** with configurable worker concurrency
- **Color output** with visual status indicators
- **Verbose and quiet modes** for detailed output control
- **Exit code behavior** suitable for CI/CD pipelines (0 for success, 1 for failures)

## Installation

> [!NOTE]
> **Python 3.12+ Required:** pymarktools requires Python 3.12+ and works best with modern terminal environments
> that support color output.

You can install pymarktools using several methods:

### Using pip

```bash
pip install pymarktools
```

### Using uv

```bash
# Install in current environment
uv add pymarktools

# Install globally as a tool
uv tool install pymarktools
```

### Using uvx (run without installation)

```bash
# Run directly without installing
uvx pymarktools --help
uvx pymarktools check --no-check-dead-images README.md
```

### Development Installation

> [!TIP]
> **Use uv for Best Experience:** For the best development experience, we recommend using `uv` for package
> management and virtual environment handling.

For development or contributing:

```bash
git clone https://github.com/yourusername/pymarktools.git
cd pymarktools
uv install -e .

# Install pre-commit hooks for code quality
uv run pre-commit install

# Or use the justfile to set up everything
uv run just setup
```

This will install [pre-commit hooks](docs/pre-commit.md) that automatically run quality checks (linting, formatting,
type checking) before each commit, ensuring your contributions meet the project's standards.

> [!IMPORTANT]
> **Always Install Pre-commit Hooks:** Pre-commit hooks are essential for maintaining code quality. Always
> run `uv run pre-commit install` after cloning the repository to ensure your commits meet the project's standards.

### Development Tasks

The project includes a `justfile` for common development tasks:

```bash
# Show available tasks
uv run just

# Run all quality checks (same as CI)
uv run just check

# Run individual tasks
uv run just lint
uv run just format
uv run just type-check
uv run just test
```

## Usage

After installation, you can use the command line interface to access the markdown utilities.

### Basic Usage

```bash
# Basic help
pymarktools --help

# Global options (verbose/quiet mode)
pymarktools --verbose check --no-check-dead-images README.md
pymarktools --quiet check --no-check-dead-links docs/
```

Replace `<command>` with the specific command you want to execute, and provide any necessary options.

### Check for Dead Links and Images

Check for dead links in a markdown file or directory:

```bash
# Basic link checking
pymarktools check --no-check-dead-images <path>

# Check with custom timeout and external validation
pymarktools check --no-check-dead-images docs/ --timeout 60 --check-external

# Check only local files, skip external URLs
pymarktools check --no-check-dead-images docs/ --no-check-external
```

Check for dead images in a markdown file or directory:

```bash
# Basic image checking
pymarktools check --no-check-dead-links <path>

# Check with pattern filtering
pymarktools check --no-check-dead-links docs/ --include "*.md" --exclude "draft_*"
```

### Local File Validation

Control local file checking behavior:

```bash
# Check both local and external references (default)
pymarktools check --no-check-dead-images docs/

# Skip local file checking, only validate external URLs
pymarktools check --no-check-dead-images docs/ --no-check-local

# Check only local files, skip external validation
pymarktools check --no-check-dead-images docs/ --no-check-external
```

Local file validation supports:

- Relative paths (`../docs/file.md`, `./images/logo.png`)
- Absolute paths (`/config/settings.json`)
- Anchors and query parameters (`README.md#installation`)
- Proper path resolution from markdown file location

### External URL Checking and Redirect Fixing

> [!WARNING]
> **Automatic File Modification:** When using `--fix-redirects`, the tool will modify your source files
> automatically. Always commit your changes or create a backup before using this option.

Control external URL validation and redirect handling:

```bash
# Basic external URL checking (default behavior)
pymarktools check --no-check-dead-images <path>

# Disable external URL checking
pymarktools check --no-check-dead-images <path> --no-check-external

# Automatically fix permanent redirects in source files
pymarktools check --no-check-dead-images <path> --fix-redirects

# Custom timeout for HTTP requests
pymarktools check --no-check-dead-images <path> --timeout 60
```

These options apply to the unified `check` command and can be combined with the link or image toggles.

### Pattern Filtering

Use glob patterns to include or exclude specific files:

```bash
# Include only markdown files
pymarktools check --no-check-dead-images docs/ --include "*.md"

# Exclude draft files
pymarktools check --no-check-dead-images docs/ --exclude "draft_*"

# Combine include and exclude patterns
pymarktools check --no-check-dead-images docs/ --include "*.md" --exclude "temp_*"

# Multiple patterns work with fnmatch
pymarktools check --no-check-dead-links assets/ --include "*.{jpg,png,gif}"
```

### Gitignore Support

By default, the check commands will respect gitignore patterns when scanning directories. You can disable this behavior
with:

```bash
pymarktools check --no-check-dead-images <path> --no-follow-gitignore
```

This option ensures that files and directories excluded by your `.gitignore` rules are not processed during checks,
making the operation faster and more focused on relevant files.

### Async Processing

> [!TIP]
> **Significant Performance Gains:** Async processing provides significant performance improvements when checking
> external URLs or processing large directories. Enable it with `--parallel` for better performance.

For better performance when checking large numbers of links or images, pymarktools supports async processing:

```bash
# Use async processing with default worker count (CPU cores)
pymarktools check --no-check-dead-images docs/ --parallel

# Customize the number of async workers
pymarktools check --no-check-dead-images docs/ --workers 8

# Disable async processing for sequential operation
pymarktools check --no-check-dead-images docs/ --no-parallel
```

Async processing is most beneficial when:

- Checking external URLs (network I/O bound operations)
- Processing large directories with many markdown files
- Working with files containing numerous links/images

The system automatically separates external URL checking (which benefits from async processing) from local file checking
(which is typically fast enough sequentially).

- Checking external URLs (network I/O bound operations)
- Processing large directories with many markdown files
- Working with files containing numerous links/images

The system automatically separates external URL checking (which benefits from parallelization) from local file checking
(which is typically fast enough sequentially).

### Color Output

Enhance your terminal experience with colored status indicators:

```bash
# Enable colored output (default in terminals that support it)
pymarktools --color check --no-check-dead-images docs/

# Disable colored output for plain text
pymarktools --no-color check --no-check-dead-images docs/

# Color output with status indicators
pymarktools check --no-check-dead-images docs/  # Shows green ✓ for valid, red ✗ for broken
```

Color coding provides instant visual feedback:

- **Green (✓)**: Valid links/images
- **Red (✗)**: Broken or invalid references
- **Yellow**: Warnings and redirects
- **Blue**: Informational messages

Colors are automatically disabled when output is redirected or in non-terminal environments.

### Verbosity Levels

Control the amount of output with three verbosity levels:

| Level       | Flag        | Description                 | Output Includes                                                                                                                               |
| ----------- | ----------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quiet**   | `--quiet`   | Minimal output, errors only | Critical errors, final summary counts                                                                                                         |
| **Default** | _(none)_    | Standard output level       | File processing status, broken link/image reports, summary statistics                                                                         |
| **Verbose** | `--verbose` | Detailed diagnostic output  | All default output plus individual validation results, HTTP response codes, redirect chains, file path resolution details, performance timing |

```bash
# Quiet mode - minimal output
pymarktools --quiet check --no-check-dead-images docs/

# Default mode - standard output
pymarktools check --no-check-dead-images docs/

# Verbose mode - detailed diagnostics
pymarktools --verbose check --no-check-dead-images docs/
```

The verbosity setting applies globally to all commands and can be combined with color output for enhanced readability.

### File Refactoring

Move files and automatically update all references:

```bash
# Move a file and update all references in markdown files
pymarktools refactor move old/path.md new/path.md

# Use pattern filtering when searching for references
pymarktools refactor move old/path.md new/path.md --include "*.md"

# Dry run to see what would be changed
pymarktools refactor move old/path.md new/path.md --dry-run
```

### Exit Codes and CI/CD Integration

> [!IMPORTANT]
> **CI/CD Pipeline Integration:** The tool returns exit code 1 when broken links/images are found, making
> it suitable for CI/CD pipelines. Use `--no-fail` to disable this behavior if needed.

The tool returns appropriate exit codes for automation:

- **Exit code 0**: All checks passed successfully
- **Exit code 1**: Invalid links/images found or errors occurred

You can disable this behavior with the `--no-fail` option on any check command.

This makes it suitable for CI/CD pipelines:

```bash
# In CI/CD scripts
pymarktools check --no-check-dead-images docs/
if [ $? -eq 0 ]; then
    echo "All links are valid!"
else
    echo "Found broken links, failing build"
    exit 1
fi
```

## Common Examples

### Quick Validation

```bash
# Check current directory for dead links
pymarktools check --no-check-dead-images .

# Check specific file with verbose output
pymarktools --verbose check --no-check-dead-images README.md

# Fast check - local files only
pymarktools check --no-check-dead-images docs/ --no-check-external
```

### Comprehensive Checking

```bash
# Full validation with redirect fixing
pymarktools check --no-check-dead-images docs/ --fix-redirects --timeout 60

# Check with custom patterns and gitignore respect
pymarktools check --no-check-dead-links assets/ --include "*.{md,mdx}" --follow-gitignore

# Batch processing with mixed options
pymarktools check --timeout 30 --no-check-dead-images docs/ --check-external --fix-redirects
```

### CI/CD Integration

```bash
# Minimal CI check
pymarktools --quiet check --no-check-dead-images docs/ --no-check-external

# Full CI validation
pymarktools check --no-check-dead-images . --include "*.md" --timeout 30 || exit 1
```

## Configuration

### pyproject.toml Support

> [!NOTE]
> **Project-wide Configuration:** Configuration via `pyproject.toml` allows you to set project-wide defaults,
> reducing the need to specify options on every command invocation.

pymarktools supports configuration via `pyproject.toml` for project-wide settings. This allows you to define default
behavior without specifying options on every command invocation.

Add configuration under the `[tool.pymarktools]` section:

```toml
[tool.pymarktools]
# Paths to check (replaces the PATH argument)
paths = ["src", "docs", "README.md"]

# Check options
timeout = 60
check_external = false
check_local = true
include_pattern = "*.md"
exclude_pattern = "test_*.md"
parallel = false
fail = true
workers = 4
```

**Usage with configuration:**

```bash
# Uses paths and options from pyproject.toml
pymarktools check

# CLI arguments override configuration values
pymarktools check --timeout 30 --check-external

# Explicit path overrides configured paths
pymarktools check specific-file.md
```

**Priority order** (highest to lowest):

1. Command-line arguments
1. pyproject.toml configuration
1. Built-in defaults

For complete configuration reference, see [docs/pyproject-config.md](docs/pyproject-config.md).

## Testing

To run the tests for pymarktools, use the following commands:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/pymarktools

# Run specific test files
uv run pytest tests/test_core/test_link_checker.py

# Run tests in verbose mode
uv run pytest -v
```

For development setup:

```bash
# Install development dependencies
uv install -e .
uv add --dev pytest pytest-cov

# Run quality checks
uv run ruff check src/pymarktools tests --fix
uv run ruff format --check src/pymarktools tests
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

For development setup:

```bash
# Install development dependencies
uv install -e .
uv add --dev pytest pytest-cov

# Run quality checks
uv run ruff check src/pymarktools tests --fix
uv run ruff format --check src/pymarktools tests
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
