"""Command line interface for pymarktools."""

import os

import typer

# Import the command modules
from .commands import check_app, refactor_app
from .state import global_state

# Create the main application
app: typer.Typer = typer.Typer(
    name="pymarktools",
    help="A set of markdown utilities for Python",
    no_args_is_help=True,
)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output"),
    color: bool = typer.Option(True, "--color/--no-color", help="Enable colorized output"),
) -> None:
    """A set of markdown utilities for Python.

    Tools for checking links, images, and refactoring markdown files.
    Supports local file validation, external URL checking, and gitignore integration.
    """
    # Check for color-related environment variables
    env_color = os.getenv("PYMARKTOOLS_COLOR")
    no_color = os.getenv("NO_COLOR")
    force_color = os.getenv("FORCE_COLOR")

    if env_color is not None:
        # Handle various string representations of boolean values
        color = env_color.lower() not in ("false", "0", "no", "off", "")
    elif no_color:
        # Respect the NO_COLOR standard
        color = False
    elif force_color == "0":
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


# Add the subcommands
app.add_typer(check_app, name="check")
app.add_typer(refactor_app, name="refactor")


# Main entry point
if __name__ == "__main__":
    app()
