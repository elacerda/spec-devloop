# 0007: Advisory report overwrite and history policy

Status: accepted

## Context

`devloop cycle advise <cycle-id> --role supervisor --allow-call --write-report`
currently persists a sanitized advisory report to:

    .ai-loop/cycles/<cycle-id>/advisory.md

The command refuses to overwrite an existing `advisory.md`. Existing-report
failures happen before model transport, avoiding unnecessary model calls and
token usage.

The current behavior is intentionally conservative:

- no implicit overwrite;
- no timestamped advisory history;
- no raw prompt persistence;
- no raw payload persistence;
- no raw response JSON persistence;
- no hidden chain-of-thought persistence;
- no mutation outside `.ai-loop/cycles/<cycle-id>/advisory.md`.

## Decision

Keep the current conservative behavior as the default.

Do not add `--overwrite-report` yet.

Do not add timestamped advisory history yet.

Treat both overwrite and history as future extensions that require an explicit
contract before implementation.

## Rationale

Refusing to overwrite `advisory.md` keeps the first persistence contract simple,
auditable, and low risk.

Failing before model transport when `advisory.md` already exists avoids spending
tokens on a result that cannot be written.

Avoiding timestamped history for now prevents introducing unresolved retention,
cleanup, comparison, and naming-policy questions.

Avoiding overwrite for now prevents accidental loss of advisory evidence while
the project is still stabilizing the model-backed workflow.

## Consequences

Users who want to regenerate an advisory must currently delete or move
`advisory.md` manually before rerunning with `--write-report`.

The CLI does not yet support:

- `--overwrite-report`;
- timestamped advisory history;
- multiple advisory reports per cycle;
- advisory report cleanup;
- advisory report comparison.

## Future options

A future `--overwrite-report` flag may be added if it remains explicit and
preserves the same safety boundaries:

- write only advisory files;
- do not mutate cycle planning artifacts;
- do not persist raw prompts, raw payloads, raw response JSON, headers,
  authorization values, API keys, environment values, or hidden chain-of-thought;
- continue to make model transport opt-in through `--allow-call`.

A future timestamped history mode may be useful, but should be designed
separately because it introduces retention, cleanup, naming, and comparison
questions.

Possible future shapes include:

    devloop cycle advise <cycle-id> --allow-call --write-report --overwrite-report

or:

    devloop cycle advise <cycle-id> --allow-call --write-report --history

These are not part of the current contract.
