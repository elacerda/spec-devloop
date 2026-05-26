# Operating Modes

`spec-devloop` should support multiple operating modes with the same underlying cycle model.

## 1. Manual mode

Manual mode is the current practical workflow.

The human mediates between supervisor and worker.

```text
Human asks supervisor for next task
Supervisor proposes task/prompt
Human sends prompt to worker
Worker executes
Human returns output/evidence
Supervisor reviews
Loop advances or corrects
```

### Benefits

- works immediately;
- no provider integration required;
- maximum human control;
- easy to debug;
- safe for early project development.

### Limitations

- requires copy/paste;
- depends on the human to transfer context;
- can become repetitive;
- does not scale well to long loops.

### Status

Manual mode is supported by MVP-0 through report-only commands such as:

- `devloop cycle check`;
- `devloop cycle list`;
- `devloop cycle prompt`;
- `devloop cycle summary`.

## 2. Agent plugin / protocol mode

In this mode, external agents integrate with `devloop`.

The external agent may ask `devloop` for structured context instead of relying on the human to copy/paste.

Possible interfaces:

- CLI with JSON output;
- `.ai-loop/` files;
- local API;
- MCP server;
- editor plugin;
- agent adapter.

### Example interaction

```text
Agent: What is the next task?
Devloop: cycle c-004, status ready_for_worker, allowed files: ...
Agent: I implemented it and ran tests.
Devloop: evidence received, status waiting_review.
Supervisor: review evidence and decide next action.
```

### Benefits

- less manual transfer;
- agent-agnostic;
- easier automation;
- still compatible with external tools.

### Requirements

- stable machine-readable contracts;
- status transitions;
- evidence schema;
- permission model;
- error handling;
- logs.

## 3. Autonomous orchestrator mode

In this mode, `devloop` contains or calls an AI supervisor and can drive the development loop.

The system may:

- plan;
- create cycles;
- choose task size;
- call workers;
- collect evidence;
- review output;
- ask for correction;
- close cycles;
- request human approval.

### Benefits

- minimal user effort;
- repeatable loops;
- scalable long-running development;
- better state continuity.

### Risks

- unsafe file modifications;
- command execution risks;
- runaway loops;
- excessive token use;
- low-quality autonomous decisions;
- unclear accountability.

### Required safeguards

- explicit permissions;
- scope limits;
- sandboxing where possible;
- human checkpoints;
- audit logs;
- rollback strategy;
- configurable autonomy;
- budget limits.

## Compatibility between modes

The modes should not be separate products.

They should share:

- the same cycle model;
- the same status vocabulary;
- the same evidence concepts;
- the same policies;
- the same project state.

A project should be able to start in manual mode and later move to plugin or autonomous mode without rewriting its history.
