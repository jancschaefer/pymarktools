"""Report commands for pymarktools CLI."""

import json
import re
from pathlib import Path
from typing import Any

import typer

from ..core.gitignore import get_gitignore_matcher, is_path_ignored
from ..core.link_checker import DeadLinkChecker
from ..core.image_checker import DeadImageChecker
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


# Create a subcommand group for report operations  
report_app: typer.Typer = typer.Typer(
    name="report",
    help="Generate analysis reports for markdown content",
    no_args_is_help=True,
)


class MarkdownAnalyzer:
    """Analyzer for generating reports about markdown content."""
    
    def __init__(self) -> None:
        """Initialize the analyzer."""
        pass
    
    def analyze_headings(self, content: str) -> dict[str, Any]:
        """Analyze heading structure in markdown content.
        
        Parameters
        ----------
        content : str
            The markdown content to analyze.
            
        Returns
        -------
        dict[str, Any]
            Analysis results including heading hierarchy and issues.
        """
        lines = content.split('\n')
        headings = []
        heading_pattern = r'^(#{1,6})\s+(.+)$'
        
        for line_num, line in enumerate(lines, 1):
            match = re.match(heading_pattern, line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append({
                    'level': level,
                    'text': text,
                    'line': line_num
                })
        
        # Check for heading hierarchy issues
        issues = []
        prev_level = 0
        
        for i, heading in enumerate(headings):
            level = heading['level']
            if prev_level > 0 and level > prev_level + 1:
                issues.append(f"Line {heading['line']}: Heading level jumps from h{prev_level} to h{level}")
            prev_level = level
        
        return {
            'headings': headings,
            'heading_count': len(headings),
            'max_level': max([h['level'] for h in headings]) if headings else 0,
            'hierarchy_issues': issues
        }
    
    def analyze_content_stats(self, content: str) -> dict[str, Any]:
        """Analyze basic content statistics.
        
        Parameters
        ----------
        content : str
            The markdown content to analyze.
            
        Returns
        -------
        dict[str, Any]
            Basic content statistics.
        """
        lines = content.split('\n')
        words = content.split()
        
        # Count different markdown elements
        code_blocks = len(re.findall(r'```[\s\S]*?```', content))
        inline_code = len(re.findall(r'`[^`]+`', content))
        
        # Links and images (basic count)
        links = len(re.findall(r'\[([^\]]*)\]\(([^)]+)\)', content))
        images = len(re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content))
        
        # Lists
        bullet_lists = len(re.findall(r'^\s*[-*+]\s', content, re.MULTILINE))
        numbered_lists = len(re.findall(r'^\s*\d+\.\s', content, re.MULTILINE))
        
        return {
            'line_count': len(lines),
            'word_count': len(words),
            'character_count': len(content),
            'code_blocks': code_blocks,
            'inline_code': inline_code,
            'links': links,
            'images': images,
            'bullet_list_items': bullet_lists,
            'numbered_list_items': numbered_lists
        }
    
    def generate_toc(self, headings: list[dict[str, Any]], max_level: int = 3) -> str:
        """Generate a table of contents from headings.
        
        Parameters
        ----------
        headings : list[dict[str, Any]]
            List of heading dictionaries with level, text, and line.
        max_level : int, optional
            Maximum heading level to include in TOC.
            
        Returns
        -------
        str
            Generated table of contents markdown.
        """
        if not headings:
            return "No headings found.\n"
            
        toc_lines = ["# Table of Contents\n"]
        
        for heading in headings:
            level = heading['level']
            text = heading['text']
            
            if level <= max_level:
                indent = "  " * (level - 1)
                # Create anchor link (simplified)
                anchor = text.lower().replace(' ', '-').replace(',', '').replace('.', '')
                anchor = re.sub(r'[^\w\-]', '', anchor)
                toc_lines.append(f"{indent}- [{text}](#{anchor})")
        
        return '\n'.join(toc_lines) + '\n'


@report_app.command("summary")
def generate_summary(
    path: Path | None = typer.Argument(
        None, help="Path to markdown file or directory (defaults to current directory)"
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output file for the summary report"
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
    format_type: str = typer.Option(
        "text", "--format", "-f", help="Output format: text, json, markdown"
    ),
) -> None:
    """Generate a summary report of markdown content analysis.
    
    This command analyzes markdown files and generates a comprehensive
    summary including heading structure, content statistics, and potential issues.
    """
    if path is None:
        path = Path.cwd()
        
    echo_info(f"Generating summary report for: {path}")
    
    analyzer = MarkdownAnalyzer()
    
    try:
        if path.is_file():
            if not path.name.endswith(('.md', '.markdown')):
                echo_error(f"File {path} does not appear to be a markdown file")
                raise typer.Exit(1)
                
            content = path.read_text(encoding='utf-8')
            heading_analysis = analyzer.analyze_headings(content)
            stats = analyzer.analyze_content_stats(content)
            
            report_data = {
                'file': str(path),
                'heading_analysis': heading_analysis,
                'content_stats': stats
            }
            
            # Generate output
            if format_type == "json":
                report_content = json.dumps(report_data, indent=2)
            elif format_type == "markdown":
                report_content = _generate_markdown_report([report_data])
            else:  # text
                report_content = _generate_text_report([report_data])
                
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
                
            echo_if_not_quiet(f"Analyzing {len(markdown_files)} markdown files")
            
            # Analyze each file
            reports = []
            for md_file in markdown_files:
                echo_if_verbose(f"Analyzing {md_file}")
                try:
                    content = md_file.read_text(encoding='utf-8')
                    heading_analysis = analyzer.analyze_headings(content)
                    stats = analyzer.analyze_content_stats(content)
                    
                    reports.append({
                        'file': str(md_file.relative_to(path)),
                        'heading_analysis': heading_analysis,
                        'content_stats': stats
                    })
                except Exception as e:
                    echo_warning(f"Could not analyze {md_file}: {e}")
            
            # Generate consolidated report
            if format_type == "json":
                report_content = json.dumps({'summary': reports}, indent=2)
            elif format_type == "markdown":
                report_content = _generate_markdown_report(reports)
            else:  # text
                report_content = _generate_text_report(reports)
        
        else:
            echo_error(f"Error: {path} is not a valid file or directory")
            raise typer.Exit(1)
        
        # Output the report
        if output:
            output.write_text(report_content, encoding='utf-8')
            echo_success(f"Report saved to {output}")
        else:
            echo_if_not_quiet(report_content)
            
    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)


@report_app.command("toc")
def generate_toc(
    path: Path = typer.Argument(..., help="Path to markdown file"),
    max_level: int = typer.Option(3, "--max-level", "-l", help="Maximum heading level to include"),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output file for the table of contents"
    ),
) -> None:
    """Generate a table of contents from markdown headings.
    
    This command extracts headings from a markdown file and generates
    a formatted table of contents with anchor links.
    """
    if not path.exists():
        echo_error(f"File {path} does not exist")
        raise typer.Exit(1)
        
    if not path.name.endswith(('.md', '.markdown')):
        echo_error(f"File {path} does not appear to be a markdown file")
        raise typer.Exit(1)
    
    echo_info(f"Generating table of contents for: {path}")
    
    analyzer = MarkdownAnalyzer()
    
    try:
        content = path.read_text(encoding='utf-8')
        heading_analysis = analyzer.analyze_headings(content)
        toc_content = analyzer.generate_toc(heading_analysis['headings'], max_level)
        
        if output:
            output.write_text(toc_content, encoding='utf-8')
            echo_success(f"Table of contents saved to {output}")
        else:
            echo_if_not_quiet(toc_content)
            
    except Exception as e:
        echo_error(f"Error: {e}")
        raise typer.Exit(1)


def _generate_text_report(reports: list[dict[str, Any]]) -> str:
    """Generate a text format report from analysis data."""
    lines = []
    lines.append("=== Markdown Analysis Report ===\n")
    
    total_files = len(reports)
    total_headings = sum(r['heading_analysis']['heading_count'] for r in reports)
    total_words = sum(r['content_stats']['word_count'] for r in reports)
    total_links = sum(r['content_stats']['links'] for r in reports)
    total_images = sum(r['content_stats']['images'] for r in reports)
    
    lines.append(f"Total files analyzed: {total_files}")
    lines.append(f"Total headings: {total_headings}")
    lines.append(f"Total words: {total_words}")
    lines.append(f"Total links: {total_links}")
    lines.append(f"Total images: {total_images}")
    lines.append("")
    
    # Individual file details
    for report in reports:
        lines.append(f"File: {report['file']}")
        lines.append(f"  Headings: {report['heading_analysis']['heading_count']}")
        lines.append(f"  Words: {report['content_stats']['word_count']}")
        lines.append(f"  Links: {report['content_stats']['links']}")
        lines.append(f"  Images: {report['content_stats']['images']}")
        
        if report['heading_analysis']['hierarchy_issues']:
            lines.append("  Issues:")
            for issue in report['heading_analysis']['hierarchy_issues']:
                lines.append(f"    - {issue}")
        lines.append("")
    
    return '\n'.join(lines)


def _generate_markdown_report(reports: list[dict[str, Any]]) -> str:
    """Generate a markdown format report from analysis data."""
    lines = []
    lines.append("# Markdown Analysis Report\n")
    
    total_files = len(reports)
    total_headings = sum(r['heading_analysis']['heading_count'] for r in reports)
    total_words = sum(r['content_stats']['word_count'] for r in reports)
    total_links = sum(r['content_stats']['links'] for r in reports)
    total_images = sum(r['content_stats']['images'] for r in reports)
    
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total files analyzed:** {total_files}")
    lines.append(f"- **Total headings:** {total_headings}")
    lines.append(f"- **Total words:** {total_words}")
    lines.append(f"- **Total links:** {total_links}")
    lines.append(f"- **Total images:** {total_images}")
    lines.append("")
    
    lines.append("## File Details")
    lines.append("")
    
    # Individual file details
    for report in reports:
        lines.append(f"### {report['file']}")
        lines.append("")
        lines.append(f"- **Headings:** {report['heading_analysis']['heading_count']}")
        lines.append(f"- **Words:** {report['content_stats']['word_count']}")
        lines.append(f"- **Links:** {report['content_stats']['links']}")
        lines.append(f"- **Images:** {report['content_stats']['images']}")
        lines.append(f"- **Code blocks:** {report['content_stats']['code_blocks']}")
        lines.append(f"- **List items:** {report['content_stats']['bullet_list_items'] + report['content_stats']['numbered_list_items']}")
        
        if report['heading_analysis']['hierarchy_issues']:
            lines.append("")
            lines.append("**Issues:**")
            for issue in report['heading_analysis']['hierarchy_issues']:
                lines.append(f"- {issue}")
        lines.append("")
    
    return '\n'.join(lines)