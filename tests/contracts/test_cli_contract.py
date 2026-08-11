"""Public command-line compatibility contracts."""

import pytest
from typer.testing import CliRunner

from pymarktools.cli import app

pytestmark = pytest.mark.contract


def test_help_and_version_are_available() -> None:
    """The existing top-level CLI metadata remains available."""
    runner = CliRunner()

    assert runner.invoke(app, ["--help"]).exit_code == 0
    assert runner.invoke(app, ["--version"]).exit_code == 0


def test_disabling_all_checks_returns_one() -> None:
    """The no-work check invocation retains its failure behavior."""
    result = CliRunner().invoke(app, ["check", "--no-check-dead-links", "--no-check-dead-images"])

    assert result.exit_code == 1
    assert "Both checks disabled; nothing to do" in result.output
