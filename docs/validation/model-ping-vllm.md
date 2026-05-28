# Manual validation: model ping with local vLLM

This is an optional manual validation procedure to verify that `devloop model ping <target> --allow-call` can perform a real OpenAI-compatible `/chat/completions` ping against a local vLLM endpoint.

**Important:**
- This is **not** an automated test.
- It should not require committing local config or secrets.
- It is intended for developers setting up local validation environments.

## Prerequisites

Before proceeding, ensure the following:

1. **Local or reachable OpenAI-compatible endpoint is running**
   - Example endpoint: `http://127.0.0.1:8000/v1`
   - The backend model ID must be exposed by `/v1/models` (e.g., `qwen-coder-next`)

2. **Local configuration exists**
   - `.ai-loop/config/models.yaml` exists locally and references the environment variable `VLLM_API_KEY`
   - `VLLM_API_KEY` is exported in your shell
   - `policy.model_calls_allowed: true` in your config
   - You pass the explicit `--allow-call` flag

3. **Safe setup references**
   - See `.env.example` for the `.env` file template
   - See `docs/examples/models.local-vllm.yaml` for a safe local vLLM configuration example
   - See `docs/supervisor-config.md` for detailed setup instructions

## Setup steps

### 1. Verify environment variable is set

Run this command to check that `VLLM_API_KEY` is set without printing its value:

```bash
test -n "$VLLM_API_KEY" && echo "VLLM_API_KEY is set"
```

If the variable is not set, export it:

```bash
export VLLM_API_KEY=your-api-key-here
```

Or load from `.env`:

```bash
set -a
source .env
set +a
```

### 2. Verify server model listing

Test that the vLLM endpoint is responding and exposing models:

```bash
curl -i -H "Authorization: Bearer $VLLM_API_KEY" http://127.0.0.1:8000/v1/models
```

**Expected non-secret output:**
- HTTP 200 OK
- `model id: qwen-coder-next`
- `max_model_len: 65536`

### 3. Verify Python subprocess environment

To confirm the environment variable is available to Python subprocesses (which the CLI uses):

```bash
python3 - <<'PY'
import os
key = os.environ.get("VLLM_API_KEY", "")
if key:
    print(f"VLLM_API_KEY is set (length: {len(key)})")
else:
    print("VLLM_API_KEY is NOT set in subprocess")
PY
```

### 4. Run validation commands

```bash
devloop model check      # Validate config (local, no network)
devloop model list       # List providers/models (local, no network)
devloop model ping supervisor --allow-call  # Test connectivity (requires --allow-call)
```

## Expected sanitized output

### `curl /v1/models` (sanitized)

```
HTTP/1.1 200 OK
content-type: application/json
...

{
  "object": "list",
  "data": [
    {
      "id": "qwen-coder-next",
      "object": "model",
      "created": 1712345678,
      "owned_by": "vllm"
    }
  ]
}
```

### `devloop model ping supervisor --allow-call` (sanitized)

```
target: supervisor
result: ok
resolved_model: qwen3_coder_next_local
backend_model: qwen-coder-next
provider: local_vllm
endpoint: http://127.0.0.1:8000/v1/chat/completions
timeout_seconds: 15
auth: required
auth_env: VLLM_API_KEY
auth_present: true
attempted_transport: true
transport: ok
```

## Troubleshooting

### Environment variable not available to subprocess

**Symptom:** `curl` succeeds but `devloop model check` says the environment variable is not set.

**Solution:** The variable may not be exported to subprocesses. Use one of:

```bash
export VLLM_API_KEY
```

Or load from `.env` with `set -a`:

```bash
set -a
source .env
set +a
```

### 401 Unauthorized on ping

**Symptom:** Ping returns HTTP 401.

**Solution:** Verify:
- The API token is correct
- The vLLM server's authentication settings match your configuration

### Model ID mismatch

**Symptom:** The model ID from `/v1/models` differs from what's in `models.yaml`.

**Solution:** Update `models.<name>.name` in `.ai-loop/config/models.yaml` to match the backend model ID.

### Config file appears in git status

**Symptom:** `.ai-loop/config/models.yaml` shows in `git status`.

**Solution:** Review the file for local-specific settings before committing, or keep it local via `.git/info/exclude`:

```bash
echo ".ai-loop/config/models.yaml" >> .git/info/exclude
```

## Safety section

**Do not:**
- Print or paste API keys in logs or chat
- Commit `.env` to version control
- Store secrets in `models.yaml`
- Allow the CLI to print Authorization headers or model response content

**What the CLI guarantees:**
- `model check`, `model list`, `doctor`, and `status` remain no-network operations
- Only `model ping` can touch the network in this flow, and only with:
  - `policy.model_calls_allowed: true` in config
  - Explicit `--allow-call` CLI flag

**What is sanitized:**
- API keys are never printed
- Authorization headers are never printed
- Model response content is never printed
- No request payload, headers, or responses are persisted to disk

## Related documentation

- `.env.example` - Template for local environment variables
- `docs/examples/models.local-vllm.yaml` - Safe local vLLM configuration example
- `docs/supervisor-config.md` - Supervisor configuration and setup details

For a sanitized manual validation transcript, see `docs/validation/model-ping-vllm.md`.