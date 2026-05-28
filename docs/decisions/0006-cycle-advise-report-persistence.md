# 0006 — Optional persistence for cycle advisory reports

Status: Proposed

Date: 2026-05-28

## Context

`devloop cycle advise <cycle-id> [--role ROLE] --allow-call` currently performs
an explicitly authorized model-backed advisory call and prints sanitized metadata
plus advisory text to stdout.

The command is intentionally advisory-only and non-mutating:

- it does not modify files;
- it does not execute shell commands;
- it does not invoke agents;
- it does not perform autonomous execution;
- it does not persist prompts, payloads, reports, or model responses;
- it does not print raw payloads, raw response JSON, Authorization headers, or API keys;
- it does not expose hidden chain-of-thought.

This stdout-only behavior was the right first boundary for validating real model
transport. However, a later workflow will benefit from optional persistence of
the advisory text as cycle evidence, as long as persistence remains explicit,
human-governed, and safe by default.

## Decision

Add a future explicit opt-in persistence mode for cycle advisory output:

```bash
devloop cycle advise <cycle-id> [--role ROLE] --allow-call --write-report
```

This ADR defines the contract for that future option. It does not implement it.

When `--write-report` is absent, the command must remain stdout-only and must not
write advisory output to disk.

When `--write-report` is present and all existing gates pass, the command may
persist a report under the target cycle directory using a deterministic,
project-local path.

## Proposed report location

Initial proposed path:

```text
.ai-loop/cycles/<cycle-id>/advisory.md
```

Rationale:

- keeps advisory evidence local to the cycle;
- avoids changing `report.md`, which may remain a human-authored execution report;
- avoids timestamped file sprawl for the first implementation;
- remains easy to inspect, diff, remove, and commit.

A future ADR may introduce timestamped advisory history if repeated advisory
runs need to be retained.

## Report content

The persisted report should be human-readable Markdown.

It should include sanitized command metadata:

- cycle id;
- requested role;
- resolved model key;
- backend model name;
- provider key;
- input artifact list;
- transport status;
- advisory generation timestamp in UTC;
- safety note that no files were modified except the explicit report write.

It should include the model-generated advisory text exactly as returned after
successful response extraction, without raw response JSON or hidden reasoning.

It must not include:

- API keys;
- Authorization headers;
- raw request payload;
- raw response JSON;
- environment variable values;
- hidden chain-of-thought;
- full endpoint URLs containing query strings or fragments;
- any non-allowlisted file content.

## Overwrite behavior

The first implementation should be conservative.

Recommended behavior:

- if `advisory.md` does not exist, create it;
- if `advisory.md` already exists, fail with a clear error unless an additional
  future overwrite flag is introduced;
- do not silently overwrite existing advisory evidence.

A future ADR may define `--overwrite-report` or timestamped report files.

## Gates

`--write-report` must not weaken existing gates.

The command must still require:

- valid `.ai-loop/config/models.yaml`;
- valid target cycle;
- `policy.model_calls_allowed: true`;
- explicit `--allow-call`;
- successful role/model/provider resolution;
- successful model transport;
- valid assistant advisory content.

If preparation fails, no report is written.

If transport fails, no report is written.

If report writing fails, the command should report a non-zero exit code and a
sanitized error.

## Exit-code implications

Existing exit-code meanings should be preserved:

- `0`: successful advisory call and, when requested, successful report write;
- `2`: config, usage, policy, cycle, or report precondition failure;
- `3`: runtime, network, model-response, or report-write runtime failure.

The CLI output should make report persistence explicit, for example:

```text
report_written: true
report_path: .ai-loop/cycles/c-001/advisory.md
```

When `--write-report` is absent:

```text
report_written: false
```

## Safety boundaries

`--write-report` permits only one mutation: writing the explicit advisory report
file.

It must not permit:

- arbitrary file writes;
- shell execution;
- agent execution;
- autonomous implementation;
- streaming side effects;
- tool-calling side effects;
- fallback orchestration;
- mutation of `task.md`, `plan.md`, `prompt.md`, `summary.md`, or `report.md`;
- mutation of `.ai-loop/config/models.yaml`;
- commit or push operations.

## Consequences

Positive consequences:

- advisory output can become auditable cycle evidence;
- users can commit advisory reports deliberately;
- repeated manual workflows become easier to review;
- persistence remains explicit and human-governed.

Tradeoffs:

- introduces the first intentional mutation in `cycle advise`;
- requires careful tests to ensure no unintended files are modified;
- requires clear overwrite semantics;
- report files may contain model-generated text that users should review before
  committing.

## Non-goals

This ADR does not define:

- autonomous execution;
- shell execution;
- agent invocation;
- tool calling;
- streaming;
- fallback orchestration;
- multi-agent workflows;
- automatic commits or pushes;
- timestamped advisory history;
- report overwriting;
- persistence of raw prompts, payloads, or response JSON.

## Testing expectations for future implementation

A future implementation should include tests for:

- stdout-only behavior remains unchanged when `--write-report` is absent;
- `--write-report` creates only `.ai-loop/cycles/<cycle-id>/advisory.md`;
- existing `advisory.md` is not overwritten silently;
- no report is written on config, policy, cycle, role, transport, or response failure;
- report content contains sanitized metadata and advisory text;
- report content excludes API keys, Authorization headers, raw payloads, and raw
  response JSON;
- CLI output reports `report_written` and `report_path`;
- file mutation boundaries are enforced.

