"""Format commands for pymarktools CLI."""

import re
from pathlib import Path
from typing import Any

import typer

from ..core.gitignore import get_gitignore_matcher, is_path_ignored
from ..global_state import global_state


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


def echo_if_not_quiet(message: str, err: bool = False, color: str | None = None) -> None:
    """Echo message only if not in quiet mode."""
    if not global_state.get("quiet", False):
        if global_state.get("color", True) and color:
            typer.secho(message, fg=color, err=err)
        else:
            typer.echo(message, err=err)


def echo_if_verbose(message: str, err: bool = False, color: str | None = None) -> None:
    """Echo message only if in verbose mode."""
    if global_state.get("verbose", False):
        if global_state.get("color", True) and color:
            typer.secho(message, fg=color, err=err)
        else:
            typer.echo(message, err=err)


# Create a subcommand group for format operations
format_app: typer.Typer = typer.Typer(
    name="format",
    help="Format and standardize markdown files",
    no_args_is_help=True,
)


class MarkdownFormatter:
    """Formatter for standardizing markdown files."""
    
    def __init__(self) -> None:
        """Initialize the formatter with default rules."""
        pass
    
    def format_content(self, content: str) -> tuple[str, list[str]]:
        """Format markdown content and return formatted content with changes list.
        
        Parameters
        ----------
        content : str
            The original markdown content.
            
        Returns
        -------
        tuple[str, list[str]]
            Tuple of (formatted_content, list_of_changes).
        """
        changes: list[str] = []
        formatted = content
        
        # 1. Normalize line endings
        if '\r\n' in formatted or '\r' in formatted:
            formatted = formatted.replace('\r\n', '\n').replace('\r', '\n')
            changes.append("Normalized line endings to LF")
        
        # 2. Remove trailing whitespace from lines
        lines = formatted.split('\n')
        new_lines = []
        removed_trailing = False
        
        for line in lines:
            stripped = line.rstrip()
            if stripped != line:
                removed_trailing = True
            new_lines.append(stripped)
        
        if removed_trailing:
            changes.append("Removed trailing whitespace")
            
        formatted = '\n'.join(new_lines)
        
        # 3. Ensure single empty line after headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = formatted.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            new_lines.append(line)
            
            # If this is a header line
            if re.match(header_pattern, line):
                # Check if next line is empty, and the one after is not empty
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip() != '':  # Next line is not empty
                        new_lines.append('')  # Add empty line
                        changes.append("Added empty line after header")
                        
            i += 1
        
        formatted = '\n'.join(new_lines)
        
        # 4. Standardize list formatting (ensure space after list markers)
        list_patterns = [
            (r'^(\s*)([-*+])([^\s])', r'\1\2 \3'),  # Unordered lists
            (r'^(\s*)(\d+\.)([^\s])', r'\1\2 \3'),  # Ordered lists
        ]
        
        for pattern, replacement in list_patterns:
            new_formatted = re.sub(pattern, replacement, formatted, flags=re.MULTILINE)
            if new_formatted != formatted:
                changes.append("Standardized list formatting")
                formatted = new_formatted
                break
        
        # 5. Ensure file ends with single newline
        if not formatted.endswith('\n'):
            formatted += '\n'
            changes.append("Added final newline")
        elif formatted.endswith('\n\n'):
            formatted = formatted.rstrip('\n') + '\n'
            changes.append("Removed extra newlines at end of file")
        
        return formatted, changes

    def format_file(self, file_path: Path, dry_run: bool = False) -> tuple[bool, list[str]]:
        """Format a single markdown file.
        
        Parameters
        ----------
        file_path : Path
            Path to the markdown file to format.
        dry_run : bool, optional
            If True, don't write changes, just report what would be done.
            
        Returns
        -------
        tuple[bool, list[str]]
            Tuple of (changes_made, list_of_changes).
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            formatted_content, changes = self.format_content(content)
            
            if formatted_content != content:
                if not dry_run:
                    file_path.write_text(formatted_content, encoding='utf-8')
                return True, changes
            else:
                return False, []
                
        except Exception as e:
            echo_error(f"Error processing {file_path}: {e}")
            return False, []


@format_app.command("markdown")
def format_markdown(
    path: Path | None = typer.Argument(
        None, help="Path to markdown file or directory (defaults to current directory)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be formatted without making changes"
    ),
    include_pattern: str = typer.Option(
        "*.md", "--include", "-i", help="File pattern to include when searching"
    ),
    exclude_pattern: str | None = typer.Option(
        None, "--exclude", "-e", help="File pattern to exclude when searching"
    ),
    follow_gitignore: bool = typer.Option(
        True,
        "--follow-gitignore/--no-follow-gitignore",
        help="Respect .gitignore patterns when scanning directories",
    ),
) -> None:
    """Format markdown files to standardize their structure and style.
    
    This command will:
    - Normalize line endings
    - Remove trailing whitespace
    - Ensure proper spacing around headers
    - Standardize list formatting
    - Ensure files end with a single newline
    """
    if path is None:
        path = Path.cwd()
        
    if dry_run:
        echo_warning("DRY RUN MODE - No changes will be made")
    
    echo_info(f"Formatting markdown files in: {path}")
    echo_if_verbose(f"Include pattern: {include_pattern}")
    if exclude_pattern:
        echo_if_verbose(f"Exclude pattern: {exclude_pattern}")
    echo_if_verbose(f"Following gitignore: {follow_gitignore}")
    
    formatter = MarkdownFormatter()
    
    try:
        if path.is_file():
            if not path.name.endswith(('.md', '.markdown')):
                echo_error(f"File {path} does not appear to be a markdown file")
                raise typer.Exit(1)
                
            changes_made, changes = formatter.format_file(path, dry_run=dry_run)
            if changes_made:
                echo_success(f"{'Would format' if dry_run else 'Formatted'} {path}")
                for change in changes:
                    echo_if_not_quiet(f"  - {change}")
            else:
                echo_if_not_quiet(f"No changes needed for {path}")
                
        elif path.is_dir():
            # Get gitignore matcher if needed
            gitignore_matcher = None
            if follow_gitignore:
                gitignore_matcher = get_gitignore_matcher(path)
            
            # Find all markdown files
            markdown_files = []
            for file_path in path.rglob(include_pattern):
                if file_path.is_file():
                    # Apply exclude pattern if specified
                    if exclude_pattern and file_path.match(exclude_pattern):
                        echo_if_verbose(f"Excluded: {file_path}")
                        continue
                        
                    # Apply gitignore if enabled
                    if gitignore_matcher and is_path_ignored(file_path, gitignore_matcher):
                        echo_if_verbose(f"Ignored by .gitignore: {file_path}")
                        continue
                        
                    markdown_files.append(file_path)
            
            if not markdown_files:
                echo_warning(f"No markdown files found in {path}")
                return
                
            echo_if_not_quiet(f"Found {len(markdown_files)} markdown files")
            
            total_formatted = 0
            total_changes = 0
            
            for md_file in markdown_files:
                changes_made, changes = formatter.format_file(md_file, dry_run=dry_run)
                if changes_made:
                    total_formatted += 1
                    total_changes += len(changes)
                    echo_if_verbose(f"{'Would format' if dry_run else 'Formatted'} {md_file}")
                    for change in changes:
                        echo_if_verbose(f"  - {change}")
                elif global_state.get("verbose", False):
                    echo_if_verbose(f"No changes needed for {md_file}")
            
            if total_formatted > 0:
                echo_success(f"{'Would format' if dry_run else 'Formatted'} {total_formatted} files with {total_changes} total changes")
            else:
                echo_if_not_quiet("No files needed formatting")
        
        else:
            echo_error(f"Error: {path} is not a valid file or directory")
            raise typer.Exit(1)
            
    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)