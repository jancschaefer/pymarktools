use pymarktools_core::http::classify_status;

#[test]
fn classifies_permanent_and_temporary_redirects() {
    assert_eq!(classify_status(301), (true, true));
    assert_eq!(classify_status(302), (true, false));
    assert_eq!(classify_status(404), (false, false));
}
