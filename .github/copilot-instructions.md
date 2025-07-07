# pymarktools AI Agent Instructions

## Project Overview

pymarktools is a Python-based markdown utility library designed to help with markdown file manipulation, validation, and refactoring. It focuses on link and image handling, with features for checking validity and fixing common issues.

## Core Assumptions

- Target python version is 3.13
- The library is intended for use in both CLI and programmatic contexts
- Properly document all public APIs and provide type hints for all functions
- Use `uv` for managing the virtual environment and running commands

## Architecture

The project follows a modular structure:

```
src/pymarktools/
├── __init__.py         # Public API exports
├── cli.py              # Main CLI app entry point with global options
├── state.py            # Global state management for CLI options
├── commands/           # CLI command implementations
│   ├── check.py        # Link/image validation commands with callback architecture
│   └── refactor.py     # File movement and reference updating
└── core/               # Core business logic
    ├── models.py       # Data classes (LinkInfo, ImageInfo)
    ├── link_checker.py # Link validation with pattern filtering support
    ├── image_checker.py# Image validation with pattern filtering support
    ├── gitignore.py    # Git repository and .gitignore handling
    ├── markdown.py     # Re-exports for backward compatibility
    └── refactor.py     # Markdown reference refactoring logic

```

### Core Components

1. **Data Classes** (in `core/models.py`)

    - `LinkInfo`: Store structured data about markdown links with validation status
    - `ImageInfo`: Store structured data about markdown images with validation status
    - Both support local file checking with `is_local` and `local_path` fields for debugging/display
    - `FileReference`: Represents file references in markdown (in refactor.py)

1. **Core Services**

    - `DeadLinkChecker` (in `core/link_checker.py`): Validates and fixes links in markdown files with pattern filtering and parallel processing
    - `DeadImageChecker` (in `core/image_checker.py`): Validates and fixes image references in markdown with pattern filtering and parallel processing
    - `FileReferenceManager` (in `core/refactor.py`): Handles refactoring file references during moves
    - Gitignore support (in `core/gitignore.py`): Respects .gitignore patterns when scanning directories

1. **CLI Interface**

    - Uses Typer for command definition with callback architecture for shared options
    - Global state management via `state.py` for verbose/quiet/color modes
    - Commands are grouped by functionality (check, refactor)
    - Supports flexible option placement: options can be specified at callback or individual command level
    - Individual command options override callback options when provided
    - Comprehensive options: `--check-external`, `--check-local`, `--fix-redirects`, `--follow-gitignore`, `--include`, `--exclude`, `--parallel`, `--workers`, `--color`
    - Exit code behavior: returns 0 for success, 1 for validation failures (suitable for CI/CD)

1. **Async Processing**

    - AsyncIO-based concurrent execution for external URL validation
    - Configurable worker limit with `--workers` option (defaults to CPU cores)
    - Enable/disable with `--parallel`/`--no-parallel` flags
    - Automatic separation of external (async) and local (sequential) validation
    - Significant performance improvements for network-bound operations with better resource utilization

1. **Color Output System**

    - Typer.secho()-based colored terminal output with visual status indicators
    - Global `--color`/`--no-color` options for consistent styling
    - Helper functions for standardized color coding across commands
    - Automatic color detection and fallback for non-terminal environments
    - Status-based coloring: green for success, red for errors, yellow for warnings, blue for info

1. **Global State Management** (in `state.py`)

    - Centralized state management to avoid circular imports
    - Supports verbose, quiet, and color modes across all commands
    - Shared between CLI entry point and command modules

## Key Workflows

### 1. CLI Option Architecture

The CLI supports flexible option placement with callback architecture:

- **Callback Options**: Common options can be specified at the check command level
- **Individual Command Options**: All options are also available on individual commands
- **Option Precedence**: Command-specific options override callback options when provided
- **Global Options**: `--verbose` and `--quiet` are available at the main CLI level

```bash
# Options at callback level (apply to all check subcommands)
uv run pymarktools check --timeout 60 --no-check-external dead-links file.md

# Options at command level (override callback settings)  
uv run pymarktools check dead-links file.md --timeout 30 --check-external

# Mixed approach (command overrides callback when both specified)
uv run pymarktools check --include "*.md" dead-links --timeout 60 file.md
```

### 2. Verbosity Levels

The system supports three verbosity levels controlled by global options:

| Level       | Flag        | Description                 | Output Includes                                                                                                                               |
| ----------- | ----------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quiet**   | `--quiet`   | Minimal output, errors only | Critical errors, final summary counts                                                                                                         |
| **Default** | _(none)_    | Standard output level       | File processing status, broken link/image reports, summary statistics                                                                         |
| **Verbose** | `--verbose` | Detailed diagnostic output  | All default output plus individual validation results, HTTP response codes, redirect chains, file path resolution details, performance timing |

```bash
# Quiet mode - minimal output
uv run pymarktools --quiet check dead-links docs/

# Default mode - standard output  
uv run pymarktools check dead-links docs/

# Verbose mode - detailed diagnostics
uv run pymarktools --verbose check dead-links docs/
```

### 3. Async Processing

The system uses asyncio for concurrent external URL validation:

```bash
# Use async processing with default worker count (CPU cores)
uv run pymarktools check dead-links docs/ --parallel

# Customize the number of concurrent workers
uv run pymarktools check dead-links docs/ --workers 8

# Disable async processing for sequential operation
uv run pymarktools check dead-links docs/ --no-parallel
```

Async processing automatically separates:

- **External URLs**: Checked asynchronously using asyncio.gather() and semaphores for network I/O efficiency
- **Local files**: Checked sequentially as they are typically fast file system operations

### 4. Color Output

Visual status indicators enhance terminal output:

```bash
# Enable colored output (default in terminals)
uv run pymarktools --color check dead-links docs/

# Disable colored output for plain text
uv run pymarktools --no-color check dead-links docs/
```

Color coding provides instant visual feedback:

- **Green (✓)**: Valid links/images
- **Red (✗)**: Broken or invalid references
- **Yellow**: Warnings and redirects
- **Blue**: Informational messages

Colors automatically disable in non-terminal environments or when output is redirected.

### 5. Link/Image Validation

The primary workflow is checking markdown files for dead links or images:

```python
# Create a checker with all validation options
checker = DeadLinkChecker(
    timeout=30, 
    check_external=True, 
    check_local=True,
    fix_redirects=True,
    follow_gitignore=True,
    parallel=True,
    workers=8
)

# Check a single file (uses async internally)
links = checker.check_file(path)

# Or check an entire directory with pattern filtering (uses async internally)
results = checker.check_directory(
    directory, 
    include_pattern="*.md", 
    exclude_pattern="draft_*"
)

# For async usage (advanced)
links = await checker.check_file_async(path)
results = await checker.check_directory_async(directory, "*.md")
```

```
follow_gitignore=True
```

)

# Check a single file

links = checker.check_file(path)

# Or check an entire directory with pattern filtering

results = checker.check_directory(
directory,
include_pattern="*.md",
exclude_pattern="draft\_*"
)

````

The same pattern applies to `DeadImageChecker`. Both checkers support:
- **External URL validation**: HTTP/HTTPS links with redirect handling
- **Local file validation**: Relative and absolute file path checking with proper path resolution
- **Gitignore integration**: Automatically skip ignored files and directories
- **Pattern filtering**: Include/exclude patterns using fnmatch for flexible file selection

### 6. File Refactoring

To move files and update all references:

```python
# Create a manager
manager = FileReferenceManager(base_dir=repo_root)

# Find references to a file
refs = manager.find_references(target_file, include_pattern="*.md")

# Move file and update references
manager.move_file_and_update_references(source, destination, refs)
````

### 7. Gitignore Integration

The system automatically respects .gitignore patterns:

- Searches for .gitignore files from current directory up to repository root
- Uses `gitignore_parser` library for spec-compliant pattern matching
- Supports hierarchical .gitignore files in subdirectories
- Can be disabled with `--no-follow-gitignore` option

## Development Conventions

### HTTP Handling

- External links are checked using `httpx.AsyncClient` with configurable timeouts for async operation
- HTTP requests use `follow_redirects=False` to detect and handle redirects manually
- Permanent redirects (301, 307, 308) can be automatically fixed with `fix_redirects=True`
- Async processing uses `asyncio.gather()` with semaphores for rate limiting and resource management

### Local File Handling

- Local file paths are validated using `pathlib.Path` for cross-platform compatibility
- Relative paths are resolved from the markdown file's directory
- Absolute paths are resolved from the markdown file's parent directory
- Anchors and query parameters are stripped for file existence checking
- Path normalization handles `..` and `.` components correctly
- Enhanced data models include `is_local` and `local_path` fields for debugging

### Markdown Processing

- Regex patterns extract links and images: `\[([^\]]*)\]\(([^)]+)\)` for links and `!\[([^\]]*)\]\(([^)]+)\)` for images
- Images are excluded from link extraction to avoid double-processing
- String replacement is used for content updates (rather than regex replacement) to avoid escaping issues
- File paths are handled via Python's `pathlib.Path` throughout the codebase

### Gitignore Support

- Uses `gitignore_parser` library for spec-compliant .gitignore parsing
- Recursively discovers .gitignore files from target directory up to repository root
- Combines patterns from all .gitignore files in the hierarchy
- Repository root is detected by finding the `.git` directory

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

```

### Runnin Quality Checks

#### Typechecker

```bash
uv run ty check
```

#### Ruff

```bash
uv run ruff check src/pymarktools tests --fix
uv run ruff format --check src/pymarktools tests
```

### CLI Usage

```bash
# Check for dead links with global verbose mode
uv run pymarktools --verbose check dead-links README.md --check-external --fix-redirects

# Check for dead images with command-specific options
uv run pymarktools check dead-images docs/ --timeout 60 --include "*.md" --exclude "draft_*"

# Check only local files, skip external URLs
uv run pymarktools check dead-links docs/ --no-check-external

# Skip local file checking, only check external URLs  
uv run pymarktools check dead-links docs/ --no-check-local

# Disable gitignore filtering
uv run pymarktools check dead-links docs/ --no-follow-gitignore

# Use parallel processing with custom worker count
uv run pymarktools check dead-links docs/ --parallel --workers 8

# Disable parallel processing
uv run pymarktools check dead-links docs/ --no-parallel

# Enable color output
uv run pymarktools --color check dead-links docs/

# Disable color output
uv run pymarktools --no-color check dead-links docs/

# Mix callback and command options (command options override callback)
uv run pymarktools check --timeout 30 dead-links file.md --timeout 10

# Move a file and update references with pattern filtering
uv run pymarktools refactor move old/path.md new/path.md --include "*.md"
```

### Async Implementation

- Core URL checking uses `async`/`await` patterns with `httpx.AsyncClient` for non-blocking HTTP requests
- `asyncio.gather()` coordinates concurrent execution with configurable semaphores for rate limiting
- Automatic fallback to synchronous execution when methods are overridden (for test compatibility)
- Event loop detection prevents `asyncio.run()` conflicts in async contexts (CLI testing)
- Uses ThreadPoolExecutor as fallback when already in async context to avoid event loop nesting issues
