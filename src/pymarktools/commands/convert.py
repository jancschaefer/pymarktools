"""Convert commands for pymarktools CLI."""

import csv
import json
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


# Create a subcommand group for convert operations
convert_app: typer.Typer = typer.Typer(
    name="convert",
    help="Convert and extract data from markdown files",
    no_args_is_help=True,
)


class MarkdownConverter:
    """Converter for extracting and transforming markdown content."""
    
    def __init__(self) -> None:
        """Initialize the converter."""
        pass
    
    def extract_links(self, content: str, file_path: Path | None = None) -> list[dict[str, Any]]:
        """Extract links from markdown content.
        
        Parameters
        ----------
        content : str
            The markdown content to extract from.
        file_path : Path | None, optional
            Path to the source file for reference.
            
        Returns
        -------
        list[dict[str, Any]]
            List of link dictionaries with text, url, and metadata.
        """
        links = []
        link_pattern = r'\[([^\]]*)\]\(([^)]+)\)'
        
        for match in re.finditer(link_pattern, content):
            text = match.group(1)
            url = match.group(2)
            
            # Determine link type
            link_type = "external"
            if url.startswith('mailto:'):
                link_type = "email"
            elif url.startswith(('#', '/')):
                link_type = "anchor" if url.startswith('#') else "absolute"
            elif not url.startswith(('http://', 'https://')):
                link_type = "relative"
            
            links.append({
                'text': text,
                'url': url,
                'type': link_type,
                'file': str(file_path) if file_path else None,
                'position': match.start()
            })
        
        return links
    
    def extract_images(self, content: str, file_path: Path | None = None) -> list[dict[str, Any]]:
        """Extract images from markdown content.
        
        Parameters
        ----------
        content : str
            The markdown content to extract from.
        file_path : Path | None, optional
            Path to the source file for reference.
            
        Returns
        -------
        list[dict[str, Any]]
            List of image dictionaries with alt text, url, and metadata.
        """
        images = []
        image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        
        for match in re.finditer(image_pattern, content):
            alt_text = match.group(1)
            url = match.group(2)
            
            # Determine image type
            img_type = "external"
            if not url.startswith(('http://', 'https://')):
                img_type = "relative"
            
            # Extract file extension
            extension = Path(url).suffix.lower() if '?' not in url else Path(url.split('?')[0]).suffix.lower()
            
            images.append({
                'alt_text': alt_text,
                'url': url,
                'type': img_type,
                'extension': extension,
                'file': str(file_path) if file_path else None,
                'position': match.start()
            })
        
        return images
    
    def extract_headings(self, content: str, file_path: Path | None = None) -> list[dict[str, Any]]:
        """Extract headings from markdown content.
        
        Parameters
        ----------
        content : str
            The markdown content to extract from.
        file_path : Path | None, optional
            Path to the source file for reference.
            
        Returns
        -------
        list[dict[str, Any]]
            List of heading dictionaries with level, text, and metadata.
        """
        headings = []
        lines = content.split('\n')
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        
        for line_num, line in enumerate(lines, 1):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                
                # Generate anchor (simplified)
                anchor = text.lower().replace(' ', '-').replace(',', '').replace('.', '')
                anchor = re.sub(r'[^\w\-]', '', anchor)
                
                headings.append({
                    'level': level,
                    'text': text,
                    'anchor': anchor,
                    'line_number': line_num,
                    'file': str(file_path) if file_path else None
                })
        
        return headings


@convert_app.command("links")
def extract_links(
    path: Path | None = typer.Argument(
        None, help="Path to markdown file or directory (defaults to current directory)"
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output file for the extracted links"
    ),
    format_type: str = typer.Option(
        "json", "--format", "-f", help="Output format: json, csv, markdown"
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
    """Extract all links from markdown files and export them in various formats.
    
    This command finds all markdown links and exports them as JSON, CSV, or markdown
    format for further analysis or processing.
    """
    if path is None:
        path = Path.cwd()
        
    echo_info(f"Extracting links from: {path}")
    
    converter = MarkdownConverter()
    all_links = []
    
    try:
        if path.is_file():
            if not path.name.endswith(('.md', '.markdown')):
                echo_error(f"File {path} does not appear to be a markdown file")
                raise typer.Exit(1)
                
            content = path.read_text(encoding='utf-8')
            links = converter.extract_links(content, path)
            all_links.extend(links)
                
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
                
            echo_if_not_quiet(f"Processing {len(markdown_files)} markdown files")
            
            # Extract links from each file
            for md_file in markdown_files:
                echo_if_verbose(f"Processing {md_file}")
                try:
                    content = md_file.read_text(encoding='utf-8')
                    links = converter.extract_links(content, md_file.relative_to(path))
                    all_links.extend(links)
                except Exception as e:
                    echo_warning(f"Could not process {md_file}: {e}")
        
        else:
            echo_error(f"Error: {path} is not a valid file or directory")
            raise typer.Exit(1)
        
        echo_if_not_quiet(f"Found {len(all_links)} links")
        
        # Generate output in requested format
        if format_type == "json":
            output_content = json.dumps(all_links, indent=2)
        elif format_type == "csv":
            output_content = _links_to_csv(all_links)
        elif format_type == "markdown":
            output_content = _links_to_markdown(all_links)
        else:
            echo_error(f"Unknown format: {format_type}")
            raise typer.Exit(1)
        
        # Output the results
        if output:
            output.write_text(output_content, encoding='utf-8')
            echo_success(f"Links exported to {output}")
        else:
            echo_if_not_quiet(output_content)
            
    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)


@convert_app.command("images")
def extract_images(
    path: Path | None = typer.Argument(
        None, help="Path to markdown file or directory (defaults to current directory)"
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output file for the extracted images"
    ),
    format_type: str = typer.Option(
        "json", "--format", "-f", help="Output format: json, csv, markdown"
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
    """Extract all images from markdown files and export them in various formats.
    
    This command finds all markdown image references and exports them as JSON, CSV,
    or markdown format for further analysis or processing.
    """
    if path is None:
        path = Path.cwd()
        
    echo_info(f"Extracting images from: {path}")
    
    converter = MarkdownConverter()
    all_images = []
    
    try:
        if path.is_file():
            if not path.name.endswith(('.md', '.markdown')):
                echo_error(f"File {path} does not appear to be a markdown file")
                raise typer.Exit(1)
                
            content = path.read_text(encoding='utf-8')
            images = converter.extract_images(content, path)
            all_images.extend(images)
                
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
                
            echo_if_not_quiet(f"Processing {len(markdown_files)} markdown files")
            
            # Extract images from each file
            for md_file in markdown_files:
                echo_if_verbose(f"Processing {md_file}")
                try:
                    content = md_file.read_text(encoding='utf-8')
                    images = converter.extract_images(content, md_file.relative_to(path))
                    all_images.extend(images)
                except Exception as e:
                    echo_warning(f"Could not process {md_file}: {e}")
        
        else:
            echo_error(f"Error: {path} is not a valid file or directory")
            raise typer.Exit(1)
        
        echo_if_not_quiet(f"Found {len(all_images)} images")
        
        # Generate output in requested format
        if format_type == "json":
            output_content = json.dumps(all_images, indent=2)
        elif format_type == "csv":
            output_content = _images_to_csv(all_images)
        elif format_type == "markdown":
            output_content = _images_to_markdown(all_images)
        else:
            echo_error(f"Unknown format: {format_type}")
            raise typer.Exit(1)
        
        # Output the results
        if output:
            output.write_text(output_content, encoding='utf-8')
            echo_success(f"Images exported to {output}")
        else:
            echo_if_not_quiet(output_content)
            
    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)


@convert_app.command("headings")
def extract_headings(
    path: Path | None = typer.Argument(
        None, help="Path to markdown file or directory (defaults to current directory)"
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output file for the extracted headings"
    ),
    format_type: str = typer.Option(
        "json", "--format", "-f", help="Output format: json, csv, markdown"
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
    """Extract all headings from markdown files and export them in various formats.
    
    This command finds all markdown headings and exports them as JSON, CSV,
    or markdown format for creating indexes or analysis.
    """
    if path is None:
        path = Path.cwd()
        
    echo_info(f"Extracting headings from: {path}")
    
    converter = MarkdownConverter()
    all_headings = []
    
    try:
        if path.is_file():
            if not path.name.endswith(('.md', '.markdown')):
                echo_error(f"File {path} does not appear to be a markdown file")
                raise typer.Exit(1)
                
            content = path.read_text(encoding='utf-8')
            headings = converter.extract_headings(content, path)
            all_headings.extend(headings)
                
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
                
            echo_if_not_quiet(f"Processing {len(markdown_files)} markdown files")
            
            # Extract headings from each file
            for md_file in markdown_files:
                echo_if_verbose(f"Processing {md_file}")
                try:
                    content = md_file.read_text(encoding='utf-8')
                    headings = converter.extract_headings(content, md_file.relative_to(path))
                    all_headings.extend(headings)
                except Exception as e:
                    echo_warning(f"Could not process {md_file}: {e}")
        
        else:
            echo_error(f"Error: {path} is not a valid file or directory")
            raise typer.Exit(1)
        
        echo_if_not_quiet(f"Found {len(all_headings)} headings")
        
        # Generate output in requested format
        if format_type == "json":
            output_content = json.dumps(all_headings, indent=2)
        elif format_type == "csv":
            output_content = _headings_to_csv(all_headings)
        elif format_type == "markdown":
            output_content = _headings_to_markdown(all_headings)
        else:
            echo_error(f"Unknown format: {format_type}")
            raise typer.Exit(1)
        
        # Output the results
        if output:
            output.write_text(output_content, encoding='utf-8')
            echo_success(f"Headings exported to {output}")
        else:
            echo_if_not_quiet(output_content)
            
    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)


def _links_to_csv(links: list[dict[str, Any]]) -> str:
    """Convert links list to CSV format."""
    if not links:
        return "text,url,type,file\n"
        
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['text', 'url', 'type', 'file'])
    writer.writeheader()
    
    for link in links:
        writer.writerow({
            'text': link['text'],
            'url': link['url'],
            'type': link['type'],
            'file': link['file'] or ''
        })
    
    return output.getvalue()


def _images_to_csv(images: list[dict[str, Any]]) -> str:
    """Convert images list to CSV format."""
    if not images:
        return "alt_text,url,type,extension,file\n"
        
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['alt_text', 'url', 'type', 'extension', 'file'])
    writer.writeheader()
    
    for image in images:
        writer.writerow({
            'alt_text': image['alt_text'],
            'url': image['url'], 
            'type': image['type'],
            'extension': image['extension'],
            'file': image['file'] or ''
        })
    
    return output.getvalue()


def _headings_to_csv(headings: list[dict[str, Any]]) -> str:
    """Convert headings list to CSV format."""
    if not headings:
        return "level,text,anchor,line_number,file\n"
        
    import io
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['level', 'text', 'anchor', 'line_number', 'file'])
    writer.writeheader()
    
    for heading in headings:
        writer.writerow({
            'level': heading['level'],
            'text': heading['text'],
            'anchor': heading['anchor'],
            'line_number': heading['line_number'],
            'file': heading['file'] or ''
        })
    
    return output.getvalue()


def _links_to_markdown(links: list[dict[str, Any]]) -> str:
    """Convert links list to markdown format."""
    lines = ["# Extracted Links\n"]
    
    if not links:
        lines.append("No links found.\n")
        return '\n'.join(lines)
    
    # Group by file
    files = {}
    for link in links:
        file_name = link['file'] or 'Unknown'
        if file_name not in files:
            files[file_name] = []
        files[file_name].append(link)
    
    for file_name, file_links in files.items():
        lines.append(f"## {file_name}")
        lines.append("")
        for link in file_links:
            lines.append(f"- [{link['text']}]({link['url']}) ({link['type']})")
        lines.append("")
    
    return '\n'.join(lines)


def _images_to_markdown(images: list[dict[str, Any]]) -> str:
    """Convert images list to markdown format."""
    lines = ["# Extracted Images\n"]
    
    if not images:
        lines.append("No images found.\n")
        return '\n'.join(lines)
    
    # Group by file
    files = {}
    for image in images:
        file_name = image['file'] or 'Unknown'
        if file_name not in files:
            files[file_name] = []
        files[file_name].append(image)
    
    for file_name, file_images in files.items():
        lines.append(f"## {file_name}")
        lines.append("")
        for image in file_images:
            lines.append(f"- ![{image['alt_text']}]({image['url']}) ({image['type']}, {image['extension']})")
        lines.append("")
    
    return '\n'.join(lines)


def _headings_to_markdown(headings: list[dict[str, Any]]) -> str:
    """Convert headings list to markdown format."""
    lines = ["# Extracted Headings\n"]
    
    if not headings:
        lines.append("No headings found.\n")
        return '\n'.join(lines)
    
    # Group by file
    files = {}
    for heading in headings:
        file_name = heading['file'] or 'Unknown'
        if file_name not in files:
            files[file_name] = []
        files[file_name].append(heading)
    
    for file_name, file_headings in files.items():
        lines.append(f"## {file_name}")
        lines.append("")
        for heading in file_headings:
            indent = "  " * (heading['level'] - 1)
            lines.append(f"{indent}- **H{heading['level']}:** {heading['text']} (line {heading['line_number']})")
        lines.append("")
    
    return '\n'.join(lines)