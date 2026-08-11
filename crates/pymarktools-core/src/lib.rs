//! Type-safe implementation shared by pymarktools entry points.

pub mod config;
pub mod discovery;
pub mod http;
pub mod markdown;
pub mod model;
pub mod paths;
pub mod refactor;

/// Version of the native core exposed through the Python extension.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
