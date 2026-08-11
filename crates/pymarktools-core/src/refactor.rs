//! Reference path calculations used by Markdown refactoring.

use std::path::{Component, Path};

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

fn components(path: &Path) -> Vec<String> {
    path.components()
        .filter_map(|component| match component {
            Component::Normal(value) => Some(value.to_string_lossy().into_owned()),
            _ => None,
        })
        .collect()
}
