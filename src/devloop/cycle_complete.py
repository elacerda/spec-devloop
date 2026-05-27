"""Backend for `devloop cycle complete` command in MVP-0.

This module provides a convenience command to mark a cycle as completed.
It reuses the implementation of `run_cycle_set_status` to avoid duplication
while maintaining the contract of the complete command.
"""

from __future__ import annotations

from pathlib import Path

from devloop.cycle_set_status import CycleSetStatusResult, run_cycle_set_status


def run_cycle_complete(project_root: Path, cycle_id: str) -> CycleSetStatusResult:
    """Mark a cycle as completed by updating its status in meta.yaml.

    This is a convenience wrapper around `run_cycle_set_status` that always
    sets the status to "completed". It preserves all other fields in meta.yaml
    and does not modify task.md or report.md.

    Parameters
    ----------
    project_root
        Filesystem project root containing ``.ai-loop/cycles``.
    cycle_id
        Cycle identifier expected as a direct child directory name.

    Returns
    -------
    CycleSetStatusResult
        Result with cycle_id, cycle_dir, old_status, new_status, and errors.

    Notes
    -----
    This function:
    - Validates cycle_id is safe
    - Requires the cycle directory to exist
    - Requires meta.yaml to exist and be valid YAML
    - Updates only the status field to "completed"
    - Preserves all other fields in meta.yaml
    - Is idempotent: succeeds if status is already "completed"
    - Does not create cycles or meta.yaml
    - Does not modify task.md or report.md
    """
    return run_cycle_set_status(project_root, cycle_id, "completed")