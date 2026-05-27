"""Tests for MVP-0.1 `devloop cycle prompt <cycle-id>` command."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app

runner = CliRunner()

# Estrutura mínima (apenas project.md, sem architecture.md nem protocol.md)
MINIMAL_PROJECT_FILES = {
    ".ai-loop/project.md": "# Project\n\nThis is a test project.",
}

# Estrutura completa (com architecture.md e protocol.md)
COMPLETE_PROJECT_FILES = {
    ".ai-loop/project.md": "# Project\n\nThis is a test project.",
    ".ai-loop/architecture.md": "# Architecture\n\nSimple architecture.",
    ".ai-loop/protocol.md": "# Protocol\n\nBasic protocol.",
}

MINIMAL_CYCLE_FILES = {
    "meta.yaml": "schema_version: '0'\ncycle_id: c-001\ncreated_at: '2026-05-26'\nstatus: planned\n",
    "task.md": "# Task\n\nImplement a simple feature.",
    "report.md": "# Report\n\nTask completed successfully.",
}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_min_project(tmp_path: Path) -> None:
    for rel, content in MINIMAL_PROJECT_FILES.items():
        _write(tmp_path / rel, content)


def _make_min_cycle(tmp_path: Path, cycle_id: str = "c-001") -> None:
    cycle_dir = tmp_path / ".ai-loop" / "cycles" / cycle_id
    for rel, content in MINIMAL_CYCLE_FILES.items():
        _write(cycle_dir / rel, content)


def _make_complete_project(tmp_path: Path) -> None:
    """Cria estrutura completa com project.md, architecture.md e protocol.md."""
    for rel, content in COMPLETE_PROJECT_FILES.items():
        _write(tmp_path / rel, content)


def _invoke_in_cwd(cwd: Path, args: list[str]) -> any:
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_cycle_prompt_valid_cycle_returns_zero(tmp_path: Path) -> None:
    """Ciclo válido gera prompt e exit 0."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 0
    assert "# Cycle Prompt: c-001" in result.stdout
    assert "# Contexto do Projeto" in result.stdout
    assert "# Arquitetura/Protocolo" in result.stdout
    assert "# Objetivo da Microtarefa" in result.stdout
    assert "# Instruções para o Agente" in result.stdout
    assert "# Instrução Final" in result.stdout


def test_cycle_prompt_includes_project_content(tmp_path: Path) -> None:
    """Prompt inclui project.md."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert "This is a test project." in result.stdout


def test_cycle_prompt_includes_architecture_content(tmp_path: Path) -> None:
    """Prompt inclui architecture.md."""
    _make_complete_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert "Simple architecture." in result.stdout


def test_cycle_prompt_includes_protocol_content(tmp_path: Path) -> None:
    """Prompt inclui protocol.md."""
    _make_complete_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert "Basic protocol." in result.stdout


def test_cycle_prompt_includes_task_content(tmp_path: Path) -> None:
    """Prompt inclui task.md."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert "Implement a simple feature." in result.stdout


def test_cycle_prompt_includes_commands_yaml_when_exists(tmp_path: Path) -> None:
    """Prompt inclui commands.yaml quando existe."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    commands_yaml = """\
schema_version: 1
schema:
  required_top_level: [project, specs, git, managed_directories, commands, execution]
project:
  name: test
specs:
  minimum_required:
    - .ai-loop/project.md
git:
  require_repository: true
managed_directories:
  - .ai-loop/cycles
  - .ai-loop/state
commands:
  test:
    - pytest
execution:
  shell: true
"""
    _write(tmp_path / ".ai-loop/config/commands.yaml", commands_yaml)

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert "# Comandos de Aceite" in result.stdout
    assert "schema_version: 1" in result.stdout


def test_cycle_prompt_includes_allowed_paths_yaml_when_exists(tmp_path: Path) -> None:
    """Prompt inclui allowed_paths.yaml quando existe."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    allowed_paths_yaml = """\
schema_version: 1
schema:
  required_top_level: [path_sets, cycle_permissions, precedence]
path_sets:
  source: [src/**]
  docs: [docs/**]
cycle_permissions:
  implementation:
    allow: [source]
    deny: []
precedence:
  rules:
    explicit_deny_over_allow: true
"""
    _write(tmp_path / ".ai-loop/config/allowed_paths.yaml", allowed_paths_yaml)

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert "# Arquivos Permitidos" in result.stdout
    assert "schema_version: 1" in result.stdout


def test_cycle_prompt_omits_commands_yaml_when_missing(tmp_path: Path) -> None:
    """Prompt omite seção de comandos quando commands.yaml não existe."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert "# Comandos de Aceite" not in result.stdout


def test_cycle_prompt_omits_allowed_paths_yaml_when_missing(tmp_path: Path) -> None:
    """Prompt omite seção de arquivos permitidos quando allowed_paths.yaml não existe."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert "# Arquivos Permitidos" not in result.stdout


def test_cycle_prompt_missing_cycle_directory_returns_error(tmp_path: Path) -> None:
    """Prompt falha quando ciclo não existe."""
    _make_min_project(tmp_path)

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-999"])

    assert result.exit_code == 2
    assert "error:" in result.stdout


def test_cycle_prompt_missing_required_cycle_files_returns_error(tmp_path: Path) -> None:
    """Prompt falha quando arquivos obrigatórios do ciclo faltam."""
    _make_min_project(tmp_path)

    cycle_dir = tmp_path / ".ai-loop" / "cycles" / "c-001"
    cycle_dir.mkdir(parents=True, exist_ok=True)
    (cycle_dir / "meta.yaml").write_text("schema_version: '0'\n", encoding="utf-8")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 2
    assert "error:" in result.stdout


def test_cycle_prompt_missing_global_required_file_returns_error(tmp_path: Path) -> None:
    """Prompt falha quando arquivo global obrigatório ausente."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    (tmp_path / ".ai-loop/project.md").unlink()

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 2
    assert "error:" in result.stdout


def test_cycle_prompt_unsafe_cycle_id_returns_error(tmp_path: Path) -> None:
    """Prompt falha quando cycle-id inseguro."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "../c-001"])

    assert result.exit_code == 2
    assert "error:" in result.stdout


def test_cycle_prompt_does_not_create_files(tmp_path: Path) -> None:
    """Comando não cria arquivos."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    prompt_path = tmp_path / ".ai-loop" / "cycles" / "c-001" / "prompt.md"
    assert not prompt_path.exists()

    _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert not prompt_path.exists()


def test_cycle_prompt_works_with_minimal_structure(tmp_path: Path) -> None:
    """Prompt funciona com estrutura mínima (apenas project.md, sem architecture.md nem protocol.md)."""
    # Criar apenas project.md (sem architecture.md e protocol.md)
    _write(tmp_path / ".ai-loop/project.md", "# Project\n\nThis is a minimal project.")
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 0
    assert "# Cycle Prompt: c-001" in result.stdout
    assert "# Contexto do Projeto" in result.stdout
    assert "# Arquitetura/Protocolo" in result.stdout
    assert "# Objetivo da Microtarefa" in result.stdout
    # O conteúdo do project.md deve estar presente
    assert "This is a minimal project." in result.stdout


def test_cycle_prompt_includes_architecture_when_exists(tmp_path: Path) -> None:
    """Prompt inclui architecture.md quando existe (estrutura completa)."""
    _make_complete_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 0
    assert "Simple architecture." in result.stdout


def test_cycle_prompt_includes_protocol_when_exists(tmp_path: Path) -> None:
    """Prompt inclui protocol.md quando existe (estrutura completa)."""
    _make_complete_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 0
    assert "Basic protocol." in result.stdout


def test_cycle_prompt_fails_without_project_md(tmp_path: Path) -> None:
    """Prompt falha quando project.md está ausente."""
    # Criar apenas architecture.md e protocol.md (sem project.md)
    _write(tmp_path / ".ai-loop/architecture.md", "# Architecture\n\nTest.")
    _write(tmp_path / ".ai-loop/protocol.md", "# Protocol\n\nTest.")
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 2
    assert "error:" in result.stdout
    assert "required global file missing: .ai-loop/project.md" in result.stdout


def test_cycle_prompt_shows_note_when_no_optional_files(tmp_path: Path) -> None:
    """Prompt mostra nota útil quando nenhum arquivo opcional existe."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 0
    # A seção deve existir, mas com a nota
    assert "## Arquitetura/Protocolo" in result.stdout
    assert "No architecture/protocol/config files found" in result.stdout
    # Não deve haver conteúdo vazio (duas quebras de linha seguidas após o título)
    lines = result.stdout.split("\n")
    for i, line in enumerate(lines):
        if line == "## Arquitetura/Protocolo":
            # A próxima linha deve ser a nota, não uma linha vazia
            assert i + 1 < len(lines)
            assert lines[i + 1].strip() != "" or lines[i + 2].strip() != ""


def test_cycle_prompt_renders_note_instead_of_empty_optional_content(tmp_path: Path) -> None:
    """Prompt renderiza nota útil no lugar de seção vazia quando nenhum arquivo opcional existe."""
    _make_min_project(tmp_path)
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 0
    # A seção ## Arquitetura/Protocolo deve existir, mas com a nota útil no lugar de conteúdo vazio
    assert "## Arquitetura/Protocolo" in result.stdout
    # A nota deve estar presente
    assert "No architecture/protocol/config files found" in result.stdout


def test_cycle_prompt_includes_architecture_when_exists_only(tmp_path: Path) -> None:
    """Prompt inclui architecture.md quando apenas este existe."""
    _write(tmp_path / ".ai-loop/project.md", "# Project\n\nTest project.")
    _write(tmp_path / ".ai-loop/architecture.md", "# Architecture\n\nOnly architecture.")
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 0
    assert "## Arquitetura/Protocolo" in result.stdout
    assert "Only architecture." in result.stdout
    assert "No architecture/protocol/config files found" not in result.stdout


def test_cycle_prompt_includes_protocol_when_exists_only(tmp_path: Path) -> None:
    """Prompt inclui protocol.md quando apenas este existe."""
    _write(tmp_path / ".ai-loop/project.md", "# Project\n\nTest project.")
    _write(tmp_path / ".ai-loop/protocol.md", "# Protocol\n\nOnly protocol.")
    _make_min_cycle(tmp_path, "c-001")

    result = _invoke_in_cwd(tmp_path, ["cycle", "prompt", "c-001"])

    assert result.exit_code == 0
    assert "## Arquitetura/Protocolo" in result.stdout
    assert "Only protocol." in result.stdout
    assert "No architecture/protocol/config files found" not in result.stdout
