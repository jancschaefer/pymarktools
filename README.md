# pymarktools

A set of markdown utilities for Python, designed to simplify the manipulation and parsing of markdown text. This project leverages Typer for a user-friendly command line interface and is built with a solid codebase structure to facilitate easy development and testing.

## Features

- **Command line interface** with flexible option placement and callback architecture
- **Link validation** in markdown files with local and external URL checking
- **Image validation** in markdown files with comprehensive error reporting
- **Pattern filtering** with include/exclude glob patterns for targeted file processing
- **Local file checking** with proper path resolution and anchor support
- **External URL validation** with HTTP requests and redirect handling
- **Automatic fixing** of permanent redirects in markdown files
- **Gitignore integration** respecting .gitignore patterns when scanning directories
- **Async processing** with configurable worker concurrency for faster validation
- **Color output** with visual status indicators and customizable display
- **Verbose and quiet modes** for detailed output control
- **Exit code behavior** suitable for CI/CD pipelines (0 for success, 1 for failures)
- **File refactoring** capabilities to move files and update references

## Installation

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
uvx pymarktools check dead-links README.md
```

### Development Installation

For development or contributing:

```bash
git clone https://github.com/yourusername/pymarktools.git
cd pymarktools
uv install -e .
```

## Usage

After installation, you can use the command line interface to access the markdown utilities. The CLI supports flexible option placement and both global and command-specific options.

### Basic Usage

```bash
# Basic help
pymarktools --help

# Global options (verbose/quiet mode)
pymarktools --verbose check dead-links README.md
pymarktools --quiet check dead-images docs/
```

Replace `<command>` with the specific command you want to execute, and provide any necessary options.

### Check for Dead Links and Images

Check for dead links in a markdown file or directory:

```bash
# Basic link checking
pymarktools check dead-links <path>

# Check with custom timeout and external validation
pymarktools check dead-links docs/ --timeout 60 --check-external

# Check only local files, skip external URLs
pymarktools check dead-links docs/ --no-check-external
```

Check for dead images in a markdown file or directory:

```bash
# Basic image checking
pymarktools check dead-images <path>

# Check with pattern filtering
pymarktools check dead-images docs/ --include "*.md" --exclude "draft_*"
```

### Flexible Option Placement

Options can be specified at the callback level (applying to all subcommands) or at the individual command level:

```bash
# Options at callback level (apply to all check commands)
pymarktools check --timeout 30 --no-check-external dead-links file.md

# Options at command level (override callback settings)
pymarktools check dead-links file.md --timeout 10 --check-external

# Mixed approach (command options override callback when both specified)
pymarktools check --include "*.md" dead-links --timeout 60 docs/
```

### Local File Validation

Control local file checking behavior:

```bash
# Check both local and external references (default)
pymarktools check dead-links docs/

# Skip local file checking, only validate external URLs
pymarktools check dead-links docs/ --no-check-local

# Check only local files, skip external validation
pymarktools check dead-links docs/ --no-check-external
```

Local file validation supports:

- Relative paths (`../docs/file.md`, `./images/logo.png`)
- Absolute paths (`/config/settings.json`)
- Anchors and query parameters (`README.md#installation`)
- Proper path resolution from markdown file location

### External URL Checking and Redirect Fixing

Control external URL validation and redirect handling:

```bash
# Basic external URL checking (default behavior)
pymarktools check dead-links <path>

# Disable external URL checking
pymarktools check dead-links <path> --no-check-external

# Automatically fix permanent redirects in source files
pymarktools check dead-links <path> --fix-redirects

# Custom timeout for HTTP requests
pymarktools check dead-links <path> --timeout 60
```

These options are available for both `dead-links` and `dead-images` commands.

### Pattern Filtering

Use glob patterns to include or exclude specific files:

```bash
# Include only markdown files
pymarktools check dead-links docs/ --include "*.md"

# Exclude draft files
pymarktools check dead-links docs/ --exclude "draft_*"

# Combine include and exclude patterns
pymarktools check dead-links docs/ --include "*.md" --exclude "temp_*"

# Multiple patterns work with fnmatch
pymarktools check dead-images assets/ --include "*.{jpg,png,gif}"
```

### Gitignore Support

By default, the check commands will respect gitignore patterns when scanning directories. You can disable this behavior with:

```bash
pymarktools check dead-links <path> --no-follow-gitignore
```

This option ensures that files and directories excluded by your `.gitignore` rules are not processed during checks, making the operation faster and more focused on relevant files.

### Async Processing

For better performance when checking large numbers of links or images, pymarktools supports async processing:

```bash
# Use async processing with default worker count (CPU cores)
pymarktools check dead-links docs/ --parallel

# Customize the number of async workers
pymarktools check dead-links docs/ --workers 8

# Disable async processing for sequential operation
pymarktools check dead-links docs/ --no-parallel
```

Async processing is most beneficial when:

- Checking external URLs (network I/O bound operations)
- Processing large directories with many markdown files
- Working with files containing numerous links/images

The system automatically separates external URL checking (which benefits from async processing) from local file checking (which is typically fast enough sequentially).

- Checking external URLs (network I/O bound operations)
- Processing large directories with many markdown files
- Working with files containing numerous links/images

The system automatically separates external URL checking (which benefits from parallelization) from local file checking (which is typically fast enough sequentially).

### Color Output

Enhance your terminal experience with colored status indicators:

```bash
# Enable colored output (default in terminals that support it)
pymarktools --color check dead-links docs/

# Disable colored output for plain text
pymarktools --no-color check dead-links docs/

# Color output with status indicators
pymarktools check dead-links docs/  # Shows green ✓ for valid, red ✗ for broken
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
pymarktools --quiet check dead-links docs/

# Default mode - standard output
pymarktools check dead-links docs/

# Verbose mode - detailed diagnostics
pymarktools --verbose check dead-links docs/
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

The tool returns appropriate exit codes for automation:

- **Exit code 0**: All checks passed successfully
- **Exit code 1**: Invalid links/images found or errors occurred

This makes it suitable for CI/CD pipelines:

```bash
# In CI/CD scripts
pymarktools check dead-links docs/
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
pymarktools check dead-links .

# Check specific file with verbose output
pymarktools --verbose check dead-links README.md

# Fast check - local files only
pymarktools check dead-links docs/ --no-check-external
```

### Comprehensive Checking

```bash
# Full validation with redirect fixing
pymarktools check dead-links docs/ --fix-redirects --timeout 60

# Check with custom patterns and gitignore respect
pymarktools check dead-images assets/ --include "*.{md,mdx}" --follow-gitignore

# Batch processing with mixed options
pymarktools check --timeout 30 dead-links docs/ --check-external --fix-redirects
```

### CI/CD Integration

```bash
# Minimal CI check
pymarktools --quiet check dead-links docs/ --no-check-external

# Full CI validation
pymarktools check dead-links . --include "*.md" --timeout 30 || exit 1
```

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
