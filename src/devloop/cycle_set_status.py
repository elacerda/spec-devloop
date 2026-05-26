"""Backend for `devloop cycle set-status` command in MVP-0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from devloop.cycle_check import (
    ALLOWED_STATUS_VALUES,
    _is_safe_cycle_id,
    _parse_yaml_file,
)


@dataclass(frozen=True)
class CycleSetStatusResult:
    """Result of cycle status update.

    Parameters
    ----------
    cycle_id
        Cycle identifier provided by the caller.
    cycle_dir
        Absolute path to the cycle directory.
    old_status
        Previous status value from meta.yaml, or None if unavailable.
    new_status
        New status value that was set, or None if update failed.
    errors
        List of error messages.
    """

    cycle_id: str
    cycle_dir: Path
    old_status: str | None
    new_status: str | None
    errors: list[str]


def run_cycle_set_status(project_root: Path, cycle_id: str, new_status: str) -> CycleSetStatusResult:
    """Update the status field in a cycle's meta.yaml file.

    Parameters
    ----------
    project_root
        Filesystem project root containing ``.ai-loop/cycles``.
    cycle_id
        Cycle identifier expected as a direct child directory name.
    new_status
        New status value to set. Must be one of the allowed status values.

    Returns
    -------
    CycleSetStatusResult
        Result with cycle_id, cycle_dir, old_status, new_status, and errors.

    Notes
    -----
    This function updates the status field in meta.yaml if it exists.
    It preserves all other fields in the file.
    It does not create the cycle or meta.yaml if they don't exist.
    """

    errors: list[str] = []

    # Validate cycle_id is safe
    if not _is_safe_cycle_id(cycle_id):
        errors.append(f"unsafe cycle id: {cycle_id}")
        return CycleSetStatusResult(
            cycle_id=cycle_id,
            cycle_dir=project_root / ".ai-loop" / "cycles" / cycle_id,
            old_status=None,
            new_status=None,
            errors=errors,
        )

    # Validate status is allowed
    if new_status not in ALLOWED_STATUS_VALUES:
        errors.append(
            f"invalid status value: {new_status}. "
            f"Allowed values are: {', '.join(sorted(ALLOWED_STATUS_VALUES))}"
        )
        return CycleSetStatusResult(
            cycle_id=cycle_id,
            cycle_dir=project_root / ".ai-loop" / "cycles" / cycle_id,
            old_status=None,
            new_status=None,
            errors=errors,
        )

    cycle_dir = project_root / ".ai-loop" / "cycles" / cycle_id

    # Check if cycle directory exists
    if not cycle_dir.is_dir():
        errors.append(f"cycle directory missing: {cycle_dir.relative_to(project_root)}")
        return CycleSetStatusResult(
            cycle_id=cycle_id,
            cycle_dir=cycle_dir,
            old_status=None,
            new_status=None,
            errors=errors,
        )

    meta_path = cycle_dir / "meta.yaml"

    # Check if meta.yaml exists
    if not meta_path.is_file():
        errors.append(f"meta.yaml missing: {meta_path.relative_to(project_root)}")
        return CycleSetStatusResult(
            cycle_id=cycle_id,
            cycle_dir=cycle_dir,
            old_status=None,
            new_status=None,
            errors=errors,
        )

    # Parse meta.yaml
    parsed = _parse_yaml_file(meta_path)
    if isinstance(parsed, str):
        errors.append(f"invalid yaml: meta.yaml: {parsed}")
        return CycleSetStatusResult(
            cycle_id=cycle_id,
            cycle_dir=cycle_dir,
            old_status=None,
            new_status=None,
            errors=errors,
        )

    # Get old status
    old_status = parsed.get("status")

    # Check if status is already the same (idempotent)
    if old_status == new_status:
        return CycleSetStatusResult(
            cycle_id=cycle_id,
            cycle_dir=cycle_dir,
            old_status=old_status,
            new_status=new_status,
            errors=errors,
        )

    # Update status in parsed data
    parsed["status"] = new_status

    # Write updated meta.yaml preserving other fields
    try:
        meta_content = yaml.dump(
            parsed,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        meta_path.write_text(meta_content, encoding="utf-8")
    except OSError as exc:
        errors.append(f"failed to write meta.yaml: {exc}")
        return CycleSetStatusResult(
            cycle_id=cycle_id,
            cycle_dir=cycle_dir,
            old_status=old_status,
            new_status=None,
            errors=errors,
        )

    return CycleSetStatusResult(
        cycle_id=cycle_id,
        cycle_dir=cycle_dir,
        old_status=old_status,
        new_status=new_status,
        errors=errors,
    )