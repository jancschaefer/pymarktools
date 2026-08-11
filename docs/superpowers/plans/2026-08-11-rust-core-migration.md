# Rust Core Migration Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Replace every pymarktools operation with a type-safe Rust core while preserving Python installation, imports, and console commands.

**Architecture:** A pymarktools-core Rust crate owns all application behavior. A PyO3 pymarktools._native extension is built by maturin; Python modules only re-export native objects or delegate a single request.

**Tech Stack:** Rust 1.85+, PyO3, maturin, Tokio, reqwest, ignore, globset, pulldown-cmark, clap, toml, pytest, uv, GitHub Actions.

---

## File structure

Create Cargo.toml; crates/pymarktools-core/src/{lib,model,markdown,paths,discovery,http,refactor,config,cli}.rs; crates/pymarktools-core/tests/{markdown,discovery,http,refactor,cli}.rs; crates/pymarktools-py/{Cargo.toml,src/lib.rs}; src/pymarktools/_native.pyi; src/pymarktools/py.typed; tests/contracts/{test_public_api,test_cli_contract}.py; and .github/workflows/wheels.yml.

The existing src/pymarktools/core modules remain only as import-compatible facades. They must contain no Markdown parsing, filesystem walking, HTTP request, or file-write logic.

### Task 1: Create the compatibility baseline

**Files:**
- Create: tests/contracts/__init__.py
- Create: tests/contracts/test_public_api.py
- Create: tests/contracts/test_cli_contract.py
- Modify: pyproject.toml:38-59

- [ ] **Step 1: Write tests locking the public result shape**

Add test_link_and_image_result_shapes_stay_stable: construct DeadLinkChecker(check_external=False), extract [docs](guide.md), construct DeadImageChecker(check_external=False), extract ![logo](logo.svg), and assert LinkInfo/ImageInfo types plus exact text or alt text, URL, and line_number values.

Add test_local_path_error_stays_stable: create README.md containing [missing](missing.md), invoke DeadLinkChecker(check_external=False).check_file, and assert is_local is true, is_valid is false, local_path is the absolute missing path, and error is File not found followed by that path.

- [ ] **Step 2: Run baseline API tests**

Run: uv run pytest tests/contracts/test_public_api.py -q
Expected: 2 passed.

- [ ] **Step 3: Write CLI contracts**

Add test_help_and_version_are_available using Typer CliRunner and pymarktools.cli.app; both --help and --version must exit 0.

Add test_disabling_all_checks_returns_one; invoking check --no-check-dead-links --no-check-dead-images must exit 1 and contain Both checks disabled; nothing to do.

- [ ] **Step 4: Run baseline CLI tests**

Run: uv run pytest tests/contracts/test_cli_contract.py -q
Expected: 2 passed.

- [ ] **Step 5: Add the contract pytest marker and commit**

Run: uv run pytest tests/contracts -q
Expected: 4 passed.

Commit: git add pyproject.toml tests/contracts && git commit -m "test: capture Python compatibility contract"

### Task 2: Add the Rust workspace and maturin extension

**Files:**
- Create: Cargo.toml
- Create: crates/pymarktools-core/Cargo.toml and src/lib.rs
- Create: crates/pymarktools-py/Cargo.toml and src/lib.rs
- Create: src/pymarktools/_native.pyi and py.typed
- Modify: pyproject.toml:1-84

- [ ] **Step 1: Add a failing native-extension smoke test**

Add test_extension_exposes_the_core_version, importing pymarktools._native and asserting native.core_version().count(".") equals 2.

- [ ] **Step 2: Verify it fails**

Run: uv run pytest tests/contracts/test_public_api.py::test_extension_exposes_the_core_version -q
Expected: import failure because pymarktools._native is absent.

- [ ] **Step 3: Implement the minimal extension**

Workspace members are crates/pymarktools-core and crates/pymarktools-py. The core crate exports public const VERSION: &str = env!("CARGO_PKG_VERSION"). The PyO3 crate defines pyfunction core_version() returning pymarktools_core::VERSION and pymodule _native that registers core_version.

Configure maturin with module-name pymarktools._native, python-source src, and PyO3 feature abi3-py312. Retain pymarktools and pymd project scripts. Add core_version() -> str to the stub.

- [ ] **Step 4: Build and prove green**

Run: uv run maturin develop --manifest-path crates/pymarktools-py/Cargo.toml && uv run pytest tests/contracts/test_public_api.py::test_extension_exposes_the_core_version -q
Expected: 1 passed.

- [ ] **Step 5: Verify and commit**

Run: cargo fmt --check && cargo clippy --workspace --all-targets -- -D warnings && cargo test --workspace
Expected: all exit 0.
Commit: git add Cargo.toml Cargo.lock crates pyproject.toml src/pymarktools/_native.pyi src/pymarktools/py.typed && git commit -m "build: add maturin Rust extension foundation"

### Task 3: Port Markdown parsing and result types

**Files:**
- Create: crates/pymarktools-core/src/model.rs, markdown.rs, tests/markdown.rs
- Modify: crates/pymarktools-core/Cargo.toml and src/lib.rs
- Modify: crates/pymarktools-py/src/lib.rs
- Modify: src/pymarktools/core/models.py, markdown.py, link_checker.py, image_checker.py
- Modify: src/pymarktools/_native.pyi
- Test: tests/test_core/test_markdown.py

- [ ] **Step 1: Write failing Rust parser tests**

Test extract_links("![logo](logo.svg) newline [guide](docs/guide.md)") returns one link with text guide, URL docs/guide.md, and one-based line 2. Test extract_images("before newline ![logo](assets/logo.svg)") returns one image with alt_text logo and line 2.

- [ ] **Step 2: Verify red**

Run: cargo test -p pymarktools-core --test markdown
Expected: compilation failure because markdown does not exist.

- [ ] **Step 3: Implement models and bindings**

Define LinkInfo with text, url, line_number, is_valid, status_code, error, redirect_url, is_permanent_redirect, updated, is_local, local_path. Define ImageInfo identically but with alt_text. Implement extract_links and extract_images using parser offsets for source-line calculation. Bind native classes/functions with PyO3. Convert Python models to native re-exports and extraction methods to delegates.

- [ ] **Step 4: Verify green**

Run: cargo test -p pymarktools-core --test markdown && uv run pytest tests/test_core/test_markdown.py tests/contracts/test_public_api.py -q
Expected: all selected tests pass.

- [ ] **Step 5: Commit**

Commit: git add crates src/pymarktools/core tests && git commit -m "feat: move Markdown parsing to Rust"

### Task 4: Port discovery, gitignore, and local paths

**Files:**
- Create: crates/pymarktools-core/src/paths.rs, discovery.rs, tests/discovery.rs
- Modify: crates/pymarktools-core/Cargo.toml and src/lib.rs; crates/pymarktools-py/src/lib.rs
- Modify: src/pymarktools/core/async_checker.py, gitignore.py, link_checker.py, image_checker.py
- Test: tests/test_core/test_gitignore_discovery.py, test_link_checker.py, test_image_checker.py

- [ ] **Step 1: Write failing Rust tests**

Create a temporary tree with .gitignore containing generated/, generated/skip.md, and keep.md. Assert discover_markdown_files(root, "*.md", None, true) returns only keep.md. Assert resolve_local_path("../guide.md#install?unused", document at fixtures/docs/README.md) normalizes to fixtures/guide.md.

- [ ] **Step 2: Verify red**

Run: cargo test -p pymarktools-core --test discovery
Expected: compilation failure for discovery and paths modules.

- [ ] **Step 3: Implement native traversal**

Use ignore::WalkBuilder when gitignore is enabled and walkdir::WalkDir otherwise. Use globset for include/exclude filtering. Strip anchors/query parameters; preserve current absolute and relative path semantics; return exact File not found diagnostics. Bind discover_files and check_local_path. Make AsyncChecker, gitignore helpers, and both checker classes native delegates.

- [ ] **Step 4: Verify green**

Run: cargo test -p pymarktools-core --test discovery && uv run pytest tests/test_core/test_gitignore_discovery.py tests/test_core/test_link_checker.py tests/test_core/test_image_checker.py -q
Expected: all selected tests pass.

- [ ] **Step 5: Commit**

Commit: git add crates src/pymarktools/core tests && git commit -m "feat: move file discovery to Rust"

### Task 5: Port concurrent HTTP and email-domain validation

**Files:**
- Create: crates/pymarktools-core/src/http.rs and tests/http.rs
- Modify: crates/pymarktools-core/Cargo.toml and src/lib.rs; crates/pymarktools-py/src/lib.rs
- Modify: src/pymarktools/core/async_checker.py, link_checker.py, image_checker.py
- Test: tests/test_core/test_check_external.py, test_email_links.py, test_email_integration.py, test_redirect_fix.py

- [ ] **Step 1: Write a failing deterministic HTTP test**

Start wiremock MockServer. Configure HEAD /old to return 301 with location /new. Assert check_url(server_url + "/old", HttpOptions::default()) produces is_valid true, is_permanent_redirect true, and redirect_url /new.

- [ ] **Step 2: Verify red**

Run: cargo test -p pymarktools-core --test http
Expected: compilation failure for the http module.

- [ ] **Step 3: Implement native HTTP**

Use Tokio and reqwest with rustls. Define HttpOptions(timeout, workers) and HttpResult(is_valid, status_code, error, redirect_url, is_permanent_redirect). Use HEAD without auto-following redirects, accept 2xx plus 301/302/307/308, classify 301/307/308 as permanent, and throttle work with a semaphore. Handle mailto by HEAD-requesting https://domain. Bind a GIL-releasing synchronous function; remove httpx/asyncio implementations.

- [ ] **Step 4: Verify green**

Run: cargo test -p pymarktools-core --test http && uv run pytest tests/test_core/test_check_external.py tests/test_core/test_email_links.py tests/test_core/test_email_integration.py tests/test_core/test_redirect_fix.py -q
Expected: all selected tests pass with no live network.

- [ ] **Step 5: Commit**

Commit: git add crates src/pymarktools/core tests && git commit -m "feat: move HTTP validation to Rust"

### Task 6: Port rewrite and reference refactoring

**Files:**
- Create: crates/pymarktools-core/src/refactor.rs and tests/refactor.rs
- Modify: crates/pymarktools-core/src/lib.rs; crates/pymarktools-py/src/lib.rs
- Modify: src/pymarktools/core/refactor.py, link_checker.py, image_checker.py
- Test: tests/test_core/test_refactor.py and test_redirect_fix.py

- [ ] **Step 1: Write a failing move test**

Create images/logo.svg and README.md with ![logo](images/logo.svg). Move to assets/logo.svg with move_file_and_update_references. Assert the destination exists and README contains ![logo](assets/logo.svg).

- [ ] **Step 2: Verify red**

Run: cargo test -p pymarktools-core --test refactor
Expected: compilation failure for refactor.

- [ ] **Step 3: Implement plan-then-apply mutation**

Define FileReference, MoveOptions, find_references, calculate_new_reference, and move_file_and_update_references. Determine all file-content changes before moving anything. Write each updated document to a same-directory temporary file, flush, and rename atomically. Exclude external URLs. Bind operations and reduce FileReferenceManager to a facade.

- [ ] **Step 4: Verify green**

Run: cargo test -p pymarktools-core --test refactor && uv run pytest tests/test_core/test_refactor.py tests/test_core/test_redirect_fix.py -q
Expected: all selected tests pass.

- [ ] **Step 5: Commit**

Commit: git add crates src/pymarktools/core tests && git commit -m "feat: move reference refactoring to Rust"

### Task 7: Port config and command execution

**Files:**
- Create: crates/pymarktools-core/src/config.rs, cli.rs, tests/cli.rs
- Modify: crates/pymarktools-core/Cargo.toml and src/lib.rs; crates/pymarktools-py/src/lib.rs
- Modify: src/pymarktools/cli.py, check_options.py, config.py, global_state.py
- Modify: src/pymarktools/commands/check.py and refactor.py
- Test: tests/test_cli.py, tests/test_config.py, tests/test_commands/

- [ ] **Step 1: Write failing precedence and dispatcher tests**

In Rust, assert merge_check_options(default timeout, config timeout 60, CLI timeout 5).timeout is 5. In Python, monkeypatch cli._native.run_cli, call cli.app(), and assert it received an empty argument list and returned normally.

- [ ] **Step 2: Verify red**

Run: cargo test -p pymarktools-core --test cli && uv run pytest tests/contracts/test_cli_contract.py -q
Expected: missing native configuration/runner failures.

- [ ] **Step 3: Implement config and CLI**

Use toml for tool.pymarktools and clap for check/refactor move. Cover every current flag, aliases, defaults, configuration precedence, paths, color environment variables, output, and exit status. Bind run_cli(args), load_pyproject_config(path), and merge_check_options. Keep Typer app and all current command/config imports as adapters only.

- [ ] **Step 4: Verify green**

Run: uv run pytest tests/test_cli.py tests/test_commands tests/test_config.py tests/contracts/test_cli_contract.py -q
Expected: all selected tests pass.

- [ ] **Step 5: Commit**

Commit: git add crates src/pymarktools tests && git commit -m "feat: move command execution to Rust"

### Task 8: Build and publish wheels

**Files:**
- Delete: src/pymarktools/core/async_checker.py and gitignore.py
- Modify: retained Python core facades, pyproject.toml, .github/workflows/test.yml, publish.yml, README.md, CHANGELOG.md
- Create: .github/workflows/wheels.yml

- [ ] **Step 1: Add a clean-wheel smoke test**

Run in CI after building: create /tmp/pymarktools-wheel-test venv; pip install the single dist wheel; import DeadLinkChecker; run pymarktools --help and pymd --help.

- [ ] **Step 2: Verify the pre-matrix local behavior**

Run: uv build
Expected: only local artifacts are created, demonstrating the cross-platform matrix is necessary.

- [ ] **Step 3: Add native-only facades and CI matrix**

Delete Python core code only once all retained imports delegate to _native. Run cargo fmt, clippy, test, and existing Python checks on PRs. Use PyO3/maturin-action to build abi3-py312 wheels for manylinux x86_64/aarch64, macOS x86_64/arm64, and Windows x86_64. Upload all wheels plus one sdist to existing trusted publishing. Document prebuilt wheel installs and Rust requirements for source builds. Add an Unreleased Changed changelog item.

- [ ] **Step 4: Run complete validation**

Run: cargo fmt --check && cargo clippy --workspace --all-targets -- -D warnings && cargo test --workspace && uv run ty check && uv run ruff check src/pymarktools tests && uv run ruff format --check src/pymarktools tests && uv run pytest --cov=src/pymarktools --cov-fail-under=80 && maturin build --release --manifest-path crates/pymarktools-py/Cargo.toml
Expected: every command exits 0 and dist contains an ABI3 wheel.

- [ ] **Step 5: Install the built wheel and commit**

Run the clean-wheel smoke test from Step 1 after confirming exactly one local wheel exists.
Expected: native import and both aliases work.
Commit: git add -A && git commit -m "feat: ship pymarktools Rust core"

## Plan self-review

- Spec coverage: Tasks 2 and 8 deliver maturin, ABI3 wheels, sdist, CI, and normal Python installation; Tasks 3 through 7 move every requested behavior into Rust.
- Placeholder scan: every task names files, types, tests, commands, errors, and expected outcomes.
- Type consistency: LinkInfo, ImageInfo, HttpOptions, FileReference, MoveOptions, and CheckOptions are defined before their consumers, and all Python modules route through _native.

