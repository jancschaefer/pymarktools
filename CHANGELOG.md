# Pymarktools Changelog

## [unreleased]

## [0.3.0] - 2025-07-16

### Added

- `--fail/--no-fail` option for the `check` command to control exit behavior.

### Changed

- **Restructured check command API**: Removed `check dead-links` and `check dead-images` subcommands and replaced with unified `check` command.
- **New options**: Added `--check-dead-links/--no-check-dead-links` and `--check-dead-images/--no-check-dead-images` options (both default to enabled).
- **Default behavior**: When no path specified, check current working directory; when path specified, check that specific file or directory.
- **Both checks run by default**: Users can disable either check type selectively with the new flags.
- **Migration required**: Old syntax `pymarktools check dead-links docs/` becomes `pymarktools check docs/ --no-check-dead-images`.

## [0.2.0] - 2025-07-08

### [0.2.0] - Added

- Global `--version` option to the CLI, allowing users to display the current pymarktools version and exit. Implements
    Typer's recommended approach for version callbacks.
- Added this changelog
- Added `.vscode` extension recommendations

### [0.2.0] - Changed

- Adjusted Readme for more clarity
- Adjusted Project description and metadata for pypi

### [0.2.0] - Fixed

- Fixed bug where email links with `mailto:` scheme were incorrectly treated as local file paths instead of external
    URLs. Email links are now properly recognized as external and validated by checking domain existence rather than
    being flagged as missing local files.

## [0.1.0] - 2025-07-08

### [0.1.0] - Added

- Initial release of pymarktools.
- CLI for markdown link and image validation.
- Async processing for external URL checks with configurable workers.
- Gitignore support for directory scanning.
- File refactoring with reference updating.
- Comprehensive test suite and CI/CD integration.
