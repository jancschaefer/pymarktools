//! Reference path calculations used by Markdown refactoring.

use std::fs;
use std::path::{Component, Path, PathBuf};

use regex::Regex;

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

/// Move a file and update Markdown links and images that reference it.
pub fn move_and_rewrite(source: &Path, destination: &Path, base_dir: &Path) -> Result<(), String> {
    let source = source.canonicalize().map_err(|error| error.to_string())?;
    let files = crate::discovery::discover_markdown_files(base_dir, "*.md", None, false)?;
    let pattern = Regex::new(r"!?\[[^\]]*\]\(([^)]+)\)").map_err(|error| error.to_string())?;
    let mut changes = Vec::<(PathBuf, String)>::new();
    for file in files {
        let content = fs::read_to_string(&file).map_err(|error| error.to_string())?;
        let replacement = relative_reference(file.parent().unwrap_or(base_dir), destination);
        let updated = pattern
            .replace_all(&content, |captures: &regex::Captures<'_>| {
                let target = &captures[1];
                if target.starts_with("http://") || target.starts_with("https://") {
                    return captures[0].to_owned();
                }
                let resolved = file
                    .parent()
                    .unwrap_or(base_dir)
                    .join(target)
                    .canonicalize();
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
    if let Some(parent) = destination.parent() {
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    }
    fs::rename(&source, destination).map_err(|error| error.to_string())?;
    for (file, content) in changes {
        fs::write(file, content).map_err(|error| error.to_string())?;
    }
    Ok(())
}

fn components(path: &Path) -> Vec<String> {
    path.components()
        .filter_map(|component| match component {
            Component::Normal(value) => Some(value.to_string_lossy().into_owned()),
            _ => None,
        })
        .collect()
}
