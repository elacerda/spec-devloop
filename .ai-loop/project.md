# Project specification: spec-devloop

## Project identity

**spec-devloop** is a local, file-based, spec-first orchestrator for AI-assisted development cycles.

The CLI command should be:

```bash
devloop
```

The project should not be tied to a specific model, provider, coding agent, IDE extension, or runtime.

## Core problem

AI coding workflows often degrade when a model or agent receives too much context, ambiguous goals, or excessive autonomy. This can lead to:

- loops of repetitive or low-quality reasoning;
- uncontrolled scope expansion;
- architecture drift;
- undocumented changes;
- convincing but unreliable reports;
- agents changing rules while executing tasks;
- hard-to-audit sequences of copy/paste interactions.

The project addresses this by making the development loop explicit, local, auditable, and governed by specifications.

## Core idea

`spec-devloop` should not start as an autonomous coding agent.

Instead, it should be a **governance layer** around AI-assisted development:

```text
specifications -> task -> plan -> review -> execution -> diff/tests -> report -> human decision
```

The tool should help users keep the loop small, controlled, and evidence-based.

## Project goals

The project should:

1. Define a file-based protocol for AI-assisted development cycles.
2. Require a minimum specification package before cycles can run.
3. Generate and store cycle artifacts locally.
4. Keep a human approval step between critical phases.
5. Remain independent from any specific coding agent.
6. Remain independent from any specific language model provider.
7. Support a manual executor as the first and most general workflow.
8. Later support adapters for tools such as Codex CLI, Cline, Roo, Continue, Aider, or an internal restricted agent.
9. Keep context small and task-relevant.
10. Use mechanical evidence such as git diff, command output, and tests before accepting a cycle.

## Non-goals for the MVP

The MVP should not:

- implement a full autonomous coding agent;
- edit code directly;
- require tool calling;
- require vLLM;
- require OpenAI-compatible APIs;
- require Cline;
- require Codex CLI;
- require VSCode integration;
- require MCP;
- create commits automatically;
- alter foundational specs during normal implementation cycles;
- choose architecture without human review;
- optimize for distributed/multi-user workflows.

## Target users

Initial target users are developers or researchers who:

- already use AI coding agents;
- want more control over iterative development;
- work with local or constrained models;
- need small, auditable development cycles;
- want to preserve human review and specification discipline;
- may switch between different coding tools over time.

## Generality requirements

The project must remain:

```text
model-agnostic
agent-agnostic
backend-agnostic
provider-agnostic
IDE-agnostic
```

Any mention of a concrete tool, such as Cline, Roo, Continue, Codex CLI, Aider, vLLM, OpenAI, Anthropic, Ollama, or OpenHands, must be treated as an example, adapter, provider, or integration point. It must not become a core assumption.

## Primary MVP workflow

The first supported workflow should be the **manual executor**:

1. `devloop` creates or validates the next cycle.
2. `devloop` generates a prompt or task artifact.
3. The user gives that prompt to any agent or model.
4. The user saves the result back into the cycle directory.
5. `devloop` reviews artifacts, runs configured commands, collects evidence, and generates a report.
6. The user approves, rejects, or requests another cycle.

This workflow should work even when no model provider is configured inside `spec-devloop`.
