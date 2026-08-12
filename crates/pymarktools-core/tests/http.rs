use pymarktools_core::http::classify_status;
use pymarktools_core::http::email_domain_url;

#[test]
fn classifies_permanent_and_temporary_redirects() {
    assert_eq!(classify_status(301), (true, true));
    assert_eq!(classify_status(302), (true, false));
    assert_eq!(classify_status(404), (false, false));
}

#[test]
fn creates_the_https_endpoint_used_for_email_domain_validation() {
    assert_eq!(email_domain_url("example.com"), "https://example.com");
}
