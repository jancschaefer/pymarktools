use std::path::Path;

use pymarktools_core::refactor::relative_reference;

#[test]
fn calculates_a_forward_slash_relative_reference() {
    assert_eq!(
        relative_reference(Path::new("docs/guides"), Path::new("assets/logo.svg")),
        "../../assets/logo.svg"
    );
}
