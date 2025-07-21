from pathlib import Path

from pymarktools.core.async_checker import AsyncChecker


def test_discover_files_skips_ignored_root(tmp_path: Path) -> None:
    """Ensure discover_files_async returns no files when the given path is ignored."""
    (tmp_path / ".gitignore").write_text(".venv\n")
    # Simulate a git repository so parent .gitignore is respected
    (tmp_path / ".git").mkdir()
    ignored = tmp_path / ".venv"
    ignored.mkdir()
    (ignored / "file.md").write_text("content")

    checker = AsyncChecker()
    result = checker.run_async_with_fallback(checker.discover_files_async, ignored)
    assert result == []
