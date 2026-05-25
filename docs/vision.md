# Vision

`spec-devloop` exists to make AI-assisted development more controlled, auditable, and resilient.

The project is based on a simple observation: the most useful AI coding workflows often work best when a human keeps the loop small, reviews plans before execution, checks diffs and tests, and prevents the model from expanding scope.

`spec-devloop` should capture that workflow as a local protocol.

## What makes this project different

It is not primarily a coding agent.

It is a governance layer around coding agents, local models, remote models, or manual workflows.

It should help users answer:

- What exactly is the current task?
- What plan was approved?
- What evidence proves the task was completed?
- What files changed?
- Which commands were run?
- Did the agent stay inside scope?
- Is it safe to move to the next cycle?

## Long-term possibility

In later versions, the tool may support direct integrations and even a restricted internal agent.

However, the core identity should remain:

```text
spec-first
file-based
agent-agnostic
model-agnostic
human-in-the-loop
evidence-driven
```
