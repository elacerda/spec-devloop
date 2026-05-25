# Development loop protocol

## Purpose

This file defines the protocol that `spec-devloop` should support.

The protocol is tool-independent. It should work with manual copy/paste, Codex CLI, Cline, Roo, Continue, Aider, future internal agents, or other tools.

## Core loop

A normal implementation cycle follows this shape:

```text
cycle_created
  -> task_defined
  -> plan_requested
  -> plan_received
  -> plan_reviewed
  -> execution_authorized
  -> execution_completed
  -> evidence_collected
  -> report_generated
  -> human_decision_recorded
```

## Required human checkpoints

A human should approve or explicitly acknowledge:

1. the task before implementation;
2. the plan before execution;
3. the final report before moving to the next cycle.

The MVP may implement these checkpoints as files and CLI prompts rather than interactive UI.

## Cycle types

The protocol should distinguish at least these cycle types:

```text
implementation
bugfix
test-only
documentation
refactor
spec-change
investigation
```

The default cycle type should be `implementation`.

## Spec-change cycles

A normal implementation cycle must not modify foundational specifications.

A cycle that changes foundational specs must be explicitly marked as:

```text
type: spec-change
```

Spec-change cycles should:

- have a justification;
- be isolated from normal implementation code changes;
- update decision records when appropriate;
- require explicit human approval;
- not be silently performed by an agent.

## Agent independence

The protocol must not assume a specific external agent.

It must accept artifacts produced by:

- humans;
- Cline;
- Codex CLI;
- Roo;
- Continue;
- Aider;
- a local model;
- a remote model;
- an internal future agent.

The protocol only requires that artifacts be saved in expected files or provided through CLI commands.

## Model independence

The protocol must not assume a specific model provider.

Model use is optional. A user may run the complete MVP manually without configuring a model.

## Evidence requirements

A cycle is not complete just because an agent reports success.

The report should be based on evidence such as:

- git status;
- git diff;
- command outputs;
- test results;
- lint results;
- generated artifacts;
- recorded human decisions.

## Failure handling

The loop should stop or request intervention when:

- tests fail;
- configured required commands fail;
- the plan violates specs;
- the diff touches forbidden paths;
- an agent attempts to change foundational specs in a normal cycle;
- the same failure repeats;
- the agent output is malformed or too broad;
- the task scope expands without approval;
- the worktree has unreviewed changes from a previous cycle.

## Context discipline

Prompts should be compact and task-relevant.

The tool should avoid dumping the entire repository or all specs into every prompt. It should prioritize:

1. task definition;
2. relevant foundational constraints;
3. relevant architecture sections;
4. allowed paths;
5. acceptance criteria;
6. recent cycle summaries when needed.

This principle is inspired by context-minimizing tools such as Aider's repo-map approach, but `spec-devloop` should not depend on Aider.

## Cycle artifact principle

Each cycle should be reconstructable from local artifacts.

A future user should be able to inspect a cycle directory and understand:

- what was requested;
- what was planned;
- what was approved;
- what changed;
- what tests ran;
- what failed or passed;
- what decision was made.
