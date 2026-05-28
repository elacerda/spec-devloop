"""Backend-only model ping preparation layer."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from devloop.model_config import run_model_config_check

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"

DEFAULT_TIMEOUT_SECONDS = 15
SUPPORTED_PROVIDER_TYPE = "openai_compatible"


@dataclass(frozen=True)
class ModelPingFinding:
    """Single finding for model ping preparation.

    Parameters
    ----------
    severity
        Finding severity (`info`, `warning`, or `error`).
    message
        Human-readable message suitable for future CLI rendering.
    location
        Dot-path style location when applicable.
    code
        Optional stable code for future machine-readable mapping.
    """

    severity: str
    message: str
    location: str | None = None
    code: str | None = None


@dataclass(frozen=True)
class ModelPingPreparedRequest:
    """Sanitized prepared request metadata for a future ping call.

    Parameters
    ----------
    target
        Input role-or-model target requested by caller.
    resolved_model_key
        Model key resolved from role/model lookup.
    backend_model_name
        Backend model identifier (`models.<key>.name` when present, else key).
    provider_key
        Provider key for the resolved model.
    provider_base_url
        Provider base URL for a future transport layer.
    timeout_seconds
        Finite timeout budget for future transport calls.
    payload
        Minimal payload intent (`ping`, `max_tokens: 1`, `temperature: 0`).
    auth_mode
        API key mode (`none`, `optional`, `required`).
    auth_env_name
        Environment variable name used for auth resolution, when configured.
    auth_present
        True when an auth token is present in environment; token value is never stored.
    """

    target: str
    resolved_model_key: str
    backend_model_name: str
    provider_key: str
    provider_base_url: str
    timeout_seconds: int
    payload: dict[str, Any]
    auth_mode: str
    auth_env_name: str | None
    auth_present: bool


@dataclass(frozen=True)
class ModelPingResult:
    """Result for backend-only model ping preparation.

    Parameters
    ----------
    ok
        True when preparation succeeds and request metadata is ready.
    attempted_transport
        Always False in this patch; transport invocation is deferred.
    findings
        Collected findings describing success/failure reasons.
    prepared
        Sanitized request metadata when preparation succeeds.
    """

    ok: bool
    attempted_transport: bool
    findings: list[ModelPingFinding]
    prepared: ModelPingPreparedRequest | None


def run_model_ping(
    project_root: Path,
    target: str,
    allow_call: bool,
    environ: Mapping[str, str] | None = None,
    transport: Any | None = None,
) -> ModelPingResult:
    """Prepare a future model ping request from local configuration only.

    Parameters
    ----------
    project_root
        Root project path used to load `.ai-loop/config/models.yaml`.
    target
        Role name or model key to resolve (`role` takes precedence over `model`).
    allow_call
        Explicit runtime authorization gate. Must be True for preparation success.
    environ
        Environment source for API key checks. Defaults to `os.environ`.
    transport
        Reserved for future transport injection. Ignored in this patch.

    Returns
    -------
    ModelPingResult
        Preparation result with sanitized request metadata and findings.
    """

    del transport
    findings: list[ModelPingFinding] = []
    env_map = os.environ if environ is None else environ

    config = run_model_config_check(project_root, environ=env_map)
    config_errors = [f for f in config.findings if f.severity == SEVERITY_ERROR]
    if not config.file_present:
        findings.append(
            ModelPingFinding(
                SEVERITY_ERROR,
                "model config file is required for ping: .ai-loop/config/models.yaml",
                code="config_missing",
            )
        )
        return ModelPingResult(False, False, findings, None)
    if config_errors:
        findings.append(
            ModelPingFinding(
                SEVERITY_ERROR,
                "model config is invalid; run `devloop model check`",
                code="config_invalid",
            )
        )
        for item in config_errors:
            findings.append(
                ModelPingFinding(
                    SEVERITY_ERROR,
                    item.message,
                    location=item.location,
                    code="config_detail",
                )
            )
        return ModelPingResult(False, False, findings, None)

    doc = config.document
    policy = doc.get("policy")
    model_calls_allowed = policy.get("model_calls_allowed") if isinstance(policy, dict) else None
    if model_calls_allowed is not True:
        findings.append(
            ModelPingFinding(
                SEVERITY_ERROR,
                "policy.model_calls_allowed must be true for model ping",
                location="policy.model_calls_allowed",
                code="policy_blocked",
            )
        )
        return ModelPingResult(False, False, findings, None)
    if allow_call is not True:
        findings.append(
            ModelPingFinding(
                SEVERITY_ERROR,
                "explicit runtime authorization required: allow_call=True",
                code="allow_call_missing",
            )
        )
        return ModelPingResult(False, False, findings, None)

    roles = doc.get("roles", {})
    models = doc.get("models", {})
    providers = doc.get("providers", {})

    resolved_model_key = _resolve_target_to_model_key(target, roles, models, findings)
    if resolved_model_key is None:
        return ModelPingResult(False, False, findings, None)

    model_data = models.get(resolved_model_key, {})
    if not isinstance(model_data, dict):
        findings.append(ModelPingFinding(SEVERITY_ERROR, f"invalid model entry: {resolved_model_key}"))
        return ModelPingResult(False, False, findings, None)

    provider_key = model_data.get("provider")
    provider_data = providers.get(provider_key) if isinstance(provider_key, str) else None
    if not isinstance(provider_key, str) or not isinstance(provider_data, dict):
        findings.append(
            ModelPingFinding(
                SEVERITY_ERROR,
                f"unknown provider for model {resolved_model_key}",
                location=f"models.{resolved_model_key}.provider",
                code="provider_missing",
            )
        )
        return ModelPingResult(False, False, findings, None)

    provider_type = provider_data.get("type")
    if provider_type != SUPPORTED_PROVIDER_TYPE:
        findings.append(
            ModelPingFinding(
                SEVERITY_ERROR,
                f"unsupported provider type for ping: {provider_type}",
                location=f"providers.{provider_key}.type",
                code="provider_unsupported",
            )
        )
        return ModelPingResult(False, False, findings, None)

    base_url = provider_data.get("base_url")
    if not isinstance(base_url, str) or not base_url.strip():
        findings.append(
            ModelPingFinding(
                SEVERITY_ERROR,
                "provider base_url is required for ping preparation",
                location=f"providers.{provider_key}.base_url",
                code="provider_base_url_missing",
            )
        )
        return ModelPingResult(False, False, findings, None)

    auth_mode, auth_env_name, auth_present = _resolve_auth(provider_key, provider_data, env_map, findings)
    if auth_mode is None:
        return ModelPingResult(False, False, findings, None)

    backend_model_name = model_data.get("name")
    if not isinstance(backend_model_name, str) or not backend_model_name.strip():
        backend_model_name = resolved_model_key

    timeout_seconds = provider_data.get("timeout_seconds")
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
        timeout_seconds = DEFAULT_TIMEOUT_SECONDS

    prepared = ModelPingPreparedRequest(
        target=target,
        resolved_model_key=resolved_model_key,
        backend_model_name=backend_model_name,
        provider_key=provider_key,
        provider_base_url=base_url,
        timeout_seconds=timeout_seconds,
        payload={
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        },
        auth_mode=auth_mode,
        auth_env_name=auth_env_name,
        auth_present=auth_present,
    )
    findings.append(ModelPingFinding(SEVERITY_INFO, "model ping request prepared"))
    return ModelPingResult(True, False, findings, prepared)


def _resolve_target_to_model_key(
    target: str,
    roles: Any,
    models: Any,
    findings: list[ModelPingFinding],
) -> str | None:
    if isinstance(roles, dict) and target in roles:
        return _resolve_role_model_key(target, roles, findings)
    if isinstance(models, dict) and target in models:
        return target
    findings.append(ModelPingFinding(SEVERITY_ERROR, f"unknown target: {target}", code="target_unknown"))
    return None


def _resolve_role_model_key(
    role_name: str,
    roles: dict[str, Any],
    findings: list[ModelPingFinding],
) -> str | None:
    visited: set[str] = set()
    current = role_name
    while True:
        if current in visited:
            findings.append(
                ModelPingFinding(
                    SEVERITY_ERROR,
                    f"role alias cycle detected at role: {current}",
                    location=f"roles.{current}.same_as",
                    code="role_cycle",
                )
            )
            return None
        visited.add(current)

        role_data = roles.get(current)
        if not isinstance(role_data, dict):
            findings.append(ModelPingFinding(SEVERITY_ERROR, f"invalid role entry: {current}", code="role_invalid"))
            return None

        model_name = role_data.get("model")
        if isinstance(model_name, str):
            return model_name

        same_as = role_data.get("same_as")
        if isinstance(same_as, str):
            if same_as not in roles:
                findings.append(
                    ModelPingFinding(
                        SEVERITY_ERROR,
                        f"unknown role alias target: {same_as}",
                        location=f"roles.{current}.same_as",
                        code="role_alias_missing",
                    )
                )
                return None
            current = same_as
            continue

        findings.append(
            ModelPingFinding(
                SEVERITY_ERROR,
                f"role does not resolve to a model: {current}",
                location=f"roles.{current}",
                code="role_unresolved",
            )
        )
        return None


def _resolve_auth(
    provider_key: str,
    provider_data: dict[str, Any],
    environ: Mapping[str, str],
    findings: list[ModelPingFinding],
) -> tuple[str | None, str | None, bool]:
    api_key = provider_data.get("api_key")
    if not isinstance(api_key, dict):
        return "none", None, False

    mode = api_key.get("mode")
    if mode == "none":
        return "none", None, False
    if mode == "optional":
        env_name = api_key.get("env")
        if isinstance(env_name, str) and env_name.strip():
            return "optional", env_name, bool(environ.get(env_name))
        return "optional", None, False
    if mode == "required":
        env_name = api_key.get("env")
        if not isinstance(env_name, str) or not env_name.strip():
            findings.append(
                ModelPingFinding(
                    SEVERITY_ERROR,
                    f"required API key env name missing for provider: {provider_key}",
                    location=f"providers.{provider_key}.api_key.env",
                    code="auth_env_missing",
                )
            )
            return None, None, False
        if not environ.get(env_name):
            findings.append(
                ModelPingFinding(
                    SEVERITY_ERROR,
                    f"required API key environment variable is not set: {env_name}",
                    location=f"providers.{provider_key}.api_key.env",
                    code="auth_env_unset",
                )
            )
            return None, env_name, False
        return "required", env_name, True

    findings.append(
        ModelPingFinding(
            SEVERITY_ERROR,
            f"unsupported api_key mode for provider: {provider_key}",
            location=f"providers.{provider_key}.api_key.mode",
            code="auth_mode_invalid",
        )
    )
    return None, None, False
