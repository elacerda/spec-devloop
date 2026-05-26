# Documentation Ingestion

> Status: future/conceptual. The commands in this document are proposed interfaces and are not current MVP-0 commands.

This document describes the ingestion mechanism for `spec-devloop`.

## Overview

Ingestion transforms existing documentation into operational context for the development loop. The goal is to avoid manual reformatting while enabling the supervisor IA to understand and act on project information.

## Core Principles

1. **No reformatting required**: Existing documentation formats are preserved.
2. **Context extraction**: Key information is extracted and structured for the supervisor.
3. **Incremental enrichment**: Context grows as more documentation is ingested.
4. **Human review**: All synthesized context is reviewed and approved by the user.

## Ingestion Flow

```text
User provides paths → Read documents → Extract context → Synthesize → Store in .ai-loop/
```

### Step 1: User provides paths

The user specifies one or more documentation sources:

```bash
devloop ingest README.md docs/roadmap.md docs/architecture.md
```

Or references previously ingested content:

```bash
devloop start --from-ingested
```

### Step 2: Read documents

The ingestion process reads the specified files:

- Markdown (`.md`)
- YAML (`.yaml`, `.yml`)
- JSON (`.json`)
- TOML (`.toml`)

### Step 3: Extract context

The system extracts:

| Concept | Source clues |
|---------|--------------|
| Project name | `README.md` title, `pyproject.toml` name |
| Vision | README overview, vision docs |
| Goals | Roadmap items, objective statements |
| Constraints | Architecture decisions, "non-goals" sections |
| Current state | Implementation status, completed items |
| Next steps | Roadmap next items, TODO comments |
| File scope | Project structure, import paths |

### Step 4: Synthesize

The supervisor IA creates a compact context packet:

```yaml
vision: "Build a CLI to consume LSST alerts via Fink"
objectives:
  - "Implement Fink API client"
  - "Add alert filtering"
  - "Create CLI interface"
constraints:
  - "Python 3.12+"
  - "No external API keys required"
current_plan:
  phase: "initial"
  steps:
    - "Set up project structure"
    - "Implement Fink client"
    - "Add CLI commands"
open_questions:
  - "Which alert fields are most important?"
  - "Should filtering be client-side or server-side?"
granularity_profile: "balanced"
```

### Step 5: Store in `.ai-loop/`

The synthesized context is stored in:

```text
.ai-loop/
  └── context/
      ├── ingestion.yaml      # Raw extracted data
      ├── synthesis.yaml      # Supervisor synthesis
      └── sources.json        # List of ingested sources
```

## Supported Documentation Types

### README.md

**Purpose**: Project overview and setup.

**Extracted**:
- Project name and description
- Installation instructions
- Basic usage examples
- Goals and value proposition

### docs/roadmap.md

**Purpose**: Planned features and milestones.

**Extracted**:
- Current phase
- Upcoming features
- Milestones and deadlines
- Priority order

### docs/architecture.md

**Purpose**: System design and constraints.

**Extracted**:
- Architecture overview
- Component responsibilities
- Technology choices
- Non-functional requirements

### docs/decisions/*.md

**Purpose**: ADRs and design decisions.

**Extracted**:
- Decisions made
- Rationale
- Alternatives considered
- Consequences

### pyproject.toml / package.json

**Purpose**: Project metadata and dependencies.

**Extracted**:
- Project name and version
- Dependencies
- Entry points
- Test configuration

### .ai-loop/state/current.yaml

**Purpose**: Current cycle state.

**Extracted**:
- Current task
- Cycle status
- Last completed work
- Pending items

## Ingestion Output

The ingestion process produces:

1. **Context packet**: A compact representation of project state.
2. **Source map**: List of ingested files with checksums.
3. **Synthesis**: Supervisor interpretation of the context.

### Context Packet Structure

```yaml
# .ai-loop/context/ingestion.yaml
version: "1.0"
ingested_at: "2024-01-01T12:00:00Z"
sources:
  - path: "README.md"
    format: "markdown"
    checksum: "sha256:abc123..."
  - path: "docs/roadmap.md"
    format: "markdown"
    checksum: "sha256:def456..."
extracted:
  project_name: "my-project"
  vision: "Build a CLI to consume LSST alerts"
  goals:
    - "Implement Fink API client"
    - "Add alert filtering"
  constraints:
    - "Python 3.12+"
  current_phase: "initial"
  next_steps:
    - "Set up project structure"
    - "Implement Fink client"
```

### Synthesis Structure

```yaml
# .ai-loop/context/synthesis.yaml
vision: "Build a CLI to consume LSST alerts via Fink"
objectives:
  - "Implement Fink API client"
  - "Add alert filtering"
  - "Create CLI interface"
constraints:
  - "Python 3.12+"
  - "No external API keys required"
current_plan:
  phase: "initial"
  steps:
    - "Set up project structure"
    - "Implement Fink client"
    - "Add CLI commands"
open_questions:
  - "Which alert fields are most important?"
  - "Should filtering be client-side or server-side?"
granularity_profile: "balanced"
suggested_paths:
  - "src/my_project/"
  - "tests/"
  - "docs/"
```

## Ingestion Commands (Future)

### `devloop ingest <paths...>`


The following commands are future conceptual interfaces. They are not implemented in MVP-0.

Ingest documentation from specified paths.

```bash
devloop ingest README.md docs/roadmap.md
devloop ingest docs/
devloop ingest README.md docs/architecture.md docs/decisions/
```

### `devloop start --from-ingested`

Start a loop using previously ingested context.

```bash
devloop start --from-ingested
```

### `devloop start --from <path>`

Start a loop using specified paths as context.

```bash
devloop start --from README.md
devloop start --from docs/roadmap.md --from docs/architecture.md
```

### `devloop context show`

Show the current context packet.

```bash
devloop context show
```

### `devloop context refresh`

Re-ingest documentation and update context.

```bash
devloop context refresh
```

## Ingestion in Practice

### Example 1: New Project with README

```bash
# Project has README.md but no docs/
devloop ingest README.md
devloop start --from-ingested
```

### Example 2: Existing Project with Roadmap

```bash
# Project has docs/roadmap.md
devloop ingest docs/roadmap.md
devloop start --from-ingested
```

### Example 3: Project with Full Documentation

```bash
# Project has comprehensive docs/
devloop ingest README.md docs/roadmap.md docs/architecture.md docs/decisions/
devloop start --from-ingested
```

### Example 4: Resume from Previous Session

```bash
# Project has .ai-loop/ with existing state
devloop start
# System detects .ai-loop/ and resumes automatically
```

## MVP-0 Status

MVP-0 does not implement ingestion.

Ingestion is planned for MVP-1 and beyond:

- MVP-1: Basic ingestion with Markdown support.
- MVP-2: Enhanced extraction with YAML/JSON support.
- MVP-3: Supervisor-driven synthesis.
- MVP-4: Automatic context enrichment.

## Design Principles

1. **Preserve source docs**: Ingestion should not modify source files.
2. **Extract, don't rewrite**: Use existing documentation as-is.
3. **Incremental**: Context grows as more docs are added.
4. **Transparent**: Users can see what was extracted and how.
5. **Reversible**: Ingestion can be refreshed or cleared.
6. **Human-governed**: All synthesized context requires approval.