"""Doctor command implementation for MVP-0 local specification validation."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from devloop.model_config import run_model_config_check

SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_ERROR = "error"

DEFAULT_EXIT_CODES = {
    "ok": 0,
    "validation_error": 2,
    "internal_failure": 3,
}

REQUIRED_FILES = [
    ".ai-loop/project.md",
    ".ai-loop/architecture.md",
    ".ai-loop/protocol.md",
    ".ai-loop/config/commands.yaml",
]

FALLBACK_OPTIONAL_FILES = [
    ".ai-loop/specification_lifecycle.md",
    ".ai-loop/config/providers.yaml",
    ".ai-loop/config/adapters.yaml",
    ".ai-loop/config/allowed_paths.yaml",
]

MANAGED_DIRECTORIES = [".ai-loop/cycles", ".ai-loop/state"]


@dataclass(frozen=True)
class Finding:
    """Single doctor finding.

    Parameters
    ----------
    severity
        One of ``info``, ``warning``, or ``error``.
    message
        Human-readable report message.
    """

    severity: str
    message: str


@dataclass(frozen=True)
class DoctorResult:
    """Result from running doctor checks.

    Parameters
    ----------
    findings
        Collected validation findings.
    exit_codes
        Effective exit code mapping.
    """

    findings: list[Finding]
    exit_codes: dict[str, int]


def run_doctor(project_root: Path) -> DoctorResult:
    """Run MVP-0 doctor checks on a project root.

    Parameters
    ----------
    project_root
        Filesystem path for the project to inspect.

    Returns
    -------
    DoctorResult
        Findings and configured exit code mapping.

    Notes
    -----
    This function is report-only and does not modify files.
    """

    findings: list[Finding] = []
    yaml_docs: dict[str, dict[str, Any]] = {}

    for rel_path in REQUIRED_FILES:
        full_path = project_root / rel_path
        if full_path.is_file():
            findings.append(Finding(SEVERITY_INFO, f"required file present: {rel_path}"))
        else:
            findings.append(Finding(SEVERITY_ERROR, f"required file missing: {rel_path}"))

    for config_file in sorted((project_root / ".ai-loop/config").glob("*.yaml")):
        rel = str(config_file.relative_to(project_root))
        parsed = _parse_yaml_file(config_file)
        if isinstance(parsed, dict):
            yaml_docs[rel] = parsed
            findings.append(Finding(SEVERITY_INFO, f"yaml parsed: {rel}"))
        else:
            findings.append(Finding(SEVERITY_ERROR, f"invalid yaml: {rel}: {parsed}"))

    # Integrate model config check (optional, report-only)
    model_config_result = run_model_config_check(project_root)
    for finding in model_config_result.findings:
        findings.append(Finding(finding.severity, f"model config: {finding.message}"))

    commands_doc = yaml_docs.get(".ai-loop/config/commands.yaml")
    optional_files = FALLBACK_OPTIONAL_FILES
    managed_dirs = MANAGED_DIRECTORIES
    exit_codes = dict(DEFAULT_EXIT_CODES)

    if isinstance(commands_doc, dict):
        optional_files = _extract_optional_files(commands_doc)
        managed_dirs = _extract_managed_dirs(commands_doc)
        exit_codes = _extract_exit_codes(commands_doc)

    for rel_path in optional_files:
        if (project_root / rel_path).exists():
            findings.append(Finding(SEVERITY_INFO, f"optional file present: {rel_path}"))
        else:
            findings.append(Finding(SEVERITY_WARNING, f"optional file missing: {rel_path}"))

    for rel_path in managed_dirs:
        if (project_root / rel_path).is_dir():
            findings.append(Finding(SEVERITY_INFO, f"managed directory present: {rel_path}"))
        else:
            findings.append(Finding(SEVERITY_WARNING, f"managed directory missing: {rel_path}"))

    findings.extend(_validate_known_schemas(yaml_docs))
    findings.extend(_git_findings(project_root))

    return DoctorResult(findings=findings, exit_codes=exit_codes)


def calculate_exit_code(result: DoctorResult) -> int:
    """Calculate process exit code from doctor findings.

    Parameters
    ----------
    result
        Doctor execution result.

    Returns
    -------
    int
        ``validation_error`` code when any ``error`` exists, otherwise ``ok``.
    """

    has_errors = any(item.severity == SEVERITY_ERROR for item in result.findings)
    key = "validation_error" if has_errors else "ok"
    return int(result.exit_codes.get(key, DEFAULT_EXIT_CODES[key]))


def _parse_yaml_file(path: Path) -> dict[str, Any] | str:
    """Parse a YAML file and return mapping or parse error text."""

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        return str(exc)

    if data is None:
        return {}
    if not isinstance(data, dict):
        return "yaml root must be a mapping"
    return data


def _extract_optional_files(commands_doc: dict[str, Any]) -> list[str]:
    specs = commands_doc.get("specs")
    if isinstance(specs, dict) and isinstance(specs.get("optional"), list):
        return [str(item) for item in specs["optional"]]
    return FALLBACK_OPTIONAL_FILES


def _extract_managed_dirs(commands_doc: dict[str, Any]) -> list[str]:
    dirs = commands_doc.get("managed_directories")
    if isinstance(dirs, list) and dirs:
        return [str(item) for item in dirs]
    return MANAGED_DIRECTORIES


def _extract_exit_codes(commands_doc: dict[str, Any]) -> dict[str, int]:
    doctor = commands_doc.get("doctor")
    if not isinstance(doctor, dict):
        return dict(DEFAULT_EXIT_CODES)
    raw = doctor.get("exit_codes")
    if not isinstance(raw, dict):
        return dict(DEFAULT_EXIT_CODES)

    result = dict(DEFAULT_EXIT_CODES)
    for key in result:
        value = raw.get(key)
        if isinstance(value, int):
            result[key] = value
    return result


def _validate_required_keys(
    doc: dict[str, Any],
    key_list_name: str,
    container_name: str,
    schema_name: str,
) -> list[Finding]:
    findings: list[Finding] = []
    schema = doc.get("schema")
    if not isinstance(schema, dict):
        return [Finding(SEVERITY_ERROR, f"schema missing in {schema_name}")]

    required_keys = schema.get(key_list_name)
    container = doc.get(container_name) if container_name else doc

    if not isinstance(required_keys, list):
        return [Finding(SEVERITY_ERROR, f"{key_list_name} missing in {schema_name}")]
    if not isinstance(container, dict):
        message = f"{container_name or 'root'} must be mapping in {schema_name}"
        return [Finding(SEVERITY_ERROR, message)]

    for key in required_keys:
        if key not in container:
            message = f"missing key in {schema_name}: {container_name}.{key}"
            findings.append(Finding(SEVERITY_ERROR, message))
    return findings


def _validate_known_schemas(yaml_docs: dict[str, dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []

    commands_path = ".ai-loop/config/commands.yaml"
    providers_path = ".ai-loop/config/providers.yaml"
    adapters_path = ".ai-loop/config/adapters.yaml"
    allowed_paths = ".ai-loop/config/allowed_paths.yaml"

    if commands_path in yaml_docs:
        doc = yaml_docs[commands_path]
        findings.extend(_validate_required_keys(doc, "required_top_level", "", "commands.yaml"))
        findings.extend(
            _validate_required_keys(doc, "project_required", "project", "commands.yaml")
        )
        findings.extend(_validate_required_keys(doc, "specs_required", "specs", "commands.yaml"))
        findings.extend(_validate_required_keys(doc, "git_required", "git", "commands.yaml"))
        findings.extend(
            _validate_required_keys(doc, "execution_required", "execution", "commands.yaml")
        )

    if providers_path in yaml_docs:
        doc = yaml_docs[providers_path]
        findings.extend(_validate_required_keys(doc, "required_top_level", "", "providers.yaml"))
        findings.extend(_validate_required_keys(doc, "policy_required", "policy", "providers.yaml"))
        providers = doc.get("providers")
        default_provider = doc.get("default_provider")
        if isinstance(providers, dict) and isinstance(default_provider, str):
            entry = providers.get(default_provider)
            if not isinstance(entry, dict):
                findings.append(
                    Finding(SEVERITY_ERROR, "default provider key missing in providers.yaml")
                )
            elif entry.get("enabled") is not True:
                findings.append(
                    Finding(
                        SEVERITY_ERROR,
                        "default provider must be enabled in providers.yaml",
                    )
                )

    if adapters_path in yaml_docs:
        doc = yaml_docs[adapters_path]
        findings.extend(_validate_required_keys(doc, "required_top_level", "", "adapters.yaml"))
        findings.extend(_validate_required_keys(doc, "policy_required", "policy", "adapters.yaml"))
        adapters = doc.get("adapters")
        default_adapter = doc.get("default_adapter")
        if isinstance(adapters, dict) and isinstance(default_adapter, str):
            entry = adapters.get(default_adapter)
            if not isinstance(entry, dict):
                findings.append(
                    Finding(SEVERITY_ERROR, "default adapter key missing in adapters.yaml")
                )
            elif entry.get("enabled") is not True:
                findings.append(
                    Finding(
                        SEVERITY_ERROR,
                        "default adapter must be enabled in adapters.yaml",
                    )
                )

    if allowed_paths in yaml_docs:
        doc = yaml_docs[allowed_paths]
        findings.extend(
            _validate_required_keys(doc, "required_top_level", "", "allowed_paths.yaml")
        )

        path_sets = doc.get("path_sets")
        cycle_permissions = doc.get("cycle_permissions")
        precedence = doc.get("precedence")

        if isinstance(path_sets, dict):
            schema = doc.get("schema")
            if isinstance(schema, dict) and isinstance(schema.get("path_sets_required"), list):
                for key in schema["path_sets_required"]:
                    if key not in path_sets:
                        message = f"missing path set in allowed_paths.yaml: {key}"
                        findings.append(Finding(SEVERITY_ERROR, message))

        if isinstance(cycle_permissions, dict) and isinstance(path_sets, dict):
            for cycle_name, rule in cycle_permissions.items():
                if not isinstance(rule, dict):
                    message = f"cycle rule must be mapping: {cycle_name}"
                    findings.append(Finding(SEVERITY_ERROR, message))
                    continue
                allow = rule.get("allow")
                deny = rule.get("deny")
                if not isinstance(allow, list) or not isinstance(deny, list):
                    message = (
                        "cycle rule must define allow and deny lists: "
                        f"{cycle_name}"
                    )
                    findings.append(Finding(SEVERITY_ERROR, message))
                    continue
                for set_name in [*allow, *deny]:
                    if set_name not in path_sets:
                        message = (
                            f"unknown path set reference in {cycle_name}: "
                            f"{set_name}"
                        )
                        findings.append(Finding(SEVERITY_ERROR, message))

        if isinstance(precedence, dict):
            rules = precedence.get("rules")
            if not isinstance(rules, dict):
                findings.append(
                    Finding(SEVERITY_ERROR, "precedence.rules missing in allowed_paths.yaml")
                )
            else:
                for key in (
                    "explicit_deny_over_allow",
                    "more_specific_pattern_over_general_pattern",
                    "foundational_specs_immutable_in_normal_cycles",
                ):
                    if rules.get(key) is not True:
                        findings.append(
                            Finding(SEVERITY_ERROR, f"precedence rule must be true: {key}")
                        )

    return findings


def _git_findings(project_root: Path) -> list[Finding]:
    """Collect git-related warnings according to MVP-0 contract."""

    cmd_repo = ["git", "rev-parse", "--is-inside-work-tree"]
    try:
        repo = subprocess.run(
            cmd_repo,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return [Finding(SEVERITY_WARNING, "git executable not found")]

    if repo.returncode != 0 or repo.stdout.strip().lower() != "true":
        return [Finding(SEVERITY_WARNING, "git repository not detected")]

    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if dirty.returncode != 0:
        return [Finding(SEVERITY_WARNING, "unable to inspect git worktree status")]

    if dirty.stdout.strip():
        return [
            Finding(SEVERITY_INFO, "git repository detected"),
            Finding(SEVERITY_WARNING, "git worktree is dirty"),
        ]

    return [
        Finding(SEVERITY_INFO, "git repository detected"),
        Finding(SEVERITY_INFO, "git worktree is clean"),
    ]
