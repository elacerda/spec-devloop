"""Backend for `devloop cycle new` command in MVP-0."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class CycleNewResult:
    """Result of cycle creation.

    Parameters
    ----------
    cycle_id
        Cycle identifier that was created.
    cycle_dir
        Absolute path to the created cycle directory.
    created_files
        List of files that were created.
    errors
        List of error messages.
    """

    cycle_id: str | None
    cycle_dir: Path | None
    created_files: list[str]
    errors: list[str]


def run_cycle_new(project_root: Path, task_description: str) -> CycleNewResult:
    """Create a new cycle with minimal structure.

    Parameters
    ----------
    project_root
        Filesystem project root containing ``.ai-loop/cycles``.
    task_description
        Description of the task to include in task.md.

    Returns
    -------
    CycleNewResult
        Result with cycle_id, cycle_dir, created_files, and errors.

    Notes
    -----
    This function creates the cycle directory and files if they don't exist.
    It finds the next sequential cycle ID (c-001, c-002, etc.).
    """

    errors: list[str] = []
    created_files: list[str] = []

    # Validate task description
    if not task_description or not task_description.strip():
        errors.append("task description cannot be empty")
        return CycleNewResult(
            cycle_id=None,
            cycle_dir=None,
            created_files=[],
            errors=errors,
        )

    # Ensure .ai-loop/cycles directory exists
    cycles_dir = project_root / ".ai-loop" / "cycles"
    cycles_dir.mkdir(parents=True, exist_ok=True)

    # Find next sequential cycle ID
    cycle_id = _find_next_cycle_id(cycles_dir)

    # Check if cycle already exists (should not happen if logic is correct)
    cycle_dir = cycles_dir / cycle_id
    if cycle_dir.exists():
        errors.append(f"cycle directory already exists: {cycle_dir}")
        return CycleNewResult(
            cycle_id=None,
            cycle_dir=None,
            created_files=[],
            errors=errors,
        )

    # Create cycle directory
    cycle_dir.mkdir(parents=True, exist_ok=True)

    # Create meta.yaml
    meta_content = _generate_meta_yaml(cycle_id)
    meta_path = cycle_dir / "meta.yaml"
    meta_path.write_text(meta_content, encoding="utf-8")
    created_files.append("meta.yaml")

    # Create task.md
    task_content = _generate_task_md(task_description)
    task_path = cycle_dir / "task.md"
    task_path.write_text(task_content, encoding="utf-8")
    created_files.append("task.md")

    # Create report.md
    report_content = _generate_report_md()
    report_path = cycle_dir / "report.md"
    report_path.write_text(report_content, encoding="utf-8")
    created_files.append("report.md")

    return CycleNewResult(
        cycle_id=cycle_id,
        cycle_dir=cycle_dir,
        created_files=created_files,
        errors=errors,
    )


def _find_next_cycle_id(cycles_dir: Path) -> str:
    """Find the next sequential cycle ID.

    Parameters
    ----------
    cycles_dir
        Path to the .ai-loop/cycles directory.

    Returns
    -------
    str
        Next cycle ID in format c-NNN.
    """
    existing_ids: list[int] = []

    if cycles_dir.exists() and cycles_dir.is_dir():
        for entry in cycles_dir.iterdir():
            if entry.is_dir():
                name = entry.name
                # Check if name matches pattern c-NNN
                if name.startswith("c-") and len(name) > 2:
                    suffix = name[2:]
                    if suffix.isdigit():
                        existing_ids.append(int(suffix))

    if not existing_ids:
        return "c-001"

    next_num = max(existing_ids) + 1
    return f"c-{next_num:03d}"


def _generate_meta_yaml(cycle_id: str) -> str:
    """Generate meta.yaml content.

    Parameters
    ----------
    cycle_id
        Cycle identifier.

    Returns
    -------
    str
        YAML content as string.
    """
    today = date.today().isoformat()
    data = {
        "schema_version": "0",
        "cycle_id": cycle_id,
        "created_at": today,
        "status": "planned",
    }
    return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _generate_task_md(task_description: str) -> str:
    """Generate task.md content.

    Parameters
    ----------
    task_description
        Description of the task.

    Returns
    -------
    str
        Markdown content as string.
    """
    return f"# Task\n\n{task_description}\n"


def _generate_report_md() -> str:
    """Generate report.md placeholder content.

    Returns
    -------
    str
        Markdown content as string.
    """
    return "# Report\n\nNo execution recorded yet.\n"