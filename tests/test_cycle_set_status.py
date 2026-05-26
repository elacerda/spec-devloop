"""Tests for MVP-0 `devloop cycle set-status` command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app
from tests.test_doctor import _make_min_project, _write

runner = CliRunner()


def _invoke_cycle_set_status_in_cwd(cwd: Path, cycle_id: str, status: str):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["cycle", "set-status", cycle_id, status], catch_exceptions=False)
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


def test_cycle_set_status_updates_status(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "ready_for_worker")

    assert result.exit_code == 0
    assert "cycle id: c-001" in result.stdout
    assert "old status: planned" in result.stdout
    assert "new status: ready_for_worker" in result.stdout

    # Verify meta.yaml was updated
    meta_path = tmp_path / ".ai-loop/cycles/c-001/meta.yaml"
    content = meta_path.read_text(encoding="utf-8")
    assert "status: ready_for_worker" in content


def test_cycle_set_status_preserves_other_fields(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "in_progress")

    assert result.exit_code == 0

    # Verify other fields are preserved
    meta_path = tmp_path / ".ai-loop/cycles/c-001/meta.yaml"
    content = meta_path.read_text(encoding="utf-8")
    # PyYAML uses single quotes for strings with special chars, no quotes for simple strings
    assert ("schema_version: \"1\"" in content or "schema_version: '1'" in content or "schema_version: 1" in content)
    assert ("cycle_id: \"c-001\"" in content or "cycle_id: 'c-001'" in content or "cycle_id: c-001" in content)
    assert ("created_at: \"2026-01-01T00:00:00Z\"" in content or "created_at: '2026-01-01T00:00:00Z'" in content or "created_at: '2026-01-01T00:00:00Z'" in content)


def test_cycle_set_status_is_idempotent(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "ready_for_worker")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "ready_for_worker")

    assert result.exit_code == 0
    assert "old status: ready_for_worker" in result.stdout
    assert "new status: ready_for_worker" in result.stdout


def test_cycle_set_status_invalid_status_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "invalid_status")

    assert result.exit_code == 2
    assert "invalid status value: invalid_status" in result.stdout
    assert "Allowed values are:" in result.stdout


def test_cycle_set_status_unsafe_cycle_id_traversal_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "../foo", "ready_for_worker")

    assert result.exit_code == 2
    assert "unsafe cycle id: ../foo" in result.stdout


def test_cycle_set_status_unsafe_cycle_id_separator_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "foo/bar", "ready_for_worker")

    assert result.exit_code == 2
    assert "unsafe cycle id: foo/bar" in result.stdout


def test_cycle_set_status_cycle_not_exists_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "ready_for_worker")

    assert result.exit_code == 2
    assert "cycle directory missing" in result.stdout


def test_cycle_set_status_meta_yaml_missing_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "ready_for_worker")

    assert result.exit_code == 2
    assert "meta.yaml missing" in result.stdout


def test_cycle_set_status_invalid_yaml_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(cycle_dir / "meta.yaml", "broken: [\n")
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "ready_for_worker")

    assert result.exit_code == 2
    assert "invalid yaml: meta.yaml" in result.stdout


def test_cycle_set_status_yaml_not_mapping_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(cycle_dir / "meta.yaml", "- list\n")
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "ready_for_worker")

    assert result.exit_code == 2
    assert "invalid yaml: meta.yaml" in result.stdout


def test_cycle_set_status_does_not_modify_task_md(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    task_path = tmp_path / ".ai-loop/cycles/c-001/task.md"
    original_content = task_path.read_text(encoding="utf-8")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "in_progress")

    assert result.exit_code == 0
    assert task_path.read_text(encoding="utf-8") == original_content


def test_cycle_set_status_does_not_modify_report_md(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    report_path = tmp_path / ".ai-loop/cycles/c-001/report.md"
    original_content = report_path.read_text(encoding="utf-8")

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "in_progress")

    assert result.exit_code == 0
    assert report_path.read_text(encoding="utf-8") == original_content


def test_cycle_set_status_after_update_cycle_check_passes(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    # First update status
    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "in_progress")
    assert result.exit_code == 0

    # Then verify cycle check passes
    result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", "in_progress")
    assert result.exit_code == 0


def test_cycle_set_status_unsafe_cycle_id_backslash_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "foo\\bar", "ready_for_worker")

    assert result.exit_code == 2
    assert "unsafe cycle id: foo\\bar" in result.stdout


def test_cycle_set_status_unsafe_cycle_id_empty_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "", "ready_for_worker")

    assert result.exit_code == 2
    assert "unsafe cycle id:" in result.stdout


def test_cycle_set_status_unsafe_cycle_id_whitespace_only_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_set_status_in_cwd(tmp_path, "   ", "ready_for_worker")

    assert result.exit_code == 2
    assert "unsafe cycle id:" in result.stdout


def test_cycle_set_status_allows_all_valid_status_values(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001", "planned")

    for status in ["ready_for_worker", "in_progress", "waiting_review", "completed", "blocked"]:
        result = _invoke_cycle_set_status_in_cwd(tmp_path, "c-001", status)
        assert result.exit_code == 0, f"Failed for status: {status}"
