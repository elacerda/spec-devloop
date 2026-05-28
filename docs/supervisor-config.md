# Supervisor Configuration

This document describes the model configuration contract for the supervisor/orchestrator.

The supervisor is the AI role responsible for planning, selecting the next task, generating worker instructions, reviewing evidence, and deciding whether the loop should correct or advance.

## Status

The `.ai-loop/config/models.yaml` file is now integrated into MVP-0 as an **optional** declarative contract for model configuration. It is validated by `devloop doctor` and `devloop status` but is not required for project readiness.

### Current implementation status

- **Optional file**: Missing `models.yaml` is not a readiness failure.
- **Validation**: Invalid config is reported as an error.
- **No network calls for check/list**: `devloop model check` and `devloop model list` are local and read-only.
- **Network call for ping**: `devloop model ping <target> --allow-call` performs a real OpenAI-compatible `/chat/completions` ping when explicitly authorized (requires dual authorization: `policy.model_calls_allowed: true` + `--allow-call` flag).

For safety constraints and sanitized output, see the [Model ping](#devloop-model-ping) section below.

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

This is illustrative of the expected schema structure. The model configuration contract is implemented and validated by `devloop model check`.

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

`devloop model ping` is implemented in the model configuration layer (MVP-2).

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

The `devloop model ping <target> --allow-call` command performs a real OpenAI-compatible `/chat/completions` ping when explicitly authorized.

**Authorization requirements:**

The command requires **both** conditions to proceed:

1. `policy.model_calls_allowed: true` in `.ai-loop/config/models.yaml`;
2. explicit CLI flag `--allow-call`.

**Target resolution:**

- `<target>` may be a role name or model key.
- Role names resolve before model names.
- Unknown targets produce an error.

**Sanitized success output:**

On successful ping, the command outputs:

- `result: ok`
- `attempted_transport: true`
- `transport: ok`
- `resolved_model`: the resolved model key (after role resolution)
- `backend_model`: the backend model identifier
- `provider`: the provider key
- `endpoint`: the final endpoint ending in `/chat/completions`
- `timeout_seconds`: the timeout budget
- `auth`: the auth mode (`none`, `optional`, `required`)
- `auth_env`: the environment variable name (if configured)
- `auth_present`: whether an auth token is present in environment

**Failure behavior:**

- **Config/usage/policy failures**: exit code 2, `attempted_transport: false`
- **Runtime/network/HTTP/response failures**: exit code 3, `attempted_transport: true`, `transport: error`

**Safety constraints:**

- API keys are never printed.
- Authorization headers are never printed.
- Model response content is never printed.
- No request payload, headers, or response is persisted to disk.
- No config file is created or modified.

**Security:**

- The preparation layer is local/read-only; only the explicitly authorized transport step performs the network call.
- All sensitive data (API keys, headers, responses) is sanitized before output.
- No secrets are logged or persisted.

**Future work:**

Additional provider types and transport features may be added in future milestones.

## Local vLLM Configuration (Safe Setup)

For local OpenAI-compatible endpoints (e.g., vLLM), use these safe configuration steps:

### 1. Create local `.env` file

Copy `.env.example` to `.env` and fill in your API key:

```bash
cp .env.example .env
# Edit .env and set your VLLM_API_KEY value
```

**Important:**
- `.env` is local-only and should never be committed.
- The CLI does NOT automatically load `.env` files.
- Load it manually before running commands:

```bash
set -a
source .env
set +a
```

### 2. Copy example model config

Copy `docs/examples/models.local-vllm.yaml` to `.ai-loop/config/models.yaml`:

```bash
mkdir -p .ai-loop/config
cp docs/examples/models.local-vllm.yaml .ai-loop/config/models.yaml
```

**Important:**
- `.ai-loop/config/models.yaml` may contain local-specific settings.
- Review before committing to version control.
- Never commit API keys or secrets.

### 3. Validate and test

Run these commands to verify your setup:

```bash
devloop model check    # Validate config (local, no network)
devloop model list     # List providers/models (local, no network)
devloop model ping supervisor --allow-call  # Test connectivity (requires --allow-call)
```

For a sanitized manual validation transcript, see `docs/validation/model-ping-vllm.md`.

### Command behavior summary

| Command | Network | Notes |
|---------|---------|-------|
| `devloop model check` | No | Local validation only |
| `devloop model list` | No | Local listing only |
| `devloop doctor` | No | Local health check |
| `devloop status` | No | Local status |
| `devloop model ping <target> --allow-call` | Yes | Only with policy + flag |
| `devloop cycle advise <cycle-id> [--role ROLE] --allow-call` | Yes, only with `policy.model_calls_allowed: true` and `--allow-call` | Advisory-only stdout transport; no file mutation |

**Safety:**
- API keys are never printed in output.
- Authorization headers are never printed.
- Model response content is never printed.
- No secrets are logged or persisted.

## `devloop cycle advise`

The `devloop cycle advise <cycle-id> [--role ROLE] --allow-call` command runs an authorized model-backed advisory request using an OpenAI-compatible `/chat/completions` transport.

**Authorization requirements:**

The command requires **both** conditions to proceed:

1. `policy.model_calls_allowed: true` in `.ai-loop/config/models.yaml`;
2. explicit CLI flag `--allow-call`.

If either condition is missing or false, execution stops before transport.

**Target resolution:**

- `<cycle-id>` must be a valid cycle directory under `.ai-loop/cycles/`.
- `<role>` defaults to `supervisor` if not specified.
- Role names resolve to models via `roles.<role>.model` or `roles.<role>.same_as`.

**Preparation behavior:**

- Validates `.ai-loop/config/models.yaml` configuration (local, read-only, no network calls).
- Validates the target cycle structure (local, read-only).
- Requires `policy.model_calls_allowed: true`.
- Requires explicit `--allow-call` CLI flag.
- Resolves role to model to provider.
- Collects only allowlisted project/cycle artifacts (`.ai-loop/project.md`, cycle metadata, task/plan/prompt/summary/report files).
- Outputs sanitized metadata to stdout only.

**Success output shape:**

On successful preparation, the command outputs:

```text
cycle_id: c-001
role: supervisor
result: prepared
resolved_model: qwen3_coder_next_local
backend_model: qwen3-coder-next
provider: local_vllm
inputs_count: 3
inputs:
  - .ai-loop/project.md
  - .ai-loop/cycles/c-001/meta.yaml
  - .ai-loop/cycles/c-001/task.md
attempted_transport: false
transport: skipped
safety: no files modified
```

**Failure behavior:**

- **Config/usage/policy failures**: exit code 2, `attempted_transport: false`
- **Cycle validation failures**: exit code 2, `attempted_transport: false`
- **Unexpected internal failures**: exit code 3, `attempted_transport: false`

**Safety constraints:**

- No secrets printed (API keys, Authorization headers, raw request headers).
- No hidden chain-of-thought.
- No prompt/payload/report/response persistence.
- No file modification.
- No network call.
- Advisory text is generated by the configured model and printed to stdout only.
- No autonomous execution.

**Future work:**

- Real model-backed advisory transport is not implemented yet.
- Autonomous execution remains out of scope.
- Persistence such as `--write-report` remains future work and requires a separate contract/ADR.


### Cycle advisory transport

`devloop cycle advise <cycle-id> [--role ROLE] --allow-call` runs an authorized
model-backed advisory request using an OpenAI-compatible `/chat/completions`
transport.

It validates:

- `.ai-loop/config/models.yaml`;
- the target cycle;
- `policy.model_calls_allowed: true`;
- explicit `--allow-call`.

It then resolves the role/model/provider, collects only allowlisted project and
cycle artifacts, builds a sanitized advisory context, calls the configured
OpenAI-compatible chat completions endpoint, extracts advisory text from
`choices[0].message.content`, and prints the result to stdout.

The command remains advisory-only. It does not mutate files, execute shell
commands, invoke agents, perform autonomous execution, stream responses, use
tool calling, run fallback orchestration, persist prompts/payloads/reports/
responses, print raw payloads, print raw response JSON, print Authorization
headers, print API keys, or expose hidden chain-of-thought.


Example success output:

```text
cycle_id: c-001
role: supervisor
result: ok
resolved_model: qwen3_coder_next_local
backend_model: qwen3-coder-next
provider: local_vllm
inputs_count: 3
attempted_transport: true
transport: ok
safety: no files modified
advisory:
- Review the plan before implementation.
- Keep the next task small.
```


Failure behavior:

- config, usage, policy, or cycle validation failures exit with code `2` and
  `attempted_transport: false`;
- runtime, network, or model-response failures exit with code `3`,
  `attempted_transport: true`, and `transport: error`;
- reported errors are sanitized and must not expose secrets.
