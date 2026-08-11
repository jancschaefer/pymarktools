use std::fs;

use pymarktools_core::discovery::discover_markdown_files;

#[test]
fn skips_gitignored_roots() {
    let root = std::env::temp_dir().join(format!("pymarktools-discovery-{}", std::process::id()));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(root.join("generated")).unwrap();
    fs::write(root.join(".gitignore"), "generated/\n").unwrap();
    fs::write(root.join("generated/skip.md"), "# skipped").unwrap();
    fs::write(root.join("keep.md"), "# kept").unwrap();

    let files = discover_markdown_files(&root, "*.md", None, true).unwrap();

    assert_eq!(files, vec![root.join("keep.md")]);
    fs::remove_dir_all(root).unwrap();
}
