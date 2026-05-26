# spec-devloop

This package contains the initial redesigned documentation and specification set for **spec-devloop**.

`spec-devloop` is intended to be a local, file-based, spec-first, human-in-the-loop orchestrator for AI-assisted development cycles. It is not intended to be a coding agent in the initial MVP. Instead, it governs a development loop around external or future internal executors.

The project name is:

```text
spec-devloop
```

The recommended CLI command name remains:

```bash
devloop
```

## Design position

`spec-devloop` should be:

- model-agnostic;
- agent-agnostic;
- backend-agnostic;
- file-based;
- spec-first;
- local-first;
- auditable;
- conservative by default;
- usable even without any model provider configured.

It should treat tools such as Cline, Roo, Continue, Codex CLI, Aider, vLLM, Ollama, OpenAI-compatible endpoints, OpenAI API, Anthropic API, or future internal agents as optional participants, adapters, or providers.

## Documentation

| Document | Description |
|----------|-------------|
| [Vision](docs/vision.md) | Visão e princípios do projeto |
| [Repository Layout](docs/repository-layout.md) | Layout mínimo e evolutivo de `.ai-loop/` |
| [Manual Cycle](docs/manual-cycle.md) | Contrato de ciclo manual e relação com futuro loop supervisionado |
| [Supervisor Config](docs/supervisor-config.md) | Configuração da IA supervisora (futuro) |
| [Roadmap](docs/roadmap.md) | Roadmap de evolução do MVP-0 para versões futuras |

## MVP-0 commands

The MVP-0 CLI exposes report-only diagnostics:

- `devloop doctor`: validates the local spec set, YAML files, minimal schemas, managed directories, and git state.
- `devloop status`: reuses `doctor` and prints a short readiness summary with project root, readiness, finding counts, and git status.
- `devloop init --check`: checks the minimum expected structure for manual setup and reports missing paths.
- `devloop cycle check <cycle-id>`: validates the minimum manual cycle layout under `.ai-loop/cycles/<cycle-id>/`.
- `devloop cycle list`: lists immediate subdirectories of `.ai-loop/cycles/`, sorted alphabetically. Does not validate cycles. Returns empty output and exit 0 if the directory does not exist or is empty.
- `devloop cycle prompt <cycle-id>`: generates a Markdown prompt for manual cycle execution. Reuses `cycle check` validation and includes project context, architecture, protocol, task, and optional commands/allowed_paths sections.

`devloop init` without `--check` is intentionally conservative in MVP-0: automatic write mode is not supported yet and no files or directories are created.

`devloop cycle check <cycle-id>` is report-only and does not create the cycle. The human must create the cycle directory and files manually before running the check. It validates only the minimum structural contract and returns `0` when there are no validation errors, `2` when validation errors are present, and `3` on unexpected internal failure.

`devloop cycle list` is report-only and does not validate cycles. It lists only immediate subdirectories of `.ai-loop/cycles/`, without recursion. If `.ai-loop/cycles/` does not exist or is empty, the output is empty and the exit code is 0. Unexpected internal failures return exit code 3.

Minimum manual cycle layout (MVP-0):

```text
.ai-loop/cycles/<cycle-id>/
  meta.yaml
  task.md
  report.md
```

Arquivos futuros/opcionais:

```text
.ai-loop/cycles/<cycle-id>/
  plan.md    # plano antes da execução (futuro)
  evidence.md # evidências como testes, logs, revisão (futuro)
```

### Semântica dos arquivos

| Arquivo | Descrição |
|---------|-----------|
| `task.md` | Tarefa proposta - o que o usuário pretende alcançar |
| `plan.md` | Plano antes da execução - opcional/futuro |
| `report.md` | Relato do que foi feito, resultado e pendências |
| `evidence.md` | Evidências como testes, comandos, logs ou revisão humana |

### Estados conceituais futuros de ciclo

Estes estados são conceituais e podem ser usados em `meta.yaml` ou comandos futuros:

- `planned` - ciclo planejado, aguardando execução
- `ready_for_worker` - pronto para ser executado por um worker
- `in_progress` - execução em andamento
- `waiting_review` - aguardando revisão
- `completed` - ciclo concluído
- `blocked` - ciclo bloqueado

> **Nota:** Estes estados são futuros/conceituais. No MVP-0, o campo `status` em `meta.yaml` é livre e não validado pelo CLI.

Example `meta.yaml`:

```yaml
schema_version: "0"
cycle_id: c-001
created_at: "2026-05-26"
status: draft
```

Both diagnostics are conservative and report-only in MVP-0:

- they do not create files or directories;
- they do not call models;
- they do not call agents;
- they do not execute configured commands.

## Local MVP-0 usage

Minimum local run for MVP-0:

```bash
python3 -m pip install -e .
devloop doctor
devloop status
devloop init --check
```

If `uv` is available, dependency sync can be done with:

```bash
uv sync
