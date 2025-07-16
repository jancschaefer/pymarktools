"""Dead image checker for markdown files."""

import logging
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import httpx

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
        self.image_pattern = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")

    def extract_images(self, content: str) -> list[ImageInfo]:
        """Extract all images from markdown content."""
        images: list[ImageInfo] = []
        lines: list[str] = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            matches = self.image_pattern.findall(line)
            for alt_text, url in matches:
                images.append(ImageInfo(alt_text=alt_text, url=url, line_number=line_num))

        return images

    def check_local_path(self, url: str, base_path: Path) -> dict[str, Any]:
        """Check if a local file path exists relative to the base path."""
        result: dict[str, Any] = {
            "is_valid": False,
            "error": None,
            "resolved_path": None,
        }

        try:
            # Handle different types of local links
            clean_url: str = url.split("#")[0].split("?")[0]  # Remove anchors and query params

            if clean_url.startswith("/"):
                # Absolute path - resolve from base_path parent directory
                # This assumes the markdown file is in a subdirectory of the project
                resolved_path: Path = base_path.parent / clean_url.lstrip("/")
            else:
                # Relative path - resolve from the directory containing the markdown file
                resolved_path = base_path.parent / clean_url

            # Normalize the path to handle .. and . components
            resolved_path = resolved_path.resolve()

            # Store the resolved path as string - for tests, use the Path object directly
            result["resolved_path"] = str(resolved_path)
            # Also store the path object for reliable comparison across platforms and symlinks
            result["path_object"] = resolved_path

            if resolved_path.exists():
                result["is_valid"] = True
            else:
                result["error"] = f"File not found: {resolved_path}"

        except Exception as e:
            result["error"] = f"Error resolving path: {e}"

        return result

    async def check_url_async(self, url: str) -> dict[str, Any]:
        """Check if a URL is valid and get redirect information asynchronously."""
        result: dict[str, Any] = {
            "is_valid": False,
            "status_code": None,
            "error": None,
            "redirect_url": None,
            "is_permanent_redirect": False,
        }

        if not self.is_external_url(url):
            # Local file reference, don't check with HTTP
            result["is_valid"] = True
            return result

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response: httpx.Response = await client.head(url)
                result["status_code"] = response.status_code

                # Check for redirects (301 permanent, 302 temporary)
                if response.status_code in (301, 307, 308):  # Permanent redirects
                    result["is_permanent_redirect"] = True
                    result["redirect_url"] = response.headers.get("location")
                elif response.status_code == 302:  # Temporary redirect
                    result["redirect_url"] = response.headers.get("location")

                # Consider anything in 2xx range as valid
                result["is_valid"] = 200 <= response.status_code < 300 or response.status_code in (301, 302, 307, 308)

        except httpx.RequestError as e:
            result["error"] = str(e)

        return result

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
        """Check all markdown files in a directory recursively using async processing.

        Args:
            directory: Directory to search
            include_pattern: Glob pattern for files to include (default: "*.md")
            exclude_pattern: Glob pattern for files to exclude (optional)
            progress_callback: Optional callback for progress reporting
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
        """Check all markdown files in a directory recursively (synchronous wrapper).

        Args:
            directory: Directory to search
            include_pattern: Glob pattern for files to include (default: "*.md")
            exclude_pattern: Glob pattern for files to exclude (optional)
        """
        return cast(
            dict[Path, list[ImageInfo]],
            self.run_async_with_fallback(self.check_directory_async, directory, include_pattern, exclude_pattern),
        )

    def check_url(self, url: str) -> dict[str, Any]:
        """Check if a URL is valid and get redirect information (synchronous wrapper for backward compatibility)."""
        result = self.run_async_with_fallback(self.check_url_async, url)
        return cast(dict[str, Any], result)
