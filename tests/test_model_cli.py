"""Tests for MVP-0 `devloop model` CLI command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app
from devloop.model_ping import ModelPingExecutionResult

runner = CliRunner()


VALID_MODELS_YAML = """\
schema_version: 1
policy:
  model_calls_allowed: false
providers:
  local_vllm:
    type: openai_compatible
    base_url: http://localhost:8000/v1
    api_key:
      mode: none
models:
  qwen3_local:
    name: qwen3_local
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
    base_url: http://localhost:8000/v1
    api_key:
      mode: none
models:
  qwen3_local:
    name: qwen3_local
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


def _invoke_model_ping_in_cwd(cwd: Path, args: list[str], env: dict[str, str] | None = None) -> any:
    """Invoke `devloop model ping` in the given directory."""
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["model", "ping", *args], env=env, catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_model_ping_missing_config_returns_error_two(tmp_path: Path) -> None:
    """Ping fails with exit code 2 and error result when config is missing."""
    result = _invoke_model_ping_in_cwd(tmp_path, ["supervisor", "--allow-call"])

    assert result.exit_code == 2
    assert "target: supervisor" in result.stdout
    assert "result: error" in result.stdout
    assert "model config file is required for ping" in result.stdout
    assert "attempted_transport: false" in result.stdout


def test_model_ping_allow_call_missing_returns_blocked_two(tmp_path: Path) -> None:
    """Ping fails with blocked result when --allow-call is omitted."""
    config = VALID_MODELS_YAML.replace("model_calls_allowed: false", "model_calls_allowed: true")
    _write(tmp_path / ".ai-loop/config/models.yaml", config)

    result = _invoke_model_ping_in_cwd(tmp_path, ["supervisor"])

    assert result.exit_code == 2
    assert "result: blocked" in result.stdout
    assert "allow_call=True" in result.stdout
    assert "attempted_transport: false" in result.stdout


def test_model_ping_policy_false_returns_blocked_two(tmp_path: Path) -> None:
    """Ping fails with blocked result when policy disallows model calls."""
    _write(tmp_path / ".ai-loop/config/models.yaml", VALID_MODELS_YAML)

    result = _invoke_model_ping_in_cwd(tmp_path, ["supervisor", "--allow-call"])

    assert result.exit_code == 2
    assert "result: blocked" in result.stdout
    assert "policy.model_calls_allowed" in result.stdout
    assert "attempted_transport: false" in result.stdout


def test_model_ping_unknown_target_returns_error_two(tmp_path: Path) -> None:
    """Ping fails with error result for unknown role/model target."""
    config = VALID_MODELS_YAML.replace("model_calls_allowed: false", "model_calls_allowed: true")
    _write(tmp_path / ".ai-loop/config/models.yaml", config)

    result = _invoke_model_ping_in_cwd(tmp_path, ["missing", "--allow-call"])

    assert result.exit_code == 2
    assert "result: error" in result.stdout
    assert "unknown target: missing" in result.stdout


def test_model_ping_success_returns_ok_zero(tmp_path: Path, monkeypatch) -> None:
    """Ping succeeds with transport output when policy and allow_call are enabled."""
    config = """schema_version: 1
policy:
  model_calls_allowed: true
providers:
  local_vllm:
    type: openai_compatible
    base_url: http://localhost:8000/v1
    timeout_seconds: 30
    api_key:
      mode: none
models:
  qwen3_local:
    name: qwen3_local
    provider: local_vllm
roles:
  supervisor:
    model: qwen3_local
"""
    _write(tmp_path / ".ai-loop/config/models.yaml", config)

    from devloop import cli as cli_module

    def _exec_stub(_prepared, environ=None, transport=None):
        return ModelPingExecutionResult(
            ok=True,
            attempted_transport=True,
            endpoint="http://localhost:8000/v1/chat/completions",
            transport="ok",
            error_message=None,
        )

    monkeypatch.setattr(cli_module, "execute_model_ping", _exec_stub)

    result = _invoke_model_ping_in_cwd(tmp_path, ["supervisor", "--allow-call"])

    assert result.exit_code == 0
    assert "result: ok" in result.stdout
    assert "resolved_model: qwen3_local" in result.stdout
    assert "provider: local_vllm" in result.stdout
    assert "attempted_transport: true" in result.stdout
    assert "transport: ok" in result.stdout
    assert "endpoint: http://localhost:8000/v1/chat/completions" in result.stdout


def test_model_ping_auth_present_true_without_secret_exposure(tmp_path: Path, monkeypatch) -> None:
    """Ping shows auth presence without printing secret values."""
    config = """schema_version: 1
policy:
  model_calls_allowed: true
providers:
  local_vllm:
    type: openai_compatible
    base_url: http://localhost:8000/v1
    api_key:
      mode: optional
      env: OPENAI_API_KEY
models:
  qwen3_local:
    name: qwen3_local
    provider: local_vllm
roles:
  supervisor:
    model: qwen3_local
"""
    _write(tmp_path / ".ai-loop/config/models.yaml", config)

    secret = "super-secret-token"
    from devloop import cli as cli_module

    def _exec_stub(_prepared, environ=None, transport=None):
        return ModelPingExecutionResult(
            ok=True,
            attempted_transport=True,
            endpoint="http://localhost:8000/v1/chat/completions",
            transport="ok",
            error_message=None,
        )

    monkeypatch.setattr(cli_module, "execute_model_ping", _exec_stub)

    result = _invoke_model_ping_in_cwd(
        tmp_path,
        ["supervisor", "--allow-call"],
        env={"OPENAI_API_KEY": secret},
    )

    assert result.exit_code == 0
    assert "auth_present: true" in result.stdout
    assert secret not in result.stdout


def test_model_ping_missing_config_does_not_create_config_file(tmp_path: Path) -> None:
    """Ping must not create models.yaml when it is absent."""
    config_path = tmp_path / ".ai-loop/config/models.yaml"
    assert not config_path.exists()

    result = _invoke_model_ping_in_cwd(tmp_path, ["supervisor", "--allow-call"])

    assert result.exit_code == 2
    assert not config_path.exists()


def test_model_ping_does_not_pass_transport_argument(tmp_path: Path, monkeypatch) -> None:
    """CLI should call backend without passing transport argument."""
    captured: dict[str, object] = {}

    from devloop.model_ping import ModelPingExecutionResult, ModelPingFinding, ModelPingPreparedRequest, ModelPingResult

    def _stub(project_root: Path, target: str, allow_call: bool, environ=None, transport=None):
        captured["project_root"] = project_root
        captured["target"] = target
        captured["allow_call"] = allow_call
        captured["environ"] = environ
        captured["transport"] = transport
        prepared = ModelPingPreparedRequest(
            target=target,
            resolved_model_key="qwen3_local",
            backend_model_name="qwen3_local",
            provider_key="local_vllm",
            provider_base_url="http://localhost:8000/v1",
            timeout_seconds=15,
            payload={"messages": [{"role": "user", "content": "ping"}], "max_tokens": 1, "temperature": 0},
            auth_mode="none",
            auth_env_name=None,
            auth_present=False,
        )
        return ModelPingResult(
            ok=True,
            attempted_transport=False,
            findings=[ModelPingFinding(severity="info", message="prepared")],
            prepared=prepared,
        )

    from devloop import cli as cli_module

    monkeypatch.setattr(cli_module, "run_model_ping", _stub)

    def _exec_stub(_prepared, environ=None, transport=None):
        return ModelPingExecutionResult(
            ok=True,
            attempted_transport=True,
            endpoint="http://localhost:8000/v1/chat/completions",
            transport="ok",
            error_message=None,
        )

    monkeypatch.setattr(cli_module, "execute_model_ping", _exec_stub)

    result = _invoke_model_ping_in_cwd(tmp_path, ["supervisor", "--allow-call"])

    assert result.exit_code == 0
    assert captured["target"] == "supervisor"
    assert captured["allow_call"] is True
    assert captured["transport"] is None


def test_model_ping_runtime_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    """Ping returns exit code 3 when transport execution fails."""
    config = """schema_version: 1
policy:
  model_calls_allowed: true
providers:
  local_vllm:
    type: openai_compatible
    base_url: http://localhost:8000/v1
    timeout_seconds: 30
    api_key:
      mode: none
models:
  qwen3_local:
    name: qwen3_local
    provider: local_vllm
roles:
  supervisor:
    model: qwen3_local
"""
    _write(tmp_path / ".ai-loop/config/models.yaml", config)

    from devloop import cli as cli_module

    def _exec_stub(_prepared, environ=None, transport=None):
        return ModelPingExecutionResult(
            ok=False,
            attempted_transport=True,
            endpoint="http://localhost:8000/v1/chat/completions",
            transport="error",
            error_message="transport request timed out",
        )

    monkeypatch.setattr(cli_module, "execute_model_ping", _exec_stub)

    result = _invoke_model_ping_in_cwd(tmp_path, ["supervisor", "--allow-call"])

    assert result.exit_code == 3
    assert "result: error" in result.stdout
    assert "attempted_transport: true" in result.stdout
    assert "transport: error" in result.stdout
    assert "transport request timed out" in result.stdout
