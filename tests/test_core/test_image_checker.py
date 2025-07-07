"""Tests for the image checker module."""

import tempfile
from pathlib import Path

import pytest

from pymarktools.core.image_checker import DeadImageChecker
from pymarktools.core.models import ImageInfo


@pytest.fixture
def sample_markdown_content():
    return """# Test Document

This is a [test link](https://example.com) and here's an image:

![Alt text](https://example.com/image.jpg)

Another [broken link](https://nonexistent-domain-12345.com).

![Another image](https://example.com/another.png)

Local image: ![Local image](assets/logo.png)

Relative image: ![Guide image](../images/guide.jpg)
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


class TestDeadImageChecker:
    def test_extract_images(self):
        checker = DeadImageChecker()
        content = (
            "Here's an image: ![Alt text](https://example.com/image.jpg) and ![Another](https://test.com/pic.png)."
        )

        images = checker.extract_images(content)

        assert len(images) == 2
        assert images[0].alt_text == "Alt text"
        assert images[0].url == "https://example.com/image.jpg"
        assert images[0].line_number == 1
        assert images[1].alt_text == "Another"
        assert images[1].url == "https://test.com/pic.png"

    def test_extract_images_multiline(self):
        checker = DeadImageChecker()
        content = """Line 1
![First image](https://example.com/1.jpg)
Line 3 with ![second image](https://test.com/2.png)"""

        images = checker.extract_images(content)

        assert len(images) == 2
        assert images[0].line_number == 2
        assert images[1].line_number == 3

    def test_is_external_url(self):
        checker = DeadImageChecker()

        assert checker.is_external_url("https://example.com/image.jpg") is True
        assert checker.is_external_url("http://example.com/image.png") is True
        assert checker.is_external_url("./local/image.jpg") is False
        assert checker.is_external_url("../other/image.png") is False
        assert checker.is_external_url("image.jpg") is False

    def test_check_file(self, temp_markdown_file):
        checker = DeadImageChecker()

        images = checker.check_file(temp_markdown_file)

        assert len(images) == 4  # Updated to reflect all images in the sample content
        assert all(isinstance(image, ImageInfo) for image in images)

        # Check the first external image
        external_images = [image for image in images if image.is_local is False]
        assert len(external_images) == 2  # Two external images
        assert external_images[0].alt_text == "Alt text"
        assert external_images[0].url == "https://example.com/image.jpg"

    def test_check_file_not_found(self):
        checker = DeadImageChecker()

        with pytest.raises(FileNotFoundError):
            checker.check_file(Path("nonexistent.md"))

    def test_check_file_no_external_check(self, temp_markdown_file):
        checker = DeadImageChecker(check_external=False)

        images = checker.check_file(temp_markdown_file)

        # External images should be marked as valid (not checked)
        # Local images will fail since the files don't exist, but that's expected
        external_images = [image for image in images if image.is_local is False]
        assert all(image.is_valid for image in external_images)
        assert all(image.status_code == 200 for image in external_images)

    def test_init_with_custom_params(self):
        checker = DeadImageChecker(
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
        """Test checking relative local image paths."""
        checker = DeadImageChecker()

        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a markdown file and a target image
            md_file = temp_path / "test.md"
            target_image = temp_path / "logo.png"

            md_file.write_text("![Logo](logo.png)")
            target_image.write_text("fake png content")

            # Check relative path
            result = checker.check_local_path("logo.png", md_file)

            assert result["is_valid"] is True
            assert result["error"] is None
            # Compare just the file name for robust cross-platform testing
            assert result["path_object"].name == target_image.name
            # Or verify the file exists at all
            assert result["path_object"].exists()

    def test_check_local_path_missing_image(self):
        """Test checking missing local image paths."""
        checker = DeadImageChecker()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "test.md"
            md_file.write_text("![Missing](missing.png)")

            result = checker.check_local_path("missing.png", md_file)

            assert result["is_valid"] is False
            assert "File not found" in result["error"]
            assert result["resolved_path"] is not None

    def test_check_file_with_local_images(self):
        """Test checking a file with both external and local images."""
        checker = DeadImageChecker(check_external=False, check_local=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files
            md_file = temp_path / "test.md"
            existing_image = temp_path / "existing.png"

            existing_image.write_text("fake png content")
            md_file.write_text("""
![External image](https://example.com/image.jpg)
![Existing local](existing.png)
![Missing local](missing.png)
""")

            images = checker.check_file(md_file)

            assert len(images) == 3

            # External image should be valid (not checked)
            external_image = [image for image in images if image.url == "https://example.com/image.jpg"][0]
            assert external_image.is_valid is True
            assert external_image.is_local is False

            # Existing local file should be valid
            existing_image_info = [image for image in images if image.url == "existing.png"][0]
            assert existing_image_info.is_valid is True
            assert existing_image_info.is_local is True
            assert existing_image_info.local_path is not None

            # Missing local file should be invalid
            missing_image = [image for image in images if image.url == "missing.png"][0]
            assert missing_image.is_valid is False
            assert missing_image.is_local is True
            assert missing_image.error is not None

    def test_check_file_no_local_check(self):
        """Test checking a file with local checking disabled."""
        checker = DeadImageChecker(check_external=False, check_local=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "test.md"

            md_file.write_text("""
![External image](https://example.com/image.jpg)
![Missing local](missing.png)
""")

            images = checker.check_file(md_file)

            # All images should be marked as valid when checking is disabled
            assert all(image.is_valid for image in images)

            # Local images should be marked as local
            local_image = [image for image in images if image.url == "missing.png"][0]
            assert local_image.is_local is True
