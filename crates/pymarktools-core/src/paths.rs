//! Local Markdown reference path handling.

use std::path::{Component, Path, PathBuf};

/// Resolve a local Markdown URL relative to the document containing it.
#[must_use]
pub fn resolve_local_path(url: &str, document_path: &Path) -> PathBuf {
    let clean_url = url.split('#').next().unwrap_or_default();
    let clean_url = clean_url.split('?').next().unwrap_or_default();
    let parent = document_path.parent().unwrap_or_else(|| Path::new(""));
    let candidate = if clean_url.starts_with('/') {
        parent.join(clean_url.trim_start_matches('/'))
    } else {
        parent.join(clean_url)
    };

    normalize_path(&candidate)
}

fn normalize_path(path: &Path) -> PathBuf {
    let mut normalized = PathBuf::new();

    for component in path.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                if !normalized.pop() {
                    normalized.push("..");
                }
            }
            _ => normalized.push(component.as_os_str()),
        }
    }

    normalized
}
