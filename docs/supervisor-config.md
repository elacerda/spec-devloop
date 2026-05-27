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

A simple future config can be expressed in `.ai-loop/config/models.yaml`:

```yaml
schema_version: 1

policy:
  model_calls_allowed: false
  require_human_approval_for_model_calls: true
  secrets_must_use_env: true
  provider_specific_logic_allowed_in_core: false

providers:
  local_vllm:
    type: openai_compatible
    enabled: true
    base_url: http://localhost:8000/v1
    api_key:
      mode: none
      env: null
    timeout_seconds: 60

models:
  qwen3_coder_next_local:
    provider: local_vllm
    model: qwen3-coder-next
    enabled: true
    aliases: [qwen3-coder-next, local-coder]
    limits:
      context_window_tokens: 65536
      default_max_output_tokens: 2048

roles:
  supervisor:
    model: qwen3_coder_next_local
  reviewer:
    same_as: supervisor

preferences:
  default_role: supervisor
  default_profile: micro
```

This is illustrative, not an implemented schema.

This document does not assume model calls are enabled in MVP-0 or MVP-1.

## Roles

Future configuration may distinguish:

```yaml
roles:
  supervisor:
    model: qwen3_coder_next_local
  worker_prompt:
    same_as: supervisor
```

The same model may be used for both roles.

```yaml
roles:
  worker_prompt:
    same_as: supervisor
```

## Task granularity profile

The supervisor should be configurable by profile:

```yaml
preferences:
  default_profile: micro
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

Use environment-variable references:

```yaml
api_key:
  mode: required
  env: DEVLOOP_SUPERVISOR_API_KEY
```

Allowed values for `api_key.mode`:

- `none`;
- `optional`;
- `required`.

## Policy

Policy should define what the supervisor and worker may do.

Example:

```yaml
policy:
  model_calls_allowed: false
  require_human_approval_for_model_calls: true
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

`devloop model ping` is explicitly out of the first implementation phase.

`providers.yaml` is already documented for MVP-0 doctor validation. The future
`models.yaml` contract is the richer model-role-preference configuration layer.
