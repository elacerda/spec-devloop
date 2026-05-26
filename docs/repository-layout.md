# Repository Layout

## Purpose

Este documento define o papel dos diretórios principais do repositório `spec-devloop` e esclarece a separação entre documentação humana e artefatos operacionais validáveis.

## Top-level layout

```
.
├── .ai-loop/
├── docs/
├── src/devloop/
├── tests/
├── README.md
└── pyproject.toml
```

## .ai-loop/

Contém artefatos operacionais validáveis pelo CLI. É o diretório onde o `devloop` lê e escreve estado operacional.

Estrutura:
- `project.md` - especificação do projeto
- `architecture.md` - arquitetura do projeto
- `protocol.md` - protocolo de desenvolvimento
- `config/` - configurações operacionais
- `cycles/` - instâncias concretas de ciclos
- `state/` - estado operacional do CLI

**Importante:** `.ai-loop/` não deve ser usado como depósito genérico de documentação humana. Documentação conceitual e decisões de design devem viver em `docs/`.

**Nota:** `.ai-loop/specs/` não existe no MVP-0. Especificações vivem em `docs/` até que a funcionalidade seja adicionada em versões futuras.

## .ai-loop/cycles/

Contém instâncias concretas de ciclos manuais. Cada ciclo vive em um subdiretório identificado por um `cycle-id` único:

```
.ai-loop/cycles/<cycle-id>/
├── meta.yaml
├── task.md
└── report.md
```

No MVP-0:
- ciclos são criados manualmente pelo usuário;
- o contrato mínimo é documentado em `docs/manual-cycle.md`;
- o comando `devloop cycle check <cycle-id>` valida a estrutura do ciclo.

## docs/

Contém documentação humana, contratos conceituais e decisões de design. Este diretório é para leitura e referência por humanos.

Arquivos típicos:
- `README.md` - documentação geral do projeto
- `manual-cycle.md` - contrato de ciclo manual
- `mvp.md` - definição do MVP
- `vision.md` - visão do projeto
- `glossary.md` - glossário de termos
- `decisions/` - registros de decisões de arquitetura (ADR)
- `research/` - pesquisas e análise de trabalhos relacionados

**Importante:** `docs/` não é estado operacional. Não deve ser confundido com artefatos que o CLI valida diretamente. Documentação conceitual e decisões de design devem viver aqui, não em `.ai-loop/`.

## src/devloop/

Contém a implementação Python do CLI e dos backends puros.

Estrutura:
- `cli.py` - entrada principal do CLI
- `doctor.py` - implementação do comando `devloop doctor`
- `status.py` - implementação do comando `devloop status`
- `init_check.py` - implementação do comando `devloop init --check`
- `cycle_check.py` - implementação do comando `devloop cycle check`

**Importante:** backends devem ser testáveis sem depender do CLI. Comandos devem permanecer report-only no MVP-0 quando aplicável.

## tests/

Contém testes automatizados que cobrem:
- contratos públicos do CLI
- validações de especificações
- comportamento de backends
- comandos implementados

Testes devem acompanhar novos comandos e validações. O objetivo é garantir que o CLI funcione corretamente sem depender de ferramentas externas.

## Non-goals for MVP-0

O MVP-0 é conservador e report-only. As seguintes funcionalidades são intencionalmente excluídas:

- não introduzir `.ai-loop/specs/`
- não mover documentação humana para `.ai-loop/`
- não criar automação
- não executar `commands.yaml`
- não acoplar o projeto a agentes, modelos ou backends específicos

Estas funcionalidades podem ser adicionadas em versões futuras, após validação do MVP-0.