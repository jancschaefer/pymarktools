"""Configuration management for pymarktools.

This module handles loading configuration from pyproject.toml files.
"""

import tomllib
from pathlib import Path
from typing import Any

from .check_options import CheckOptions


def find_pyproject_toml(start_path: Path | None = None) -> Path | None:
    """Find pyproject.toml file by walking up the directory tree.
    
    Args:
        start_path: Directory to start searching from. Defaults to current directory.
        
    Returns:
        Path to pyproject.toml if found, None otherwise.
    """
    if start_path is None:
        start_path = Path.cwd()
    
    current = start_path.resolve()
    
    # Walk up the directory tree
    while current != current.parent:
        pyproject_path = current / "pyproject.toml"
        if pyproject_path.exists():
            return pyproject_path
        current = current.parent
    
    return None


def load_pyproject_config(pyproject_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from pyproject.toml.
    
    Args:
        pyproject_path: Path to pyproject.toml file. If None, searches for it.
        
    Returns:
        Configuration dictionary from [tool.pymarktools] section.
    """
    if pyproject_path is None:
        pyproject_path = find_pyproject_toml()
    
    if pyproject_path is None or not pyproject_path.exists():
        return {}
    
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        
        # Get the tool.pymarktools section
        tool_config = data.get("tool", {})
        return tool_config.get("pymarktools", {})
    
    except (tomllib.TOMLDecodeError, OSError):
        # If there's an error reading the file, return empty config
        return {}


def merge_check_options(
    base_options: CheckOptions,
    pyproject_config: dict[str, Any],
    cli_overrides: dict[str, Any],
) -> tuple[CheckOptions, list[Path]]:
    """Merge check options from different sources.
    
    Priority order (highest to lowest):
    1. CLI arguments (cli_overrides)
    2. pyproject.toml configuration (pyproject_config)
    3. Default options (base_options)
    
    Args:
        base_options: Base default options
        pyproject_config: Configuration from pyproject.toml
        cli_overrides: Explicit CLI argument overrides
        
    Returns:
        Tuple of (merged_options, paths_list)
    """
    # Start with base options
    merged_options = base_options.copy()
    
    # Extract paths from pyproject config
    paths = []
    if "paths" in pyproject_config:
        paths_config = pyproject_config["paths"]
        if isinstance(paths_config, list):
            paths = [Path(p) for p in paths_config]
        elif isinstance(paths_config, str):
            paths = [Path(paths_config)]
    
    # Apply pyproject.toml configuration
    for key, value in pyproject_config.items():
        if key == "paths":
            continue  # Handled separately
        
        # Convert string values to appropriate types
        if key in merged_options:
            if key == "output" and value:
                merged_options[key] = Path(value)
            elif key in ["workers"] and value is not None:
                merged_options[key] = int(value) if value is not None else None
            elif key in ["timeout"]:
                merged_options[key] = int(value)
            elif key in [
                "check_external", "check_local", "fix_redirects", 
                "follow_gitignore", "parallel", "fail",
                "check_dead_links", "check_dead_images"
            ]:
                merged_options[key] = bool(value)
            else:
                merged_options[key] = value
    
    # Apply CLI overrides (highest priority)
    for key, value in cli_overrides.items():
        if value is not None:  # Only override if explicitly set
            merged_options[key] = value
    
    return merged_options, paths