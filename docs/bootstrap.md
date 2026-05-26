# Bootstrap Flows

This document describes the future bootstrap flows for `spec-devloop`.

## Overview

`spec-devloop` supports multiple entry points for starting a development loop. The user should not need to manually create many files to begin.

The system adapts to the available context:

- **Idea-first**: Start from a natural language description.
- **Documentation-first**: Start from existing project documentation.
- **Project-first**: Start from an existing codebase with documentation.
- **Resume**: Continue from an existing `.ai-loop/` state.

## Bootstrap by Idea

### Command (future)

```bash
devloop start "Quero criar um CLI para consumir alertas LSST via Fink"
```

### Flow

1. The user provides a natural language description of the project or task.
2. The supervisor IA interprets the idea and proposes:
   - **Visão do projeto**: high-level goal and value proposition.
   - **Objetivos**: concrete, measurable outcomes.
   - **Restrições**: known limitations, constraints, or non-goals.
   - **Plano inicial**: high-level implementation plan.
   - **Próxima tarefa**: the first bounded task to execute.
   - **Perfil de granularidade**: recommended task size profile (micro, balanced, yolo, deep).
   - **Dúvidas abertas**: questions that need clarification.

3. The user reviews and approves (or refines) the proposal.
4. The cycle is created and the loop begins.

### When to use

- New projects with no existing documentation.
- Exploratory tasks where the scope is not yet clear.
- Rapid prototyping where speed matters more than precision.

## Bootstrap by Documentation

### Command (future)

```bash
# Ingest documentation first
devloop ingest README.md docs/roadmap.md docs/architecture.md

# Then start from ingested context
devloop start --from-ingested
```

Or alternatively:

```bash
# Start directly from specific files
devloop start --from README.md --from docs/architecture.md
```

### Flow

1. The user provides one or more documentation paths.
2. The ingestion process reads and analyzes the documents.
3. The supervisor IA synthesizes:
   - **Visão do projeto**: inferred from existing documentation.
   - **Objetivos**: extracted or inferred from roadmap/requirements.
   - **Restrições**: identified from architecture/decisions.
   - **Plano atual**: current state of implementation or planned work.
   - **Lacunas**: missing information or unclear areas.
   - **Próxima tarefa**: the next logical step based on existing docs.
   - **Perfil de granularidade**: inferred from project scope and complexity.
   - **Dúvidas abertas**: questions that documentation doesn't answer.

4. The user reviews and approves (or refines) the synthesized context.
5. The cycle is created and the loop begins.

### When to use

- Existing projects with documentation but no `.ai-loop/` yet.
- Projects with architecture decisions, roadmaps, or specs.
- When you want the supervisor to understand the project context before starting.

## Bootstrap from Existing Project

### Command (future)

```bash
devloop start
```

### Flow

1. The system scans the project for:
   - `README.md`
   - `docs/` directory contents
   - `pyproject.toml`, `package.json`, or similar metadata files
   - `.ai-loop/` directory (if present)

2. If `.ai-loop/` exists, the system resumes the existing loop (see Resume flow below).

3. If documentation exists, the system uses it as context (see Bootstrap by Documentation).

4. If no documentation exists, the system prompts for an idea (see Bootstrap by Idea).

5. The supervisor IA synthesizes the current state and proposes the next step.

### When to use

- Existing codebases with some documentation.
- Projects that evolved organically and now want structured AI assistance.

## Resume from Existing State

### Command (future)

```bash
devloop start
```

### Flow

1. The system detects an existing `.ai-loop/` directory.
2. The system reads:
   - Current cycle state
   - Cycle history
   - Project identity
   - Policies and configuration
   - Memory and evidence

3. The supervisor IA:
   - Reviews the last completed work
   - Identifies the next logical step
   - Considers any blocked or pending tasks
   - Proposes the next task with updated context

4. The user reviews and approves (or refines) the proposed next step.

### When to use

- Continuing work after a break.
- Switching between projects with preserved state.
- Resuming after human intervention or correction.

## Ingestion Process

The ingestion process transforms documentation into operational context without requiring manual rewrites.

### What ingestion does

- Reads documentation files (Markdown, YAML, JSON, TOML).
- Extracts key information: goals, constraints, current state.
- Identifies project structure and file organization.
- Maps documentation to operational concepts (vision, plan, tasks).
- Creates a compact context packet for the supervisor.

### What ingestion does NOT do

- Require manual reformatting of existing docs.
- Create duplicate documentation.
- Force users to learn a new spec format upfront.
- Modify source documentation (unless explicitly requested).

### Supported source formats

- `README.md`: project overview, setup, goals.
- `docs/roadmap.md`: planned features and milestones.
- `docs/architecture.md`: system design and constraints.
- `docs/decisions/*.md`: ADRs and design decisions.
- `pyproject.toml`, `package.json`: project metadata and dependencies.
- `.ai-loop/` state files: existing loop state.

## Supervisor Synthesis Output

When starting a loop, the supervisor IA produces a synthesis that includes:

| Field | Description |
|-------|-------------|
| `vision` | High-level project goal and value proposition. |
| `objectives` | Concrete, measurable outcomes for the current phase. |
| `constraints` | Known limitations, non-goals, or hard requirements. |
| `current_plan` | The existing or proposed implementation plan. |
| `open_questions` | Questions that need clarification before proceeding. |
| `next_task` | The first bounded task to execute. |
| `granularity_profile` | Recommended task size (micro, balanced, yolo, deep). |
| `suggested_paths` | Files and directories likely to be involved. |

This synthesis becomes the initial context for the development loop.

## MVP-0 Status

MVP-0 is report-only and does not implement bootstrap flows.

Bootstrap features are planned for MVP-1 and beyond:

- MVP-1: Low-friction cycle creation and state management.
- MVP-2: Supervisor model calls for idea interpretation.
- MVP-3: Agent protocol for external tool integration.
- MVP-4: Autonomous orchestrator with full loop execution.

## Design Principles

1. **Low-friction first**: Users should be able to start with minimal ceremony.
2. **Context-aware**: The system should infer as much as possible from existing docs.
3. **Human-governed**: All proposals require human approval before execution.
4. **Incremental**: Documentation can grow as the project evolves.
5. **Format-agnostic**: Support common formats without requiring rewrites.
6. **Stateful**: Existing `.ai-loop/` state enables seamless resumption.