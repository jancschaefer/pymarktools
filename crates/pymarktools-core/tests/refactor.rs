use std::path::Path;
use std::{fs, process};

use pymarktools_core::refactor::move_and_rewrite;
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
fn moves_a_file_and_updates_markdown_references() {
    let root = std::env::temp_dir().join(format!("pymarktools-move-{}", process::id()));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(root.join("images")).unwrap();
    fs::write(root.join("images/logo.svg"), "svg").unwrap();
    fs::write(root.join("README.md"), "![logo](images/logo.svg)\n").unwrap();

    move_and_rewrite(
        &root.join("images/logo.svg"),
        &root.join("assets/logo.svg"),
        &root,
    )
    .unwrap();

    assert!(root.join("assets/logo.svg").is_file());
    assert_eq!(
        fs::read_to_string(root.join("README.md")).unwrap(),
        "![logo](assets/logo.svg)\n"
    );
    fs::remove_dir_all(root).unwrap();
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
