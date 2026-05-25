# Acceptance policy

## Purpose

This policy defines what must be true before a cycle can be accepted.

## Plan acceptance

A plan should not be accepted if it:

- exceeds the requested scope;
- modifies forbidden files;
- changes foundational specs in a non-spec-change cycle;
- lacks tests or validation strategy when applicable;
- introduces new dependencies without justification;
- proposes broad refactors for a small task;
- ignores architecture constraints;
- relies only on model confidence.

## Execution acceptance

A completed cycle should not be accepted unless:

- changed files are known;
- git diff is collected;
- required commands are run;
- required commands pass or failures are explicitly accepted by the human;
- report is generated;
- human decision is recorded.

## Human decision values

Suggested decision values:

```text
accepted
accepted_with_notes
needs_fix
rejected
reverted
deferred
```

## Mechanical evidence

Reports should include:

- commands executed;
- exit codes;
- summarized outputs;
- changed files;
- risk notes;
- whether the worktree is clean or dirty after the cycle.

## No self-approval

Agents cannot approve their own work.

A human decision must be recorded before a cycle is considered complete.
