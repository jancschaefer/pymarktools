"""Public Python API compatibility contracts."""

from pathlib import Path

import pytest

from pymarktools.core.image_checker import DeadImageChecker
from pymarktools.core.link_checker import DeadLinkChecker
from pymarktools.core.models import ImageInfo, LinkInfo

pytestmark = pytest.mark.contract


def test_native_extension_exposes_the_core_version() -> None:
    """The Python package exposes its compiled native core."""
    import pymarktools._native as native

    assert native.core_version().count(".") == 2


def test_link_and_image_result_shapes_stay_stable() -> None:
    """Extraction exposes the current result types and primary fields."""
    link = DeadLinkChecker(check_external=False).extract_links("[docs](guide.md)")[0]
    image = DeadImageChecker(check_external=False).extract_images("![logo](logo.svg)")[0]

    assert isinstance(link, LinkInfo)
    assert isinstance(image, ImageInfo)
    assert (link.text, link.url, link.line_number) == ("docs", "guide.md", 1)
    assert (image.alt_text, image.url, image.line_number) == ("logo", "logo.svg", 1)


def test_local_path_error_stays_stable(tmp_path: Path) -> None:
    """Missing local references retain their result fields and diagnostic."""
    document = tmp_path / "README.md"
    document.write_text("[missing](missing.md)", encoding="utf-8")

    result = DeadLinkChecker(check_external=False).check_file(document)[0]

    assert result.is_local is True
    assert result.is_valid is False
    assert result.local_path == str(tmp_path / "missing.md")
    assert result.error == f"File not found: {tmp_path / 'missing.md'}"
