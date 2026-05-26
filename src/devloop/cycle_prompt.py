"""Backend report-only prompt generation for `devloop cycle prompt` in MVP-0.1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from devloop.cycle_check import run_cycle_check


@dataclass(frozen=True)
class CyclePromptResult:
    """Result of cycle prompt generation.

    Parameters
    ----------
    cycle_id
        Cycle identifier provided by the caller.
    cycle_dir
        Absolute cycle directory path inspected.
    prompt
        Generated Markdown prompt string, or None if generation failed.
    errors
        Validation error messages, or None if generation succeeded.
    """

    cycle_id: str
    cycle_dir: Path
    prompt: str | None
    errors: list[str] | None


def run_cycle_prompt(project_root: Path, cycle_id: str) -> CyclePromptResult:
    """Generate a Markdown prompt for a manual cycle.

    Parameters
    ----------
    project_root
        Filesystem project root containing ``.ai-loop/cycles``.
    cycle_id
        Cycle identifier expected as a direct child directory name.

    Returns
    -------
    CyclePromptResult
        Result with prompt string or validation errors.

    Notes
    -----
    This function is report-only. It does not create or modify files.
    It reuses cycle check validation before generating the prompt.
    """

    errors: list[str] = []

    # Validate cycle-id is safe
    if not _is_safe_cycle_id(cycle_id):
        errors.append(f"unsafe cycle id: {cycle_id}")
        return CyclePromptResult(
            cycle_id=cycle_id,
            cycle_dir=project_root / ".ai-loop" / "cycles" / cycle_id,
            prompt=None,
            errors=errors,
        )

    # Run cycle check validation
    cycle_check_result = run_cycle_check(project_root, cycle_id)
    if cycle_check_result.errors:
        errors.extend(cycle_check_result.errors)
        return CyclePromptResult(
            cycle_id=cycle_id,
            cycle_dir=cycle_check_result.cycle_dir,
            prompt=None,
            errors=errors,
        )

    # Validate global required files
    global_required_files = [
        ".ai-loop/project.md",
        ".ai-loop/architecture.md",
        ".ai-loop/protocol.md",
    ]
    for rel_path in global_required_files:
        full_path = project_root / rel_path
        if not full_path.is_file():
            errors.append(f"required global file missing: {rel_path}")

    if errors:
        return CyclePromptResult(
            cycle_id=cycle_id,
            cycle_dir=cycle_check_result.cycle_dir,
            prompt=None,
            errors=errors,
        )

    # Read file contents
    project_content = (project_root / ".ai-loop/project.md").read_text(
        encoding="utf-8"
    ).strip()
    architecture_content = (project_root / ".ai-loop/architecture.md").read_text(
        encoding="utf-8"
    ).strip()
    protocol_content = (project_root / ".ai-loop/protocol.md").read_text(
        encoding="utf-8"
    ).strip()
    task_content = (cycle_check_result.cycle_dir / "task.md").read_text(
        encoding="utf-8"
    ).strip()

    # Build prompt sections
    sections: list[str] = []

    # Title
    sections.append(f"# Cycle Prompt: {cycle_id}")
    sections.append("")

    # Contexto do Projeto
    sections.append("## Contexto do Projeto")
    sections.append("")
    sections.append(project_content)
    sections.append("")

    # Arquitetura/Protocolo
    sections.append("## Arquitetura/Protocolo")
    sections.append("")
    sections.append(architecture_content)
    sections.append("")
    sections.append(protocol_content)
    sections.append("")

    # Objetivo da Microtarefa
    sections.append("## Objetivo da Microtarefa")
    sections.append("")
    sections.append(task_content)
    sections.append("")

    # Arquivos Permitidos (opcional)
    allowed_paths_path = project_root / ".ai-loop" / "config" / "allowed_paths.yaml"
    if allowed_paths_path.is_file():
        allowed_paths_content = allowed_paths_path.read_text(encoding="utf-8").strip()
        sections.append("## Arquivos Permitidos")
        sections.append("")
        sections.append("```yaml")
        sections.append(allowed_paths_content)
        sections.append("```")
        sections.append("")

    # Comandos de Aceite (opcional)
    commands_path = project_root / ".ai-loop" / "config" / "commands.yaml"
    if commands_path.is_file():
        commands_content = commands_path.read_text(encoding="utf-8").strip()
        sections.append("## Comandos de Aceite")
        sections.append("")
        sections.append("```yaml")
        sections.append(commands_content)
        sections.append("```")
        sections.append("")

    # Instruções para o Agente
    sections.append("## Instruções para o Agente")
    sections.append("")
    sections.append("- Mantenha o patch pequeno e focado")
    sections.append("- Não saia do escopo definido no objetivo da microtarefa")
    sections.append("- Não execute ações fora das instruções")
    sections.append("- Mostre o diff antes de aplicar mudanças")
    sections.append("- Execute testes após mudanças")
    sections.append("- Reporte status após cada etapa")
    sections.append("")

    # Instrução Final
    sections.append("## Instrução Final")
    sections.append("")
    sections.append(
        "Copie este prompt e cole no seu agente externo (Cline, Codex, Continue, "
        "Roo, Aider, etc.)."
    )
    sections.append("")

    prompt = "\n".join(sections)

    return CyclePromptResult(
        cycle_id=cycle_id,
        cycle_dir=cycle_check_result.cycle_dir,
        prompt=prompt,
        errors=None,
    )


def _is_safe_cycle_id(cycle_id: str) -> bool:
    """Return ``True`` when cycle_id is safe as a direct child directory name."""

    if cycle_id in {".", ".."}:
        return False
    if not cycle_id or not cycle_id.strip():
        return False
    if "/" in cycle_id or "\\" in cycle_id:
        return False
    return True

