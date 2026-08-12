use pymarktools_core::config::parse_tool_config;

#[test]
fn extracts_the_pymarktools_tool_table() {
    let config = parse_tool_config("[tool.pymarktools]\ntimeout = 12\n").unwrap();
    assert_eq!(config, r#"{"timeout":12}"#);
}
