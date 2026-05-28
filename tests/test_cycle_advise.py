"""Tests for cycle advise preparation and execution backend."""

from __future__ import annotations

from pathlib import Path

from devloop.cycle_advise import SEVERITY_ERROR, run_cycle_advise


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _files_snapshot(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*")}


def _errors(result) -> list[str]:
    return [item.message for item in result.findings if item.severity == SEVERITY_ERROR]


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


def test_cycle_advise_executes_successfully_with_fake_transport(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _write(tmp_path / ".ai-loop/project.md", "project\n")
    _make_cycle(tmp_path, "c-001")
    _write(tmp_path / ".ai-loop/cycles/c-001/prompt.md", "prompt\n")

    def _fake_transport(url, payload, headers, timeout_seconds):
        assert url == "http://localhost:8000/v1/chat/completions"
        assert payload["model"] == "qwen3_local_backend"
        assert payload["temperature"] == 0
        assert isinstance(payload["messages"], list)
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers
        assert timeout_seconds == 15
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"- Keep scope focused."}}]}'

    result = run_cycle_advise(
        tmp_path,
        cycle_id="c-001",
        role="supervisor",
        allow_call=True,
        transport=_fake_transport,
    )

    assert result.ok is True
    assert result.attempted_transport is True
    assert result.prepared is not None
    assert result.execution is not None
    assert result.execution.ok is True
    assert result.execution.transport == "ok"
    assert result.execution.advisory_text == "- Keep scope focused."
    assert result.prepared.cycle_id == "c-001"
    assert result.prepared.role == "supervisor"
    assert result.prepared.resolved_model_key == "qwen3_local"
    assert result.prepared.backend_model_name == "qwen3_local_backend"
    assert result.prepared.provider_key == "local_vllm"
    assert ".ai-loop/project.md" in result.prepared.input_artifacts
    assert ".ai-loop/cycles/c-001/meta.yaml" in result.prepared.input_artifacts
    assert ".ai-loop/cycles/c-001/task.md" in result.prepared.input_artifacts
    assert ".ai-loop/cycles/c-001/prompt.md" in result.prepared.input_artifacts


def test_cycle_advise_transport_payload_shape_with_required_api_key(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        _valid_models_yaml(policy_allowed=True).replace(
            "mode: none",
            "mode: required\n      env: OPENAI_API_KEY",
        ),
    )
    _make_cycle(tmp_path, "c-001")
    captured: dict[str, object] = {}
    secret = "top-secret-token"

    def _fake_transport(url, payload, headers, timeout_seconds):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = dict(headers)
        captured["timeout"] = timeout_seconds
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"advisory text"}}]}'

    result = run_cycle_advise(
        tmp_path,
        cycle_id="c-001",
        role="supervisor",
        allow_call=True,
        environ={"OPENAI_API_KEY": secret},
        transport=_fake_transport,
    )

    assert result.ok is True
    assert result.prepared is not None
    assert result.prepared.auth_present is True
    assert captured["url"] == "http://localhost:8000/v1/chat/completions"
    assert "model" in captured["payload"]
    assert "messages" in captured["payload"]
    assert "Authorization" in captured["headers"]
    assert secret in captured["headers"]["Authorization"]
    assert secret not in " ".join(item.message for item in result.findings)


def test_cycle_advise_blocks_when_allow_call_missing(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")
    attempted = {"value": False}

    def _fake_transport(*_args):
        attempted["value"] = True
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"x"}}]}'

    result = run_cycle_advise(tmp_path, cycle_id="c-001", allow_call=False, transport=_fake_transport)

    assert result.ok is False
    assert result.attempted_transport is False
    assert attempted["value"] is False
    assert any("allow_call=True" in message for message in _errors(result))


def test_cycle_advise_blocks_when_policy_false(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=False))
    _make_cycle(tmp_path, "c-001")
    attempted = {"value": False}

    def _fake_transport(*_args):
        attempted["value"] = True
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"x"}}]}'

    result = run_cycle_advise(tmp_path, cycle_id="c-001", allow_call=True, transport=_fake_transport)

    assert result.ok is False
    assert result.attempted_transport is False
    assert attempted["value"] is False
    assert any("policy.model_calls_allowed" in message for message in _errors(result))


def test_cycle_advise_fails_when_config_missing_or_invalid(tmp_path: Path) -> None:
    attempted = {"value": False}

    def _fake_transport(*_args):
        attempted["value"] = True
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"x"}}]}'

    missing = run_cycle_advise(tmp_path, cycle_id="c-001", allow_call=True, transport=_fake_transport)
    assert missing.ok is False
    assert missing.attempted_transport is False
    assert attempted["value"] is False
    assert any("model config file is required for cycle advise" in message for message in _errors(missing))

    _write(tmp_path / ".ai-loop/config/models.yaml", "schema_version: 2\n")
    invalid = run_cycle_advise(tmp_path, cycle_id="c-001", allow_call=True, transport=_fake_transport)
    assert invalid.ok is False
    assert invalid.attempted_transport is False
    assert attempted["value"] is False
    assert any("model config is invalid" in message for message in _errors(invalid))


def test_cycle_advise_unknown_role_fails_before_transport(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")
    attempted = {"value": False}

    def _fake_transport(*_args):
        attempted["value"] = True
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"x"}}]}'

    result = run_cycle_advise(tmp_path, cycle_id="c-001", role="missing", allow_call=True, transport=_fake_transport)

    assert result.ok is False
    assert result.attempted_transport is False
    assert attempted["value"] is False
    assert any("unknown role: missing" in message for message in _errors(result))


def test_cycle_advise_missing_cycle_fails_before_transport(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    attempted = {"value": False}

    def _fake_transport(*_args):
        attempted["value"] = True
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"x"}}]}'

    result = run_cycle_advise(tmp_path, cycle_id="c-999", role="supervisor", allow_call=True, transport=_fake_transport)

    assert result.ok is False
    assert result.attempted_transport is False
    assert attempted["value"] is False
    assert any("cycle directory missing" in message for message in _errors(result))


def test_cycle_advise_runtime_failure_is_sanitized(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")

    def _fake_transport(*_args):
        raise TimeoutError("secret-token")

    result = run_cycle_advise(tmp_path, cycle_id="c-001", role="reviewer", allow_call=True, transport=_fake_transport)

    assert result.ok is False
    assert result.attempted_transport is True
    assert result.execution is not None
    assert result.execution.transport == "error"
    assert result.execution.error_message == "transport request timed out"
    assert "secret-token" not in (result.execution.error_message or "")


def test_cycle_advise_invalid_model_response_fails(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")

    def _fake_transport(*_args):
        return 200, b'{"choices":[{"message":{"role":"assistant"}}]}'

    result = run_cycle_advise(tmp_path, cycle_id="c-001", role="reviewer", allow_call=True, transport=_fake_transport)

    assert result.ok is False
    assert result.attempted_transport is True
    assert result.execution is not None
    assert result.execution.transport == "error"
    assert "assistant content" in (result.execution.error_message or "")


def test_cycle_advise_does_not_modify_files(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_models_yaml(policy_allowed=True))
    _make_cycle(tmp_path, "c-001")
    before = _files_snapshot(tmp_path)

    def _fake_transport(*_args):
        return 200, b'{"choices":[{"message":{"role":"assistant","content":"all good"}}]}'

    result = run_cycle_advise(tmp_path, cycle_id="c-001", role="reviewer", allow_call=True, transport=_fake_transport)
    after = _files_snapshot(tmp_path)

    assert result.ok is True
    assert result.attempted_transport is True
    assert before == after
