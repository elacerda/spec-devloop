"""Typer CLI entrypoint for spec-devloop MVP-0."""

from __future__ import annotations

from pathlib import Path

import typer

from devloop.doctor import DEFAULT_EXIT_CODES, calculate_exit_code, run_doctor

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


if __name__ == "__main__":
    app()
