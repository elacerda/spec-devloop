# Supervisor Configuration

This document describes the future configuration surface for the supervisor/orchestrator.

The supervisor is the AI role responsible for planning, selecting the next task, generating worker instructions, reviewing evidence, and deciding whether the loop should correct or advance.

## Status

This configuration is future-facing.

MVP-0 does not require it and does not call models.

## Design goals

The configuration should be:

- model-agnostic;
- backend-agnostic;
- agent-agnostic;
- local-first;
- secure by default;
- simple for common cases;
- extensible for advanced orchestration.

## Minimal conceptual config

A simple future config might look like:

```yaml
schema_version: "0.1"

orchestrator:
  provider: openai-compatible
  model: qwen-coder-next
  endpoint: http://localhost:8000/v1
  api_key_env: DEVLOOP_SUPERVISOR_API_KEY

  profile: micro
  max_output_tokens: 2048
  temperature: 0.2

policy:
  require_human_approval: true
  allow_model_calls: true
  allow_file_writes: false
  allow_command_execution: false
```

This is illustrative, not an implemented schema.

## Roles

Future configuration may distinguish:

```yaml
roles:
  supervisor:
    provider: openai-compatible
    model: qwen-coder-next

  worker:
    mode: external-agent
    tool_hint: cline
```

The same model may be used for both roles.

```yaml
roles:
  worker:
    same_as: supervisor
```

## Task granularity profile

The supervisor should be configurable by profile:

```yaml
orchestrator:
  profile: micro
```

Possible profiles:

- `micro`;
- `balanced`;
- `yolo`;
- `deep` or `torra-token`.

The profile affects:

- task size;
- token budget;
- context selection;
- checkpoint frequency;
- evidence requirements;
- risk tolerance.

## Credentials

Secrets must not be hardcoded.

Use environment variables:

```yaml
api_key_env: DEVLOOP_SUPERVISOR_API_KEY
```

## Policy

Policy should define what the supervisor and worker may do.

Example:

```yaml
policy:
  require_human_approval: true
  allow_model_calls: true
  allow_file_writes: false
  allow_command_execution: false
  allowed_paths:
    - src/
    - tests/
```

## Safety defaults

Default behavior should be conservative:

- no file writes unless explicitly allowed;
- no command execution unless explicitly allowed;
- human approval for sensitive transitions;
- logs for model calls and decisions;
- rollback strategy before broad changes.

## Future commands

Possible future commands:

- `devloop supervisor check`;
- `devloop next`;
- `devloop plan`;
- `devloop review`;
- `devloop run`.

These commands do not exist in MVP-0 unless implemented separately.
