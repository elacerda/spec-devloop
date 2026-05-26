"""Typer CLI entrypoint for spec-devloop MVP-0."""

from __future__ import annotations

from pathlib import Path

import typer

from devloop.doctor import (
    DEFAULT_EXIT_CODES,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    Finding,
    calculate_exit_code,
    run_doctor,
)

app = typer.Typer(help="spec-devloop CLI")


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


if __name__ == "__main__":
    app()
