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

### Bootstrap mínimo do projeto

Para iniciar um projeto, apenas um arquivo é obrigatório:

```
.ai-loop/project.md
```

Este arquivo contém a identidade do projeto e serve como âncora para todos os ciclos subsequentes.

### Bootstrap mínimo de um ciclo com IA

Para iniciar um ciclo com supervisão de IA, três arquivos são obrigatórios:

```
.ai-loop/project.md
.ai-loop/cycles/<cycle-id>/meta.yaml
.ai-loop/cycles/<cycle-id>/task.md
```

O arquivo `meta.yaml` contém metadados do ciclo (versão do schema, ID do ciclo, timestamp de criação, status). O arquivo `task.md` contém a descrição da tarefa.

### Arquivos obrigatórios apenas para comandos com IA

Para comandos que usam supervisão de IA, o seguinte arquivo é obrigatório:

```
.ai-loop/config/supervisor.yaml
```

Este arquivo configura a IA supervisora (modelo, provedor, parâmetros). Não é obrigatório para os comandos atuais report-only.

### Arquivos recomendados, mas opcionais

Os seguintes arquivos são recomendados, mas opcionais:

```
.ai-loop/architecture.md
.ai-loop/protocol.md
.ai-loop/config/commands.yaml
.ai-loop/config/allowed_paths.yaml
.ai-loop/config/providers.yaml
.ai-loop/config/adapters.yaml
.ai-loop/policies/
.ai-loop/state/
.ai-loop/memory/
.ai-loop/templates/
```

Estes arquivos suportam fluxos de trabalho avançados, mas não são obrigatórios para iniciar o loop.

### Layout evolutivo ideal de `.ai-loop/`

O layout ideal evolui conforme as necessidades emergem:

```
.ai-loop/                    # v1: project.md
.ai-loop/cycles/             # v1: ciclos manuais
.ai-loop/state/              # v2: estado runtime
.ai-loop/policies/           # v2: políticas
.ai-loop/memory/             # v3: memória histórica
.ai-loop/templates/          # v3: templates de produtividade
.ai-loop/specs/              # v4+: specs gerenciadas no futuro
```

### O que NÃO deve ser obrigatório no bootstrap

Os seguintes arquivos NÃO devem ser obrigatórios no bootstrap:

- `.ai-loop/state/` — estado pode ser gerado sob demanda
- `.ai-loop/policies/` — políticas podem ser adicionadas gradualmente
- `.ai-loop/templates/` — templates são conveniência, não requisito
- `.ai-loop/config/providers.yaml` — pode ter valor default "none"
- `.ai-loop/config/adapters.yaml` — pode ter valor default "manual"
- `.ai-loop/config/commands.yaml` — pode ter valor default "none"

### Estrutura atual de `.ai-loop/`

```
Estrutura:
- `project.md` - especificação do projeto
- `architecture.md` - arquitetura do projeto
- `protocol.md` - protocolo de desenvolvimento
- `config/` - configurações operacionais
- `cycles/` - instâncias concretas de ciclos
- `state/` - estado operacional do CLI
```

**Importante:** `.ai-loop/` não deve ser usado como depósito genérico de documentação humana. Documentação conceitual e decisões de design devem viver em `docs/`.

**Nota:** `.ai-loop/specs/` não existe no MVP-0. Especificações vivem em `docs/` até que a funcionalidade seja adicionada em versões futuras.

### Estratégia de migração

Os comandos atuais (`cycle check`, `cycle prompt`, `doctor`) devem continuar funcionando com a estrutura atual. A validação deve reportar warnings para arquivos ausentes que são recomendados, mas não erros (a menos que o comando específico os exija).

O schema versioning é uma estratégia recomendada para evolução futura, não um requisito atual.

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
