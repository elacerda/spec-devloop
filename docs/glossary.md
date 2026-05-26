# Glossary

## Agent

A tool or process that can act on a task, usually by reading context, editing files, running commands, and reporting results.

## Autonomous orchestrator mode

A future mode where `devloop` calls or embeds a supervisor AI and drives the development loop with limited human checkpoints.

## Cycle

A bounded unit of development work.

A cycle may include task, plan, execution, evidence, review, and final status.

## Devloop

The local coordination layer that stores state, contracts, evidence, policies, and integration surfaces.

## Evidence

Proof that a task was executed and validated.

Examples:

- test output;
- command logs;
- diff summary;
- changed file list;
- screenshots;
- human review notes;
- benchmark results.

## Human/operator

The person who defines intent, chooses autonomy level, approves sensitive decisions, and can override the system.

## Manual mode

A mode where the human mediates between supervisor and worker, often by copy/paste.

## Model-agnostic

The project does not depend on a specific model.

## Agent-agnostic

The project does not depend on a specific agent or editor tool.

## Backend-agnostic

The project does not depend on a specific provider or execution backend.

## Supervisor/orchestrator

The AI role that plans, decomposes, delegates, reviews, corrects, and advances the loop.

## Worker/executor

The role that performs implementation work, edits files, runs commands, and produces evidence.

## Task granularity

The size and ambition of each task delegated by the supervisor.

## `micro`

A careful task granularity profile with small tasks and frequent checkpoints.

## `balanced`

A moderate task granularity profile intended as a default.

## `yolo`

A high-autonomy task granularity profile with larger tasks and fewer checkpoints.

## `torra-token` / `deep`

A high-context, high-analysis task granularity profile for hard design, debugging, review, and architecture work.
