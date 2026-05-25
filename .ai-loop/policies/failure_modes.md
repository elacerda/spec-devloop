# Failure modes

## Purpose

This file records known failure modes and the expected response.

## Degenerative model loop

Symptoms:

- repeated suggestions with no progress;
- circular reasoning;
- repeated failed fixes;
- increasing context without clarity;
- generic responses unrelated to evidence.

Response:

- stop the cycle;
- reduce scope;
- create a smaller task;
- require human review;
- record failure in report.

## Scope creep

Symptoms:

- plan changes unrelated files;
- plan adds features not requested;
- plan proposes refactors outside task;
- agent changes architecture unprompted.

Response:

- reject or revise plan;
- split into separate cycles;
- require explicit approval.

## Spec mutation in normal cycle

Symptoms:

- agent changes `.ai-loop/project.md`;
- agent changes policies;
- agent changes allowed paths;
- agent changes command requirements.

Response:

- fail the cycle unless cycle type is `spec-change`;
- require human review.

## Unsupported adapter assumptions

Symptoms:

- core logic assumes Cline Plan/Act;
- core logic assumes Codex CLI;
- core logic assumes vLLM/OpenAI-compatible endpoint.

Response:

- move behavior into adapter/provider;
- update architecture docs if needed.

## False success

Symptoms:

- agent reports success but tests fail;
- no commands were run;
- diff does not match report;
- changed files are omitted from summary.

Response:

- rely on evidence, not claim;
- mark cycle as `needs_fix` or `rejected`.

## Context overload

Symptoms:

- prompts become too large;
- model ignores instructions;
- model repeats irrelevant prior context;
- output becomes generic.

Response:

- reduce context;
- use summaries;
- split task;
- reference files instead of embedding full content.

## Repeated command failure

Symptoms:

- same test/lint/build error persists;
- agent makes unrelated changes;
- failure count exceeds threshold.

Response:

- stop after configured attempts;
- create an investigation cycle;
- ask for human diagnosis.
