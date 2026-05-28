"""Tests for MVP-0 `devloop model` CLI command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app

runner = CliRunner()


VALID_MODELS_YAML = """\
schema_version: 1
policy:
  model_calls_allowed: false
providers:
  local_vllm:
    type: openai_compatible
    api_key:
      mode: none
models:
  qwen3_local:
    provider: local_vllm
roles:
  supervisor:
    model: qwen3_local
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _invoke_in_cwd(cwd: Path) -> any:
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["model", "check"], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_model_check_no_config_returns_zero(tmp_path: Path) -> None:
    """Command succeeds with exit code 0 when config file is absent (optional)."""
    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "file_present: False" in result.stdout


def test_model_check_valid_config_returns_zero(tmp_path: Path) -> None:
    """Command succeeds with exit code 0 when config is valid."""
    _write(tmp_path / ".ai-loop/config/models.yaml", VALID_MODELS_YAML)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "file_present: True" in result.stdout


def test_model_check_invalid_yaml_returns_two(tmp_path: Path) -> None:
    """Command fails with exit code 2 when YAML is invalid."""
    _write(tmp_path / ".ai-loop/config/models.yaml", "models: [broken\n")

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 2
    assert "error:" in result.stdout.lower() or "invalid yaml" in result.stdout.lower()


def test_model_check_invalid_schema_version_returns_two(tmp_path: Path) -> None:
    """Command fails with exit code 2 when schema_version is not 1."""
    _write(tmp_path / ".ai-loop/config/models.yaml", "schema_version: 2\n")

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 2
    assert "schema_version must be 1" in result.stdout


def test_model_check_missing_provider_reference_returns_two(tmp_path: Path) -> None:
    """Command fails with exit code 2 when model references unknown provider."""
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
models:
  qwen3_local:
    provider: missing_provider
""",
    )

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 2
    assert "unknown provider reference" in result.stdout


def test_model_check_missing_role_reference_returns_two(tmp_path: Path) -> None:
    """Command fails with exit code 2 when role references unknown model."""
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
roles:
  supervisor:
    model: missing_model
""",
    )

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 2
    assert "unknown model reference" in result.stdout


def test_model_check_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    """Command fails with exit code 3 on unexpected internal failure."""
    _write(tmp_path / ".ai-loop/config/models.yaml", VALID_MODELS_YAML)

    from devloop import cli as cli_module

    def _boom(_: Path):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_model_config_check", _boom)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 3
    assert "unexpected model check failure" in result.stdout


def _invoke_model_list_in_cwd(cwd: Path) -> any:
    """Invoke `devloop model list` in the given directory."""
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["model", "list"], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_model_list_no_config_returns_zero(tmp_path: Path) -> None:
    """Command succeeds with exit code 0 when config file is absent."""
    result = _invoke_model_list_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "no model config present" in result.stdout


def test_model_list_valid_config_returns_zero(tmp_path: Path) -> None:
    """Command succeeds with exit code 0 when config is valid."""
    _write(tmp_path / ".ai-loop/config/models.yaml", VALID_MODELS_YAML)

    result = _invoke_model_list_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "providers:" in result.stdout
    assert "  - local_vllm" in result.stdout
    assert "models:" in result.stdout
    assert "  - qwen3_local" in result.stdout
    assert "roles:" in result.stdout
    assert "  - supervisor -> qwen3_local" in result.stdout


def test_model_list_invalid_config_returns_two(tmp_path: Path) -> None:
    """Command fails with exit code 2 when config has validation errors."""
    _write(tmp_path / ".ai-loop/config/models.yaml", "schema_version: 2\n")

    result = _invoke_model_list_in_cwd(tmp_path)

    assert result.exit_code == 2
    assert "model config has errors" in result.stdout


def test_model_list_with_aliases(tmp_path: Path) -> None:
    """Command correctly displays role aliases (same_as)."""
    config = """\
schema_version: 1
providers:
  local_vllm:
    type: openai_compatible
    api_key:
      mode: none
models:
  qwen3_local:
    provider: local_vllm
roles:
  reviewer:
    model: qwen3_local
  supervisor:
    same_as: reviewer
"""
    _write(tmp_path / ".ai-loop/config/models.yaml", config)

    result = _invoke_model_list_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "roles:" in result.stdout
    assert "  - reviewer -> qwen3_local" in result.stdout
    assert "  - supervisor (alias of reviewer)" in result.stdout


def test_model_list_empty_config(tmp_path: Path) -> None:
    """Command handles empty config file."""
    _write(tmp_path / ".ai-loop/config/models.yaml", "schema_version: 1\n")

    result = _invoke_model_list_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "providers: (none)" in result.stdout
    assert "models: (none)" in result.stdout
    assert "roles: (none)" in result.stdout


def test_model_list_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    """Command fails with exit code 3 on unexpected internal failure."""
    _write(tmp_path / ".ai-loop/config/models.yaml", VALID_MODELS_YAML)

    from devloop import cli as cli_module

    def _boom(_: Path):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_model_config_check", _boom)

    result = _invoke_model_list_in_cwd(tmp_path)

    assert result.exit_code == 3
    assert "unexpected model list failure" in result.stdout
