"""Tests for MVP-0 `devloop status` command."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app
from tests.test_doctor import _make_min_project, _write

runner = CliRunner()


def _invoke_status_in_cwd(cwd: Path):
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["status"], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_status_valid_minimum_returns_zero_and_ready_yes(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_status_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "ready: yes" in result.stdout


def test_status_missing_required_file_returns_two_and_ready_no(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/project.md").unlink()

    result = _invoke_status_in_cwd(tmp_path)

    assert result.exit_code == 2
    assert "ready: no" in result.stdout


def test_status_outside_git_returns_zero_and_not_detected(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_status_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "git: not detected" in result.stdout


def test_status_dirty_git_worktree_returns_zero_and_dirty(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    _write(tmp_path / "dirty.txt", "x")

    result = _invoke_status_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "git: dirty" in result.stdout


def test_status_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    _make_min_project(tmp_path)

    from devloop import cli as cli_module

    def _boom(_: Path):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_doctor", _boom)

    result = _invoke_status_in_cwd(tmp_path)

    assert result.exit_code == 3


VALID_MODELS_YAML = """\
schema_version: 1
providers:
  openai:
    type: openai_compatible
    enabled: true
    api_key:
      mode: none
models:
  qwen3-coder-next-fp8:
    provider: openai
roles:
  default:
    model: qwen3-coder-next-fp8
"""


def test_status_missing_model_config_reports_absent(tmp_path: Path) -> None:
    """Missing models.yaml should report model_config: absent but not affect readiness."""
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_status_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "model_config: absent" in result.stdout
    assert "ready: yes" in result.stdout


def test_status_valid_model_config_reports_valid(tmp_path: Path) -> None:
    """Valid models.yaml should report model_config: valid."""
    _make_min_project(tmp_path)
    _write(tmp_path / ".ai-loop/config/models.yaml", VALID_MODELS_YAML)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_status_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "model_config: valid" in result.stdout


def test_status_invalid_model_config_reports_invalid(tmp_path: Path) -> None:
    """Invalid models.yaml should report model_config: invalid and fail readiness."""
    _make_min_project(tmp_path)
    _write(tmp_path / ".ai-loop/config/models.yaml", "schema_version: 2\n")
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_status_in_cwd(tmp_path)

    assert result.exit_code == 2
    assert "model_config: invalid" in result.stdout
    assert "ready: no" in result.stdout
