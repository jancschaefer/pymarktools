"""Global state for pymarktools CLI."""

from typing import TypedDict


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
