//! Typed values produced by Markdown validation.

/// Information about a Markdown link.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct LinkInfo {
    pub text: String,
    pub url: String,
    pub line_number: usize,
    pub is_valid: Option<bool>,
    pub status_code: Option<u16>,
    pub error: Option<String>,
    pub redirect_url: Option<String>,
    pub is_permanent_redirect: Option<bool>,
    pub updated: bool,
    pub is_local: Option<bool>,
    pub local_path: Option<String>,
}

/// Information about a Markdown image.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct ImageInfo {
    pub alt_text: String,
    pub url: String,
    pub line_number: usize,
    pub is_valid: Option<bool>,
    pub status_code: Option<u16>,
    pub error: Option<String>,
    pub redirect_url: Option<String>,
    pub is_permanent_redirect: Option<bool>,
    pub updated: bool,
    pub is_local: Option<bool>,
    pub local_path: Option<String>,
}
