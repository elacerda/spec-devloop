# Agent policy

## Purpose

This policy defines how coding agents or execution tools may participate in `spec-devloop` cycles.

## Agent-agnostic requirement

The project must not depend on a specific agent.

Possible agents or executors include:

- manual copy/paste;
- Codex CLI;
- Cline;
- Roo;
- Continue;
- Aider;
- OpenHands;
- SWE-agent or mini-swe-agent-inspired tools;
- a future internal restricted agent;
- custom scripts.

These are adapters or external participants, not core assumptions.

## Default MVP executor

The default MVP executor is:

```text
manual
```

The manual executor means:

- `spec-devloop` prepares artifacts or prompts;
- the user passes them to an external tool;
- the user saves outputs back into cycle files;
- `spec-devloop` validates, audits, and reports.

## Cline/Roo/Continue/Codex position

Cline, Roo, Continue, and Codex CLI may be useful executors, but the core must not assume:

- VSCode;
- Plan/Act modes;
- a specific prompt format;
- a specific response format;
- direct API integration;
- a specific model backend.

Plan/Act can be implemented by an adapter, not by the core protocol.

## Internal agent position

A built-in internal agent may be added later, but it is not part of MVP 1.

If implemented, it must be restricted by:

- allowed paths;
- allowed commands;
- explicit cycle states;
- human checkpoints;
- test requirements;
- action logs;
- failure stop conditions.

## Agent permissions

No agent may, during a normal cycle:

- modify foundational specs;
- modify policies;
- bypass test requirements;
- mark its own work as accepted;
- create commits without approval;
- alter allowed paths to permit its own changes;
- silently expand task scope.

## Evidence over claims

Agent statements are not sufficient evidence.

The tool should prefer:

- actual file diffs;
- command outputs;
- test logs;
- linter outputs;
- recorded decisions.

## Adapter design

Adapters should translate between the generic protocol and a specific tool.

Example:

```text
generic phase: plan_requested
Cline adapter: generate Plan mode prompt

generic phase: execution_authorized
Cline adapter: generate Act mode prompt
```

The core protocol should remain unchanged when adding or removing adapters.
