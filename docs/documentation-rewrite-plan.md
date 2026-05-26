# Documentation Rewrite Plan

This document proposes how to migrate the current documentation to the new product narrative.

## Goal

Reframe `spec-devloop` as a local AI orchestration layer, not merely a report-only validator or manual prompt generator.

## Key narrative changes

### Before

- local file-based spec-first human-in-the-loop orchestrator;
- not a coding agent in MVP;
- manual cycles and prompts;
- many report-only constraints;
- future model integration described cautiously.

### After

- local orchestration layer for AI-assisted development;
- supports manual, plugin/protocol, and autonomous modes;
- supervisor AI is central;
- worker may be external or internal;
- copy/paste is only the initial/manual mode;
- task granularity is configurable;
- UX should be low-friction;
- documentation should not become bureaucracy.

## Suggested commit sequence

### Commit 1

```text
docs: realign project vision around AI orchestration
```

Files:

- `README.md`;
- `docs/vision.md`;
- `docs/roadmap.md`.

### Commit 2

```text
docs: define operating modes and task granularity profiles
```

Files:

- `docs/operating-modes.md`;
- `docs/task-granularity.md`;
- README links.

### Commit 3

```text
docs: update architecture and repository layout
```

Files:

- `docs/architecture.md`;
- `docs/repository-layout.md`;
- `docs/glossary.md`.

### Commit 4

```text
docs: clarify supervisor config and agent integration roadmap
```

Files:

- `docs/supervisor-config.md`;
- `docs/agent-integration.md`;
- `docs/safety.md`.

### Commit 5

```text
docs: refresh manual cycle contract for current MVP
```

Files:

- `docs/manual-cycle.md`;
- `docs/mvp.md`.

## Migration notes

Do not remove truthful MVP-0 constraints.

Instead, reframe them:

- MVP-0 is the safe foundation;
- manual mode is the initial mode;
- report-only commands are current capabilities;
- automation is future direction, not current behavior.

## Review checklist

- Does the README explain the product in less than one minute?
- Is copy/paste described as a mode, not the final goal?
- Is the supervisor AI central?
- Are model/agent/backend agnosticism preserved?
- Is user friction reduced?
- Are task granularity profiles documented?
- Are MVP-0 commands still accurate?
- Are future commands clearly marked as future?
