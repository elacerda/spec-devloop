# Repository Layout

This document defines the repository layout and the role of `.ai-loop/`.

## Top-level layout

```text
.
├── .ai-loop/
├── docs/
├── src/devloop/
├── tests/
├── README.md
└── pyproject.toml
```

## `.ai-loop/`

`.ai-loop/` contains operational state for the development loop.

It is where `devloop` reads and writes project-loop artifacts such as:

- project identity;
- cycles;
- state;
- policies;
- model/agent configuration;
- evidence;
- memory.

`.ai-loop/` should be minimal at first and grow incrementally.

It should not become a heavy documentation burden.

## Minimal project bootstrap

The ideal minimal bootstrap should require as little as possible.

### Current implementation

The `devloop init` command (without `--check`) creates the minimum project structure:

```text
.ai-loop/
├── project.md
└── cycles/
```

- `.ai-loop/`: root directory for project state.
- `.ai-loop/project.md`: project identity file with a simple placeholder.
- `.ai-loop/cycles/`: directory for development cycles.

### Behavior

- **Idempotent**: running `devloop init` multiple times is safe.
- **Preserves existing files**: if `.ai-loop/`, `.ai-loop/project.md`, or `.ai-loop/cycles/` already exist, they are preserved and not overwritten.
- **No AI calls**: the command does not call any AI models.
- **No external commands**: the command does not execute any external commands.
- **Local only**: all files are created within `.ai-loop/`.

### Output

When successful, `devloop init` reports:

```bash
initialized devloop project
created: .ai-loop
created: .ai-loop/project.md
created: .ai-loop/cycles
```

If files already exist, they are listed as preserved:

```bash
initialized devloop project
created: .ai-loop
preserved: .ai-loop/project.md
created: .ai-loop/cycles
```

### Placeholder content

`project.md` receives a simple, editable placeholder:

```markdown
# Project

Describe the project here.
```

This provides a starting point for users to define their project without requiring heavy documentation upfront.

## Minimal cycle layout

Current MVP-0 cycle layout:

```text
.ai-loop/cycles/<cycle-id>/
├── meta.yaml
├── task.md
└── report.md
```

Optional/future cycle files:

```text
.ai-loop/cycles/<cycle-id>/
├── plan.md
├── evidence.md
├── review.md
└── worker.md
```

## Conceptual future layout

```text
.ai-loop/
├── project.md
├── config/
│   ├── supervisor.yaml
│   ├── agents.yaml
│   ├── commands.yaml
│   └── allowed_paths.yaml
├── cycles/
│   └── <cycle-id>/
│       ├── meta.yaml
│       ├── task.md
│       ├── plan.md
│       ├── worker.md
│       ├── report.md
│       ├── evidence.md
│       └── review.md
├── state/
│   ├── current.yaml
│   └── history.jsonl
├── policies/
├── memory/
└── templates/
```

This is an evolutionary target, not a bootstrap requirement.

## Required versus optional

### Required for basic use

- project identity;
- current task or cycle.

### Recommended for better results

- acceptance criteria;
- allowed paths (`.ai-loop/config/allowed_paths.yaml`);
- test commands (`.ai-loop/config/commands.yaml`);
- reports;
- evidence.

### Optional for cycle prompt

The following files are optional and included in the prompt when present:

- `.ai-loop/architecture.md` - Project architecture documentation;
- `.ai-loop/protocol.md` - Protocol or specification details.

### Advanced

- model configuration;
- agent adapters;
- policy files;
- memory;
- templates;
- autonomous orchestration state.

## `docs/`

`docs/` contains human-facing documentation:

- vision;
- architecture;
- roadmap;
- contracts;
- design decisions;
- research.

`docs/` is not runtime state.

## `src/devloop/`

Contains the Python implementation.

Backends should remain testable without the CLI.

MVP-0 commands are report-only. Future commands may introduce controlled side effects behind explicit contracts and policies.

## `tests/`

Contains automated tests for CLI contracts, backends, validation behavior, and future orchestration components.

## Design rule

The repository layout should support progressive disclosure:

- start with a small number of files;
- add structure only when it creates value;
- keep advanced configuration optional;
- make state inspectable;
- avoid turning the tool into documentation bureaucracy.
