# Architecture

This document describes the conceptual architecture of `spec-devloop`.

## System boundary

`spec-devloop` is the coordination layer between:

- project files;
- human decisions;
- supervisor AI;
- worker agents;
- evidence collection;
- safety policies.

It is not tied to a specific editor, model, agent framework, provider, or cloud service.

## Core components

### Devloop CLI

The CLI is the primary local interface.

Current MVP-0 commands are report-only. Future commands may create cycles, call a supervisor model, expose JSON for agents, or run an autonomous loop.

### `.ai-loop/`

The `.ai-loop/` directory stores operational state.

It should contain machine-readable or semi-structured artifacts used by `devloop`:

- project identity;
- cycles;
- current state;
- policies;
- configuration;
- evidence;
- memory;
- integration metadata.

It should not become a dumping ground for heavy human documentation.

### Documentation

The `docs/` directory stores human-oriented documentation:

- product vision;
- architecture;
- roadmap;
- contracts;
- design decisions;
- research notes.

### Supervisor/orchestrator

The supervisor is responsible for reasoning about the development process.

It may:

- read project state;
- decide the next task;
- choose task granularity;
- generate worker instructions;
- review worker output;
- request correction;
- close a cycle;
- update the plan.

In early usage, the supervisor may be a human using ChatGPT manually. In future usage, it may be a configured model called by `devloop`.

### Worker/executor

The worker is responsible for implementation.

It may:

- edit files;
- run tests;
- run linters;
- produce diffs;
- produce logs;
- create reports;
- return evidence.

In early usage, the worker may be Cline/Qwen or another external tool. In future usage, workers may interact with `devloop` through an agent protocol, plugin, MCP server, or internal execution layer.

### Human/operator

The human defines intent and governs autonomy.

The human should be able to:

- choose operating mode;
- choose task granularity;
- approve sensitive actions;
- review results;
- override supervisor decisions;
- stop or pause the loop.

## Data flow

### Manual flow

```text
Human → Supervisor AI → Worker prompt → Worker agent
Human ← Worker output ← Worker agent
Human → Supervisor AI review → next/correct/finish
```

`devloop` supports this by storing cycles, tasks, reports, and evidence.

### Plugin/protocol flow

```text
Worker agent → devloop: get current task/context
Worker agent → filesystem: modify code
Worker agent → devloop: submit evidence/report
Supervisor → devloop: review and advance
```

### Autonomous flow

```text
devloop run
  → read state
  → call supervisor
  → select/create task
  → invoke worker
  → collect evidence
  → call supervisor for review
  → correct or advance
  → checkpoint human when needed
```

## State model

The central unit is the cycle.

A cycle represents one bounded development step.

A cycle may contain:

- metadata;
- task description;
- plan;
- worker instructions;
- report;
- evidence;
- review;
- status;
- links to changed files or commits.

## Cycle lifecycle

Conceptual statuses:

- `planned`: defined but not ready for execution.
- `ready_for_worker`: ready to be executed.
- `in_progress`: currently being executed.
- `waiting_review`: execution completed, awaiting review.
- `completed`: accepted and closed.
- `blocked`: cannot proceed without intervention.

MVP-0 validates status values but does not execute transitions.

## Interfaces

Future interfaces may include:

- human CLI;
- machine-readable CLI JSON;
- `.ai-loop/` files;
- local HTTP API;
- MCP server;
- plugin adapters;
- internal orchestrator.

## Non-coupling requirements

The architecture must not depend on:

- one model;
- one provider;
- one agent;
- one IDE;
- one operating system;
- one execution backend.

Specific tools may have adapters, but the core must remain independent.
