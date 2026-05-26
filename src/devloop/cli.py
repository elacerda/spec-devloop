"""Typer CLI entrypoint for spec-devloop MVP-0."""

from __future__ import annotations

from pathlib import Path

import typer

from devloop.cycle_check import run_cycle_check
from devloop.cycle_list import list_cycles
from devloop.cycle_new import run_cycle_new
from devloop.cycle_prompt import run_cycle_prompt
from devloop.cycle_summary import run_cycle_summary
from devloop.doctor import (
    DEFAULT_EXIT_CODES,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    Finding,
    calculate_exit_code,
    run_doctor,
)
from devloop.init_check import run_init_check

app = typer.Typer(help="spec-devloop CLI")
cycle_app = typer.Typer(help="Manual cycle report-only commands.")


@app.callback()
def main() -> None:
    """Main command group for devloop."""


@app.command("doctor")
def doctor() -> None:
    """Validate project specs and local readiness in report-only mode."""

    project_root = Path.cwd()
    try:
        result = run_doctor(project_root)
        for finding in result.findings:
            typer.echo(f"{finding.severity}: {finding.message}")
        raise typer.Exit(code=calculate_exit_code(result))
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        typer.echo(f"error: unexpected doctor failure: {exc}")
        raise typer.Exit(code=DEFAULT_EXIT_CODES["internal_failure"]) from exc


def _infer_git_status(findings: list[Finding]) -> str:
    """Infer git status from doctor findings without re-checking git state."""

    messages = [finding.message for finding in findings]
    if "git repository not detected" in messages:
        return "not detected"
    if "git worktree is dirty" in messages:
        return "dirty"
    if "git worktree is clean" in messages:
        return "clean"
    if "git executable not found" in messages:
        return "unknown"
    if "unable to inspect git worktree status" in messages:
        return "unknown"
    return "unknown"


@app.command("status")
def status() -> None:
    """Show a compact readiness summary derived from doctor findings."""

    project_root = Path.cwd()
    try:
        result = run_doctor(project_root)
        errors = sum(1 for item in result.findings if item.severity == SEVERITY_ERROR)
        warnings = sum(1 for item in result.findings if item.severity == SEVERITY_WARNING)
        info = sum(1 for item in result.findings if item.severity == SEVERITY_INFO)
        ready = "yes" if errors == 0 else "no"
        git_status = _infer_git_status(result.findings)

        typer.echo(f"project root: {project_root}")
        typer.echo(f"ready: {ready}")
        typer.echo(f"errors: {errors}")
        typer.echo(f"warnings: {warnings}")
        typer.echo(f"info: {info}")
        typer.echo(f"git: {git_status}")

        raise typer.Exit(code=DEFAULT_EXIT_CODES["ok"] if errors == 0 else 2)
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        typer.echo(f"error: unexpected status failure: {exc}")
        raise typer.Exit(code=DEFAULT_EXIT_CODES["internal_failure"]) from exc


@app.command("init")
def init(check: bool = typer.Option(False, "--check", help="Run report-only init checks.")) -> None:
    """Run conservative init behavior for MVP-0."""

    if not check:
        typer.echo("error: automatic init write mode is not supported in MVP-0; use --check")
        raise typer.Exit(code=2)

    project_root = Path.cwd()
    try:
        result = run_init_check(project_root)
        for item in result.items:
            state = "present" if item.present else "missing"
            typer.echo(f"{item.path}: {state}")
        typer.echo(f"project root: {result.project_root}")
        typer.echo(f"missing: {result.missing_count}")
        ready = "yes" if result.ready_for_manual_setup else "no"
        typer.echo(f"ready_for_manual_setup: {ready}")
        raise typer.Exit(code=0 if result.missing_count == 0 else 2)
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        typer.echo(f"error: unexpected init check failure: {exc}")
        raise typer.Exit(code=DEFAULT_EXIT_CODES["internal_failure"]) from exc


@cycle_app.command("list")
def cycle_list() -> None:
    """List cycle IDs from .ai-loop/cycles/ directory."""
    project_root = Path.cwd()
    try:
        cycle_ids = list_cycles(project_root)
        for cycle_id in cycle_ids:
            typer.echo(cycle_id)
        raise typer.Exit(code=0)
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        typer.echo(f"error: unexpected cycle list failure: {exc}")
        raise typer.Exit(code=DEFAULT_EXIT_CODES["internal_failure"]) from exc


@cycle_app.command("check")
def cycle_check(cycle_id: str) -> None:
    """Validate manual cycle structure for a single cycle id."""

    project_root = Path.cwd()
    try:
        result = run_cycle_check(project_root, cycle_id)
        for item in result.items:
            state = "present" if item.present else "missing"
            typer.echo(f"{item.path}: {state}")
        for error in result.errors:
            typer.echo(f"error: {error}")
        typer.echo(f"cycle id: {result.cycle_id}")
        typer.echo(f"cycle dir: {result.cycle_dir}")
        typer.echo(f"errors: {len(result.errors)}")
        ready = "yes" if not result.errors else "no"
        typer.echo(f"ready: {ready}")
        raise typer.Exit(code=0 if not result.errors else 2)
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        typer.echo(f"error: unexpected cycle check failure: {exc}")
        raise typer.Exit(code=DEFAULT_EXIT_CODES["internal_failure"]) from exc


@cycle_app.command("prompt")
def cycle_prompt(cycle_id: str) -> None:
    """Generate a Markdown prompt for manual cycle execution."""

    project_root = Path.cwd()
    try:
        result = run_cycle_prompt(project_root, cycle_id)
        if result.prompt is not None:
            typer.echo(result.prompt)
            raise typer.Exit(code=0)
        if result.errors:
            for error in result.errors:
                typer.echo(f"error: {error}")
            typer.echo(f"cycle id: {result.cycle_id}")
            typer.echo(f"cycle dir: {result.cycle_dir}")
        raise typer.Exit(code=2)
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        typer.echo(f"error: unexpected cycle prompt failure: {exc}")
        raise typer.Exit(code=DEFAULT_EXIT_CODES["internal_failure"]) from exc


@cycle_app.command("new")
def cycle_new(task_description: str) -> None:
    """Create a new cycle with minimal structure."""

    project_root = Path.cwd()
    try:
        result = run_cycle_new(project_root, task_description)

        if result.errors:
            for error in result.errors:
                typer.echo(f"error: {error}")
            raise typer.Exit(code=2)

        if result.cycle_dir is not None:
            typer.echo(f"created cycle: {result.cycle_id}")
            typer.echo(f"path: {result.cycle_dir.relative_to(project_root)}")
            typer.echo("status: planned")
        raise typer.Exit(code=0)
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        typer.echo(f"error: unexpected cycle new failure: {exc}")
        raise typer.Exit(code=DEFAULT_EXIT_CODES["internal_failure"]) from exc


@cycle_app.command("summary")
def cycle_summary(cycle_id: str) -> None:
    """Show a compact summary for a single cycle."""

    project_root = Path.cwd()
    try:
        result = run_cycle_summary(project_root, cycle_id)

        typer.echo(f"cycle id: {result.cycle_id}")

        if result.status is not None:
            typer.echo(f"status: {result.status}")
        else:
            typer.echo("status: missing")

        if result.created_at is not None:
            # Extract date portion if datetime string
            created_at_str = result.created_at
            if "T" in created_at_str:
                created_at_str = created_at_str.split("T")[0]
            typer.echo(f"created_at: {created_at_str}")
        else:
            typer.echo("created_at: missing")

        typer.echo("required files:")
        for filename in ["meta.yaml", "task.md", "report.md"]:
            state = "present" if result.required_files.get(filename, False) else "missing"
            typer.echo(f"  {filename}: {state}")

        typer.echo("optional files:")
        for filename in ["plan.md", "evidence.md"]:
            state = "present" if result.optional_files.get(filename, False) else "missing"
            typer.echo(f"  {filename}: {state}")

        typer.echo(f"errors: {len(result.errors)}")

        # Display individual error messages
        for error in result.errors:
            typer.echo(f"  - {error}")

        # Exit code 0 for valid cycle, 2 for validation errors
        if result.errors:
            raise typer.Exit(code=2)
        raise typer.Exit(code=0)
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - defensive fallback
        typer.echo(f"error: unexpected cycle summary failure: {exc}")
        raise typer.Exit(code=DEFAULT_EXIT_CODES["internal_failure"]) from exc


app.add_typer(cycle_app, name="cycle")


if __name__ == "__main__":
    app()
