"""Data models for markdown processing."""

from dataclasses import dataclass


@dataclass
class LinkInfo:
    """Information about a link found in markdown."""

    text: str
    url: str
    line_number: int
    is_valid: bool | None = None
    status_code: int | None = None
    error: str | None = None
    redirect_url: str | None = None
    is_permanent_redirect: bool | None = None
    updated: bool = False
    is_local: bool | None = None
    local_path: str | None = None


@dataclass
class ImageInfo:
    """Information about an image found in markdown."""

    alt_text: str
    url: str
    line_number: int
    is_valid: bool | None = None
    status_code: int | None = None
    error: str | None = None
    redirect_url: str | None = None
    is_permanent_redirect: bool | None = None
    updated: bool = False
    is_local: bool | None = None
    local_path: str | None = None
