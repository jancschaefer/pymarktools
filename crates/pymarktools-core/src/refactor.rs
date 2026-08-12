//! Reference path calculations used by Markdown refactoring.

use std::fs;
use std::path::{Component, Path, PathBuf};

use regex::Regex;

/// A Markdown reference to a file discovered during refactoring.
#[derive(Debug, Eq, PartialEq)]
pub struct FileReference {
    /// Markdown file containing the reference.
    pub file_path: PathBuf,
    /// One-based source line number.
    pub line_number: usize,
    /// Complete Markdown reference text.
    pub reference_text: String,
    /// Either `link` or `image`.
    pub reference_type: String,
    /// The original target text inside the Markdown reference.
    pub target_path: String,
}

/// Calculate a forward-slash relative reference from one directory to a file.
#[must_use]
pub fn relative_reference(from_dir: &Path, to_file: &Path) -> String {
    let from = components(from_dir);
    let to = components(to_file);
    let common = from
        .iter()
        .zip(&to)
        .take_while(|(left, right)| left == right)
        .count();
    let mut parts = vec!["..".to_owned(); from.len().saturating_sub(common)];
    parts.extend(to.into_iter().skip(common));
    if parts.is_empty() {
        ".".to_owned()
    } else {
        parts.join("/")
    }
}

/// Replace one target path inside a Markdown link or image reference.
#[must_use]
pub fn rewrite_reference(reference: &str, old_target: &str, new_target: &str) -> String {
    reference.replacen(&format!("({old_target})"), &format!("({new_target})"), 1)
}

/// Find Markdown links and images that resolve to `target_file`.
pub fn find_references(
    target_file: &Path,
    base_dir: &Path,
    include_pattern: &str,
    exclude_pattern: Option<&str>,
) -> Result<Vec<FileReference>, String> {
    let target = target_file
        .canonicalize()
        .map_err(|error| error.to_string())?;
    let files = crate::discovery::discover_markdown_files(
        base_dir,
        include_pattern,
        exclude_pattern,
        false,
    )?;
    let pattern = Regex::new(r"(!?)\[[^\]]*\]\(([^)]+)\)").map_err(|error| error.to_string())?;
    let mut references = Vec::new();

    for file_path in files {
        let content = fs::read_to_string(&file_path).map_err(|error| error.to_string())?;
        for (line_index, line) in content.lines().enumerate() {
            for captures in pattern.captures_iter(line) {
                let target_path = captures[2].to_owned();
                if target_path.starts_with("http://") || target_path.starts_with("https://") {
                    continue;
                }
                let candidate = resolve_reference_target(&target_path, &file_path, base_dir);
                if candidate
                    .canonicalize()
                    .as_ref()
                    .is_ok_and(|path| path == &target)
                {
                    references.push(FileReference {
                        file_path: file_path.clone(),
                        line_number: line_index + 1,
                        reference_text: captures[0].to_owned(),
                        reference_type: if captures[1].is_empty() {
                            "link".to_owned()
                        } else {
                            "image".to_owned()
                        },
                        target_path,
                    });
                }
            }
        }
    }

    Ok(references)
}

/// Move a file and update Markdown links and images that reference it.
pub fn move_and_rewrite(
    source: &Path,
    destination: &Path,
    base_dir: &Path,
    include_pattern: &str,
    exclude_pattern: Option<&str>,
    selected_files: Option<&[PathBuf]>,
) -> Result<(), String> {
    let source = source.canonicalize().map_err(|error| error.to_string())?;
    let base_dir = base_dir.canonicalize().map_err(|error| error.to_string())?;
    let destination_parent = destination
        .parent()
        .filter(|path| !path.as_os_str().is_empty())
        .unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(destination_parent).map_err(|error| error.to_string())?;
    let destination_name = destination
        .file_name()
        .ok_or_else(|| "destination must name a file".to_owned())?;
    let destination = destination_parent
        .canonicalize()
        .map_err(|error| error.to_string())?
        .join(destination_name);
    let files = match selected_files {
        Some(files) => files
            .iter()
            .map(|path| path.canonicalize().map_err(|error| error.to_string()))
            .collect::<Result<Vec<_>, _>>()?,
        None => crate::discovery::discover_markdown_files(
            &base_dir,
            include_pattern,
            exclude_pattern,
            false,
        )?,
    };
    let pattern = Regex::new(r"!?\[[^\]]*\]\(([^)]+)\)").map_err(|error| error.to_string())?;
    let mut changes = Vec::<(PathBuf, String)>::new();
    for file in files {
        let content = fs::read_to_string(&file).map_err(|error| error.to_string())?;
        let replacement = relative_reference(file.parent().unwrap_or(&base_dir), &destination);
        let updated = pattern
            .replace_all(&content, |captures: &regex::Captures<'_>| {
                let target = &captures[1];
                if target.starts_with("http://") || target.starts_with("https://") {
                    return captures[0].to_owned();
                }
                let resolved = resolve_reference_target(target, &file, &base_dir).canonicalize();
                if resolved.as_ref().is_ok_and(|path| path == &source) {
                    rewrite_reference(&captures[0], target, &replacement)
                } else {
                    captures[0].to_owned()
                }
            })
            .into_owned();
        if updated != content {
            changes.push((file, updated));
        }
    }
    fs::rename(&source, destination).map_err(|error| error.to_string())?;
    for (file, content) in changes {
        fs::write(file, content).map_err(|error| error.to_string())?;
    }
    Ok(())
}

fn resolve_reference_target(target: &str, source_file: &Path, base_dir: &Path) -> PathBuf {
    if target.starts_with('/') {
        base_dir.join(target.trim_start_matches('/'))
    } else {
        source_file.parent().unwrap_or(base_dir).join(target)
    }
}

fn components(path: &Path) -> Vec<String> {
    path.components()
        .filter_map(|component| match component {
            Component::Normal(value) => Some(value.to_string_lossy().into_owned()),
            _ => None,
        })
        .collect()
}
