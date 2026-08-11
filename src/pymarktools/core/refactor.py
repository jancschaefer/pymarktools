"""Python compatibility facade for native Markdown refactoring."""

from dataclasses import dataclass
from pathlib import Path

from pymarktools import _native


@dataclass
class FileReference:
    """Information about a file reference found in Markdown."""

    file_path: Path
    line_number: int
    reference_text: str
    reference_type: str
    target_path: str


class FileReferenceManager:
    """Manage Markdown references through the Rust core."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()

    def find_references(
        self,
        target_file: Path,
        include_pattern: str = "*.md",
        exclude_pattern: str | None = None,
    ) -> list[FileReference]:
        """Find all references to ``target_file`` within Markdown files."""
        return [
            FileReference(
                file_path=Path(reference["file_path"]),
                line_number=int(reference["line_number"]),
                reference_text=str(reference["reference_text"]),
                reference_type=str(reference["reference_type"]),
                target_path=str(reference["target_path"]),
            )
            for reference in _native.find_references(
                str(target_file),
                str(self.base_dir),
                include_pattern,
                exclude_pattern,
            )
        ]

    def _get_search_files(self, include_pattern: str, exclude_pattern: str | None) -> list[Path]:
        """Return Markdown files selected by the native discoverer."""
        return [
            Path(path)
            for path in _native.discover_files(
                str(self.base_dir),
                include_pattern,
                exclude_pattern,
                False,
            )
        ]

    def _is_reference_to_target(self, ref_path: str, target_file: Path, source_file: Path) -> bool:
        """Return whether a Markdown target resolves to ``target_file``."""
        if ref_path.startswith(("http://", "https://")):
            return False
        try:
            resolved = (
                self.base_dir / ref_path.lstrip("/")
                if ref_path.startswith("/")
                else Path(_native.resolve_local_path(ref_path, str(source_file)))
            )
            return resolved.resolve() == target_file.resolve()
        except OSError:
            return False

    def _calculate_relative_path(self, from_dir: Path, to_file: Path) -> str:
        """Calculate a portable Markdown path through the native core."""
        return _native.relative_reference(str(from_dir), str(to_file))

    def calculate_new_reference(self, reference: FileReference, old_path: Path, new_path: Path) -> str:
        """Calculate the replacement Markdown reference after a move."""
        new_relative_path = self._calculate_relative_path(reference.file_path.parent, new_path)
        if reference.reference_type in {"link", "image"}:
            return _native.rewrite_reference(reference.reference_text, reference.target_path, new_relative_path)
        return new_relative_path

    def move_file_and_update_references(
        self,
        source: Path,
        destination: Path,
        references: list[FileReference],
        include_pattern: str = "*.md",
        exclude_pattern: str | None = None,
    ) -> None:
        """Move ``source`` and rewrite Markdown references through Rust."""
        del references
        _native.move_and_rewrite(
            str(source),
            str(destination),
            str(self.base_dir),
            include_pattern,
            exclude_pattern,
        )

    def _update_file_content(
        self,
        content: str,
        references: list[FileReference],
        old_path: Path,
        new_path: Path,
    ) -> str:
        """Compatibility helper for replacing known references in text."""
        lines = content.split("\n")
        for reference in sorted(references, key=lambda value: value.line_number, reverse=True):
            if Path(reference.target_path).name != old_path.name:
                continue
            line_index = reference.line_number - 1
            if 0 <= line_index < len(lines):
                replacement = self.calculate_new_reference(reference, old_path, new_path)
                lines[line_index] = lines[line_index].replace(reference.reference_text, replacement)
        return "\n".join(lines)
