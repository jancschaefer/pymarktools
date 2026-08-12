//! TOML configuration parsing for the Python compatibility facade.

/// Extract the `[tool.pymarktools]` table as JSON.
pub fn parse_tool_config(content: &str) -> Result<String, String> {
    let document = content
        .parse::<toml::Value>()
        .map_err(|error| error.to_string())?;
    let value = document
        .get("tool")
        .and_then(|tool| tool.get("pymarktools"))
        .cloned()
        .unwrap_or(toml::Value::Table(Default::default()));
    serde_json::to_string(&value).map_err(|error| error.to_string())
}
