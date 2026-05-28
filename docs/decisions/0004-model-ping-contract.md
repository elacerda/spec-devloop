# Decision 0004: `devloop model ping` contract

## Status

Accepted.

## Context

The project has maintained a local-first, read-only validation approach for model configuration. Commands like `devloop model check`, `devloop model list`, `devloop doctor`, and `devloop status` perform only local validation without network calls.

The first intentional transition from local read-only validation to an explicitly authorized model call requires a formal contract to ensure safety, predictability, and clear boundaries.

## Decision

Introduce `devloop model ping` as a minimal, explicitly authorized network call command for MVP.

### Command shape

```bash
devloop model ping <role-or-model> --allow-call
```

The target can be a role name or model name:

- resolve role first;
- then model;
- otherwise error.

### Authorization requirements

The command requires **both** conditions to proceed:

1. `policy.model_calls_allowed: true` in `.ai-loop/config/models.yaml`;
2. explicit CLI flag `--allow-call`.

Missing or false policy blocks the call. Missing `--allow-call` blocks the call.

### Supported provider type (MVP)

Only `openai_compatible` provider type is supported in the MVP.

### API key handling

Respect the configured `api_key.mode`:

- `none`: no Authorization header;
- `optional`: use env var only if configured and present;
- `required`: env var must be configured and present.

Secrets must never be printed.

### Request payload

Suggested minimal payload:

- one user message with content `ping`;
- low output limit, e.g. `max_tokens: 1`;
- `temperature: 0`.

### Timeout

Conservative finite timeout, e.g. 15 seconds.

### Exit codes

- `0` for successful ping;
- `2` for config/usage/policy errors;
- `3` for network/runtime/unexpected failures.

### Test requirements

Tests must not require real network calls; use fake/injected transport.

### Scope exclusions

The following are explicitly out of scope for this decision:

- autonomous execution;
- model selection fallback;
- streaming responses;
- tool calling;
- benchmarking;
- task execution.

### Config file constraints

`devloop model ping` must not create or modify config files.

`devloop model ping` must not persist model responses, request payloads, API keys, or Authorization headers.

## Consequences

### Positive

- maintains safety by requiring dual authorization (policy + CLI flag);
- preserves local-first principle for other commands;
- provides minimal network call for connectivity validation;
- keeps secrets external via environment variables;
- enables future model selection validation with real endpoints.

### Tradeoffs

- introduces first network call in the CLI;
- requires careful timeout and error handling;
- adds complexity to test infrastructure (fake transport needed);
- creates a boundary between read-only and active commands.

## Notes

- `devloop model check`, `devloop model list`, `devloop doctor`, and `devloop status` remain local/read-only/no-network.
- This is the first intentional transition from local read-only validation to an explicitly authorized model call.
