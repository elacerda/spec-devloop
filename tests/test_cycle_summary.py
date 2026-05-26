"""Tests for MVP-0 `devloop cycle summary <cycle-id>` command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app

runner = CliRunner()


def _invoke_cycle_summary_in_cwd(cwd: Path, cycle_id: str):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["cycle", "summary", cycle_id], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_min_project(tmp_path: Path) -> None:
    """Create minimal project structure."""
    _write(tmp_path / ".ai-loop/project.md", "# Project\n\nTest project.")
    _write(tmp_path / ".ai-loop/architecture.md", "# Architecture\n\nTest architecture.")
    _write(tmp_path / ".ai-loop/protocol.md", "# Protocol\n\nTest protocol.")


def _make_valid_cycle(tmp_path: Path, cycle_id: str) -> None:
    """Create a valid cycle with all required files."""
    cycle_dir = tmp_path / ".ai-loop/cycles" / cycle_id
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            f"cycle_id: \"{cycle_id}\"\n"
            "created_at: \"2026-05-26T10:00:00Z\"\n"
            "status: \"planned\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "# Task\n\nTest task.")
    _write(cycle_dir / "report.md", "# Report\n\nTest report.")


def test_cycle_summary_valid_cycle_returns_zero(tmp_path: Path) -> None:
    """Ciclo válido retorna exit code 0 e mostra resumo."""
    _make_min_project(tmp_path)
    _make_valid_cycle(tmp_path, "c-001")

    result = _invoke_cycle_summary_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 0
    assert "cycle id: c-001" in result.stdout
    assert "status: planned" in result.stdout
    assert "created_at: 2026-05-26" in result.stdout
    assert "required files:" in result.stdout
    assert "  meta.yaml: present" in result.stdout
    assert "  task.md: present" in result.stdout
    assert "  report.md: present" in result.stdout
    assert "optional files:" in result.stdout
    assert "  plan.md: missing" in result.stdout
    assert "  evidence.md: missing" in result.stdout
    assert "errors: 0" in result.stdout


def test_cycle_summary_missing_report_md_returns_error(tmp_path: Path) -> None:
    """Ciclo com report.md ausente retorna exit code 2."""
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles" / "c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"2026-05-26T10:00:00Z\"\n"
            "status: \"planned\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "# Task\n\nTest task.")

    result = _invoke_cycle_summary_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "required files:" in result.stdout
    assert "  report.md: missing" in result.stdout
    assert "errors: 1" in result.stdout


def test_cycle_summary_missing_cycle_directory_returns_error(tmp_path: Path) -> None:
    """Ciclo inexistente retorna exit code 2."""
    _make_min_project(tmp_path)

    result = _invoke_cycle_summary_in_cwd(tmp_path, "c-999")

    assert result.exit_code == 2
    assert "cycle id: c-999" in result.stdout
    assert "status: missing" in result.stdout
    assert "created_at: missing" in result.stdout
    assert "required files:" in result.stdout
    assert "  meta.yaml: missing" in result.stdout
    assert "  task.md: missing" in result.stdout
    assert "  report.md: missing" in result.stdout
    assert "optional files:" in result.stdout
    assert "  plan.md: missing" in result.stdout
    assert "  evidence.md: missing" in result.stdout
    assert "errors: 4" in result.stdout
    assert "cycle directory missing:" in result.stdout


def test_cycle_summary_unsafe_cycle_id_returns_error(tmp_path: Path) -> None:
    """Cycle-id inseguro retorna exit code 2."""
    _make_min_project(tmp_path)

    result = _invoke_cycle_summary_in_cwd(tmp_path, "../foo")

    assert result.exit_code == 2
    assert "cycle id: ../foo" in result.stdout
    assert "status: missing" in result.stdout
    assert "created_at: missing" in result.stdout
    assert "required files:" in result.stdout
    assert "optional files:" in result.stdout
    assert "errors: 1" in result.stdout
    assert "unsafe cycle id: ../foo" in result.stdout


def test_cycle_summary_optional_files_present(tmp_path: Path) -> None:
    """Arquivos opcionais presentes aparecem como present."""
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles" / "c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"2026-05-26T10:00:00Z\"\n"
            "status: \"planned\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "# Task\n\nTest task.")
    _write(cycle_dir / "report.md", "# Report\n\nTest report.")
    _write(cycle_dir / "plan.md", "# Plan\n\nTest plan.")
    _write(cycle_dir / "evidence.md", "# Evidence\n\nTest evidence.")

    result = _invoke_cycle_summary_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 0
    assert "optional files:" in result.stdout
    assert "  plan.md: present" in result.stdout
    assert "  evidence.md: present" in result.stdout


def test_cycle_summary_does_not_create_files(tmp_path: Path) -> None:
    """Comando não cria arquivos."""
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles" / "c-001"
    assert not cycle_dir.exists()

    result = _invoke_cycle_summary_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert not cycle_dir.exists()


def test_cycle_summary_missing_status_shows_missing(tmp_path: Path) -> None:
    """Status ausente mostra 'missing' e retorna exit code 2."""
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles" / "c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "created_at: \"2026-05-26T10:00:00Z\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "# Task\n\nTest task.")
    _write(cycle_dir / "report.md", "# Report\n\nTest report.")

    result = _invoke_cycle_summary_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "status: missing" in result.stdout
    assert "errors: 1" in result.stdout
    assert "required meta field missing: status" in result.stdout


def test_cycle_summary_missing_created_at_shows_missing(tmp_path: Path) -> None:
    """Created_at ausente mostra 'missing' e retorna exit code 2."""
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles" / "c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "status: \"planned\"\n"
        ),
    )
    _write(cycle_dir / "task.md", "# Task\n\nTest task.")
    _write(cycle_dir / "report.md", "# Report\n\nTest report.")

    result = _invoke_cycle_summary_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "created_at: missing" in result.stdout
    assert "errors: 1" in result.stdout
    assert "required meta field missing: created_at" in result.stdout


def test_cycle_summary_unsafe_cycle_id_backslash_returns_error(tmp_path: Path) -> None:
    """Cycle-id inseguro com backslash retorna exit code 2."""
    _make_min_project(tmp_path)

    result = _invoke_cycle_summary_in_cwd(tmp_path, "foo\\bar")

    assert result.exit_code == 2
    assert "cycle id: foo\\bar" in result.stdout
    assert "status: missing" in result.stdout
    assert "created_at: missing" in result.stdout
    assert "required files:" in result.stdout
    assert "optional files:" in result.stdout
    assert "errors: 1" in result.stdout
    assert "unsafe cycle id: foo\\bar" in result.stdout


def test_cycle_summary_unsafe_cycle_id_empty_returns_error(tmp_path: Path) -> None:
    """Cycle-id vazio retorna exit code 2."""
    _make_min_project(tmp_path)

    result = _invoke_cycle_summary_in_cwd(tmp_path, "")

    assert result.exit_code == 2
    assert "cycle id: " in result.stdout
    assert "status: missing" in result.stdout
    assert "created_at: missing" in result.stdout
    assert "required files:" in result.stdout
    assert "optional files:" in result.stdout
    assert "errors: 1" in result.stdout
    assert "unsafe cycle id: " in result.stdout


def test_cycle_summary_unsafe_cycle_id_whitespace_only_returns_error(tmp_path: Path) -> None:
    """Cycle-id com apenas espaços retorna exit code 2."""
    _make_min_project(tmp_path)

    result = _invoke_cycle_summary_in_cwd(tmp_path, "   ")

    assert result.exit_code == 2
    assert "cycle id:    " in result.stdout
    assert "status: missing" in result.stdout
    assert "created_at: missing" in result.stdout
    assert "required files:" in result.stdout
    assert "optional files:" in result.stdout
    assert "errors: 1" in result.stdout
    assert "unsafe cycle id:    " in result.stdout


def test_cycle_summary_created_at_not_string_returns_exit_code_2(tmp_path: Path) -> None:
    """Created_at que não é string (ex: int) mostra 'missing' e retorna exit code 2."""
    _make_min_project(tmp_path)
    cycle_dir = tmp_path / ".ai-loop/cycles" / "c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    _write(
        cycle_dir / "meta.yaml",
        (
            "schema_version: \"1\"\n"
            "cycle_id: \"c-001\"\n"
            "status: \"planned\"\n"
            "created_at: 12345\n"  # Int em vez de string
        ),
    )
    _write(cycle_dir / "task.md", "# Task\n\nTest task.")
    _write(cycle_dir / "report.md", "# Report\n\nTest report.")

    result = _invoke_cycle_summary_in_cwd(tmp_path, "c-001")

    assert result.exit_code == 2
    assert "created_at: missing" in result.stdout
    assert "errors: 1" in result.stdout
    assert "required meta field must be non-empty string: created_at" in result.stdout
