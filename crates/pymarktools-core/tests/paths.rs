use std::path::{Path, PathBuf};

use pymarktools_core::paths::resolve_local_path;

#[test]
fn removes_fragment_and_query_before_resolving_relative_paths() {
    let document = Path::new("fixtures/docs/README.md");

    assert_eq!(
        resolve_local_path("../guide.md#install?unused", document),
        PathBuf::from("fixtures/guide.md")
    );
}

#[test]
fn preserves_leading_parent_components_for_relative_document_paths() {
    assert_eq!(
        resolve_local_path("../outside.md", Path::new("README.md")),
        PathBuf::from("../outside.md")
    );
}
