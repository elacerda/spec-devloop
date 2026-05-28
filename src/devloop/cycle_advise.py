"""Backend preparation and transport execution for `devloop cycle advise`."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from devloop.cycle_check import run_cycle_check
from devloop.model_config import run_model_config_check
from devloop.model_resolution import resolve_role_model_key

SEVERITY_INFO = "info"
SEVERITY_ERROR = "error"
SUPPORTED_PROVIDER_TYPE = "openai_compatible"
DEFAULT_TIMEOUT_SECONDS = 15

SYSTEM_PROMPT = (
    "You are the supervisor advisor for spec-devloop, a local-first, file-based, "
    "human-governed development cycle tool. Return advisory text only. "
    "Ground your advice only in the provided project and cycle artifacts. "
    "The canonical project state directory is `.ai-loop`; do not introduce alternate "
    "project structures unless they appear in the provided artifacts. "
    "Do not invent missing files, evidence, commands that were run, test results, "
    "or implementation details. The current allowlisted cycle artifacts are "
    "`meta.yaml`, `task.md`, `plan.md`, `prompt.md`, `summary.md`, and `report.md`; "
    "prefer these names when recommending artifact updates, and label any new "
    "artifact name as a future schema extension rather than a current requirement. "
    "For validation commands, prefer repository commands that are already part of "
    "the workflow, such as `devloop model check`, `devloop cycle check <cycle-id>`, "
    "`devloop cycle advise <cycle-id> --role supervisor --allow-call`, "
    "`python3 -m pytest -q`, `git diff --check`, and `git status --short`; "
    "do not recommend external tools unless they appear in the provided artifacts. "
    "Do not claim the repository lacks executable code or configuration solely "
    "because the current cycle has sparse artifacts. Distinguish transport/configuration validation "
    "from feature implementation work. Prefer concise, actionable guidance. "
    "Use these sections: Summary, Readiness, Risks, Recommended next microtask, "
    "Validation commands, Open questions. "
    "Do not execute code, run commands, mutate files, call agents, or suggest "
    "autonomous execution. Do not expose hidden chain-of-thought."
)

ALLOWED_OPTIONAL_INPUTS = (
    ".ai-loop/project.md",
    "meta.yaml",
    "task.md",
    "plan.md",
    "prompt.md",
    "summary.md",
    "report.md",
)

MAX_ARTIFACT_CHARS = 4000
MAX_CONTEXT_CHARS = 20000

CycleAdviseTransport = Callable[[str, dict[str, Any], dict[str, str], int], tuple[int, bytes]]


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
    """Sanitized request metadata for cycle advisory transport execution.

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
    provider_base_url
        OpenAI-compatible base URL used to derive `/chat/completions` endpoint.
    timeout_seconds
        Finite request timeout budget in seconds.
    auth_mode
        API key mode (`none`, `optional`, `required`).
    auth_env_name
        Environment variable name used for API key lookup when configured.
    auth_present
        True when auth environment variable is currently set; token value is not stored.
    input_artifacts
        Relative artifact paths considered during preparation.
    advisory_context
        Sanitized user-context text built only from allowlisted cycle artifacts.
    """

    cycle_id: str
    role: str
    resolved_model_key: str
    backend_model_name: str
    provider_key: str
    provider_base_url: str
    timeout_seconds: int
    auth_mode: str
    auth_env_name: str | None
    auth_present: bool
    input_artifacts: tuple[str, ...]
    advisory_context: str


@dataclass(frozen=True)
class CycleAdviseExecutionResult:
    """Result of cycle advise transport execution.

    Parameters
    ----------
    ok
        True when transport succeeds and response includes assistant advisory text.
    attempted_transport
        True when an HTTP request attempt was made.
    transport
        Transport status label (`ok` or `error`).
    endpoint
        Sanitized endpoint used for execution.
    advisory_text
        Assistant advisory text content from `choices[0].message.content`.
    error_code
        Stable sanitized error code for runtime/response failures.
    error_message
        Human-readable sanitized execution error.
    """

    ok: bool
    attempted_transport: bool
    transport: str
    endpoint: str
    advisory_text: str | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class CycleAdviseResult:
    """Result for `cycle advise` preparation and optional transport execution.

    Parameters
    ----------
    ok
        True when preparation succeeds and transport returns valid advisory text.
    attempted_transport
        True when model transport was attempted.
    findings
        Validation and preparation findings.
    prepared
        Sanitized prepared request metadata on preparation success.
    execution
        Execution result when transport was attempted.
    """

    ok: bool
    attempted_transport: bool
    findings: list[CycleAdviseFinding]
    prepared: CycleAdvisePreparedRequest | None
    execution: CycleAdviseExecutionResult | None


def run_cycle_advise(
    project_root: Path,
    cycle_id: str,
    role: str = "supervisor",
    allow_call: bool = False,
    environ: Mapping[str, str] | None = None,
    transport: CycleAdviseTransport | None = None,
) -> CycleAdviseResult:
    """Prepare and execute an explicitly authorized cycle advisory model call.

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
        Environment map used by config validation and auth token resolution.
        Defaults to `os.environ`.
    transport
        Optional transport function for tests. It must accept
        `(url, payload, headers, timeout_seconds)` and return
        `(status_code, response_body_bytes)`.

    Returns
    -------
    CycleAdviseResult
        Structured outcome for preparation or execution paths.

    Notes
    -----
    This function is advisory-only and does not perform file mutation, shell
    execution, agent execution, or persistence of prompt/response payloads.
    """

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
        return CycleAdviseResult(False, False, findings, None, None)

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
        return CycleAdviseResult(False, False, findings, None, None)

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
        return CycleAdviseResult(False, False, findings, None, None)
    if allow_call is not True:
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message="explicit runtime authorization required: allow_call=True",
                code="allow_call_missing",
            )
        )
        return CycleAdviseResult(False, False, findings, None, None)

    cycle_check = run_cycle_check(project_root, cycle_id)
    if cycle_check.errors:
        for error in cycle_check.errors:
            findings.append(CycleAdviseFinding(severity=SEVERITY_ERROR, message=error, code="cycle_invalid"))
        return CycleAdviseResult(False, False, findings, None, None)

    roles = doc.get("roles", {})
    models = doc.get("models", {})
    providers = doc.get("providers", {})

    resolved_model_key = resolve_role_model_key(
        role_name=role,
        roles=roles,
        add_finding=lambda severity, message, location, code: findings.append(
            CycleAdviseFinding(severity, message, location=location, code=code)
        ),
        severity_error=SEVERITY_ERROR,
    )
    if resolved_model_key is None:
        return CycleAdviseResult(False, False, findings, None, None)

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
        return CycleAdviseResult(False, False, findings, None, None)

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
        return CycleAdviseResult(False, False, findings, None, None)

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
        return CycleAdviseResult(False, False, findings, None, None)

    base_url = provider_data.get("base_url")
    if not isinstance(base_url, str) or not base_url.strip():
        findings.append(
            CycleAdviseFinding(
                severity=SEVERITY_ERROR,
                message="provider base_url is required for cycle advise",
                location=f"providers.{provider_key}.base_url",
                code="provider_base_url_missing",
            )
        )
        return CycleAdviseResult(False, False, findings, None, None)

    auth_mode, auth_env_name, auth_present = _resolve_auth(provider_key, provider_data, env_map, findings)
    if auth_mode is None:
        return CycleAdviseResult(False, False, findings, None, None)

    backend_model_name = model_data.get("name")
    if not isinstance(backend_model_name, str) or not backend_model_name.strip():
        backend_model_name = resolved_model_key

    timeout_seconds = provider_data.get("timeout_seconds")
    if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
        timeout_seconds = DEFAULT_TIMEOUT_SECONDS

    input_artifacts = _collect_input_artifacts(project_root, cycle_id)
    advisory_context = _build_advisory_context(project_root, cycle_id, role, input_artifacts)

    findings.append(CycleAdviseFinding(severity=SEVERITY_INFO, message="cycle advise request prepared"))
    prepared = CycleAdvisePreparedRequest(
        cycle_id=cycle_id,
        role=role,
        resolved_model_key=resolved_model_key,
        backend_model_name=backend_model_name,
        provider_key=provider_key,
        provider_base_url=base_url,
        timeout_seconds=timeout_seconds,
        auth_mode=auth_mode,
        auth_env_name=auth_env_name,
        auth_present=auth_present,
        input_artifacts=input_artifacts,
        advisory_context=advisory_context,
    )

    execution = execute_cycle_advise(prepared, environ=env_map, transport=transport)
    if not execution.ok:
        return CycleAdviseResult(False, True, findings, prepared, execution)

    findings.append(CycleAdviseFinding(severity=SEVERITY_INFO, message="cycle advise advisory received"))
    return CycleAdviseResult(True, True, findings, prepared, execution)


def execute_cycle_advise(
    prepared: CycleAdvisePreparedRequest,
    environ: Mapping[str, str] | None = None,
    transport: CycleAdviseTransport | None = None,
) -> CycleAdviseExecutionResult:
    """Execute the model transport for an already-prepared cycle advisory request.

    Parameters
    ----------
    prepared
        Sanitized request metadata produced by `run_cycle_advise`.
    environ
        Environment source for auth token resolution at execution time.
        Defaults to `os.environ`.
    transport
        Optional transport function for tests. It must accept
        `(url, payload, headers, timeout_seconds)` and return
        `(status_code, response_body_bytes)`.

    Returns
    -------
    CycleAdviseExecutionResult
        Execution status with sanitized endpoint and advisory/error content.
    """

    env_map = os.environ if environ is None else environ
    endpoint = _build_chat_completions_endpoint(prepared.provider_base_url)
    payload = {
        "model": prepared.backend_model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prepared.advisory_context},
        ],
        "temperature": 0,
        "max_tokens": 800,
    }
    headers = {"Content-Type": "application/json"}

    token = None
    if prepared.auth_env_name:
        token = env_map.get(prepared.auth_env_name)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        executor = transport if transport is not None else _default_http_transport
        status_code, response_body = executor(endpoint, payload, headers, prepared.timeout_seconds)
        if status_code != 200:
            return CycleAdviseExecutionResult(
                ok=False,
                attempted_transport=True,
                transport="error",
                endpoint=endpoint,
                error_code="transport_http_status",
                error_message=f"transport request failed with status {status_code}",
            )

        try:
            response_json = json.loads(response_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return CycleAdviseExecutionResult(
                ok=False,
                attempted_transport=True,
                transport="error",
                endpoint=endpoint,
                error_code="response_invalid_json",
                error_message="transport response is not valid JSON",
            )

        advisory_text = _extract_assistant_content(response_json)
        if advisory_text is None:
            return CycleAdviseExecutionResult(
                ok=False,
                attempted_transport=True,
                transport="error",
                endpoint=endpoint,
                error_code="response_invalid_shape",
                error_message="transport response is missing assistant content",
            )

        return CycleAdviseExecutionResult(
            ok=True,
            attempted_transport=True,
            transport="ok",
            endpoint=endpoint,
            advisory_text=advisory_text,
        )
    except TimeoutError:
        return CycleAdviseExecutionResult(
            ok=False,
            attempted_transport=True,
            transport="error",
            endpoint=endpoint,
            error_code="transport_timeout",
            error_message="transport request timed out",
        )
    except Exception:
        return CycleAdviseExecutionResult(
            ok=False,
            attempted_transport=True,
            transport="error",
            endpoint=endpoint,
            error_code="transport_runtime_error",
            error_message="transport request failed due to runtime/network error",
        )


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


def _build_advisory_context(
    project_root: Path,
    cycle_id: str,
    role: str,
    input_artifacts: tuple[str, ...],
) -> str:
    """Build deterministic advisory context from allowlisted artifacts only."""

    chunks: list[str] = [
        "request: cycle_advisory",
        f"cycle_id: {cycle_id}",
        f"role: {role}",
        "project: spec-devloop",
        "canonical_project_state: .ai-loop",
        "role_contract: supervisor advisor for a local file-based development cycle",
        "constraints: advisory-only; stdout-only; no code execution; no file mutation; no shell execution; no agent execution",
        "grounding: use only the artifacts listed below; do not invent missing files, directories, specs, evidence, or test results",
        "allowed_cycle_artifacts: meta.yaml; task.md; plan.md; prompt.md; summary.md; report.md",
        "artifact_guidance: prefer allowed cycle artifacts for recommendations; label any new artifact as future schema extension, not a current requirement",
        "validation_command_guidance: prefer devloop model check; devloop cycle check <cycle-id>; devloop cycle advise <cycle-id> --role supervisor --allow-call; python3 -m pytest -q; git diff --check; git status --short",
        "output_format: Summary; Readiness; Risks; Recommended next microtask; Validation commands; Open questions",
    ]

    if not input_artifacts:
        chunks.append("artifacts: (none)")
        return "\n".join(chunks)

    chunks.append("artifacts:")
    for rel_path in input_artifacts:
        chunks.append(f"- {rel_path}")

    chunks.append("artifact_contents:")
    for rel_path in input_artifacts:
        content = _read_artifact_text(project_root / rel_path)
        chunks.append(f"[{rel_path}]\n{content}")

    context = "\n".join(chunks)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]
    return context


def _read_artifact_text(path: Path) -> str:
    """Read an advisory artifact as UTF-8 text with deterministic truncation."""

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "(unreadable artifact)"

    if len(text) > MAX_ARTIFACT_CHARS:
        return f"{text[:MAX_ARTIFACT_CHARS]}\n... [truncated]"
    return text


def _extract_assistant_content(response_json: Any) -> str | None:
    """Extract assistant content from OpenAI-compatible choices response."""

    if not isinstance(response_json, dict):
        return None
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    message = first.get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        return None
    return content.strip()


def _build_chat_completions_endpoint(base_url: str) -> str:
    """Build `/chat/completions` endpoint from provider base URL.

    Query strings and fragments are stripped before appending the endpoint path.
    """

    parsed = urllib_parse.urlsplit(base_url.strip())
    clean_path = parsed.path.rstrip("/")
    endpoint_path = f"{clean_path}/chat/completions"
    sanitized = parsed._replace(path=endpoint_path, query="", fragment="")
    return urllib_parse.urlunsplit(sanitized)


def _default_http_transport(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout_seconds: int,
) -> tuple[int, bytes]:
    """Execute an HTTP POST to an OpenAI-compatible endpoint using urllib."""

    body = json.dumps(payload).encode("utf-8")
    request = urllib_request.Request(url=url, data=body, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(response.getcode())
            return status_code, response.read()
    except urllib_error.HTTPError as exc:
        return int(exc.code), b""


def _resolve_auth(
    provider_key: str,
    provider_data: dict[str, Any],
    environ: Mapping[str, str],
    findings: list[CycleAdviseFinding],
) -> tuple[str | None, str | None, bool]:
    """Resolve provider auth configuration without persisting token values."""

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
                CycleAdviseFinding(
                    severity=SEVERITY_ERROR,
                    message=f"required API key env name missing for provider: {provider_key}",
                    location=f"providers.{provider_key}.api_key.env",
                    code="auth_env_missing",
                )
            )
            return None, None, False
        if not environ.get(env_name):
            findings.append(
                CycleAdviseFinding(
                    severity=SEVERITY_ERROR,
                    message=f"required API key environment variable is not set: {env_name}",
                    location=f"providers.{provider_key}.api_key.env",
                    code="auth_env_unset",
                )
            )
            return None, env_name, False
        return "required", env_name, True

    findings.append(
        CycleAdviseFinding(
            severity=SEVERITY_ERROR,
            message=f"unsupported api_key mode for provider: {provider_key}",
            location=f"providers.{provider_key}.api_key.mode",
            code="auth_mode_invalid",
        )
    )
    return None, None, False
