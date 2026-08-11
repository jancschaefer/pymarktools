# Rust Core Migration Design

## Objective

Move all pymarktools core behavior to Rust for speed and type safety while preserving its normal Python installation, public import surface, and command-line interface.

## Chosen approach

Use a PyO3 native extension built and packaged by maturin. This keeps `pip install pymarktools` and `uv add pymarktools` as the user experience while placing parsing, validation, filesystem traversal, network checks, refactoring, and command execution in Rust.

Alternatives considered:

- A Rust subprocess behind a Python wrapper would add process-startup cost and weaken the library API.
- A standalone Rust binary plus a Python launcher would break normal Python-package expectations.

## Architecture

Add a Cargo workspace with a PyO3 crate exposed as `pymarktools._native`. Build it with maturin and the `abi3-py312` ABI, supporting Python 3.12 and later.

The Rust crate owns:

- Markdown parsing, link and image extraction, and reference rewriting.
- Filesystem discovery, glob filtering, and gitignore handling.
- Local path validation.
- Concurrent HTTP validation, redirect handling, timeouts, and worker limits.
- Refactor planning, file moves, and atomic content writes.
- CLI parsing, output decisions, and exit-code decisions.

The Python package remains a compatibility facade:

- Existing modules, classes, functions, dataclass-shaped results, and exception behavior remain available at their current import paths.
- `pymarktools.cli:app` remains the console-script entry point for `pymarktools` and `pymd`, and delegates immediately to the Rust extension.
- `py.typed` and `.pyi` stubs describe the public Python API.
- The package contains no runtime Python implementation of the core behavior once migration is complete.

## Data flow and errors

Python calls into `pymarktools._native`; PyO3 converts arguments to typed Rust request structs. Rust executes the requested operation and returns typed result structs, which map losslessly to the existing Python-visible result objects. Paths, URLs, source locations, status codes, redirect targets, and current diagnostic text are retained.

Malformed inputs, filesystem errors, and network errors are converted to documented Python exceptions or existing CLI diagnostics. Rust code must not panic across the extension boundary. Refactor writes use a plan-then-apply flow with atomic replacement where the platform supports it.

## Migration and compatibility strategy

First establish API and CLI parity tests around the existing behavior. Migrate one vertical slice at a time behind the same public Python API: parsing and result types, local discovery and validation, HTTP checking, then reference refactoring and the CLI. After parity is demonstrated for each slice, remove its Python implementation.

Existing pytest tests remain the Python compatibility contract. New Rust unit and integration tests exercise native logic directly. Both layers mock external network calls deterministically.

## Packaging and release

Replace Hatchling with maturin as the PEP 517 build backend. CI will build and test Rust on every pull request and produce/install wheels in clean environments.

Release CI publishes signed wheels for:

- Linux: `x86_64` and `aarch64`.
- macOS: `x86_64` and `arm64`.
- Windows: `x86_64`.

It also publishes an sdist. End users receive a matching prebuilt wheel and need no Rust compiler. Source installs remain supported when a compatible Rust toolchain is available.

## Validation

- Run Rust formatting, linting, unit tests, and integration tests.
- Run Python type checking, linting, formatting, and the full pytest suite.
- Test built wheels with clean `pip` installs on each supported operating system and Python version.
- Verify console entry points and the preserved Python import surface from the built wheel.
