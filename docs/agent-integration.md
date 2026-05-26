# Agent Integration

`spec-devloop` should support external agents without depending on any specific one.

This document describes the future plugin/protocol direction.

## Goal

Allow agents to use `devloop` as the state, contract, and evidence layer for development tasks.

An agent should not need to infer everything from ad-hoc prompts. It should be able to ask `devloop` for structured information.

## Possible agent questions

- What is the current project?
- What is the current cycle?
- What is the next task?
- What files may I modify?
- What commands should I run?
- What output format should I provide?
- How do I submit evidence?
- How do I signal completion or blockage?

## Possible interfaces

### CLI JSON

Example future command:

```bash
devloop cycle current --json
```

### File protocol

Agents read and write structured files under `.ai-loop/`.

### Local API

A local HTTP server exposes state and accepts evidence.

### MCP server

`devloop` exposes tools/resources to MCP-capable agents.

### Editor/agent plugins

Adapters for Cline, Roo, Continue, Codex CLI, Aider, or future agents.

## Core contracts

An integration should define:

- cycle identity;
- status;
- task;
- allowed paths;
- forbidden paths;
- commands;
- evidence requirements;
- report schema;
- completion criteria.

## Agent-agnostic principle

Adapters may be tool-specific, but the core should not be.

The core concepts should work regardless of whether the worker is:

- Cline;
- Qwen through Cline;
- Codex CLI;
- Roo;
- Continue;
- Aider;
- an internal worker;
- another future agent.

## Evidence submission

A future worker may submit:

- diff summary;
- changed files;
- command output;
- test results;
- lint results;
- error logs;
- notes;
- questions;
- blockers.

## Status transitions

Agents should not freely mutate state without policy.

Possible future transition flow:

```text
ready_for_worker → in_progress → waiting_review → completed
                                      ↓
                                   blocked
                                      ↓
                                ready_for_worker
```

The supervisor or human may approve transitions depending on policy.

## Safety

Agent integration must respect:

- explicit file scope;
- command permissions;
- human checkpoints;
- audit logs;
- rollback strategy;
- token and runtime budgets.
