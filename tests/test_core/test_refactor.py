"""Tests for the refactor module."""

import tempfile
from pathlib import Path

import pytest

from pymarktools.core.refactor import FileReference, FileReferenceManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown_with_refs():
    """Sample markdown content with various references."""
    return """# Test Document

Here's a link to [another doc](./docs/other.md) and an image:

![Test Image](../images/test.jpg)

Also check out [this file](relative/path.md).

External link: [Google](https://google.com)
"""


@pytest.fixture
def sample_referencing_file(temp_dir, sample_markdown_with_refs):
    """Create a markdown file that references other files."""
    md_file = temp_dir / "source.md"
    md_file.write_text(sample_markdown_with_refs)
    return md_file


@pytest.fixture
def sample_target_file(temp_dir):
    """Create a target file to be referenced."""
    target = temp_dir / "docs" / "other.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Target Document\n\nThis is the target.")
    return target


class TestFileReferenceManager:
    def test_init(self, temp_dir):
        manager = FileReferenceManager(temp_dir)
        assert manager.base_dir == temp_dir.resolve()

    def test_find_references_simple(self, temp_dir, sample_referencing_file, sample_target_file):
        manager = FileReferenceManager(temp_dir)

        references = manager.find_references(sample_target_file)

        # Should find the reference to other.md
        assert len(references) == 1
        assert references[0].target_path == "./docs/other.md"
        assert references[0].reference_type == "link"
        assert references[0].line_number == 3

    def test_find_references_no_matches(self, temp_dir, sample_referencing_file):
        manager = FileReferenceManager(temp_dir)

        # Create a file that's not referenced
        unreferenced = temp_dir / "unreferenced.md"
        unreferenced.write_text("# Unreferenced")

        references = manager.find_references(unreferenced)
        assert len(references) == 0

    def test_calculate_new_reference_link(self, temp_dir):
        manager = FileReferenceManager(temp_dir)

        # Create a file reference
        ref_file = temp_dir / "source.md"
        ref = FileReference(
            file_path=ref_file,
            line_number=1,
            reference_text="[Test](./old/path.md)",
            reference_type="link",
            target_path="./old/path.md",
        )

        old_path = temp_dir / "old" / "path.md"
        new_path = temp_dir / "new" / "location.md"

        new_ref = manager.calculate_new_reference(ref, old_path, new_path)
        assert "[Test]" in new_ref
        # Use Path normalization to handle platform-specific path separators
        assert "new" in new_ref and "location.md" in new_ref

    def test_calculate_new_reference_image(self, temp_dir):
        manager = FileReferenceManager(temp_dir)

        # Create an image reference
        ref_file = temp_dir / "source.md"
        ref = FileReference(
            file_path=ref_file,
            line_number=1,
            reference_text="![Alt text](./old/image.jpg)",
            reference_type="image",
            target_path="./old/image.jpg",
        )

        old_path = temp_dir / "old" / "image.jpg"
        new_path = temp_dir / "new" / "image.jpg"

        new_ref = manager.calculate_new_reference(ref, old_path, new_path)
        assert "![Alt text]" in new_ref
        # Use Path normalization to handle platform-specific path separators
        assert "new" in new_ref and "image.jpg" in new_ref

    def test_is_reference_to_target_relative_path(self, temp_dir):
        manager = FileReferenceManager(temp_dir)

        source_file = temp_dir / "source.md"
        target_file = temp_dir / "docs" / "target.md"
        target_file.parent.mkdir(exist_ok=True)
        target_file.touch()

        # Test relative path
        assert manager._is_reference_to_target("./docs/target.md", target_file, source_file)
        assert manager._is_reference_to_target("docs/target.md", target_file, source_file)

        # Test non-matching path
        assert not manager._is_reference_to_target("./other/file.md", target_file, source_file)

    def test_is_reference_to_target_external_url(self, temp_dir):
        manager = FileReferenceManager(temp_dir)

        source_file = temp_dir / "source.md"
        target_file = temp_dir / "target.md"
        target_file.touch()

        # External URLs should not match
        assert not manager._is_reference_to_target("https://example.com", target_file, source_file)
        assert not manager._is_reference_to_target("http://test.com/file.md", target_file, source_file)

    def test_get_search_files_include_pattern(self, temp_dir):
        manager = FileReferenceManager(temp_dir)

        # Create various files
        (temp_dir / "test1.md").touch()
        (temp_dir / "test2.md").touch()
        (temp_dir / "test.txt").touch()
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "test3.md").touch()

        files = manager._get_search_files("*.md", None)
        md_files = [f for f in files if f.suffix == ".md"]

        assert len(md_files) == 3
        assert all(f.suffix == ".md" for f in md_files)

    def test_update_file_content(self, temp_dir):
        manager = FileReferenceManager(temp_dir)

        content = """# Test
        
[Link](./old.md)

![Image](./old.jpg)
"""

        ref_file = temp_dir / "test.md"
        references = [
            FileReference(
                file_path=ref_file,
                line_number=3,
                reference_text="[Link](./old.md)",
                reference_type="link",
                target_path="./old.md",
            ),
            FileReference(
                file_path=ref_file,
                line_number=5,
                reference_text="![Image](./old.jpg)",
                reference_type="image",
                target_path="./old.jpg",
            ),
        ]

        old_path = temp_dir / "old.md"
        new_path = temp_dir / "new.md"

        updated_content = manager._update_file_content(content, references, old_path, new_path)

        assert "[Link](new.md)" in updated_content
        assert "![Image](./old.jpg)" in updated_content  # Only the .md file should be updated
