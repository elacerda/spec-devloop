"""Backend report-only list for `devloop cycle list` in MVP-0."""

from __future__ import annotations

from pathlib import Path


def list_cycles(project_root: Path) -> list[str]:
    """List cycle IDs from .ai-loop/cycles/ directory.

    Parameters
    ----------
    project_root
        Filesystem project root containing ``.ai-loop/cycles``.

    Returns
    -------
    list[str]
        Sorted list of cycle IDs (subdirectory names).

    Notes
    -----
    This function is report-only. It does not create or modify files.
    It does not validate cycle contents.
    """
    cycles_dir = project_root / ".ai-loop" / "cycles"

    if not cycles_dir.exists():
        return []

    if not cycles_dir.is_dir():
        return []

    cycle_ids: list[str] = []

    for entry in cycles_dir.iterdir():
        if entry.is_dir():
            cycle_ids.append(entry.name)

    return sorted(cycle_ids)
