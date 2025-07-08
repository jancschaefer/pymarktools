# Release Process for pymarktools

![](https://badgen.net/github/license/jancschaefer/pymarktools)
![](https://badgen.net/github/tag/jancschaefer/pymarktools)
![](https://badgen.net/github/release/jancschaefer/pymarktools)
![](https://badgen.net/github/checks/jancschaefer/pymarktools/main)

This document outlines the release process for the pymarktools package.

## Overview

The pymarktools project uses automated releases through GitHub Actions with PyPI's trusted publisher (OIDC) authentication. This means no manual API tokens are required - releases are fully automated and secure.

## Prerequisites

- [ ] All tests are passing on the main branch
- [ ] Version number has been updated in `pyproject.toml`
- [ ] CHANGELOG or release notes are prepared
- [ ] All intended changes are merged to the main branch

## Release Types

### 1. Development/Pre-release (TestPyPI)

TestPyPI releases happen automatically on every push to any branch for testing purposes.

**Process:**

1. Push changes to any branch
1. GitHub Actions automatically builds and publishes to TestPyPI
1. Test the package from TestPyPI: `pip install -i https://test.pypi.org/simple/pymarktools`

### 2. Production Release (PyPI)

Production releases to PyPI happen when you create a GitHub release.

## Step-by-Step Release Process

### Step 1: Prepare the Release


1. **Update the changelog** in `CHANGELOG.md`:

    - Add a new section for the release version and date
    - Summarize all user-facing changes, fixes, and improvements

1. **Update the version** in `pyproject.toml`:

    ```toml
    [project]
    name = "pymarktools"
    version = "0.2.0"  # Update this
    ```

1. **Update documentation** if needed (README.md, CHANGELOG.md, etc.)

1. **Commit and push** changes:

    ```bash
    git add pyproject.toml
    git commit -m "chore: bump version to 0.2.0"
    git push origin main
    ```

1. **Wait for CI** to pass on the main branch

### Step 2: Create and Push a Git Tag

```bash
# Create a tag (must match the version in pyproject.toml)
git tag v0.2.0

# Push the tag to trigger the release workflow
git push origin v0.2.0
```

### Step 3: Create a GitHub Release

1. Go to [GitHub Releases](https://github.com/jancschaefer/pymarktools/releases)
1. Click "Create a new release"
1. Select the tag you just created (`v0.2.0`)
1. Fill in the release title and description
1. Click "Publish release"

### Step 4: Automated Process

Once you publish the GitHub release, the following happens automatically:

1. ✅ **Build Process**: GitHub Actions builds the package
1. 🧪 **TestPyPI**: Package is published to TestPyPI for testing
1. 🚀 **PyPI**: Package is published to PyPI (production)
1. 🔐 **Signing**: Package artifacts are signed with Sigstore
1. 📋 **GitHub Release**: Signed artifacts are uploaded to the GitHub release

## Workflow Details

### Automatic Triggers

| Event                    | TestPyPI | PyPI | GitHub Release |
| ------------------------ | -------- | ---- | -------------- |
| Push to any branch       | ❌       | ❌   | ❌             |
| Create GitHub release    | ✅       | ✅   | ✅             |
| Manual workflow dispatch | ✅       | ❌   | ❌             |

PyPI publishing only happens for tagged releases

### Environments

The project uses two PyPI environments:

- **pypi**: Production PyPI with OIDC trusted publisher
- **testpypi**: Test PyPI for pre-release testing

Both are configured with OIDC authentication, so no manual token management is required.

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.0.0)
- **Pre-release**: Use suffixes like `a1`, `b1`, `rc1` (e.g., 1.0.0a1)

Examples:

- `0.1.0` - Initial release
- `0.2.0` - Patch release (bug fixes)
- `0.2.0` - Minor release (new features, backward compatible)
- `1.0.0` - Major release (breaking changes)
- `1.0.0a1` - Alpha pre-release

## Testing Releases

### Testing from TestPyPI

```bash
# Install from TestPyPI
pip install -i https://test.pypi.org/simple/ pymarktools

# Test basic functionality
pymarktools --help
pymarktools check dead-links README.md
```

### Testing from PyPI

```bash
# Install from PyPI
pip install pymarktools

# Verify version
pymarktools --version
```

## Rollback Process

If a release needs to be rolled back:

1. **Immediate action**: Yank the problematic release on PyPI

    - Go to [PyPI project page](https://pypi.org/project/pymarktools/)
    - Select the problematic version
    - Click "Options" → "Yank release"

1. **Fix and re-release**:

    - Fix the issue in code
    - Bump the version (e.g., 0.2.0 → 0.2.1) in `pyproject.toml` and `src/pymarktools/__init__.py`
    - Follow the normal release process

## Troubleshooting

### Common Issues

1. **"Permission denied" on PyPI**

    - Verify OIDC trusted publisher is correctly configured
    - Check that workflow name matches: `publish.yml`
    - Verify environment name matches: `pypi`

1. **Build failures**

    - Check that all tests pass locally: `uv run pytest`
    - Verify dependencies are correctly specified in `pyproject.toml`
    - Run local build test: `uv tool run build`

1. **Version conflicts**

    - Ensure version in `pyproject.toml` matches the git tag
    - Check that the version doesn't already exist on PyPI

### Getting Help

- Check the [GitHub Actions logs](https://github.com/jancschaefer/pymarktools/actions)
- Review [PyPI trusted publisher documentation](https://docs.pypi.org/trusted-publishers/)
- Open an issue in the repository for release-related problems

## Security

- All packages are automatically signed with [Sigstore](https://www.sigstore.dev/)
- OIDC authentication eliminates the need for long-lived API tokens
- Artifacts are uploaded to GitHub releases for transparency
- All release actions are logged and auditable

## Checklist Template

Use this checklist for each release:

- [ ] Version updated in `pyproject.toml`
- [ ] All tests passing on main branch
- [ ] Changes documented (CHANGELOG.md, release notes)
- [ ] Git tag created and pushed
- [ ] GitHub release created
- [ ] Automated workflows completed successfully
- [ ] Package available on PyPI
- [ ] Installation and basic functionality tested

---

For questions about the release process, please open an issue or contact the maintainers.
