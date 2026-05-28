"""Tests for model ping preparation and execution."""

from __future__ import annotations

from pathlib import Path

from devloop.model_ping import SEVERITY_ERROR, execute_model_ping, run_model_ping


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _errors(result) -> list[str]:
    return [item.message for item in result.findings if item.severity == SEVERITY_ERROR]


def _prepare(tmp_path: Path, *, policy: bool = True, api_key_mode: str = "none", api_key_env: str | None = None):
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        _valid_config(policy=policy, api_key_mode=api_key_mode, api_key_env=api_key_env),
    )
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True, environ={"OPENAI_API_KEY": "secret"})
    assert result.ok is True
    assert result.prepared is not None
    return result.prepared


def test_missing_config_blocks_ping(tmp_path: Path) -> None:
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True)
    assert result.ok is False
    assert result.prepared is None
    assert result.attempted_transport is False
    assert any("model config file is required for ping" in msg for msg in _errors(result))


def test_invalid_config_blocks_ping(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", "schema_version: 2\n")
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True)
    assert result.ok is False
    assert result.prepared is None
    assert result.attempted_transport is False


def test_unknown_target_errors(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_config(policy=True))
    result = run_model_ping(tmp_path, target="missing", allow_call=True)
    assert result.ok is False
    assert any("unknown target" in msg for msg in _errors(result))


def test_role_wins_over_model_name_collision(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _collision_config(policy=True))
    result = run_model_ping(tmp_path, target="shared", allow_call=True)
    assert result.ok is True
    assert result.prepared is not None
    assert result.prepared.resolved_model_key == "from_role"


def test_direct_model_target_resolves(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_config(policy=True))
    result = run_model_ping(tmp_path, target="qwen3_local", allow_call=True)
    assert result.ok is True
    assert result.prepared is not None
    assert result.prepared.resolved_model_key == "qwen3_local"


def test_policy_false_blocks_even_with_allow_call(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_config(policy=False))
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True)
    assert result.ok is False
    assert result.prepared is None
    assert any("model_calls_allowed" in msg for msg in _errors(result))


def test_allow_call_false_blocks_even_with_policy_true(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_config(policy=True))
    result = run_model_ping(tmp_path, target="supervisor", allow_call=False)
    assert result.ok is False
    assert result.prepared is None
    assert any("allow_call=True" in msg for msg in _errors(result))


def test_openai_compatible_prepares_successfully(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_config(policy=True))
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True)
    assert result.ok is True
    assert result.prepared is not None
    assert result.prepared.provider_key == "local_vllm"


def test_unsupported_provider_type_errors(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_config(policy=True, provider_type="other"))
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True)
    assert result.ok is False
    assert any("unsupported provider" in msg for msg in _errors(result))


def test_api_key_none_requires_no_env(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_config(policy=True, api_key_mode="none"))
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True, environ={})
    assert result.ok is True
    assert result.prepared is not None
    assert result.prepared.auth_mode == "none"
    assert result.prepared.auth_env_name is None
    assert result.prepared.auth_present is False


def test_api_key_optional_works_with_env_absent_and_present(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        _valid_config(policy=True, api_key_mode="optional", api_key_env="OPENAI_API_KEY"),
    )
    absent = run_model_ping(tmp_path, target="supervisor", allow_call=True, environ={})
    present = run_model_ping(
        tmp_path,
        target="supervisor",
        allow_call=True,
        environ={"OPENAI_API_KEY": "secret"},
    )
    assert absent.ok is True and present.ok is True
    assert absent.prepared is not None and present.prepared is not None
    assert absent.prepared.auth_present is False
    assert present.prepared.auth_present is True


def test_api_key_required_errors_when_env_missing(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        _valid_config(policy=True, api_key_mode="required", api_key_env="OPENAI_API_KEY"),
    )
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True, environ={})
    assert result.ok is False
    assert any("required api key environment variable is not set" in msg for msg in _errors(result))


def test_api_key_required_succeeds_with_env_without_secret_exposure(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        _valid_config(policy=True, api_key_mode="required", api_key_env="OPENAI_API_KEY"),
    )
    result = run_model_ping(
        tmp_path,
        target="supervisor",
        allow_call=True,
        environ={"OPENAI_API_KEY": "super-secret"},
    )
    assert result.ok is True
    assert result.prepared is not None
    assert "super-secret" not in " ".join(item.message for item in result.findings)


def test_prepared_payload_defaults_and_timeout_default(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _valid_config(policy=True, timeout=None))
    result = run_model_ping(tmp_path, target="supervisor", allow_call=True)
    assert result.ok is True
    assert result.prepared is not None
    assert result.prepared.payload["messages"][0]["content"] == "ping"
    assert result.prepared.payload["max_tokens"] == 1
    assert result.prepared.payload["temperature"] == 0
    assert result.prepared.timeout_seconds == 15


def test_same_as_cycle_detected(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", _same_as_cycle_config(policy=True))
    result = run_model_ping(tmp_path, target="a", allow_call=True)
    assert result.ok is False
    assert any("role alias cycle detected" in msg for msg in _errors(result))


def test_execute_model_ping_success_with_choices(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path)

    def _fake_transport(url, payload, headers, timeout_seconds):
        assert url == "http://localhost:8000/v1/chat/completions"
        assert payload["model"] == "qwen3_local"
        assert payload["messages"] == [{"role": "user", "content": "ping"}]
        assert payload["max_tokens"] == 1
        assert payload["temperature"] == 0
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers
        assert timeout_seconds == prepared.timeout_seconds
        return 200, b'{"id":"x","choices":[{"index":0}]}'

    result = execute_model_ping(prepared, environ={}, transport=_fake_transport)
    assert result.ok is True
    assert result.attempted_transport is True
    assert result.transport == "ok"


def test_execute_model_ping_http_non_2xx_fails(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path)

    def _fake_transport(*_args):
        return 500, b"{}"

    result = execute_model_ping(prepared, transport=_fake_transport)
    assert result.ok is False
    assert result.transport == "error"
    assert "status 500" in (result.error_message or "")


def test_execute_model_ping_timeout_fails_sanitized(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path)

    def _fake_transport(*_args):
        raise TimeoutError("secret-token")

    result = execute_model_ping(prepared, transport=_fake_transport)
    assert result.ok is False
    assert result.error_message == "transport request timed out"
    assert "secret-token" not in (result.error_message or "")


def test_execute_model_ping_runtime_network_fails_sanitized(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path)

    def _fake_transport(*_args):
        raise OSError("leaked-secret")

    result = execute_model_ping(prepared, transport=_fake_transport)
    assert result.ok is False
    assert result.error_message == "transport request failed due to runtime/network error"


def test_execute_model_ping_invalid_json_fails(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path)

    def _fake_transport(*_args):
        return 200, b"not-json"

    result = execute_model_ping(prepared, transport=_fake_transport)
    assert result.ok is False
    assert result.error_message == "transport response is not valid JSON"


def test_execute_model_ping_missing_choices_fails(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path)

    def _fake_transport(*_args):
        return 200, b'{"id":"x"}'

    result = execute_model_ping(prepared, transport=_fake_transport)
    assert result.ok is False
    assert "missing required field: choices" in (result.error_message or "")


def test_endpoint_builder_handles_trailing_slash(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        _valid_config(policy=True, base_url="http://localhost:8000/v1/"),
    )
    prep = run_model_ping(tmp_path, target="supervisor", allow_call=True)
    assert prep.prepared is not None

    def _fake_transport(url, *_args):
        assert url == "http://localhost:8000/v1/chat/completions"
        return 200, b'{"choices":[]}'

    result = execute_model_ping(prep.prepared, transport=_fake_transport)
    assert result.ok is True




def test_endpoint_builder_strips_query_and_fragment(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        _valid_config(policy=True, base_url="http://localhost:8000/v1?api_key=secret#fragment"),
    )
    prep = run_model_ping(tmp_path, target="supervisor", allow_call=True)
    assert prep.prepared is not None

    def _fake_transport(url, *_args):
        assert url == "http://localhost:8000/v1/chat/completions"
        assert "secret" not in url
        assert "?" not in url
        assert "#" not in url
        return 200, b'{"choices":[]}'

    result = execute_model_ping(prep.prepared, transport=_fake_transport)
    assert result.ok is True
    assert "secret" not in result.endpoint
    assert "?" not in result.endpoint
    assert "#" not in result.endpoint

def test_auth_header_behavior_none_optional_required(tmp_path: Path) -> None:
    captured: list[dict[str, str]] = []

    def _fake_transport(_url, _payload, headers, _timeout):
        captured.append(dict(headers))
        return 200, b'{"choices":[]}'

    none_prepared = _prepare(tmp_path, api_key_mode="none")
    execute_model_ping(none_prepared, environ={"OPENAI_API_KEY": "token"}, transport=_fake_transport)
    assert "Authorization" not in captured[-1]

    optional_prepared = _prepare(tmp_path, api_key_mode="optional", api_key_env="OPENAI_API_KEY")
    execute_model_ping(optional_prepared, environ={}, transport=_fake_transport)
    assert "Authorization" not in captured[-1]

    execute_model_ping(optional_prepared, environ={"OPENAI_API_KEY": "opt-token"}, transport=_fake_transport)
    assert captured[-1]["Authorization"] == "Bearer opt-token"

    required_prepared = _prepare(tmp_path, api_key_mode="required", api_key_env="OPENAI_API_KEY")
    execute_model_ping(required_prepared, environ={"OPENAI_API_KEY": "req-token"}, transport=_fake_transport)
    assert captured[-1]["Authorization"] == "Bearer req-token"


def _valid_config(
    policy: bool,
    provider_type: str = "openai_compatible",
    api_key_mode: str = "none",
    api_key_env: str | None = None,
    timeout: int | None = 30,
    base_url: str = "http://localhost:8000/v1",
) -> str:
    timeout_line = f"    timeout_seconds: {timeout}\n" if timeout is not None else ""
    env_line = f"      env: {api_key_env}\n" if api_key_env is not None else ""
    return f"""\
schema_version: 1
policy:
  model_calls_allowed: {str(policy).lower()}
providers:
  local_vllm:
    type: {provider_type}
    base_url: {base_url}
{timeout_line}    api_key:
      mode: {api_key_mode}
{env_line}models:
  qwen3_local:
    provider: local_vllm
roles:
  supervisor:
    model: qwen3_local
"""


def _collision_config(policy: bool) -> str:
    return f"""\
schema_version: 1
policy:
  model_calls_allowed: {str(policy).lower()}
providers:
  local_vllm:
    type: openai_compatible
    base_url: http://localhost:8000/v1
    api_key:
      mode: none
models:
  shared:
    provider: local_vllm
  from_role:
    provider: local_vllm
roles:
  shared:
    model: from_role
"""


def _same_as_cycle_config(policy: bool) -> str:
    return f"""\
schema_version: 1
policy:
  model_calls_allowed: {str(policy).lower()}
providers:
  local_vllm:
    type: openai_compatible
    base_url: http://localhost:8000/v1
    api_key:
      mode: none
models:
  qwen3_local:
    provider: local_vllm
roles:
  a:
    same_as: b
  b:
    same_as: a
"""
