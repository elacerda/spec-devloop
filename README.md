# spec-devloop

`spec-devloop` is a local orchestration layer for AI-assisted software development.

It helps transform an initial idea, project state, implementation evidence, and human decisions into auditable development cycles that can be executed manually, by external agents, or by a future autonomous orchestrator.

The project starts conservative and local-first, but its long-term goal is not to remain a copy/paste workflow. The manual workflow is only the first operating mode.

## Core idea

Modern AI coding workflows often work best when there is a clear separation between:

- **Human/operator**: defines intent, chooses autonomy level, approves sensitive decisions.
- **Supervisor/orchestrator**: plans, decomposes work, selects the next task, reviews evidence, decides whether to correct or advance.
- **Worker/executor**: edits code, runs commands, produces diffs, tests, logs, and reports.
- **Devloop**: maintains state, contracts, cycles, evidence, policies, and integration surfaces.

`spec-devloop` is the state and coordination layer that makes this loop explicit, repeatable, configurable, and auditable.

## What problem does it solve?

AI-assisted development can become chaotic when:

- tasks are too large or too vague;
- context is lost between interactions;
- agents modify files outside scope;
- there is no record of why a change was accepted;
- tests and evidence are not captured;
- the human must manually remember the whole implementation plan;
- different tools and models cannot share a common project state.

`spec-devloop` addresses this by keeping a local, file-based operational memory of the development loop.

## Operating modes

The project is designed to evolve through three compatible modes.

### 1. Manual mode

The human mediates interactions between supervisor and worker.

Example:

1. The user asks a supervisor AI for the next implementation step.
2. The supervisor proposes a microtask and a worker prompt.
3. The user sends that prompt to a worker such as Cline, Qwen, Roo, Codex CLI, Continue, or Aider.
4. The worker executes and reports the result.
5. The user returns the result to the supervisor.
6. The supervisor accepts, asks for correction, or proposes the next task.

This is the current practical workflow. It is useful for early development, debugging, and maximum human control.

### 2. Agent plugin / protocol mode

External agents interact with `devloop` directly.

In this mode, `devloop` exposes project state, cycle contracts, allowed scope, evidence requirements, and next-step information through one or more interfaces:

- CLI commands;
- JSON stdout;
- `.ai-loop/` files;
- local API;
- MCP server;
- agent plugins/adapters.

The agent can ask:

- What is the current cycle?
- What is the next task?
- Which files may I change?
- What commands should I run?
- What evidence must I provide?
- How should I report the result?

### 3. Autonomous orchestrator mode

The `devloop` tool calls or embeds a supervisor AI.

In this mode, the system can:

1. read the project state;
2. call the supervisor model;
3. select or create the next task;
4. delegate to a worker;
5. collect diffs, logs, tests, and evidence;
6. ask the supervisor to review the result;
7. request correction or close the cycle;
8. stop for human approval at sensitive checkpoints.

This is the long-term goal. It requires stronger safety policies, permissions, rollback strategy, sandboxing, and audit logs.

## Task granularity profiles

Different users and projects need different task sizes. `spec-devloop` should support configurable task granularity.

Initial conceptual profiles:

| Profile | Description | Best for |
|---------|-------------|----------|
| `micro` | Small tasks, narrow file scope, frequent checkpoints. | Careful development, local models, critical code. |
| `balanced` | Medium tasks with useful checks and moderate autonomy. | Default product development. |
| `yolo` | Large tasks, fewer checkpoints, faster iteration, higher risk. | Prototypes, experiments, low-risk code. |
| `torra-token` / `deep` | High-context, high-analysis, expensive reasoning mode. | Architecture, debugging, complex specs, reviews. |

These profiles should influence how the supervisor decomposes tasks, how much context it reads, how much output it generates, how often it asks for checkpoints, and how strict evidence requirements are.

## Design principles

`spec-devloop` should be:

- **local-first**: project state lives locally;
- **file-based**: operational state is inspectable and versionable;
- **model-agnostic**: no hard dependency on one model;
- **backend-agnostic**: local and remote providers can be supported;
- **agent-agnostic**: Cline, Roo, Codex, Continue, Aider, internal agents, and future tools are optional participants;
- **human-governed**: humans remain in control of sensitive decisions;
- **auditable**: cycles, evidence, and decisions should be traceable;
- **low-friction**: documentation and specs improve quality but should not become mandatory bureaucracy.

## Current status: MVP-0

MVP-0 is intentionally conservative and report-only.

It does not:

- call AI models;
- call agents;
- execute commands;
- modify project files;
- create cycles automatically.

It only validates, summarizes, and emits text.

## Current commands

The current CLI command name is:

```bash
devloop
```

MVP-0 commands:

- `devloop doctor`: validates local project readiness.
- `devloop status`: prints a compact readiness summary.
- `devloop init --check`: checks the expected minimum structure without creating it (report-only).
- `devloop cycle list`: lists cycle IDs.
- `devloop cycle check <cycle-id>`: validates the structure of one cycle.
- `devloop cycle prompt <cycle-id>`: emits a Markdown context packet for manual execution. Requires a valid cycle and `.ai-loop/project.md`. Optional files (`.ai-loop/architecture.md`, `.ai-loop/protocol.md`, `.ai-loop/config/commands.yaml`, `.ai-loop/config/allowed_paths.yaml`) are included when present. Does not call AI or execute external commands.
- `devloop cycle summary <cycle-id>`: prints a compact cycle summary.
- `devloop model check`: validates `.ai-loop/config/models.yaml` configuration (local, read-only, no network calls).
- `devloop model list`: lists providers, models, roles, and aliases from `.ai-loop/config/models.yaml` (local, read-only, no network calls).
- `devloop model ping <target> --allow-call`: prepares a sanitized model ping request without performing network transport (local, read-only, no network calls). See [Supervisor Config](docs/supervisor-config.md) for details.

### Model configuration

Model configuration is optional and report-only. The `.ai-loop/config/models.yaml` file defines providers, models, roles, and preferences for future AI orchestration. It does not trigger network calls or model invocations.

- **Missing config**: Not a readiness failure. `devloop doctor` and `devloop status` continue to work without it.
- **Invalid config**: If present but malformed or invalid, reported as an error.
- **Status reporting**: `devloop status` reports `model_config: absent|valid|invalid|missing`.

All `devloop model` commands (`check`, `list`) are local and read-only.

### `devloop model ping`

The `devloop model ping <target> --allow-call` command prepares a sanitized model ping request without performing network transport (local, read-only, no network calls). Requires `policy.model_calls_allowed: true` in `.ai-loop/config/models.yaml` and the `--allow-call` flag. See [Supervisor Config](docs/supervisor-config.md) for details.

### MVP-1 low-friction cycle management

- `devloop init`: creates the minimum project structure (`.ai-loop/`, `.ai-loop/project.md`, `.ai-loop/cycles/`).
- `devloop cycle new "<task description>"`: creates a new cycle with minimal structure.
- `devloop cycle set-status <cycle-id> <status>`: updates the cycle status in `.ai-loop/cycles/<cycle-id>/meta.yaml`.
- `devloop cycle complete <cycle-id>`: marks a cycle as `completed`. Equivalent to `devloop cycle set-status <cycle-id> completed`.

These are post-MVP-0 commands that enable low-friction cycle creation and state management, moving beyond the report-only nature of MVP-0.

## Minimal manual cycle flow

The current manual workflow follows this complete cycle:

```bash
devloop init
devloop cycle new "Minha tarefa"
devloop cycle summary c-001
devloop cycle prompt c-001
devloop cycle set-status c-001 ready_for_worker
devloop cycle complete c-001
devloop cycle summary c-001
devloop cycle check c-001
```

**What happens in this flow:**

- `init` creates the minimum project structure (`.ai-loop/`, `.ai-loop/project.md`, `.ai-loop/cycles/`).
- `cycle new` creates a new cycle with status `planned`.
- `cycle summary` shows a compact state of the cycle.
- `cycle prompt` generates a Markdown packet for manual execution by an external agent.
- `cycle set-status` marks the cycle as `ready_for_worker` (or any valid status: `planned`, `ready_for_worker`, `in_progress`, `waiting_review`, `completed`, `blocked`).
- `cycle complete` is a convenience command equivalent to `set-status completed`.
- `cycle check` validates that the cycle structure remains intact.

**Important notes:**

- This flow does not call AI directly.
- This flow does not execute external commands.
- The human still mediates execution and review.
- This is the manual/local-first mode.
- Commands that modify state belong to MVP-1 / low-friction cycle management, not the core MVP-0 report-only commands.

## Minimal local usage

```bash
python3 -m pip install -e .
devloop doctor
devloop status
devloop init --check
```

## Documentation

| Document | Purpose |
|----------|---------|
| [Vision](docs/vision.md) | Product vision and principles. |
| [Architecture](docs/architecture.md) | Roles, components, and system boundaries. |
| [Operating Modes](docs/operating-modes.md) | Manual, plugin/protocol, and autonomous modes. |
| [Task Granularity](docs/task-granularity.md) | Micro, balanced, yolo, and torra-token/deep profiles. |
| [Roadmap](docs/roadmap.md) | Evolution from MVP-0 to autonomous orchestration. |
| [MVP](docs/mvp.md) | MVP-0 and product MVP definitions. |
| [Repository Layout](docs/repository-layout.md) | Repository and `.ai-loop/` layout. |
| [Manual Cycle](docs/manual-cycle.md) | Current manual cycle contract. |
| [Supervisor Config](docs/supervisor-config.md) | Future supervisor/orchestrator configuration. |
| [Agent Integration](docs/agent-integration.md) | Future plugin/protocol integration surface. |
| [Safety](docs/safety.md) | Safety, approval, permissions, and rollback principles. |
| [Glossary](docs/glossary.md) | Terms used by the project. |
| [Documentation Rewrite Plan](docs/documentation-rewrite-plan.md) | Suggested migration plan from current docs to the new narrative. |
| [Bootstrap Flows](docs/bootstrap.md) | Future bootstrap entry points (idea-first, doc-first, resume). |
| [Ingestion](docs/ingestion.md) | Documentation ingestion and context extraction mechanism. |
