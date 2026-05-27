# Decision 0003: Declarative AI model configuration contract

## Status

Accepted.

## Context

The project needs a single declarative contract for future AI model selection
without introducing model calls in the current stage.

Existing documentation already references `providers.yaml` in MVP-0 doctor
validation as a minimal inventory-level artifact. That does not yet define a
complete model-role preference contract for supervisor-oriented workflows.

## Decision

Adopt `.ai-loop/config/models.yaml` as the richer future declarative contract
for model configuration.

This contract is configuration-only in the first implementation phase. It does
not imply active model invocation.

`models.yaml` defines:

- provider entries and endpoints;
- model entries mapped to providers;
- role-to-model mapping;
- selection preferences and fallbacks;
- policy flags for model-call governance;
- API key mode and environment-variable references.

### Minimal illustrative shape

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
    aliases:
      - qwen3-coder-next
      - local-coder
    capabilities:
      chat: true
      tools: false
      json_mode: false
      embeddings: false
    limits:
      context_window_tokens: 65536
      default_max_output_tokens: 2048
    defaults:
      temperature: 0.2

roles:
  supervisor:
    model: qwen3_coder_next_local
    purpose: plan next tasks and review evidence
  reviewer:
    same_as: supervisor
    purpose: review worker reports and decide advance/correct/block
  worker_prompt:
    same_as: supervisor
    purpose: generate instructions for external worker agents

preferences:
  default_role: supervisor
  default_profile: micro
  fallback_order:
    supervisor:
      - qwen3_coder_next_local
```

### API key policy

`api_key.mode` is explicitly one of:

- `none`;
- `optional`;
- `required`.

Secrets remain external to YAML values. When a key is used, it must be
referenced via environment variable name.

### Scope boundary for first implementation

The current decision records the contract only. A later first implementation may
be limited to validation and listing, without model calls.

It explicitly excludes:

- direct model calls;
- network connectivity checks;
- `devloop model ping`.

## Consequences

Positive:

- keeps the project local-first and human-governed in the current stage;
- provides a single richer contract for future model-role configuration;
- preserves backend and agent agnosticism via provider abstraction;
- avoids hardcoding secrets by standardizing environment-variable references.

Tradeoffs:

- introduces an additional future-facing config artifact;
- requires later schema validation work to enforce cross-references;
- keeps operational connectivity checks deferred to a later phase.

