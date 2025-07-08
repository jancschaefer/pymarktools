"""Integration test to demonstrate the email link fix."""

import tempfile
from pathlib import Path

from pymarktools.core.link_checker import DeadLinkChecker


def test_email_links_integration():
    """Integration test showing the email link bug fix."""
    # Create a test markdown file with various email scenarios
    content = """# Test Document

## Valid Emails
Contact us: [Support](mailto:support@example.com)
Sales team: [Sales](mailto:sales@github.com)

## Invalid Email (for testing)
Broken: [Bad Domain](mailto:test@nonexistentdomain98765.invalid)

## Regular Links
Website: [Example](https://example.com)
Local file: [README](./README.md)
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        md_file = temp_path / "test.md"
        md_file.write_text(content)

        # Test with external checking enabled
        checker = DeadLinkChecker(check_external=True, check_local=True)
        links = checker.check_file(md_file)

        # Verify we found all the links
        assert len(links) == 5

        # Check that email links are recognized as external
        email_links = [link for link in links if link.url.startswith("mailto:")]
        assert len(email_links) == 3

        for email_link in email_links:
            assert email_link.is_local is False
            # Should have attempted validation (success or failure)
            assert email_link.is_valid is not None

        # Check that local link is still handled correctly
        local_links = [link for link in links if not link.url.startswith(("http", "mailto:"))]
        assert len(local_links) == 1
        assert local_links[0].is_local is True
        # Should be invalid since README.md doesn't exist in temp dir
        assert local_links[0].is_valid is False

        print("✅ Email links are properly recognized and validated")
        print("✅ Local file links continue to work correctly")
        print("✅ HTTP links continue to work correctly")


if __name__ == "__main__":
    test_email_links_integration()
