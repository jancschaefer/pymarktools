"""Command line interface for pymarktools."""

import os

import typer

from . import __version__

# Import the command modules
from .commands import check, refactor_app
from .global_state import global_state

# Create the main application
app: typer.Typer = typer.Typer(
    name="pymarktools",
    help="A set of markdown utilities for Python",
    no_args_is_help=True,
    add_completion=True,
    pretty_exceptions_enable=True,
)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output"),
    color: bool = typer.Option(True, "--color/--no-color", help="Enable colorized output"),
    version: bool = typer.Option(
        None,
        "--version",
        callback=lambda value: (typer.echo(__version__) or raise_(typer.Exit())) if value else None,
        is_eager=True,
        help="Show the version and exit.",
        show_default=False,
    ),
) -> None:
    """A set of markdown utilities for Python.
    Tools for checking links, images, and refactoring markdown files.
    Supports local file validation, external URL checking, and gitignore integration.
    """
    # Check for color-related environment variables
    env_color = os.getenv("PYMARKTOOLS_COLOR")
    no_color = os.getenv("NO_COLOR")
    force_color = os.getenv("FORCE_COLOR")

    if env_color is not None:  # pragma: no cover
        # Handle various string representations of boolean values
        color = env_color.lower() not in ("false", "0", "no", "off", "")
    elif no_color:  # pragma: no cover
        # Respect the NO_COLOR standard
        color = False
    elif force_color == "0":  # pragma: no cover
        # Respect FORCE_COLOR=0
        color = False

    # Update global state
    global_state.update(
        {
            "verbose": verbose,
            "quiet": quiet,
            "color": color,
        }
    )

    # Configure output level
    if verbose and not quiet:
        typer.echo("Verbose mode enabled")
    elif quiet:
        typer.echo("Quiet mode enabled", err=True)


# Helper to raise exceptions in lambda
def raise_(ex):
    """Raise the given exception. Used for control flow in Typer option callbacks."""
    raise ex


# Register commands
app.command("check")(check)
app.add_typer(refactor_app, name="refactor")


# Main entry point
if __name__ == "__main__":
    app()  # pragma: no cover
