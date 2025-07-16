"""Check commands for pymarktools CLI."""

import asyncio
import os
from pathlib import Path
from typing import Any, Optional, Union

import typer

from ..core.image_checker import DeadImageChecker
from ..core.link_checker import DeadLinkChecker
from ..state import global_state

# Global state for common options
check_state: dict[str, Any] = {
    "timeout": 30,
    "output": None,
    "check_external": True,
    "check_local": True,
    "fix_redirects": False,
    "follow_gitignore": True,
    "include_pattern": "*.md",
    "exclude_pattern": None,
    "parallel": True,
    "workers": None,  # Will default to cpu_count() in checkers
    "fail": True,
    "check_dead_links": True,
    "check_dead_images": True,
}


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


def print_common_info(path: Path) -> None:
    """Print common information about the check operation."""
    echo_if_verbose(f"Checking in: {path}")
    echo_if_verbose(f"Using timeout: {check_state['timeout']}s")
    echo_if_verbose(f"Checking external: {check_state['check_external']}")
    echo_if_verbose(f"Checking local files: {check_state['check_local']}")
    echo_if_verbose(f"Fixing redirects: {check_state['fix_redirects']}")
    echo_if_verbose(f"Following gitignore: {check_state['follow_gitignore']}")
    echo_if_verbose(f"Include pattern: {check_state['include_pattern']}")
    if check_state["exclude_pattern"]:
        echo_if_verbose(f"Exclude pattern: {check_state['exclude_pattern']}")
    echo_if_verbose(f"Parallel processing: {check_state['parallel']}")
    if check_state["workers"]:
        echo_if_verbose(f"Worker threads: {check_state['workers']}")
    else:
        echo_if_verbose(f"Worker threads: {os.cpu_count()} (auto-detected)")
    if check_state["output"]:
        echo_if_verbose(f"Report will be saved to: {check_state['output']}")
    echo_if_verbose(f"Fail on invalid items: {check_state['fail']}")
    echo_if_verbose(f"Check dead links: {check_state['check_dead_links']}")
    echo_if_verbose(f"Check dead images: {check_state['check_dead_images']}")


def process_path_and_check(checker: Union[DeadLinkChecker, DeadImageChecker], item_type: str, path: Path) -> bool:
    """Process the path and run the checker, displaying results.

    Returns:
        True if all items are valid, False if any invalid items are found.
    """
    # For directory processing with many files, use async for better performance and progress reporting
    if path.is_dir() and check_state.get("parallel", True):
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
                include_pattern=check_state["include_pattern"],
                exclude_pattern=check_state["exclude_pattern"],
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
                include_pattern=check_state["include_pattern"],
                exclude_pattern=check_state["exclude_pattern"],
                progress_callback=progress_callback if global_state.get("verbose", False) else None,
            )

            total_items: int = sum(len(items) for items in results.values())
            echo_if_not_quiet(f"Found {total_items} {item_type} across {len(results)} files")

            # Update has_invalid_items from the callback
            has_invalid_items: bool = has_invalid_items or has_invalid_items_ref[0]

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


def check_command(
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
    check_dead_links: bool = typer.Option(
        True,
        "--check-dead-links/--no-check-dead-links",
        help="Whether to check for dead links in markdown files",
    ),
    check_dead_images: bool = typer.Option(
        True,
        "--check-dead-images/--no-check-dead-images",
        help="Whether to check for dead images in markdown files",
    ),
) -> None:
    """Check markdown files for dead links and images.

    By default, both link and image checking are enabled. Use --no-check-dead-links
    or --no-check-dead-images to disable specific checks.

    Examples:
        pymarktools check                             # Check current directory (both links and images)
        pymarktools check docs/                       # Check specific directory
        pymarktools check README.md                   # Check specific file
        pymarktools check --no-check-dead-images      # Check only links
        pymarktools check --no-check-dead-links       # Check only images
    """
    # Use current directory as default if no path specified
    if path is None:
        resolved_path: Path = Path.cwd()
    else:
        resolved_path: Path = path

    # Update global state with command parameters
    check_state.update(
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

    # Validate that at least one check type is enabled
    if not check_state["check_dead_links"] and not check_state["check_dead_images"]:
        echo_error(
            "Error: Both --no-check-dead-links and --no-check-dead-images specified. At least one check type must be enabled."
        )
        raise typer.Exit(1)

    print_common_info(resolved_path)
    echo_info("Checking markdown files...")

    # Show what checks are enabled
    enabled_checks = []
    if check_state["check_dead_links"]:
        enabled_checks.append("dead links")
    if check_state["check_dead_images"]:
        enabled_checks.append("dead images")
    echo_if_verbose(f"Enabled checks: {', '.join(enabled_checks)}")

    all_valid = True

    # Check dead links if enabled
    if check_state["check_dead_links"]:
        echo_info("Checking for dead links...")

        link_checker = DeadLinkChecker(
            timeout=check_state["timeout"],
            check_external=check_state["check_external"],
            check_local=check_state["check_local"],
            fix_redirects=check_state["fix_redirects"],
            follow_gitignore=check_state["follow_gitignore"],
            parallel=check_state["parallel"],
            workers=check_state["workers"],
        )

        # Use async processing for directories with parallel enabled, otherwise use sync
        if check_state.get("parallel", True) and resolved_path.is_dir():
            try:
                links_valid = asyncio.run(process_path_and_check_async(link_checker, "links", resolved_path))
            except RuntimeError:
                # Fall back to sync if already in event loop
                links_valid = process_path_and_check(link_checker, "links", resolved_path)
        else:
            # Use sync processing for files or when parallel is disabled
            links_valid = process_path_and_check(link_checker, "links", resolved_path)

        if not links_valid:
            all_valid = False

    # Check dead images if enabled
    if check_state["check_dead_images"]:
        echo_info("Checking for dead images...")

        image_checker = DeadImageChecker(
            timeout=check_state["timeout"],
            check_external=check_state["check_external"],
            check_local=check_state["check_local"],
            fix_redirects=check_state["fix_redirects"],
            follow_gitignore=check_state["follow_gitignore"],
            parallel=check_state["parallel"],
            workers=check_state["workers"],
        )

        # Use async processing for directories with parallel enabled, otherwise use sync
        if check_state.get("parallel", True) and resolved_path.is_dir():
            try:
                images_valid = asyncio.run(process_path_and_check_async(image_checker, "images", resolved_path))
            except RuntimeError:
                # Fall back to sync if already in event loop
                images_valid = process_path_and_check(image_checker, "images", resolved_path)
        else:
            # Use sync processing for files or when parallel is disabled
            images_valid = process_path_and_check(image_checker, "images", resolved_path)

        if not images_valid:
            all_valid = False

    # Report final results
    if not all_valid:
        if check_state["fail"]:
            echo_error("Some links or images are invalid or broken")
            raise typer.Exit(1)
        else:
            echo_info("Some links or images are invalid or broken; continuing due to --no-fail")
    else:
        echo_success("All links and images are valid")
