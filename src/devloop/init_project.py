"""Backend project initialization for `devloop init` in MVP-0.

This module provides functions to create the minimum project structure
for local devloop usage without AI or external command execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Minimum structure paths for local devloop usage
MINIMUM_STRUCTURE_PATHS = [
    ".ai-loop",
    ".ai-loop/project.md",
    ".ai-loop/cycles",
]

# Default content for project.md placeholder
DEFAULT_PROJECT_MD = """# Project

Describe the project here.
"""


@dataclass(frozen=True)
class InitProjectResult:
    """Result of project initialization.

    Parameters
    ----------
    project_root
        Absolute root path that was initialized.
    created_paths
        List of paths that were created during initialization.
    preserved_paths
        List of paths that already existed and were preserved.
    errors
        List of error messages encountered during initialization.
    """

    project_root: Path
    created_paths: list[str]
    preserved_paths: list[str]
    errors: list[str]


def run_init_project(project_root: Path) -> InitProjectResult:
    """Create minimum project structure for local devloop usage.

    Parameters
    ----------
    project_root
        Filesystem root path to initialize.

    Returns
    -------
    InitProjectResult
        Result with created paths, preserved paths, and any errors.

    Notes
    -----
    This function is idempotent:
    - It will not overwrite existing files.
    - It will not fail if directories already exist.
    - Running twice is safe.
    """

    created_paths: list[str] = []
    preserved_paths: list[str] = []
    errors: list[str] = []

    # Ensure .ai-loop directory exists
    ai_loop_dir = project_root / ".ai-loop"
    if not ai_loop_dir.exists():
        try:
            ai_loop_dir.mkdir(parents=True, exist_ok=True)
            created_paths.append(".ai-loop")
        except OSError as exc:
            errors.append(f"failed to create .ai-loop: {exc}")
    else:
        preserved_paths.append(".ai-loop")

    # Create .ai-loop/project.md if it doesn't exist
    project_md_path = ai_loop_dir / "project.md"
    if not project_md_path.exists():
        try:
            project_md_path.write_text(DEFAULT_PROJECT_MD, encoding="utf-8")
            created_paths.append(".ai-loop/project.md")
        except OSError as exc:
            errors.append(f"failed to create .ai-loop/project.md: {exc}")
    else:
        preserved_paths.append(".ai-loop/project.md")

    # Ensure .ai-loop/cycles directory exists
    cycles_dir = ai_loop_dir / "cycles"
    if not cycles_dir.exists():
        try:
            cycles_dir.mkdir(parents=True, exist_ok=True)
            created_paths.append(".ai-loop/cycles")
        except OSError as exc:
            errors.append(f"failed to create .ai-loop/cycles: {exc}")
    else:
        preserved_paths.append(".ai-loop/cycles")

    return InitProjectResult(
        project_root=project_root,
        created_paths=created_paths,
        preserved_paths=preserved_paths,
        errors=errors,
    )