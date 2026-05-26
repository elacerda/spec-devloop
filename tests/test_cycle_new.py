"""Tests for MVP-0 `devloop cycle new` command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app
from tests.test_doctor import _make_min_project, _write

runner = CliRunner()


def _invoke_cycle_new_in_cwd(cwd: Path, task_description: str):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["cycle", "new", task_description], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_cycle_new_creates_first_cycle_c001(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_new_in_cwd(tmp_path, "Test task description")

    assert result.exit_code == 0
    assert "created cycle: c-001" in result.stdout
    assert "path: .ai-loop/cycles/c-001" in result.stdout
    assert "status: planned" in result.stdout

    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    assert cycle_dir.is_dir()

    meta_path = cycle_dir / "meta.yaml"
    assert meta_path.is_file()

    task_path = cycle_dir / "task.md"
    assert task_path.is_file()

    report_path = cycle_dir / "report.md"
    assert report_path.is_file()


def test_cycle_new_creates_c002_when_c001_exists(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    # Create c-001 first
    _invoke_cycle_new_in_cwd(tmp_path, "First task")

    # Create c-002
    result = _invoke_cycle_new_in_cwd(tmp_path, "Second task")

    assert result.exit_code == 0
    assert "created cycle: c-002" in result.stdout


def test_cycle_new_ignores_non_matching_directories(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    # Create non-matching directories
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".ai-loop/cycles/other").mkdir()
    (tmp_path / ".ai-loop/cycles/c-001").mkdir()
    (tmp_path / ".ai-loop/cycles/c-003").mkdir()
    (tmp_path / ".ai-loop/cycles/invalid-001").mkdir()

    result = _invoke_cycle_new_in_cwd(tmp_path, "Test task")

    assert result.exit_code == 0
    assert "created cycle: c-004" in result.stdout


def test_cycle_new_creates_meta_yaml_with_correct_content(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    _invoke_cycle_new_in_cwd(tmp_path, "Test task")

    meta_path = tmp_path / ".ai-loop/cycles/c-001/meta.yaml"
    content = meta_path.read_text(encoding="utf-8")

    # PyYAML may use single or double quotes, so check for both
    assert ("schema_version: '0'" in content or 'schema_version: "0"' in content)
    assert "cycle_id: c-001" in content
    assert "status: planned" in content


def test_cycle_new_creates_task_md_with_description(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    _invoke_cycle_new_in_cwd(tmp_path, "My custom task description")

    task_path = tmp_path / ".ai-loop/cycles/c-001/task.md"
    content = task_path.read_text(encoding="utf-8")

    assert "# Task" in content
    assert "My custom task description" in content


def test_cycle_new_creates_report_md_placeholder(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    _invoke_cycle_new_in_cwd(tmp_path, "Test task")

    report_path = tmp_path / ".ai-loop/cycles/c-001/report.md"
    content = report_path.read_text(encoding="utf-8")

    assert "# Report" in content
    assert "No execution recorded yet" in content


def test_cycle_new_does_not_overwrite_existing_cycle(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    # Create c-001
    result1 = _invoke_cycle_new_in_cwd(tmp_path, "First task")
    assert result1.exit_code == 0

    # Try to create c-001 again (should not happen with correct logic, but test anyway)
    # Actually, the logic should create c-002, not overwrite
    result2 = _invoke_cycle_new_in_cwd(tmp_path, "Second task")
    assert result2.exit_code == 0
    assert "created cycle: c-002" in result2.stdout


def test_cycle_new_creates_cycles_directory_if_missing(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    # Ensure .ai-loop/cycles doesn't exist
    cycles_dir = tmp_path / ".ai-loop/cycles"
    assert not cycles_dir.exists()

    result = _invoke_cycle_new_in_cwd(tmp_path, "Test task")

    assert result.exit_code == 0
    assert cycles_dir.is_dir()
    assert (cycles_dir / "c-001").is_dir()


def test_cycle_new_fails_for_empty_task_description(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_new_in_cwd(tmp_path, "")

    assert result.exit_code == 2
    assert "error: task description cannot be empty" in result.stdout


def test_cycle_new_fails_for_whitespace_only_task_description(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_new_in_cwd(tmp_path, "   ")

    assert result.exit_code == 2
    assert "error: task description cannot be empty" in result.stdout


def test_cycle_new_compatible_with_cycle_check(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    # Create cycle using cycle new
    result_new = _invoke_cycle_new_in_cwd(tmp_path, "Test task")
    assert result_new.exit_code == 0

    # Check cycle using cycle check
    result_check = _invoke_cycle_check_in_cwd(tmp_path, "c-001")
    assert result_check.exit_code == 0
    assert "errors: 0" in result_check.stdout
    assert "ready: yes" in result_check.stdout


def _invoke_cycle_check_in_cwd(cwd: Path, cycle_id: str):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["cycle", "check", cycle_id], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_cycle_new_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    _make_min_project(tmp_path)

    from devloop import cli as cli_module

    def _boom(_: Path, __: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_cycle_new", _boom)

    result = _invoke_cycle_new_in_cwd(tmp_path, "Test task")

    assert result.exit_code == 3