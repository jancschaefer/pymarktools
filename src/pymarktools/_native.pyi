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
def discover_files(
    directory: str, include_pattern: str = "*.md", exclude_pattern: str | None = None, follow_gitignore: bool = True
) -> list[str]: ...
def check_url(url: str, timeout: int) -> dict[str, object]: ...
def check_email_domain(domain: str, timeout: int) -> dict[str, object]: ...
def relative_reference(from_dir: str, to_file: str) -> str: ...
def rewrite_reference(reference: str, old_target: str, new_target: str) -> str: ...
def find_references(
    target_file: str, base_dir: str, include_pattern: str = "*.md", exclude_pattern: str | None = None
) -> list[dict[str, object]]: ...
def move_and_rewrite(source: str, destination: str, base_dir: str) -> None: ...
def load_tool_config(path: str) -> str: ...
