//! Type-safe implementation shared by pymarktools entry points.

/// Version of the native core exposed through the Python extension.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
