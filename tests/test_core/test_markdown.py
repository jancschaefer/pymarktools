import tempfile
from pathlib import Path

import pytest

from pymarktools.core.markdown import (
    DeadImageChecker,
    DeadLinkChecker,
    ImageInfo,
    LinkInfo,
)


@pytest.fixture
def sample_markdown_content():
    return """# Test Document

This is a [test link](https://example.com) and here's an image:

![Alt text](https://example.com/image.jpg)

Another [broken link](https://nonexistent-domain-12345.com).

![Another image](https://example.com/another.png)
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

    def test_check_file(self, temp_markdown_file):
        checker = DeadLinkChecker()

        links = checker.check_file(temp_markdown_file)

        assert len(links) == 2
        assert all(isinstance(link, LinkInfo) for link in links)
        assert links[0].text == "test link"
        assert links[0].url == "https://example.com"

    def test_check_file_not_found(self):
        checker = DeadLinkChecker()

        with pytest.raises(FileNotFoundError):
            checker.check_file(Path("nonexistent.md"))


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

    def test_check_file(self, temp_markdown_file):
        checker = DeadImageChecker()

        images = checker.check_file(temp_markdown_file)

        assert len(images) == 2
        assert all(isinstance(image, ImageInfo) for image in images)
        assert images[0].alt_text == "Alt text"
        assert images[0].url == "https://example.com/image.jpg"

    def test_check_file_not_found(self):
        checker = DeadImageChecker()

        with pytest.raises(FileNotFoundError):
            checker.check_file(Path("nonexistent.md"))
