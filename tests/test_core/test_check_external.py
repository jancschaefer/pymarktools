"""Tests for the check command extensions."""

import pytest

from pymarktools.core.markdown import DeadImageChecker, DeadLinkChecker

# Test data
SAMPLE_MARKDOWN_LINKS = """
# Sample Markdown

This is a [test link](https://example.com) and another [link with redirect](https://old-domain.com).
"""

SAMPLE_MARKDOWN_IMAGES = """
# Sample Markdown

And here's an image: ![test image](https://example.com/image.png)
"""


@pytest.fixture
def temp_markdown_links_file(tmp_path):
    """Create a temporary markdown file with links for testing."""
    file_path = tmp_path / "test_links.md"
    file_path.write_text(SAMPLE_MARKDOWN_LINKS)
    return file_path


@pytest.fixture
def temp_markdown_images_file(tmp_path):
    """Create a temporary markdown file with images for testing."""
    file_path = tmp_path / "test_images.md"
    file_path.write_text(SAMPLE_MARKDOWN_IMAGES)
    return file_path


def test_link_checker_with_external_check():
    """Test that the check_external option works."""
    # With check_external=False
    checker = DeadLinkChecker(check_external=False)
    content = SAMPLE_MARKDOWN_LINKS
    links = checker.extract_links(content)
    assert len(links) == 2

    # Since check_external=False, all links should be marked valid without HTTP requests
    for link in links:
        assert link.is_valid is None  # Not yet checked


def test_link_checker_fix_redirects(temp_markdown_links_file):
    """Test directly testing that fix_redirects updates content."""
    # Create test content with the "before" URL
    test_content = "\n# Sample Markdown\n\nThis is a [test link](https://example.com) and another [link with redirect](https://old-domain.com).\n"
    temp_markdown_links_file.write_text(test_content)

    # Mock the checker.check_url method directly
    checker = DeadLinkChecker(check_external=True, fix_redirects=True)

    def mock_check_url(url):
        # For testing, print the URL
        print(f"Checking URL: {url}")
        if url == "https://old-domain.com":
            print("Matched old domain URL, returning redirect")
            return {
                "is_valid": True,
                "status_code": 301,
                "error": None,
                "redirect_url": "https://new-domain.com",
                "is_permanent_redirect": True,
            }
        print(f"No match for {url}, returning normal result")
        return {
            "is_valid": True,
            "status_code": 200,
            "error": None,
            "redirect_url": None,
            "is_permanent_redirect": False,
        }

    # Replace the method
    checker.check_url = mock_check_url  # type: ignore[method-assign]

    # Run the check
    links = checker.check_file(temp_markdown_links_file)

    # Verify the file was updated
    assert len(links) == 2
    found_updated = False
    for link in links:
        if link.text == "link with redirect":
            assert link.updated
            assert link.url == "https://new-domain.com"
            found_updated = True

    assert found_updated, "The link should have been updated"

    # Check the file content was actually modified
    content = temp_markdown_links_file.read_text()
    assert "https://new-domain.com" in content
    assert "https://old-domain.com" not in content


def test_image_checker_fix_redirects(temp_markdown_images_file):
    """Test directly testing that fix_redirects updates content."""
    # Create test content with the "before" URL
    test_content = "\n# Sample Markdown\n\nAnd here's an image: ![test image](https://example.com/image.png)\n"
    temp_markdown_images_file.write_text(test_content)

    # Mock the checker.check_url method directly
    checker = DeadImageChecker(check_external=True, fix_redirects=True)

    def mock_check_url_image(url):
        if url == "https://example.com/image.png":
            return {
                "is_valid": True,
                "status_code": 301,
                "error": None,
                "redirect_url": "https://new-example.com/image.png",
                "is_permanent_redirect": True,
            }
        return {
            "is_valid": True,
            "status_code": 200,
            "error": None,
            "redirect_url": None,
            "is_permanent_redirect": False,
        }

    # Replace the method
    checker.check_url = mock_check_url_image  # type: ignore[method-assign]

    # Run the check
    images = checker.check_file(temp_markdown_images_file)

    # Verify the file was updated
    assert len(images) == 1
    assert images[0].updated
    assert images[0].url == "https://new-example.com/image.png"

    # Check the file content was actually modified
    content = temp_markdown_images_file.read_text()
    assert "https://new-example.com/image.png" in content
