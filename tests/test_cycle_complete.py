"""Tests for MVP-0 `devloop cycle complete` command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app
from tests.test_doctor import _make_min_project, _write

runner = CliRunner()


def _invoke_cycle_complete_in_cwd(cwd: Path, cycle_id: str):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["cycle", "complete", cycle_id], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def _make_valid_cycle(tmp_path: Path, cycle_id: str, initial_status: str = "planned") -> None:
    cycle_dir = tmp_path / ".ai-loop/cycles" / cycle_id
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            f"schema_version: \"1\"\n"
            f"cycle_id: \"{cycle_id}\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
            f"status: \"{initial_status}\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")


def test_cycle_complete_updates_status_to_completed(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 0
    assert "cycle id: c-001" in result.stdout
    assert "old status: planned" in result.stdout
    assert "new status: completed" in result.stdout

    # Verify meta.yaml was updated
    meta_path = tmp_path / ".ai-loop/cycles/c-001/meta.yaml"
    content = meta_path.read_text(encoding="utf-8")
    assert "status: completed" in content


def test_cycle_complete_is_idempotent(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "completed")

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 0
    assert "old status: completed" in result.stdout
    assert "new status: completed" in result.stdout


def test_cycle_complete_preserves_other_meta_fields(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 0

    # Verify other fields are preserved
    meta_path = tmp_path / ".ai-loop/cycles/c-001/meta.yaml"
    content = meta_path.read_text(encoding="utf-8")
    # PyYAML uses single quotes for strings with special chars, no quotes for simple strings
    assert ("schema_version: \"1\"" in content or "schema_version: '1'" in content or "schema_version: 1" in content)
    assert ("cycle_id: \"c-001\"" in content or "cycle_id: 'c-001'" in content or "cycle_id: c-001" in content)
    assert ("created_at: \"2026-01-01T00:00:00Z\"" in content or "created_at: '2026-01-01T00:00:00Z'" in content or "created_at: '2026-01-01T00:00:00Z'" in content)


def test_cycle_complete_does_not_modify_task_md(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    task_path = tmp_path / ".ai-loop/cycles/c-001/task.md"
    original_content = task_path.read_text(encoding="utf-8")

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 0
    assert task_path.read_text(encoding="utf-8") == original_content


def test_cycle_complete_does_not_modify_report_md(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    report_path = tmp_path / ".ai-loop/cycles/c-001/report.md"
    original_content = report_path.read_text(encoding="utf-8")

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 0
    assert report_path.read_text(encoding="utf-8") == original_content


def test_cycle_complete_unsafe_cycle_id_traversal_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_complete_in_cwd(tmp_path, "../foo")

    assert result.exit_code == 2
    assert "unsafe cycle id: ../foo" in result.stdout


def test_cycle_complete_unsafe_cycle_id_separator_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_complete_in_cwd(tmp_path, "foo/bar")

    assert result.exit_code == 2
    assert "unsafe cycle id: foo/bar" in result.stdout


def test_cycle_complete_cycle_not_exists_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "cycle directory missing" in result.stdout


def test_cycle_complete_meta_yaml_missing_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "meta.yaml missing" in result.stdout


def test_cycle_complete_invalid_yaml_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(cycle_dir / "meta.yaml", "broken: [\n")
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "invalid yaml: meta.yaml" in result.stdout


def test_cycle_complete_unsafe_cycle_id_backslash_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_complete_in_cwd(tmp_path, "foo\\bar")

    assert result.exit_code == 2
    assert "unsafe cycle id: foo\\bar" in result.stdout


def test_cycle_complete_unsafe_cycle_id_empty_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_complete_in_cwd(tmp_path, "")

    assert result.exit_code == 2
    assert "unsafe cycle id:" in result.stdout


def test_cycle_complete_unsafe_cycle_id_whitespace_only_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_complete_in_cwd(tmp_path, "   ")

    assert result.exit_code == 2
    assert "unsafe cycle id:" in result.stdout


def test_cycle_complete_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    from devloop import cli as cli_module

    def _boom(_: Path, __: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_cycle_complete", _boom)

    result = _invoke_cycle_complete_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 3