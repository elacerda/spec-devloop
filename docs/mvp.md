# MVP Definition

This document separates the current conservative MVP-0 from the broader product MVP.

## MVP-0: report-only foundation

MVP-0 proves that a local CLI can inspect and validate development-loop artifacts without side effects.

MVP-0 must:

- validate minimum project structure;
- validate cycle structure;
- parse required YAML files;
- validate minimal schemas;
- report missing required files;
- report optional file presence;
- detect git state when relevant;
- use stable exit codes;
- avoid modifying files;
- avoid calling models;
- avoid calling agents;
- avoid executing commands.

MVP-0 is intentionally conservative.

It is not the final product experience.

## MVP-0 current command set

- `devloop doctor`;
- `devloop status`;
- `devloop init --check`;
- `devloop cycle list`;
- `devloop cycle check <cycle-id>`;
- `devloop cycle prompt <cycle-id>`;
- `devloop cycle summary <cycle-id>`.

## Product MVP

The product MVP should demonstrate the real value proposition:

> A supervisor AI can help drive a development loop from intent to implementation evidence, while `devloop` maintains state, contracts, and auditability.

A product MVP should include:

1. minimal project bootstrap;
2. cycle creation from a user task;
3. supervisor-generated next step;
4. configurable task granularity;
5. worker instructions;
6. evidence/report capture;
7. supervisor review;
8. correction or acceptance decision;
9. low-friction user experience.

The product MVP may still be human-mediated, but it should clearly exercise the supervisor loop.

## What MVP-0 should not include

MVP-0 should not include:

- autonomous code editing;
- internal tool-calling agent;
- direct Cline automation;
- direct Roo automation;
- direct Continue automation;
- direct Codex CLI automation;
- required model provider calls;
- MCP integration;
- database;
- web UI;
- background daemon.

These are not excluded from the product. They are excluded from the initial report-only foundation.

## Product non-goals

The product should not:

- force users to write heavy documentation before starting;
- require a specific model;
- require a specific agent;
- hide unsafe operations;
- make unreviewable changes by default;
- turn every workflow into microtasks;
- assume cloud providers are required.

## Suggested milestones

### Milestone 0: report-only foundation

- CLI entrypoint;
- doctor/status/init check;
- cycle list/check/prompt/summary;
- tests;
- documentation realignment.

### Milestone 1: low-friction cycle creation

- `devloop init`: creates minimum project structure (`.ai-loop/`, `.ai-loop/project.md`, `.ai-loop/cycles/`).
- `devloop cycle new`: creates a new cycle with minimal structure.
- simple state management;
- status transitions;
- better first-run UX.

`devloop init` is idempotent, preserves existing files, does not call AI models, and does not execute external commands.

### Milestone 2: supervisor-assisted loop

- supervisor config;
- model call abstraction;
- next-step generation;
- task granularity profiles;
- review generation.

### Milestone 3: agent protocol

- JSON CLI;
- evidence submission;
- allowed paths contract;
- command contract;
- MCP/API/plugin experiments.

### Milestone 4: autonomous orchestration

- supervisor-run loop;
- worker invocation;
- evidence collection;
- correction loop;
- human checkpoints;
- rollback and safety.
