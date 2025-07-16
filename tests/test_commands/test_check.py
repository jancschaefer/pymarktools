"""Tests for the unified check command."""

import tempfile
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


@pytest.fixture
def temp_markdown_file():
    """Temporary markdown file with sample content."""
    content = """# Test Document

This is a [test link](./local.md) and here's an image:

![Alt text](./image.png)
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(content)
        temp_file = Path(f.name)

    # Create referenced files in the same directory
    temp_dir = temp_file.parent
    local_file = temp_dir / "local.md"
    local_file.write_text("# Local file")

    image_file = temp_dir / "image.png"
    image_file.write_bytes(b"fake image content")

    yield temp_file

    # Cleanup
    for file in [temp_file, local_file, image_file]:
        if file.exists():
            file.unlink()


@pytest.fixture
def temp_directory_with_files():
    """Temporary directory with multiple markdown files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create main markdown file
        main_file = temp_path / "main.md"
        main_file.write_text("""# Main Document

This is a [test link](./local.md).

![Test image](./image.png)
""")

        # Create the referenced local file
        local_file = temp_path / "local.md"
        local_file.write_text("# Local file")

        # Create the referenced image file
        image_file = temp_path / "image.png"
        image_file.write_bytes(b"fake image content")

        # Create draft file (for exclude pattern testing)
        draft_file = temp_path / "draft_notes.md"
        draft_file.write_text("""# Draft Notes

Draft content with [link](./local.md).
""")

        # Create ignored file
        ignored_file = temp_path / "ignored.txt"
        ignored_file.write_text("Not markdown content")

        yield temp_path


def test_both_checks_disabled_error(runner, temp_markdown_file):
    """Test that disabling both checks raises an error."""
    result = runner.invoke(app, ["check", str(temp_markdown_file), "--no-check-dead-links", "--no-check-dead-images"])
    assert result.exit_code == 1
    assert "Both checks disabled; nothing to do" in result.output


def test_verbose_output_with_exclude_pattern(runner, temp_directory_with_files):
    """Test that exclude pattern is shown in verbose output."""
    result = runner.invoke(
        app, ["--verbose", "check", str(temp_directory_with_files), "--no-check-external", "--exclude", "draft_*"]
    )
    assert result.exit_code == 0
    assert "Verbose mode enabled" in result.output
    assert "Exclude pattern: draft_*" in result.output


def test_verbose_output_with_workers_option(runner, temp_markdown_file):
    """Test that worker count is shown in verbose output."""
    result = runner.invoke(
        app, ["--verbose", "check", str(temp_markdown_file), "--no-check-external", "--workers", "4"]
    )
    assert result.exit_code == 0
    assert "Worker threads: 4" in result.output


def test_verbose_output_with_output_file(runner, temp_markdown_file):
    """Test that output file is shown in verbose output."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as output_file:
        output_path = Path(output_file.name)

    try:
        result = runner.invoke(
            app, ["--verbose", "check", str(temp_markdown_file), "--no-check-external", "--output", str(output_path)]
        )
        assert result.exit_code == 0
        assert f"Report will be saved to: {output_path}" in result.output
    finally:
        if output_path.exists():
            output_path.unlink()


def test_directory_with_parallel_disabled(runner, temp_directory_with_files):
    """Test directory processing with parallel disabled (fallback to sync)."""
    result = runner.invoke(app, ["check", str(temp_directory_with_files), "--no-check-external", "--no-parallel"])
    assert result.exit_code == 0
    assert "Checking for dead links" in result.output
    assert "Checking for dead images" in result.output


def test_directory_with_parallel_enabled(runner, temp_directory_with_files):
    """Test directory processing with parallel enabled (async processing)."""
    result = runner.invoke(app, ["check", str(temp_directory_with_files), "--no-check-external", "--parallel"])
    assert result.exit_code == 0
    assert "Checking for dead links" in result.output
    assert "Checking for dead images" in result.output


def test_check_directory_with_include_exclude_patterns(runner, temp_directory_with_files):
    """Test that include and exclude patterns are passed to checker methods."""
    result = runner.invoke(
        app,
        ["check", str(temp_directory_with_files), "--no-check-external", "--include", "*.md", "--exclude", "draft_*"],
    )
    assert result.exit_code == 0
    # Should process main.md but exclude draft_notes.md
    assert "Found" in result.output


def test_directory_processing_patterns(runner, temp_directory_with_files):
    """Test that include and exclude patterns work with directory processing."""
    result = runner.invoke(
        app,
        [
            "--verbose",
            "check",
            str(temp_directory_with_files),
            "--no-check-external",
            "--include",
            "*.md",
            "--exclude",
            "draft_*",
        ],
    )
    assert result.exit_code == 0
    # Verify the patterns are shown in verbose output
    assert "Include pattern: *.md" in result.output
    assert "Exclude pattern: draft_*" in result.output


def test_check_only_links(runner, temp_markdown_file):
    """Test checking only links (images disabled)."""
    result = runner.invoke(app, ["check", str(temp_markdown_file), "--no-check-external", "--no-check-dead-images"])
    assert result.exit_code == 0
    assert "Checking for dead links" in result.output
    assert "Checking for dead images" not in result.output


def test_check_only_images(runner, temp_markdown_file):
    """Test checking only images (links disabled)."""
    result = runner.invoke(app, ["check", str(temp_markdown_file), "--no-check-external", "--no-check-dead-links"])
    assert result.exit_code == 0
    assert "Checking for dead images" in result.output
    assert "Checking for dead links" not in result.output


def test_default_path_current_directory(runner):
    """Test that check command defaults to current directory when no path provided."""
    # This test just verifies the CLI accepts no path argument
    # The actual directory checking is tested elsewhere
    result = runner.invoke(
        app,
        [
            "check",
            "--no-check-external",
            "--include",
            "nonexistent_pattern_*.md",  # Avoid finding actual files
        ],
    )
    # Should not error due to missing path argument
    assert result.exit_code == 0


def test_verbose_output_auto_detected_workers(runner, temp_markdown_file):
    """Test that auto-detected worker count is shown in verbose output."""
    result = runner.invoke(
        app,
        [
            "--verbose",
            "check",
            str(temp_markdown_file),
            "--no-check-external",
            # No --workers specified, should auto-detect
        ],
    )
    assert result.exit_code == 0
    assert "Worker threads:" in result.output
    assert "(auto-detected)" in result.output


def test_check_with_all_verbose_options(runner, temp_directory_with_files):
    """Test verbose output with all possible options to ensure coverage."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as output_file:
        output_path = Path(output_file.name)

    try:
        result = runner.invoke(
            app,
            [
                "--verbose",
                "check",
                str(temp_directory_with_files),
                "--no-check-external",
                "--include",
                "*.md",
                "--exclude",
                "draft_*",
                "--workers",
                "2",
                "--output",
                str(output_path),
                "--timeout",
                "10",
                "--follow-gitignore",
                "--fix-redirects",
                "--parallel",
                "--fail",
            ],
        )

        # Verify all verbose output lines are present
        assert "Verbose mode enabled" in result.output
        assert f"Checking in: {temp_directory_with_files}" in result.output
        assert "Using timeout: 10s" in result.output
        assert "Checking external: False" in result.output
        assert "Checking local files: True" in result.output
        assert "Fixing redirects: True" in result.output
        assert "Following gitignore: True" in result.output
        assert "Include pattern: *.md" in result.output
        assert "Exclude pattern: draft_*" in result.output
        assert "Parallel processing: True" in result.output
        assert "Worker threads: 2" in result.output
        assert f"Report will be saved to: {output_path}" in result.output
        assert "Fail on invalid items: True" in result.output

    finally:
        if output_path.exists():
            output_path.unlink()
