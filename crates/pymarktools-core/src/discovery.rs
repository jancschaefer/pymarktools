//! Gitignore-aware Markdown file discovery.

use std::path::{Path, PathBuf};

use globset::{Glob, GlobSet, GlobSetBuilder};
use ignore::WalkBuilder;
use ignore::gitignore::GitignoreBuilder;

/// Discover files beneath `root` matching the include and optional exclude patterns.
pub fn discover_markdown_files(
    root: &Path,
    include_pattern: &str,
    exclude_pattern: Option<&str>,
    follow_gitignore: bool,
) -> Result<Vec<PathBuf>, String> {
    let include = compile_glob(include_pattern)?;
    let exclude = exclude_pattern.map(compile_glob).transpose()?;
    let root_gitignore = build_root_gitignore(root, follow_gitignore)?;
    let mut builder = WalkBuilder::new(root);
    builder
        .git_ignore(follow_gitignore)
        .git_global(false)
        .git_exclude(false);

    let mut files = builder
        .build()
        .filter_map(Result::ok)
        .map(|entry| entry.into_path())
        .filter(|path| path.is_file())
        .filter(|path| {
            root_gitignore
                .as_ref()
                .is_none_or(|matcher| !matcher.matched_path_or_any_parents(path, false).is_ignore())
        })
        .filter(|path| include.is_match(path))
        .filter(|path| {
            exclude
                .as_ref()
                .is_none_or(|patterns| !patterns.is_match(path))
        })
        .collect::<Vec<_>>();
    files.sort();
    Ok(files)
}

fn build_root_gitignore(
    root: &Path,
    follow_gitignore: bool,
) -> Result<Option<ignore::gitignore::Gitignore>, String> {
    let gitignore_path = root.join(".gitignore");
    if !follow_gitignore || !gitignore_path.is_file() {
        return Ok(None);
    }

    let mut builder = GitignoreBuilder::new(root);
    builder.add(gitignore_path);
    builder.build().map(Some).map_err(|error| error.to_string())
}

fn compile_glob(pattern: &str) -> Result<GlobSet, String> {
    let mut builder = GlobSetBuilder::new();
    builder.add(Glob::new(pattern).map_err(|error| error.to_string())?);
    builder.build().map_err(|error| error.to_string())
}
