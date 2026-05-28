"""Tests for MVP-0 `devloop doctor` command."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from devloop.cli import app

runner = CliRunner()


REQUIRED_FILES = {
    ".ai-loop/project.md": "project\n",
    ".ai-loop/architecture.md": "architecture\n",
    ".ai-loop/protocol.md": "protocol\n",
}

VALID_COMMANDS_YAML = """\
schema_version: 1
schema:
  required_top_level: [project, specs, git, managed_directories, commands, execution, doctor]
  project_required: [name, cli_command, python_version]
  specs_required: [minimum_required, optional]
  git_required: [require_repository, require_clean_worktree_before_cycle, collect_diff_after_execution, allow_auto_commit]
  execution_required: [shell, timeout_seconds, stop_on_required_command_failure]
project:
  name: spec-devloop
  cli_command: devloop
  python_version: \"3.12\"
specs:
  minimum_required:
    - .ai-loop/project.md
    - .ai-loop/architecture.md
    - .ai-loop/protocol.md
    - .ai-loop/config/commands.yaml
  optional:
    - .ai-loop/specification_lifecycle.md
git:
  require_repository: true
  require_clean_worktree_before_cycle: true
  collect_diff_after_execution: true
  allow_auto_commit: false
managed_directories:
  - .ai-loop/cycles
  - .ai-loop/state
commands:
  test: []
execution:
  shell: true
  timeout_seconds: 120
  stop_on_required_command_failure: true
doctor:
  mode: report_only
  create_missing_directories: false
  severities:
    info:
      blocks: false
    warning:
      blocks: false
    error:
      blocks: true
  exit_codes:
    ok: 0
    validation_error: 2
    internal_failure: 3
  checks:
    required_specs_present: error
    optional_specs_present: warning
    yaml_parse_valid: error
    yaml_schema_minimum_valid: error
    managed_directories_present: warning
    git_repository_detected: warning
    git_worktree_clean: warning
    default_provider_valid: error
    default_adapter_valid: error
"""

VALID_PROVIDERS_YAML = """\
schema_version: 1
schema:
  required_top_level: [default_provider, providers, policy]
  provider_entry_required: [type, enabled]
  policy_required: [provider_required_for_doctor, provider_required_for_manual_cycles, provider_specific_logic_allowed_in_core]
  validation_rules:
    - default_provider key must exist in providers
    - default_provider entry must have enabled: true
default_provider: none
providers:
  none:
    type: none
    enabled: true
policy:
  provider_required_for_doctor: false
  provider_required_for_manual_cycles: false
  provider_specific_logic_allowed_in_core: false
"""

VALID_ADAPTERS_YAML = """\
schema_version: 1
schema:
  required_top_level: [default_adapter, adapters, policy]
  adapter_entry_required: [type, enabled]
  policy_required: [adapter_required_for_doctor, default_mvp_adapter, agent_specific_logic_allowed_in_core]
  validation_rules:
    - default_adapter key must exist in adapters
    - default_adapter entry must have enabled: true
default_adapter: manual
adapters:
  manual:
    type: manual
    enabled: true
policy:
  adapter_required_for_doctor: false
  default_mvp_adapter: manual
  agent_specific_logic_allowed_in_core: false
"""

VALID_ALLOWED_PATHS_YAML = """\
schema_version: 1
schema:
  required_top_level: [path_sets, cycle_permissions, precedence]
  path_sets_required: [foundational_specs, operational_config, docs, source, generated_cycle_artifacts]
  validation_rules:
    - each cycle type must define allow and deny lists
    - referenced set names in allow or deny must exist in path_sets
precedence:
  rule_order:
    - explicit_deny_over_allow
    - more_specific_pattern_over_general_pattern
    - foundational_specs_immutable_in_normal_cycles
  rules:
    explicit_deny_over_allow: true
    more_specific_pattern_over_general_pattern: true
    foundational_specs_immutable_in_normal_cycles: true
path_sets:
  foundational_specs: []
  operational_config: []
  docs: []
  source: []
  generated_cycle_artifacts: []
cycle_permissions:
  implementation:
    allow: [source]
    deny: [foundational_specs]
  documentation:
    allow: [docs]
    deny: [foundational_specs]
"""


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _make_min_project(tmp_path: Path) -> None:
    for rel, content in REQUIRED_FILES.items():
        _write(tmp_path / rel, content)

    _write(tmp_path / ".ai-loop/config/commands.yaml", VALID_COMMANDS_YAML)
    _write(tmp_path / ".ai-loop/config/providers.yaml", VALID_PROVIDERS_YAML)
    _write(tmp_path / ".ai-loop/config/adapters.yaml", VALID_ADAPTERS_YAML)
    _write(tmp_path / ".ai-loop/config/allowed_paths.yaml", VALID_ALLOWED_PATHS_YAML)


def _invoke_in_cwd(cwd: Path) -> any:
    old_cwd = Path.cwd()
    os.chdir(cwd)
    try:
        return runner.invoke(app, ["doctor"], catch_exceptions=False)
    finally:
        os.chdir(old_cwd)


def test_doctor_valid_minimum_returns_zero(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 0


def test_doctor_missing_required_file_returns_two(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/project.md").unlink()

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 2


def test_doctor_invalid_yaml_returns_two(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    _write(tmp_path / ".ai-loop/config/providers.yaml", "providers: [broken\n")

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 2


def test_doctor_no_git_is_warning_only(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "git repository not detected" in result.stdout


def test_doctor_dirty_worktree_is_warning_only(tmp_path: Path) -> None:
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    _write(tmp_path / "dirty.txt", "x")

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "git worktree is dirty" in result.stdout


def test_missing_managed_directories_are_warnings(tmp_path: Path) -> None:
    _make_min_project(tmp_path)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "managed directory missing" in result.stdout


def test_unexpected_failure_returns_three(tmp_path: Path, monkeypatch) -> None:
    _make_min_project(tmp_path)

    from devloop import cli as cli_module

    def _boom(_: Path):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli_module, "run_doctor", _boom)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 3


VALID_MODELS_YAML = """\
schema_version: 1
providers:
  openai:
    type: openai_compatible
    enabled: true
    base_url: http://localhost:8000/v1
    api_key:
      mode: none
models:
  qwen3-coder-next-fp8:
    name: qwen3-coder-next-fp8
    provider: openai
roles:
  default:
    model: qwen3-coder-next-fp8
"""


def test_doctor_missing_model_config_is_warning_not_error(tmp_path: Path) -> None:
    """Missing models.yaml should not cause doctor to fail."""
    _make_min_project(tmp_path)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "model config: optional file missing: .ai-loop/config/models.yaml" in result.stdout


def test_doctor_valid_model_config_reports_ok(tmp_path: Path) -> None:
    """Valid models.yaml should be reported as valid."""
    _make_min_project(tmp_path)
    _write(tmp_path / ".ai-loop/config/models.yaml", VALID_MODELS_YAML)
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 0
    assert "model config: yaml parsed: .ai-loop/config/models.yaml" in result.stdout


def test_doctor_invalid_model_config_reports_error(tmp_path: Path) -> None:
    """Invalid models.yaml should report errors."""
    _make_min_project(tmp_path)
    _write(tmp_path / ".ai-loop/config/models.yaml", "schema_version: 2\n")
    (tmp_path / ".ai-loop/cycles").mkdir(parents=True)
    (tmp_path / ".ai-loop/state").mkdir(parents=True)

    result = _invoke_in_cwd(tmp_path)

    assert result.exit_code == 2
    assert "model config: schema_version must be 1" in result.stdout
