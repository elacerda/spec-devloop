"""Model configuration parsing and validation for declarative contracts."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"

MODELS_CONFIG_PATH = ".ai-loop/config/models.yaml"
SUPPORTED_PROVIDER_TYPES = {"openai_compatible"}
ALLOWED_API_KEY_MODES = {"none", "optional", "required"}


@dataclass(frozen=True)
class ModelConfigFinding:
    """Single finding emitted by model config validation.

    Parameters
    ----------
    severity
        Finding severity (`info`, `warning`, or `error`).
    message
        Human-readable explanation for the finding.
    location
        Dot path pointing to the relevant field, when applicable.
    """

    severity: str
    message: str
    location: str | None = None


@dataclass(frozen=True)
class ModelConfigResult:
    """Result for declarative model configuration validation.

    Parameters
    ----------
    config_path
        Project-relative config path inspected by the validator.
    file_present
        True when the config file exists.
    document
        Parsed YAML mapping. Empty when file is missing or invalid.
    findings
        Collected parser and validator findings.
    """

    config_path: str
    file_present: bool
    document: dict[str, Any]
    findings: list[ModelConfigFinding]


def run_model_config_check(
    project_root: Path,
    environ: Mapping[str, str] | None = None,
) -> ModelConfigResult:
    """Validate `.ai-loop/config/models.yaml` as an optional declarative contract.

    Parameters
    ----------
    project_root
        Filesystem root path of the project to inspect.
    environ
        Environment mapping used for `api_key.mode: required` checks.
        When omitted, uses `os.environ`.

    Returns
    -------
    ModelConfigResult
        Structured report with parsed document and validation findings.

    Notes
    -----
    This function is report-only and does not perform network calls or file writes.
    """

    findings: list[ModelConfigFinding] = []
    env_map = os.environ if environ is None else environ
    config_file = project_root / MODELS_CONFIG_PATH

    if not config_file.is_file():
        findings.append(
            ModelConfigFinding(
                severity=SEVERITY_WARNING,
                message=f"optional file missing: {MODELS_CONFIG_PATH}",
                location=MODELS_CONFIG_PATH,
            )
        )
        return ModelConfigResult(
            config_path=MODELS_CONFIG_PATH,
            file_present=False,
            document={},
            findings=findings,
        )

    parsed = _parse_yaml_file(config_file)
    if isinstance(parsed, str):
        findings.append(
            ModelConfigFinding(
                severity=SEVERITY_ERROR,
                message=f"invalid yaml: {MODELS_CONFIG_PATH}: {parsed}",
                location=MODELS_CONFIG_PATH,
            )
        )
        return ModelConfigResult(
            config_path=MODELS_CONFIG_PATH,
            file_present=True,
            document={},
            findings=findings,
        )

    findings.append(
        ModelConfigFinding(
            severity=SEVERITY_INFO,
            message=f"yaml parsed: {MODELS_CONFIG_PATH}",
            location=MODELS_CONFIG_PATH,
        )
    )
    findings.extend(_validate_document(parsed, env_map))
    return ModelConfigResult(
        config_path=MODELS_CONFIG_PATH,
        file_present=True,
        document=parsed,
        findings=findings,
    )


def _parse_yaml_file(path: Path) -> dict[str, Any] | str:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        return str(exc)

    if data is None:
        return {}
    if not isinstance(data, dict):
        return "yaml root must be a mapping"
    return data


def _validate_document(
    doc: dict[str, Any],
    environ: Mapping[str, str],
) -> list[ModelConfigFinding]:
    findings: list[ModelConfigFinding] = []

    schema_version = doc.get("schema_version")
    if schema_version != 1:
        findings.append(
            ModelConfigFinding(
                severity=SEVERITY_ERROR,
                message="schema_version must be 1",
                location="schema_version",
            )
        )

    policy = doc.get("policy")
    if policy is not None:
        if not isinstance(policy, dict):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message="policy must be a mapping",
                    location="policy",
                )
            )
        else:
            model_calls_allowed = policy.get("model_calls_allowed")
            if model_calls_allowed is not None and not isinstance(model_calls_allowed, bool):
                findings.append(
                    ModelConfigFinding(
                        severity=SEVERITY_ERROR,
                        message="policy.model_calls_allowed must be boolean",
                        location="policy.model_calls_allowed",
                    )
                )

    providers = doc.get("providers")
    provider_names: set[str] = set()
    if providers is not None:
        if not isinstance(providers, dict):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message="providers must be a mapping",
                    location="providers",
                )
            )
        else:
            provider_names = set(providers.keys())
            findings.extend(_validate_providers(providers, environ))

    models = doc.get("models")
    model_names: set[str] = set()
    if models is not None:
        if not isinstance(models, dict):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message="models must be a mapping",
                    location="models",
                )
            )
        else:
            model_names = set(models.keys())
            findings.extend(_validate_models(models, provider_names))

    roles = doc.get("roles")
    if roles is not None:
        if not isinstance(roles, dict):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message="roles must be a mapping",
                    location="roles",
                )
            )
        else:
            findings.extend(_validate_roles(roles, model_names))

    return findings


def _validate_providers(
    providers: dict[str, Any],
    environ: Mapping[str, str],
) -> list[ModelConfigFinding]:
    findings: list[ModelConfigFinding] = []

    for provider_name, provider_data in providers.items():
        base_location = f"providers.{provider_name}"
        if not isinstance(provider_data, dict):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"provider entry must be a mapping: {provider_name}",
                    location=base_location,
                )
            )
            continue

        provider_type = provider_data.get("type")
        if not isinstance(provider_type, str):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"provider.type must be a string: {provider_name}",
                    location=f"{base_location}.type",
                )
            )
        elif provider_type not in SUPPORTED_PROVIDER_TYPES:
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=(
                        "unsupported provider.type: "
                        f"{provider_name}: {provider_type}"
                    ),
                    location=f"{base_location}.type",
                )
            )

        if provider_type == "openai_compatible":
            base_url = provider_data.get("base_url")
            if not isinstance(base_url, str) or not base_url.strip():
                findings.append(
                    ModelConfigFinding(
                        severity=SEVERITY_ERROR,
                        message="provider.base_url is required for openai_compatible",
                        location=f"{base_location}.base_url",
                    )
                )

        timeout_seconds = provider_data.get("timeout_seconds")
        if timeout_seconds is not None:
            is_number = isinstance(timeout_seconds, (int, float))
            is_bool = isinstance(timeout_seconds, bool)
            if is_bool or not is_number or timeout_seconds <= 0:
                findings.append(
                    ModelConfigFinding(
                        severity=SEVERITY_ERROR,
                        message="provider.timeout_seconds must be a positive number",
                        location=f"{base_location}.timeout_seconds",
                    )
                )

        api_key = provider_data.get("api_key")
        if api_key is None:
            continue
        if not isinstance(api_key, dict):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"provider.api_key must be a mapping: {provider_name}",
                    location=f"{base_location}.api_key",
                )
            )
            continue

        mode = api_key.get("mode")
        if mode not in ALLOWED_API_KEY_MODES:
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=(
                        "provider.api_key.mode must be one of "
                        "`none`, `optional`, `required`"
                    ),
                    location=f"{base_location}.api_key.mode",
                )
            )
            continue

        if mode == "required":
            env_name = api_key.get("env")
            if not isinstance(env_name, str) or not env_name.strip():
                findings.append(
                    ModelConfigFinding(
                        severity=SEVERITY_ERROR,
                        message=f"api_key.env is required when mode=required: {provider_name}",
                        location=f"{base_location}.api_key.env",
                    )
                )
                continue
            env_value = environ.get(env_name)
            if env_value is None or env_value == "":
                findings.append(
                    ModelConfigFinding(
                        severity=SEVERITY_ERROR,
                        message=(
                            "required api key environment variable is not set: "
                            f"{env_name}; it must be exported in the shell and present in "
                            "the process environment before running devloop; .env is not "
                            "automatically loaded (load manually with: "
                            "set -a; source .env; set +a)"
                        ),
                        location=f"{base_location}.api_key.env",
                    )
                )

    return findings


def _validate_models(
    models: dict[str, Any],
    provider_names: set[str],
) -> list[ModelConfigFinding]:
    findings: list[ModelConfigFinding] = []

    for model_name, model_data in models.items():
        base_location = f"models.{model_name}"
        if not isinstance(model_data, dict):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"model entry must be a mapping: {model_name}",
                    location=base_location,
                )
            )
            continue

        resolved_name = model_data.get("name")
        if not isinstance(resolved_name, str) or not resolved_name.strip():
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message="model.name must be a non-empty string",
                    location=f"{base_location}.name",
                )
            )

        provider_name = model_data.get("provider")
        if not isinstance(provider_name, str):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"model.provider must be a string: {model_name}",
                    location=f"{base_location}.provider",
                )
            )
            continue
        if provider_name not in provider_names:
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=(
                        f"unknown provider reference in model {model_name}: "
                        f"{provider_name}"
                    ),
                    location=f"{base_location}.provider",
                )
            )

    return findings


def _validate_roles(
    roles: dict[str, Any],
    model_names: set[str],
) -> list[ModelConfigFinding]:
    findings: list[ModelConfigFinding] = []

    for role_name, role_data in roles.items():
        base_location = f"roles.{role_name}"
        if not isinstance(role_data, dict):
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"role entry must be a mapping: {role_name}",
                    location=base_location,
                )
            )
            continue

        model_name = role_data.get("model")
        same_as = role_data.get("same_as")
        has_model = isinstance(model_name, str)
        has_same_as = isinstance(same_as, str)

        if has_model and has_same_as:
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"role cannot define both model and same_as: {role_name}",
                    location=base_location,
                )
            )
            continue

        if not has_model and not has_same_as:
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"role must define model or same_as: {role_name}",
                    location=base_location,
                )
            )
            continue

        if has_model and model_name not in model_names:
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=(
                        f"unknown model reference in role {role_name}: {model_name}"
                    ),
                    location=f"{base_location}.model",
                )
            )

        if has_same_as and same_as not in roles:
            findings.append(
                ModelConfigFinding(
                    severity=SEVERITY_ERROR,
                    message=f"unknown role reference in role {role_name}: {same_as}",
                    location=f"{base_location}.same_as",
                )
            )

    return findings
