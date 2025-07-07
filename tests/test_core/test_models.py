"""Tests for markdown models."""

from pymarktools.core.models import ImageInfo, LinkInfo


class TestLinkInfo:
    def test_create_link_info(self):
        link = LinkInfo(text="Test Link", url="https://example.com", line_number=1)

        assert link.text == "Test Link"
        assert link.url == "https://example.com"
        assert link.line_number == 1
        assert link.is_valid is None
        assert link.status_code is None
        assert link.error is None
        assert link.redirect_url is None
        assert link.is_permanent_redirect is None
        assert link.updated is False

    def test_link_info_with_all_fields(self):
        link = LinkInfo(
            text="Test Link",
            url="https://example.com",
            line_number=1,
            is_valid=True,
            status_code=200,
            error=None,
            redirect_url=None,
            is_permanent_redirect=False,
            updated=False,
        )

        assert link.is_valid is True
        assert link.status_code == 200


class TestImageInfo:
    def test_create_image_info(self):
        image = ImageInfo(alt_text="Test Image", url="https://example.com/image.jpg", line_number=1)

        assert image.alt_text == "Test Image"
        assert image.url == "https://example.com/image.jpg"
        assert image.line_number == 1
        assert image.is_valid is None
        assert image.status_code is None
        assert image.error is None
        assert image.redirect_url is None
        assert image.is_permanent_redirect is None
        assert image.updated is False

    def test_image_info_with_all_fields(self):
        image = ImageInfo(
            alt_text="Test Image",
            url="https://example.com/image.jpg",
            line_number=1,
            is_valid=True,
            status_code=200,
            error=None,
            redirect_url=None,
            is_permanent_redirect=False,
            updated=False,
        )

        assert image.is_valid is True
        assert image.status_code == 200
