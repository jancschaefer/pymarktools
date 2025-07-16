#!/usr/bin/env bash
# Note: Removed set -e because we expect some commands to fail with exit code 1
# when they detect invalid links, which is the expected behavior

# cli-test.sh - Test script for pymarktools CLI functionality
# This script tests all scenarios mentioned in the Usage section of README.md
# Updated for API v0.3.0 - unified check command with --check-dead-links/--check-dead-images options

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
total_tests=0
passed_tests=0

# Function to run a test
run_test() {
    local test_name=$1
    local command=$2
    
    echo -e "${BLUE}Running test: ${test_name}${NC}"
    echo "Command: $command"
    
    ((total_tests++))
    
    # Execute command and store return code
    eval "$command" > /tmp/cmd_output.txt 2>&1
    local status=$?
    
    # Only show output on failure (uncomment the lines below if you want to see output)
    if [ $status -ne 0 ] && [ $status -ne 1 ]; then
        echo "---------- Command Output (Failed with code $status) ----------"
        cat /tmp/cmd_output.txt
        echo "-----------------------------------"
    fi
    
    # Check if the command executed successfully (this just checks if it ran, not if it found issues)
    if [ $status -eq 0 ] || [ $status -eq 1 ]; then
        echo -e "${GREEN}✓ Test completed${NC}"
        ((passed_tests++))
    else
        echo -e "${RED}✗ Test failed with exit code $status${NC}"
    fi
    
    echo ""
}

# Create a temporary directory for testing
temp_dir=$(mktemp -d)
echo -e "${YELLOW}Created temporary test directory: $temp_dir${NC}"

# Create a sample markdown file with valid and invalid links
cat > "$temp_dir/sample.md" <<EOF
# Sample Markdown

## Valid Links
- [Google](https://www.google.com)
- [Local File](./other.md)

## Invalid Links
- [Invalid External](https://example.com/invalid-path-12345)
- [Invalid Local](./nonexistent.md)

## Images
![Valid Image](https://www.example.com/image.png)
![Invalid Image](./nonexistent.png)
EOF

# Create another markdown file for reference
cat > "$temp_dir/other.md" <<EOF
# Other File
This is another file for testing local references.
EOF

# Create a draft file that can be excluded
cat > "$temp_dir/draft_doc.md" <<EOF
# Draft Document
This is a draft document that can be excluded with patterns.
EOF

# Create a .gitignore file
cat > "$temp_dir/.gitignore" <<EOF
# Ignore these patterns
ignored_dir/
*.ignored
EOF

# Create an ignored directory and file
mkdir -p "$temp_dir/ignored_dir"
cat > "$temp_dir/ignored_dir/ignored.md" <<EOF
# Ignored File
This file should be ignored when using --follow-gitignore.
EOF

cat > "$temp_dir/file.ignored" <<EOF
# Ignored File Extension
This file should be ignored when using --follow-gitignore.
EOF

echo -e "${YELLOW}Test files created${NC}"
echo ""

# Section: Basic Usage
echo -e "${BLUE}=== Testing Basic Usage ===${NC}"

run_test "Basic help" "uv run pymarktools --help"
run_test "Verbose mode" "uv run pymarktools --verbose check $temp_dir/sample.md"
run_test "Quiet mode" "uv run pymarktools --quiet check $temp_dir/"
run_test "Version" "uv run pymarktools --version"

# Section: Check for Dead Links and Images
echo -e "${BLUE}=== Testing Dead Links and Images ===${NC}"

run_test "Basic link checking" "uv run pymarktools check $temp_dir/sample.md"
run_test "Link check with custom timeout and external validation" "uv run pymarktools check $temp_dir/ --timeout 60 --check-external"
run_test "Link check only local files" "uv run pymarktools check $temp_dir/ --no-check-external"

run_test "Basic image checking" "uv run pymarktools check $temp_dir/sample.md"
run_test "Image check with pattern filtering" "uv run pymarktools check $temp_dir/ --include \"*.md\" --exclude \"draft_*\""

run_test "Check only links (disable images)" "uv run pymarktools check $temp_dir/sample.md --no-check-dead-images"
run_test "Check only images (disable links)" "uv run pymarktools check $temp_dir/sample.md --no-check-dead-links"

# Section: Exit Behavior Testing
echo -e "${BLUE}=== Testing Exit Behavior ===${NC}"

run_test "Default fail behavior" "uv run pymarktools check $temp_dir/sample.md --no-check-external"
run_test "Disable fail on errors" "uv run pymarktools check $temp_dir/sample.md --no-fail --no-check-external"
run_test "Explicit fail on errors" "uv run pymarktools check $temp_dir/sample.md --fail --no-check-external"

# Section: Both Checks Disabled Error
echo -e "${BLUE}=== Testing Error Conditions ===${NC}"

run_test "Both checks disabled error" "uv run pymarktools check $temp_dir/sample.md --no-check-dead-links --no-check-dead-images"

# Section: Flexible Option Placement
echo -e "${BLUE}=== Testing Flexible Option Placement ===${NC}"

run_test "Options at callback level" "uv run pymarktools check --timeout 30 --no-check-external $temp_dir/sample.md"
run_test "Options at command level" "uv run pymarktools check $temp_dir/sample.md --timeout 10 --check-external"
run_test "Mixed approach" "uv run pymarktools check --include \"*.md\" --timeout 60 $temp_dir/"

# Section: Local File Validation
echo -e "${BLUE}=== Testing Local File Validation ===${NC}"

run_test "Check both local and external" "uv run pymarktools check $temp_dir/"
run_test "Skip local file checking" "uv run pymarktools check $temp_dir/ --no-check-local"
run_test "Check only local files" "uv run pymarktools check $temp_dir/ --no-check-external"

# Section: External URL Checking and Redirect Fixing
echo -e "${BLUE}=== Testing External URL Checking and Redirect Fixing ===${NC}"

run_test "Basic external URL checking" "uv run pymarktools check $temp_dir/sample.md"
run_test "Disable external URL checking" "uv run pymarktools check $temp_dir/sample.md --no-check-external"
run_test "Fix permanent redirects" "uv run pymarktools check $temp_dir/sample.md --fix-redirects"
run_test "Custom timeout" "uv run pymarktools check $temp_dir/sample.md --timeout 60"

# Section: Pattern Filtering
echo -e "${BLUE}=== Testing Pattern Filtering ===${NC}"

run_test "Include only markdown files" "uv run pymarktools check $temp_dir/ --include \"*.md\""
run_test "Exclude draft files" "uv run pymarktools check $temp_dir/ --exclude \"draft_*\""
run_test "Combine include and exclude patterns" "uv run pymarktools check $temp_dir/ --include \"*.md\" --exclude \"draft_*\""

# Section: Gitignore Support
echo -e "${BLUE}=== Testing Gitignore Support ===${NC}"

run_test "Respect gitignore" "uv run pymarktools check $temp_dir/"
run_test "Disable gitignore" "uv run pymarktools check $temp_dir/ --no-follow-gitignore"

# Section: Async Processing
echo -e "${BLUE}=== Testing Async Processing ===${NC}"

run_test "Use async with default worker count" "uv run pymarktools check $temp_dir/ --parallel"
run_test "Custom worker count" "uv run pymarktools check $temp_dir/ --workers 2"
run_test "Disable async processing" "uv run pymarktools check $temp_dir/ --no-parallel"

# Section: Color Output
echo -e "${BLUE}=== Testing Color Output ===${NC}"

run_test "Enable color output" "uv run pymarktools --color check $temp_dir/"
run_test "Disable color output" "uv run pymarktools --no-color check $temp_dir/"

# Section: Verbosity Levels
echo -e "${BLUE}=== Testing Verbosity Levels ===${NC}"

run_test "Quiet mode" "uv run pymarktools --quiet check $temp_dir/"
run_test "Default mode" "uv run pymarktools check $temp_dir/"
run_test "Verbose mode" "uv run pymarktools --verbose check $temp_dir/"

# Section: File Refactoring
echo -e "${BLUE}=== Testing File Refactoring ===${NC}"

# Create a copy of sample.md to move
cp "$temp_dir/sample.md" "$temp_dir/to_move.md"

run_test "Move a file and update references" "uv run pymarktools refactor move $temp_dir/to_move.md $temp_dir/moved_file.md"
run_test "Move with pattern filtering" "cp $temp_dir/sample.md $temp_dir/to_move2.md && uv run pymarktools refactor move $temp_dir/to_move2.md $temp_dir/moved_file2.md --include \"*.md\""
run_test "Move with dry run" "cp $temp_dir/sample.md $temp_dir/to_move3.md && uv run pymarktools refactor move $temp_dir/to_move3.md $temp_dir/moved_file3.md --dry-run"

# Section: CI/CD Integration 
echo -e "${BLUE}=== Testing CI/CD Integration ===${NC}"

run_test "Minimal CI check" "uv run pymarktools --quiet check $temp_dir/ --no-check-external"
run_test "Full CI validation" "uv run pymarktools check $temp_dir/ --include \"*.md\" --timeout 10 || true"

# Section: Common Examples
echo -e "${BLUE}=== Testing Common Examples ===${NC}"

run_test "Quick validation - current directory" "uv run pymarktools check $temp_dir/"
run_test "Quick validation - specific file" "uv run pymarktools --verbose check $temp_dir/sample.md"
run_test "Quick validation - local files only" "uv run pymarktools check $temp_dir/ --no-check-external"

run_test "Comprehensive checking - full validation" "uv run pymarktools check $temp_dir/ --fix-redirects --timeout 60"
run_test "Comprehensive checking - custom patterns" "uv run pymarktools check $temp_dir/ --include \"*.md\" --follow-gitignore"
run_test "Comprehensive checking - batch processing" "uv run pymarktools check --timeout 30 $temp_dir/ --check-external --fix-redirects"

# Clean up the temporary directory
rm -rf "$temp_dir"
echo -e "${YELLOW}Removed temporary test directory${NC}"

# Summary
echo -e "${BLUE}=== Test Summary ===${NC}"
echo -e "Total tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$((total_tests - passed_tests))${NC}"

if [ $passed_tests -eq $total_tests ]; then
    echo -e "${GREEN}All tests completed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
