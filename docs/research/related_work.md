# Related work and positioning

This document records projects and ideas that influence `spec-devloop`.

The purpose is not to copy them or depend on them in the MVP. The purpose is to position `spec-devloop` clearly.

## GitHub Spec Kit

Relevant ideas:

- specification-first development;
- constitution/spec/plan/tasks style artifacts;
- small implementation tasks derived from specs;
- agent-facing prompt artifacts.

Potential influence:

- templates for specs, plans, tasks, and checklists;
- future import/export compatibility;
- stronger spec discipline.

Positioning:

```text
Spec Kit helps define what should be built.
spec-devloop governs the operational cycle around building it.
```

## Aider

Relevant ideas:

- AI pair programming with git-aware workflows;
- compact repository maps;
- minimizing context sent to models;
- lint/test integration.

Potential influence:

- future `repo-map` command;
- context minimization policy;
- command-based evidence collection.

Positioning:

```text
Aider can be an executor.
spec-devloop can govern cycles around Aider or similar tools.
```

## Cline, Roo, Continue, Codex CLI

Relevant ideas:

- practical developer-facing agents;
- IDE or terminal integration;
- model-backed planning and editing.

Potential influence:

- future adapters;
- prompt templates;
- manual executor workflows.

Positioning:

```text
These tools are possible executors.
They should not be core dependencies.
```

## SWE-agent, mini-swe-agent, OpenHands

Relevant ideas:

- action/observation loops;
- tool boundaries;
- sandbox/workspace abstractions;
- model-agnostic agent execution;
- software engineering agents.

Potential influence:

- future internal restricted agent;
- action logs;
- workspace safety patterns;
- lifecycle control.

Positioning:

```text
These are closer to agent platforms.
spec-devloop starts as a governance layer, not as a full autonomous agent.
```

## Agents SDKs and tool-calling frameworks

Relevant ideas:

- separation of model, tools, state, guardrails, and tracing;
- structured tool execution;
- multi-step workflows.

Potential influence:

- future provider/adapter abstractions;
- tracing and action logs.

Positioning:

```text
Useful architecture vocabulary, but not required for MVP.
```

## Summary

`spec-devloop` should import principles, not heavy dependencies, during the MVP.

Imported principles:

1. Specs and tasks should be explicit artifacts.
2. Context should be compact and task-relevant.
3. Agent/tool actions should be separated from observations/evidence.
4. Human checkpoints should remain central.
5. External agents should be adapters, not assumptions.
