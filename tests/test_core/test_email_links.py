"""Tests for email link validation."""

import tempfile
from pathlib import Path

from pymarktools.core.link_checker import DeadLinkChecker


class TestEmailLinks:
    """Test email link validation."""

    def test_extract_email_links(self):
        """Test extracting email links from markdown content."""
        checker = DeadLinkChecker()
        content = """# Test Document

Contact us: [email support](mailto:support@example.com)
Send feedback to [feedback](mailto:feedback@test.org)
Regular link: [website](https://example.com)
"""

        links = checker.extract_links(content)

        assert len(links) == 3

        # Check email links
        email_links = [link for link in links if link.url.startswith("mailto:")]
        assert len(email_links) == 2

        assert email_links[0].text == "email support"
        assert email_links[0].url == "mailto:support@example.com"
        assert email_links[0].line_number == 3

        assert email_links[1].text == "feedback"
        assert email_links[1].url == "mailto:feedback@test.org"
        assert email_links[1].line_number == 4

    def test_is_external_url_with_email(self):
        """Test that email URLs are recognized as external."""
        checker = DeadLinkChecker()

        # Email URLs should be external
        assert checker.is_external_url("mailto:user@example.com") is True
        assert checker.is_external_url("mailto:support@domain.org") is True

        # HTTP/HTTPS should still work
        assert checker.is_external_url("https://example.com") is True
        assert checker.is_external_url("http://example.com") is True

        # Local files should not be external
        assert checker.is_external_url("./local/file.md") is False
        assert checker.is_external_url("../other/file.md") is False
        assert checker.is_external_url("file.md") is False

    def test_is_external_url_with_other_schemes(self):
        """Test that other common URL schemes are recognized as external."""
        checker = DeadLinkChecker()

        # Common schemes that should be external
        assert checker.is_external_url("ftp://files.example.com") is True
        assert checker.is_external_url("ftps://secure.example.com") is True
        assert checker.is_external_url("ssh://server.example.com") is True
        assert checker.is_external_url("tel:+1234567890") is True
        assert checker.is_external_url("sms:+1234567890") is True

    def test_email_domain_validation(self):
        """Test that email URLs validate domain existence instead of full email."""
        checker = DeadLinkChecker(check_external=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "test.md"

            # Use a known domain for testing
            md_file.write_text("""
[Contact](mailto:test@example.com)
""")

            links = checker.check_file(md_file)

            assert len(links) == 1
            email_link = links[0]

            # Should be recognized as external and non-local
            assert email_link.is_local is False

            # For now, let's just check that it doesn't try to validate as local file
            # The actual domain validation will be implemented in the fix
            assert email_link.url == "mailto:test@example.com"

    def test_extract_email_domain(self):
        """Test email domain extraction."""
        checker = DeadLinkChecker()

        # Test basic email
        assert checker.extract_email_domain("mailto:user@example.com") == "example.com"

        # Test email with query parameters
        assert checker.extract_email_domain("mailto:user@test.org?subject=Hello") == "test.org"

        # Test email with fragment
        assert checker.extract_email_domain("mailto:user@domain.net#section") == "domain.net"

        # Test complex domain
        assert checker.extract_email_domain("mailto:contact@subdomain.example.org") == "subdomain.example.org"

    def test_extract_email_domain_invalid(self):
        """Test email domain extraction with invalid inputs."""
        checker = DeadLinkChecker()

        # Test non-email URL
        try:
            checker.extract_email_domain("https://example.com")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Not an email URL" in str(e)

        # Test malformed email
        try:
            checker.extract_email_domain("mailto:invalidformat")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Invalid email format" in str(e)

    def test_email_links_not_treated_as_local_files(self):
        """Test that email links are not treated as local file paths."""
        checker = DeadLinkChecker(check_external=False, check_local=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            md_file = temp_path / "test.md"

            md_file.write_text("""
[Contact](mailto:contact@example.com)
[Local file](./README.md)
""")

            links = checker.check_file(md_file)

            assert len(links) == 2

            # Email link should not be checked as local file
            email_link = [link for link in links if link.url.startswith("mailto:")][0]
            assert email_link.is_local is False
            # Should be valid since external checking is disabled
            assert email_link.is_valid is True

            # Local file link should be checked as local
            local_link = [link for link in links if not link.url.startswith("mailto:")][0]
            assert local_link.is_local is True
            # Should be invalid since README.md doesn't exist in temp dir
            assert local_link.is_valid is False
