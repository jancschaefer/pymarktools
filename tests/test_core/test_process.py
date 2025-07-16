from pathlib import Path

from pymarktools.check_options import check_options
from pymarktools.commands.check import print_common_info, process_path_and_check
from pymarktools.core.image_checker import DeadImageChecker
from pymarktools.core.link_checker import DeadLinkChecker
from pymarktools.core.models import ImageInfo, LinkInfo
from pymarktools.global_state import global_state


def test_print_common_info_includes_fail(capsys, monkeypatch, tmp_path):
    monkeypatch.setitem(check_options, "fail", False)
    global_state["verbose"] = True
    print_common_info(tmp_path, check_options)
    captured = capsys.readouterr()
    assert "Fail on invalid items: False" in captured.out
    global_state["verbose"] = False
    monkeypatch.setitem(check_options, "fail", True)


class DummyLinkChecker(DeadLinkChecker):
    """Stub link checker used in tests to avoid network access."""

    def __init__(self, result: list[LinkInfo]):
        super().__init__(check_external=False)
        self.result = result

    def check_file(self, path: Path) -> list[LinkInfo]:
        return self.result


class DummyImageChecker(DeadImageChecker):
    """Stub image checker for tests with a configurable result."""

    def __init__(self, result: list[ImageInfo]):
        super().__init__(check_external=False)
        self.result = result

    def check_file(self, path: Path) -> list[ImageInfo]:
        return self.result


def test_process_path_and_check_valid(tmp_path, monkeypatch):
    file_path = tmp_path / "test.md"
    file_path.write_text("content")
    result = [LinkInfo(text="ok", url="https://example.com", line_number=1, is_valid=True)]
    monkeypatch.setitem(check_options, "parallel", False)
    global_state["quiet"] = True
    assert process_path_and_check(DummyLinkChecker(result), "links", file_path, check_options) is True
    global_state["quiet"] = False


def test_process_path_and_check_invalid(tmp_path, monkeypatch):
    file_path = tmp_path / "test.md"
    file_path.write_text("content")
    result = [ImageInfo(alt_text="bad", url="x", line_number=1, is_valid=False)]
    monkeypatch.setitem(check_options, "parallel", False)
    global_state["quiet"] = True
    assert process_path_and_check(DummyImageChecker(result), "images", file_path, check_options) is False
    global_state["quiet"] = False
