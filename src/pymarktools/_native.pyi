"""Typed bindings for pymarktools' compiled Rust core."""


class LinkInfo:
    text: str
    url: str
    line_number: int
    is_valid: bool | None
    status_code: int | None
    error: str | None
    redirect_url: str | None
    is_permanent_redirect: bool | None
    updated: bool
    is_local: bool | None
    local_path: str | None


class ImageInfo:
    alt_text: str
    url: str
    line_number: int
    is_valid: bool | None
    status_code: int | None
    error: str | None
    redirect_url: str | None
    is_permanent_redirect: bool | None
    updated: bool
    is_local: bool | None
    local_path: str | None


def core_version() -> str:
    """Return the compiled Rust core version."""


def extract_links(content: str) -> list[LinkInfo]: ...
def extract_images(content: str) -> list[ImageInfo]: ...
def resolve_local_path(url: str, document_path: str) -> str: ...
