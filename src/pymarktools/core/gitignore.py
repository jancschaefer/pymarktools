"""Gitignore handling utilities for markdown processing."""

from collections.abc import Callable
from pathlib import Path

from gitignore_parser import parse_gitignore


def find_repo_root(path: Path) -> Path:
    """Find the root directory of the git repository by looking for .git folder."""
    current: Path = path.absolute()
    while current != current.parent:  # Stop at filesystem root
        if (current / ".git").exists():
            return current
        current = current.parent
    # If no .git folder found, return the original path
    return path


def get_gitignore_matcher(base_dir: Path) -> Callable[[str], bool]:
    """Get a gitignore matcher function that uses the spec-compliant gitignore_parser library.

    This function will automatically find and parse all .gitignore files from the repository
    root down to and including all subdirectories within the base directory.

    Args:
        base_dir: The directory to start looking for .gitignore files

    Returns:
        A function that takes a file path (as string) and returns True if the file should be ignored
    """
    repo_root: Path = find_repo_root(base_dir)

    # Collect all .gitignore files from repo root and all subdirectories within base_dir
    gitignore_files: list[Path] = []

    # First, get .gitignore files from repo root up to base_dir (parent .gitignore files)
    current_dir: Path = base_dir.absolute()
    dirs_to_check: list[Path] = []
    while current_dir != repo_root.parent:  # Stop after including repo_root
        dirs_to_check.append(current_dir)
        if current_dir == repo_root:
            break
        current_dir = current_dir.parent

    # Check for .gitignore files in parent directories (from repo root down to base_dir)
    for check_dir in reversed(dirs_to_check):  # Start from repo root
        gitignore_path: Path = check_dir / ".gitignore"
        if gitignore_path.exists():
            gitignore_files.append(gitignore_path)

    # Then, recursively find all .gitignore files within base_dir and its subdirectories
    for gitignore_path in base_dir.rglob(".gitignore"):
        if gitignore_path not in gitignore_files:  # Avoid duplicates
            gitignore_files.append(gitignore_path)

    # If no .gitignore files found, return a function that ignores nothing
    if not gitignore_files:
        return lambda path: False

    # Create matchers for each .gitignore file with their respective base directories
    matchers_with_bases: list[tuple[Callable[[str], bool], Path]] = []
    for gitignore_file in gitignore_files:
        try:
            # Each .gitignore file applies to its own directory and subdirectories
            gitignore_dir: Path = gitignore_file.parent
            # Parse with the correct base_dir for proper pattern matching
            matcher: Callable[[str], bool] = parse_gitignore(str(gitignore_file), base_dir=str(gitignore_dir))
            matchers_with_bases.append((matcher, gitignore_dir))
        except Exception:
            # If we can't parse a gitignore file, just skip it
            continue

    # Return a combined matcher that checks all .gitignore files
    def combined_matcher(file_path: str) -> bool:
        file_path_obj: Path = Path(file_path)

        # Convert to absolute path for proper matching
        if not file_path_obj.is_absolute():
            file_path_obj = (base_dir / file_path_obj).resolve()

        # Check against all matchers in order (most specific first)
        # Reverse the list so we check subdirectory .gitignore files before parent ones
        for matcher, gitignore_dir in reversed(matchers_with_bases):
            # Only check this gitignore if the file is within its scope
            try:
                # Check if the file is within this gitignore's directory or subdirectories
                file_path_obj.relative_to(gitignore_dir)
                # The matcher expects absolute paths
                if matcher(str(file_path_obj)):
                    return True
            except ValueError:
                # File is not within this gitignore's scope, skip it
                continue

        return False

    return combined_matcher


def is_path_ignored(path: Path, gitignore_matcher: Callable[[str], bool]) -> bool:
    """Check if a file path should be ignored using the gitignore matcher."""
    return gitignore_matcher(str(path))
