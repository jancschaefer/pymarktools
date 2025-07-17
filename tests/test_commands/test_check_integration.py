"""Integration tests for pyproject.toml configuration with check command."""

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pymarktools.cli import app


@pytest.fixture
def runner():
    return CliRunner(
        env={
            "PYMARKTOOLS_COLOR": "false",
            "NO_COLOR": "1",
            "FORCE_COLOR": "0",
            "_TYPER_COMPLETE_TEST_DISABLE_SHELL_COMPLETION": "1",
        }
    )


@contextmanager
def change_dir(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


@pytest.fixture
def temp_project_with_config():
    """Create a temporary project directory with pyproject.toml and markdown files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create pyproject.toml
        pyproject_content = """[tool.pymarktools]
paths = ["docs"]
timeout = 3
check_external = false
parallel = false
fail = false
include_pattern = "*.md"
"""
        (temp_path / "pyproject.toml").write_text(pyproject_content)

        # Create docs directory with markdown file
        docs_dir = temp_path / "docs"
        docs_dir.mkdir()

        md_content = """# Test Document

This has a [broken local link](./nonexistent.md).
"""
        (docs_dir / "test.md").write_text(md_content)

        yield temp_path


class TestCheckCommandIntegration:
    """Integration tests for check command with pyproject.toml configuration."""

    def test_check_uses_pyproject_config(self, runner, temp_project_with_config):
        """Test that check command loads and uses pyproject.toml configuration."""
        # Change to the project directory and run check without arguments
        with change_dir(temp_project_with_config):
            result = runner.invoke(app, ["check"])

        # Should use configuration values
        assert result.exit_code == 0  # fail = false in config
        assert "timeout: 3s" in result.stdout  # Custom timeout from config
        assert "Checking external: False" in result.stdout  # check_external = false
        assert "Parallel processing: False" in result.stdout  # parallel = false
        assert "docs/test.md" in result.stdout  # Should check the docs directory

    def test_cli_args_override_config(self, runner, temp_project_with_config):
        """Test that CLI arguments override pyproject.toml values."""
        # Override timeout with CLI argument
        with change_dir(temp_project_with_config):
            result = runner.invoke(app, ["check", "--timeout", "2", "--check-external"])

        # Should use CLI values instead of config
        assert "timeout: 2s" in result.stdout  # CLI override
        assert "Checking external: True" in result.stdout  # CLI override
        assert "Parallel processing: False" in result.stdout  # Still from config

    def test_explicit_path_overrides_config_paths(self, runner, temp_project_with_config):
        """Test that explicit path argument overrides paths from config."""
        # Create a different markdown file
        other_file = temp_project_with_config / "other.md"
        other_file.write_text("# Other file\n\nNo links here.")

        # Run with explicit path
        with change_dir(temp_project_with_config):
            result = runner.invoke(app, ["check", str(other_file)])

        # Should check the explicit file, not the paths from config
        assert "other.md" in result.stdout
        assert "docs/test.md" not in result.stdout

    def test_check_without_config_uses_defaults(self, runner):
        """Test that check command uses defaults when no pyproject.toml exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a simple markdown file
            md_file = temp_path / "test.md"
            md_file.write_text("# Test\n\nJust some text.")

            with change_dir(temp_path):
                result = runner.invoke(app, ["check", str(md_file)])

            # Should use default values
            assert "timeout: 30s" in result.stdout  # Default timeout
            assert "Checking external: True" in result.stdout  # Default check_external
            assert "Parallel processing: True" in result.stdout  # Default parallel
