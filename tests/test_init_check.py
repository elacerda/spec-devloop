"""Tests for MVP-0 `devloop init --check` command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app
from tests.test_doctor import _make_min_project

runner = CliRunner()


def _invoke_init_in_cwd(cwd: Path, *args: str):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["init", *args], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_init_check_all_minimum_paths_present_returns_zero(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_init_in_cwd(tmp_path, "--check")

    assert result.exit_code == 0
    assert "ready_for_manual_setup: yes" in result.stdout
    assert "missing: 0" in result.stdout


def test_init_check_missing_required_file_returns_two(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)
    (tmp_path / ".ai-loop/project.md").unlink()

    result = _invoke_init_in_cwd(tmp_path, "--check")

    assert result.exit_code == 2
    assert "missing:" in result.stdout
    assert "ready_for_manual_setup: no" in result.stdout


def test_init_check_missing_managed_directory_returns_two(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)

    result = _invoke_init_in_cwd(tmp_path, "--check")

    assert result.exit_code == 2


def test_init_without_check_is_explicit_failure(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_init_in_cwd(tmp_path)

    assert result.exit_code != 0
    assert "not supported in MVP-0" in result.stdout


def test_init_check_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    _make_min_project(tmp_path)

    from devloop import cli as cli_module

    def _boom(_: Path):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_init_check", _boom)

    result = _invoke_init_in_cwd(tmp_path, "--check")

    assert result.exit_code == 3


def test_init_check_does_not_create_missing_managed_directories(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_init_in_cwd(tmp_path, "--check")

    assert result.exit_code == 2
    assert not (tmp_path / ".ai-loop/cycles").exists()
    assert not (tmp_path / ".ai-loop/state").exists()
