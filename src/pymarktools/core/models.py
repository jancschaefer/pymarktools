"""Data models for markdown processing."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LinkInfo:
    """Information about a link found in markdown."""

    text: str
    url: str
    line_number: int
    is_valid: Optional[bool] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    redirect_url: Optional[str] = None
    is_permanent_redirect: Optional[bool] = None
    updated: bool = False
    is_local: Optional[bool] = None
    local_path: Optional[str] = None


@dataclass
class ImageInfo:
    """Information about an image found in markdown."""

    alt_text: str
    url: str
    line_number: int
    is_valid: Optional[bool] = None
    status_code: Optional[int] = None
    error: Optional[str] = None
    redirect_url: Optional[str] = None
    is_permanent_redirect: Optional[bool] = None
    updated: bool = False
    is_local: Optional[bool] = None
    local_path: Optional[str] = None
