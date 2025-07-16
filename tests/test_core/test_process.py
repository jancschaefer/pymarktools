from pathlib import Path

from pymarktools.commands.check import (
    check_state,
    print_common_info,
    process_path_and_check,
)
from pymarktools.core.models import ImageInfo, LinkInfo
from pymarktools.state import global_state


def test_print_common_info_includes_fail(capsys, monkeypatch, tmp_path):
    monkeypatch.setitem(check_state, "fail", False)
    global_state["verbose"] = True
    print_common_info(tmp_path)
    captured = capsys.readouterr()
    assert "Fail on invalid items: False" in captured.out
    global_state["verbose"] = False
    monkeypatch.setitem(check_state, "fail", True)


class DummyChecker:
    def __init__(self, result):
        self.result = result

    def check_file(self, path: Path):
        return self.result


def test_process_path_and_check_valid(tmp_path, monkeypatch):
    file_path = tmp_path / "test.md"
    file_path.write_text("content")
    result = [LinkInfo(text="ok", url="https://example.com", line_number=1, is_valid=True)]
    monkeypatch.setitem(check_state, "parallel", False)
    global_state["quiet"] = True
    assert process_path_and_check(DummyChecker(result), "links", file_path) is True
    global_state["quiet"] = False


def test_process_path_and_check_invalid(tmp_path, monkeypatch):
    file_path = tmp_path / "test.md"
    file_path.write_text("content")
    result = [ImageInfo(alt_text="bad", url="x", line_number=1, is_valid=False)]
    monkeypatch.setitem(check_state, "parallel", False)
    global_state["quiet"] = True
    assert process_path_and_check(DummyChecker(result), "images", file_path) is False
    global_state["quiet"] = False
