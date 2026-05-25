# Decision 0002: Define `devloop doctor` contract

## Status

Accepted.

## Context

The specification review identified ambiguity in the first command scope, especially around checks, severities, exit codes, git behavior, managed directories, and minimum config schemas.

Without a formal contract, implementation could drift into premature automation or inconsistent validation behavior.

## Decision

Define `devloop doctor` as MVP-0 with a strict validation-only scope.

`devloop doctor` must:

- validate required and optional specification files;
- parse YAML for `.ai-loop/config/*.yaml`;
- validate minimum schemas for `commands.yaml`, `providers.yaml`, `adapters.yaml`, and `allowed_paths.yaml`;
- report managed directories presence without creating directories;
- report git repository absence and dirty worktree as warnings;
- use severities `info`, `warning`, and `error`;
- return exit code `0` when no errors exist, even with warnings;
- return exit code `2` when one or more validation errors exist;
- return exit code `3` for internal doctor runtime failures.

Policies are declared as specialized foundational specifications.

`state/` remains managed by CLI, but `loop_state.json` and `current_cycle.json` are not required for doctor readiness.

Python 3.12, Typer, Rich, Pydantic, YAML parser, pytest, ruff, and uv are maintained as future implementation recommendations, not proof of current files.

`allowed_paths.yaml` precedence is defined as:

- explicit deny over allow;
- more specific pattern over general pattern;
- foundational specs immutable in normal cycles.

A readiness matrix is adopted:

- `ready_for_doctor`;
- `ready_for_manual_cycle`;
- `ready_for_evidence_collection`;
- `ready_for_model_provider`;
- `ready_for_agent_adapter`.

## Consequences

Positive:

- stable contract for first implementation;
- lower risk of scope creep;
- deterministic CLI behavior for first validation command;
- preserved architecture neutrality across agents and providers.

Tradeoffs:

- no auto-fix behavior in doctor;
- additional explicit schema maintenance in config specs.
