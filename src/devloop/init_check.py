"""Backend report-only checks for `devloop init --check` in MVP-0."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MINIMUM_SETUP_PATHS = [
    ".ai-loop/project.md",
    ".ai-loop/architecture.md",
    ".ai-loop/protocol.md",
    ".ai-loop/config/commands.yaml",
    ".ai-loop/cycles",
    ".ai-loop/state",
]


@dataclass(frozen=True)
class InitCheckItem:
    """Single structural path check entry.

    Parameters
    ----------
    path
        Project-relative path expected by manual MVP-0 setup.
    present
        ``True`` when the path exists, ``False`` when missing.
    """

    path: str
    present: bool


@dataclass(frozen=True)
class InitCheckResult:
    """Result of minimum-structure checks for manual setup.

    Parameters
    ----------
    project_root
        Absolute root path inspected by the checker.
    items
        List of required paths and their presence status.
    missing_count
        Number of missing required paths in ``items``.
    ready_for_manual_setup
        ``True`` only when ``missing_count == 0``.
    """

    project_root: Path
    items: list[InitCheckItem]
    missing_count: int
    ready_for_manual_setup: bool


def run_init_check(project_root: Path) -> InitCheckResult:
    """Validate the minimum local structure for manual setup.

    Parameters
    ----------
    project_root
        Filesystem root path to inspect.

    Returns
    -------
    InitCheckResult
        Immutable report with per-path presence and setup readiness.

    Notes
    -----
    This function is report-only. It never writes files or creates directories.
    """

    items = [
        InitCheckItem(path=rel_path, present=(project_root / rel_path).exists())
        for rel_path in MINIMUM_SETUP_PATHS
    ]
    missing_count = sum(1 for item in items if not item.present)
    return InitCheckResult(
        project_root=project_root,
        items=items,
        missing_count=missing_count,
        ready_for_manual_setup=missing_count == 0,
    )
