# MVP definition

## MVP goal

The MVP should prove that a local CLI can validate specifications, create auditable development cycles, and generate reports without depending on any specific model or coding agent.

## MVP-0 (first deliverable): `devloop doctor`

MVP-0 is the first implementation stage and includes only `devloop doctor` plus the minimum loader and validator behavior needed by doctor.

MVP-0 must:

1. verify minimum required specification files;
2. parse and validate YAML configuration syntax;
3. validate minimum schemas for config YAML files;
4. report optional file presence;
5. validate managed directories presence (report-only);
6. detect git repository and worktree cleanliness (report-only);
7. output severities (`info`, `warning`, `error`) and consistent exit code;
8. avoid creating files or directories automatically.

MVP-0 must not:

- run tests, lint, format, or typecheck commands;
- create cycles;
- call model providers;
- call external agent adapters;
- modify repository files.

## MVP complete (after MVP-0)

The complete MVP should include:

1. Python CLI with command name `devloop`.
2. Spec loader.
3. Spec validator.
4. `devloop doctor`.
5. Basic `devloop status`.
6. Cycle directory creation.
7. Manual executor workflow.
8. Markdown report generation.
9. YAML and JSON state files.
10. Git status and diff collection.
11. Configured command execution.

## MVP should not include

- autonomous code editing;
- internal tool-calling agent;
- direct Cline automation;
- direct Roo automation;
- direct Continue automation;
- direct Codex CLI automation;
- model provider calls as a requirement;
- MCP integration;
- database;
- web UI;
- background daemon.

## First command

The first command to implement should be:

```bash
devloop doctor
```

It should:

- verify required files;
- parse YAML config;
- report optional files;
- validate managed directories;
- detect git repository;
- report whether the project is ready for manual cycles.

## Suggested milestones

### Milestone 1: MVP-0 spec validation

- initial CLI entrypoint;
- spec path resolution;
- YAML parsing;
- doctor command;
- tests for doctor behavior.

### Milestone 2: manual cycles

- create cycle;
- write task template;
- save plan;
- review plan file presence;
- collect report shell.

### Milestone 3: evidence collection

- git status;
- git diff;
- configured command execution;
- report generation.

### Milestone 4: policy enforcement

- allowed path checks;
- cycle type permissions;
- spec-change restrictions.

### Milestone 5: optional model or adapters

Only after the previous milestones are stable.
