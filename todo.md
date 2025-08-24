# TODO: pymarktools Development Tasks

## Completed
1. ✅ Basic link validation functionality
2. ✅ Image validation functionality  
3. ✅ File refactoring with reference updates
4. ✅ Configuration via pyproject.toml
5. ✅ Async processing and parallel execution
6. ✅ CLI interface with global options and color output
7. ✅ **Format Command** - Add a `format` command to standardize markdown files
   - Fix common markdown formatting issues (spacing, indentation)
   - Standardize link and image reference formatting
   - Ensure consistent heading structure
8. ✅ **Report Command** - Add a `report` command to generate markdown analysis reports
   - Generate summary reports of link/image validation results
   - Create table of contents from headings
   - Analyze markdown structure and provide insights
9. ✅ **Convert Command** - Add a `convert` command for format transformation
   - Extract links and images to separate files/formats
   - Convert between different markdown flavors
   - Generate link inventories in various formats (JSON, CSV, etc.)

## In Progress / Planned

10. **Validate Command** - Add structural markdown validation
    - Check for proper heading hierarchy
    - Validate markdown syntax and structure
    - Check for common markdown issues

11. **Clean Command** - Add cleanup utilities
    - Remove unused images/files
    - Clean up broken reference patterns
    - Optimize markdown file structure

12. **Watch Command** - Add file watching capabilities
    - Monitor markdown files for changes
    - Automatic validation on file changes
    - Real-time feedback during editing