from pymarktools.check_options import check_options
from pymarktools.commands.check import (
    echo_error,
    echo_if_not_quiet,
    echo_if_verbose,
    echo_info,
    echo_success,
    echo_warning,
    print_common_info,
)
from pymarktools.global_state import global_state


def test_echo_functions(capsys):
    global_state.update({"verbose": False, "quiet": False, "color": False})
    echo_if_not_quiet("message")
    echo_success("success")
    echo_error("error")
    echo_warning("warn")
    echo_info("info")
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "message" in output
    assert "success" in output
    assert "error" in output
    assert "warn" in output
    assert "info" in output


def test_echo_verbose(capsys):
    global_state.update({"verbose": True, "quiet": False, "color": False})
    echo_if_verbose("verbose msg")
    captured = capsys.readouterr()
    assert "verbose msg" in captured.out


def test_echo_print_common_info(capsys, tmp_path):
    global_state.update({"verbose": True, "quiet": False, "color": False})
    check_options.update({"include_pattern": "*.md", "parallel": True, "output": None, "workers": None})
    print_common_info(tmp_path, check_options)
    captured = capsys.readouterr()
    assert "Checking in:" in captured.out
