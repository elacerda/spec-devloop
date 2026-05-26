"""Tests for `devloop init` project creation in MVP-0."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app

runner = CliRunner()


def _invoke_init_in_cwd(cwd: Path, *args: str):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["init", *args], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_init_creates_ai_loop_directory(tmp_path: Path) -> None:
    """Test that init creates .ai-loop directory."""
    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert (tmp_path / ".ai-loop").is_dir()
    assert "created: .ai-loop" in result.stdout


def test_init_creates_project_md(tmp_path: Path) -> None:
    """Test that init creates .ai-loop/project.md with placeholder content."""
    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 0
    project_md = tmp_path / ".ai-loop/project.md"
    assert project_md.is_file()

    content = project_md.read_text(encoding="utf-8")
    assert "# Project" in content
    assert "Describe the project here." in content
    assert "created: .ai-loop/project.md" in result.stdout


def test_init_creates_cycles_directory(tmp_path: Path) -> None:
    """Test that init creates .ai-loop/cycles directory."""
    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 0
    cycles_dir = tmp_path / ".ai-loop/cycles"
    assert cycles_dir.is_dir()
    assert "created: .ai-loop/cycles" in result.stdout


def test_init_does_not_overwrite_existing_project_md(tmp_path: Path) -> None:
    """Test that init preserves existing project.md content."""
    # Create existing project.md with custom content
    (tmp_path / ".ai-loop").mkdir(parents=True)
    existing_content = "# Custom Project\nThis is my custom content.\n"
    (tmp_path / ".ai-loop/project.md").write_text(existing_content, encoding="utf-8")

    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 0
    project_md = tmp_path / ".ai-loop/project.md"
    assert project_md.is_file()
    # Content should be preserved, not overwritten
    assert project_md.read_text(encoding="utf-8") == existing_content
    assert "preserved: .ai-loop/project.md" in result.stdout


def test_init_is_idempotent(tmp_path: Path) -> None:
    """Test that running init twice is safe and produces same result."""
    # First run
    result1 = _invoke_init_in_cwd(tmp_path)
    assert result1.exit_code == 0
    assert "created: .ai-loop" in result1.stdout
    assert "created: .ai-loop/project.md" in result1.stdout
    assert "created: .ai-loop/cycles" in result1.stdout

    # Second run
    result2 = _invoke_init_in_cwd(tmp_path)
    assert result2.exit_code == 0
    # Should preserve existing files
    assert "preserved: .ai-loop" in result2.stdout
    assert "preserved: .ai-loop/project.md" in result2.stdout
    assert "preserved: .ai-loop/cycles" in result2.stdout


def test_init_check_continues_to_work(tmp_path: Path) -> None:
    """Test that init --check continues to work as before."""
    # Create minimal project structure matching MINIMUM_SETUP_PATHS
    (tmp_path / ".ai-loop").mkdir(parents=True)
    (tmp_path / ".ai-loop/project.md").write_text("# Test\n", encoding="utf-8")
    (tmp_path / ".ai-loop/architecture.md").write_text("# Architecture\n", encoding="utf-8")
    (tmp_path / ".ai-loop/protocol.md").write_text("# Protocol\n", encoding="utf-8")
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)
    (tmp_path / ".ai-loop/config").mkdir(parents=True)
    (tmp_path / ".ai-loop/config/commands.yaml").write_text("schema_version: 1\n", encoding="utf-8")

    result = _invoke_init_in_cwd(tmp_path, "--check")

    assert result.exit_code == 0
    assert "ready_for_manual_setup: yes" in result.stdout


def test_init_output_contains_created_preserved_paths(tmp_path: Path) -> None:
    """Test that output lists created and preserved paths."""
    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "initialized devloop project" in result.stdout
    assert "created: .ai-loop" in result.stdout
    assert "created: .ai-loop/project.md" in result.stdout
    assert "created: .ai-loop/cycles" in result.stdout


def test_init_does_not_create_files_outside_ai_loop(tmp_path: Path) -> None:
    """Test that init does not create files outside .ai-loop directory."""
    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 0

    # Check no files were created outside .ai-loop
    for item in tmp_path.iterdir():
        if item.name == ".ai-loop":
            continue
        assert not item.exists() or item.is_dir()


def test_init_with_existing_ai_loop_directory(tmp_path: Path) -> None:
    """Test init when .ai-loop directory already exists but other files don't."""
    # Create only .ai-loop directory
    (tmp_path / ".ai-loop").mkdir(parents=True)

    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "preserved: .ai-loop" in result.stdout
    assert "created: .ai-loop/project.md" in result.stdout
    assert "created: .ai-loop/cycles" in result.stdout


def test_init_exit_code_zero_on_success(tmp_path: Path) -> None:
    """Test that init returns exit code 0 on success."""
    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 0


def test_init_exit_code_two_on_error(tmp_path: Path, monkeypatch) -> None:
    """Test that init returns exit code 2 on error from run_init_project."""
    # Mock run_init_project to raise an error
    from devloop import cli as cli_module

    def _boom(_: Path):
        raise OSError("simulated error")

    monkeypatch.setattr(cli_module, "run_init_project", _boom)

    result = _invoke_init_in_cwd(tmp_path)

    # OSError is caught as unexpected internal failure, returns exit code 3
    assert result.exit_code == 3


def test_init_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    """Test that unexpected failures return exit code 3."""
    from devloop import cli as cli_module

    def _boom(_: Path):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_init_project", _boom)

    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code == 3