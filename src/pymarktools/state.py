"""Global state for pymarktools CLI."""

from pathlib import Path
from typing import Optional, TypedDict


# Global state for options that apply to all commands
class GlobalState(TypedDict):
    """Global state for pymarktools CLI options."""

    verbose: bool
    quiet: bool
    color: bool


global_state: GlobalState = GlobalState(
    verbose=False,
    quiet=False,
    color=True,  # Default to enabled
)


# Default options for the ``check`` command
class CheckOptions(TypedDict):
    """Default configuration for the :mod:`pymarktools.commands.check` module."""

    timeout: int
    output: Optional[Path]
    check_external: bool
    check_local: bool
    fix_redirects: bool
    follow_gitignore: bool
    include_pattern: str
    exclude_pattern: Optional[str]
    parallel: bool
    workers: Optional[int]
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
