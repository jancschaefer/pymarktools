//! PyO3 bindings for the pymarktools Rust core.

use pyo3::prelude::*;

/// Return the version of the compiled Rust core.
#[pyfunction]
fn core_version() -> &'static str {
    pymarktools_core::VERSION
}

/// Register pymarktools native bindings.
#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(core_version, module)?)
}
