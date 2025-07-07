"""Command line interface for pymarktools."""

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
