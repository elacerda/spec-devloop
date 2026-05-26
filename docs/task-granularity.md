# Task Granularity Profiles

Different users and projects need different task sizes.

`spec-devloop` should allow the supervisor/orchestrator to use configurable task granularity profiles.

These profiles are not only prompt styles. They affect planning, context selection, file scope, evidence requirements, token budget, and checkpoint frequency.

## Profiles

### `micro`

Small, careful, low-risk tasks.

The supervisor should:

- propose one narrow change at a time;
- limit the number of files touched;
- define clear acceptance criteria;
- ask for tests whenever reasonable;
- prefer correction loops over broad rewrites;
- keep worker prompts short and specific.

Best for:

- critical code;
- unfamiliar codebases;
- local models with limited reliability;
- early project setup;
- test-driven implementation;
- the workflow currently used in this project.

Trade-offs:

- slower;
- more iterations;
- more human checkpoints;
- lower risk.

### `balanced`

Default mode for regular development.

The supervisor should:

- group related small changes;
- keep scope understandable;
- require evidence;
- avoid unnecessary over-planning;
- balance speed and safety.

Best for:

- normal feature development;
- documentation updates;
- small refactors;
- reliable workers.

Trade-offs:

- moderate risk;
- moderate speed;
- reasonable token use.

### `yolo`

High-autonomy, larger tasks, fewer checkpoints.

The supervisor may:

- delegate broader changes;
- allow more files;
- reduce intermediate review;
- optimize for speed;
- accept higher risk.

Best for:

- prototypes;
- experiments;
- disposable branches;
- low-risk projects;
- early exploration.

Trade-offs:

- higher risk;
- harder review;
- bigger diffs;
- more chance of scope creep.

Required safeguards:

- run in a branch;
- capture diff;
- require tests when possible;
- never use for sensitive code without explicit approval.

### `torra-token` / `deep`

High-analysis, high-context, token-heavy mode.

The supervisor should:

- read more context;
- compare alternatives;
- explain trade-offs;
- produce richer plans;
- perform deeper review;
- use more output tokens;
- be conservative in acceptance decisions.

Best for:

- architecture decisions;
- complex bugs;
- large refactors;
- security-sensitive changes;
- scientific/technical design;
- documentation restructuring.

Trade-offs:

- expensive;
- slower;
- may overthink simple tasks;
- needs budget control.

## Conceptual configuration

Future config may support:

```yaml
orchestrator:
  profile: micro  # micro | balanced | yolo | deep
  token_budget: standard  # low | standard | high | burn
  checkpoint_policy: frequent
```

Or:

```yaml
execution_profile: micro

profiles:
  micro:
    max_files_per_task: 3
    require_tests: true
    require_human_checkpoint: true

  balanced:
    max_files_per_task: 8
    require_tests: true
    require_human_checkpoint: true

  yolo:
    max_files_per_task: null
    require_tests: true
    require_human_checkpoint: false

  deep:
    max_files_per_task: 5
    require_deep_analysis: true
    require_alternatives: true
    require_review: true
```

The exact schema is future work.

## How profiles affect the loop

A profile may affect:

| Dimension | Micro | Balanced | Yolo | Deep |
|----------|-------|----------|------|------|
| Task size | Small | Medium | Large | Variable |
| Token use | Low/medium | Medium | Medium/high | High |
| Checkpoints | Many | Some | Few | Many/strategic |
| Risk | Low | Medium | High | Low/medium |
| Analysis depth | Focused | Moderate | Shallow/moderate | High |
| Speed | Slow | Medium | Fast | Slow |
| Review strictness | High | Medium | Lower | High |

## Principle

Task granularity is a user preference and project policy.

The system should not force everyone into microtasks, nor should it default to unsafe autonomy.

The user should decide how careful or aggressive the loop should be.
