# MVP definition

## MVP goal

The MVP should prove that a local CLI can validate specifications, create auditable development cycles, and generate reports without depending on any specific model or coding agent.

## MVP must include

1. Python CLI with command name `devloop`.
2. Spec loader.
3. Spec validator.
4. `devloop doctor`.
5. Basic `devloop status`.
6. Cycle directory creation.
7. Manual executor workflow.
8. Markdown report generation.
9. YAML/JSON state files.
10. Git status/diff collection.
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

## Suggested first milestones

### Milestone 1: spec validation

- package skeleton;
- CLI entrypoint;
- spec paths;
- YAML parsing;
- doctor command;
- tests.

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

### Milestone 5: optional model/adapters

Only after the previous milestones are stable.
