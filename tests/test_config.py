"""Tests for pyproject.toml configuration support."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pymarktools.check_options import check_options
from pymarktools.config import find_pyproject_toml, load_pyproject_config, merge_check_options


@pytest.fixture
def temp_pyproject():
    """Create a temporary pyproject.toml file."""
    content = """[tool.pymarktools]
paths = ["src", "docs"]
timeout = 5
check_external = false
check_local = true
include_pattern = "*.md"
exclude_pattern = "test_*.md"
parallel = false
fail = false
workers = 2
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(content)
        temp_file = Path(f.name)

    yield temp_file

    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


@pytest.fixture
def temp_directory_with_pyproject():
    """Create a temporary directory with a pyproject.toml file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pyproject_path = temp_path / "pyproject.toml"

        content = """[tool.pymarktools]
paths = [".", "tests"]
timeout = 3
check_external = true
parallel = true
"""
        pyproject_path.write_text(content)

        yield temp_path, pyproject_path


class TestFindPyprojectToml:
    """Tests for finding pyproject.toml files."""

    def test_find_pyproject_in_current_directory(self, temp_directory_with_pyproject):
        """Test finding pyproject.toml in the current directory."""
        temp_path, pyproject_path = temp_directory_with_pyproject

        # Change to the temp directory
        with patch("pathlib.Path.cwd", return_value=temp_path):
            found_path = find_pyproject_toml()
            assert found_path is not None
            assert found_path.resolve() == pyproject_path.resolve()

    def test_find_pyproject_in_parent_directory(self, temp_directory_with_pyproject):
        """Test finding pyproject.toml in a parent directory."""
        temp_path, pyproject_path = temp_directory_with_pyproject

        # Create a subdirectory
        subdir = temp_path / "subdir"
        subdir.mkdir()

        # Search from subdirectory should find parent's pyproject.toml
        found_path = find_pyproject_toml(subdir)
        assert found_path is not None
        assert found_path.resolve() == pyproject_path.resolve()

    def test_find_pyproject_not_found(self):
        """Test when pyproject.toml is not found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            found_path = find_pyproject_toml(temp_path)
            assert found_path is None

    def test_find_pyproject_explicit_path(self, temp_pyproject):
        """Test finding pyproject.toml with explicit start path."""
        # Rename to pyproject.toml for this test
        pyproject_path = temp_pyproject.parent / "pyproject.toml"
        temp_pyproject.rename(pyproject_path)

        try:
            found_path = find_pyproject_toml(temp_pyproject.parent)
            assert found_path is not None
            assert found_path.resolve() == pyproject_path.resolve()
        finally:
            if pyproject_path.exists():
                pyproject_path.unlink()


class TestLoadPyprojectConfig:
    """Tests for loading configuration from pyproject.toml."""

    def test_load_config_from_file(self, temp_pyproject):
        """Test loading configuration from a specific file."""
        # Rename to pyproject.toml for this test
        pyproject_path = temp_pyproject.parent / "pyproject.toml"
        temp_pyproject.rename(pyproject_path)

        try:
            config = load_pyproject_config(pyproject_path)

            assert config["timeout"] == 5
            assert config["check_external"] is False
            assert config["check_local"] is True
            assert config["paths"] == ["src", "docs"]
            assert config["include_pattern"] == "*.md"
            assert config["exclude_pattern"] == "test_*.md"
            assert config["parallel"] is False
            assert config["fail"] is False
            assert config["workers"] == 2
        finally:
            if pyproject_path.exists():
                pyproject_path.unlink()

    def test_load_config_file_not_found(self):
        """Test loading configuration when file doesn't exist."""
        config = load_pyproject_config(Path("/nonexistent/pyproject.toml"))
        assert config == {}

    def test_load_config_no_tool_section(self):
        """Test loading configuration when tool.pymarktools section doesn't exist."""
        content = """[project]
name = "test"
version = "1.0.0"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            temp_file = Path(f.name)

        try:
            pyproject_path = temp_file.parent / "pyproject.toml"
            temp_file.rename(pyproject_path)

            config = load_pyproject_config(pyproject_path)
            assert config == {}
        finally:
            if pyproject_path.exists():
                pyproject_path.unlink()

    def test_load_config_invalid_toml(self):
        """Test loading configuration with invalid TOML."""
        content = """[tool.pymarktools
invalid toml
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(content)
            temp_file = Path(f.name)

        try:
            pyproject_path = temp_file.parent / "pyproject.toml"
            temp_file.rename(pyproject_path)

            config = load_pyproject_config(pyproject_path)
            assert config == {}  # Should return empty dict on error
        finally:
            if pyproject_path.exists():
                pyproject_path.unlink()


class TestMergeCheckOptions:
    """Tests for merging configuration options."""

    def test_merge_with_pyproject_config(self):
        """Test merging options with pyproject.toml configuration."""
        pyproject_config = {
            "timeout": 5,
            "check_external": False,
            "paths": ["src", "docs"],
        }

        merged_options, paths = merge_check_options(check_options, pyproject_config, {})

        assert merged_options["timeout"] == 5
        assert merged_options["check_external"] is False
        assert merged_options["check_local"] is True  # Default preserved
        assert paths == [Path("src"), Path("docs")]

    def test_merge_with_cli_overrides(self):
        """Test that CLI overrides take precedence."""
        pyproject_config = {
            "timeout": 5,
            "check_external": False,
        }
        cli_overrides = {
            "timeout": 8,
            "parallel": False,
        }

        merged_options, paths = merge_check_options(check_options, pyproject_config, cli_overrides)

        assert merged_options["timeout"] == 8  # CLI override
        assert merged_options["check_external"] is False  # From pyproject
        assert merged_options["parallel"] is False  # CLI override
        assert merged_options["check_local"] is True  # Default preserved
        assert paths == []  # No paths configured

    def test_merge_paths_string_to_list(self):
        """Test converting single path string to list."""
        pyproject_config = {
            "paths": "src",
        }

        merged_options, paths = merge_check_options(check_options, pyproject_config, {})

        assert paths == [Path("src")]

    def test_merge_output_path_conversion(self):
        """Test converting output string to Path object."""
        pyproject_config = {
            "output": "report.txt",
        }

        merged_options, paths = merge_check_options(check_options, pyproject_config, {})

        assert merged_options["output"] == Path("report.txt")

    def test_merge_workers_type_conversion(self):
        """Test converting workers to integer."""
        pyproject_config = {
            "workers": "4",
        }

        merged_options, paths = merge_check_options(check_options, pyproject_config, {})

        assert merged_options["workers"] == 4

    def test_merge_boolean_options(self):
        """Test boolean option handling."""
        pyproject_config = {
            "check_external": True,
            "check_local": False,
            "fix_redirects": True,
            "follow_gitignore": False,
            "parallel": True,
            "fail": False,
            "check_dead_links": False,
            "check_dead_images": True,
        }

        merged_options, paths = merge_check_options(check_options, pyproject_config, {})

        assert merged_options["check_external"] is True
        assert merged_options["check_local"] is False
        assert merged_options["fix_redirects"] is True
        assert merged_options["follow_gitignore"] is False
        assert merged_options["parallel"] is True
        assert merged_options["fail"] is False
        assert merged_options["check_dead_links"] is False
        assert merged_options["check_dead_images"] is True

    def test_merge_ignore_unknown_options(self):
        """Test that unknown options are ignored."""
        pyproject_config = {
            "timeout": 4,
            "unknown_option": "value",
            "another_unknown": True,
        }

        merged_options, paths = merge_check_options(check_options, pyproject_config, {})

        assert merged_options["timeout"] == 4
        assert "unknown_option" not in merged_options
        assert "another_unknown" not in merged_options
