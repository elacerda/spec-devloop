# Architecture specification

## Architectural principle

`spec-devloop` should be a small Python CLI application whose core is independent from any coding agent or model provider.

The core should operate on local files, explicit states, and mechanical evidence.

## Recommended language and runtime

- Language: Python
- Target version for MVP: Python 3.12
- Suggested Python requirement: `>=3.12,<3.13`
- Packaging: `pyproject.toml`
- Suggested tooling: `uv`, `pytest`, `ruff`, `mypy` or `pyright` if useful
- CLI framework: `typer`
- Terminal output: `rich`
- Config validation: `pydantic`
- YAML parsing: `pyyaml` or `ruamel.yaml`
- HTTP client for future providers: `httpx`

## Core modules

A future Python package may use a structure similar to:

```text
src/spec_devloop/
  cli/
    app.py
    commands/
      doctor.py
      status.py
      cycle.py
      report.py

  specs/
    loader.py
    validator.py
    models.py

  protocol/
    states.py
    transitions.py
    cycle.py

  artifacts/
    paths.py
    templates.py
    writer.py
    reader.py

  runner/
    shell.py
    git.py
    commands.py

  reports/
    markdown.py

  adapters/
    manual.py
    base.py
    codex_cli.py      # future
    cline.py          # future
    roo.py            # future
    continue_dev.py   # future
    internal.py       # future

  providers/
    base.py
    none.py
    openai_compatible.py  # future
    ollama.py             # future
    openai.py             # future
    anthropic.py          # future
```

This module structure is illustrative, not mandatory.

## Core boundary

The core should own:

- specification loading;
- specification validation;
- protocol state transitions;
- cycle directory creation;
- artifact naming;
- command execution;
- git status/diff collection;
- report generation;
- human decision recording.

The core should not own provider-specific or agent-specific behavior.

## Agent adapter boundary

An **agent adapter** is anything that helps a user or tool move through the phases of a cycle.

Examples:

- `manual`: generates prompts and expects the user to paste outputs back;
- `codex_cli`: may later call Codex CLI commands or prepare Codex-specific prompts;
- `cline`: may later prepare Plan/Act prompts for Cline;
- `roo`: may later prepare prompts for Roo;
- `continue`: may later prepare context or instructions for Continue;
- `aider`: may later prepare instructions for Aider;
- `internal`: may later implement a restricted built-in agent.

The MVP should implement only the `manual` adapter.

The core must not assume that every agent has Plan/Act modes. Plan/Act is an adapter strategy, not a protocol requirement.

## Model provider boundary

A **model provider** is a source of language model completions.

Examples:

- no provider;
- OpenAI-compatible endpoint;
- vLLM;
- Ollama;
- LM Studio;
- OpenAI API;
- Anthropic API;
- local mock provider.

The MVP should not require any provider.

Provider integration should be optional and configured separately from agent adapter selection.

## Separation of concerns

The architecture must preserve these separations:

```text
protocol != agent
agent != model provider
model provider != tool execution
specification != cycle artifact
cycle artifact != foundational rule
```

## File-based design

The MVP should use local files instead of a database.

Benefits:

- easy inspection;
- easy git versioning;
- easy debugging;
- easy copy/paste into external agents;
- low infrastructure burden;
- compatibility with different tools.

## Managed directories

The CLI may manage these directories:

```text
.ai-loop/cycles/
.ai-loop/state/
.ai-loop/reports/       # optional
.ai-loop/prompts/       # optional
```

However, per-cycle artifacts should preferably live inside `.ai-loop/cycles/<cycle-id>/`.

## Internal agent position

An internal agent with tool calling may be feasible later, but it is outside the MVP.

If implemented later, it must:

- obey `allowed_paths.yaml`;
- use only allowed commands;
- produce proposed patches or controlled edits;
- never alter foundational specs during normal cycles;
- stop on repeated failures;
- require human approval at critical boundaries;
- log actions and observations as artifacts.

The project should not be architected in a way that prevents this future, but should not start there.
