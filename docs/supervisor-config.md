# Supervisor Configuration

This document describes the future configuration surface for the supervisor/orchestrator.

The supervisor is the AI role responsible for planning, selecting the next task, generating worker instructions, reviewing evidence, and deciding whether the loop should correct or advance.

## Status

This configuration is future-facing.

MVP-0 does not require it and does not call models.

### Current implementation status

The `.ai-loop/config/models.yaml` file is now integrated into MVP-0 as an **optional** declarative contract for model configuration. It is validated by `devloop doctor` and `devloop status` but is not required for project readiness.

- **Optional file**: Missing `models.yaml` is not a readiness failure.
- **Validation**: Invalid config is reported as an error.
- **No network calls**: All validation is local and read-only.

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

## Model configuration commands

The `devloop model` command group provides local, read-only validation and listing of the declarative model configuration contract.

### `devloop model check`

Validates `.ai-loop/config/models.yaml` as a declarative contract.

- **Local and read-only**: no network calls, no AI/model calls.
- **Optional file**: missing config is allowed (returns warning, exit code 0).
- **Validation errors**: returns exit code 2.
- **Unexpected failures**: returns exit code 3.

Outputs:
- config path
- file presence status
- severity: message for each finding (info, warning, error)

### `devloop model list`

Lists providers, models, roles, and aliases from `.ai-loop/config/models.yaml`.

- **Local and read-only**: no network calls, no AI/model calls.
- **No config present**: prints "no model config present", exit code 0.
- **Validation errors**: prints error message, suggests running `check`, exit code 2.
- **Success**: prints compact listing of providers, models, roles (with aliases shown).

### Notes

- Both commands are report-only and do not modify files.
- Both commands do not contact endpoints or make model calls.

### `devloop model ping`

The `devloop model ping <target> --allow-call` command prepares a sanitized model ping request without performing network transport.

**Current implementation status (MVP-0):**

- **Preparation-only**: The command calls the backend preparation layer only. No HTTP/network calls are performed.
- **No model invocation**: The command does not call a model yet.
- **No config modification**: The command does not create or modify `.ai-loop/config/models.yaml`.
- **Sanitized output**: The command prints sanitized metadata such as:
  - `resolved_model`: the resolved model key (after role resolution)
  - `backend_model`: the backend model identifier
  - `provider`: the provider key
  - `endpoint`: the provider base URL
  - `timeout_seconds`: the timeout budget
  - `auth`: the auth mode (`none`, `optional`, `required`)
  - `auth_env`: the environment variable name (if configured)
  - `auth_present`: whether an auth token is present in environment
  - `attempted_transport: false` (no network call was performed)
  - `note: no network call was performed`

**Authorization requirements:**

The command requires **both** conditions to proceed:

1. `policy.model_calls_allowed: true` in `.ai-loop/config/models.yaml`;
2. explicit CLI flag `--allow-call`.

**Target resolution:**

- `<target>` may be a role name or model key.
- Role names resolve before model names.
- Unknown targets produce an error.

**Security:**

- API keys, Authorization headers, and secret values are never printed.
- The command is local and read-only for the preparation layer.

**Future work:**

Real OpenAI-compatible HTTP transport remains future work. The current implementation is preparation-only.
