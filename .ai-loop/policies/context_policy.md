# Context policy

## Purpose

This policy defines how context should be selected for prompts and reports.

## Principle

Use the smallest context that is sufficient for the current task.

Too much context can degrade model performance, especially for local or constrained models.

## Context priority

Prompt context should usually prioritize:

1. current task;
2. cycle type;
3. relevant acceptance criteria;
4. relevant architecture constraints;
5. relevant allowed paths;
6. relevant commands;
7. recent cycle summaries only when needed;
8. selected code snippets or file summaries.

## Avoid

Avoid including:

- entire repositories;
- all previous cycles;
- all documentation;
- long unrelated logs;
- large test outputs unless needed;
- repeated model outputs;
- stale plans from unrelated cycles.

## Repo map concept

A future version may implement a compact repository map inspired by tools such as Aider.

The goal would be to provide useful structure without overwhelming the model.

This should be optional and should not require Aider as a dependency.

## Context artifacts

Each cycle may include:

```text
context.md
```

This should explain what context was used for that cycle and why.

## Truncation and summarization

When outputs are too large, the tool may:

- store full logs as files;
- include summaries in reports;
- reference file paths rather than embedding everything;
- require human inspection for large or ambiguous outputs.
