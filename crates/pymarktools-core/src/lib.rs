//! Type-safe implementation shared by pymarktools entry points.

pub mod markdown;
pub mod model;

/// Version of the native core exposed through the Python extension.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
