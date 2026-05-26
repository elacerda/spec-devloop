# Vision

`spec-devloop` exists to make AI-assisted development easier to control, automate, audit, and scale.

The project is based on a practical workflow:

1. A human has a project, idea, bug, or implementation goal.
2. A supervisor AI analyzes the project state and decides the next step.
3. A worker AI or external agent implements that step.
4. Evidence is collected.
5. The supervisor reviews the result.
6. The loop either corrects the task or advances to the next one.

The long-term goal is to make this loop automatic where safe, explicit where necessary, and always recoverable.

## Product thesis

`spec-devloop` is not just a documentation validator and not merely a prompt generator.

It is a local orchestration layer for AI-assisted development.

It should help users answer:

- What are we building?
- What is the current implementation goal?
- What should happen next?
- How large should the next task be?
- Which files may the worker modify?
- What evidence proves the task succeeded?
- Should the result be accepted, corrected, or rolled back?
- What is the next cycle?

## Model-agnostic is not model-less

The project does not depend on a specific model or provider.

However, this does not mean that models are peripheral. The supervisor/orchestrator AI is central to the future product.

`model-agnostic` means the user should be able to choose the model and backend:

- local vLLM model;
- Ollama model;
- OpenAI-compatible endpoint;
- remote API;
- future provider;
- same model for supervisor and worker;
- different models for supervisor and worker.

## Agent-agnostic is not agent-less

The project should not depend on a specific external agent.

However, agent integration is a core future direction.

A worker may be:

- Cline;
- Roo;
- Continue;
- Codex CLI;
- Aider;
- a custom script;
- an MCP-enabled agent;
- an internal worker implemented by `devloop`;
- the same model used by the supervisor.

## Roles, not necessarily different models

The project separates roles:

- **Human/operator**: intent, preferences, approvals, risk decisions.
- **Supervisor/orchestrator**: planning, decomposition, review, correction, advancement.
- **Worker/executor**: implementation, command execution, tests, reports.
- **Devloop**: persistent state, contracts, policies, evidence, integration surface.

The same model may play multiple roles. The roles define responsibilities, not physical infrastructure.

## Low-friction first

The project must not turn AI-assisted development into bureaucracy.

Documentation and specs should improve results, but basic usage should require little ceremony.

A good user experience should allow:

```bash
devloop start "Build a CLI that consumes LSST alerts"
devloop next
devloop run
```

Those commands may not exist yet, but they express the target experience.

The system should ask for more information only when needed, infer from local context when possible, and allow specs to grow incrementally.

## Manual mode is not the final product

The current human-mediated workflow is valuable:

- it is safe;
- it is debuggable;
- it works before full automation exists;
- it allows rapid design iteration.

But it should be documented as a mode, not as the destination.

The long-term direction is to automate the interactions between supervisor, worker, evidence collection, review, and next-step selection.

## Human-governed autonomy

The goal is not uncontrolled autonomy.

The goal is configurable autonomy.

Different projects may require different levels of control:

- strict microtask mode;
- balanced mode;
- high-autonomy yolo mode;
- expensive deep-analysis mode.

Humans should be able to decide how much autonomy to allow and where approval is mandatory.

## Success criteria

The project succeeds when a user can:

1. describe an idea or point `devloop` at an existing project;
2. let an AI supervisor build or update the implementation plan;
3. choose a granularity profile;
4. let workers execute cycles;
5. review evidence and decisions;
6. resume later without losing context;
7. switch models or agents without rewriting the project workflow.
