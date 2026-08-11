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


def test_native_parser_returns_mutable_result_objects() -> None:
    """Native parsing preserves the result-object interface used by checkers."""
    import pymarktools._native as native

    result = native.extract_links("[docs](guide.md)")[0]
    result.is_valid = True

    assert (result.text, result.url, result.line_number, result.is_valid) == ("docs", "guide.md", 1, True)


def test_python_checkers_expose_native_result_objects() -> None:
    """The existing checker API returns results backed by the Rust extension."""
    import pymarktools._native as native

    result = DeadLinkChecker(check_external=False).extract_links("[docs](guide.md)")[0]

    assert isinstance(result, native.LinkInfo)


def test_native_path_resolution_strips_fragments_and_queries() -> None:
    """Native local path resolution keeps the established URL-cleaning rules."""
    import pymarktools._native as native

    assert native.resolve_local_path("../guide.md#install?unused", "fixtures/docs/README.md") == "fixtures/guide.md"


def test_native_discovery_honors_gitignore(tmp_path: Path) -> None:
    """The Rust extension discovers only non-ignored Markdown files."""
    import pymarktools._native as native

    (tmp_path / ".gitignore").write_text("generated/\n", encoding="utf-8")
    (tmp_path / "generated").mkdir()
    (tmp_path / "generated" / "skip.md").write_text("# skip", encoding="utf-8")
    (tmp_path / "keep.md").write_text("# keep", encoding="utf-8")

    assert native.discover_files(str(tmp_path)) == [str(tmp_path / "keep.md")]


def test_native_http_returns_the_existing_result_shape() -> None:
    """Native HTTP failures retain the dictionary fields consumed by checkers."""
    import pymarktools._native as native

    result = native.check_url("not a url", 1)

    assert result == {
        "is_valid": False,
        "status_code": None,
        "error": result["error"],
        "redirect_url": None,
        "is_permanent_redirect": False,
    }
    assert isinstance(result["error"], str)


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
