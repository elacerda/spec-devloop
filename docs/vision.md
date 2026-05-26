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

## Vision and principles

The project is governed by a set of principles that define its architecture and evolution.

### Model-agnostic is not model-less

The project does not depend on a specific model or provider. However, this does not mean the model is absent or irrelevant. On the contrary, the **supervisor AI is central** to the project: it defines scope, recommends acceptance or correction, and orchestrates the cycle. Model-agnostic means flexibility in choosing the model, not removing the model from the equation.

### `.ai-loop` starts minimal and grows evolutively

The `.ai-loop/` directory should begin with the smallest possible set of files to start the loop, then grow as needs emerge. This avoids over-engineering and allows the project to evolve based on real usage, not assumptions.

### Separation of roles, not physical models

The project separates **roles**, not physical models:

- **Supervisor/orchestrator**: defines scope, recommends acceptance or correction, orchestrates the cycle
- **Worker/troubleshooter**: executes tasks, generates code, produces diffs
- **Human**: approves plans, reviews evidence, decides when the cycle is complete

The same model may act as supervisor in one step and worker in another. Models may be different or the same.

### Deterministic prompt as auxiliary infrastructure

The `devloop cycle prompt <cycle-id>` command is an auxiliary infrastructure: it provides a context packet, fallback, or deterministic prompt for manual execution. It is not the main future flow, nor is it an error or legacy to be removed.
