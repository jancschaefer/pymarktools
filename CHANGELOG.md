# Pymarktools Changelog

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
