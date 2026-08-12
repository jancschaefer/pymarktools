use pymarktools_core::markdown::{extract_images, extract_links};

#[test]
fn extracts_links_but_not_images_with_one_based_line_numbers() {
    let links = extract_links("![logo](logo.svg)\n[guide](docs/guide.md)");

    assert_eq!(links.len(), 1);
    assert_eq!(links[0].text, "guide");
    assert_eq!(links[0].url, "docs/guide.md");
    assert_eq!(links[0].line_number, 2);
}

#[test]
fn extracts_images_with_alt_text_and_line_numbers() {
    let images = extract_images("before\n![logo](assets/logo.svg)");

    assert_eq!(images.len(), 1);
    assert_eq!(images[0].alt_text, "logo");
    assert_eq!(images[0].url, "assets/logo.svg");
    assert_eq!(images[0].line_number, 2);
}
