"""Default options for the ``check`` command."""

from pathlib import Path
from typing import TypedDict


class CheckOptions(TypedDict):
    """Default configuration for the :mod:`pymarktools.commands.check` module."""

    timeout: int
    output: Path | None
    check_external: bool
    check_local: bool
    fix_redirects: bool
    follow_gitignore: bool
    include_pattern: str
    exclude_pattern: str | None
    parallel: bool
    workers: int | None
    fail: bool
    check_dead_links: bool
    check_dead_images: bool


check_options: CheckOptions = CheckOptions(
    timeout=30,
    output=None,
    check_external=True,
    check_local=True,
    fix_redirects=False,
    follow_gitignore=True,
    include_pattern="*.md",
    exclude_pattern=None,
    parallel=True,
    workers=None,
    fail=True,
    check_dead_links=True,
    check_dead_images=True,
)
