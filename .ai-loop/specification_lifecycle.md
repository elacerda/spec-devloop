# Specification lifecycle

## Purpose

This document defines how specifications, configuration files, state files, and generated cycle artifacts relate to each other.

This distinction is central to the project.

## File classes

`spec-devloop` recognizes four conceptual classes of files.

### 1. Foundational specifications

These define the identity and governing rules of the project.

Policies are **foundational specifications specialized by role**.

Examples:

```text
.ai-loop/project.md
.ai-loop/architecture.md
.ai-loop/protocol.md
.ai-loop/specification_lifecycle.md
.ai-loop/policies/model_policy.md
.ai-loop/policies/agent_policy.md
.ai-loop/policies/context_policy.md
.ai-loop/policies/acceptance_policy.md
.ai-loop/policies/failure_modes.md
```

They are high-authority documents.

They may change, but only through explicit spec-change cycles or direct human-maintained updates.

### 2. Operational configuration

These define mechanically consumable settings.

Examples:

```text
.ai-loop/config/commands.yaml
.ai-loop/config/allowed_paths.yaml
.ai-loop/config/providers.yaml
.ai-loop/config/adapters.yaml
```

They may change more often than foundational specs, but still influence execution and validation.

### 3. Generated cycle artifacts

These are created during cycles.

Examples:

```text
.ai-loop/cycles/0001/task.md
.ai-loop/cycles/0001/agent_plan.md
.ai-loop/cycles/0001/plan_review.md
.ai-loop/cycles/0001/execution_result.md
.ai-loop/cycles/0001/git_diff.patch
.ai-loop/cycles/0001/test_output.txt
.ai-loop/cycles/0001/report.md
.ai-loop/cycles/0001/decision.yaml
```

They are historical evidence, not governing rules.

### 4. Runtime state

These files help the CLI know the current state.

Examples:

```text
.ai-loop/state/loop_state.json
.ai-loop/state/current_cycle.json
```

They are generated or maintained by the CLI.

`state/` is managed by the CLI, but `loop_state.json` and `current_cycle.json` are not required for `devloop doctor`.

## Authority hierarchy

When files conflict, the intended authority order is:

```text
1. Foundational specifications (including policies)
2. Operational configuration
3. Human decision records
4. Cycle reports and previous artifacts
5. Runtime state
6. Agent claims
```

Agent claims have the lowest authority unless supported by evidence.

## Rule against self-modifying governance

Normal cycles must not change the rules that govern them.

In other words:

```text
A normal implementation cycle cannot rewrite foundational specifications.
```

Foundational spec changes require an explicit `spec-change` cycle or manual human edit.

## Living documentation

The project may evolve. Specs are not frozen forever.

However, evolution must be visible, deliberate, and auditable.

Recommended practice:

- normal implementation cycles change product code or tests;
- documentation cycles change non-governing docs;
- spec-change cycles change foundational specs or policies;
- decision records capture meaningful architectural changes.

## Readiness matrix

The following readiness levels are used by `devloop doctor` and by higher-level workflows.

### `ready_for_doctor`

Minimum required specs for doctor are present and parseable.

### `ready_for_manual_cycle`

`ready_for_doctor` plus managed directories exist and optional cycle templates are available.

### `ready_for_evidence_collection`

`ready_for_manual_cycle` plus git repository detected and command configuration parseable for future execution phases.

### `ready_for_model_provider`

`ready_for_doctor` plus a valid, enabled provider configuration beyond `none`.

### `ready_for_agent_adapter`

`ready_for_doctor` plus a valid, enabled adapter configuration beyond `manual`.

## Decision records

Significant changes should be recorded in:

```text
docs/decisions/
```

Decision records should be short and should explain:

- context;
- decision;
- consequences;
- alternatives considered, when useful.
