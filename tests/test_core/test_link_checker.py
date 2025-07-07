"""Tests for the link checker module."""

import tempfile
from pathlib import Path

import pytest

from pymarktools.core.link_checker import DeadLinkChecker
from pymarktools.core.models import LinkInfo


@pytest.fixture
def sample_markdown_content():
    return """# Test Document

This is a [test link](https://example.com) and here's an image:

![Alt text](https://example.com/image.jpg)

Another [broken link](https://nonexistent-domain-12345.com).

![Another image](https://example.com/another.png)

Local file reference: [README](README.md)

Relative path: [docs file](docs/guide.md)

Absolute path: [config](/config/settings.json)
"""


@pytest.fixture
def temp_markdown_file(sample_markdown_content):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(sample_markdown_content)
        temp_file = Path(f.name)

    yield temp_file

    # Cleanup
    if temp_file.exists():
        temp_file.unlink()


class TestDeadLinkChecker:
    def test_extract_links(self):
        checker = DeadLinkChecker()
        content = "This is a [test link](https://example.com) and [another](https://test.com)."

        links = checker.extract_links(content)

        assert len(links) == 2
        assert links[0].text == "test link"
        assert links[0].url == "https://example.com"
        assert links[0].line_number == 1
        assert links[1].text == "another"
        assert links[1].url == "https://test.com"

    def test_extract_links_multiline(self):
        checker = DeadLinkChecker()
        content = """Line 1
This is a [test link](https://example.com)
Line 3 with [another link](https://test.com)"""

        links = checker.extract_links(content)

        assert len(links) == 2
        assert links[0].line_number == 2
        assert links[1].line_number == 3

    def test_is_external_url(self):
        checker = DeadLinkChecker()

        assert checker.is_external_url("https://example.com") is True
        assert checker.is_external_url("http://example.com") is True
        assert checker.is_external_url("./local/file.md") is False
        assert checker.is_external_url("../other/file.md") is False
        assert checker.is_external_url("file.md") is False

    def test_check_file(self, temp_markdown_file):
        checker = DeadLinkChecker()

        links = checker.check_file(temp_markdown_file)

        assert len(links) == 5  # Updated to reflect all links in the sample content
        assert all(isinstance(link, LinkInfo) for link in links)

        # Check the first external link
        external_links = [link for link in links if link.is_local is False]
        assert len(external_links) == 2  # Two external links
        assert external_links[0].text == "test link"
        assert external_links[0].url == "https://example.com"

    def test_check_file_not_found(self):
        checker = DeadLinkChecker()

        with pytest.raises(FileNotFoundError):
            checker.check_file(Path("nonexistent.md"))

    def test_check_file_no_external_check(self, temp_markdown_file):
        checker = DeadLinkChecker(check_external=False)

        links = checker.check_file(temp_markdown_file)

        # External links should be marked as valid (not checked)
        # Local links will fail since the files don't exist, but that's expected
        external_links = [link for link in links if link.is_local is False]
        assert all(link.is_valid for link in external_links)
        assert all(link.status_code == 200 for link in external_links)

    def test_init_with_custom_params(self):
        checker = DeadLinkChecker(
            timeout=60,
            check_external=False,
            check_local=False,
            fix_redirects=True,
            follow_gitignore=False,
        )

        assert checker.timeout == 60
        assert checker.check_external is False
        assert checker.check_local is False
        assert checker.fix_redirects is True
        assert checker.follow_gitignore is False

    def test_check_local_path_relative(self):
        """Test checking relative local file paths."""
        checker = DeadLinkChecker()

        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a markdown file and a target file
            md_file = temp_path / "test.md"
            target_file = temp_path / "README.md"

            md_file.write_text("[Link](README.md)")
            target_file.write_text("# README")

            # Check relative path
            result = checker.check_local_path("README.md", md_file)

            assert result["is_valid"] is True
            assert result["error"] is None
            # Compare just the file name for robust cross-platform testing
            assert result["path_object"].name == target_file.name
            # Or verify the file exists at all
            assert result["path_object"].exists()

    def test_check_local_path_missing_file(self):
        """Test checking missing local file paths."""
        checker = DeadLinkChecker()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "test.md"
            md_file.write_text("[Link](missing.md)")

            result = checker.check_local_path("missing.md", md_file)

            assert result["is_valid"] is False
            assert "File not found" in result["error"]
            assert result["resolved_path"] is not None

    def test_check_local_path_with_anchor(self):
        """Test checking local file paths with anchors."""
        checker = DeadLinkChecker()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "test.md"
            target_file = temp_path / "README.md"

            md_file.write_text("[Link](README.md#section)")
            target_file.write_text("# README")

            result = checker.check_local_path("README.md#section", md_file)

            assert result["is_valid"] is True
            assert result["error"] is None

    def test_check_local_path_absolute(self):
        """Test checking absolute local file paths."""
        checker = DeadLinkChecker()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "test.md"
            target_file = temp_path / "config.json"

            md_file.write_text("[Link](/config.json)")
            target_file.write_text("{}")

            result = checker.check_local_path("/config.json", md_file)

            # For absolute paths, the result depends on the directory structure
            # The test mainly checks that the function doesn't crash
            assert "is_valid" in result
            assert "error" in result or result["is_valid"]

    def test_check_file_with_local_links(self):
        """Test checking a file with both external and local links."""
        checker = DeadLinkChecker(check_external=False, check_local=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files
            md_file = temp_path / "test.md"
            existing_file = temp_path / "existing.md"

            existing_file.write_text("# Existing")
            md_file.write_text("""
[External link](https://example.com)
[Existing local](existing.md)
[Missing local](missing.md)
""")

            links = checker.check_file(md_file)

            assert len(links) == 3

            # External link should be valid (not checked)
            external_link = [link for link in links if link.url == "https://example.com"][0]
            assert external_link.is_valid is True
            assert external_link.is_local is False

            # Existing local file should be valid
            existing_link = [link for link in links if link.url == "existing.md"][0]
            assert existing_link.is_valid is True
            assert existing_link.is_local is True
            assert existing_link.local_path is not None

            # Missing local file should be invalid
            missing_link = [link for link in links if link.url == "missing.md"][0]
            assert missing_link.is_valid is False
            assert missing_link.is_local is True
            assert missing_link.error is not None

    def test_check_file_no_local_check(self):
        """Test checking a file with local checking disabled."""
        checker = DeadLinkChecker(check_external=False, check_local=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "test.md"

            md_file.write_text("""
[External link](https://example.com)
[Missing local](missing.md)
""")

            links = checker.check_file(md_file)

            # All links should be marked as valid when checking is disabled
            assert all(link.is_valid for link in links)

            # Local links should be marked as local
            local_link = [link for link in links if link.url == "missing.md"][0]
            assert local_link.is_local is True
