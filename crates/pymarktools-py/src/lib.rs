//! PyO3 bindings for the pymarktools Rust core.

use pymarktools_core::markdown::{
    extract_images as extract_core_images, extract_links as extract_core_links,
};
use pymarktools_core::model::{ImageInfo, LinkInfo};
use pyo3::prelude::*;

/// Python-visible information about a Markdown link.
#[pyclass(name = "LinkInfo", module = "pymarktools._native")]
#[derive(Clone)]
struct PyLinkInfo {
    #[pyo3(get, set)]
    text: String,
    #[pyo3(get, set)]
    url: String,
    #[pyo3(get, set)]
    line_number: usize,
    #[pyo3(get, set)]
    is_valid: Option<bool>,
    #[pyo3(get, set)]
    status_code: Option<u16>,
    #[pyo3(get, set)]
    error: Option<String>,
    #[pyo3(get, set)]
    redirect_url: Option<String>,
    #[pyo3(get, set)]
    is_permanent_redirect: Option<bool>,
    #[pyo3(get, set)]
    updated: bool,
    #[pyo3(get, set)]
    is_local: Option<bool>,
    #[pyo3(get, set)]
    local_path: Option<String>,
}

impl From<LinkInfo> for PyLinkInfo {
    fn from(value: LinkInfo) -> Self {
        Self {
            text: value.text,
            url: value.url,
            line_number: value.line_number,
            is_valid: value.is_valid,
            status_code: value.status_code,
            error: value.error,
            redirect_url: value.redirect_url,
            is_permanent_redirect: value.is_permanent_redirect,
            updated: value.updated,
            is_local: value.is_local,
            local_path: value.local_path,
        }
    }
}

#[pymethods]
impl PyLinkInfo {
    #[new]
    #[pyo3(signature = (text, url, line_number, is_valid=None, status_code=None, error=None, redirect_url=None, is_permanent_redirect=None, updated=false, is_local=None, local_path=None))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        text: String,
        url: String,
        line_number: usize,
        is_valid: Option<bool>,
        status_code: Option<u16>,
        error: Option<String>,
        redirect_url: Option<String>,
        is_permanent_redirect: Option<bool>,
        updated: bool,
        is_local: Option<bool>,
        local_path: Option<String>,
    ) -> Self {
        Self {
            text,
            url,
            line_number,
            is_valid,
            status_code,
            error,
            redirect_url,
            is_permanent_redirect,
            updated,
            is_local,
            local_path,
        }
    }
}

/// Python-visible information about a Markdown image.
#[pyclass(name = "ImageInfo", module = "pymarktools._native")]
#[derive(Clone)]
struct PyImageInfo {
    #[pyo3(get, set)]
    alt_text: String,
    #[pyo3(get, set)]
    url: String,
    #[pyo3(get, set)]
    line_number: usize,
    #[pyo3(get, set)]
    is_valid: Option<bool>,
    #[pyo3(get, set)]
    status_code: Option<u16>,
    #[pyo3(get, set)]
    error: Option<String>,
    #[pyo3(get, set)]
    redirect_url: Option<String>,
    #[pyo3(get, set)]
    is_permanent_redirect: Option<bool>,
    #[pyo3(get, set)]
    updated: bool,
    #[pyo3(get, set)]
    is_local: Option<bool>,
    #[pyo3(get, set)]
    local_path: Option<String>,
}

impl From<ImageInfo> for PyImageInfo {
    fn from(value: ImageInfo) -> Self {
        Self {
            alt_text: value.alt_text,
            url: value.url,
            line_number: value.line_number,
            is_valid: value.is_valid,
            status_code: value.status_code,
            error: value.error,
            redirect_url: value.redirect_url,
            is_permanent_redirect: value.is_permanent_redirect,
            updated: value.updated,
            is_local: value.is_local,
            local_path: value.local_path,
        }
    }
}

#[pymethods]
impl PyImageInfo {
    #[new]
    #[pyo3(signature = (alt_text, url, line_number, is_valid=None, status_code=None, error=None, redirect_url=None, is_permanent_redirect=None, updated=false, is_local=None, local_path=None))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        alt_text: String,
        url: String,
        line_number: usize,
        is_valid: Option<bool>,
        status_code: Option<u16>,
        error: Option<String>,
        redirect_url: Option<String>,
        is_permanent_redirect: Option<bool>,
        updated: bool,
        is_local: Option<bool>,
        local_path: Option<String>,
    ) -> Self {
        Self {
            alt_text,
            url,
            line_number,
            is_valid,
            status_code,
            error,
            redirect_url,
            is_permanent_redirect,
            updated,
            is_local,
            local_path,
        }
    }
}

/// Return the version of the compiled Rust core.
#[pyfunction]
fn core_version() -> &'static str {
    pymarktools_core::VERSION
}

/// Extract non-image Markdown links.
#[pyfunction(name = "extract_links")]
fn extract_links_py(content: &str) -> Vec<PyLinkInfo> {
    extract_core_links(content)
        .into_iter()
        .map(PyLinkInfo::from)
        .collect()
}

/// Extract Markdown image references.
#[pyfunction(name = "extract_images")]
fn extract_images_py(content: &str) -> Vec<PyImageInfo> {
    extract_core_images(content)
        .into_iter()
        .map(PyImageInfo::from)
        .collect()
}

/// Register pymarktools native bindings.
#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyLinkInfo>()?;
    module.add_class::<PyImageInfo>()?;
    module.add_function(wrap_pyfunction!(core_version, module)?)?;
    module.add_function(wrap_pyfunction!(extract_links_py, module)?)?;
    module.add_function(wrap_pyfunction!(extract_images_py, module)?)
}
