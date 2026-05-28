"""Preparation-only backend for `devloop cycle advise`."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from devloop.cycle_check import run_cycle_check
from devloop.model_config import run_model_config_check

SEVERITY_INFO = "info"
SEVERITY_ERROR = "error"
SUPPORTED_PROVIDER_TYPE = "openai_compatible"

ALLOWED_OPTIONAL_INPUTS = (
    ".ai-loop/project.md",
    "meta.yaml",
    "task.md",
    "plan.md",
    "prompt.md",
    "summary.md",
    "report.md",
)


@dataclass(frozen=True)
class CycleAdviseFinding:
    """Single finding for cycle advise preparation.

    Parameters
    ----------
    severity
        Finding severity (`info` or `error`).
    message
        Human-readable message for CLI rendering.
    location
        Dot-path style location for config findings when applicable.
    code
        Stable code for blocked/error classification.
    """

    severity: str
    message: str
    location: str | None = None
    code: str | None = None


@dataclass(frozen=True)
class CycleAdvisePreparedRequest:
    """Sanitized advisory request metadata prepared for future transport.

    Parameters
    ----------
    cycle_id
        Validated cycle identifier.
    role
        Resolved role name requested by the caller.
    resolved_model_key
        Model key resolved from `roles.<role>.model`.
    backend_model_name
        Provider backend model name (`models.<key>.name`), or model key fallback.
    provider_key
        Provider key for the resolved model.
    input_artifacts
        Relative artifact paths considered during preparation.
    """

    cycle_id: str
    role: str
    resolved_model_key: str
    backend_model_name: str
    provider_key: str
    input_artifacts: tuple[str, ...]


@dataclass(frozen=True)
class CycleAdviseResult:
    """Result for preparation-only `cycle advise` backend flow.

    Parameters
    ----------
    ok
        `True` when preparation succeeded.
    attempted_transport
        Always `False` in this patch because transport is not implemented.
    findings
        Validation/preparation findings.
    prepared
        Sanitized prepared request metadata on success.
    """

    ok: bool
    attempted_transport: bool
    findings: list[CycleAdviseFinding]
    prepared: CycleAdvisePreparedRequest | None


def run_cycle_advise(
    project_root: Path,
    cycle_id: str,
    role: str = "supervisor",
    allow_call: bool = False,
    environ: Mapping[str, str] | None = None,
    transport: Any | None = None,
) -> CycleAdviseResult:
    """Prepare a cycle advisory request without any model transport call.

    Parameters
    ----------
    project_root
        Project root used to load cycle artifacts and `.ai-loop/config/models.yaml`.
    cycle_id
        Cycle identifier expected as a direct child of `.ai-loop/cycles/`.
    role
        Role name to resolve in model config. Defaults to `supervisor`.
    allow_call
        Explicit runtime authorization gate. Must be `True`.
    environ
        Environment map used by config validation. Defaults to `os.environ`.
    transport
        Reserved for future transport integration. Ignored in this patch.

    Returns
    -------
    CycleAdviseResult
        Preparation-only result with sanitized metadata.

    Notes
    -----
    This function is preparation-only and does not perform network I/O, file
    mutation, shell execution, agent execution, or persistence.
    """

    del transport
    env_map = os.environ if environ is None else environ
    findings: list[CycleAdviseFinding] = []

    config = run_model_config_check(project_root, environ=env_map)
    config_errors = [item for item in config.findings if item.severity == SEVERITY_ERROR]

    if not config.file_present:
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message="model config file is required for cycle advise: .ai-loop/config/models.yaml",
                code="config_missing",
            )
        )
        return CycleAdviseResult(False, False, findings, None)

    if config_errors:
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message="model config is invalid; run `devloop model check`",
                code="config_invalid",
            )
        )
        for item in config_errors:
            findings.append(
                CycleAdviseFinding(
                    severity=SEVERITY_ERROR,
                    message=item.message,
                    location=item.location,
                    code="config_detail",
                )
            )
        return CycleAdviseResult(False, False, findings, None)

    doc = config.document
    policy = doc.get("policy")
    model_calls_allowed = policy.get("model_calls_allowed") if isinstance(policy, dict) else None
    if model_calls_allowed is not True:
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message="policy.model_calls_allowed must be true for cycle advise",
                location="policy.model_calls_allowed",
                code="policy_blocked",
            )
        )
        return CycleAdviseResult(False, False, findings, None)
    if allow_call is not True:
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message="explicit runtime authorization required: allow_call=True",
                code="allow_call_missing",
            )
        )
        return CycleAdviseResult(False, False, findings, None)

    cycle_check = run_cycle_check(project_root, cycle_id)
    if cycle_check.errors:
        for error in cycle_check.errors:
            findings.append(CycleAdviseFinding(severity=SEVERITY_ERROR, message=error, code="cycle_invalid"))
        return CycleAdviseResult(False, False, findings, None)

    roles = doc.get("roles", {})
    models = doc.get("models", {})
    providers = doc.get("providers", {})

    resolved_model_key = _resolve_role_model_key(role, roles, findings)
    if resolved_model_key is None:
        return CycleAdviseResult(False, False, findings, None)

    model_data = models.get(resolved_model_key) if isinstance(models, dict) else None
    if not isinstance(model_data, dict):
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message=f"unknown model reference: {resolved_model_key}",
                location=f"roles.{role}.model",
                code="model_unknown",
            )
        )
        return CycleAdviseResult(False, False, findings, None)

    provider_key = model_data.get("provider")
    provider_data = providers.get(provider_key) if isinstance(provider_key, str) and isinstance(providers, dict) else None
    if not isinstance(provider_key, str) or not isinstance(provider_data, dict):
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message=f"unknown provider for model {resolved_model_key}",
                location=f"models.{resolved_model_key}.provider",
                code="provider_missing",
            )
        )
        return CycleAdviseResult(False, False, findings, None)

    provider_type = provider_data.get("type")
    if provider_type != SUPPORTED_PROVIDER_TYPE:
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message=f"unsupported provider type for cycle advise: {provider_type}",
                location=f"providers.{provider_key}.type",
                code="provider_unsupported",
            )
        )
        return CycleAdviseResult(False, False, findings, None)

    backend_model_name = model_data.get("name")
    if not isinstance(backend_model_name, str) or not backend_model_name.strip():
        backend_model_name = resolved_model_key

    input_artifacts = _collect_input_artifacts(project_root, cycle_id)
    findings.append(CycleAdviseFinding(severity=SEVERITY_INFO, message="cycle advise request prepared"))
    prepared = CycleAdvisePreparedRequest(
        cycle_id=cycle_id,
        role=role,
        resolved_model_key=resolved_model_key,
        backend_model_name=backend_model_name,
        provider_key=provider_key,
        input_artifacts=input_artifacts,
    )
    return CycleAdviseResult(True, False, findings, prepared)


def _resolve_role_model_key(
    role_name: str,
    roles: Any,
    findings: list[CycleAdviseFinding],
) -> str | None:
    if not isinstance(roles, dict) or role_name not in roles:
        findings.append(CycleAdviseFinding(SEVERITY_ERROR, f"unknown role: {role_name}", code="role_unknown"))
        return None

    visited: set[str] = set()
    current = role_name
    while True:
        if current in visited:
            findings.append(
                CycleAdviseFinding(
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
            findings.append(CycleAdviseFinding(SEVERITY_ERROR, f"invalid role entry: {current}", code="role_invalid"))
            return None

        model_name = role_data.get("model")
        if isinstance(model_name, str):
            return model_name

        same_as = role_data.get("same_as")
        if isinstance(same_as, str):
            if same_as not in roles:
                findings.append(
                    CycleAdviseFinding(
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
            CycleAdviseFinding(
                SEVERITY_ERROR,
                f"role does not resolve to a model: {current}",
                location=f"roles.{current}",
                code="role_unresolved",
            )
        )
        return None


def _collect_input_artifacts(project_root: Path, cycle_id: str) -> tuple[str, ...]:
    """Collect existing artifacts from the conservative cycle advise allowlist."""

    cycle_dir = project_root / ".ai-loop" / "cycles" / cycle_id
    artifacts: list[str] = []

    project_md = project_root / ".ai-loop" / "project.md"
    if project_md.is_file():
        artifacts.append(".ai-loop/project.md")

    for rel in ALLOWED_OPTIONAL_INPUTS:
        if rel == ".ai-loop/project.md":
            continue
        path = cycle_dir / rel
        if path.is_file():
            artifacts.append(str(path.relative_to(project_root)))

    return tuple(artifacts)
