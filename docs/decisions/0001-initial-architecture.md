# Decision 0001: Initial architecture

## Status

Accepted as initial direction.

## Context

The project began from a repeated human-in-the-loop workflow involving ChatGPT, a local or cluster-hosted model, and coding agents. The workflow worked best when tasks were small, plans were reviewed, execution was constrained, tests were run, and the human decided when to proceed.

There was concern that relying on a constrained model as the primary architect could create degenerative loops or malformed project structure.

There was also concern that building specifically around Cline would unnecessarily lock the project to one tool.

## Decision

Build `spec-devloop` as a local, file-based, spec-first, agent-agnostic and model-agnostic CLI.

The MVP will use:

- Python 3.12;
- local files;
- manual executor;
- required specs;
- optional policies and config;
- git and command evidence;
- human decisions.

The project will not initially implement:

- autonomous code editing;
- direct Cline automation;
- direct Codex CLI automation;
- internal tool-calling agent;
- required model provider calls.

## Consequences

Positive:

- simpler MVP;
- lower risk of tool lock-in;
- usable with many agents;
- usable without a model provider;
- easier auditing.

Tradeoffs:

- more manual interaction at first;
- less automation in MVP;
- adapters must be designed later.

## Future work

After the core is stable, adapters may be added for Codex CLI, Cline, Roo, Continue, Aider, or an internal restricted agent.
