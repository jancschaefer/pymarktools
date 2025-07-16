"""Refactor commands for pymarktools CLI."""

from pathlib import Path

import typer

from ..core.refactor import FileReference, FileReferenceManager
from ..global_state import global_state

# Create a subcommand group for refactor operations
refactor_app: typer.Typer = typer.Typer(
    name="refactor",
    help="Refactor and reorganize markdown content",
    no_args_is_help=True,
)


@refactor_app.command("move")
def move_file(
    source: Path = typer.Argument(..., help="Source file path (markdown or image file)"),
    destination: Path = typer.Argument(..., help="Destination file path"),
    base_dir: Path | None = typer.Option(
        None,
        "--base-dir",
        "-b",
        help="Base directory to search for references (defaults to current directory)",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be done without making changes"),
    include_pattern: str | None = typer.Option(
        "*.md",
        "--include",
        "-i",
        help="File pattern to include when searching for references",
    ),
    exclude_pattern: str | None = typer.Option(
        None,
        "--exclude",
        "-e",
        help="File pattern to exclude when searching for references",
    ),
) -> None:
    """Move a file and update all references to it in markdown files.

    This command will:
    1. Find all references to the source file in markdown files
    2. Move the source file to the destination
    3. Update all references to point to the new location

    Supports both markdown files (.md) and image files commonly referenced in markdown.
    """
    echo_info(f"Moving {source} to {destination}")

    if base_dir is None:
        base_dir = Path.cwd()

    if dry_run:
        echo_warning("DRY RUN MODE - No changes will be made")

    echo_info(f"Searching for references in: {base_dir}")
    echo_info(f"Include pattern: {include_pattern}")
    if exclude_pattern:
        echo_info(f"Exclude pattern: {exclude_pattern}")

    manager: FileReferenceManager = FileReferenceManager(base_dir=base_dir)

    try:
        # Validate source file exists
        if not source.exists():
            echo_error(f"Error: Source file {source} does not exist")
            raise typer.Exit(1)

        # Check if destination already exists
        if destination.exists() and not dry_run:
            if not typer.confirm(f"Destination {destination} already exists. Overwrite?"):
                echo_warning("Operation cancelled")
                raise typer.Exit(0)

        # Find all references to the source file
        echo_info("Searching for references...")
        references: list[FileReference] = manager.find_references(
            target_file=source,
            include_pattern=include_pattern or "*.md",
            exclude_pattern=exclude_pattern,
        )

        if not references:
            echo_warning("No references found in markdown files")
        else:
            echo_success(f"Found {len(references)} references:")
            for ref in references:
                typer.echo(f"  {ref.file_path}:{ref.line_number} - {ref.reference_text}")

        if dry_run:
            echo_info(f"\nWould move: {source} -> {destination}")
            if references:
                echo_info("Would update the following references:")
                for ref in references:
                    new_ref: str = manager.calculate_new_reference(ref, source, destination)
                    typer.echo(f"  {ref.file_path}:{ref.line_number}: {ref.reference_text} -> {new_ref}")
        else:
            # Perform the actual move and update
            echo_info("Performing move operation...")
            manager.move_file_and_update_references(source=source, destination=destination, references=references)
            echo_success("✅ Move operation completed successfully")

    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)


def echo_success(message: str, err: bool = False):
    """Echo a success message with green color if color is enabled."""
    if global_state.get("color", True):
        typer.secho(message, fg=typer.colors.GREEN, err=err)
    else:
        typer.echo(message, err=err)


def echo_error(message: str, err: bool = True):
    """Echo an error message with red color if color is enabled."""
    if global_state.get("color", True):
        typer.secho(message, fg=typer.colors.RED, err=err)
    else:
        typer.echo(message, err=err)


def echo_warning(message: str, err: bool = False):
    """Echo a warning message with yellow color if color is enabled."""
    if global_state.get("color", True):
        typer.secho(message, fg=typer.colors.YELLOW, err=err)
    else:
        typer.echo(message, err=err)


def echo_info(message: str, err: bool = False):
    """Echo an info message with blue color if color is enabled."""
    if global_state.get("color", True):
        typer.secho(message, fg=typer.colors.BLUE, err=err)
    else:
        typer.echo(message, err=err)
