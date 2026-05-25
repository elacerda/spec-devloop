# Glossary

## spec-devloop

The project name.

## devloop

The recommended CLI command.

## Foundational specification

A high-authority document that defines the project identity, architecture, protocol, or policies.

## Operational configuration

Machine-readable configuration used by the CLI, usually YAML.

## Cycle

A bounded unit of AI-assisted development work.

## Cycle artifact

A file generated or collected during a cycle, such as task, plan, diff, test output, report, or decision.

## Agent

A tool or participant that can produce plans or code changes. Examples include Cline, Codex CLI, Roo, Continue, Aider, humans, or future internal agents.

## Adapter

A module that translates the generic `spec-devloop` protocol into behavior suitable for a specific agent.

## Model provider

A source of model completions, such as no provider, vLLM, Ollama, OpenAI-compatible API, OpenAI API, Anthropic API, or another backend.

## Manual executor

The MVP executor. The CLI generates artifacts, the user interacts with an external tool manually, and then saves outputs back into the cycle.

## Spec-change cycle

A special cycle type allowed to change foundational specifications or policies.

## Evidence

Mechanical information used to verify a cycle, such as git diff, command outputs, test logs, and recorded decisions.
