//! HTTP status semantics shared by native validators.

use std::time::Duration;

/// Detailed result of validating one URL.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct HttpResult {
    pub is_valid: bool,
    pub status_code: Option<u16>,
    pub error: Option<String>,
    pub redirect_url: Option<String>,
    pub is_permanent_redirect: bool,
}

/// Return `(is_valid, is_permanent_redirect)` for an HTTP response status.
#[must_use]
pub fn classify_status(status: u16) -> (bool, bool) {
    let permanent_redirect = matches!(status, 301 | 307 | 308);
    let valid = (200..300).contains(&status) || permanent_redirect || status == 302;
    (valid, permanent_redirect)
}

/// Validate a URL with a HEAD request without automatically following redirects.
#[must_use]
pub fn check_url(url: &str, timeout_seconds: u64) -> HttpResult {
    let client = match reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(timeout_seconds))
        .redirect(reqwest::redirect::Policy::none())
        .build()
    {
        Ok(client) => client,
        Err(error) => return failed(error.to_string()),
    };
    match client.head(url).send() {
        Ok(response) => {
            let status = response.status().as_u16();
            let (is_valid, is_permanent_redirect) = classify_status(status);
            HttpResult {
                is_valid,
                status_code: Some(status),
                error: None,
                redirect_url: response
                    .headers()
                    .get(reqwest::header::LOCATION)
                    .and_then(|value| value.to_str().ok())
                    .map(str::to_owned),
                is_permanent_redirect,
            }
        }
        Err(error) => failed(error.to_string()),
    }
}

fn failed(error: String) -> HttpResult {
    HttpResult {
        is_valid: false,
        status_code: None,
        error: Some(error),
        redirect_url: None,
        is_permanent_redirect: false,
    }
}
