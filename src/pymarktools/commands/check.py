"""Check commands for pymarktools CLI."""

import asyncio
import os
from pathlib import Path
from typing import Any, Optional, Union

import typer

from ..check_options import check_options
from ..core.image_checker import DeadImageChecker
from ..core.link_checker import DeadLinkChecker
from ..global_state import global_state


def echo_if_not_quiet(message: str, err: bool = False, color: Optional[str] = None) -> None:
    """Echo message only if not in quiet mode."""
    if not global_state.get("quiet", False):
        if global_state.get("color", True) and color:
            typer.secho(message, fg=color, err=err)
        else:
            typer.echo(message, err=err)


def echo_if_verbose(message: str, err: bool = False, color: Optional[str] = None) -> None:
    """Echo message only if in verbose mode."""
    if global_state.get("verbose", False):
        if global_state.get("color", True) and color:
            typer.secho(message, fg=color, err=err)
        else:
            typer.echo(message, err=err)


def echo_success(message: str, err: bool = False) -> None:
    """Echo a success message with green color if color is enabled."""
    if global_state.get("color", True):
        typer.secho(message, fg=typer.colors.GREEN, err=err)
    else:
        typer.echo(message, err=err)


def echo_error(message: str, err: bool = True) -> None:
    """Echo an error message with red color if color is enabled."""
    if global_state.get("color", True):
        typer.secho(message, fg=typer.colors.RED, err=err)
    else:
        typer.echo(message, err=err)


def echo_warning(message: str, err: bool = False) -> None:
    """Echo a warning message with yellow color if color is enabled."""
    if global_state.get("color", True):
        typer.secho(message, fg=typer.colors.YELLOW, err=err)
    else:
        typer.echo(message, err=err)


def echo_info(message: str, err: bool = False) -> None:
    """Echo an info message with blue color if color is enabled."""
    if global_state.get("color", True):
        typer.secho(message, fg=typer.colors.BLUE, err=err)
    else:
        typer.echo(message, err=err)


def check(
    path: Optional[Path] = typer.Argument(
        None, help="Path to markdown file or directory (defaults to current directory)"
    ),
    timeout: int = typer.Option(30, "--timeout", "-t", help="Request timeout in seconds"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file for the report"),
    check_external: bool = typer.Option(
        True,
        "--check-external/--no-check-external",
        help="Whether to check external links/images with HTTP requests",
    ),
    check_local: bool = typer.Option(
        True,
        "--check-local/--no-check-local",
        help="Whether to check if local file links/images exist",
    ),
    fix_redirects: bool = typer.Option(
        False,
        "--fix-redirects",
        help="Update links/images with permanent redirects in the source files",
    ),
    follow_gitignore: bool = typer.Option(
        True,
        "--follow-gitignore/--no-follow-gitignore",
        help="Respect .gitignore patterns when scanning directories",
    ),
    include_pattern: str = typer.Option(
        "*.md",
        "--include",
        "-i",
        help="File pattern to include when searching for references",
    ),
    exclude_pattern: Optional[str] = typer.Option(
        None,
        "--exclude",
        "-e",
        help="File pattern to exclude when searching for references",
    ),
    parallel: bool = typer.Option(
        True,
        "--parallel/--no-parallel",
        help="Enable parallel processing for external URL checks",
    ),
    fail: bool = typer.Option(
        True,
        "--fail/--no-fail",
        help="Exit with status 1 if invalid links/images are found",
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers",
        "-w",
        help="Number of worker threads for parallel processing (defaults to CPU count)",
    ),
    check_dead_links: bool = typer.Option(True, "--check-dead-links/--no-check-dead-links", help="Validate links"),
    check_dead_images: bool = typer.Option(True, "--check-dead-images/--no-check-dead-images", help="Validate images"),
) -> None:
    """Check markdown files for dead links and images."""
    if path is None:
        path = Path.cwd()

    local_state: dict[str, Any] = check_options.copy()
    local_state.update(
        {
            "timeout": timeout,
            "output": output,
            "check_external": check_external,
            "check_local": check_local,
            "fix_redirects": fix_redirects,
            "follow_gitignore": follow_gitignore,
            "include_pattern": include_pattern,
            "exclude_pattern": exclude_pattern,
            "parallel": parallel,
            "fail": fail,
            "workers": workers,
            "check_dead_links": check_dead_links,
            "check_dead_images": check_dead_images,
        }
    )

    if not local_state["check_dead_links"] and not local_state["check_dead_images"]:
        echo_error("Both checks disabled; nothing to do")
        raise typer.Exit(1)

    check_options.update(local_state)

    overall_valid = True

    if local_state["check_dead_links"]:
        echo_info("Checking for dead links...")
        print_common_info(path)

        link_checker = DeadLinkChecker(
            timeout=check_options["timeout"],
            check_external=check_options["check_external"],
            check_local=check_options["check_local"],
            fix_redirects=check_options["fix_redirects"],
            follow_gitignore=check_options["follow_gitignore"],
            parallel=check_options["parallel"],
            workers=check_options["workers"],
        )

        try:
            all_valid = asyncio.run(process_path_and_check_async(link_checker, "links", path))
        except RuntimeError:
            all_valid = process_path_and_check(link_checker, "links", path)

        overall_valid = overall_valid and all_valid
        if all_valid:
            echo_success("All links are valid")
        else:
            echo_error("Some links are invalid or broken")

    if local_state["check_dead_images"]:
        echo_info("Checking for dead images...")
        print_common_info(path)

        image_checker = DeadImageChecker(
            timeout=check_options["timeout"],
            check_external=check_options["check_external"],
            check_local=check_options["check_local"],
            fix_redirects=check_options["fix_redirects"],
            follow_gitignore=check_options["follow_gitignore"],
            parallel=check_options["parallel"],
            workers=check_options["workers"],
        )

        try:
            all_valid = asyncio.run(process_path_and_check_async(image_checker, "images", path))
        except RuntimeError:
            all_valid = process_path_and_check(image_checker, "images", path)

        overall_valid = overall_valid and all_valid
        if all_valid:
            echo_success("All images are valid")
        else:
            echo_error("Some images are invalid or broken")

    if not overall_valid and check_options["fail"]:
        raise typer.Exit(1)


def print_common_info(path: Path) -> None:
    """Print common information about the check operation."""
    echo_if_verbose(f"Checking in: {path}")
    echo_if_verbose(f"Using timeout: {check_options['timeout']}s")
    echo_if_verbose(f"Checking external: {check_options['check_external']}")
    echo_if_verbose(f"Checking local files: {check_options['check_local']}")
    echo_if_verbose(f"Fixing redirects: {check_options['fix_redirects']}")
    echo_if_verbose(f"Following gitignore: {check_options['follow_gitignore']}")
    echo_if_verbose(f"Include pattern: {check_options['include_pattern']}")
    if check_options["exclude_pattern"]:
        echo_if_verbose(f"Exclude pattern: {check_options['exclude_pattern']}")
    echo_if_verbose(f"Parallel processing: {check_options['parallel']}")
    if check_options["workers"]:
        echo_if_verbose(f"Worker threads: {check_options['workers']}")
    else:
        echo_if_verbose(f"Worker threads: {os.cpu_count()} (auto-detected)")
    if check_options["output"]:
        echo_if_verbose(f"Report will be saved to: {check_options['output']}")
    echo_if_verbose(f"Fail on invalid items: {check_options['fail']}")


def process_path_and_check(checker: Union[DeadLinkChecker, DeadImageChecker], item_type: str, path: Path) -> bool:
    """Process the path and run the checker, displaying results.

    Returns:
        True if all items are valid, False if any invalid items are found.
    """
    # For directory processing with many files, use async for better performance and progress reporting
    if path.is_dir() and check_options.get("parallel", True):
        try:
            return asyncio.run(process_path_and_check_async(checker, item_type, path))
        except RuntimeError:
            # Already in an event loop, fall back to sync processing
            pass

    # Fallback to synchronous processing
    has_invalid_items: bool = False

    try:
        if path.is_file():
            items = checker.check_file(path)
            echo_if_not_quiet(f"Found {len(items)} {item_type}")
            for item in items:
                display_item_result(item, item_type)
                if not item.is_valid:
                    has_invalid_items = True
        elif path.is_dir():
            results = checker.check_directory(
                path,
                include_pattern=check_options["include_pattern"],
                exclude_pattern=check_options["exclude_pattern"],
            )
            total_items: int = sum(len(items) for items in results.values())
            echo_if_not_quiet(f"Found {total_items} {item_type} across {len(results)} files")
            for file_path, items in results.items():
                if items or global_state.get("verbose", False):  # Show empty files only in verbose mode
                    echo_if_not_quiet(f"\n{file_path}: Found {len(items)} {item_type}")
                for item in items:
                    display_item_result(item, item_type)
                    if not item.is_valid:
                        has_invalid_items = True
        else:
            echo_error(f"Error: {path} is not a valid file or directory")
            raise typer.Exit(1)
    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)

    return not has_invalid_items


async def process_path_and_check_async(
    checker: Union[DeadLinkChecker, DeadImageChecker], item_type: str, path: Path
) -> bool:
    """Process the path and run the checker asynchronously with progress reporting.

    Returns:
        True if all items are valid, False if any invalid items are found.
    """
    has_invalid_items: bool = False

    try:
        if path.is_file():
            items = await checker.check_file_async(path)
            echo_if_not_quiet(f"Found {len(items)} {item_type}")
            for item in items:
                display_item_result(item, item_type)
                if not item.is_valid:
                    has_invalid_items = True
        elif path.is_dir():
            # Progress callback for real-time updates
            completed_files = [0]  # Use list to allow modification in nested function
            has_invalid_items_ref = [False]  # Use list to allow modification in nested function

            def progress_callback(file_path: Path, items: Any) -> None:
                completed_files[0] += 1
                if items:
                    echo_if_verbose(f"[{completed_files[0]:3d}] {file_path}: Found {len(items)} {item_type}")
                else:
                    echo_if_verbose(f"[{completed_files[0]:3d}] {file_path}: No {item_type} found")
                # Display results for this file immediately
                for item in items:
                    display_item_result(item, item_type)
                    if not item.is_valid:
                        has_invalid_items_ref[0] = True

            # Run async directory check with progress reporting
            results = await checker.check_directory_async(
                path,
                include_pattern=check_options["include_pattern"],
                exclude_pattern=check_options["exclude_pattern"],
                progress_callback=progress_callback if global_state.get("verbose", False) else None,
            )

            total_items: int = sum(len(items) for items in results.values())
            echo_if_not_quiet(f"Found {total_items} {item_type} across {len(results)} files")

            # Update has_invalid_items from the callback
            has_invalid_items = has_invalid_items or has_invalid_items_ref[0]

            # If not in verbose mode, display results at the end
            if not global_state.get("verbose", False):
                for file_path, items in results.items():
                    if items or global_state.get("verbose", False):
                        echo_if_not_quiet(f"\n{file_path}: Found {len(items)} {item_type}")
                    for item in items:
                        display_item_result(item, item_type)
                        if not item.is_valid:
                            has_invalid_items = True
        else:
            echo_error(f"Error: {path} is not a valid file or directory")
            raise typer.Exit(1)
    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)

    return not has_invalid_items


def display_item_result(item: Any, item_type: str) -> None:
    """Display the result for a single link or image item."""
    # Build status string with color coding
    if item.is_valid:
        status = "VALID"
        status_color = typer.colors.GREEN
    else:
        status = "INVALID"
        status_color = typer.colors.RED

    # Add status code if available
    if item.status_code:
        status += f" {item.status_code}"

    # Add update indicator
    if item.updated:
        status += " [UPDATED]"

    # Add local indicator
    if item.is_local:
        status += " [LOCAL]"

    # Display differently based on item type
    if item_type == "links":
        line_info = f"  Line {item.line_number}: {item.text} -> {item.url}"
    else:  # images
        line_info = f"  Line {item.line_number}: {item.alt_text} -> {item.url}"

    # Use colored output for status
    if global_state.get("color", True):
        # Print line info and status separately for proper coloring
        if not global_state.get("quiet", False):
            typer.echo(f"{line_info} ", nl=False)
            typer.secho(f"[{status}]", fg=status_color)
    else:
        echo_if_not_quiet(f"{line_info} [{status}]")

    # Display error messages in red
    if item.error:
        echo_error(f"    Error: {item.error}")

    # Display redirect info in yellow
    if item.redirect_url and not item.updated:
        echo_warning(f"    Redirects to: {item.redirect_url}")

    # Display resolved path in blue (verbose mode only)
    if item.local_path and global_state.get("verbose", False):
        echo_info(f"    Resolved path: {item.local_path}")
