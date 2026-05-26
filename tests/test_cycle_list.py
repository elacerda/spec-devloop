"""Tests for MVP-0 `devloop cycle list` command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app

runner = CliRunner()


def _invoke_cycle_list_in_cwd(cwd: Path):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["cycle", "list"], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def _make_min_project(tmp_path: Path) -> None:
    """Create minimal project structure for testing."""
    ai_loop = tmp_path / ".ai-loop"
    ai_loop.mkdir(parents=True, exist_ok=True)
    (ai_loop / "cycles").mkdir(parents=True, exist_ok=True)


def test_cycle_list_missing_cycles_dir_returns_empty_and_zero(tmp_path: Path) -> None:
    """Test that missing .ai-loop/cycles/ returns empty list and exit 0."""
    result = _invoke_cycle_list_in_cwd(tmp_path)
    assert result.exit_code == 0
    assert result.stdout == ""


def test_cycle_list_empty_cycles_dir_returns_empty_and_zero(tmp_path: Path) -> None:
    """Test that empty .ai-loop/cycles/ returns empty list and exit 0."""
    _make_min_project(tmp_path)
    result = _invoke_cycle_list_in_cwd(tmp_path)
    assert result.exit_code == 0
    assert result.stdout == ""


def test_cycle_list_single_cycle(tmp_path: Path) -> None:
    """Test that a single cycle is listed."""
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles/c-001").mkdir()
    result = _invoke_cycle_list_in_cwd(tmp_path)
    assert result.exit_code == 0
    assert result.stdout == "c-001\n"


def test_cycle_list_multiple_cycles_sorted(tmp_path: Path) -> None:
    """Test that multiple cycles are listed in alphabetical order."""
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles/c-003").mkdir()
    (tmp_path / ".ai-loop/cycles/c-001").mkdir()
    (tmp_path / ".ai-loop/cycles/c-002").mkdir()
    result = _invoke_cycle_list_in_cwd(tmp_path)
    assert result.exit_code == 0
    assert result.stdout == "c-001\nc-002\nc-003\n"


def test_cycle_list_ignores_files(tmp_path: Path) -> None:
    """Test that files inside .ai-loop/cycles/ are ignored."""
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles/c-001").mkdir()
    (tmp_path / ".ai-loop/cycles/README.md").write_text("readme")
    result = _invoke_cycle_list_in_cwd(tmp_path)
    assert result.exit_code == 0
    assert result.stdout == "c-001\n"


def test_cycle_list_ignores_nested_directories(tmp_path: Path) -> None:
    """Test that nested directories are not listed recursively."""
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles/c-001").mkdir()
    (tmp_path / ".ai-loop/cycles/c-001/nested").mkdir()
    result = _invoke_cycle_list_in_cwd(tmp_path)
    assert result.exit_code == 0
    assert result.stdout == "c-001\n"


def test_cycle_list_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    """Test that unexpected failure in CLI returns exit code 3."""
    _make_min_project(tmp_path)

    from devloop import cli as cli_module

    def _boom(_: Path):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "list_cycles", _boom)

    result = _invoke_cycle_list_in_cwd(tmp_path)

    assert result.exit_code == 3


def test_cycle_list_does_not_create_files_or_directories(tmp_path: Path) -> None:
    """Test that the command does not create files or directories."""
    result = _invoke_cycle_list_in_cwd(tmp_path)
    assert result.exit_code == 0
    assert not (tmp_path / ".ai-loop").exists()
