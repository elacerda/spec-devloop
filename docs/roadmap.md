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

- `devloop doctor`;
- `devloop status`;
- `devloop init --check`;
- `devloop cycle list`;
- `devloop cycle check <cycle-id>`;
- `devloop cycle prompt <cycle-id>`;
- `devloop cycle summary <cycle-id>`.

MVP-0 proves that the project can maintain local contracts before adding automation.

## MVP-1: Low-friction cycles and state

Goal: reduce manual setup and make cycles easier to create and manage.

Possible features:

- `devloop init` to create minimal structure;
- `devloop cycle new "<task>"`;
- `devloop cycle update-status`;
- state files under `.ai-loop/state/`;
- safer defaults;
- minimal project bootstrap;
- better UX for first-time users.

Principle:

The user should not need to manually create many files just to start.

## MVP-2: Supervisor model calls

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

## MVP-3: Agent plugin / protocol mode

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

## MVP-4: Autonomous orchestrator

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
