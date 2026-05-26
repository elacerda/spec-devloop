"""Tests for MVP-0 `devloop cycle check` command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app
from tests.test_doctor import _make_min_project, _write

runner = CliRunner()


def _invoke_cycle_check_in_cwd(cwd: Path, cycle_id: str):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["cycle", "check", cycle_id], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def _make_valid_cycle(tmp_path: Path, cycle_id: str) -> None:
    cycle_dir = tmp_path / ".ai-loop/cycles" / cycle_id
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            f"cycle_id: \"{cycle_id}\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
            "status: \"draft\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")


def test_cycle_check_valid_cycle_returns_success(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 0
    assert "errors: 0" in result.stdout
    assert "ready: yes" in result.stdout


def test_cycle_check_missing_cycle_directory_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "cycle directory missing" in result.stdout


def test_cycle_check_missing_required_files_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "required artifact missing" in result.stdout


def test_cycle_check_invalid_meta_yaml_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(cycle_dir / "meta.yaml", "broken: [\n")
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "invalid yaml: meta.yaml" in result.stdout


def test_cycle_check_meta_yaml_not_mapping_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(cycle_dir / "meta.yaml", "- list\n")
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "yaml root must be a mapping" in result.stdout


def test_cycle_check_required_meta_field_missing_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "required meta field missing: status" in result.stdout


def test_cycle_check_required_meta_field_empty_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
            "status: \"\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "required meta field must be non-empty string: status" in result.stdout


def test_cycle_check_meta_cycle_id_mismatch_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"different\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
            "status: \"draft\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "meta cycle_id does not match requested cycle id" in result.stdout


def test_cycle_check_unsafe_cycle_id_traversal_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_check_in_cwd(tmp_path, "../foo")

    assert result.exit_code == 2
    assert "unsafe cycle id: ../foo" in result.stdout


def test_cycle_check_unsafe_cycle_id_separator_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_check_in_cwd(tmp_path, "foo/bar")

    assert result.exit_code == 2
    assert "unsafe cycle id: foo/bar" in result.stdout


def test_cycle_check_does_not_create_files_or_directories(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    assert not cycle_dir.exists()

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert not cycle_dir.exists()


def test_cycle_check_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    _make_min_project(tmp_path)

    from devloop import cli as cli_module

    def _boom(_: Path, __: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_cycle_check", _boom)

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 3


def test_cycle_check_unsafe_cycle_id_backslash_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_check_in_cwd(tmp_path, "foo\\bar")

    assert result.exit_code == 2
    assert "unsafe cycle id: foo\\bar" in result.stdout


def test_cycle_check_unsafe_cycle_id_empty_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_check_in_cwd(tmp_path, "")

    assert result.exit_code == 2
    assert "unsafe cycle id:" in result.stdout


def test_cycle_check_unsafe_cycle_id_whitespace_only_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_cycle_check_in_cwd(tmp_path, "   ")

    assert result.exit_code == 2
    assert "unsafe cycle id:" in result.stdout


def test_cycle_check_meta_yaml_null_field_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: null\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
            "status: \"draft\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "required meta field must be non-empty string: schema_version" in result.stdout


def test_cycle_check_meta_yaml_whitespace_field_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"   \"\n"
            "status: \"draft\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "required meta field must be non-empty string: created_at" in result.stdout


def test_cycle_check_meta_yaml_non_string_field_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: 1\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
            "status: \"draft\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "required meta field must be non-empty string: schema_version" in result.stdout


def test_cycle_check_missing_task_and_report_returns_errors(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
            "status: \"draft\"\n"
        ),
    )

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "required artifact missing: task.md" in result.stdout
    assert "required artifact missing: report.md" in result.stdout


def test_cycle_check_meta_cycle_id_case_sensitive_mismatch_returns_error(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles/c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"C-001\"\n"
            "created_at: \"2026-01-01T00:00:00Z\"\n"
            "status: \"draft\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")

    result = _invoke_cycle_check_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "meta cycle_id does not match requested cycle id" in result.stdout
