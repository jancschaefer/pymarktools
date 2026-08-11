//! Markdown reference extraction compatible with the existing public API.

use std::sync::LazyLock;

use regex::Regex;

use crate::model::{ImageInfo, LinkInfo};

static LINK_PATTERN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"\[([^\]]*)\]\(([^)]+)\)").expect("valid link pattern"));
static IMAGE_PATTERN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"!\[([^\]]*)\]\(([^)]+)\)").expect("valid image pattern"));

/// Extract links from Markdown content, excluding image references.
#[must_use]
pub fn extract_links(content: &str) -> Vec<LinkInfo> {
    content
        .lines()
        .enumerate()
        .flat_map(|(index, line)| {
            LINK_PATTERN
                .captures_iter(line)
                .filter_map(move |captures| {
                    let full_match = captures.get(0)?;
                    let is_image =
                        full_match.start() > 0 && line.as_bytes()[full_match.start() - 1] == b'!';
                    (!is_image).then(|| LinkInfo {
                        text: captures[1].to_owned(),
                        url: captures[2].to_owned(),
                        line_number: index + 1,
                        ..LinkInfo::default()
                    })
                })
        })
        .collect()
}

/// Extract image references from Markdown content.
#[must_use]
pub fn extract_images(content: &str) -> Vec<ImageInfo> {
    content
        .lines()
        .enumerate()
        .flat_map(|(index, line)| {
            IMAGE_PATTERN
                .captures_iter(line)
                .map(move |captures| ImageInfo {
                    alt_text: captures[1].to_owned(),
                    url: captures[2].to_owned(),
                    line_number: index + 1,
                    ..ImageInfo::default()
                })
        })
        .collect()
}
