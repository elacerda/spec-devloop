# Decision 0005: `devloop cycle advise` model-backed guidance contract

## Status

Accepted.

## Context

`spec-devloop` now has a safe model configuration and connectivity baseline:

- `.ai-loop/config/models.yaml` as the declarative model contract;
- `devloop model check` and `devloop model list` for local validation and inspection;
- `devloop model ping <target> --allow-call` as the first explicitly authorized real HTTP call to an OpenAI-compatible endpoint.

`devloop model ping` verifies connectivity and basic request/response viability, but it does not perform cycle reasoning or produce development guidance.

The next capability should provide useful model-backed guidance for a cycle while preserving project principles:

- local-first;
- spec-first;
- human-governed;
- model-agnostic;
- backend-agnostic;
- agent-agnostic.

The first capability after `model ping` must remain advisory-only and non-autonomous.

## Decision

Introduce the first model-backed cycle command as a **non-mutating advisory command**.

### Command name and shape

```bash
devloop cycle advise <cycle-id> --role supervisor --allow-call
```

`advise` is selected over alternatives like `review` because it communicates recommendation/report intent more clearly and avoids implying execution or approval workflow side effects.

`--role` remains available for explicit role selection, with default role `supervisor`.

### Authorization requirements

The command is allowed to call a model only when both conditions are true:

1. `policy.model_calls_allowed: true` in `.ai-loop/config/models.yaml`;
2. explicit CLI flag `--allow-call`.

If either condition is missing or false, execution must stop before transport.

### Allowed inputs (initial conservative scope)

The initial command may read only scoped cycle/project artifacts, such as:

- `.ai-loop/project.md`;
- cycle metadata;
- cycle task/spec files;
- existing cycle prompt/summary artifacts, if present.

Reading arbitrary repository files is not part of this initial contract.

### Output contract

The command must print a stable, human-readable CLI report including:

- target cycle id;
- selected role/model/provider;
- authorization status;
- `attempted_transport`;
- result;
- advisory report text;
- explicit safety note that no files were modified.

Output must not print secrets, Authorization headers, raw request headers, or hidden chain-of-thought.

### Non-mutation and non-autonomy guarantees

The command must not:

- edit files;
- run shell commands;
- call agents;
- commit or push;
- execute tasks autonomously.

### Persistence contract (initial version)

The initial command is stdout-only.

It must not persist model response content, advisory reports, prompts, payloads, or headers.

Any persistence capability (for example `--write-report`) is future work and must be introduced only by a separate explicit ADR.

### Failure behavior and exit codes

Reuse existing categories:

- exit code `2`: config/usage/policy errors; no transport attempted;
- exit code `3`: runtime/network/model-response errors; transport attempted;
- exit code `0`: success.

### Out of scope

The following are explicitly excluded from this decision:

- autonomous supervisor loop;
- task execution;
- shell command execution;
- file mutation;
- commits/pushes;
- fallback orchestration;
- streaming;
- tool calling;
- benchmarking;
- multi-agent workflows.

### Testing strategy for implementation phase

Implementation should use injected/fake transport tests only, without real network calls.

Tests should verify:

- blocked paths do not attempt transport;
- no files are modified;
- secrets are not printed;
- advisory output remains stable enough for users;
- invalid config exits before model call.

## Relationship to existing commands

- `devloop model ping`: connectivity and basic endpoint viability only; no cycle guidance.
- `devloop cycle prompt` (if present): local/manual prompt-generation support without model-backed advisory call.
- future autonomous supervisor commands: separate future scope; not defined by this ADR.

## Consequences

Positive:

- delivers first useful model-backed cycle guidance while preserving strict human control;
- keeps initial operational risk low through advisory-only, non-mutating behavior;
- maintains clear safety boundary between model insight and autonomous execution.

Tradeoffs:

- no automatic execution or persistence in initial version;
- users must manually copy/apply recommendations;
- richer orchestration remains deferred to future decisions.
