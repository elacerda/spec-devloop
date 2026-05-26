"""Backend report-only checks for `devloop cycle check` in MVP-0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REQUIRED_CYCLE_FILES = ["meta.yaml", "task.md", "report.md"]
REQUIRED_META_FIELDS = ["schema_version", "cycle_id", "created_at", "status"]


@dataclass(frozen=True)
class CycleCheckItem:
    """Single cycle artifact check item.

    Parameters
    ----------
    path
        Cycle-relative path checked in the cycle directory.
    present
        ``True`` when the artifact exists, ``False`` when missing.
    """

    path: str
    present: bool


@dataclass(frozen=True)
class CycleCheckResult:
    """Result of cycle structure validation checks.

    Parameters
    ----------
    cycle_id
        Cycle identifier provided by the caller.
    cycle_dir
        Absolute cycle directory path inspected by the checker.
    items
        Required artifact presence results.
    errors
        Validation error messages.
    """

    cycle_id: str
    cycle_dir: Path
    items: list[CycleCheckItem]
    errors: list[str]


def run_cycle_check(project_root: Path, cycle_id: str) -> CycleCheckResult:
    """Validate manual cycle artifacts for a single cycle.

    Parameters
    ----------
    project_root
        Filesystem project root containing ``.ai-loop/cycles``.
    cycle_id
        Cycle identifier expected as a direct child directory name.

    Returns
    -------
    CycleCheckResult
        Immutable report with artifact presence and validation errors.

    Notes
    -----
    This function is report-only. It does not create or modify files.
    """

    errors: list[str] = []
    if not _is_safe_cycle_id(cycle_id):
        errors.append(f"unsafe cycle id: {cycle_id}")
        return CycleCheckResult(
            cycle_id=cycle_id,
            cycle_dir=project_root / ".ai-loop" / "cycles" / cycle_id,
            items=[],
            errors=errors,
        )

    cycle_dir = project_root / ".ai-loop" / "cycles" / cycle_id
    if not cycle_dir.is_dir():
        errors.append(f"cycle directory missing: {cycle_dir.relative_to(project_root)}")

    items = [
        CycleCheckItem(path=filename, present=(cycle_dir / filename).is_file())
        for filename in REQUIRED_CYCLE_FILES
    ]
    for item in items:
        if not item.present:
            errors.append(f"required artifact missing: {item.path}")

    meta_path = cycle_dir / "meta.yaml"
    if meta_path.is_file():
        parsed = _parse_yaml_file(meta_path)
        if isinstance(parsed, dict):
            errors.extend(_validate_meta_fields(parsed, cycle_id))
        else:
            errors.append(f"invalid yaml: meta.yaml: {parsed}")

    return CycleCheckResult(
        cycle_id=cycle_id,
        cycle_dir=cycle_dir,
        items=items,
        errors=errors,
    )


def _is_safe_cycle_id(cycle_id: str) -> bool:
    """Return ``True`` when cycle_id is safe as a direct child directory name."""

    if cycle_id in {".", ".."}:
        return False
    if "/" in cycle_id or "\\" in cycle_id:
        return False
    return True


def _parse_yaml_file(path: Path) -> dict[str, Any] | str:
    """Parse YAML file and return mapping, or error text."""

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError) as exc:
        return str(exc)

    if data is None:
        return {}
    if not isinstance(data, dict):
        return "yaml root must be a mapping"
    return data


def _validate_meta_fields(meta: dict[str, Any], cycle_id: str) -> list[str]:
    """Validate minimum required fields in meta.yaml."""

    errors: list[str] = []
    for field in REQUIRED_META_FIELDS:
        if field not in meta:
            errors.append(f"required meta field missing: {field}")
            continue
        value = meta[field]
        if not isinstance(value, str) or not value.strip():
            errors.append(f"required meta field must be non-empty string: {field}")

    if "cycle_id" in meta and isinstance(meta["cycle_id"], str) and meta["cycle_id"] != cycle_id:
        errors.append("meta cycle_id does not match requested cycle id")

    return errors
