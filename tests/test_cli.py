import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pymarktools.cli import app


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_markdown_content():
    return """# Test Document

This is a [test link](https://example.com) and here's an image:

![Alt text](https://example.com/image.jpg)

Another [broken link](https://nonexistent-domain-12345.com).
"""


@pytest.fixture
def sample_valid_markdown_content():
    """Markdown content with only valid links for tests expecting success."""
    return """# Test Document

This is a [test link](https://example.com) and here's an image:

![Alt text](https://example.com/image.jpg)
"""


@pytest.fixture
def temp_markdown_file(sample_markdown_content):
    """Temporary markdown file with mixed valid and invalid links."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_markdown_content)
        temp_file = Path(f.name)

    yield temp_file

    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


@pytest.fixture
def temp_valid_markdown_file(sample_valid_markdown_content):
    """Temporary markdown file with only valid links."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_valid_markdown_content)
        temp_file = Path(f.name)

    yield temp_file

    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


def test_cli_help(runner):
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "pymarktools" in result.output


def test_check_dead_links_help(runner):
    result = runner.invoke(app, ["check", "dead-links", "--help"])
    assert result.exit_code == 0
    assert "Check for dead links" in result.output


def test_check_dead_images_help(runner):
    result = runner.invoke(app, ["check", "dead-images", "--help"])
    assert result.exit_code == 0
    assert "Check for dead images" in result.output


def test_check_dead_links_with_file(runner, temp_valid_markdown_file):
    result = runner.invoke(app, ["check", "dead-links", str(temp_valid_markdown_file)])
    assert result.exit_code == 0
    assert "Checking for dead links" in result.output
    assert "Found" in result.output


def test_check_dead_images_with_file(runner, temp_valid_markdown_file):
    result = runner.invoke(
        app,
        ["check", "dead-images", str(temp_valid_markdown_file), "--no-check-external"],
    )
    assert result.exit_code == 0
    assert "Checking for dead images" in result.output
    assert "Found" in result.output


def test_check_dead_links_with_invalid_links(runner, temp_markdown_file):
    """Test that invalid links cause exit code 1."""
    result = runner.invoke(app, ["check", "dead-links", str(temp_markdown_file)])
    assert result.exit_code == 1
    assert "Checking for dead links" in result.output
    assert "Found" in result.output


def test_check_dead_images_with_invalid_images(runner, temp_markdown_file):
    """Test that invalid images cause exit code 1."""
    result = runner.invoke(app, ["check", "dead-images", str(temp_markdown_file)])
    assert result.exit_code == 1
    assert "Checking for dead images" in result.output
    assert "Found" in result.output


def test_check_dead_links_nonexistent_file(runner):
    result = runner.invoke(app, ["check", "dead-links", "nonexistent.md"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_check_dead_images_nonexistent_file(runner):
    result = runner.invoke(app, ["check", "dead-images", "nonexistent.md"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_refactor_help(runner):
    result = runner.invoke(app, ["refactor", "--help"])
    assert result.exit_code == 0
    assert "Refactor and reorganize" in result.output


def test_refactor_move_help(runner):
    result = runner.invoke(app, ["refactor", "move", "--help"])
    assert result.exit_code == 0
    assert "Move a file and update all references" in result.output


def test_refactor_move_nonexistent_file(runner):
    result = runner.invoke(app, ["refactor", "move", "nonexistent.md", "new.md"])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_refactor_move_dry_run(runner, temp_markdown_file):
    # Create a temporary destination path
    dest = temp_markdown_file.parent / "moved.md"

    result = runner.invoke(app, ["refactor", "move", str(temp_markdown_file), str(dest), "--dry-run"])
    assert result.exit_code == 0
    assert "DRY RUN MODE" in result.output
    assert "Would move:" in result.output


def test_check_dead_links_respects_gitignore(runner):
    """Test that check dead-links respects .gitignore patterns."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a .gitignore file
        gitignore_content = """
# Ignore build directories
build/
dist/
node_modules/

# Ignore cache files
*.cache
__pycache__/

# Ignore specific files
ignore-me.md
"""
        (temp_path / ".gitignore").write_text(gitignore_content)

        # Create markdown files
        regular_md = temp_path / "regular.md"
        regular_md.write_text("# Regular File\n\n[Link](https://example.com)")

        ignored_md = temp_path / "ignore-me.md"
        ignored_md.write_text("# Ignored File\n\n[Link](https://broken-link.example)")

        # Create ignored directory with markdown
        build_dir = temp_path / "build"
        build_dir.mkdir()
        build_md = build_dir / "build.md"
        build_md.write_text("# Build File\n\n[Link](https://another-broken-link.example)")

        # Test with gitignore enabled (default)
        result = runner.invoke(app, ["check", "dead-links", str(temp_path), "--no-check-external"])
        assert result.exit_code == 0

        # Should only check regular.md, not the ignored files
        assert "regular.md" in result.output
        assert "ignore-me.md" not in result.output
        assert "build.md" not in result.output

        # Test with gitignore disabled
        result = runner.invoke(
            app,
            [
                "check",
                "dead-links",
                str(temp_path),
                "--no-check-external",
                "--no-follow-gitignore",
            ],
        )
        assert result.exit_code == 0

        # Should check all files when gitignore is disabled
        assert "regular.md" in result.output
        assert "ignore-me.md" in result.output
        assert "build.md" in result.output


def test_check_dead_images_respects_gitignore(runner):
    """Test that check dead-images respects .gitignore patterns."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a .gitignore file
        gitignore_content = """
# Ignore documentation
docs/
*.tmp
"""
        (temp_path / ".gitignore").write_text(gitignore_content)

        # Create markdown files
        regular_md = temp_path / "regular.md"
        regular_md.write_text("# Regular File\n\n![Image](image.jpg)")

        # Create the referenced image file so the test passes
        (temp_path / "image.jpg").write_text("fake jpg content")

        temp_md = temp_path / "temp.tmp"
        temp_md.write_text("# Temp File\n\n![Image](broken-image.jpg)")

        # Create ignored directory
        docs_dir = temp_path / "docs"
        docs_dir.mkdir()
        docs_md = docs_dir / "doc.md"
        docs_md.write_text("# Doc File\n\n![Image](doc-image.jpg)")

        # Test with gitignore enabled
        result = runner.invoke(app, ["check", "dead-images", str(temp_path), "--no-check-external"])
        assert result.exit_code == 0

        # Should only check regular.md
        assert "regular.md" in result.output
        assert "temp.tmp" not in result.output
        assert "doc.md" not in result.output


def test_gitignore_hierarchical_patterns(runner):
    """Test that gitignore patterns work hierarchically from repo root to subdirectories."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a root .gitignore
        root_gitignore = """
# Global ignores
*.log
temp/
"""
        (temp_path / ".gitignore").write_text(root_gitignore)

        # Create a subdirectory with its own .gitignore
        sub_dir = temp_path / "subdir"
        sub_dir.mkdir()
        sub_gitignore = """
# Local ignores
local-ignore.md
"""
        (sub_dir / ".gitignore").write_text(sub_gitignore)

        # Create test files
        (temp_path / "root.md").write_text("# Root\n\n[Link](https://example.com)")
        (temp_path / "test.log").write_text("# Log file (should be ignored)")

        temp_subdir = temp_path / "temp"
        temp_subdir.mkdir()
        (temp_subdir / "temp.md").write_text("# Temp\n\n[Link](https://example.com)")

        (sub_dir / "sub.md").write_text("# Sub\n\n[Link](https://example.com)")
        (sub_dir / "local-ignore.md").write_text("# Local ignore\n\n[Link](https://example.com)")

        # Test checking from root
        result = runner.invoke(app, ["check", "dead-links", str(temp_path), "--no-check-external"])
        assert result.exit_code == 0

        # Should find root.md and sub.md, but not ignored files
        assert "root.md" in result.output
        assert "sub.md" in result.output
        assert "test.log" not in result.output
        assert "temp.md" not in result.output
        assert "local-ignore.md" not in result.output

        # Test checking from subdirectory
        result = runner.invoke(app, ["check", "dead-links", str(sub_dir), "--no-check-external"])
        assert result.exit_code == 0

        # Should find sub.md but not local-ignore.md
        assert "sub.md" in result.output
        assert "local-ignore.md" not in result.output


def test_gitignore_with_git_repo_simulation(runner):
    """Test gitignore functionality in a simulated git repository structure."""
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a fake .git directory to simulate a git repo
        git_dir = temp_path / ".git"
        git_dir.mkdir()

        # Create .gitignore with common patterns
        gitignore_content = """
# Dependencies
node_modules/
.venv/

# Build outputs
dist/
build/
*.pyc
__pycache__/

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
"""
        (temp_path / ".gitignore").write_text(gitignore_content)

        # Create various files and directories
        (temp_path / "README.md").write_text("# Project\n\n[Link](https://example.com)")

        # Create ignored directories
        for ignored_dir in ["node_modules", ".venv", "dist", "__pycache__", ".vscode"]:
            dir_path = temp_path / ignored_dir
            dir_path.mkdir()
            (dir_path / "file.md").write_text("# Ignored\n\n[Link](https://example.com)")

        # Create ignored files
        (temp_path / ".DS_Store").write_text("binary file")
        (temp_path / "script.pyc").write_text("compiled python")

        # Test that only non-ignored files are checked
        result = runner.invoke(app, ["check", "dead-links", str(temp_path), "--no-check-external"])
        assert result.exit_code == 0

        # Should only check README.md
        assert "README.md" in result.output

        # Should not check any ignored files
        ignored_patterns = [
            "node_modules",
            ".venv",
            "dist",
            "__pycache__",
            ".vscode",
            ".DS_Store",
            ".pyc",
        ]
        for pattern in ignored_patterns:
            assert pattern not in result.output


def test_check_dead_links_local_files(runner):
    """Test checking local file links."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a markdown file with local links
        md_file = temp_path / "test.md"
        existing_file = temp_path / "existing.md"

        existing_file.write_text("# Existing File")
        md_file.write_text("""# Test Document

[External link](https://example.com)
[Existing local file](existing.md)
[Missing local file](missing.md)
[Local file with anchor](existing.md#section)
""")

        # Test with local checking enabled (default)
        result = runner.invoke(app, ["check", "dead-links", str(md_file), "--no-check-external"])
        assert result.exit_code == 1  # Should fail because missing.md doesn't exist

        # Should show local file status
        assert "[LOCAL]" in result.output
        assert "existing.md" in result.output
        assert "missing.md" in result.output


def test_check_dead_links_no_local_check(runner):
    """Test disabling local file checking."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a markdown file with local links
        md_file = temp_path / "test.md"
        md_file.write_text("""# Test Document

[Existing local file](existing.md)
[Missing local file](missing.md)
""")

        # Test with local checking disabled
        result = runner.invoke(
            app,
            [
                "check",
                "dead-links",
                str(md_file),
                "--no-check-external",
                "--no-check-local",
            ],
        )
        assert result.exit_code == 0

        # Should still show links but all marked as valid
        assert "existing.md" in result.output
        assert "missing.md" in result.output
        # When local checking is disabled, files should be marked as valid
        assert "[INVALID]" not in result.output


def test_check_dead_images_local_files(runner):
    """Test checking local image files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a markdown file with local images
        md_file = temp_path / "test.md"
        existing_image = temp_path / "logo.png"

        existing_image.write_text("fake png content")
        md_file.write_text("""# Test Document

![External image](https://example.com/image.jpg)
![Existing local image](logo.png)
![Missing local image](missing.png)
""")

        # Test with local checking enabled (default)
        result = runner.invoke(app, ["check", "dead-images", str(md_file), "--no-check-external"])
        assert result.exit_code == 1  # Should fail because missing.png doesn't exist

        # Should show local image status
        assert "[LOCAL]" in result.output
        assert "logo.png" in result.output
        assert "missing.png" in result.output


def test_check_dead_images_no_local_check(runner):
    """Test disabling local image checking."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a markdown file with local images
        md_file = temp_path / "test.md"
        md_file.write_text("""# Test Document

![Existing local image](logo.png)
![Missing local image](missing.png)
""")

        # Test with local checking disabled
        result = runner.invoke(
            app,
            [
                "check",
                "dead-images",
                str(md_file),
                "--no-check-external",
                "--no-check-local",
            ],
        )
        assert result.exit_code == 0

        # Should still show images but all marked as valid
        assert "logo.png" in result.output
        assert "missing.png" in result.output
        # When local checking is disabled, files should be marked as valid
        assert "[INVALID]" not in result.output


def test_check_local_path_resolution(runner):
    """Test different types of local path resolution."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create directory structure
        docs_dir = temp_path / "docs"
        assets_dir = temp_path / "assets"
        docs_dir.mkdir()
        assets_dir.mkdir()

        # Create files
        md_file = docs_dir / "test.md"
        (assets_dir / "image.png").write_text("fake png")
        (temp_path / "README.md").write_text("# Root README")

        md_file.write_text("""# Test Document

[Relative to parent](../README.md)
[Relative image](../assets/image.png)
[Missing relative](../missing.md)
""")

        # Test with local checking enabled
        result = runner.invoke(app, ["check", "dead-links", str(md_file), "--no-check-external"])
        assert result.exit_code == 1  # Should fail because ../missing.md doesn't exist

        # Should resolve relative paths correctly
        assert "README.md" in result.output
        assert "[LOCAL]" in result.output


def test_check_local_help_options(runner):
    """Test that help shows the new local checking options."""
    result = runner.invoke(app, ["check", "dead-links", "--help"])
    assert result.exit_code == 0
    assert "--check-local" in result.output
    assert "--no-check-local" in result.output
    assert "local file links" in result.output  # More flexible text check

    result = runner.invoke(app, ["check", "dead-images", "--help"])
    assert result.exit_code == 0
    assert "--check-local" in result.output
    assert "--no-check-local" in result.output
    assert "local file images" in result.output  # Should match "local file images exist"
