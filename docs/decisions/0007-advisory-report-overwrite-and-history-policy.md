# 0007: Advisory report overwrite and history policy

Status: accepted

Update 2026-05-28: explicit `--overwrite-report` has now been implemented with
the same safety boundaries. Timestamped advisory history remains future work.

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

Explicit `--overwrite-report` is now implemented as an opt-in extension.

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

Keeping overwrite explicit prevents accidental loss of advisory evidence while
still allowing intentional regeneration when the user passes `--overwrite-report`.

## Consequences

By default, users who want to regenerate an advisory must delete or move
`advisory.md` manually before rerunning with `--write-report`, or explicitly
opt into replacement with `--write-report --overwrite-report`.

The CLI now supports explicit `--overwrite-report` when combined with `--write-report`.

The CLI does not yet support:

- timestamped advisory history;
- multiple advisory reports per cycle;
- advisory report cleanup;
- advisory report comparison.

## Future options

`--overwrite-report` has been implemented and must remain explicit. It preserves the same safety boundaries:

- write only advisory files;
- do not mutate cycle planning artifacts;
- do not persist raw prompts, raw payloads, raw response JSON, headers,
  authorization values, API keys, environment values, or hidden chain-of-thought;
- continue to make model transport opt-in through `--allow-call`.

A future timestamped history mode may be useful, but should be designed
separately because it introduces retention, cleanup, naming, and comparison
questions.

The implemented overwrite shape is:

    devloop cycle advise <cycle-id> --allow-call --write-report --overwrite-report

A possible future history shape is:

    devloop cycle advise <cycle-id> --allow-call --write-report --history

Timestamped history is not part of the current contract.
