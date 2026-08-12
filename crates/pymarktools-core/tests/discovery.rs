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

#[test]
fn applies_parent_and_nested_gitignore_rules() {
    let root = std::env::temp_dir().join(format!(
        "pymarktools-discovery-nested-{}",
        std::process::id()
    ));
    let docs = root.join("docs");
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(root.join(".git")).unwrap();
    fs::create_dir_all(&docs).unwrap();
    fs::write(root.join(".gitignore"), "from-parent.md\n").unwrap();
    fs::write(docs.join(".gitignore"), "from-nested.md\n").unwrap();
    fs::write(docs.join("from-parent.md"), "# skipped").unwrap();
    fs::write(docs.join("from-nested.md"), "# skipped").unwrap();
    fs::write(docs.join("keep.md"), "# kept").unwrap();

    let files = discover_markdown_files(&docs, "*.md", None, true).unwrap();

    assert_eq!(files, vec![docs.join("keep.md")]);
    fs::remove_dir_all(root).unwrap();
}
