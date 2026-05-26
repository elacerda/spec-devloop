"""Backend report-only summary for `devloop cycle summary <cycle-id>` in MVP-0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from devloop.cycle_check import (
    REQUIRED_CYCLE_FILES,
    run_cycle_check,
)

OPTIONAL_CYCLE_FILES = ["plan.md", "evidence.md"]


@dataclass(frozen=True)
class CycleSummaryResult:
    """Result of cycle summary generation.

    Parameters
    ----------
    cycle_id
        Cycle identifier provided by the caller.
    status
        Status value from meta.yaml, or None if unavailable.
    created_at
        Created_at value from meta.yaml, or None if unavailable.
    required_files
        Mapping of required filename to presence status.
    optional_files
        Mapping of optional filename to presence status.
    errors
        Validation error messages.
    """

    cycle_id: str
    status: str | None
    created_at: str | None
    required_files: dict[str, bool]
    optional_files: dict[str, bool]
    errors: list[str]


def run_cycle_summary(project_root: Path, cycle_id: str) -> CycleSummaryResult:
    """Generate a compact summary for a single cycle.

    Parameters
    ----------
    project_root
        Filesystem project root containing ``.ai-loop/cycles``.
    cycle_id
        Cycle identifier expected as a direct child directory name.

    Returns
    -------
    CycleSummaryResult
        Immutable report with cycle summary information.

    Notes
    -----
    This function is report-only. It does not create or modify files.
    """

    # Use run_cycle_check as the main source of validation
    check_result = run_cycle_check(project_root, cycle_id)

    # Use cycle_dir from check_result for consistency
    cycle_dir = check_result.cycle_dir

    # Build optional files mapping
    optional_files: dict[str, bool] = {}
    for filename in OPTIONAL_CYCLE_FILES:
        file_path = cycle_dir / filename
        optional_files[filename] = file_path.is_file()

    # Extract status and created_at from meta.yaml if available
    status: str | None = None
    created_at: str | None = None

    meta_path = cycle_dir / "meta.yaml"
    if meta_path.is_file():
        parsed = _parse_yaml_file(meta_path)
        if isinstance(parsed, dict):
            raw_status = parsed.get("status")
            raw_created_at = parsed.get("created_at")
            # Accept only str values; ignore other types
            if isinstance(raw_status, str):
                status = raw_status
            if isinstance(raw_created_at, str):
                created_at = raw_created_at

    # Build required files mapping from check_result items
    required_files: dict[str, bool] = {}
    for item in check_result.items:
        required_files[item.path] = item.present

    # Use errors from run_cycle_check directly - all validation errors must be preserved
    errors = list(check_result.errors)

    return CycleSummaryResult(
        cycle_id=check_result.cycle_id,
        status=status,
        created_at=created_at,
        required_files=required_files,
        optional_files=optional_files,
        errors=errors,
    )


def _parse_yaml_file(path: Path) -> dict[str, str] | str:
    """Parse YAML file and return mapping, or error text."""
    import yaml

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        return str(exc)

    if data is None:
        return {}
    if not isinstance(data, dict):
        return "yaml root must be a mapping"
    return data