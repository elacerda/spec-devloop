# spec-devloop

This package contains the initial redesigned documentation and specification set for **spec-devloop**.

`spec-devloop` is intended to be a local, file-based, spec-first, human-in-the-loop orchestrator for AI-assisted development cycles. It is not intended to be a coding agent in the initial MVP. Instead, it governs a development loop around external or future internal executors.

The project name is:

```text
spec-devloop
```

The recommended CLI command name remains:

```bash
devloop
```

## Design position

`spec-devloop` should be:

- model-agnostic;
- agent-agnostic;
- backend-agnostic;
- file-based;
- spec-first;
- local-first;
- auditable;
- conservative by default;
- usable even without any model provider configured.

It should treat tools such as Cline, Roo, Continue, Codex CLI, Aider, vLLM, Ollama, OpenAI-compatible endpoints, OpenAI API, Anthropic API, or future internal agents as optional participants, adapters, or providers.

## Specification layers

This package separates the project into four kinds of files:

1. **Foundational specifications**  
   Stable, high-authority documents that define the identity, architecture, protocol, and governance of the project.

2. **Policies**  
   Stable or semi-stable documents that constrain models, agents, context, acceptance, and failure handling.

3. **Operational configuration**  
   YAML files that the CLI can validate and execute mechanically.

4. **Generated cycle artifacts**  
   Per-cycle files created by the CLI during actual use.

## Directory overview

```text
.ai-loop/
  project.md
  architecture.md
  protocol.md
  specification_lifecycle.md

  policies/
    model_policy.md
    agent_policy.md
    context_policy.md
    acceptance_policy.md
    failure_modes.md

  config/
    commands.yaml
    allowed_paths.yaml
    providers.yaml
    adapters.yaml

  templates/
    cycle/
      task.md
      agent_plan.md
      plan_review.md
      execution_result.md
      report.md
      decision.yaml

  cycles/
  state/

docs/
  vision.md
  mvp.md
  glossary.md
  research/
    related_work.md
  decisions/
    0001-initial-architecture.md
```

## Minimum required files

The MVP should be able to work with a smaller minimum set:

```text
.ai-loop/project.md
.ai-loop/architecture.md
.ai-loop/protocol.md
.ai-loop/config/commands.yaml
```

All other files should be read if present, but absence of optional policy/config files should not prevent basic operation unless the selected command explicitly requires them.

## Recommended first implementation target

The first implementation target should be:

```bash
devloop doctor
```

It should validate the minimum required specification set, inspect optional files, verify YAML syntax, confirm managed directories, and report whether the project is ready for manual cycles.

No model calls, no agent automation, and no code editing should be implemented before the local spec validation layer is reliable.

## MVP-0 commands

The MVP-0 CLI exposes report-only diagnostics:

- `devloop doctor`: validates the local spec set, YAML files, minimal schemas, managed directories, and git state.
- `devloop status`: reuses `doctor` and prints a short readiness summary with project root, readiness, finding counts, and git status.
- `devloop init --check`: checks the minimum expected structure for manual setup and reports missing paths.
- `devloop cycle check <cycle-id>`: validates the minimum manual cycle layout under `.ai-loop/cycles/<cycle-id>/`.
- `devloop cycle list`: lists immediate subdirectories of `.ai-loop/cycles/`, sorted alphabetically. Does not validate cycles. Returns empty output and exit 0 if the directory does not exist or is empty.

`devloop init` without `--check` is intentionally conservative in MVP-0: automatic write mode is not supported yet and no files or directories are created.

`devloop cycle check <cycle-id>` is report-only and does not create the cycle. The human must create the cycle directory and files manually before running the check. It validates only the minimum structural contract and returns `0` when there are no validation errors, `2` when validation errors are present, and `3` on unexpected internal failure.

`devloop cycle list` is report-only and does not validate cycles. It lists only immediate subdirectories of `.ai-loop/cycles/`, without recursion. If `.ai-loop/cycles/` does not exist or is empty, the output is empty and the exit code is 0. Unexpected internal failures return exit code 3.

Minimum manual cycle layout:

```text
.ai-loop/cycles/<cycle-id>/
  meta.yaml
  task.md
  report.md
```

Example `meta.yaml`:

```yaml
schema_version: "0"
cycle_id: c-001
created_at: "2026-05-26"
status: draft
```

Both diagnostics are conservative and report-only in MVP-0:

- they do not create files or directories;
- they do not call models;
- they do not call agents;
- they do not execute configured commands.

## Local MVP-0 usage

Minimum local run for MVP-0:

```bash
python3 -m pip install -e .
devloop doctor
devloop status
devloop init --check
```

If `uv` is available, dependency sync can be done with:

```bash
uv sync
```
