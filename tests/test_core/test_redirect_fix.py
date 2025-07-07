"""Direct tests for fixing redirects in markdown files."""

from pathlib import Path

from pymarktools.core.markdown import DeadImageChecker, DeadLinkChecker


def test_link_redirect_fix():
    """Test fixing redirects for links directly."""
    # Create a temporary file
    temp_dir = Path("./temp_test")
    temp_dir.mkdir(exist_ok=True)
    test_file = temp_dir / "test_links.md"

    try:
        # Create test content with the "before" URL
        test_content = "\n# Sample Markdown\n\nThis is a [test link](https://example.com) and another [link with redirect](https://old-domain.com).\n"
        test_file.write_text(test_content)

        # Create a custom link checker that handles our test URLs
        class TestLinkChecker(DeadLinkChecker):
            def check_url(self, url):
                if url == "https://old-domain.com":
                    return {
                        "is_valid": True,
                        "status_code": 301,
                        "error": None,
                        "redirect_url": "https://new-domain.com",
                        "is_permanent_redirect": True,
                    }
                return {
                    "is_valid": True,
                    "status_code": 200,
                    "error": None,
                    "redirect_url": None,
                    "is_permanent_redirect": False,
                }

        # Run the check with our custom checker
        checker = TestLinkChecker(check_external=True, fix_redirects=True)
        links = checker.check_file(test_file)

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
        content = test_file.read_text()
        assert "https://new-domain.com" in content
        assert "https://old-domain.com" not in content

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
        if temp_dir.exists():
            temp_dir.rmdir()


def test_image_redirect_fix():
    """Test fixing redirects for images directly."""
    # Create a temporary file
    temp_dir = Path("./temp_test")
    temp_dir.mkdir(exist_ok=True)
    test_file = temp_dir / "test_images.md"

    try:
        # Create test content with the "before" URL
        test_content = "\n# Sample Markdown\n\nAnd here's an image: ![test image](https://example.com/image.png)\n"
        test_file.write_text(test_content)

        # Create a custom image checker that handles our test URLs
        class TestImageChecker(DeadImageChecker):
            def check_url(self, url):
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

        # Run the check with our custom checker
        checker = TestImageChecker(check_external=True, fix_redirects=True)
        images = checker.check_file(test_file)

        # Verify the file was updated
        assert len(images) == 1
        assert images[0].updated
        assert images[0].url == "https://new-example.com/image.png"

        # Check the file content was actually modified
        content = test_file.read_text()
        assert "https://new-example.com/image.png" in content
        assert "https://example.com/image.png" not in content

    finally:
        # Clean up
        if test_file.exists():
            test_file.unlink()
        if temp_dir.exists():
            temp_dir.rmdir()
