"""Tests for `devloop cycle advise` CLI command."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from devloop.cli import app

runner = CliRunner()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _invoke_in_cwd(cwd: Path, args: list[str]) -> Any:
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["cycle", "advise", *args], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def _valid_models_yaml(policy_allowed: bool = True) -> str:
    allowed = "true" if policy_allowed else "false"
    return f"""\
schema_version: 1
policy:
  model_calls_allowed: {allowed}
providers:
  local_vllm:
    type: openai_compatible
    base_url: http://localhost:8000/v1
    api_key:
      mode: none
models:
  qwen3_local:
    name: qwen3_local_backend
    provider: local_vllm
roles:
  supervisor:
    model: qwen3_local
  reviewer:
    model: qwen3_local
"""


def _make_cycle(tmp_path: Path, cycle_id: str = "c-001") -> None:
    cycle_dir = tmp_path / ".ai-loop/cycles" / cycle_id
    _write(
        cycle_dir / "meta.yaml",
        f"schema_version: '0'\ncycle_id: {cycle_id}\ncreated_at: '2026-05-28'\nstatus: planned\n",
    )
    _write(cycle_dir / "task.md", "task\n")
    _write(cycle_dir / "report.md", "report\n")


def test_cycle_advise_success_output_prepared(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _write(tmp_path / ".ai-loop/project.md", "project\n")
    _make_cycle(tmp_path, "c-001")
    _write(tmp_path / ".ai-loop/cycles/c-001/summary.md", "summary\n")
    from devloop import cycle_advise as advise_module

    def _fake_transport(_url, _payload, _headers, _timeout):
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"- Focus the next validation step."}}]}'

    monkeypatch.setattr(advise_module, "_default_http_transport", _fake_transport)

    result = _invoke_in_cwd(tmp_path, ["c-001", "--allow-call"])

    assert result.exit_code == 0
    assert "cycle_id: c-001" in result.stdout
    assert "role: supervisor" in result.stdout
    assert "result: ok" in result.stdout
    assert "resolved_model: qwen3_local" in result.stdout
    assert "backend_model: qwen3_local_backend" in result.stdout
    assert "provider: local_vllm" in result.stdout
    assert "attempted_transport: true" in result.stdout
    assert "transport: ok" in result.stdout
    assert "safety: no files modified" in result.stdout
    assert "advisory:" in result.stdout
    assert "- Focus the next validation step." in result.stdout


def test_cycle_advise_missing_allow_call_returns_blocked(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["c-001"])

    assert result.exit_code == 2
    assert "result: blocked" in result.stdout
    assert "attempted_transport: false" in result.stdout


def test_cycle_advise_policy_false_returns_blocked(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=False))
    _make_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["c-001", "--allow-call"])

    assert result.exit_code == 2
    assert "result: blocked" in result.stdout
    assert "policy.model_calls_allowed" in result.stdout
    assert "attempted_transport: false" in result.stdout


def test_cycle_advise_unknown_role_returns_error_two(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["c-001", "--role", "missing", "--allow-call"])

    assert result.exit_code == 2
    assert "result: error" in result.stdout
    assert "unknown role: missing" in result.stdout
    assert "attempted_transport: false" in result.stdout


def test_cycle_advise_missing_cycle_returns_error_two(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))

    result = _invoke_in_cwd(tmp_path, ["c-999", "--allow-call"])

    assert result.exit_code == 2
    assert "result: error" in result.stdout
    assert "cycle directory missing" in result.stdout
    assert "attempted_transport: false" in result.stdout


def test_cycle_advise_does_not_print_secret_values(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")
    secret = "very-secret-value"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    from devloop import cycle_advise as advise_module

    def _fake_transport(_url, _payload, _headers, _timeout):
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"safe advisory"}}]}'

    monkeypatch.setattr(advise_module, "_default_http_transport", _fake_transport)

    result = _invoke_in_cwd(tmp_path, ["c-001", "--allow-call"])

    assert result.exit_code == 0
    assert secret not in result.stdout
    assert "Authorization" not in result.stdout
    assert '"messages"' not in result.stdout
    assert '"model"' not in result.stdout


def test_cycle_advise_transport_runtime_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")
    from devloop import cycle_advise as advise_module

    def _fake_transport(*_args):
        raise TimeoutError("super-secret")

    monkeypatch.setattr(advise_module, "_default_http_transport", _fake_transport)
    result = _invoke_in_cwd(tmp_path, ["c-001", "--allow-call"])

    assert result.exit_code == 3
    assert "result: error" in result.stdout
    assert "attempted_transport: true" in result.stdout
    assert "transport: error" in result.stdout
    assert "transport request timed out" in result.stdout
    assert "super-secret" not in result.stdout


def test_cycle_advise_invalid_model_response_returns_three(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")
    from devloop import cycle_advise as advise_module

    def _fake_transport(_url, _payload, _headers, _timeout):
        return 200, b'{"choices":[{"message":{"role":"assistant"}}]}'

    monkeypatch.setattr(advise_module, "_default_http_transport", _fake_transport)
    result = _invoke_in_cwd(tmp_path, ["c-001", "--allow-call"])

    assert result.exit_code == 3
    assert "result: error" in result.stdout
    assert "attempted_transport: true" in result.stdout
    assert "transport: error" in result.stdout
    assert "assistant content" in result.stdout
