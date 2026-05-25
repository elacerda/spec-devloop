# Model policy

## Purpose

This policy defines how language models may be used by `spec-devloop`.

## Model-agnostic requirement

`spec-devloop` must not depend on a specific model, provider, protocol, or API.

Supported or future model providers may include:

- no model provider;
- OpenAI-compatible endpoints;
- vLLM;
- Ollama;
- LM Studio;
- OpenAI API;
- Anthropic API;
- local mock providers;
- other future providers.

These must be treated as optional provider integrations, not core assumptions.

## No-model mode

The MVP must support operation without any model provider configured.

In no-model mode, the tool can still:

- validate specs;
- create cycles;
- generate template prompts;
- accept user-provided plans;
- collect git diff;
- run commands;
- generate reports;
- record human decisions.

## Model roles

When model integration exists, models may be used for:

- summarizing context;
- drafting prompts;
- reviewing plans;
- scoring risk;
- summarizing diffs;
- generating report drafts;
- suggesting next microtasks.

Models should not be the final authority for:

- architecture decisions;
- accepting a failed test run;
- bypassing policies;
- changing foundational specs;
- expanding scope.

## Constrained model behavior

Prompts should instruct models to:

- stay within the task;
- avoid broad refactors unless requested;
- produce structured output;
- cite the files or evidence they used;
- refuse to proceed if context is insufficient;
- avoid changing specs unless the cycle type is `spec-change`.

## Degenerative loop handling

Some models may enter repetitive or low-quality loops under large context, ambiguous tasks, or excessive autonomy.

The system should detect or mitigate this by:

- limiting task scope;
- limiting prompt size;
- limiting output size;
- requiring schemas where possible;
- stopping after repeated failures;
- preferring mechanical evidence over claims;
- keeping human approval checkpoints.

## Provider configuration

Provider configuration belongs in:

```text
.ai-loop/config/providers.yaml
```

Provider-specific behavior must not leak into the core protocol.
