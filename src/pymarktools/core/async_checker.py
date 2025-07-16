"""Base async checker class for pymarktools."""

import asyncio
import fnmatch
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from .gitignore import get_gitignore_matcher, is_path_ignored

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Type for the result objects (LinkInfo, ImageInfo, etc.)


class AsyncChecker[T]:
    """Base class for async checkers with utilities for concurrent processing."""

    timeout: int
    check_external: bool
    fix_redirects: bool
    follow_gitignore: bool
    check_local: bool
    parallel: bool
    workers: int | None

    def __init__(
        self: "AsyncChecker",
        timeout: int = 30,
        check_external: bool = True,
        fix_redirects: bool = False,
        follow_gitignore: bool = True,
        check_local: bool = True,
        parallel: bool = True,
        workers: int | None = None,
    ):
        self.timeout = timeout
        self.check_external = check_external
        self.fix_redirects = fix_redirects
        self.follow_gitignore = follow_gitignore
        self.check_local = check_local
        self.parallel = parallel
        self.workers = workers if workers is not None else os.cpu_count()

    async def discover_files_async(
        self: "AsyncChecker",
        directory: Path,
        include_pattern: str = "*.md",
        exclude_pattern: str | None = None,
    ) -> list[Path]:
        """Discover files asynchronously with first-level directory listing and parallel expansion."""
        if not directory.is_dir():
            return [directory] if directory.is_file() else []

        # Get gitignore matcher if needed
        gitignore_matcher: Callable[[str], bool] | None = None
        if self.follow_gitignore:
            gitignore_matcher = get_gitignore_matcher(directory)

        async def check_and_add_file(file_path: Path) -> Path | None:
            """Check if a file should be included."""
            if not file_path.is_file():
                return None

            # Check exclude pattern
            if exclude_pattern:
                relative_path = file_path.relative_to(directory)
                if fnmatch.fnmatch(str(relative_path), exclude_pattern) or fnmatch.fnmatch(
                    file_path.name, exclude_pattern
                ):
                    return None

            # Check gitignore
            if self.follow_gitignore and gitignore_matcher:
                if is_path_ignored(file_path, gitignore_matcher):
                    return None

            # Check include pattern
            if fnmatch.fnmatch(file_path.name, include_pattern):
                return file_path
            return None

        async def process_directory_level(dir_path: Path) -> list[Path]:
            """Process a single directory level and return matching files."""
            try:
                files: list[Path] = []
                subdirs: list[Path] = []

                # Separate files and directories
                for item in dir_path.iterdir():
                    if item.is_file():
                        files.append(item)
                    elif item.is_dir():
                        subdirs.append(item)

                # Process files in current directory
                file_tasks: list[asyncio.Task[Path | None]] = [
                    asyncio.create_task(check_and_add_file(file_path)) for file_path in files
                ]
                file_results: list[Path | None | BaseException] = await asyncio.gather(
                    *file_tasks, return_exceptions=True
                )

                valid_files = [f for f in file_results if isinstance(f, Path)]

                # Process subdirectories recursively
                if subdirs:
                    subdir_tasks = [process_directory_level(subdir) for subdir in subdirs]
                    subdir_results = await asyncio.gather(*subdir_tasks, return_exceptions=True)

                    for result in subdir_results:
                        if isinstance(result, list):
                            valid_files.extend(result)

                return valid_files

            except (PermissionError, OSError) as e:
                logger.debug(f"Cannot access directory {dir_path}: {e}")
                return []

        # Start the async file discovery
        return await process_directory_level(directory)

    def run_async_with_fallback(self: "AsyncChecker", coro_func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run an async function with fallback to thread pool if already in event loop."""
        try:
            asyncio.get_running_loop()
            # We're already in an async context, can't use asyncio.run()
            # Fall back to creating a new event loop in a thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro_func(*args, **kwargs))
                return future.result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            return asyncio.run(coro_func(*args, **kwargs))

    async def process_files_async(
        self: "AsyncChecker",
        files: list[Path],
        file_processor: Callable[[Path], Any],
        progress_callback: Callable[[Path, Any], None] | None = None,
    ) -> dict[Path, Any]:
        """Process files asynchronously with progress callbacks."""
        results: dict[Path, Any] = {}

        # Use semaphore to limit concurrent file processing
        file_semaphore = asyncio.Semaphore(min(len(files), self.workers or os.cpu_count() or 4))

        async def process_file_safe(file_path: Path) -> tuple[Path, Any]:
            async with file_semaphore:
                try:
                    result: Any = await file_processor(file_path)

                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(file_path, result)

                    return file_path, result
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    return file_path, None

        # Process all files concurrently
        if files:
            tasks: list[asyncio.Task[tuple[Path, Any]]] = [
                asyncio.create_task(process_file_safe(file_path)) for file_path in files
            ]
            file_results: list[tuple[Path, Any] | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)

            for result in file_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in async file processing: {result}")
                    continue

                if isinstance(result, tuple) and len(result) == 2:
                    file_path, file_result = result
                    if file_result is not None:
                        results[file_path] = file_result

        return results

    async def process_items_async(
        self: "AsyncChecker",
        items: list[str],
        item_processor: Callable[[str], Any],
    ) -> dict[str, Any]:
        """Process individual items (like URLs) asynchronously."""
        results: dict[str, Any] = {}

        if not self.parallel or len(items) <= 1:
            # Fall back to sequential processing for small batches or when disabled
            for item in items:
                results[item] = await item_processor(item)
            return results

        # Use asyncio.gather for concurrent execution with semaphore for rate limiting
        semaphore = asyncio.Semaphore(self.workers or os.cpu_count() or 4)

        async def process_with_semaphore(item: str) -> tuple[str, Any]:
            async with semaphore:
                result = await item_processor(item)
                return item, result

        try:
            # Execute all item checks concurrently
            tasks: list[asyncio.Task[tuple[str, Any]]] = [
                asyncio.create_task(process_with_semaphore(item)) for item in items
            ]
            task_results: list[tuple[str, Any] | BaseException] = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for task_result in task_results:
                if isinstance(task_result, Exception):
                    logger.error(f"Error in async item processing: {task_result}")
                    continue

                if isinstance(task_result, tuple) and len(task_result) == 2:
                    item, result = task_result
                    results[item] = result

        except Exception as e:
            logger.error(f"Error in async item processing: {e}")
            # Fall back to sequential processing on error
            for item in items:
                try:
                    results[item] = await item_processor(item)
                except Exception as item_error:
                    logger.error(f"Error processing item {item}: {item_error}")
                    results[item] = None

        return results

    def is_external_url(self: "AsyncChecker", url: str) -> bool:
        """Check if URL is external (has a scheme)."""
        # Common external URL schemes
        external_schemes = (
            "ftp://",  # File transfer
            "ftps://",  # Secure File transfer
            "http://",  # Web
            "https://",  # Secure Web
            "mailto:",  # Email
            "sftp://",  # Secure shell/file transfer
            "sms:",  # Telephone/SMS
            "ssh://",  # Secure shell
            "tel:",  # Telephone
        )
        return url.startswith(external_schemes)
