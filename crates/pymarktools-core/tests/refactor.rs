use std::path::Path;

use pymarktools_core::refactor::relative_reference;
use pymarktools_core::refactor::rewrite_reference;

#[test]
fn calculates_a_forward_slash_relative_reference() {
    assert_eq!(
        relative_reference(Path::new("docs/guides"), Path::new("assets/logo.svg")),
        "../../assets/logo.svg"
    );
}

#[test]
fn rewrites_the_target_of_a_markdown_image_without_changing_alt_text() {
    assert_eq!(
        rewrite_reference(
            "![logo](images/logo.svg)",
            "images/logo.svg",
            "assets/logo.svg"
        ),
        "![logo](assets/logo.svg)"
    );
}
