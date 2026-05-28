"""Tests for declarative model configuration parsing and validation."""

from __future__ import annotations

from pathlib import Path

from devloop.model_config import SEVERITY_ERROR, SEVERITY_WARNING, run_model_config_check


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _find_messages(result, severity: str) -> list[str]:
    return [item.message for item in result.findings if item.severity == severity]


def test_models_yaml_absent_is_optional_warning(tmp_path: Path) -> None:
    result = run_model_config_check(tmp_path)

    warnings = _find_messages(result, SEVERITY_WARNING)
    errors = _find_messages(result, SEVERITY_ERROR)

    assert result.file_present is False
    assert result.document == {}
    assert errors == []
    assert ".ai-loop/config/models.yaml" in warnings[0]


def test_models_yaml_invalid_yaml_reports_error(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", "models: [broken\n")

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert result.file_present is True
    assert result.document == {}
    assert any("invalid yaml" in message for message in errors)


def test_schema_version_must_be_one(tmp_path: Path) -> None:
    _write(tmp_path / ".ai-loop/config/models.yaml", "schema_version: 2\n")

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("schema_version must be 1" in message for message in errors)


def test_valid_minimal_config_has_no_errors(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
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
""",
    )

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert result.file_present is True
    assert errors == []


def test_provider_type_must_support_openai_compatible(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
providers:
  cloud:
    type: custom_backend
""",
    )

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("unsupported provider.type" in message for message in errors)


def test_api_key_mode_must_be_allowed_value(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
providers:
  local_vllm:
    type: openai_compatible
    api_key:
      mode: invalid
""",
    )

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("api_key.mode" in message for message in errors)


def test_model_must_reference_existing_provider(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
providers:
  local_vllm:
    type: openai_compatible
models:
  qwen3_local:
    provider: missing_provider
""",
    )

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("unknown provider reference" in message for message in errors)


def test_role_model_must_reference_existing_model(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
roles:
  supervisor:
    model: missing_model
""",
    )

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("unknown model reference" in message for message in errors)


def test_role_same_as_must_reference_existing_role(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
roles:
  reviewer:
    same_as: supervisor
""",
    )

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("unknown role reference" in message for message in errors)


def test_role_with_model_and_same_as_is_invalid(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
providers:
  local_vllm:
    type: openai_compatible
models:
  qwen3_local:
    provider: local_vllm
roles:
  supervisor:
    model: qwen3_local
    same_as: reviewer
  reviewer:
    model: qwen3_local
""",
    )

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("cannot define both model and same_as" in message for message in errors)


def test_required_api_key_env_name_missing_is_error(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
providers:
  cloud:
    type: openai_compatible
    api_key:
      mode: required
""",
    )

    result = run_model_config_check(tmp_path)

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("api_key.env is required" in message for message in errors)


def test_required_api_key_env_not_set_is_error(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
providers:
  cloud:
    type: openai_compatible
    api_key:
      mode: required
      env: OPENAI_API_KEY
""",
    )

    result = run_model_config_check(tmp_path, environ={})

    errors = _find_messages(result, SEVERITY_ERROR)
    assert any("environment variable is not set" in message for message in errors)


def test_required_api_key_env_set_is_valid(tmp_path: Path) -> None:
    _write(
        tmp_path / ".ai-loop/config/models.yaml",
        """\
schema_version: 1
providers:
  cloud:
    type: openai_compatible
    api_key:
      mode: required
      env: OPENAI_API_KEY
""",
    )

    result = run_model_config_check(tmp_path, environ={"OPENAI_API_KEY": "token"})

    errors = _find_messages(result, SEVERITY_ERROR)
    assert errors == []
