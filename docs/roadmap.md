# Roadmap

This roadmap describes the evolution of `spec-devloop` from a report-only local CLI into a configurable AI orchestration layer.

## MVP-0: Report-only foundation

Goal: establish safe local foundations.

Characteristics:

- no model calls;
- no agent calls;
- no command execution;
- no file modification at runtime;
- validates project and cycle structure;
- emits summaries and context packets;
- supports manual workflows.

Implemented or in progress:

- `devloop doctor`: validates local project readiness, including optional `.ai-loop/config/models.yaml` validation.
- `devloop status`: prints a compact readiness summary, including `model_config: absent|valid|invalid|missing`.
- `devloop init --check`: checks the expected minimum structure without creating it (report-only).
- `devloop cycle list`: lists cycle IDs.
- `devloop cycle check <cycle-id>`: validates the structure of one cycle.
- `devloop cycle prompt <cycle-id>`: emits a Markdown context packet for manual execution.
- `devloop cycle summary <cycle-id>`: prints a compact cycle summary.
- `devloop model check`: validates `.ai-loop/config/models.yaml` configuration (local, read-only, no network calls).
- `devloop model list`: lists providers, models, roles, and aliases from `.ai-loop/config/models.yaml` (local, read-only, no network calls).
- `devloop model ping <target> --allow-call`: performs a real OpenAI-compatible `/chat/completions` ping when explicitly authorized. See [Supervisor Config](docs/supervisor-config.md) for details on sanitized output, exit codes, and safety constraints.
- `devloop cycle advise <cycle-id> [--role ROLE] --allow-call`: runs an authorized model-backed advisory request using an OpenAI-compatible `/chat/completions` transport. Validates model config, cycle structure, policy, and explicit `--allow-call`; resolves role/model/provider; collects only allowlisted artifacts; prints sanitized metadata and advisory text to stdout. It remains advisory-only and does not mutate files, execute shell commands, invoke agents, persist payloads/responses, or print secrets. See [Supervisor Config](docs/supervisor-config.md) for details on behavior, output shape, and safety constraints.

### Model configuration

The `.ai-loop/config/models.yaml` file is **optional**. Its absence is not a readiness failure.

- **Missing config**: `devloop doctor` and `devloop status` continue to work; status shows `absent`.
- **Invalid config**: If present but malformed or invalid, reported as an error.
- **No network calls**: All validation is local and read-only.

MVP-0 proves that the project can maintain local contracts before adding automation.

## MVP-1: Low-friction cycles and state

Goal: reduce manual setup and make cycles easier to create and manage.

Implemented or in progress:

- `devloop init`: creates the minimum project structure (`.ai-loop/`, `.ai-loop/project.md`, `.ai-loop/cycles/`).
- `devloop cycle new "<task description>"`.
- `devloop cycle set-status <cycle-id> <status>`: updates the cycle status in `meta.yaml`.
- `devloop cycle complete <cycle-id>`: marks a cycle as `completed`.

`devloop cycle set-status` is a low-friction cycle management command that enables updating cycle status without manual file editing. It is idempotent and validates both the cycle ID and status values against the accepted list.

`devloop cycle complete` is a convenience command equivalent to `devloop cycle set-status <cycle-id> completed`. It provides a shorter, more intuitive way to mark cycles as completed while preserving all other fields in `meta.yaml`.

This moves beyond the report-only nature of MVP-0 by enabling actual cycle status management while preserving all other fields in `meta.yaml`.

`devloop init` is a low-friction setup command that creates the basic project structure without calling AI or executing external commands. It is idempotent and preserves existing files.

This moves beyond the report-only nature of MVP-0 by enabling actual project initialization.

## MVP-2: Declarative model configuration contract

Goal: define a stable model/provider/role/preference contract before any direct model invocation.

**Status: COMPLETED**

Implemented features:

- `.ai-loop/config/models.yaml` as the richer model configuration contract;
- support for local OpenAI-compatible endpoints (for example, local vLLM);
- explicit API key modes: `none`, `optional`, `required`;
- role mapping and role aliases;
- policy defaults with `model_calls_allowed: false`;
- `devloop model check`: validates configuration (local, read-only, no network calls);
- `devloop model list`: lists providers, models, roles, and aliases (local, read-only, no network calls);
- `devloop model ping <target> --allow-call`: performs a real OpenAI-compatible `/chat/completions` ping when explicitly authorized (requires dual authorization: `policy.model_calls_allowed: true` + `--allow-call` flag).

This phase includes the model configuration contract and the optional network call for ping validation.

For details, see [Supervisor Config](supervisor-config.md).

## MVP-3: Supervisor model calls

Goal: allow a configured supervisor AI to generate next steps, plans, reviews, and corrections.

Possible features:

- `devloop supervisor check`;
- `devloop next`;
- `devloop plan`;
- `devloop review`;
- configurable supervisor model;
- task granularity profiles;
- model provider abstraction;
- token and budget limits.

The supervisor should be a real model call, not just a deterministic template.

## MVP-4: Agent plugin / protocol mode

Goal: allow external agents to interact with `devloop` directly.

Possible interfaces:

- CLI JSON mode;
- local API;
- MCP server;
- file-based protocol;
- plugins/adapters for agents.

Possible features:

- get current task;
- get allowed paths;
- submit evidence;
- submit report;
- request review;
- mark cycle status;
- retrieve next action.

This phase reduces copy/paste and makes `devloop` useful as a protocol layer.

## MVP-5: Autonomous orchestrator

Goal: allow `devloop` to run a supervised development loop.

Possible features:

- `devloop run`;
- automatic cycle creation;
- supervisor-driven task selection;
- worker invocation;
- evidence collection;
- review loop;
- correction loop;
- human checkpoints;
- pause/resume;
- budget control.

This phase turns `devloop` into an autonomous or semi-autonomous orchestrator.

## Future: Bootstrap flows and ingestion

Short-term future (after MVP-0):

The following commands are conceptual future interfaces, not current MVP-0 commands:

- `devloop start "<idea>"`: Start from natural language description.
- `devloop ingest <paths...>`: Ingest existing documentation.
- `devloop start --from-ingested`: Start from previously ingested context.
- `devloop start --from <path>`: Start from specific documentation files.
- Automatic context synthesis from README, docs/, and project metadata.
- AI supervisor interprets ideas and proposes vision, objectives, plan, and next task.

Bootstrap flows should:

- Require minimal manual setup;
- Preserve existing documentation formats;
- Extract context without requiring reformatting;
- Allow human review and refinement of proposed context;
- Support resumption from existing `.ai-loop/` state.

## Future: Safety, rollback, multi-agent workflows

Longer-term capabilities:

- sandboxed execution;
- branch management;
- rollback strategy;
- policy engine;
- multi-worker orchestration;
- task queue;
- project memory;
- long-horizon planning;
- web UI;
- background daemon;
- richer evidence analysis.

## Evolution principles

1. **Start safe**: report-only first.
2. **Reduce friction**: do not require heavy documentation for basic use.
3. **Automate progressively**: manual mode, plugin mode, autonomous mode.
4. **Keep humans in control**: require approval for sensitive decisions.
5. **Stay agnostic**: no hard dependency on one model, provider, or agent.
6. **Keep state local and inspectable**: prefer file-based contracts.
7. **Make autonomy configurable**: support micro, balanced, yolo, and deep profiles.

## H3 — Post-write-report documentation status

Status: implemented.

The `devloop cycle advise` command now supports optional advisory persistence through:

    devloop cycle advise <cycle-id> --role supervisor --allow-call --write-report

Implemented behavior:

- without `--write-report`, the command remains stdout-only and does not mutate files;
- with `--write-report`, the command writes only `.ai-loop/cycles/<cycle-id>/advisory.md`;
- existing `advisory.md` files are not overwritten;
- the existing-report case fails before model transport, avoiding unnecessary calls;
- persisted reports contain sanitized metadata and advisory text;
- raw prompts, raw payloads, raw response JSON, headers, authorization values, API keys, environment values, and hidden chain-of-thought are not persisted.

Current deliberate limitations:

- no `--overwrite-report` flag;
- no timestamped advisory history;
- no autonomous shell execution;
- no external agent execution;
- no automatic `.env` loading;
- no raw transport persistence.

## H5 — Supervisor prompt advisory persistence semantics

Status: implemented and manually validated.

The supervisor advisory prompt now explicitly distinguishes the normal cycle artifact
`report.md` from the persisted model advisory file `advisory.md`.

Clarified contract:

- `devloop cycle advise <cycle-id> --role supervisor --allow-call` remains advisory-only and stdout-only by default;
- `devloop cycle advise <cycle-id> --role supervisor --allow-call --write-report` writes only `.ai-loop/cycles/<cycle-id>/advisory.md`;
- `--write-report` does not write or update `report.md`;
- `cycle advise` does not generate or update `plan.md`, `prompt.md`, `summary.md`, or `report.md`;
- `plan.md`, `prompt.md`, and `summary.md` are optional context artifacts;
- missing optional artifacts alone should not imply low readiness;
- for transport/configuration or advisory-persistence validation cycles, a minimal artifact set such as `meta.yaml`, `task.md`, and `report.md` may be sufficient.

Manual validation after H5 confirmed that the model advisory no longer confused
`report.md` with `advisory.md`, and did not classify a minimal validation cycle
as low readiness only because optional artifacts were absent.
