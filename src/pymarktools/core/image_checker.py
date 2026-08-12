"""Dead image checker for markdown files."""

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from pymarktools import _native

from .async_checker import AsyncChecker
from .models import ImageInfo

logger = logging.getLogger(__name__)


class DeadImageChecker(AsyncChecker[ImageInfo]):
    """Checks for dead images in markdown files."""

    def __init__(
        self,
        timeout: int = 30,
        check_external: bool = True,
        fix_redirects: bool = False,
        follow_gitignore: bool = True,
        check_local: bool = True,
        parallel: bool = True,
        workers: int | None = None,
    ):
        super().__init__(
            timeout=timeout,
            check_external=check_external,
            fix_redirects=fix_redirects,
            follow_gitignore=follow_gitignore,
            check_local=check_local,
            parallel=parallel,
            workers=workers,
        )

    def extract_images(self, content: str) -> list[ImageInfo]:
        """Extract all images from markdown content."""
        return _native.extract_images(content)

    def check_local_path(self, url: str, base_path: Path) -> dict[str, Any]:
        """Check if a local file path exists relative to the base path."""
        try:
            resolved_path = Path(_native.resolve_local_path(url, str(base_path)))
        except Exception as e:
            return {
                "is_valid": False,
                "error": f"Error resolving path: {e}",
                "resolved_path": None,
            }

        if resolved_path.exists():
            return {
                "is_valid": True,
                "error": None,
                "resolved_path": str(resolved_path),
                "path_object": resolved_path,
            }
        return {
            "is_valid": False,
            "error": f"File not found: {resolved_path}",
            "resolved_path": str(resolved_path),
            "path_object": resolved_path,
        }

    async def check_url_async(self, url: str) -> dict[str, Any]:
        """Check if a URL is valid and get redirect information asynchronously."""
        if not self.is_external_url(url):
            # Local file reference, don't check with HTTP
            return {
                "is_valid": True,
                "status_code": None,
                "error": None,
                "redirect_url": None,
                "is_permanent_redirect": False,
            }

        return cast(dict[str, Any], await asyncio.to_thread(_native.check_url, url, self.timeout))

    async def check_file_async(self, file_path: Path) -> list[ImageInfo]:
        """Check all images in a single markdown file asynchronously."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content: str = file_path.read_text(encoding="utf-8")
        images: list[ImageInfo] = self.extract_images(content)
        updated: bool = False

        # Separate external and local images for async processing
        external_images: list[ImageInfo] = []
        local_images: list[ImageInfo] = []

        for image in images:
            if self.is_external_url(image.url):
                image.is_local = False
                external_images.append(image)
            else:
                image.is_local = True
                local_images.append(image)

        # Process external images asynchronously if enabled and checking external images
        if self.check_external and external_images:
            external_urls: list[str] = [image.url for image in external_images]
            url_results: dict[str, dict[str, Any]] = await self.check_urls_async(external_urls)

            for image in external_images:
                check_result = url_results[image.url]
                image.is_valid = check_result["is_valid"]
                image.status_code = check_result["status_code"]
                image.error = check_result["error"]

                # Store redirect information
                image.redirect_url = check_result["redirect_url"]
                image.is_permanent_redirect = check_result["is_permanent_redirect"]

                # Handle fixing redirects if needed
                if self.fix_redirects and check_result["is_permanent_redirect"] and check_result["redirect_url"]:
                    # Update content with the redirect URL - don't use regex here
                    old_markdown: str = f"![{image.alt_text}]({image.url})"
                    new_markdown: str = f"![{image.alt_text}]({check_result['redirect_url']})"
                    content = content.replace(old_markdown, new_markdown)
                    image.url = check_result["redirect_url"]
                    image.updated = True
                    updated = True
        else:
            # External images but not checking - mark as valid
            for image in external_images:
                image.is_valid = True
                image.status_code = 200

        # Process local images sequentially (file I/O is typically fast and doesn't benefit much from parallelization)
        for image in local_images:
            if self.check_local:
                local_result: dict[str, Any] = self.check_local_path(image.url, file_path)
                image.is_valid = local_result["is_valid"]
                image.local_path = local_result["resolved_path"]
                if not local_result["is_valid"]:
                    image.error = local_result["error"]
            else:
                # Local image but not checking - mark as valid
                image.is_valid = True

        # If any redirects were fixed, update the file
        if updated:
            file_path.write_text(content, encoding="utf-8")

        return images

    def check_file(self, file_path: Path) -> list[ImageInfo]:
        """Check all images in a single markdown file (synchronous wrapper)."""
        result = self.run_async_with_fallback(self.check_file_async, file_path)
        return cast(list[ImageInfo], result)

    async def check_urls_async(self, urls: list[str]) -> dict[str, dict[str, Any]]:
        """Check multiple URLs asynchronously using asyncio."""
        # Check if check_url method has been overridden (for test compatibility)
        # This happens in tests where they replace the method directly or subclass
        method_is_overridden = (
            self.__class__.check_url is not DeadImageChecker.check_url  # Subclassed
            or (hasattr(self.check_url, "__name__") and self.check_url.__name__ != "check_url")  # Renamed function
            or str(type(self.check_url)) == "<class 'function'>"  # Standalone function
        )

        if method_is_overridden:
            # Fall back to sequential processing when method is overridden
            results = {}
            for url in urls:
                results[url] = self.check_url(url)
            return results

        # Use the base class async processing utility
        return await self.process_items_async(urls, self.check_url_async)

    async def check_directory_async(
        self,
        directory: Path,
        include_pattern: str = "*.md",
        exclude_pattern: str | None = None,
        progress_callback: Callable[[Path, list[ImageInfo]], None] | None = None,
    ) -> dict[Path, list[ImageInfo]]:
        """Check all markdown files in ``directory`` using async processing.

        Parameters
        ----------
        directory : Path
            Directory to search.
        include_pattern : str, optional
            Glob pattern for files to include, by default ``"*.md"``.
        exclude_pattern : str or None, optional
            Glob pattern for files to exclude.
        progress_callback : Callable[[Path, list[ImageInfo]], None] or None, optional
            Optional callback for progress reporting.
        """
        # Discover files asynchronously
        files_to_check = await self.discover_files_async(directory, include_pattern, exclude_pattern)

        # Process files asynchronously with progress callback
        results = await self.process_files_async(
            files_to_check,
            self.check_file_async,
            progress_callback,
        )

        return results

    def check_directory(
        self,
        directory: Path,
        include_pattern: str = "*.md",
        exclude_pattern: str | None = None,
    ) -> dict[Path, list[ImageInfo]]:
        """Check all markdown files in ``directory`` synchronously.

        Parameters
        ----------
        directory : Path
            Directory to search.
        include_pattern : str, optional
            Glob pattern for files to include, by default ``"*.md"``.
        exclude_pattern : str or None, optional
            Glob pattern for files to exclude.
        """
        return cast(
            dict[Path, list[ImageInfo]],
            self.run_async_with_fallback(self.check_directory_async, directory, include_pattern, exclude_pattern),
        )

    def check_url(self, url: str) -> dict[str, Any]:
        """Check if a URL is valid and get redirect information (synchronous wrapper for backward compatibility)."""
        result = self.run_async_with_fallback(self.check_url_async, url)
        return cast(dict[str, Any], result)
