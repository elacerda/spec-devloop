# Safety and Governance

`spec-devloop` is intended to support increasing levels of automation.

Automation requires explicit safety principles.

## Core principle

Autonomy must be configurable and governed.

The system should be able to operate carefully in critical projects and aggressively in low-risk prototypes.

## Safety dimensions

### File scope

Workers should know which files and directories are allowed.

Future policies may define:

```yaml
allowed_paths:
  - src/
  - tests/

forbidden_paths:
  - .env
  - secrets/
```

### Command execution

Commands should be explicit.

Future policies may distinguish:

- allowed test commands;
- allowed lint commands;
- forbidden destructive commands;
- commands requiring approval.

### Human checkpoints

Human approval may be required for:

- broad refactors;
- deleting files;
- modifying configuration;
- changing public APIs;
- modifying secrets;
- pushing commits;
- dependency changes;
- running external network commands.

### Token and cost budgets

Supervisor and worker calls should support budget controls:

- max input tokens;
- max output tokens;
- max calls per cycle;
- max cost per run;
- profile-specific budgets.

### Rollback

Before risky actions, the system should have a rollback strategy:

- git branch;
- commit checkpoint;
- patch file;
- diff capture;
- undo instructions.

### Audit logs

Important decisions should be recorded:

- who/what proposed a task;
- what model was used;
- what prompt/context was used;
- what files changed;
- what commands ran;
- what evidence was produced;
- why a cycle was accepted or rejected.

## Profile-specific risk

Different granularity profiles imply different risks.

| Profile | Risk level | Required safeguards |
|---------|------------|--------------------|
| `micro` | Low | frequent review, narrow scope |
| `balanced` | Medium | tests, summary, review |
| `yolo` | High | branch, diff capture, explicit opt-in |
| `deep` / `torra-token` | Medium | budget control, review, alternatives |

## Secure by default

Defaults should be conservative:

- no model calls in MVP-0;
- no file writes unless explicitly enabled;
- no command execution unless explicitly enabled;
- no secrets in config files;
- no autonomous destructive actions.

## Human-governed does not mean manual forever

Human-governed means humans define the autonomy boundaries.

It does not mean every step must be copy/paste forever.
